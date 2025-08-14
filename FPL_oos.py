import requests
import pandas as pd
import sqlite3
from flask import Flask, render_template_string, request

# Initialize Flask app
app = Flask(__name__)

# Fetch team data from FPL API
def fetch_fpl_data():
    """Fetch team and fixture data from FPL API"""
    try:
        # Fetch team data
        teams_response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
        teams = teams_response.json()
        team_map = {t["id"]: t["name"] for t in teams["teams"]}
        team_abbr = {t["id"]: t["short_name"] for t in teams["teams"]}

        # Fetch fixture data
        fixtures_response = requests.get("https://fantasy.premierleague.com/api/fixtures/")
        fixtures = fixtures_response.json()

        return team_map, team_abbr, fixtures
    except Exception as e:
        print(f"Error fetching FPL data: {e}")
        return {}, {}, []

# Fetch player data from FPL API
def fetch_players_data():
    """Fetch player data from FPL API"""
    try:
        response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
        if response.status_code == 200:
            data = response.json()
            players = data.get("elements", [])
            teams = data.get("teams", [])
            
            # Create team mapping
            team_map = {t["id"]: t["name"] for t in teams}
            
            # Process players data
            players_data = []
            for player in players:
                if player.get("status") == "a":  # Only active players
                    player_info = {
                        "id": player.get("id"),
                        "name": player.get("web_name", ""),
                        "full_name": player.get("first_name", "") + " " + player.get("second_name", ""),
                        "position": player.get("element_type"),
                        "team": team_map.get(player.get("team"), "Unknown"),
                        "price": player.get("now_cost", 0) / 10.0,  # Convert from 0.1M units
                        "total_points": player.get("total_points", 0),
                        "form": player.get("form", "0.0"),
                        "points_per_game": player.get("points_per_game", "0.0"),
                        "selected_by_percent": player.get("selected_by_percent", "0.0"),
                        "transfers_in": player.get("transfers_in", 0),
                        "transfers_out": player.get("transfers_out", 0),
                        "influence": player.get("influence", "0.0"),
                        "creativity": player.get("creativity", "0.0"),
                        "threat": player.get("threat", "0.0"),
                        "ict_index": player.get("ict_index", "0.0"),
                        "chance_of_playing_next_round": player.get("chance_of_playing_next_round") or 100,
                        "news": player.get("news", ""),
                        "injury_status": player.get("news", "No injury concerns")
                    }
                    
                    # Add position names
                    position_names = {1: "Goalkeeper", 2: "Defender", 3: "Midfielder", 4: "Forward"}
                    player_info["position_name"] = position_names.get(player_info["position"], "Unknown")
                    
                    # Calculate expected points for GW1-9 (simplified calculation)
                    base_points = float(player_info["points_per_game"]) if player_info["points_per_game"] != "0.0" else 4.0
                    player_info["gw1_9_points"] = [round(base_points * (0.8 + 0.4 * (i % 3)), 1) for i in range(9)]
                    player_info["total_gw1_9"] = sum(player_info["gw1_9_points"])
                    
                    # Calculate efficiency metrics
                    player_info["points_per_million"] = player_info["total_gw1_9"] / player_info["price"] if player_info["price"] > 0 else 0
                    
                    players_data.append(player_info)
            
            return players_data
        else:
            print(f"Error fetching players data: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching players data: {e}")
        return []

# Build FDR DataFrame
def build_fdr_dataframe():
    """Build the FDR DataFrame with opponent information"""
    team_map, team_abbr, fixtures = fetch_fpl_data()
    
    if not team_map or not fixtures:
        return pd.DataFrame()

    # Create structure: {team: {gw: (fdr, opp)}}
    data = {}

    for fixture in fixtures:
        gw = fixture["event"]
        if gw is None:
            continue

        h_id = fixture["team_h"]
        a_id = fixture["team_a"]
        h_fdr = fixture["team_h_difficulty"]
        a_fdr = fixture["team_a_difficulty"]

        h_name = team_map[h_id]
        a_name = team_map[a_id]
        h_abbr = team_abbr[a_id]  # Home team plays away team abbreviation
        a_abbr = team_abbr[h_id]  # Away team plays home team abbreviation

        data.setdefault(h_name, {})[gw] = (h_fdr, h_abbr)
        data.setdefault(a_name, {})[gw] = (a_fdr, a_abbr)

    # Build DataFrame
    rows = []
    for team, gw_data in data.items():
        # Find team abbreviation
        team_id = [k for k, v in team_map.items() if v == team]
        team_abbr_name = team_abbr.get(team_id[0], team) if team_id else team
        
        row = {"team": team_abbr_name}
        for gw in range(1, 39):
            if gw in gw_data:
                fdr, opp = gw_data[gw]
                row[f"GW{gw}"] = fdr
                row[f"GW{gw} Opp"] = opp
            else:
                row[f"GW{gw}"] = "-"
                row[f"GW{gw} Opp"] = "-"
        rows.append(row)

    df = pd.DataFrame(rows).set_index("team")
    
    # Save to SQLite database
    try:
        conn = sqlite3.connect("fpl_fdr.db")
        df.to_sql("fdr_with_opponents", conn, if_exists="replace")
        conn.close()
        print("FDR data saved to database successfully")
    except Exception as e:
        print(f"Error saving to database: {e}")
    
    return df

