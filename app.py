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
    return render_template('fdr.html')

@app.route('/players')
def players_page():
    """Serve the original players page with DataTables"""
    players = db_manager.get_all_players()
    teams = db_manager.get_teams()
    
    # Get unique positions and teams for dropdowns
    positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    team_names = [team['name'] for team in teams]
    
    return render_template('players.html')

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
