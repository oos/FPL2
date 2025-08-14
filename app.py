from flask import Flask, jsonify, request, render_template, render_template_string
from flask_cors import CORS
import sqlite3
import requests
from typing import List, Dict, Any
import os

app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE_PATH = "fpl_oos.db"

class DatabaseManager:
    """Manages database operations for the FPL application"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        try:
            # Create players table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    position_name TEXT NOT NULL,
                    team TEXT NOT NULL,
                    price REAL NOT NULL,
                    availability TEXT DEFAULT 'Available',
                    uncertainty_percent TEXT DEFAULT '24%',
                    overall_total REAL NOT NULL,
                    gw1_points REAL DEFAULT 0.0,
                    gw2_points REAL DEFAULT 0.0,
                    gw3_points REAL DEFAULT 0.0,
                    gw4_points REAL DEFAULT 0.0,
                    gw5_points REAL DEFAULT 0.0,
                    gw6_points REAL DEFAULT 0.0,
                    gw7_points REAL DEFAULT 0.0,
                    gw8_points REAL DEFAULT 0.0,
                    gw9_points REAL DEFAULT 0.0,
                    points_per_million REAL DEFAULT 0.0,
                    chance_of_playing_next_round INTEGER DEFAULT 100
                )
            """)
            
            # Create teams table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    short_name TEXT NOT NULL,
                    strength INTEGER DEFAULT 0
                )
            """)
            
            # Create fixtures table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fixtures (
                    id INTEGER PRIMARY KEY,
                    home_team_id INTEGER,
                    away_team_id INTEGER,
                    home_difficulty INTEGER,
                    away_difficulty INTEGER,
                    gameweek INTEGER,
                    FOREIGN KEY (home_team_id) REFERENCES teams (id),
                    FOREIGN KEY (away_team_id) REFERENCES teams (id)
                )
            """)
            
            conn.commit()
            print("Database initialized successfully")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players from the database"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT id, name, position_name, team, price, availability, uncertainty_percent, overall_total,
                       gw1_points, gw2_points, gw3_points, gw4_points, gw5_points, gw6_points, gw7_points, gw8_points, gw9_points,
                       points_per_million, chance_of_playing_next_round
                FROM players
                ORDER BY overall_total DESC
            """)
            
            players = []
            for row in cursor.fetchall():
                player = {
                    "id": row[0],
                    "name": row[1],
                    "position_name": row[2],
                    "team": row[3],
                    "price": row[4],
                    "availability": row[5],
                    "uncertainty_percent": row[6],
                    "total_gw1_9": row[7],
                    "gw1_9_points": [row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16]],
                    "points_per_million": row[17],
                    "chance_of_playing_next_round": row[18],
                    "ownership": row[6]  # For compatibility with existing frontend
                }
                players.append(player)
            
            return players
            
        except Exception as e:
            print(f"Error fetching players: {e}")
            return []
        finally:
            conn.close()
    
    def get_players_by_position(self, position: str) -> List[Dict[str, Any]]:
        """Get players filtered by position"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT id, name, position_name, team, price, availability, uncertainty_percent, overall_total,
                       gw1_points, gw2_points, gw3_points, gw4_points, gw5_points, gw6_points, gw7_points, gw8_points, gw9_points,
                       points_per_million, chance_of_playing_next_round
                FROM players
                WHERE position_name = ?
                ORDER BY overall_total DESC
            """, (position,))
            
            players = []
            for row in cursor.fetchall():
                player = {
                    "id": row[0],
                    "name": row[1],
                    "position_name": row[2],
                    "team": row[3],
                    "price": row[4],
                    "availability": row[5],
                    "uncertainty_percent": row[6],
                    "total_gw1_9": row[7],
                    "gw1_9_points": [row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16]],
                    "points_per_million": row[17],
                    "chance_of_playing_next_round": row[18],
                    "ownership": row[6]
                }
                players.append(player)
            
            return players
            
        except Exception as e:
            print(f"Error fetching players by position: {e}")
            return []
        finally:
            conn.close()
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams from the database"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT id, name, short_name, strength FROM teams ORDER BY name")
            teams = []
            for row in cursor.fetchall():
                teams.append({
                    "id": row[0],
                    "name": row[1],
                    "short_name": row[2],
                    "strength": row[3]
                })
            return teams
        except Exception as e:
            print(f"Error fetching teams: {e}")
            return []
        finally:
            conn.close()
    
    def get_fixtures(self) -> List[Dict[str, Any]]:
        """Get all fixtures from the database"""
        conn = self.get_connection()
        try:
            cursor = conn.execute("""
                SELECT f.id, f.home_team_id, f.away_team_id, f.home_difficulty, f.away_difficulty, f.gameweek,
                       ht.name as home_team_name, at.name as away_team_name
                FROM fixtures f
                JOIN teams ht ON f.home_team_id = ht.id
                JOIN teams at ON f.away_team_id = at.id
                ORDER BY f.gameweek, f.id
            """)
            
            fixtures = []
            for row in cursor.fetchall():
                fixtures.append({
                    "id": row[0],
                    "home_team_id": row[1],
                    "away_team_id": row[2],
                    "home_difficulty": row[3],
                    "away_difficulty": row[4],
                    "gameweek": row[5],
                    "home_team_name": row[6],
                    "away_team_name": row[7]
                })
            return fixtures
        except Exception as e:
            print(f"Error fetching fixtures: {e}")
            return []
        finally:
            conn.close()

class FPLDataManager:
    """Manages FPL API data fetching and processing"""
    
    @staticmethod
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

# Initialize database and data managers
db_manager = DatabaseManager(DATABASE_PATH)
fpl_data_manager = FPLDataManager()

# Initialize database on startup
db_manager.init_database()

@app.route('/')
def index():
    """Serve the FDR page (original UI)"""
    return render_template_string("""
    <html>
    <head>
        <title>FPL Fixture Difficulty Ratings (FDR)</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.11.3/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
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
            .gw-card {
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
                    <a class="nav-link" href="/squad">Squad</a>
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
                    <strong>1 - Very Easy</strong> (Green)
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #4a7c59;"></span>
                    <strong>2 - Easy</strong> (Light Green)
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #f39c12;"></span>
                    <strong>3 - Medium</strong> (Orange)
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #e74c3c;"></span>
                    <strong>4 - Hard</strong> (Red)
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #8b0000;"></span>
                    <strong>5 - Very Hard</strong> (Dark Red)
                </div>
            </div>
            
            <!-- Weekly Tabs -->
            <ul class="nav nav-tabs" id="gwTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="all-tab" data-bs-toggle="tab" data-bs-target="#all" type="button" role="tab">ALL</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw1-tab" data-bs-toggle="tab" data-bs-target="#gw1" type="button" role="tab">GW1</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw2-tab" data-bs-toggle="tab" data-bs-target="#gw2" type="button" role="tab">GW2</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw3-tab" data-bs-toggle="tab" data-bs-target="#gw3" type="button" role="tab">GW3</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw4-tab" data-bs-toggle="tab" data-bs-target="#gw4" type="button" role="tab">GW4</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw5-tab" data-bs-toggle="tab" data-bs-target="#gw5" type="button" role="tab">GW5</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw6-tab" data-bs-toggle="tab" data-bs-target="#gw6" type="button" role="tab">GW6</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw7-tab" data-bs-toggle="tab" data-bs-target="#gw7" type="button" role="tab">GW7</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw8-tab" data-bs-toggle="tab" data-bs-target="#gw8" type="button" role="tab">GW8</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw9-tab" data-bs-toggle="tab" data-bs-target="#gw9" type="button" role="tab">GW9</button>
                </li>
            </ul>
            
            <!-- Weekly Content -->
            <div class="tab-content" id="gwTabContent">
                <div class="tab-pane fade show active" id="all" role="tabpanel">
                    <div class="gw-card">
                        <h3>All Fixtures (GW1-9)</h3>
                        <div class="table-responsive">
                            <table id="fdrTableAll" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Home Team</th>
                                        <th>Home FDR</th>
                                        <th>Away Team</th>
                                        <th>Away FDR</th>
                                        <th>Gameweek</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- Data will be populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw1" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW1 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable1" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Home Team</th>
                                        <th>Home FDR</th>
                                        <th>Away Team</th>
                                        <th>Away FDR</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- Data will be populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw2" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW2 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable2" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Home Team</th>
                                        <th>Home FDR</th>
                                        <th>Away Team</th>
                                        <th>Away FDR</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- Data will be populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw3" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW3 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable3" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Home Team</th>
                                        <th>Home FDR</th>
                                        <th>Away Team</th>
                                        <th>Away FDR</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- Data will be populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw4" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW4 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable4" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Home Team</th>
                                        <th>Home FDR</th>
                                        <th>Away Team</th>
                                        <th>Away FDR</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- Data will be populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw5" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW5 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable5" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Home Team</th>
                                        <th>Home FDR</th>
                                        <th>Away Team</th>
                                        <th>Away FDR</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- Data will be populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw6" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW6 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable6" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Home Team</th>
                                        <th>Home FDR</th>
                                        <th>Away Team</th>
                                        <th>Away FDR</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- Data will be populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw7" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW7 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable6" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Home Team</th>
                                        <th>Home FDR</th>
                                        <th>Away Team</th>
                                        <th>Away FDR</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- Data will be populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw8" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW8 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable8" class="table table-striped table-hover">
                                <thead>
                                    <th>Home Team</th>
                                    <th>Home FDR</th>
                                    <th>Away Team</th>
                                    <th>Away FDR</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Data will be populated by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="tab-pane fade" id="gw9" role="tabpanel">
                <div class="gw-card">
                    <h3>GW9 Fixtures</h3>
                    <div class="table-responsive">
                        <table id="fdrTable9" class="table table-striped table-hover">
                            <thead>
                                <tr>
                                    <th>Home Team</th>
                                    <th>Home FDR</th>
                                    <th>Away Team</th>
                                    <th>Away FDR</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Data will be populated by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            $(document).ready(function() {
                // Fetch FDR data from API
                fetch('/api/fdr')
                    .then(response => response.json())
                    .then(data => {
                        // Create DataTable for ALL fixtures
                        $('#fdrTableAll').DataTable({
                            data: data,
                            columns: [
                                { data: 'home_team' },
                                { 
                                    data: 'home_difficulty',
                                    render: function(data) {
                                        const colors = ['#234f1e', '#4a7c59', '#f39c12', '#e74c3c', '#8b0000'];
                                        return '<span style="background-color: ' + colors[data-1] + '; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">' + data + '</span>';
                                    }
                                },
                                { data: 'away_team' },
                                { 
                                    data: 'away_difficulty',
                                    render: function(data) {
                                        const colors = ['#234f1e', '#4a7c59', '#f39c12', '#e74c3c', '#8b0000'];
                                        return '<span style="background-color: ' + colors[data-1] + '; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">' + data + '</span>';
                                    }
                                },
                                { data: 'gameweek' }
                            ],
                            order: [[4, 'asc'], [0, 'asc']],
                            pageLength: 25,
                            responsive: true
                        });
                        
                        // Create DataTables for each gameweek
                        for (let gw = 1; gw <= 9; gw++) {
                            const gwData = data.filter(fixture => fixture.gameweek === gw);
                            
                            $('#fdrTable' + gw).DataTable({
                                data: gwData,
                                columns: [
                                    { data: 'home_team' },
                                    { 
                                        data: 'home_difficulty',
                                        render: function(data) {
                                            const colors = ['#234f1e', '#4a7c59', '#f39c12', '#e74c3c', '#8b0000'];
                                            return '<span style="background-color: ' + colors[data-1] + '; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">' + data + '</span>';
                                        }
                                    },
                                    { data: 'away_team' },
                                    { 
                                        data: 'away_difficulty',
                                        render: function(data) {
                                            const colors = ['#234f1e', '#4a7c59', '#f39c12', '#e74c3c', '#8b0000'];
                                            return '<span style="background-color: ' + colors[data-1] + '; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">' + data + '</span>';
                                        }
                                    }
                                ],
                                order: [[0, 'asc']],
                                pageLength: 25,
                                responsive: true
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching FDR data:', error);
                        $('#fdrTableAll tbody').html('<tr><td colspan="5" class="text-center text-danger">Error loading data</td></tr>');
                        for (let gw = 1; gw <= 9; gw++) {
                            $('#fdrTable' + gw + ' tbody').html('<tr><td colspan="4" class="text-center text-danger">Error loading data</td></tr>');
                        }
                    });
            });
        </script>
    </body>
    </html>
    """)

# API Routes
@app.route('/api/players', methods=['GET'])
def get_players():
    """Get all players"""
    players = db_manager.get_all_players()
    return jsonify(players)

@app.route('/api/players/<position>', methods=['GET'])
def get_players_by_position(position):
    """Get players by position"""
    players = db_manager.get_players_by_position(position)
    return jsonify(players)

@app.route('/players')
def players_page():
    """Serve the original players page with DataTables"""
    players = db_manager.get_all_players()
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
            .table th { 
                white-space: normal !important; 
                word-wrap: break-word !important;
                max-width: 80px !important;
                font-size: 0.85em;
                padding: 8px 4px;
                text-align: center;
                vertical-align: middle;
            }
            .table td { 
                vertical-align: middle; 
                font-size: 0.9em;
                padding: 6px 4px;
            }
            .chance-playing {
                font-weight: bold;
            }
            .chance-playing.healthy { color: #28a745; }
            .chance-playing.injured { color: #dc3545; }
            .points-per-million {
                color: #17a2b8;
                font-weight: bold;
            }
            .position-badge {
                font-size: 0.75em;
                padding: 2px 6px;
            }
            .player-name {
                font-weight: bold;
                min-width: 80px;
            }
            .team-name {
                min-width: 60px;
            }
            .price-column {
                min-width: 50px;
            }
            .form-column {
                min-width: 40px;
            }
            .total-column {
                min-width: 60px;
                font-weight: bold;
            }
            .points-per-pound {
                min-width: 50px;
            }
            .chance-column {
                min-width: 60px;
            }
            .gw-column {
                min-width: 35px;
                text-align: center;
            }
            .table {
                table-layout: fixed;
                width: 100%;
            }
            .table th, .table td {
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .dataTables_wrapper .dataTables_scroll {
                overflow-x: auto;
            }
            .dataTables_wrapper .dataTables_scrollHead {
                overflow: visible !important;
            }
            .dataTables_wrapper .dataTables_scrollBody {
                overflow-x: auto;
            }
            .table-responsive {
                overflow-x: auto;
            }
            .dataTables_wrapper {
                font-size: 0.9em;
            }
            
            /* Force DataTable column widths to match sort controls exactly */
            #playersTable th:nth-child(1) { width: 40px !important; min-width: 40px !important; max-width: 40px !important; }
            #playersTable th:nth-child(2) { width: 120px !important; min-width: 120px !important; max-width: 120px !important; }
            #playersTable th:nth-child(3) { width: 60px !important; min-width: 60px !important; max-width: 60px !important; }
            #playersTable th:nth-child(4) { width: 80px !important; min-width: 80px !important; max-width: 80px !important; }
            #playersTable th:nth-child(5) { width: 70px !important; min-width: 70px !important; max-width: 70px !important; }
            #playersTable th:nth-child(6) { width: 50px !important; min-width: 50px !important; max-width: 50px !important; }
            #playersTable th:nth-child(7) { width: 80px !important; min-width: 80px !important; max-width: 80px !important; }
            #playersTable th:nth-child(8) { width: 70px !important; min-width: 70px !important; max-width: 70px !important; }
            #playersTable th:nth-child(9) { width: 80px !important; min-width: 80px !important; max-width: 80px !important; }
            #playersTable th:nth-child(10) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            #playersTable th:nth-child(11) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            #playersTable th:nth-child(12) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            #playersTable th:nth-child(13) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            #playersTable th:nth-child(14) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            #playersTable th:nth-child(15) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            #playersTable th:nth-child(16) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            #playersTable th:nth-child(17) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            #playersTable th:nth-child(18) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            
            /* Ensure sort controls table columns match exactly */
            .sort-controls-table th:nth-child(1) { width: 40px !important; min-width: 40px !important; max-width: 40px !important; }
            .sort-controls-table th:nth-child(2) { width: 120px !important; min-width: 120px !important; max-width: 120px !important; }
            .sort-controls-table th:nth-child(3) { width: 60px !important; min-width: 60px !important; max-width: 60px !important; }
            .sort-controls-table th:nth-child(4) { width: 80px !important; min-width: 80px !important; max-width: 80px !important; }
            .sort-controls-table th:nth-child(5) { width: 70px !important; min-width: 70px !important; max-width: 70px !important; }
            .sort-controls-table th:nth-child(6) { width: 50px !important; min-width: 50px !important; max-width: 50px !important; }
            .sort-controls-table th:nth-child(7) { width: 80px !important; min-width: 80px !important; max-width: 80px !important; }
            .sort-controls-table th:nth-child(8) { width: 70px !important; min-width: 70px !important; max-width: 70px !important; }
            .sort-controls-table th:nth-child(9) { width: 80px !important; min-width: 80px !important; max-width: 80px !important; }
            .sort-controls-table th:nth-child(10) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            .sort-controls-table th:nth-child(11) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            .sort-controls-table th:nth-child(12) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            .sort-controls-table th:nth-child(13) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            .sort-controls-table th:nth-child(14) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            .sort-controls-table th:nth-child(15) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            .sort-controls-table th:nth-child(16) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            .sort-controls-table th:nth-child(17) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            .sort-controls-table th:nth-child(18) { width: 45px !important; min-width: 45px !important; max-width: 45px !important; }
            
            /* Enhanced sorting styles */
            .sort-level {
                display: inline-block;
                background: #007bff;
                color: white;
                border-radius: 50%;
                width: 18px;
                height: 18px;
                line-height: 18px;
                text-align: center;
                font-size: 10px;
                font-weight: bold;
                margin-left: 5px;
                vertical-align: middle;
            }
            
            .sorting_asc .sort-level {
                background: #28a745;
            }
            
            .sorting_desc .sort-level {
                background: #dc3545;
            }
            
            /* Hover effects for sortable columns */
            #playersTable thead th {
                cursor: pointer;
                position: relative;
            }
            
            #playersTable thead th:hover {
                background-color: #e9ecef !important;
            }
            
            /* Filter form styling */
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
                width: 80px;
            }
            
            .filter-form .btn {
                margin-right: 10px;
            }
            
            /* Table styling */
            .table-responsive {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
            }
            
            .table th {
                background-color: #f8f9fa;
                border-color: #dee2e6;
                font-weight: 600;
                color: #2c3e50;
            }
            
            .table td {
                border-color: #dee2e6;
            }
            
            /* DataTables customization */
            .dataTables_wrapper .dataTables_length,
            .dataTables_wrapper .dataTables_filter,
            .dataTables_wrapper .dataTables_info,
            .dataTables_wrapper .dataTables_paginate {
                margin: 10px 0;
            }
            
            .dataTables_wrapper .dataTables_paginate .paginate_button {
                border-radius: 5px;
                margin: 0 2px;
            }
            
            .dataTables_wrapper .dataTables_paginate .paginate_button.current {
                background: #007bff !important;
                border-color: #007bff !important;
                color: white !important;
            }
            
            .dataTables_wrapper .dataTables_paginate .paginate_button:hover {
                background: #0056b3 !important;
                border-color: #0056b3 !important;
                color: white !important;
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
                    <a class="nav-link" href="/squad">Squad</a>
                </div>
            </div>
        </nav>
        
        <div class="container-fluid">
            <h1 class="text-center">FPL Players - Expected Points (GW1-9)</h1>
            
            <!-- Filter Form -->
            <div class="filter-form">
                <div class="row">
                    <div class="col-md-12">
                        <h5 class="mb-3">Filters:</h5>
                        <div class="d-flex flex-wrap align-items-center">
                            <label>Position:</label>
                            <input type="text" id="positionFilter" placeholder="e.g., Midfielder">
                            
                            <label>Team:</label>
                            <input type="text" id="teamFilter" placeholder="e.g., Liverpool">
                            
                            <label>Max Price:</label>
                            <input type="number" id="priceFilter" placeholder="e.g., 10.0" step="0.1">
                            
                            <label>Min Chance:</label>
                            <input type="number" id="chanceFilter" placeholder="e.g., 75" min="0" max="100">
                            
                            <label>Min Points/£:</label>
                            <input type="number" id="pointsPerPoundFilter" placeholder="e.g., 3.0" step="0.1">
                            
                            <label>Min Total Points:</label>
                            <input type="number" id="totalPointsFilter" placeholder="e.g., 25.0" step="0.1">
                            
                            <label>Min Form:</label>
                            <input type="number" id="formFilter" placeholder="e.g., 3.0" step="0.1">
                            
                            <label>Min Ownership:</label>
                            <input type="number" id="ownershipFilter" placeholder="e.g., 20" min="0" max="100">
                            
                            <button type="button" class="btn btn-primary" id="clearFilters">Clear All Filters</button>
                        </div>
                        <div class="mt-2">
                            <span id="filterInfo" class="text-muted">Showing all players</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Sort Controls Table -->
            <div class="table-responsive mb-3">
                <table class="table table-sm sort-controls-table">
                    <thead>
                        <tr>
                            <th>Sort Level</th>
                            <th>Player Name</th>
                            <th>Position</th>
                            <th>Team</th>
                            <th>Price</th>
                            <th>Form</th>
                            <th>Total Points</th>
                            <th>Points/£</th>
                            <th>Chance</th>
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
                        <tr>
                            <td><span class="sort-level">1</span></td>
                            <td>Sort by Name</td>
                            <td>Sort by Position</td>
                            <td>Sort by Team</td>
                            <td>Sort by Price</td>
                            <td>Sort by Form</td>
                            <td>Sort by Total Points</td>
                            <td>Sort by Points/£</td>
                            <td>Sort by Chance</td>
                            <td>Sort by GW1</td>
                            <td>Sort by GW2</td>
                            <td>Sort by GW3</td>
                            <td>Sort by GW4</td>
                            <td>Sort by GW5</td>
                            <td>Sort by GW6</td>
                            <td>Sort by GW7</td>
                            <td>Sort by GW8</td>
                            <td>Sort by GW9</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- Players Table -->
            <div class="table-responsive">
                <table id="playersTable" class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Sort Level</th>
                            <th>Player Name</th>
                            <th>Position</th>
                            <th>Team</th>
                            <th>Price</th>
                            <th>Form</th>
                            <th>Total Points</th>
                            <th>Points/£</th>
                            <th>Chance</th>
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
                        <!-- Data will be populated by JavaScript -->
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            $(document).ready(function() {
                // Fetch players data from API
                fetch('/api/players')
                    .then(response => response.json())
                    .then(data => {
                        const table = $('#playersTable').DataTable({
                            data: data,
                            columns: [
                                { 
                                    data: null,
                                    render: function(data, type, row, meta) {
                                        return '<span class="sort-level">' + (meta.row + 1) + '</span>';
                                    }
                                },
                                { 
                                    data: 'name',
                                    className: 'player-name'
                                },
                                { 
                                    data: 'position_name',
                                    render: function(data) {
                                        const classes = {
                                            'Goalkeeper': 'gk',
                                            'Defender': 'def',
                                            'Midfielder': 'mid',
                                            'Forward': 'fwd'
                                        };
                                        return '<span class="position-badge ' + (classes[data] || '') + '">' + data + '</span>';
                                    }
                                },
                                { 
                                    data: 'team',
                                    className: 'team-name'
                                },
                                { 
                                    data: 'price',
                                    className: 'price-column',
                                    render: function(data) {
                                        return '£' + data.toFixed(1) + 'm';
                                    }
                                },
                                { 
                                    data: 'points_per_million',
                                    className: 'form-column',
                                    render: function(data) {
                                        return data.toFixed(2);
                                    }
                                },
                                { 
                                    data: 'total_gw1_9',
                                    className: 'total-column',
                                    render: function(data) {
                                        return data.toFixed(1);
                                    }
                                },
                                { 
                                    data: 'points_per_million',
                                    className: 'points-per-pound',
                                    render: function(data) {
                                        return data.toFixed(2);
                                    }
                                },
                                { 
                                    data: 'chance_of_playing_next_round',
                                    className: 'chance-column',
                                    render: function(data) {
                                        if (data >= 75) {
                                            return '<span class="chance-playing healthy">' + data + '%</span>';
                                        } else if (data >= 50) {
                                            return '<span class="chance-playing" style="color: #ffc107;">' + data + '%</span>';
                                        } else {
                                            return '<span class="chance-playing injured">' + data + '%</span>';
                                        }
                                    }
                                },
                                { 
                                    data: 'gw1_9_points',
                                    render: function(data, type, row, meta) {
                                        return data[0] ? data[0].toFixed(1) : '0.0';
                                    },
                                    className: 'gw-column'
                                },
                                { 
                                    data: 'gw1_9_points',
                                    render: function(data, type, row, meta) {
                                        return data[1] ? data[1].toFixed(1) : '0.0';
                                    },
                                    className: 'gw-column'
                                },
                                { 
                                    data: 'gw1_9_points',
                                    render: function(data, type, row, meta) {
                                        return data[2] ? data[2].toFixed(1) : '0.0';
                                    },
                                    className: 'gw-column'
                                },
                                { 
                                    data: 'gw1_9_points',
                                    render: function(data, type, row, meta) {
                                        return data[3] ? data[3].toFixed(1) : '0.0';
                                    },
                                    className: 'gw-column'
                                },
                                { 
                                    data: 'gw1_9_points',
                                    render: function(data, type, row, meta) {
                                        return data[4] ? data[4].toFixed(1) : '0.0';
                                    },
                                    className: 'gw-column'
                                },
                                { 
                                    data: 'gw1_9_points',
                                    render: function(data, type, row, meta) {
                                        return data[5] ? data[5].toFixed(1) : '0.0';
                                    },
                                    className: 'gw-column'
                                },
                                { 
                                    data: 'gw1_9_points',
                                    render: function(data, type, row, meta) {
                                        return data[6] ? data[6].toFixed(1) : '0.0';
                                    },
                                    className: 'gw-column'
                                },
                                { 
                                    data: 'gw1_9_points',
                                    render: function(data, type, row, meta) {
                                        return data[7] ? data[7].toFixed(1) : '0.0';
                                    },
                                    className: 'gw-column'
                                },
                                { 
                                    data: 'gw1_9_points',
                                    render: function(data, type, row, meta) {
                                        return data[8] ? data[8].toFixed(1) : '0.0';
                                    },
                                    className: 'gw-column'
                                }
                            ],
                            order: [[6, 'desc']], // Sort by total points by default
                            pageLength: 25,
                            responsive: true,
                            scrollX: true
                        });
                        
                        // Apply filters
                        $('#positionFilter').on('input', function() {
                            table.column(2).search(this.value).draw();
                        });
                        
                        $('#teamFilter').on('input', function() {
                            table.column(3).search(this.value).draw();
                        });
                        
                        $('#priceFilter').on('input', function() {
                            var maxPrice = parseFloat($(this).val());
                            if (isNaN(maxPrice)) return;
                            
                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var price = parseFloat(data[4].replace('£', '').replace('m', ''));
                                return price <= maxPrice;
                            });
                            table.draw();
                        });
                        
                        $('#chanceFilter').on('input', function() {
                            var minChance = parseInt($(this).val());
                            if (isNaN(minChance)) return;
                            
                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var chanceText = data[8];
                                var chance = parseInt(chanceText.match(/\d+/)[0]);
                                return chance >= minChance;
                            });
                            table.draw();
                        });
                        
                        $('#pointsPerPoundFilter').on('input', function() {
                            var minPointsPerPound = parseFloat($(this).val());
                            if (isNaN(minPointsPerPound)) return;
                            
                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var pointsPerPound = parseFloat(data[7]);
                                return pointsPerPound >= minPointsPerPound;
                            });
                            table.draw();
                        });
                        
                        $('#totalPointsFilter').on('input', function() {
                            var minTotalPoints = parseFloat($(this).val());
                            if (isNaN(minTotalPoints)) return;
                            
                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var totalPoints = parseFloat(data[6]);
                                return totalPoints >= minTotalPoints;
                            });
                            table.draw();
                        });
                        
                        $('#formFilter').on('input', function() {
                            var minForm = parseFloat($(this).val());
                            if (isNaN(minForm)) return;
                            
                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var form = parseFloat(data[5]);
                                return form >= minForm;
                            });
                            table.draw();
                        });
                        
                        $('#ownershipFilter').on('input', function() {
                            var minOwnership = parseFloat($(this).val());
                            if (isNaN(minOwnership)) return;
                            
                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var player = data.find(p => p.name === data[1]);
                                if (player && player.ownership) {
                                    var ownership = parseFloat(player.ownership.replace('%', ''));
                                    return ownership >= minOwnership;
                                }
                                return true;
                            });
                            table.draw();
                        });
                        
                        // Clear all filters
                        $('#clearFilters').on('click', function() {
                            $('#positionFilter').val('');
                            $('#teamFilter').val('');
                            $('#priceFilter').val('');
                            $('#chanceFilter').val('');
                            $('#pointsPerPoundFilter').val('');
                            $('#totalPointsFilter').val('');
                            $('#formFilter').val('');
                            $('#ownershipFilter').val('');
                            $.fn.dataTable.ext.search.splice(0, $.fn.dataTable.ext.search.length);
                            table.draw();
                        });
                    })
                    .catch(error => {
                        console.error('Error fetching players data:', error);
                        $('#playersTable tbody').html('<tr><td colspan="18" class="text-center text-danger">Error loading data</td></tr>');
                    });
            });
        </script>
    </body>
    </html>
    """)

@app.route('/squad')
def squad_page():
    """Serve the original squad page with weekly breakdown"""
    return render_template_string("""
    <html>
    <head>
        <title>FPL Optimal Squad - GW1-9</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <style>
            body { background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .navbar-brand { font-weight: bold; color: #2c3e50 !important; }
            .nav-link { color: #34495e !important; font-weight: 500; }
            .nav-link.active { background-color: #3498db !important; color: white !important; border-radius: 5px; }
            .nav-link:hover { color: #3498db !important; }
            h1, h2, h3 { color: #2c3e50; font-weight: 600; margin-bottom: 1.5rem; }
            .summary-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem; }
            .gw-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem; }
            .position-badge { font-size: 0.8em; padding: 4px 8px; border-radius: 12px; color: white; font-weight: bold; }
            .gk { background-color: #dc3545; }
            .def { background-color: #007bff; }
            .mid { background-color: #28a745; }
            .fwd { background-color: #ffc107; color: #212529; }
            .nav-tabs .nav-link { color: #495057; }
            .nav-tabs .nav-link.active { color: #007bff; font-weight: 600; }
            .points-display { font-size: 1.2em; font-weight: bold; color: #28a745; }
            .budget-info { font-size: 1.1em; color: #6c757d; }
        </style>
    </head>
    <body class="p-4">
        <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
            <div class="container-fluid">
                <span class="navbar-brand">FPL Tools</span>
                <div class="navbar-nav">
                    <a class="nav-link" href="/">FDR Table</a>
                    <a class="nav-link" href="/players">Players</a>
                    <a class="nav-link active" href="/squad">Squad</a>
                </div>
            </div>
        </nav>
        
        <div class="container-fluid">
            <h1 class="text-center mb-4">FPL Optimal Squad - GW1-9</h1>
            
            <!-- Summary Section -->
            <div class="summary-card">
                <div class="row">
                    <div class="col-md-3">
                        <h4>Total Points (GW1-9)</h4>
                        <div class="points-display" id="totalPoints">Loading...</div>
                    </div>
                    <div class="col-md-3">
                        <h4>Squad Value</h4>
                        <div class="budget-info" id="squadValue">Loading...</div>
                    </div>
                    <div class="col-md-3">
                        <h4>Remaining Budget</h4>
                        <div class="budget-info" id="remainingBudget">Loading...</div>
                    </div>
                    <div class="col-md-3">
                        <h4>Formation</h4>
                        <div class="budget-info">4-4-2</div>
                    </div>
                </div>
            </div>
            
            <!-- Weekly Tabs -->
            <ul class="nav nav-tabs" id="gwTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="gw1-tab" data-bs-toggle="tab" data-bs-target="#gw1" type="button" role="tab">GW1</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw2-tab" data-bs-toggle="tab" data-bs-target="#gw2" type="button" role="tab">GW2</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw3-tab" data-bs-toggle="tab" data-bs-target="#gw3" type="button" role="tab">GW3</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw4-tab" data-bs-toggle="tab" data-bs-target="#gw4" type="button" role="tab">GW4</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw5-tab" data-bs-toggle="tab" data-bs-target="#gw5" type="button" role="tab">GW5</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw6-tab" data-bs-toggle="tab" data-bs-target="#gw6" type="button" role="tab">GW6</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw7-tab" data-bs-toggle="tab" data-bs-target="#gw7" type="button" role="tab">GW7</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw8-tab" data-bs-toggle="tab" data-bs-target="#gw8" type="button" role="tab">GW8</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw9-tab" data-bs-toggle="tab" data-bs-target="#gw9" type="button" role="tab">GW9</button>
                </li>
            </ul>
            
            <!-- Weekly Content -->
            <div class="tab-content" id="gwTabContent">
                <div class="tab-pane fade show active" id="gw1" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW1 - 4-4-2</h3>
                        <div id="gw1Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw2" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW2 - 4-4-2</h3>
                        <div id="gw2Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw3" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW3 - 4-4-2</h3>
                        <div id="gw3Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw4" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW4 - 4-4-2</h3>
                        <div id="gw4Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw5" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW5 - 4-4-2</h3>
                        <div id="gw5Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw6" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW6 - 4-4-2</h3>
                        <div id="gw6Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw7" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW7 - 4-4-2</h3>
                        <div id="gw7Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw8" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW8 - 4-4-2</h3>
                        <div id="gw8Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw9" role="tabpanel">
                    <div class="gw-card">
                        <h3>GW9 - 4-4-2</h3>
                        <div id="gw9Content">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            $(document).ready(function() {
                fetch('/api/optimize-team', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ budget: 100.0, formation: '4-4-2' })
                })
                .then(response => response.json())
                .then(data => {
                    let totalPoints = 0;
                    let totalValue = 0;
                    
                    const allPlayers = [
                        ...data.goalkeepers,
                        ...data.defenders, 
                        ...data.midfielders,
                        ...data.forwards
                    ];
                    
                    allPlayers.forEach(p => {
                        totalPoints += p.total_gw1_9;
                        totalValue += p.price;
                    });
                    
                    $('#totalPoints').text(totalPoints.toFixed(1));
                    $('#squadValue').text('£' + totalValue.toFixed(1) + 'M');
                    $('#remainingBudget').text('£' + (100.0 - totalValue).toFixed(1) + 'M');
                    
                    // Generate weekly content for each gameweek
                    for (let gw = 1; gw <= 9; gw++) {
                        let gwContent = '<div class="row">';
                        gwContent += '<div class="col-md-4"><h5>Expected Points: <span class="points-display">' + 
                            allPlayers.reduce((sum, p) => sum + (p['gw' + gw + '_points'] || 0), 0).toFixed(1) + '</span></h5></div>';
                        gwContent += '<div class="col-md-8"><h5>Team:</h5></div>';
                        gwContent += '</div>';
                        
                        // Add players by position
                        gwContent += '<div class="row">';
                        gwContent += '<div class="col-md-3"><h6>Goalkeepers</h6>';
                        data.goalkeepers.forEach(p => {
                            const gwPoints = p['gw' + gw + '_points'] || 0;
                            gwContent += '<div class="mb-2"><span class="position-badge gk">GK</span> ' + p.name + ' (' + p.team + ') - ' + gwPoints.toFixed(1) + ' pts</div>';
                        });
                        gwContent += '</div>';
                        
                        gwContent += '<div class="col-md-3"><h6>Defenders</h6>';
                        data.defenders.forEach(p => {
                            const gwPoints = p['gw' + gw + '_points'] || 0;
                            gwContent += '<div class="mb-2"><span class="position-badge def">DEF</span> ' + p.name + ' (' + p.team + ') - ' + gwPoints.toFixed(1) + ' pts</div>';
                        });
                        gwContent += '</div>';
                        
                        gwContent += '<div class="col-md-3"><h6>Midfielders</h6>';
                        data.midfielders.forEach(p => {
                            const gwPoints = p['gw' + gw + '_points'] || 0;
                            gwContent += '<div class="mb-2"><span class="position-badge mid">MID</span> ' + p.name + ' (' + p.team + ') - ' + gwPoints.toFixed(1) + ' pts</div>';
                        });
                        gwContent += '</div>';
                        
                        gwContent += '<div class="col-md-3"><h6>Forwards</h6>';
                        data.forwards.forEach(p => {
                            const gwPoints = p['gw' + gw + '_points'] || 0;
                            gwContent += '<div class="mb-2"><span class="position-badge fwd">FWD</span> ' + p.name + ' (' + p.team + ') - ' + gwPoints.toFixed(1) + ' pts</div>';
                        });
                        gwContent += '</div></div>';
                        
                        $('#gw' + gw + 'Content').html(gwContent);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    $('#totalPoints').text('Error');
                    $('#squadValue').text('Error');
                    $('#remainingBudget').text('Error');
                });
            });
        </script>
    </body>
    </html>
    """)

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get all teams"""
    teams = db_manager.get_teams()
    return jsonify(teams)

@app.route('/api/fixtures', methods=['GET'])
def get_fixtures():
    """Get all fixtures"""
    fixtures = db_manager.get_fixtures()
    return jsonify(fixtures)

@app.route('/api/fdr', methods=['GET'])
def get_fdr():
    """Get FDR (Fixture Difficulty Rating) data"""
    try:
        team_map, team_abbr, fixtures = fpl_data_manager.fetch_fpl_data()
        
        # Process fixtures for FDR
        fdr_data = []
        for fixture in fixtures:
            home_team = team_map.get(fixture.get("team_h"), "Unknown")
            away_team = team_map.get(fixture.get("team_a"), "Unknown")
            home_difficulty = fixture.get("team_h_difficulty", 0)
            away_difficulty = fixture.get("team_a_difficulty", 0)
            gameweek = fixture.get("event", 0)
            
            fdr_data.append({
                "home_team": home_team,
                "away_team": away_team,
                "home_difficulty": home_difficulty,
                "away_difficulty": away_difficulty,
                "gameweek": gameweek
            })
        
        return jsonify(fdr_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/optimize-team', methods=['POST'])
def optimize_team():
    """Optimize team selection based on budget and constraints"""
    try:
        data = request.get_json()
        budget = data.get('budget', 100.0)
        formation = data.get('formation', '4-4-2')
        
        # Get all players
        players = db_manager.get_all_players()
        
        # Simple optimization algorithm (can be enhanced)
        # For now, return top players within budget
        affordable_players = [p for p in players if p['price'] <= budget]
        affordable_players.sort(key=lambda x: x['points_per_million'], reverse=True)
        
        # Select players based on formation
        optimized_team = {
            'goalkeepers': [p for p in affordable_players if p['position_name'] == 'Goalkeeper'][:2],
            'defenders': [p for p in affordable_players if p['position_name'] == 'Defender'][:5],
            'midfielders': [p for p in affordable_players if p['position_name'] == 'Midfielder'][:5],
            'forwards': [p for p in affordable_players if p['position_name'] == 'Forward'][:3]
        }
        
        return jsonify(optimized_team)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