# FDR color coding
FDR_COLORS = {
    "1": "#234f1e",  # Dark green - Very Easy
    "2": "#00f090",  # Light green - Easy
    "3": "#dddddd",  # Gray - Medium
    "4": "#ff3366",  # Pink - Hard
    "5": "#800038"   # Dark red - Very Hard
}

def style_fdr(val):
    """Style FDR values with colors"""
    val_str = str(val)
    color = FDR_COLORS.get(val_str, "none")
    return f"background-color: {color}; color: black" if color != "none" else ""

def style_opp(val, context):
    """Style opponent cells with matching FDR colors"""
    if context.name.endswith(" Opp"):
        fdr_col = context.name.replace(" Opp", "")
        fdr_val = context.at[fdr_col]
        color = FDR_COLORS.get(str(fdr_val), "none")
        return f"background-color: {color}; color: black" if color != "none" else ""
    return ""

# Routes
@app.route("/")
def fdr_table():
    """Main FDR table page"""
    # Get filter parameters
    gw_from = int(request.args.get("from", 1))
    gw_to = int(request.args.get("to", 38))
    team_filter = request.args.get("filter", "").lower()

    # Build FDR DataFrame
    df = build_fdr_dataframe()
    
    if df.empty:
        return "Error: Could not fetch FPL data. Please try again later."

    # Filter columns based on gameweek range
    cols = []
    for gw in range(gw_from, gw_to + 1):
        cols.append(f"GW{gw}")
        cols.append(f"GW{gw} Opp")

    available_cols = [col for col in cols if col in df.columns]
    styled_df = df[available_cols]

    # Apply team filter
    if team_filter:
        styled_df = styled_df[styled_df.index.str.lower().str.contains(team_filter)]

    # Apply styling
    styled = styled_df.style \
        .applymap(style_fdr, subset=[col for col in available_cols if " Opp" not in col]) \
        .apply(lambda x: [style_opp(val, x) for val in x], axis=1, subset=[col for col in available_cols if " Opp" in col])

    html_table = styled.to_html(classes="table table-bordered table-sm display", border=0, table_id="fdrTable")

    return render_template_string("""
    <html>
    <head>
        <title>FPL Fixture Difficulty Ratings (FDR)</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.11.3/js/jquery.dataTables.min.js"></script>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.11.3/css/jquery.dataTables.min.css">
        <style>
            body { 
                background-color: #f8f9fa; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .navbar-brand { 
                font-weight: bold; 
                color: #2c3e50 !important; 
            }
            .nav-link { 
                color: #34495e !important; 
                font-weight: 500;
            }
            .nav-link.active { 
                background-color: #3498db !important; 
                color: white !important; 
                border-radius: 5px;
            }
            .nav-link:hover { 
                color: #3498db !important; 
            }
            h1 { 
                color: #2c3e50; 
                font-weight: 600;
                margin-bottom: 1.5rem;
            }
            .filter-form {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            .filter-form label {
                font-weight: 500;
                margin-right: 10px;
                color: #2c3e50;
            }
            .filter-form input {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px 10px;
                margin-right: 15px;
            }
            .btn-primary {
                background-color: #3498db;
                border-color: #3498db;
                border-radius: 5px;
                padding: 8px 20px;
            }
            .btn-primary:hover {
                background-color: #2980b9;
                border-color: #2980b9;
            }
            .table-responsive {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
            }
            table.dataTable thead th { 
                white-space: normal; 
                background-color: #f8f9fa;
                border-color: #dee2e6;
                font-weight: 600;
                color: #2c3e50;
            }
            table.dataTable td:first-child {
                white-space: nowrap;
                max-width: 75px;
                overflow: hidden;
                text-overflow: ellipsis;
                font-weight: 600;
                color: #2c3e50;
            }
            .legend {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            .legend-item {
                display: inline-block;
                margin-right: 20px;
                margin-bottom: 10px;
            }
            .legend-color {
                display: inline-block;
                width: 20px;
                height: 20px;
                border-radius: 3px;
                margin-right: 8px;
                border: 1px solid #ddd;
            }
        </style>
    </head>
    <body class="p-4">
        <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
            <div class="container-fluid">
                <span class="navbar-brand">FPL Tools</span>
                <div class="navbar-nav">
                    <a class="nav-link active" href="/">FDR Table</a>
                    <a class="nav-link" href="/players">Players</a>
                </div>
            </div>
        </nav>
        
        <div class="container-fluid">
            <h1 class="text-center">Fixture Difficulty Ratings (FDR)</h1>
            
            <!-- FDR Legend -->
            <div class="legend">
                <h5 class="mb-3">FDR Color Legend:</h5>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #234f1e;"></span>
                    <span>1 - Very Easy</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #00f090;"></span>
                    <span>2 - Easy</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #dddddd;"></span>
                    <span>3 - Medium</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #ff3366;"></span>
                    <span>4 - Hard</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #800038;"></span>
                    <span>5 - Very Hard</span>
                </div>
            </div>
            
            <!-- Filter Form -->
            <form method="get" class="filter-form">
                <div class="row align-items-center">
                    <div class="col-md-3">
                        <label>Gameweek from:</label>
                        <input type="number" name="from" value="{{ gw_from }}" min="1" max="38" class="form-control">
                    </div>
                    <div class="col-md-3">
                        <label>to:</label>
                        <input type="number" name="to" value="{{ gw_to }}" min="1" max="38" class="form-control">
                    </div>
                    <div class="col-md-3">
                        <label>Filter by team:</label>
                        <input type="text" name="filter" value="{{ team_filter }}" placeholder="e.g., Arsenal" class="form-control">
                    </div>
                    <div class="col-md-3">
                        <button type="submit" class="btn btn-primary">Apply Filters</button>
                    </div>
                </div>
            </form>
            
            <!-- FDR Table -->
            <div class="table-responsive">
                {{ table|safe }}
            </div>
        </div>
        
        <script>
            $(document).ready(function() {
                $('#fdrTable').DataTable({
                    paging: false,
                    ordering: true,
                    info: false,
                    searching: true,
                    order: [],
                    scrollX: true,
                    columnDefs: [
                        { targets: '_all', orderable: true }
                    ],
                    language: {
                        search: "Search teams:",
                        lengthMenu: "Show _MENU_ teams per page",
                        info: "Showing _START_ to _END_ of _TOTAL_ teams"
                    }
                });
            });
        </script>
    </body>
    </html>
    """, table=html_table, gw_from=gw_from, gw_to=gw_to, team_filter=team_filter)

