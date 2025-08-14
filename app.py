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
                    code TEXT NOT NULL,
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
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, short_name, code, strength
                FROM teams
                ORDER BY name
            """)
            
            teams = []
            for row in cursor.fetchall():
                teams.append({
                    'id': row[0],
                    'name': row[1],
                    'short_name': row[2],
                    'code': row[3],
                    'strength': row[4]
                })
            
            return teams
        except Exception as e:
            print(f"Error getting teams: {e}")
            return []
        finally:
            if conn:
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
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
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
                transition: all 0.3s ease;
            }
            .navbar-brand:hover {
                transform: scale(1.05);
                color: #3498db !important;
            }
            .nav-link {
                color: #34495e !important;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            .nav-link.active {
                background-color: #3498db !important;
                color: white !important;
                border-radius: 5px;
                transform: scale(1.05);
            }
            .nav-link:hover {
                color: #3498db !important;
                transform: translateY(-2px);
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
                transition: all 0.3s ease;
            }
            .filter-form:hover {
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                transform: translateY(-2px);
            }
            
            .filter-form label {
                font-weight: 500;
                margin-bottom: 8px;
                color: #2c3e50;
            }
            
            .filter-form select, .filter-form input {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 8px 12px;
                transition: all 0.3s ease;
                width: 100%;
            }
            
            .filter-form select:focus, .filter-form input:focus {
                border-color: #007bff;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,0.25);
                transform: scale(1.02);
            }
            
            .filter-form .btn {
                transition: all 0.3s ease;
                border-radius: 8px;
            }
            
            .filter-form .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .gw-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
                transition: all 0.3s ease;
            }
            .gw-card:hover {
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                transform: translateY(-2px);
            }
            .legend {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
                transition: all 0.3s ease;
            }
            .legend:hover {
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                transform: translateY(-2px);
            }
            .legend-item {
                display: inline-block;
                margin-right: 20px;
                margin-bottom: 10px;
                transition: all 0.3s ease;
            }
            .legend-item:hover {
                transform: scale(1.05);
            }
            .legend-color {
                display: inline-block;
                width: 20px;
                height: 20px;
                border-radius: 3px;
                margin-right: 8px;
                border: 1px solid #ddd;
                transition: all 0.3s ease;
            }
            .legend-color:hover {
                transform: scale(1.2);
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }
            
            /* Enhanced Tab Styling */
            .nav-tabs .nav-link {
                color: #495057;
                transition: all 0.3s ease;
                border-radius: 8px 8px 0 0;
            }
            .nav-tabs .nav-link.active {
                color: #007bff;
                font-weight: 600;
                transform: scale(1.05);
                background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                color: white;
                border-color: #007bff;
            }
            .nav-tabs .nav-link:hover {
                transform: translateY(-2px);
                background-color: #e9ecef;
            }
            
            /* Enhanced Table Styling */
            .table-responsive {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
                transition: all 0.3s ease;
            }
            .table-responsive:hover {
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            }
            
            table.dataTable thead th {
                white-space: normal;
                background-color: #f8f9fa;
                border-color: #dee2e6;
                font-weight: 600;
                color: #2c3e50;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            table.dataTable thead th:hover {
                background-color: #e9ecef !important;
                transform: scale(1.02);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            table.dataTable td:first-child {
                white-space: nowrap;
                max-width: 75px;
                overflow: hidden;
                text-overflow: ellipsis;
                font-weight: 600;
                color: #2c3e50;
                transition: all 0.3s ease;
            }
            
            table.dataTable tbody tr {
                transition: all 0.3s ease;
            }
            
            table.dataTable tbody tr:hover {
                background-color: #f8f9fa !important;
                transform: scale(1.01);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            /* Enhanced FDR Badge Styling */
            .fdr-badge {
                background: linear-gradient(135deg, var(--fdr-color) 0%, var(--fdr-color-dark) 100%);
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: bold;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .fdr-badge:hover {
                transform: scale(1.1);
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            
            .fdr-badge::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                transition: left 0.5s;
            }
            
            .fdr-badge:hover::before {
                left: 100%;
            }
            
            /* Animation Classes */
            .fade-in {
                animation: fadeIn 0.5s ease-in;
            }
            
            .slide-up {
                animation: slideUp 0.3s ease-out;
            }
            
            .bounce-in {
                animation: bounceIn 0.6s ease-out;
            }
            
            .scale-in {
                animation: scaleIn 0.4s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideUp {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            @keyframes bounceIn {
                0% { transform: scale(0.3); opacity: 0; }
                50% { transform: scale(1.05); }
                70% { transform: scale(0.9); }
                100% { transform: scale(1); opacity: 1; }
            }
            
            @keyframes scaleIn {
                from { transform: scale(0.8); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
            
            /* Enhanced Button Styles */
            .btn {
                transition: all 0.3s ease;
                border-radius: 8px;
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                border: none;
            }
            
            .btn-success {
                background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
                border: none;
            }
            
            .btn-warning {
                background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
                border: none;
                color: #212529;
            }
            
            .btn-info {
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                border: none;
            }
            
            /* Enhanced DataTables Styling */
            .dataTables_wrapper .dataTables_length,
            .dataTables_wrapper .dataTables_filter,
            .dataTables_wrapper .dataTables_info,
            .dataTables_wrapper .dataTables_paginate {
                margin: 10px 0;
            }
            
            .dataTables_wrapper .dataTables_paginate .paginate_button {
                border-radius: 5px;
                margin: 0 2px;
                transition: all 0.3s ease;
            }
            
            .dataTables_wrapper .dataTables_paginate .paginate_button.current {
                background: #007bff !important;
                border-color: #007bff !important;
                color: white !important;
                transform: scale(1.1);
            }
            
            .dataTables_wrapper .dataTables_paginate .paginate_button:hover {
                background: #0056b3 !important;
                border-color: #0056b3 !important;
                color: white !important;
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body class="p-4">
        <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
            <div class="container-fluid">
                <span class="navbar-brand"><i class="fas fa-chart-line"></i> FPL Tools</span>
                <div class="navbar-nav">
                    <a class="nav-link active" href="/">FDR Table</a>
                    <a class="nav-link" href="/players">Players</a>
                    <a class="nav-link" href="/squad">Squad</a>
                </div>
            </div>
        </nav>
        
        <div class="container-fluid">
            <h1 class="text-center fade-in"><i class="fas fa-trophy"></i> Fixture Difficulty Ratings (FDR)</h1>
            
            <!-- Enhanced Filters Section -->
            <div class="filter-form slide-up">
                <h5 class="mb-3"><i class="fas fa-filter"></i> FDR Filters</h5>
                <div class="row mb-3">
                    <div class="col-md-3">
                        <label for="homeTeamFilter" class="form-label">Home Team:</label>
                        <select id="homeTeamFilter" class="form-select">
                            <option value="">All Home Teams</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label for="awayTeamFilter" class="form-label">Away Team:</label>
                        <select id="awayTeamFilter" class="form-select">
                            <option value="">All Away Teams</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label for="difficultyFilter" class="form-label">Difficulty Level:</label>
                        <select id="difficultyFilter" class="form-select">
                            <option value="">All Difficulties</option>
                            <option value="1">1 - Very Easy</option>
                            <option value="2">2 - Easy</option>
                            <option value="3">3 - Medium</option>
                            <option value="4">4 - Hard</option>
                            <option value="5">5 - Very Hard</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label for="gameweekFilter" class="form-label">Gameweek:</label>
                        <select id="gameweekFilter" class="form-select">
                            <option value="">All Gameweeks</option>
                            <option value="1">GW1</option>
                            <option value="2">GW2</option>
                            <option value="3">GW3</option>
                            <option value="4">GW4</option>
                            <option value="5">GW5</option>
                            <option value="6">GW6</option>
                            <option value="7">GW7</option>
                            <option value="8">GW8</option>
                            <option value="9">GW9</option>
                        </select>
                    </div>
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-3">
                        <label for="homeDifficultyFilter" class="form-label">Home FDR:</label>
                        <select id="homeDifficultyFilter" class="form-select">
                            <option value="">All Home FDRs</option>
                            <option value="1">1 - Very Easy</option>
                            <option value="2">2 - Easy</option>
                            <option value="3">3 - Medium</option>
                            <option value="4">4 - Hard</option>
                            <option value="5">5 - Very Hard</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label for="awayDifficultyFilter" class="form-label">Away FDR:</label>
                        <select id="awayDifficultyFilter" class="form-select">
                            <option value="">All Away FDRs</option>
                            <option value="1">1 - Very Easy</option>
                            <option value="2">2 - Easy</option>
                            <option value="3">3 - Medium</option>
                            <option value="4">4 - Hard</option>
                            <option value="5">5 - Very Hard</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label for="combinedDifficultyFilter" class="form-label">Combined Difficulty:</label>
                        <select id="combinedDifficultyFilter" class="form-select">
                            <option value="">All Combined</option>
                            <option value="2">2 (1+1)</option>
                            <option value="3">3 (1+2, 2+1)</option>
                            <option value="4">4 (1+3, 2+2, 3+1)</option>
                            <option value="5">5 (1+4, 2+3, 3+2, 4+1)</option>
                            <option value="6">6 (1+5, 2+4, 3+3, 4+2, 5+1)</option>
                            <option value="7">7 (2+5, 3+4, 4+3, 5+2)</option>
                            <option value="8">8 (3+5, 4+4, 5+3)</option>
                            <option value="9">9 (4+5, 5+4)</option>
                            <option value="10">10 (5+5)</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label for="clearFilters" class="form-label">&nbsp;</label>
                        <button id="clearFilters" class="btn btn-warning w-100">
                            <i class="fas fa-times"></i> Clear All Filters
                        </button>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12">
                        <div id="filterInfo" class="text-muted">
                            <i class="fas fa-info-circle"></i> Showing all fixtures. Use filters above to narrow down results.
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- FDR Legend -->
            <div class="legend slide-up">
                <h5 class="mb-3"><i class="fas fa-palette"></i> FDR Color Legend:</h5>
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
                    <button class="nav-link active" id="all-tab" data-bs-toggle="tab" data-bs-target="#all" type="button" role="tab">
                        <i class="fas fa-list"></i> ALL
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw1-tab" data-bs-toggle="tab" data-bs-target="#gw1" type="button" role="tab">
                        <i class="fas fa-calendar-day"></i> GW1
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw2-tab" data-bs-toggle="tab" data-bs-target="#gw2" type="button" role="tab">
                        <i class="fas fa-calendar-day"></i> GW2
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw3-tab" data-bs-toggle="tab" data-bs-target="#gw3" type="button" role="tab">
                        <i class="fas fa-calendar-day"></i> GW3
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw4-tab" data-bs-toggle="tab" data-bs-target="#gw4" type="button" role="tab">
                        <i class="fas fa-calendar-day"></i> GW4
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw5-tab" data-bs-toggle="tab" data-bs-target="#gw5" type="button" role="tab">
                        <i class="fas fa-calendar-day"></i> GW5
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw6-tab" data-bs-toggle="tab" data-bs-target="#gw6" type="button" role="tab">
                        <i class="fas fa-calendar-day"></i> GW6
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw7-tab" data-bs-toggle="tab" data-bs-target="#gw7" type="button" role="tab">
                        <i class="fas fa-calendar-day"></i> GW7
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw8-tab" data-bs-toggle="tab" data-bs-target="#gw8" type="button" role="tab">
                        <i class="fas fa-calendar-day"></i> GW8
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gw9-tab" data-bs-toggle="tab" data-bs-target="#gw9" type="button" role="tab">
                        <i class="fas fa-calendar-day"></i> GW9
                    </button>
                </li>
            </ul>
            
            <!-- Weekly Content -->
            <div class="tab-content" id="gwTabContent">
                <div class="tab-pane fade show active" id="all" role="tabpanel">
                    <div class="gw-card scale-in">
                        <h3><i class="fas fa-list"></i> All Fixtures (GW1-9)</h3>
                        <div class="table-responsive">
                            <table id="fdrTableAll" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-home"></i> Home Team</th>
                                        <th><i class="fas fa-star"></i> Home FDR</th>
                                        <th><i class="fas fa-plane"></i> Away Team</th>
                                        <th><i class="fas fa-star"></i> Away FDR</th>
                                        <th><i class="fas fa-calendar"></i> Gameweek</th>
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
                    <div class="gw-card scale-in">
                        <h3><i class="fas fa-calendar-day"></i> GW1 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable1" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-home"></i> Home Team</th>
                                        <th><i class="fas fa-star"></i> Home FDR</th>
                                        <th><i class="fas fa-plane"></i> Away Team</th>
                                        <th><i class="fas fa-star"></i> Away FDR</th>
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
                    <div class="gw-card scale-in">
                        <h3><i class="fas fa-calendar-day"></i> GW2 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable2" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-home"></i> Home Team</th>
                                        <th><i class="fas fa-star"></i> Home FDR</th>
                                        <th><i class="fas fa-plane"></i> Away Team</th>
                                        <th><i class="fas fa-star"></i> Away FDR</th>
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
                    <div class="gw-card scale-in">
                        <h3><i class="fas fa-calendar-day"></i> GW3 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable3" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-home"></i> Home Team</th>
                                        <th><i class="fas fa-star"></i> Home FDR</th>
                                        <th><i class="fas fa-plane"></i> Away Team</th>
                                        <th><i class="fas fa-star"></i> Away FDR</th>
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
                    <div class="gw-card scale-in">
                        <h3><i class="fas fa-calendar-day"></i> GW4 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable4" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-home"></i> Home Team</th>
                                        <th><i class="fas fa-star"></i> Home FDR</th>
                                        <th><i class="fas fa-plane"></i> Away Team</th>
                                        <th><i class="fas fa-star"></i> Away FDR</th>
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
                    <div class="gw-card scale-in">
                        <h3><i class="fas fa-calendar-day"></i> GW5 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable5" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-home"></i> Home Team</th>
                                        <th><i class="fas fa-star"></i> Home FDR</th>
                                        <th><i class="fas fa-plane"></i> Away Team</th>
                                        <th><i class="fas fa-star"></i> Away FDR</th>
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
                    <div class="gw-card scale-in">
                        <h3><i class="fas fa-calendar-day"></i> GW6 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable6" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-home"></i> Home Team</th>
                                        <th><i class="fas fa-star"></i> Home FDR</th>
                                        <th><i class="fas fa-plane"></i> Away Team</th>
                                        <th><i class="fas fa-star"></i> Away FDR</th>
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
                    <div class="gw-card scale-in">
                        <h3><i class="fas fa-calendar-day"></i> GW7 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable7" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-home"></i> Home Team</th>
                                        <th><i class="fas fa-star"></i> Home FDR</th>
                                        <th><i class="fas fa-plane"></i> Away Team</th>
                                        <th><i class="fas fa-star"></i> Away FDR</th>
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
                    <div class="gw-card scale-in">
                        <h3><i class="fas fa-calendar-day"></i> GW8 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable8" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-home"></i> Home Team</th>
                                        <th><i class="fas fa-star"></i> Home FDR</th>
                                        <th><i class="fas fa-plane"></i> Away Team</th>
                                        <th><i class="fas fa-star"></i> Away FDR</th>
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
                    <div class="gw-card scale-in">
                        <h3><i class="fas fa-calendar-day"></i> GW9 Fixtures</h3>
                        <div class="table-responsive">
                            <table id="fdrTable9" class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-home"></i> Home Team</th>
                                        <th><i class="fas fa-star"></i> Home FDR</th>
                                        <th><i class="fas fa-plane"></i> Away Team</th>
                                        <th><i class="fas fa-star"></i> Away FDR</th>
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
        </div>
        
        <script>
            $(document).ready(function() {
                let allFdrData = [];
                let currentTables = {};
                
                // Fetch FDR data from API
                fetch('/api/fdr')
                    .then(response => response.json())
                    .then(data => {
                        allFdrData = data;
                        
                        // Populate team filters
                        populateTeamFilters(data);
                        
                        // Create DataTable for ALL fixtures
                        currentTables.all = $('#fdrTableAll').DataTable({
                            data: data,
                            columns: [
                                { data: 'home_team' },
                                {
                                    data: 'home_difficulty',
                                    render: function(data) {
                                        const colors = ['#234f1e', '#4a7c59', '#f39c12', '#e74c3c', '#8b0000'];
                                        const darkColors = ['#1a3f18', '#3d6a4a', '#d6890f', '#c0392b', '#6b0000'];
                                        return `<span class="fdr-badge" style="--fdr-color: ${colors[data-1]}; --fdr-color-dark: ${darkColors[data-1]};">${data}</span>`;
                                    }
                                },
                                { data: 'away_team' },
                                {
                                    data: 'away_difficulty',
                                    render: function(data) {
                                        const colors = ['#234f1e', '#4a7c59', '#f39c12', '#e74c3c', '#8b0000'];
                                        const darkColors = ['#1a3f18', '#3d6a4a', '#d6890f', '#c0392b', '#6b0000'];
                                        return `<span class="fdr-badge" style="--fdr-color: ${colors[data-1]}; --fdr-color-dark: ${darkColors[data-1]};">${data}</span>`;
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

                            currentTables[gw] = $('#fdrTable' + gw).DataTable({
                                data: gwData,
                                columns: [
                                    { data: 'home_team' },
                                    {
                                        data: 'home_difficulty',
                                        render: function(data) {
                                            const colors = ['#234f1e', '#4a7c59', '#f39c12', '#e74c3c', '#8b0000'];
                                            const darkColors = ['#1a3f18', '#3d6a4a', '#d6890f', '#c0392b', '#6b0000'];
                                            return `<span class="fdr-badge" style="--fdr-color: ${colors[data-1]}; --fdr-color-dark: ${darkColors[data-1]};">${data}</span>`;
                                        }
                                    },
                                    { data: 'away_team' },
                                    {
                                        data: 'away_difficulty',
                                        render: function(data) {
                                            const colors = ['#234f1e', '#4a7c59', '#f39c12', '#e74c3c', '#8b0000'];
                                            const darkColors = ['#1a3f18', '#3d6a4a', '#d6890f', '#c0392b', '#6b0000'];
                                            return `<span class="fdr-badge" style="--fdr-color: ${colors[data-1]}; --fdr-color-dark: ${darkColors[data-1]};">${data}</span>`;
                                        }
                                    }
                                ],
                                order: [[0, 'asc']],
                                pageLength: 25,
                                responsive: true
                            });
                        }
                        
                        // Set up filter event handlers
                        setupFilters();
                    })
                    .catch(error => {
                        console.error('Error fetching FDR data:', error);
                        $('#fdrTableAll tbody').html('<tr><td colspan="5" class="text-center text-danger">Error loading data</td></tr>');
                        for (let gw = 1; gw <= 9; gw++) {
                            $('#fdrTable' + gw + ' tbody').html('<tr><td colspan="4" class="text-center text-danger">Error loading data</td></tr>');
                        }
                    });
                
                function populateTeamFilters(data) {
                    const homeTeams = [...new Set(data.map(f => f.home_team))].sort();
                    const awayTeams = [...new Set(data.map(f => f.away_team))].sort();
                    
                    // Populate home team filter
                    homeTeams.forEach(team => {
                        $('#homeTeamFilter').append(`<option value="${team}">${team}</option>`);
                    });
                    
                    // Populate away team filter
                    awayTeams.forEach(team => {
                        $('#awayTeamFilter').append(`<option value="${team}">${team}</option>`);
                    });
                }
                
                function setupFilters() {
                    // Home team filter
                    $('#homeTeamFilter').on('change', function() {
                        applyFilters();
                    });
                    
                    // Away team filter
                    $('#awayTeamFilter').on('change', function() {
                        applyFilters();
                    });
                    
                    // Difficulty filter
                    $('#difficultyFilter').on('change', function() {
                        applyFilters();
                    });
                    
                    // Gameweek filter
                    $('#gameweekFilter').on('change', function() {
                        applyFilters();
                    });
                    
                    // Home difficulty filter
                    $('#homeDifficultyFilter').on('change', function() {
                        applyFilters();
                    });
                    
                    // Away difficulty filter
                    $('#awayDifficultyFilter').on('change', function() {
                        applyFilters();
                    });
                    
                    // Combined difficulty filter
                    $('#combinedDifficultyFilter').on('change', function() {
                        applyFilters();
                    });
                    
                    // Clear filters button
                    $('#clearFilters').on('click', function() {
                        clearAllFilters();
                    });
                }
                
                function applyFilters() {
                    const homeTeam = $('#homeTeamFilter').val();
                    const awayTeam = $('#awayTeamFilter').val();
                    const difficulty = $('#difficultyFilter').val();
                    const gameweek = $('#gameweekFilter').val();
                    const homeDifficulty = $('#homeDifficultyFilter').val();
                    const awayDifficulty = $('#awayDifficultyFilter').val();
                    const combinedDifficulty = $('#combinedDifficultyFilter').val();
                    
                    // Filter the data
                    let filteredData = allFdrData.filter(fixture => {
                        if (homeTeam && fixture.home_team !== homeTeam) return false;
                        if (awayTeam && fixture.away_team !== awayTeam) return false;
                        if (difficulty && (fixture.home_difficulty != difficulty && fixture.away_difficulty != difficulty)) return false;
                        if (gameweek && fixture.gameweek != parseInt(gameweek)) return false;
                        if (homeDifficulty && fixture.home_difficulty != parseInt(homeDifficulty)) return false;
                        if (awayDifficulty && fixture.away_difficulty != parseInt(awayDifficulty)) return false;
                        if (combinedDifficulty && (fixture.home_difficulty + fixture.away_difficulty) != parseInt(combinedDifficulty)) return false;
                        return true;
                    });
                    
                    // Update filter info
                    updateFilterInfo(filteredData.length);
                    
                    // Update all tables
                    updateAllTables(filteredData);
                }
                
                function updateFilterInfo(count) {
                    const total = allFdrData.length;
                    $('#filterInfo').html(`
                        <i class="fas fa-info-circle"></i> Showing ${count} of ${total} fixtures 
                        ${count < total ? '(filtered)' : '(all fixtures)'}
                    `);
                }
                
                function updateAllTables(filteredData) {
                    // Update main table
                    currentTables.all.clear().rows.add(filteredData).draw();
                    
                    // Update gameweek tables
                    for (let gw = 1; gw <= 9; gw++) {
                        const gwData = filteredData.filter(fixture => fixture.gameweek === gw);
                        currentTables[gw].clear().rows.add(gwData).draw();
                    }
                }
                
                function clearAllFilters() {
                    $('#homeTeamFilter').val('');
                    $('#awayTeamFilter').val('');
                    $('#difficultyFilter').val('');
                    $('#gameweekFilter').val('');
                    $('#homeDifficultyFilter').val('');
                    $('#awayDifficultyFilter').val('');
                    $('#combinedDifficultyFilter').val('');
                    
                    // Reset all tables to show all data
                    updateAllTables(allFdrData);
                    updateFilterInfo(allFdrData.length);
                }
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
    teams = db_manager.get_teams()
    
    # Get unique positions and teams for dropdowns
    positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    team_names = [team['name'] for team in teams]
    
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
                transition: all 0.3s ease;
            }
            .nav-link.active { 
                background-color: #3498db !important; 
                color: white !important; 
                border-radius: 5px;
                transform: scale(1.05);
            }
            .nav-link:hover { 
                color: #3498db !important; 
                transform: translateY(-2px);
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
                transition: all 0.3s ease;
            }
            .gk { background-color: #dc3545; }
            .def { background-color: #007bff; }
            .mid { background-color: #28a745; }
            .fwd { background-color: #ffc107; color: #212529; }
            
            .position-badge:hover {
                transform: scale(1.1);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            
            .table th { 
                white-space: normal !important; 
                word-wrap: break-word !important;
                max-width: 80px !important;
                font-size: 0.85em;
                padding: 8px 4px;
                text-align: center;
                vertical-align: middle;
                transition: background-color 0.3s ease;
            }
            .table th:hover {
                background-color: #e9ecef !important;
            }
            
            .table td { 
                vertical-align: middle; 
                font-size: 0.9em;
                padding: 6px 4px;
                transition: all 0.2s ease;
            }
            
            .table tbody tr:hover {
                background-color: #f8f9fa !important;
                transform: scale(1.01);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .chance-playing {
                font-weight: bold;
                transition: all 0.3s ease;
            }
            .chance-playing.healthy { color: #28a745; }
            .chance-playing.injured { color: #dc3545; }
            .points-per-million {
                color: #17a2b8;
                font-weight: bold;
            }
            
            .player-name {
                font-weight: bold;
                min-width: 80px;
                transition: color 0.3s ease;
            }
            .player-name:hover {
                color: #007bff;
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
            
            /* Enhanced filter form styling */
            .filter-form {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
                transition: all 0.3s ease;
            }
            
            .filter-form:hover {
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                transform: translateY(-2px);
            }
            
            .filter-form label {
                font-weight: 500;
                margin-right: 10px;
                color: #2c3e50;
            }
            
            .filter-form select, .filter-form input {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px 10px;
                margin-right: 15px;
                transition: all 0.3s ease;
            }
            
            .filter-form select:focus, .filter-form input:focus {
                border-color: #007bff;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,0.25);
                transform: scale(1.02);
            }
            
            .filter-form .btn {
                margin-right: 10px;
                transition: all 0.3s ease;
            }
            
            .filter-form .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            
            /* Save/Load Views Section */
            .views-section {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            
            .views-section h5 {
                color: white;
                margin-bottom: 15px;
            }
            
            .views-section input, .views-section select {
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                margin-right: 10px;
                transition: all 0.3s ease;
            }
            
            .views-section input:focus, .views-section select:focus {
                transform: scale(1.05);
                box-shadow: 0 0 0 0.2rem rgba(255,255,255,0.25);
            }
            
            .views-section .btn {
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                transition: all 0.3s ease;
            }
            
            .views-section .btn:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            
            /* Table styling */
            .table-responsive {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
                transition: all 0.3s ease;
            }
            
            .table-responsive:hover {
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
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
                transition: all 0.3s ease;
            }
            
            .dataTables_wrapper .dataTables_paginate .paginate_button.current {
                background: #007bff !important;
                border-color: #007bff !important;
                color: white !important;
                transform: scale(1.1);
            }
            
            .dataTables_wrapper .dataTables_paginate .paginate_button:hover {
                background: #0056b3 !important;
                border-color: #0056b3 !important;
                color: white !important;
                transform: translateY(-2px);
            }
            
            /* Animation classes */
            .fade-in {
                animation: fadeIn 0.5s ease-in;
            }
            
            .slide-up {
                animation: slideUp 0.3s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideUp {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            /* Enhanced button styles */
            .btn {
                transition: all 0.3s ease;
                border-radius: 8px;
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                border: none;
            }
            
            .btn-success {
                background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
                border: none;
            }
            
            .btn-warning {
                background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
                border: none;
                color: #212529;
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
            <h1 class="text-center mb-4 fade-in">FPL Players - Expected Points (GW1-9)</h1>
            
            <!-- Save/Load Views Section -->
            <div class="views-section slide-up">
                <h5><i class="fas fa-save"></i> Save & Load Views</h5>
                <div class="row">
                    <div class="col-md-4">
                        <input type="text" id="viewName" class="form-control" placeholder="Enter view name...">
                    </div>
                    <div class="col-md-4">
                        <button id="saveView" class="btn btn-success">
                            <i class="fas fa-save"></i> Save Current View
                        </button>
                    </div>
                    <div class="col-md-4">
                        <select id="loadView" class="form-select">
                            <option value="">Load Saved View...</option>
                        </select>
                    </div>
                </div>
                <div class="mt-2">
                    <small class="text-white-50">
                        <i class="fas fa-info-circle"></i> Save your current filters and sorting as a named view for quick access
                    </small>
                </div>
            </div>
            
            <!-- Enhanced Filters Section -->
            <div class="filter-form slide-up">
                <h5 class="mb-3"><i class="fas fa-filter"></i> Advanced Filters</h5>
                <div class="row mb-3">
                    <div class="col-md-3">
                        <label for="positionFilter" class="form-label">Position:</label>
                        <select id="positionFilter" class="form-select">
                            <option value="">All Positions</option>
                            <option value="Goalkeeper">Goalkeeper</option>
                            <option value="Defender">Defender</option>
                            <option value="Midfielder">Midfielder</option>
                            <option value="Forward">Forward</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label for="teamFilter" class="form-label">Team:</label>
                        <select id="teamFilter" class="form-select">
                            <option value="">All Teams</option>
                            {% for team in team_names %}
                            <option value="{{ team }}">{{ team }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label for="priceFilter" class="form-label">Max Price (£M):</label>
                        <input type="number" id="priceFilter" class="form-control" placeholder="e.g., 10.0" step="0.1" min="0">
                    </div>
                    <div class="col-md-3">
                        <label for="chanceFilter" class="form-label">Min Chance of Playing (%):</label>
                        <input type="number" id="chanceFilter" class="form-control" placeholder="e.g., 75" min="0" max="100">
                    </div>
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-3">
                        <label for="pointsPerPoundFilter" class="form-label">Min Points/£:</label>
                        <input type="number" id="pointsPerPoundFilter" class="form-control" placeholder="e.g., 3.0" step="0.1" min="0">
                    </div>
                    <div class="col-md-3">
                        <label for="totalPointsFilter" class="form-label">Min Total Points (GW1-9):</label>
                        <input type="number" id="totalPointsFilter" class="form-control" placeholder="e.g., 30.0" step="0.1" min="0">
                    </div>
                    <div class="col-md-3">
                        <label for="formFilter" class="form-label">Min Form:</label>
                        <input type="number" id="formFilter" class="form-control" placeholder="e.g., 5.0" step="0.1" min="0">
                    </div>
                    <div class="col-md-3">
                        <label for="ownershipFilter" class="form-label">Min Ownership (%):</label>
                        <input type="number" id="ownershipFilter" class="form-control" placeholder="e.g., 5.0" step="0.1" min="0">
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12">
                        <button id="clearFilters" class="btn btn-warning">
                            <i class="fas fa-times"></i> Clear All Filters
                        </button>
                        <span id="filterInfo" class="ms-3 text-muted"></span>
                    </div>
                </div>
            </div>
            
            <!-- Players Table -->
            <div class="table-responsive slide-up">
                <table id="playersTable" class="table table-striped table-hover">
                    <thead>
                        <tr>
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
                            order: [[5, 'desc']], // Sort by total points by default
                            pageLength: 25,
                            responsive: true,
                            scrollX: true
                        });

                        // Apply filters
                        $('#positionFilter').on('change', function() {
                            table.column(1).search(this.value).draw();
                        });

                        $('#teamFilter').on('change', function() {
                            table.column(2).search(this.value).draw();
                        });

                        $('#priceFilter').on('input', function() {
                            var maxPrice = parseFloat($(this).val());
                            if (isNaN(maxPrice)) return;

                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var price = parseFloat(data[3].replace('£', '').replace('m', ''));
                                return price <= maxPrice;
                            });
                            table.draw();
                        });

                        $('#chanceFilter').on('input', function() {
                            var minChance = parseInt($(this).val());
                            if (isNaN(minChance)) return;

                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var chanceText = data[7];
                                var chance = parseInt(chanceText.match(/\d+/)[0]);
                                return chance >= minChance;
                            });
                            table.draw();
                        });

                        $('#pointsPerPoundFilter').on('input', function() {
                            var minPointsPerPound = parseFloat($(this).val());
                            if (isNaN(minPointsPerPound)) return;

                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var pointsPerPound = parseFloat(data[6]);
                                return pointsPerPound >= minPointsPerPound;
                            });
                            table.draw();
                        });

                        $('#totalPointsFilter').on('input', function() {
                            var minTotalPoints = parseFloat($(this).val());
                            if (isNaN(minTotalPoints)) return;

                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var totalPoints = parseFloat(data[5]);
                                return totalPoints >= minTotalPoints;
                            });
                            table.draw();
                        });

                        $('#formFilter').on('input', function() {
                            var minForm = parseFloat($(this).val());
                            if (isNaN(minForm)) return;

                            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                                var form = parseFloat(data[4]);
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

                        // Save/Load Views functionality
                        $('#saveView').on('click', function() {
                            const viewName = $('#viewName').val().trim();
                            if (!viewName) {
                                alert('Please enter a view name');
                                return;
                            }

                            const currentView = {
                                name: viewName,
                                filters: {
                                    position: $('#positionFilter').val(),
                                    team: $('#teamFilter').val(),
                                    price: $('#priceFilter').val(),
                                    chance: $('#chanceFilter').val(),
                                    pointsPerPound: $('#pointsPerPoundFilter').val(),
                                    totalPoints: $('#totalPointsFilter').val(),
                                    form: $('#formFilter').val(),
                                    ownership: $('#ownershipFilter').val()
                                },
                                sorting: table.order(),
                                pageLength: table.page.len(),
                                search: table.search()
                            };

                            // Save to localStorage
                            const savedViews = JSON.parse(localStorage.getItem('fplPlayerViews') || '{}');
                            savedViews[viewName] = currentView;
                            localStorage.setItem('fplPlayerViews', JSON.stringify(savedViews));

                            // Update dropdown
                            updateViewsDropdown();
                            $('#viewName').val('');
                            
                            // Show success message
                            showNotification('View saved successfully!', 'success');
                        });

                        $('#loadView').on('change', function() {
                            const viewName = $(this).val();
                            if (!viewName) return;

                            const savedViews = JSON.parse(localStorage.getItem('fplPlayerViews') || '{}');
                            const view = savedViews[viewName];
                            
                            if (view) {
                                // Apply filters
                                $('#positionFilter').val(view.filters.position);
                                $('#teamFilter').val(view.filters.team);
                                $('#priceFilter').val(view.filters.price);
                                $('#chanceFilter').val(view.filters.chance);
                                $('#pointsPerPoundFilter').val(view.filters.pointsPerPound);
                                $('#totalPointsFilter').val(view.filters.totalPoints);
                                $('#formFilter').val(view.filters.form);
                                $('#ownershipFilter').val(view.filters.ownership);

                                // Apply sorting
                                table.order(view.sorting).draw();

                                // Apply page length
                                table.page.len(view.pageLength).draw();

                                // Apply search
                                table.search(view.search).draw();

                                // Trigger filter events
                                $('#positionFilter').trigger('change');
                                $('#teamFilter').trigger('change');
                                $('#priceFilter').trigger('input');
                                $('#chanceFilter').trigger('input');
                                $('#pointsPerPoundFilter').trigger('input');
                                $('#totalPointsFilter').trigger('input');
                                $('#formFilter').trigger('input');
                                $('#ownershipFilter').trigger('input');

                                showNotification('View loaded successfully!', 'info');
                            }
                        });

                        // Initialize views dropdown
                        updateViewsDropdown();
                    })
                    .catch(error => {
                        console.error('Error fetching players data:', error);
                        $('#playersTable tbody').html('<tr><td colspan="16" class="text-center text-danger">Error loading data</td></tr>');
                    });

                function updateViewsDropdown() {
                    const savedViews = JSON.parse(localStorage.getItem('fplPlayerViews') || '{}');
                    const $dropdown = $('#loadView');
                    
                    // Clear existing options except the first one
                    $dropdown.find('option:not(:first)').remove();
                    
                    // Add saved views
                    Object.keys(savedViews).forEach(viewName => {
                        $dropdown.append(`<option value="${viewName}">${viewName}</option>`);
                    });
                }

                function showNotification(message, type) {
                    const alertClass = type === 'success' ? 'alert-success' : 'alert-info';
                    const $notification = $(`
                        <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
                             style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
                            <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i> ${message}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    `);
                    
                    $('body').append($notification);
                    
                    // Auto-remove after 3 seconds
                    setTimeout(() => {
                        $notification.alert('close');
                    }, 3000);
                }
            });
        </script>
    </body>
    </html>
    """, players=players, team_names=team_names)

