import requests
import pandas as pd
import sqlite3
from flask import Flask, render_template_string, request
from fpl_team_optimizer import FPLTeamOptimizer

# Fetch team data
teams = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
team_map = {t["id"]: t["name"] for t in teams["teams"]}
team_abbr = {t["id"]: t["short_name"] for t in teams["teams"]}

# Fetch fixture data
fixtures = requests.get("https://fantasy.premierleague.com/api/fixtures/").json()

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
    h_abbr = team_abbr[a_id]
    a_abbr = team_abbr[h_id]

    data.setdefault(h_name, {})[gw] = (h_fdr, h_abbr)
    data.setdefault(a_name, {})[gw] = (a_fdr, a_abbr)

# Build DataFrame
rows = []
for team, gw_data in data.items():
    row = {"team": team_abbr.get([k for k, v in team_map.items() if v == team][0], team)}
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
display_df = df.copy()

# Save to SQLite
conn = sqlite3.connect("fpl_fdr_with_opponents.db")
df.to_sql("fdr_with_opponents", conn, if_exists="replace")

# Flask UI
app = Flask(__name__)

# Initialize team optimizer
team_optimizer = FPLTeamOptimizer()

@app.route("/home")
def home_page():
    """Home page - blank for now"""
    return render_template_string("""
    <html>
    <head>
        <title>FPL Tools - Home</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body { background-color: #f9f9f9; }
            h1 { color: #4b0d2f; }
            .nav-link { color: #4b0d2f; }
            .nav-link.active { background-color: #4b0d2f !important; color: white !important; }
            .welcome-card { background: white; border-radius: 10px; padding: 40px; margin: 40px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        </style>
    </head>
    <body class="p-4">
        <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
            <div class="container-fluid">
                <span class="navbar-brand">FPL Tools</span>
                <div class="navbar-nav">
                    <a class="nav-link active" href="/home">Home</a>
                    <a class="nav-link" href="/">FDR</a>
                    <a class="nav-link" href="/players-table">Players</a>
                    <a class="nav-link" href="/optimal-team">Squad</a>
                </div>
            </div>
        </nav>
        
        <div class="container">
            <div class="welcome-card">
                <h1 class="mb-4">Welcome to FPL Tools</h1>
                <p class="lead">Your comprehensive Fantasy Premier League analysis toolkit</p>
                <hr class="my-4">
                <div class="row">
                    <div class="col-md-3">
                        <h5>FDR</h5>
                        <p>Fixture Difficulty Ratings with opponent information</p>
                        <a href="/" class="btn btn-primary">View FDR</a>
                    </div>
                    <div class="col-md-3">
                        <h5>Players</h5>
                        <p>Top 200 players sorted by expected points</p>
                        <a href="/players-table" class="btn btn-primary">View Players</a>
                    </div>
                    <div class="col-md-3">
                        <h5>Squad</h5>
                        <p>Optimal FPL team for maximum points</p>
                        <a href="/optimal-team" class="btn btn-primary">View Squad</a>
                    </div>
                    <div class="col-md-3">
                        <h5>Home</h5>
                        <p>Welcome and navigation hub</p>
                        <span class="btn btn-secondary">Current Page</span>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

# Colour coding logic
FDR_COLORS = {
    "1": "#234f1e",
    "2": "#00f090",
    "3": "#dddddd",
    "4": "#ff3366",
    "5": "#800038"
}

def style_fdr(val):
    val_str = str(val)
    color = FDR_COLORS.get(val_str, "none")
    return f"background-color: {color}; color: black" if color != "none" else ""

def style_opp(val, context):
    if context.name.endswith(" Opp"):
        fdr_col = context.name.replace(" Opp", "")
        fdr_val = context.at[fdr_col]
        color = FDR_COLORS.get(str(fdr_val), "none")
        return f"background-color: {color}; color: black" if color != "none" else ""
    return ""

@app.route("/")
def home():
    gw_from = int(request.args.get("from", 1))
    gw_to = int(request.args.get("to", 38))
    team_filter = request.args.get("filter", "").lower()

    cols = []
    for gw in range(gw_from, gw_to + 1):
        cols.append(f"GW{gw}")
        cols.append(f"GW{gw} Opp")

    available_cols = [col for col in cols if col in display_df.columns]
    styled_df = display_df[available_cols]

    if team_filter:
        styled_df = styled_df[styled_df.index.str.lower().str.contains(team_filter)]

    styled = styled_df.style \
        .applymap(style_fdr, subset=[col for col in available_cols if " Opp" not in col]) \
        .apply(lambda x: [style_opp(val, x) for val in x], axis=1, subset=[col for col in available_cols if " Opp" in col])

    html_table = styled.to_html(classes="table table-bordered table-sm display", border=0, table_id="fdrTable")

    return render_template_string("""
    <html>
    <head>
        <title>FDR with Opponents</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.11.3/js/jquery.dataTables.min.js"></script>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.11.3/css/jquery.dataTables.min.css">
        <style>
            body { background-color: #f9f9f9; }
            h1 { color: #4b0d2f; }
            table.dataTable thead th { white-space: normal; }
            table.dataTable td:first-child {
                white-space: nowrap;
                max-width: 75px;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .nav-link { color: #4b0d2f; }
            .nav-link.active { background-color: #4b0d2f !important; color: white !important; }
        </style>
    </head>
    <body class="p-4">
        <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
            <div class="container-fluid">
                <span class="navbar-brand">FPL Tools</span>
                                    <div class="navbar-nav">
                        <a class="nav-link" href="/home">Home</a>
                        <a class="nav-link active" href="/">FDR</a>
                        <a class="nav-link" href="/players-table">Players</a>
                        <a class="nav-link" href="/optimal-team">Squad</a>
                    </div>
            </div>
        </nav>
        
        <h1 class="mb-4">Fixture Difficulty Ratings (FDR)</h1>
        <form method="get" class="mb-3">
            <label>Gameweek from:</label>
            <input type="number" name="from" value="{{ gw_from }}" min="1" max="38">
            <label>to:</label>
            <input type="number" name="to" value="{{ gw_to }}" min="1" max="38">
            <label>Filter by team:</label>
            <input type="text" name="filter" value="{{ team_filter }}">
            <button type="submit" class="btn btn-primary btn-sm">Apply</button>
        </form>
        <div class="table-responsive">
            {{ table|safe }}
        </div>
        <script>
            $(document).ready(function() {
                $('#fdrTable').DataTable({
                    paging: false,
                    ordering: true,
                    info: false,
                    searching: true,
                    order: [],
                    columnDefs: [
                        { targets: '_all', orderable: true }
                    ]
                });
            });
        </script>
    </body>
    </html>
    """, table=html_table, gw_from=gw_from, gw_to=gw_to, team_filter=team_filter)

@app.route("/optimal-team")
def optimal_team():
    """Display the optimal FPL team based on expected points"""
    try:
        # Get optimal team
        optimal_team_data = team_optimizer.get_optimal_team()
        
        # Try to fetch player team information from FPL API
        try:
            response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
            if response.status_code == 200:
                data = response.json()
                players_api = data.get("elements", [])
                
                # Create a mapping of player names to teams
                player_team_map = {}
                for player in players_api:
                    player_name = player.get("web_name", "")
                    team_id = player.get("team", 0)
                    team_name = ""
                    
                    # Find team name
                    for team in data.get("teams", []):
                        if team.get("id") == team_id:
                            team_name = team.get("short_name", "")
                            break
                    
                    if player_name and team_name:
                        player_team_map[player_name] = team_name
                
                # Update player team information
                for player in optimal_team_data["players"]:
                    player_name = player["Name"]
                    # Handle some name variations
                    if player_name in player_team_map:
                        player["Team"] = player_team_map[player_name]
                    elif player_name.replace(".", "") in player_team_map:
                        player["Team"] = player_team_map[player_name.replace(".", "")]
                    elif player_name.split(".")[-1] in player_team_map:
                        player["Team"] = player_team_map[player_name.split(".")[-1]]
                    else:
                        player["Team"] = "Unknown"
        except Exception as e:
            print(f"Error fetching player team data: {e}")
            # Keep team as "Unknown" if API call fails
        
        # Calculate position counts and points
        gk_count = sum(1 for p in optimal_team_data["players"] if p["Position"] == "Goalkeeper")
        def_count = sum(1 for p in optimal_team_data["players"] if p["Position"] == "Defender")
        mid_count = sum(1 for p in optimal_team_data["players"] if p["Position"] == "Midfielder")
        fwd_count = sum(1 for p in optimal_team_data["players"] if p["Position"] == "Forward")
        
        gk_points = sum(p["Total_Points"] for p in optimal_team_data["players"] if p["Position"] == "Goalkeeper")
        def_points = sum(p["Total_Points"] for p in optimal_team_data["players"] if p["Position"] == "Defender")
        mid_points = sum(p["Total_Points"] for p in optimal_team_data["players"] if p["Position"] == "Midfielder")
        fwd_points = sum(p["Total_Points"] for p in optimal_team_data["players"] if p["Position"] == "Forward")
        
        # Calculate budget breakdown by position
        gk_budget = sum(p["Price"] for p in optimal_team_data["players"] if p["Position"] == "Goalkeeper")
        def_budget = sum(p["Price"] for p in optimal_team_data["players"] if p["Position"] == "Defender")
        mid_budget = sum(p["Price"] for p in optimal_team_data["players"] if p["Position"] == "Midfielder")
        fwd_budget = sum(p["Price"] for p in optimal_team_data["players"] if p["Position"] == "Forward")
        
        # Generate weekly transfer recommendations
        weekly_transfers = []
        for week in range(1, 10):
            week_transfers = []
            for player in optimal_team_data["players"]:
                # Get expected points for this week
                gw_points = player['GW1_9_Breakdown'][week-1]
                avg_points = player['Total_Points'] / 9
                
                # Determine transfer recommendation based on performance
                if gw_points < avg_points * 0.7:  # Significantly below average
                    week_transfers.append({
                        'player': player['Name'],
                        'action': 'OUT',
                        'reason': f'Expected {gw_points:.1f} pts vs avg {avg_points:.1f} pts',
                        'gw_points': round(gw_points, 1),
                        'avg_points': round(avg_points, 1)
                    })
                elif gw_points > avg_points * 1.3:  # Significantly above average
                    week_transfers.append({
                        'player': player['Name'],
                        'action': 'IN',
                        'reason': f'Expected {gw_points:.1f} pts vs avg {avg_points:.1f} pts',
                        'gw_points': round(gw_points, 1),
                        'avg_points': round(avg_points, 1)
                    })
                else:
                    week_transfers.append({
                        'player': player['Name'],
                        'action': 'N/A',
                        'reason': 'Performance in line with expectations',
                        'gw_points': round(gw_points, 1),
                        'avg_points': round(avg_points, 1)
                    })
            
            weekly_transfers.append({
                'week': week,
                'transfers': week_transfers
            })
        
        return render_template_string("""
        <html>
        <head>
            <title>Optimal FPL Squad</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { background-color: #f9f9f9; }
                h1 { color: #4b0d2f; }
                .team-card { background: white; border-radius: 10px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .position-badge { font-size: 0.8em; padding: 4px 8px; border-radius: 12px; color: white; }
                .gk { background-color: #dc3545; }
                .def { background-color: #007bff; }
                .mid { background-color: #28a745; }
                .fwd { background-color: #ffc107; color: #212529; }
                .budget-color.gk { background-color: #dc3545; }
                .budget-color.def { background-color: #007bff; }
                .budget-color.mid { background-color: #28a745; }
                .budget-color.fwd { background-color: #ffc107; }
                .stats-card { background: #f8f9fa; border-radius: 8px; padding: 15px; margin: 10px 0; }
                .nav-link { color: #4b0d2f; }
                .nav-link.active { background-color: #4b0d2f !important; color: white !important; }
            </style>
        </head>
        <body class="p-4">
            <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
                <div class="container-fluid">
                    <span class="navbar-brand">FPL Tools</span>
                    <div class="navbar-nav">
                        <a class="nav-link" href="/home">Home</a>
                        <a class="nav-link" href="/">FDR</a>
                        <a class="nav-link" href="/players-table">Players</a>
                        <a class="nav-link active" href="/optimal-team">Squad</a>
                    </div>
                </div>
            </nav>
            
            <div class="container">
                <h1 class="mb-4">Optimal FPL Squad for GW1-9</h1>
                
                <div class="stats-card">
                    <h4>Team Overview</h4>
                    <p><strong>Formation:</strong> {{ formation }}</p>
                    <p><strong>Total Expected Points (GW1-9):</strong> {{ "%.1f"|format(total_expected_points) }}</p>
                    <p><strong>Remaining Budget:</strong> £{{ "%.1f"|format(remaining_budget) }}M</p>
                    <p><strong>Team Value:</strong> £{{ "%.1f"|format(team_value) }}M</p>
                    <p><strong>Squad Size:</strong> {{ players|length }} players (11 Starting + 4 Bench)</p>
                </div>
                
                <!-- Full Squad Table -->
                <div class="team-card">
                    <h3>Full 15-Player Squad</h3>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Position</th>
                                    <th>Team</th>
                                    <th>Price</th>
                                    <th>Total Points</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for player in players %}
                                <tr class="{% if player.Status == 'Bench' %}table-secondary{% endif %}">
                                    <td><strong>{{ player.Name }}</strong></td>
                                    <td>
                                        <span class="position-badge 
                                            {% if player.Position == 'Goalkeeper' %}gk
                                            {% elif player.Position == 'Defender' %}def
                                            {% elif player.Position == 'Midfielder' %}mid
                                            {% else %}fwd{% endif %}">
                                            {{ player.Position }}
                                        </span>
                                    </td>
                                    <td>{{ player.Team }}</td>
                                    <td>£{{ "%.1f"|format(player.Price) }}M</td>
                                    <td>{{ "%.1f"|format(player.Total_Points) }}</td>
                                    <td>
                                        {% if player.Status == 'Starting' %}
                                            <span class="badge bg-success">Starting XI</span>
                                        {% else %}
                                            <span class="badge bg-secondary">Bench</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Total Spend Summary -->
                    <div class="mt-4 p-3 bg-light rounded">
                        <div class="row text-center">
                            <div class="col-md-4">
                                <h5 class="text-muted">Total Spend</h5>
                                <h3 class="text-primary">£{{ "%.1f"|format(team_value) }}M</h3>
                            </div>
                            <div class="col-md-4">
                                <h5 class="text-muted">Remaining Budget</h5>
                                <h3 class="text-success">£{{ "%.1f"|format(remaining_budget) }}M</h3>
                            </div>
                            <div class="col-md-4">
                                <h5 class="text-muted">Budget Used</h5>
                                <h3 class="text-info">{{ "%.1f"|format((team_value / 100.0) * 100) }}%</h3>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Budget Distribution Chart -->
                <div class="team-card">
                    <h3>Budget Distribution by Position</h3>
                    <div class="row">
                        <div class="col-md-8">
                            <canvas id="budgetChart" width="400" height="200"></canvas>
                        </div>
                        <div class="col-md-4">
                            <div class="budget-legend">
                                <div class="d-flex align-items-center mb-2">
                                    <div class="budget-color gk me-2" style="width: 20px; height: 20px; border-radius: 50%;"></div>
                                    <span><strong>Goalkeepers:</strong> £{{ "%.1f"|format(gk_budget) }}M ({{ "%.1f"|format((gk_budget / team_value) * 100) }}%)</span>
                                </div>
                                <div class="d-flex align-items-center mb-2">
                                    <div class="budget-color def me-2" style="width: 20px; height: 20px; border-radius: 50%;"></div>
                                    <span><strong>Defenders:</strong> £{{ "%.1f"|format(def_budget) }}M ({{ "%.1f"|format((def_budget / team_value) * 100) }}%)</span>
                                </div>
                                <div class="d-flex align-items-center mb-2">
                                    <div class="budget-color mid me-2" style="width: 20px; height: 20px; border-radius: 50%;"></div>
                                    <span><strong>Midfielders:</strong> £{{ "%.1f"|format(mid_budget) }}M ({{ "%.1f"|format((mid_budget / team_value) * 100) }}%)</span>
                                </div>
                                <div class="d-flex align-items-center mb-2">
                                    <div class="budget-color fwd me-2" style="width: 20px; height: 20px; border-radius: 50%;"></div>
                                    <span><strong>Forwards:</strong> £{{ "%.1f"|format(fwd_budget) }}M ({{ "%.1f"|format((fwd_budget / team_value) * 100) }}%)</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="team-card">
                    <h3>Weekly Transfer Recommendations & Performance</h3>
                    
                    <!-- Weekly Tabs -->
                    <ul class="nav nav-tabs" id="weeklyTabs" role="tablist">
                        {% for week_data in weekly_transfers %}
                        <li class="nav-item" role="presentation">
                            <button class="nav-link {% if loop.first %}active{% endif %}" 
                                    id="week{{ week_data.week }}-tab" 
                                    data-bs-toggle="tab" 
                                    data-bs-target="#week{{ week_data.week }}" 
                                    type="button" 
                                    role="tab">
                                GW{{ week_data.week }}
                            </button>
                        </li>
                        {% endfor %}
                    </ul>
                    
                    <!-- Weekly Content -->
                    <div class="tab-content" id="weeklyTabContent">
                        {% for week_data in weekly_transfers %}
                        <div class="tab-pane fade {% if loop.first %}show active{% endif %}" 
                             id="week{{ week_data.week }}" 
                             role="tabpanel">
                            
                            <div class="table-responsive mt-3">
                                <table class="table table-striped table-sm">
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Position</th>
                                            <th>Team</th>
                                            <th>Price</th>
                                            <th>GW{{ week_data.week }} Points</th>
                                            <th>Transfer</th>
                                            <th>Reason</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for transfer in week_data.transfers %}
                                        <tr>
                                            <td><strong>{{ transfer.player }}</strong></td>
                                            <td>
                                                {% for player in players %}
                                                    {% if player.Name == transfer.player %}
                                                        <span class="position-badge 
                                                            {% if player.Position == 'Goalkeeper' %}gk
                                                            {% elif player.Position == 'Defender' %}def
                                                            {% elif player.Position == 'Midfielder' %}mid
                                                            {% else %}fwd{% endif %}">
                                                            {{ player.Position }}
                                                        </span>
                                                    {% endif %}
                                                {% endfor %}
                                            </td>
                                            <td>
                                                {% for player in players %}
                                                    {% if player.Name == transfer.player %}
                                                        {{ player.Team }}
                                                    {% endif %}
                                                {% endfor %}
                                            </td>
                                            <td>
                                                {% for player in players %}
                                                    {% if player.Name == transfer.player %}
                                                        £{{ player.Price }}M
                                                    {% endif %}
                                                {% endfor %}
                                            </td>
                                            <td>
                                                <span class="{% if transfer.action == 'IN' %}text-success{% elif transfer.action == 'OUT' %}text-danger{% else %}text-muted{% endif %}">
                                                    {{ "%.1f"|format(transfer.gw_points) }}
                                                </span>
                                            </td>
                                            <td>
                                                {% if transfer.action == 'IN' %}
                                                    <span class="badge bg-success">IN</span>
                                                {% elif transfer.action == 'OUT' %}
                                                    <span class="badge bg-danger">OUT</span>
                                                {% else %}
                                                    <span class="badge bg-secondary">N/A</span>
                                                {% endif %}
                                            </td>
                                            <td>
                                                <small class="text-muted">{{ transfer.reason }}</small>
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="stats-card">
                            <h5>Position Breakdown</h5>
                            <p><strong>Goalkeepers:</strong> {{ gk_count }}</p>
                            <p><strong>Defenders:</strong> {{ def_count }}</p>
                            <p><strong>Midfielders:</strong> {{ mid_count }}</p>
                            <p><strong>Forwards:</strong> {{ fwd_count }}</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stats-card">
                            <h5>Expected Points by Position</h5>
                            <p><strong>Goalkeepers:</strong> {{ "%.1f"|format(gk_points) }} pts</p>
                            <p><strong>Defenders:</strong> {{ "%.1f"|format(def_points) }} pts</p>
                            <p><strong>Midfielders:</strong> {{ "%.1f"|format(mid_points) }} pts</p>
                            <p><strong>Forwards:</strong> {{ "%.1f"|format(fwd_points) }} pts</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stats-card">
                            <h5>Squad Status</h5>
                            <p><strong>Starting XI:</strong> 11 players</p>
                            <p><strong>Bench:</strong> 4 players</p>
                            <p><strong>Total Squad:</strong> 15 players</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                // Budget Distribution Pie Chart
                const ctx = document.getElementById('budgetChart').getContext('2d');
                const budgetChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: ['Goalkeepers', 'Defenders', 'Midfielders', 'Forwards'],
                        datasets: [{
                            data: [
                                {{ gk_budget }},
                                {{ def_budget }},
                                {{ mid_budget }},
                                {{ fwd_budget }}
                            ],
                            backgroundColor: [
                                '#dc3545',  // GK - Red
                                '#007bff',  // DEF - Blue
                                '#28a745',  // MID - Green
                                '#ffc107'   // FWD - Yellow
                            ],
                            borderColor: '#ffffff',
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.parsed || 0;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((value / total) * 100).toFixed(1);
                                        return `${label}: £${value.toFixed(1)}M (${percentage}%)`;
                                    }
                                }
                            }
                        }
                    }
                });
            </script>
        </body>
        </html>
        """, 
        players=optimal_team_data["players"],
        weekly_transfers=weekly_transfers,
        total_expected_points=optimal_team_data["total_expected_points"],
        remaining_budget=optimal_team_data["remaining_budget"],
        team_value=100 - optimal_team_data["remaining_budget"],
        formation=optimal_team_data["formation"],
        gk_count=gk_count,
        def_count=def_count,
        mid_count=mid_count,
        fwd_count=fwd_count,
        gk_points=gk_points,
        def_points=def_points,
        mid_points=mid_points,
        fwd_points=fwd_points,
        gk_budget=gk_budget,
        def_budget=def_budget,
        mid_budget=mid_budget,
        fwd_budget=fwd_budget
        )
        
    except Exception as e:
        return f"Error generating optimal team: {str(e)}"

@app.route("/players-table")
def players_table():
    """Display the top 200 players in a sortable table"""
    try:
        # Get all players data from the optimizer
        all_players = team_optimizer.players_data.copy()
        
        # Calculate total expected points for first 9 weeks
        gw_columns = [f"GW {i}" for i in range(1, 10)]
        all_players["Total_GW1_9"] = all_players[gw_columns].sum(axis=1)
        
        # Sort by total expected points (descending)
        sorted_players = all_players.sort_values("Total_GW1_9", ascending=False)
        
        # Fetch injury news from FPL Scout (simplified - in real app you'd parse the HTML)
        injury_news = {
            "Haaland": "Minor knock, expected to be fit for GW1",
            "Salah": "Fully fit and ready",
            "Palmer": "No injury concerns",
            "Watkins": "Recovered from previous issue",
            "Isak": "Minor fitness concern, monitoring required"
        }
        
        # Convert to list of dictionaries for template
        players_list = []
        for _, player in sorted_players.iterrows():
            player_name = player["Name"]
            is_injured = player_name in injury_news and "injury" in injury_news[player_name].lower()
            
            players_list.append({
                "Name": player_name,
                "Position": player["Position"],
                "Price": player["Price"],
                "Uncertainty": player["Uncertainty"],
                "Overall": player["Overall"],
                "Total_GW1_9": player["Total_GW1_9"],
                "Chance_Playing": "100%" if not is_injured else "75%",
                "Injury_Status": injury_news.get(player_name, "No injury concerns"),
                "Is_Injured": is_injured,
                "GW1": player["GW 1"],
                "GW2": player["GW 2"],
                "GW3": player["GW 3"],
                "GW4": player["GW 4"],
                "GW5": player["GW 5"],
                "GW6": player["GW 6"],
                "GW7": player["GW 7"],
                "GW8": player["GW 8"],
                "GW9": player["GW 9"]
            })
        
        return render_template_string("""
        <html>
        <head>
            <title>Top 200 FPL Players</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdn.datatables.net/1.11.3/css/jquery.dataTables.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script src="https://cdn.datatables.net/1.11.3/js/jquery.dataTables.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <style>
                body { background-color: #f9f9f9; }
                h1 { color: #4b0d2f; }
                .nav-link { color: #4b0d2f; }
                .nav-link.active { background-color: #4b0d2f !important; color: white !important; }
                .position-badge { font-size: 0.8em; padding: 4px 8px; border-radius: 12px; color: white; }
                .gk { background-color: #dc3545; }
                .def { background-color: #007bff; }
                .mid { background-color: #28a745; }
                .fwd { background-color: #ffc107; color: #212529; }
                .table th { white-space: nowrap; }
                .table td { vertical-align: middle; }
            </style>
        </head>
        <body class="p-4">
            <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
                <div class="container-fluid">
                    <span class="navbar-brand">FPL Tools</span>
                    <div class="navbar-nav">
                        <a class="nav-link" href="/home">Home</a>
                        <a class="nav-link" href="/">FDR</a>
                        <a class="nav-link active" href="/players-table">Players</a>
                        <a class="nav-link" href="/optimal-team">Squad</a>
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
                                <th>Price</th>
                                <th>Uncertainty</th>
                                <th>Overall</th>
                                <th>Total (GW1-9)</th>
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
                                    <td><strong>{{ player.Name }}</strong></td>
                                    <td>
                                        <span class="position-badge 
                                            {% if player.Position == 'Goalkeeper' %}gk
                                            {% elif player.Position == 'Midfielder' %}mid
                                            {% elif player.Position == 'Forward' %}fwd
                                            {% else %}def{% endif %}">
                                            {{ player.Position }}
                                        </span>
                                    </td>
                                    <td>£{{ "%.1f"|format(player.Price) }}M</td>
                                    <td>{{ player.Uncertainty }}%</td>
                                    <td>{{ "%.1f"|format(player.Overall) }}</td>
                                    <td><strong>{{ "%.1f"|format(player.Total_GW1_9) }}</strong></td>
                                    <td>
                                        {% if player.Is_Injured %}
                                            <span class="text-danger" style="cursor: pointer;" data-bs-toggle="modal" data-bs-target="#injuryModal{{ loop.index }}">
                                                <i class="fas fa-exclamation-triangle"></i> {{ player.Chance_Playing }}
                                            </span>
                                        {% else %}
                                            <span class="text-success">{{ player.Chance_Playing }}</span>
                                        {% endif %}
                                    </td>
                                    <td>{{ "%.1f"|format(player.GW1) }}</td>
                                    <td>{{ "%.1f"|format(player.GW2) }}</td>
                                    <td>{{ "%.1f"|format(player.GW3) }}</td>
                                    <td>{{ "%.1f"|format(player.GW4) }}</td>
                                    <td>{{ "%.1f"|format(player.GW5) }}</td>
                                    <td>{{ "%.1f"|format(player.GW6) }}</td>
                                    <td>{{ "%.1f"|format(player.GW7) }}</td>
                                    <td>{{ "%.1f"|format(player.GW8) }}</td>
                                    <td>{{ "%.1f"|format(player.GW9) }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Injury Modals -->
            {% for player in players %}
                {% if player.Is_Injured %}
                <div class="modal fade" id="injuryModal{{ loop.index }}" tabindex="-1" aria-labelledby="injuryModalLabel{{ loop.index }}" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="injuryModalLabel{{ loop.index }}">
                                    <i class="fas fa-exclamation-triangle text-warning"></i> 
                                    Injury Update: {{ player.Name }}
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>Chance of Playing:</strong> {{ player.Chance_Playing }}
                                    </div>
                                    <div class="col-md-6">
                                        <strong>Position:</strong> 
                                        <span class="position-badge 
                                            {% if player.Position == 'Goalkeeper' %}gk
                                            {% elif player.Position == 'Midfielder' %}mid
                                            {% elif player.Position == 'Forward' %}fwd
                                            {% else %}def{% endif %}">
                                            {{ player.Position }}
                                        </span>
                                    </div>
                                </div>
                                <hr>
                                <div class="alert alert-warning">
                                    <strong>Injury Status:</strong><br>
                                    {{ player.Injury_Status }}
                                </div>
                                <div class="alert alert-info">
                                    <strong>Source:</strong> <a href="https://fantasy.premierleague.com/the-scout/player-news" target="_blank">FPL Scout</a>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
                {% endif %}
            {% endfor %}
            
            <script>
                $(document).ready(function() {
                    $('#playersTable').DataTable({
                        paging: true,
                        pageLength: 25,
                        ordering: true,
                        info: true,
                        searching: true,
                        order: [[6, 'desc']], // Sort by Total (GW1-9) by default
                        columnDefs: [
                            { targets: [0], orderable: false }, // Rank column not sortable
                            { targets: [1, 2], orderable: true }, // Name and Position
                            { targets: [3, 4, 5, 6, 7], orderable: true, type: 'num' }, // Numeric columns
                            { targets: [8, 9, 10, 11, 12, 13, 14, 15, 16], orderable: true, type: 'num' } // GW columns
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
        """, players=players_list)
        
    except Exception as e:
        return f"Error generating players table: {str(e)}"

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001, debug=True)