@app.route("/players")
def players_table():
    """Display the FPL players table"""
    try:
        # Fetch players data
        players_data = fetch_players_data()
        
        if not players_data:
            return "Error: Could not fetch players data. Please try again later."
        
        # Sort players by total GW1-9 points (descending)
        players_data.sort(key=lambda x: x["total_gw1_9"], reverse=True)
        
        return render_template_string("""
        <html>
        <head>
            <title>FPL Players - Expected Points (GW1-9)</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdn.datatables.net/1.11.3/css/jquery.dataTables.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script src="https://cdn.datatables.net/1.11.3/js/jquery.dataTables.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <style>
                body { 
                    background-color: #f8f9fa; 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }
                .navbar-brand { 
                    font-weight: bold; 
                    color: #2c3e50 !important; 
                }
                .nav-link { 
                    color: #34495e !important; 
                    font-weight: 500;
                }
                .nav-link.active { 
                    background-color: #3498db !important; 
                    color: white !important; 
                    border-radius: 5px;
                }
                .nav-link:hover { 
                    color: #3498db !important; 
                }
                h1 { 
                    color: #2c3e50; 
                    font-weight: 600;
                    margin-bottom: 1.5rem;
                }
                .position-badge { 
                    font-size: 0.8em; 
                    padding: 4px 8px; 
                    border-radius: 12px; 
                    color: white; 
                    font-weight: bold;
                }
                .gk { background-color: #dc3545; }
                .def { background-color: #007bff; }
                .mid { background-color: #28a745; }
                .fwd { background-color: #ffc107; color: #212529; }
                .table th { white-space: nowrap; }
                .table td { vertical-align: middle; }
                .chance-playing {
                    font-weight: bold;
                }
                .chance-playing.healthy { color: #28a745; }
                .chance-playing.injured { color: #dc3545; }
                .points-per-million {
                    color: #17a2b8;
                    font-weight: bold;
                }
            </style>
        </head>
        <body class="p-4">
            <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
                <div class="container-fluid">
                    <span class="navbar-brand">FPL Tools</span>
                    <div class="navbar-nav">
                        <a class="nav-link" href="/">FDR Table</a>
                        <a class="nav-link active" href="/players">Players</a>
                    </div>
                </div>
            </nav>
            
            <div class="container-fluid">
                <h1 class="mb-4">FPL Players - Expected Points (GW1-9)</h1>
                
                <div class="table-responsive">
                    <table id="playersTable" class="table table-striped table-bordered">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Name</th>
                                <th>Position</th>
                                <th>Team</th>
                                <th>Price</th>
                                <th>Form</th>
                                <th>Total (GW1-9)</th>
                                <th>Points/£</th>
                                <th>Chance of Playing</th>
                                <th>GW1</th>
                                <th>GW2</th>
                                <th>GW3</th>
                                <th>GW4</th>
                                <th>GW5</th>
                                <th>GW6</th>
                                <th>GW7</th>
                                <th>GW8</th>
                                <th>GW9</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for player in players %}
                            <tr>
                                <td>{{ loop.index }}</td>
                                <td><strong>{{ player.name }}</strong></td>
                                <td>
                                    <span class="position-badge 
                                        {% if player.position_name == 'Goalkeeper' %}gk
                                        {% elif player.position_name == 'Defender' %}def
                                        {% elif player.position_name == 'Midfielder' %}mid
                                        {% else %}fwd{% endif %}">
                                        {{ player.position_name }}
                                    </span>
                                </td>
                                <td>{{ player.team }}</td>
                                <td>£{{ "%.1f"|format(player.price) }}M</td>
                                <td>{{ player.form }}</td>
                                <td><strong>{{ "%.1f"|format(player.total_gw1_9) }}</strong></td>
                                <td class="points-per-million">{{ "%.2f"|format(player.points_per_million) }}</td>
                                <td>
                                    {% if player.chance_of_playing_next_round and player.chance_of_playing_next_round < 100 %}
                                        <span class="chance-playing injured">
                                            <i class="fas fa-exclamation-triangle"></i> {{ player.chance_of_playing_next_round }}%
                                        </span>
                                    {% else %}
                                        <span class="chance-playing healthy">{{ player.chance_of_playing_next_round or 100 }}%</span>
                                    {% endif %}
                                </td>
                                <td>{{ "%.1f"|format(player.gw1_9_points[0]) }}</td>
                                <td>{{ "%.1f"|format(player.gw1_9_points[1]) }}</td>
                                <td>{{ "%.1f"|format(player.gw1_9_points[2]) }}</td>
                                <td>{{ "%.1f"|format(player.gw1_9_points[3]) }}</td>
                                <td>{{ "%.1f"|format(player.gw1_9_points[4]) }}</td>
                                <td>{{ "%.1f"|format(player.gw1_9_points[5]) }}</td>
                                <td>{{ "%.1f"|format(player.gw1_9_points[6]) }}</td>
                                <td>{{ "%.1f"|format(player.gw1_9_points[7]) }}</td>
                                <td>{{ "%.1f"|format(player.gw1_9_points[8]) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <script>
                $(document).ready(function() {
                    $('#playersTable').DataTable({
                        paging: true,
                        pageLength: 25,
                        ordering: true,
                        info: true,
                        searching: true,
                        order: [[6, 'desc']], // Sort by Total (GW1-9) by default
                        scrollX: true,
                        columnDefs: [
                            { targets: [0], orderable: false }, // Rank column not sortable
                            { targets: [1, 2, 3], orderable: true }, // Name, Position, Team
                            { targets: [4, 5, 6, 7], orderable: true, type: 'num' }, // Price, Form, Total, Points/£
                            { targets: [8], orderable: false }, // Chance of Playing not sortable
                            { targets: [9, 10, 11, 12, 13, 14, 15, 16, 17], orderable: true, type: 'num' } // GW columns
                        ],
                        language: {
                            search: "Search players:",
                            lengthMenu: "Show _MENU_ players per page",
                            info: "Showing _START_ to _END_ of _TOTAL_ players"
                        }
                    });
                });
            </script>
        </body>
        </html>
        """, players=players_data)
        
    except Exception as e:
        return f"Error generating players table: {str(e)}"

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "FPL FDR service is running"}

if __name__ == "__main__":
    print("Starting FPL FDR application...")
    print("Building FDR data...")
    df = build_fdr_dataframe()
    if not df.empty:
        print(f"FDR data loaded successfully for {len(df)} teams")
        print("Available gameweeks: 1-38")
        print("Starting Flask server on http://127.0.0.1:8001")
    else:
        print("Warning: Could not load FDR data")
    
    app.run(host="127.0.0.1", port=8003, debug=True)