@app.route('/squad')
def squad_page():
    """Serve the original squad page"""
    return render_template_string("""
    <html>
    <head>
        <title>FPL Optimal Squad - GW1-9</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
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
                transition: all 0.3s ease;
            }
            .nav-link.active { 
                background-color: #3498db !important; 
                color: white !important; 
                border-radius: 5px;
                transform: scale(1.05);
            }
            .nav-link:hover { 
                color: #3498db !important; 
                transform: translateY(-2px);
            }
            h1, h2, h3 { 
                color: #2c3e50; 
                font-weight: 600; 
                margin-bottom: 1.5rem; 
            }
            .summary-card { 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                margin-bottom: 2rem;
                transition: all 0.3s ease;
            }
            .summary-card:hover {
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                transform: translateY(-2px);
            }
            .gw-card { 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                margin-bottom: 2rem;
                transition: all 0.3s ease;
            }
            .gw-card:hover {
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            }
            .position-badge { 
                font-size: 0.8em; 
                padding: 4px 8px; 
                border-radius: 12px; 
                color: white; 
                font-weight: bold;
                transition: all 0.3s ease;
            }
            .gk { background-color: #dc3545; }
            .def { background-color: #007bff; }
            .mid { background-color: #28a745; }
            .fwd { background-color: #ffc107; color: #212529; }
            
            .position-badge:hover {
                transform: scale(1.1);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            
            .nav-tabs .nav-link { 
                color: #495057; 
                transition: all 0.3s ease;
            }
            .nav-tabs .nav-link.active { 
                color: #007bff; 
                font-weight: 600;
                transform: scale(1.05);
            }
            .nav-tabs .nav-link:hover {
                transform: translateY(-2px);
            }
            
            .points-display { 
                font-size: 1.2em; 
                font-weight: bold; 
                color: #28a745; 
            }
            .budget-info { 
                font-size: 1.1em; 
                color: #6c757d; 
            }
            
            /* Captain Management */
            .captain-section {
                background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                border: 2px solid #ffc107;
            }
            
            .captain-badge {
                background: #dc3545;
                color: white;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 12px;
                margin-right: 8px;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            
            /* Transfer Tracking */
            .transfer-section {
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
            }
            
            .transfer-in {
                color: #28a745;
                font-weight: bold;
            }
            
            .transfer-out {
                color: #dc3545;
                font-weight: bold;
            }
            
            .transfer-arrow {
                font-size: 1.2em;
                margin: 0 8px;
                animation: slideRight 1s ease-in-out infinite alternate;
            }
            
            @keyframes slideRight {
                from { transform: translateX(0); }
                to { transform: translateX(5px); }
            }
            
            /* Bench Management */
            .bench-section {
                background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
            }
            
            .bench-promotion {
                color: #17a2b8;
                font-weight: bold;
            }
            
            .bench-demotion {
                color: #ffc107;
                font-weight: bold;
            }
            
            /* Enhanced UI Elements */
            .player-card {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .player-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                border-color: #007bff;
            }
            
            .player-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
                transition: left 0.5s;
            }
            
            .player-card:hover::before {
                left: 100%;
            }
            
            .player-stats {
                display: flex;
                justify-content: space-between;
                margin-top: 8px;
                font-size: 0.9em;
            }
            
            .player-price {
                color: #6c757d;
            }
            
            .player-points {
                color: #28a745;
                font-weight: bold;
            }
            
            /* Animation Classes */
            .fade-in {
                animation: fadeIn 0.5s ease-in;
            }
            
            .slide-up {
                animation: slideUp 0.3s ease-out;
            }
            
            .bounce-in {
                animation: bounceIn 0.6s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideUp {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            @keyframes bounceIn {
                0% { transform: scale(0.3); opacity: 0; }
                50% { transform: scale(1.05); }
                70% { transform: scale(0.9); }
                100% { transform: scale(1); opacity: 1; }
            }
            
            /* Enhanced Button Styles */
            .btn {
                transition: all 0.3s ease;
                border-radius: 8px;
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                border: none;
            }
            
            .btn-success {
                background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
                border: none;
            }
            
            .btn-warning {
                background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
                border: none;
                color: #212529;
            }
            
            .btn-info {
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                border: none;
            }
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
            <h1 class="text-center mb-4 fade-in">FPL Optimal Squad - GW1-9</h1>
            
            <!-- Summary Section -->
            <div class="summary-card slide-up">
                <div class="row">
                    <div class="col-md-3">
                        <h4><i class="fas fa-trophy"></i> Total Points (GW1-9)</h4>
                        <div class="points-display" id="totalPoints">Loading...</div>
                    </div>
                    <div class="col-md-3">
                        <h4><i class="fas fa-coins"></i> Squad Value</h4>
                        <div class="budget-info" id="squadValue">Loading...</div>
                    </div>
                    <div class="col-md-3">
                        <h4><i class="fas fa-wallet"></i> Remaining Budget</h4>
                        <div class="budget-info" id="remainingBudget">Loading...</div>
                    </div>
                    <div class="col-md-3">
                        <h4><i class="fas fa-users"></i> Formation</h4>
                        <div class="budget-info">4-4-2</div>
                    </div>
                </div>
            </div>
            
            <!-- Captain Management Section -->
            <div class="summary-card slide-up">
                <h4><i class="fas fa-crown"></i> Captain Management</h4>
                <div class="captain-section">
                    <div class="row">
                        <div class="col-md-6">
                            <h6><i class="fas fa-star"></i> Current Captain</h6>
                            <div id="currentCaptain">Loading...</div>
                        </div>
                        <div class="col-md-6">
                            <h6><i class="fas fa-exchange-alt"></i> Captain Changes</h6>
                            <div id="captainChanges">Loading...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Transfer Tracking Section -->
            <div class="summary-card slide-up">
                <h4><i class="fas fa-exchange-alt"></i> Transfer History</h4>
                <div id="transferHistory">Loading...</div>
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
                    <div class="gw-card bounce-in">
                        <h3>GW1 - 4-4-2</h3>
                        <div id="gw1Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw2" role="tabpanel">
                    <div class="gw-card bounce-in">
                        <h3>GW2 - 4-4-2</h3>
                        <div id="gw2Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw3" role="tabpanel">
                    <div class="gw-card bounce-in">
                        <h3>GW3 - 4-4-2</h3>
                        <div id="gw3Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw4" role="tabpanel">
                    <div class="gw-card bounce-in">
                        <h3>GW4 - 4-4-2</h3>
                        <div id="gw4Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw5" role="tabpanel">
                    <div class="gw-card bounce-in">
                        <h3>GW5 - 4-4-2</h3>
                        <div id="gw5Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw6" role="tabpanel">
                    <div class="gw-card bounce-in">
                        <h3>GW6 - 4-4-2</h3>
                        <div id="gw6Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw7" role="tabpanel">
                    <div class="gw-card bounce-in">
                        <h3>GW7 - 4-4-2</h3>
                        <div id="gw7Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw8" role="tabpanel">
                    <div class="gw-card bounce-in">
                        <h3>GW8 - 4-4-2</h3>
                        <div id="gw8Content">Loading...</div>
                    </div>
                </div>
                <div class="tab-pane fade" id="gw9" role="tabpanel">
                    <div class="gw-card bounce-in">
                        <h3>GW9 - 4-4-2</h3>
                        <div id="gw9Content">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            $(document).ready(function() {
                // Simulate squad data with captain and transfer management
                const squadData = {
                    totalPoints: 0,
                    totalValue: 0,
                    captain: 'Watkins',
                    captainChanges: [
                        { gw: 1, player: 'Watkins', points: 10.4 },
                        { gw: 2, player: 'M.Salah', points: 12.2 },
                        { gw: 3, player: 'M.Salah', points: 11.2 },
                        { gw: 4, player: 'M.Salah', points: 14.0 },
                        { gw: 5, player: 'M.Salah', points: 13.5 },
                        { gw: 6, player: 'Watkins', points: 8.2 },
                        { gw: 7, player: 'Eze', points: 6.8 },
                        { gw: 8, player: 'Virgil', points: 5.4 },
                        { gw: 9, player: 'Wood', points: 7.1 }
                    ],
                    transfers: [
                        { gw: 2, in: 'M.Salah', out: 'Palmer', cost: 0 },
                        { gw: 3, in: 'Rogers', out: 'Tonali', cost: 0 },
                        { gw: 4, in: 'Tosin', out: 'Richards', cost: 0 },
                        { gw: 5, in: 'Evanilson', out: 'Wood', cost: 0 },
                        { gw: 6, in: 'Palmer', out: 'Evanilson', cost: 0 },
                        { gw: 7, in: 'Wood', out: 'Palmer', cost: 0 },
                        { gw: 8, in: 'Richards', out: 'Tosin', cost: 0 },
                        { gw: 9, in: 'Tonali', out: 'Richards', cost: 0 }
                    ],
                    benchPromotions: [
                        { gw: 2, player: 'Petrović', position: 'GK' },
                        { gw: 4, player: 'Lacroix', position: 'DEF' },
                        { gw: 6, player: 'Richards', position: 'DEF' },
                        { gw: 8, player: 'Tonali', position: 'MID' }
                    ],
                    benchDemotions: [
                        { gw: 2, player: 'Palmer', position: 'MID' },
                        { gw: 3, player: 'Tonali', position: 'MID' },
                        { gw: 4, player: 'Richards', position: 'DEF' },
                        { gw: 5, player: 'Wood', position: 'FWD' }
                    ]
                };

                // Update summary information
                $('#totalPoints').text(squadData.totalPoints.toFixed(1));
                $('#squadValue').text('£' + squadData.totalValue.toFixed(1) + 'M');
                $('#remainingBudget').text('£' + (100.0 - squadData.totalValue).toFixed(1) + 'M');

                // Update captain information
                $('#currentCaptain').html(`
                    <div class="player-card">
                        <span class="captain-badge">C</span>
                        <strong>${squadData.captain}</strong>
                        <div class="player-stats">
                            <span>Current GW Captain</span>
                        </div>
                    </div>
                `);

                // Update captain changes
                let captainChangesHtml = '';
                squadData.captainChanges.forEach(change => {
                    captainChangesHtml += `
                        <div class="player-card">
                            <span class="captain-badge">C</span>
                            <strong>${change.player}</strong> (GW${change.gw})
                            <div class="player-stats">
                                <span>${change.points.toFixed(1)} pts</span>
                            </div>
                        </div>
                    `;
                });
                $('#captainChanges').html(captainChangesHtml);

                // Update transfer history
                let transferHistoryHtml = '';
                squadData.transfers.forEach(transfer => {
                    transferHistoryHtml += `
                        <div class="transfer-section">
                            <h6>GW${transfer.gw} Transfer</h6>
                            <div class="d-flex align-items-center">
                                <span class="transfer-out">${transfer.out}</span>
                                <i class="fas fa-arrow-right transfer-arrow"></i>
                                <span class="transfer-in">${transfer.in}</span>
                                <span class="ms-3">Cost: £${transfer.cost.toFixed(1)}M</span>
                            </div>
                        </div>
                    `;
                });
                $('#transferHistory').html(transferHistoryHtml);

                // Fetch team optimization data
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

                    // Update summary with real data
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

                        // Add players by position with enhanced styling
                        gwContent += '<div class="row">';
                        gwContent += '<div class="col-md-3"><h6><i class="fas fa-shield-alt"></i> Goalkeepers</h6>';
                        data.goalkeepers.forEach(p => {
                            const gwPoints = p['gw' + gw + '_points'] || 0;
                            const isCaptain = squadData.captainChanges.find(c => c.gw === gw && c.player === p.name);
                            const isTransferIn = squadData.transfers.find(t => t.gw === gw && t.in === p.name);
                            const isTransferOut = squadData.transfers.find(t => t.gw === gw && t.out === p.name);
                            const isBenchPromotion = squadData.benchPromotions.find(b => b.gw === gw && b.player === p.name);
                            const isBenchDemotion = squadData.benchDemotions.find(b => b.gw === gw && b.player === p.name);
                            
                            let playerClass = 'player-card';
                            let statusBadge = '';
                            
                            if (isCaptain) {
                                playerClass += ' captain-section';
                                statusBadge = '<span class="captain-badge">C</span> ';
                            } else if (isTransferIn) {
                                playerClass += ' transfer-section';
                                statusBadge = '<span class="transfer-in"><i class="fas fa-plus-circle"></i> IN</span> ';
                            } else if (isTransferOut) {
                                playerClass += ' transfer-section';
                                statusBadge = '<span class="transfer-out"><i class="fas fa-minus-circle"></i> OUT</span> ';
                            } else if (isBenchPromotion) {
                                playerClass += ' bench-section';
                                statusBadge = '<span class="bench-promotion"><i class="fas fa-arrow-up"></i> ↑</span> ';
                            } else if (isBenchDemotion) {
                                playerClass += ' bench-section';
                                statusBadge = '<span class="bench-demotion"><i class="fas fa-arrow-down"></i> ↓</span> ';
                            }
                            
                            gwContent += `<div class="${playerClass}">${statusBadge}<span class="position-badge gk">GK</span> ${p.name} (${p.team}) - ${gwPoints.toFixed(1)} pts</div>`;
                        });
                        gwContent += '</div>';

                        gwContent += '<div class="col-md-3"><h6><i class="fas fa-shield-alt"></i> Defenders</h6>';
                        data.defenders.forEach(p => {
                            const gwPoints = p['gw' + gw + '_points'] || 0;
                            const isCaptain = squadData.captainChanges.find(c => c.gw === gw && c.player === p.name);
                            const isTransferIn = squadData.transfers.find(t => t.gw === gw && t.in === p.name);
                            const isTransferOut = squadData.transfers.find(t => t.gw === gw && t.out === p.name);
                            const isBenchPromotion = squadData.benchPromotions.find(b => b.gw === gw && b.player === p.name);
                            const isBenchDemotion = squadData.benchDemotions.find(b => b.gw === gw && b.player === p.name);
                            
                            let playerClass = 'player-card';
                            let statusBadge = '';
                            
                            if (isCaptain) {
                                playerClass += ' captain-section';
                                statusBadge = '<span class="captain-badge">C</span> ';
                            } else if (isTransferIn) {
                                playerClass += ' transfer-section';
                                statusBadge = '<span class="transfer-in"><i class="fas fa-plus-circle"></i> IN</span> ';
                            } else if (isTransferOut) {
                                playerClass += ' transfer-section';
                                statusBadge = '<span class="transfer-out"><i class="fas fa-minus-circle"></i> OUT</span> ';
                            } else if (isBenchPromotion) {
                                playerClass += ' bench-section';
                                statusBadge = '<span class="bench-promotion"><i class="fas fa-arrow-up"></i> ↑</span> ';
                            } else if (isBenchDemotion) {
                                playerClass += ' bench-section';
                                statusBadge = '<span class="bench-demotion"><i class="fas fa-arrow-down"></i> ↓</span> ';
                            }
                            
                            gwContent += `<div class="${playerClass}">${statusBadge}<span class="position-badge def">DEF</span> ${p.name} (${p.team}) - ${gwPoints.toFixed(1)} pts</div>`;
                        });
                        gwContent += '</div>';

                        gwContent += '<div class="col-md-3"><h6><i class="fas fa-running"></i> Midfielders</h6>';
                        data.midfielders.forEach(p => {
                            const gwPoints = p['gw' + gw + '_points'] || 0;
                            const isCaptain = squadData.captainChanges.find(c => c.gw === gw && c.player === p.name);
                            const isTransferIn = squadData.transfers.find(t => t.gw === gw && t.in === p.name);
                            const isTransferOut = squadData.transfers.find(t => t.gw === gw && t.out === p.name);
                            const isBenchPromotion = squadData.benchPromotions.find(b => b.gw === gw && b.player === p.name);
                            const isBenchDemotion = squadData.benchDemotions.find(b => b.gw === gw && b.player === p.name);
                            
                            let playerClass = 'player-card';
                            let statusBadge = '';
                            
                            if (isCaptain) {
                                playerClass += ' captain-section';
                                statusBadge = '<span class="captain-badge">C</span> ';
                            } else if (isTransferIn) {
                                playerClass += ' transfer-section';
                                statusBadge = '<span class="transfer-in"><i class="fas fa-plus-circle"></i> IN</span> ';
                            } else if (isTransferOut) {
                                playerClass += ' transfer-section';
                                statusBadge = '<span class="transfer-out"><i class="fas fa-minus-circle"></i> OUT</span> ';
                            } else if (isBenchPromotion) {
                                playerClass += ' bench-section';
                                statusBadge = '<span class="bench-promotion"><i class="fas fa-arrow-up"></i> ↑</span> ';
                            } else if (isBenchDemotion) {
                                playerClass += ' bench-section';
                                statusBadge = '<span class="bench-demotion"><i class="fas fa-arrow-down"></i> ↓</span> ';
                            }
                            
                            gwContent += `<div class="${playerClass}">${statusBadge}<span class="position-badge mid">MID</span> ${p.name} (${p.team}) - ${gwPoints.toFixed(1)} pts</div>`;
                        });
                        gwContent += '</div>';

                        gwContent += '<div class="col-md-3"><h6><i class="fas fa-bullseye"></i> Forwards</h6>';
                        data.forwards.forEach(p => {
                            const gwPoints = p['gw' + gw + '_points'] || 0;
                            const isCaptain = squadData.captainChanges.find(c => c.gw === gw && c.player === p.name);
                            const isTransferIn = squadData.transfers.find(t => t.gw === gw && t.in === p.name);
                            const isTransferOut = squadData.transfers.find(t => t.gw === gw && t.out === p.name);
                            const isBenchPromotion = squadData.benchPromotions.find(b => b.gw === gw && b.player === p.name);
                            const isBenchDemotion = squadData.benchDemotions.find(b => b.gw === gw && b.player === p.name);
                            
                            let playerClass = 'player-card';
                            let statusBadge = '';
                            
                            if (isCaptain) {
                                playerClass += ' captain-section';
                                statusBadge = '<span class="captain-badge">C</span> ';
                            } else if (isTransferIn) {
                                playerClass += ' transfer-section';
                                statusBadge = '<span class="transfer-in"><i class="fas fa-plus-circle"></i> IN</span> ';
                            } else if (isTransferOut) {
                                playerClass += ' transfer-section';
                                statusBadge = '<span class="transfer-out"><i class="fas fa-minus-circle"></i> OUT</span> ';
                            } else if (isBenchPromotion) {
                                playerClass += ' bench-section';
                                statusBadge = '<span class="bench-promotion"><i class="fas fa-arrow-up"></i> ↑</span> ';
                            } else if (isBenchDemotion) {
                                playerClass += ' bench-section';
                                statusBadge = '<span class="bench-demotion"><i class="fas fa-arrow-down"></i> ↓</span> ';
                            }
                            
                            gwContent += `<div class="${playerClass}">${statusBadge}<span class="position-badge fwd">FWD</span> ${p.name} (${p.team}) - ${gwPoints.toFixed(1)} pts</div>`;
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
