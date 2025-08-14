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

# Fetch player data from unified database
def create_and_populate_players_table(conn):
    """Create and populate the players table with hardcoded data"""
    try:
        # Drop existing table to clear all data
        conn.execute("DROP TABLE IF EXISTS players")
        
        # Create players table with all required fields
        conn.execute("""
            CREATE TABLE players (
                id INTEGER PRIMARY KEY,
                name TEXT,
                position_name TEXT,
                team TEXT,
                price REAL,
                availability TEXT,
                uncertainty_percent TEXT,
                overall_total REAL,
                gw1_points REAL,
                gw2_points REAL,
                gw3_points REAL,
                gw4_points REAL,
                gw5_points REAL,
                gw6_points REAL,
                gw7_points REAL,
                gw8_points REAL,
                gw9_points REAL,
                points_per_million REAL,
                chance_of_playing_next_round INTEGER
            )
        """)
        
        # Get the hardcoded data
        hardcoded_players = get_additional_top_players()
        
        # Insert all players
        for player in hardcoded_players:
            conn.execute("""
                INSERT INTO players (id, name, position_name, team, price, availability, uncertainty_percent, overall_total, 
                                   gw1_points, gw2_points, gw3_points, gw4_points, gw5_points, gw6_points, gw7_points, gw8_points, gw9_points,
                                   points_per_million, chance_of_playing_next_round)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player.get("id"),
                player.get("name"),
                player.get("position_name"),
                player.get("team"),
                player.get("price"),
                "Available",  # Default availability
                player.get("ownership", "24%"),  # Use ownership as uncertainty_percent
                player.get("total_gw1_9"),
                player.get("gw1_9_points", [0.0] * 9)[0],  # GW1
                player.get("gw1_9_points", [0.0] * 9)[1],  # GW2
                player.get("gw1_9_points", [0.0] * 9)[2],  # GW3
                player.get("gw1_9_points", [0.0] * 9)[3],  # GW4
                player.get("gw1_9_points", [0.0] * 9)[4],  # GW5
                player.get("gw1_9_points", [0.0] * 9)[5],  # GW6
                player.get("gw1_9_points", [0.0] * 9)[6],  # GW7
                player.get("gw1_9_points", [0.0] * 9)[7],  # GW8
                player.get("gw1_9_points", [0.0] * 9)[8],  # GW9
                player.get("points_per_million"),
                player.get("chance_of_playing_next_round", 100)
            ))
        
        conn.commit()
        print(f"Players table cleared and populated with {len(hardcoded_players)} players")
        
    except Exception as e:
        print(f"Error creating players table: {e}")

def fetch_players_data():
    """Fetch player data from unified database"""
    try:
        import sqlite3
        conn = sqlite3.connect("fpl_oos.db")
        
        # Check if players table exists, if not create it
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players'")
        if not cursor.fetchone():
            print("Players table not found, creating empty table...")
            create_and_populate_players_table(conn)
        else:
            print("Players table exists, checking if it has data...")
            # Check if table has data, if not add the players
            cursor = conn.execute("SELECT COUNT(*) FROM players")
            count = cursor.fetchone()[0]
            if count == 0:
                print("Table is empty, adding players...")
                add_players_via_sql()
            else:
                print(f"Table has {count} players, no need to add more")
        
        # Read players data from database
        cursor = conn.execute("""
            SELECT id, name, position_name, team, price, availability, uncertainty_percent, overall_total,
                   gw1_points, gw2_points, gw3_points, gw4_points, gw5_points, gw6_points, gw7_points, gw8_points, gw9_points,
                   points_per_million, chance_of_playing_next_round
            FROM players
            ORDER BY overall_total DESC
        """)
        
        players_data = []
        for row in cursor.fetchall():
            # Reconstruct gw1_9_points array from individual GW fields
            gw1_9_points = [row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16]]
            
            player = {
                "id": row[0],
                "name": row[1],
                "position_name": row[2],
                "team": row[3],
                "price": row[4],
                "availability": row[5],
                "uncertainty_percent": row[6],
                "total_gw1_9": row[7],
                "gw1_9_points": gw1_9_points,
                "points_per_million": row[17],
                "chance_of_playing_next_round": row[18],
                "ownership": row[6]  # Use uncertainty_percent as ownership for compatibility
            }
            players_data.append(player)
        
        conn.close()
        
        print(f"Loaded {len(players_data)} players from unified database")
        
        # Debug: Check for duplicates
        names = [p["name"] for p in players_data]
        salah_count = names.count("M.Salah")
        print(f"Salah entries found: {salah_count}")
        
        if salah_count > 1:
            print("Duplicate Salah entries found in database:")
            for i, p in enumerate(players_data):
                if p["name"] == "M.Salah":
                    print(f"  Entry {i}: {p}")
        
        return players_data
        
    except Exception as e:
        print(f"Error loading players data: {e}")
        return []

def get_additional_top_players():
    """Get the complete list of players with their specific expected points from the provided data"""
    # This function is no longer needed - data is added directly via SQL
    return []

def clear_players_table():
    """Standalone function to clear all data from the players table (keeps table structure)"""
    try:
        import sqlite3
        conn = sqlite3.connect("fpl_oos.db")
        
        # Clear all data from players table
        conn.execute("DELETE FROM players")
        conn.commit()
        print("Successfully cleared all data from players table")
        conn.close()
        
    except Exception as e:
        print(f"Error clearing players table: {e}")

def add_players_via_sql():
    """Add players directly to the database using SQL INSERT statements"""
    
    # Array of all players with their data
    players_data = [
        {"id": 1001, "name": "M.Salah", "position_name": "Midfielder", "team": "Liverpool", "price": 14.5, "uncertainty_percent": "24%", "overall_total": 57.0, "gw1_points": 6.7, "gw2_points": 6.1, "gw3_points": 5.6, "gw4_points": 7.0, "gw5_points": 6.6, "gw6_points": 5.7, "gw7_points": 5.7, "gw8_points": 7.4, "gw9_points": 6.2, "points_per_million": 3.93},
        {"id": 1002, "name": "Haaland", "position_name": "Forward", "team": "Man City", "price": 14.0, "uncertainty_percent": "24%", "overall_total": 47.0, "gw1_points": 5.1, "gw2_points": 6.3, "gw3_points": 5.1, "gw4_points": 5.8, "gw5_points": 3.8, "gw6_points": 6.6, "gw7_points": 4.8, "gw8_points": 5.1, "gw9_points": 4.4, "points_per_million": 3.36},
        {"id": 1003, "name": "Palmer", "position_name": "Midfielder", "team": "Chelsea", "price": 10.5, "uncertainty_percent": "28%", "overall_total": 45.8, "gw1_points": 5.1, "gw2_points": 4.9, "gw3_points": 5.5, "gw4_points": 4.6, "gw5_points": 4.3, "gw6_points": 5.9, "gw7_points": 4.4, "gw8_points": 4.3, "gw9_points": 6.7, "points_per_million": 4.36},
        {"id": 1004, "name": "Watkins", "position_name": "Forward", "team": "Aston Villa", "price": 9.0, "uncertainty_percent": "24%", "overall_total": 44.9, "gw1_points": 5.2, "gw2_points": 4.6, "gw3_points": 4.8, "gw4_points": 4.1, "gw5_points": 5.7, "gw6_points": 5.2, "gw7_points": 6.6, "gw8_points": 4.5, "gw9_points": 4.1, "points_per_million": 4.99},
        {"id": 1005, "name": "Isak", "position_name": "Forward", "team": "Newcastle", "price": 10.5, "uncertainty_percent": "24%", "overall_total": 44.6, "gw1_points": 4.4, "gw2_points": 4.5, "gw3_points": 5.8, "gw4_points": 5.7, "gw5_points": 4.7, "gw6_points": 4.1, "gw7_points": 5.4, "gw8_points": 4.7, "gw9_points": 5.4, "points_per_million": 4.25},
        {"id": 1006, "name": "Wood", "position_name": "Forward", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 40.3, "gw1_points": 4.8, "gw2_points": 3.9, "gw3_points": 5.2, "gw4_points": 3.2, "gw5_points": 4.8, "gw6_points": 5.8, "gw7_points": 3.9, "gw8_points": 4.6, "gw9_points": 4.0, "points_per_million": 5.37},
        {"id": 1007, "name": "Eze", "position_name": "Midfielder", "team": "Crystal Palace", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 39.4, "gw1_points": 4.1, "gw2_points": 4.8, "gw3_points": 4.0, "gw4_points": 5.8, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 4.0, "gw8_points": 4.9, "gw9_points": 3.4, "points_per_million": 5.25},
        {"id": 1008, "name": "Saka", "position_name": "Midfielder", "team": "Arsenal", "price": 10.0, "uncertainty_percent": "29%", "overall_total": 37.8, "gw1_points": 3.9, "gw2_points": 5.9, "gw3_points": 3.3, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.7, "gw7_points": 4.6, "gw8_points": 3.6, "gw9_points": 4.5, "points_per_million": 3.78},
        {"id": 1009, "name": "Evanilson", "position_name": "Forward", "team": "Fulham", "price": 7.0, "uncertainty_percent": "24%", "overall_total": 36.9, "gw1_points": 3.4, "gw2_points": 4.6, "gw3_points": 3.9, "gw4_points": 4.2, "gw5_points": 4.3, "gw6_points": 4.7, "gw7_points": 4.0, "gw8_points": 3.6, "gw9_points": 4.2, "points_per_million": 5.27},
        {"id": 1010, "name": "Wissa", "position_name": "Forward", "team": "Brentford", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 36.6, "gw1_points": 3.8, "gw2_points": 4.4, "gw3_points": 4.7, "gw4_points": 4.0, "gw5_points": 3.7, "gw6_points": 4.5, "gw7_points": 3.8, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 4.88},
        {"id": 1011, "name": "B.Fernandes", "position_name": "Midfielder", "team": "Man United", "price": 9.0, "uncertainty_percent": "29%", "overall_total": 35.4, "gw1_points": 3.4, "gw2_points": 3.7, "gw3_points": 4.9, "gw4_points": 3.1, "gw5_points": 4.1, "gw6_points": 3.8, "gw7_points": 5.3, "gw8_points": 2.9, "gw9_points": 4.1, "points_per_million": 3.93},
        {"id": 1012, "name": "Virgil", "position_name": "Defender", "team": "Liverpool", "price": 6.0, "uncertainty_percent": "24%", "overall_total": 35.1, "gw1_points": 4.2, "gw2_points": 3.2, "gw3_points": 3.5, "gw4_points": 4.4, "gw5_points": 4.6, "gw6_points": 3.7, "gw7_points": 3.3, "gw8_points": 4.4, "gw9_points": 3.8, "points_per_million": 5.85},
        {"id": 1013, "name": "Gibbs-White", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 35.1, "gw1_points": 4.3, "gw2_points": 3.5, "gw3_points": 4.4, "gw4_points": 2.9, "gw5_points": 4.2, "gw6_points": 5.2, "gw7_points": 3.4, "gw8_points": 3.9, "gw9_points": 3.4, "points_per_million": 4.68},
        {"id": 1014, "name": "Strand Larsen", "position_name": "Forward", "team": "Wolves", "price": 6.5, "uncertainty_percent": "25%", "overall_total": 34.8, "gw1_points": 3.2, "gw2_points": 3.5, "gw3_points": 3.7, "gw4_points": 3.4, "gw5_points": 5.1, "gw6_points": 3.5, "gw7_points": 3.8, "gw8_points": 4.3, "gw9_points": 4.4, "points_per_million": 5.35},
        {"id": 1015, "name": "Rice", "position_name": "Midfielder", "team": "Arsenal", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 34.4, "gw1_points": 3.7, "gw2_points": 5.0, "gw3_points": 3.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.5, "gw7_points": 4.1, "gw8_points": 3.6, "gw9_points": 4.0, "points_per_million": 5.29},
        {"id": 1016, "name": "Rogers", "position_name": "Midfielder", "team": "Aston Villa", "price": 7.0, "uncertainty_percent": "28%", "overall_total": 33.7, "gw1_points": 1.1, "gw2_points": 4.0, "gw3_points": 4.2, "gw4_points": 3.7, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 5.2, "gw8_points": 3.7, "gw9_points": 3.3, "points_per_million": 4.81},
        {"id": 1017, "name": "Sánchez", "position_name": "Goalkeeper", "team": "Chelsea", "price": 5.0, "uncertainty_percent": "22%", "overall_total": 33.7, "gw1_points": 4.0, "gw2_points": 3.7, "gw3_points": 4.0, "gw4_points": 3.5, "gw5_points": 3.7, "gw6_points": 3.9, "gw7_points": 3.3, "gw8_points": 3.3, "gw9_points": 4.3, "points_per_million": 6.74},
        {"id": 1018, "name": "Welbeck", "position_name": "Forward", "team": "Brighton", "price": 6.5, "uncertainty_percent": "26%", "overall_total": 33.5, "gw1_points": 4.1, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.4, "gw5_points": 4.1, "gw6_points": 3.3, "gw7_points": 4.0, "gw8_points": 4.2, "gw9_points": 3.5, "points_per_million": 5.15},
        {"id": 1019, "name": "Mac Allister", "position_name": "Midfielder", "team": "Liverpool", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.4, "gw1_points": 4.0, "gw2_points": 3.5, "gw3_points": 3.2, "gw4_points": 4.0, "gw5_points": 3.9, "gw6_points": 3.6, "gw7_points": 3.2, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 5.14},
        {"id": 1020, "name": "Petrović", "position_name": "Goalkeeper", "team": "Chelsea", "price": 4.5, "uncertainty_percent": "21%", "overall_total": 33.3, "gw1_points": 3.4, "gw2_points": 3.9, "gw3_points": 3.3, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 3.8, "gw7_points": 3.8, "gw8_points": 3.9, "gw9_points": 3.8, "points_per_million": 7.40},
        {"id": 1021, "name": "Muñoz", "position_name": "Defender", "team": "Crystal Palace", "price": 5.5, "uncertainty_percent": "28%", "overall_total": 33.3, "gw1_points": 2.9, "gw2_points": 4.2, "gw3_points": 3.2, "gw4_points": 5.3, "gw5_points": 3.7, "gw6_points": 3.3, "gw7_points": 3.9, "gw8_points": 4.3, "gw9_points": 2.7, "points_per_million": 6.05},
        {"id": 1022, "name": "Bruno G.", "position_name": "Midfielder", "team": "Fulham", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.0, "gw1_points": 3.4, "gw2_points": 3.5, "gw3_points": 4.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.1, "gw7_points": 3.9, "gw8_points": 3.5, "gw9_points": 3.9, "points_per_million": 5.08},
        {"id": 1023, "name": "Schade", "position_name": "Midfielder", "team": "Brentford", "price": 7.0, "uncertainty_percent": "27%", "overall_total": 33.0, "gw1_points": 1.6, "gw2_points": 4.2, "gw3_points": 4.5, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 4.4, "gw7_points": 3.5, "gw8_points": 3.8, "gw9_points": 3.5, "points_per_million": 4.71},
        {"id": 1024, "name": "Saliba", "position_name": "Defender", "team": "Arsenal", "price": 6.0, "uncertainty_percent": "25%", "overall_total": 32.8, "gw1_points": 3.4, "gw2_points": 4.7, "gw3_points": 2.8, "gw4_points": 3.9, "gw5_points": 3.5, "gw6_points": 3.1, "gw7_points": 4.2, "gw8_points": 3.5, "gw9_points": 3.9, "points_per_million": 5.47},
        {"id": 1025, "name": "Leno", "position_name": "Goalkeeper", "team": "Fulham", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 32.7, "gw1_points": 3.8, "gw2_points": 4.1, "gw3_points": 3.5, "gw4_points": 4.2, "gw5_points": 3.8, "gw6_points": 3.2, "gw7_points": 3.9, "gw8_points": 3.3, "gw9_points": 3.0, "points_per_million": 6.54},
        {"id": 1026, "name": "Murillo", "position_name": "Defender", "team": "Nottingham Forest", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.6, "gw1_points": 3.9, "gw2_points": 3.4, "gw3_points": 3.9, "gw4_points": 3.0, "gw5_points": 4.0, "gw6_points": 4.6, "gw7_points": 2.8, "gw8_points": 3.4, "gw9_points": 3.5, "points_per_million": 5.93},
        {"id": 1027, "name": "Raya", "position_name": "Goalkeeper", "team": "Arsenal", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.5, "gw1_points": 3.3, "gw2_points": 4.3, "gw3_points": 3.3, "gw4_points": 3.7, "gw5_points": 3.5, "gw6_points": 3.1, "gw7_points": 4.3, "gw8_points": 3.3, "gw9_points": 3.8, "points_per_million": 5.91},
        {"id": 1028, "name": "Milenković", "position_name": "Defender", "team": "Fulham", "price": 5.5, "uncertainty_percent": "27%", "overall_total": 32.5, "gw1_points": 4.0, "gw2_points": 3.2, "gw3_points": 4.1, "gw4_points": 2.7, "gw5_points": 4.1, "gw6_points": 4.7, "gw7_points": 2.7, "gw8_points": 3.5, "gw9_points": 3.4, "points_per_million": 5.91},
        {"id": 1029, "name": "Branthwaite", "position_name": "Defender", "team": "Everton", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.0, "gw1_points": 4.0, "gw2_points": 3.8, "gw3_points": 3.5, "gw4_points": 3.5, "gw5_points": 3.0, "gw6_points": 3.9, "gw7_points": 3.7, "gw8_points": 3.0, "gw9_points": 3.5, "points_per_million": 5.82},
        {"id": 1030, "name": "Martinelli", "position_name": "Midfielder", "team": "Arsenal", "price": 7.0, "uncertainty_percent": "32%", "overall_total": 31.7, "gw1_points": 3.1, "gw2_points": 4.6, "gw3_points": 2.9, "gw4_points": 3.8, "gw5_points": 3.2, "gw6_points": 3.0, "gw7_points": 4.0, "gw8_points": 3.4, "gw9_points": 3.7, "points_per_million": 4.53},
        {"id": 1031, "name": "Sarr", "position_name": "Midfielder", "team": "Tottenham", "price": 6.5, "uncertainty_percent": "27%", "overall_total": 31.6, "gw1_points": 3.1, "gw2_points": 3.9, "gw3_points": 3.1, "gw4_points": 4.7, "gw5_points": 3.7, "gw6_points": 3.3, "gw7_points": 3.3, "gw8_points": 3.7, "gw9_points": 2.8, "points_per_million": 4.86},
        {"id": 1032, "name": "Lacroix", "position_name": "Defender", "team": "Wolves", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 31.5, "gw1_points": 2.8, "gw2_points": 3.6, "gw3_points": 3.0, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.3, "gw7_points": 3.9, "gw8_points": 3.7, "gw9_points": 3.0, "points_per_million": 6.30},
        {"id": 1033, "name": "Tarkowski", "position_name": "Defender", "team": "Everton", "price": 5.5, "uncertainty_percent": "26%", "overall_total": 31.2, "gw1_points": 3.9, "gw2_points": 3.6, "gw3_points": 3.5, "gw4_points": 3.6, "gw5_points": 3.0, "gw6_points": 3.6, "gw7_points": 3.8, "gw8_points": 2.7, "gw9_points": 3.4, "points_per_million": 5.67},
        {"id": 1034, "name": "Mykolenko", "position_name": "Defender", "team": "Everton", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 31.0, "gw1_points": 4.0, "gw2_points": 3.6, "gw3_points": 3.4, "gw4_points": 3.5, "gw5_points": 2.6, "gw6_points": 3.9, "gw7_points": 3.8, "gw8_points": 2.7, "gw9_points": 3.5, "points_per_million": 6.20},
        {"id": 1035, "name": "McNeil", "position_name": "Midfielder", "team": "Everton", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 30.7, "gw1_points": 4.0, "gw2_points": 3.6, "gw3_points": 3.3, "gw4_points": 3.7, "gw5_points": 2.7, "gw6_points": 3.6, "gw7_points": 3.5, "gw8_points": 2.7, "gw9_points": 3.6, "points_per_million": 5.12},
        {"id": 1036, "name": "Tonali", "position_name": "Midfielder", "team": "Newcastle", "price": 5.5, "uncertainty_percent": "23%", "overall_total": 30.7, "gw1_points": 3.2, "gw2_points": 3.3, "gw3_points": 3.7, "gw4_points": 3.8, "gw5_points": 3.3, "gw6_points": 3.0, "gw7_points": 3.6, "gw8_points": 3.2, "gw9_points": 3.5, "points_per_million": 5.58},
        {"id": 1037, "name": "Johnson", "position_name": "Midfielder", "team": "Tottenham", "price": 7.0, "uncertainty_percent": "35%", "overall_total": 30.6, "gw1_points": 4.7, "gw2_points": 2.5, "gw3_points": 3.3, "gw4_points": 3.1, "gw5_points": 3.1, "gw6_points": 3.4, "gw7_points": 3.9, "gw8_points": 3.6, "gw9_points": 3.0, "points_per_million": 4.37},
        {"id": 1038, "name": "Konaté", "position_name": "Defender", "team": "Liverpool", "price": 5.5, "uncertainty_percent": "25%", "overall_total": 30.6, "gw1_points": 3.8, "gw2_points": 2.8, "gw3_points": 3.1, "gw4_points": 3.8, "gw5_points": 4.2, "gw6_points": 3.1, "gw7_points": 2.6, "gw8_points": 3.9, "gw9_points": 3.2, "points_per_million": 5.56},
        {"id": 1039, "name": "José Sá", "position_name": "Goalkeeper", "team": "Wolves", "price": 4.5, "uncertainty_percent": "23%", "overall_total": 30.3, "gw1_points": 3.5, "gw2_points": 3.6, "gw3_points": 3.9, "gw4_points": 1.9, "gw5_points": 3.3, "gw6_points": 3.1, "gw7_points": 3.6, "gw8_points": 3.5, "gw9_points": 4.0, "points_per_million": 6.73},
        {"id": 1040, "name": "Cucurella", "position_name": "Defender", "team": "Chelsea", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 30.3, "gw1_points": 3.7, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.1, "gw5_points": 3.0, "gw6_points": 3.6, "gw7_points": 2.7, "gw8_points": 2.8, "gw9_points": 4.5, "points_per_million": 5.05},
        {"id": 1041, "name": "Henderson", "position_name": "Goalkeeper", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 30.2, "gw1_points": 3.2, "gw2_points": 3.4, "gw3_points": 3.0, "gw4_points": 4.2, "gw5_points": 3.1, "gw6_points": 3.3, "gw7_points": 3.1, "gw8_points": 3.8, "gw9_points": 3.0, "points_per_million": 6.04},
        {"id": 1042, "name": "Verbruggen", "position_name": "Goalkeeper", "team": "Brighton", "price": 4.5, "uncertainty_percent": "23%", "overall_total": 30.1, "gw1_points": 3.6, "gw2_points": 3.8, "gw3_points": 3.2, "gw4_points": 3.5, "gw5_points": 3.4, "gw6_points": 2.8, "gw7_points": 3.3, "gw8_points": 3.1, "gw9_points": 3.4, "points_per_million": 6.69},
        {"id": 1043, "name": "Richards", "position_name": "Defender", "team": "Crystal Palace", "price": 4.5, "uncertainty_percent": "25%", "overall_total": 30.0, "gw1_points": 2.6, "gw2_points": 3.5, "gw3_points": 2.9, "gw4_points": 4.5, "gw5_points": 3.3, "gw6_points": 3.1, "gw7_points": 3.7, "gw8_points": 3.7, "gw9_points": 2.8, "points_per_million": 6.67},
        {"id": 1044, "name": "A.Becker", "position_name": "Goalkeeper", "team": "Liverpool", "price": 5.5, "uncertainty_percent": "25%", "overall_total": 30.0, "gw1_points": 3.9, "gw2_points": 2.7, "gw3_points": 2.8, "gw4_points": 3.6, "gw5_points": 4.0, "gw6_points": 3.4, "gw7_points": 2.2, "gw8_points": 4.1, "gw9_points": 3.4, "points_per_million": 5.45},
        {"id": 1045, "name": "Beto", "position_name": "Forward", "team": "Everton", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 29.9, "gw1_points": 3.8, "gw2_points": 3.4, "gw3_points": 3.2, "gw4_points": 3.5, "gw5_points": 2.8, "gw6_points": 3.6, "gw7_points": 3.4, "gw8_points": 2.7, "gw9_points": 3.6, "points_per_million": 5.44},
        {"id": 1046, "name": "Vicario", "position_name": "Goalkeeper", "team": "Tottenham", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 29.7, "gw1_points": 3.9, "gw2_points": 2.9, "gw3_points": 3.4, "gw4_points": 3.0, "gw5_points": 3.2, "gw6_points": 3.3, "gw7_points": 3.5, "gw8_points": 3.2, "gw9_points": 3.4, "points_per_million": 5.94},
        {"id": 1047, "name": "Rúben", "position_name": "Defender", "team": "Wolves", "price": 5.5, "uncertainty_percent": "26%", "overall_total": 29.7, "gw1_points": 3.4, "gw2_points": 3.5, "gw3_points": 3.1, "gw4_points": 3.7, "gw5_points": 2.5, "gw6_points": 4.0, "gw7_points": 3.0, "gw8_points": 3.7, "gw9_points": 2.8, "points_per_million": 5.40},
        {"id": 1048, "name": "Mitchell", "position_name": "Defender", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "27%", "overall_total": 29.7, "gw1_points": 2.7, "gw2_points": 3.6, "gw3_points": 2.9, "gw4_points": 4.6, "gw5_points": 3.2, "gw6_points": 2.9, "gw7_points": 3.5, "gw8_points": 3.8, "gw9_points": 2.4, "points_per_million": 5.94},
        {"id": 1049, "name": "Guéhi", "position_name": "Defender", "team": "Crystal Palace", "price": 4.5, "uncertainty_percent": "27%", "overall_total": 29.7, "gw1_points": 2.6, "gw2_points": 3.5, "gw3_points": 2.8, "gw4_points": 4.6, "gw5_points": 3.2, "gw6_points": 3.0, "gw7_points": 3.6, "gw8_points": 3.7, "gw9_points": 2.7, "points_per_million": 6.60},
        {"id": 1050, "name": "Ndiaye", "position_name": "Midfielder", "team": "Sheffield United", "price": 6.5, "uncertainty_percent": "28%", "overall_total": 29.6, "gw1_points": 3.8, "gw2_points": 3.3, "gw3_points": 3.5, "gw4_points": 3.5, "gw5_points": 2.6, "gw6_points": 3.5, "gw7_points": 3.5, "gw8_points": 2.5, "gw9_points": 3.5, "points_per_million": 4.55},
        {"id": 1051, "name": "Tosin", "position_name": "Defender", "team": "Fulham", "price": 4.5, "uncertainty_percent": "27%", "overall_total": 29.6, "gw1_points": 3.5, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.1, "gw5_points": 2.9, "gw6_points": 3.5, "gw7_points": 2.7, "gw8_points": 2.7, "gw9_points": 4.4, "points_per_million": 6.58},
        {"id": 1052, "name": "Collins", "position_name": "Defender", "team": "Brentford", "price": 5.0, "uncertainty_percent": "26%", "overall_total": 29.5, "gw1_points": 3.0, "gw2_points": 3.2, "gw3_points": 4.0, "gw4_points": 3.1, "gw5_points": 3.2, "gw6_points": 3.6, "gw7_points": 3.1, "gw8_points": 3.3, "gw9_points": 3.0, "points_per_million": 5.90},
        {"id": 1053, "name": "Iwobi", "position_name": "Midfielder", "team": "Fulham", "price": 6.5, "uncertainty_percent": "30%", "overall_total": 29.5, "gw1_points": 3.0, "gw2_points": 3.5, "gw3_points": 2.9, "gw4_points": 4.3, "gw5_points": 3.9, "gw6_points": 3.1, "gw7_points": 3.1, "gw8_points": 2.8, "gw9_points": 3.0, "points_per_million": 4.54},
        {"id": 1054, "name": "Wirtz", "position_name": "Midfielder", "team": "Bayer Leverkusen", "price": 8.5, "uncertainty_percent": "29%", "overall_total": 29.4, "gw1_points": 3.6, "gw2_points": 3.1, "gw3_points": 2.8, "gw4_points": 3.5, "gw5_points": 3.4, "gw6_points": 3.1, "gw7_points": 2.9, "gw8_points": 3.6, "gw9_points": 3.4, "points_per_million": 3.46},
        {"id": 1055, "name": "Matheus N.", "position_name": "Defender", "team": "Wolves", "price": 5.5, "uncertainty_percent": "30%", "overall_total": 29.4, "gw1_points": 3.3, "gw2_points": 3.7, "gw3_points": 2.9, "gw4_points": 3.8, "gw5_points": 2.4, "gw6_points": 4.2, "gw7_points": 2.9, "gw8_points": 3.7, "gw9_points": 2.5, "points_per_million": 5.35},
        {"id": 1056, "name": "Martinez", "position_name": "Goalkeeper", "team": "Aston Villa", "price": 5.0, "uncertainty_percent": "22%", "overall_total": 29.3, "gw1_points": 0.0, "gw2_points": 3.2, "gw3_points": 3.9, "gw4_points": 3.8, "gw5_points": 3.5, "gw6_points": 3.9, "gw7_points": 4.4, "gw8_points": 3.0, "gw9_points": 3.6, "points_per_million": 5.86},
        {"id": 1057, "name": "Mepham", "position_name": "Defender", "team": "Bournemouth", "price": 4.0, "uncertainty_percent": "25%", "overall_total": 29.3, "gw1_points": 3.0, "gw2_points": 3.5, "gw3_points": 3.0, "gw4_points": 3.5, "gw5_points": 2.9, "gw6_points": 3.6, "gw7_points": 3.4, "gw8_points": 3.1, "gw9_points": 3.3, "points_per_million": 7.33},
        {"id": 1058, "name": "Chalobah", "position_name": "Defender", "team": "Chelsea", "price": 5.0, "uncertainty_percent": "26%", "overall_total": 29.3, "gw1_points": 3.5, "gw2_points": 3.2, "gw3_points": 3.5, "gw4_points": 3.1, "gw5_points": 2.9, "gw6_points": 3.4, "gw7_points": 2.7, "gw8_points": 2.7, "gw9_points": 4.3, "points_per_million": 5.86},
        {"id": 1059, "name": "Neto", "position_name": "Midfielder", "team": "Wolves", "price": 7.0, "uncertainty_percent": "29%", "overall_total": 29.2, "gw1_points": 3.5, "gw2_points": 3.0, "gw3_points": 3.3, "gw4_points": 3.0, "gw5_points": 3.1, "gw6_points": 3.4, "gw7_points": 2.6, "gw8_points": 2.9, "gw9_points": 4.3, "points_per_million": 4.17},
        {"id": 1060, "name": "Frimpong", "position_name": "Defender", "team": "Bayer Leverkusen", "price": 6.0, "uncertainty_percent": "27%", "overall_total": 29.0, "gw1_points": 3.9, "gw2_points": 2.7, "gw3_points": 2.7, "gw4_points": 3.8, "gw5_points": 4.0, "gw6_points": 2.8, "gw7_points": 2.3, "gw8_points": 3.7, "gw9_points": 3.1, "points_per_million": 4.83},
        {"id": 1061, "name": "Nørgaard", "position_name": "Midfielder", "team": "Brentford", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 29.0, "gw1_points": 2.8, "gw2_points": 3.7, "gw3_points": 2.9, "gw4_points": 3.5, "gw5_points": 2.9, "gw6_points": 3.1, "gw7_points": 3.7, "gw8_points": 3.0, "gw9_points": 3.4, "points_per_million": 5.27},
        {"id": 1062, "name": "Anderson", "position_name": "Midfielder", "team": "Crystal Palace", "price": 5.5, "uncertainty_percent": "21%", "overall_total": 29.0, "gw1_points": 3.6, "gw2_points": 3.1, "gw3_points": 3.6, "gw4_points": 2.6, "gw5_points": 3.4, "gw6_points": 3.5, "gw7_points": 2.8, "gw8_points": 3.2, "gw9_points": 3.1, "points_per_million": 5.27},
        {"id": 1063, "name": "Enzo", "position_name": "Midfielder", "team": "Chelsea", "price": 6.5, "uncertainty_percent": "28%", "overall_total": 29.0, "gw1_points": 3.6, "gw2_points": 3.2, "gw3_points": 3.3, "gw4_points": 2.9, "gw5_points": 2.8, "gw6_points": 3.3, "gw7_points": 2.9, "gw8_points": 2.8, "gw9_points": 4.1, "points_per_million": 4.46},
        {"id": 1064, "name": "Andersen", "position_name": "Defender", "team": "Crystal Palace", "price": 4.5, "uncertainty_percent": "26%", "overall_total": 28.9, "gw1_points": 3.3, "gw2_points": 3.6, "gw3_points": 2.7, "gw4_points": 4.0, "gw5_points": 3.7, "gw6_points": 2.7, "gw7_points": 3.4, "gw8_points": 3.0, "gw9_points": 2.4, "points_per_million": 6.42},
        {"id": 1065, "name": "Gana", "position_name": "Midfielder", "team": "Everton", "price": 5.5, "uncertainty_percent": "21%", "overall_total": 28.6, "gw1_points": 3.3, "gw2_points": 3.4, "gw3_points": 3.1, "gw4_points": 3.3, "gw5_points": 2.8, "gw6_points": 3.5, "gw7_points": 3.1, "gw8_points": 2.6, "gw9_points": 3.4, "points_per_million": 5.20},
        {"id": 1066, "name": "Mateta", "position_name": "Forward", "team": "Crystal Palace", "price": 7.5, "uncertainty_percent": "27%", "overall_total": 28.4, "gw1_points": 3.0, "gw2_points": 3.5, "gw3_points": 3.1, "gw4_points": 4.0, "gw5_points": 3.4, "gw6_points": 3.2, "gw7_points": 2.9, "gw8_points": 3.0, "gw9_points": 2.2, "points_per_million": 3.79},
        {"id": 1067, "name": "Lewis-Skelly", "position_name": "Defender", "team": "Arsenal", "price": 5.5, "uncertainty_percent": "29%", "overall_total": 28.4, "gw1_points": 2.9, "gw2_points": 4.0, "gw3_points": 2.2, "gw4_points": 3.5, "gw5_points": 2.9, "gw6_points": 2.7, "gw7_points": 3.7, "gw8_points": 2.9, "gw9_points": 3.5, "points_per_million": 5.16},
        {"id": 1068, "name": "Hudson-Odoi", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 28.2, "gw1_points": 3.5, "gw2_points": 2.9, "gw3_points": 3.7, "gw4_points": 2.4, "gw5_points": 3.4, "gw6_points": 3.9, "gw7_points": 2.7, "gw8_points": 3.1, "gw9_points": 2.7, "points_per_million": 4.70},
        {"id": 1069, "name": "Trippier", "position_name": "Defender", "team": "Newcastle", "price": 5.0, "uncertainty_percent": "29%", "overall_total": 28.1, "gw1_points": 2.7, "gw2_points": 2.6, "gw3_points": 3.8, "gw4_points": 3.6, "gw5_points": 2.7, "gw6_points": 2.7, "gw7_points": 3.6, "gw8_points": 2.7, "gw9_points": 3.6, "points_per_million": 5.62},
        {"id": 1070, "name": "Konsa", "position_name": "Defender", "team": "Aston Villa", "price": 4.5, "uncertainty_percent": "28%", "overall_total": 28.0, "gw1_points": 2.9, "gw2_points": 2.6, "gw3_points": 3.5, "gw4_points": 3.1, "gw5_points": 3.3, "gw6_points": 3.4, "gw7_points": 4.0, "gw8_points": 2.3, "gw9_points": 2.9, "points_per_million": 6.22},
        {"id": 1071, "name": "Raúl", "position_name": "Forward", "team": "Wolves", "price": 6.5, "uncertainty_percent": "34%", "overall_total": 27.9, "gw1_points": 3.0, "gw2_points": 3.5, "gw3_points": 2.6, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 2.8, "gw7_points": 3.0, "gw8_points": 2.7, "gw9_points": 2.8, "points_per_million": 4.29},
        {"id": 1072, "name": "Gomes", "position_name": "Midfielder", "team": "Wolves", "price": 5.5, "uncertainty_percent": "21%", "overall_total": 27.6, "gw1_points": 2.7, "gw2_points": 3.0, "gw3_points": 3.2, "gw4_points": 2.8, "gw5_points": 3.4, "gw6_points": 3.0, "gw7_points": 3.0, "gw8_points": 2.9, "gw9_points": 3.5, "points_per_million": 5.02},
        {"id": 1073, "name": "Onana", "position_name": "Goalkeeper", "team": "Man United", "price": 5.0, "uncertainty_percent": "25%", "overall_total": 27.6, "gw1_points": 0.9, "gw2_points": 3.1, "gw3_points": 3.9, "gw4_points": 3.1, "gw5_points": 3.6, "gw6_points": 3.0, "gw7_points": 3.1, "gw8_points": 2.9, "gw9_points": 3.8, "points_per_million": 5.52},
        {"id": 1074, "name": "Kilman", "position_name": "Defender", "team": "Wolves", "price": 4.5, "uncertainty_percent": "27%", "overall_total": 27.5, "gw1_points": 3.7, "gw2_points": 2.6, "gw3_points": 2.6, "gw4_points": 3.0, "gw5_points": 3.0, "gw6_points": 3.5, "gw7_points": 2.6, "gw8_points": 3.3, "gw9_points": 3.3, "points_per_million": 6.11},
        {"id": 1075, "name": "Neil", "position_name": "Midfielder", "team": "Brentford", "price": 5.0, "uncertainty_percent": "20%", "overall_total": 27.5, "gw1_points": 3.2, "gw2_points": 3.2, "gw3_points": 3.2, "gw4_points": 2.9, "gw5_points": 3.1, "gw6_points": 2.9, "gw7_points": 3.0, "gw8_points": 3.2, "gw9_points": 2.7, "points_per_million": 5.50},
        {"id": 1076, "name": "Semenyo", "position_name": "Midfielder", "team": "Bournemouth", "price": 7.0, "uncertainty_percent": "35%", "overall_total": 27.5, "gw1_points": 2.5, "gw2_points": 3.3, "gw3_points": 3.1, "gw4_points": 3.2, "gw5_points": 3.1, "gw6_points": 3.4, "gw7_points": 2.8, "gw8_points": 2.8, "gw9_points": 3.2, "points_per_million": 3.93},
        {"id": 1077, "name": "Caicedo", "position_name": "Midfielder", "team": "Chelsea", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 27.4, "gw1_points": 3.4, "gw2_points": 3.1, "gw3_points": 3.2, "gw4_points": 2.9, "gw5_points": 2.9, "gw6_points": 3.1, "gw7_points": 2.9, "gw8_points": 2.7, "gw9_points": 3.2, "points_per_million": 4.98},
        {"id": 1078, "name": "Patterson", "position_name": "Goalkeeper", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "26%", "overall_total": 27.3, "gw1_points": 3.3, "gw2_points": 3.4, "gw3_points": 3.0, "gw4_points": 3.1, "gw5_points": 3.0, "gw6_points": 2.5, "gw7_points": 3.1, "gw8_points": 3.0, "gw9_points": 2.9, "points_per_million": 6.07},
        {"id": 1079, "name": "O.Dango", "position_name": "Midfielder", "team": "Bournemouth", "price": 6.0, "uncertainty_percent": "25%", "overall_total": 27.3, "gw1_points": 2.6, "gw2_points": 3.1, "gw3_points": 3.1, "gw4_points": 3.0, "gw5_points": 3.2, "gw6_points": 3.4, "gw7_points": 3.2, "gw8_points": 2.7, "gw9_points": 3.0, "points_per_million": 4.55},
        {"id": 1080, "name": "Mbeumo", "position_name": "Midfielder", "team": "Brentford", "price": 8.0, "uncertainty_percent": "27%", "overall_total": 27.1, "gw1_points": 2.6, "gw2_points": 2.9, "gw3_points": 3.8, "gw4_points": 2.5, "gw5_points": 3.0, "gw6_points": 2.9, "gw7_points": 3.8, "gw8_points": 2.5, "gw9_points": 3.2, "points_per_million": 3.39},
        {"id": 1081, "name": "Cash", "position_name": "Defender", "team": "Aston Villa", "price": 4.5, "uncertainty_percent": "29%", "overall_total": 27.1, "gw1_points": 2.8, "gw2_points": 2.6, "gw3_points": 3.4, "gw4_points": 3.0, "gw5_points": 2.9, "gw6_points": 3.3, "gw7_points": 4.3, "gw8_points": 2.2, "gw9_points": 2.7, "points_per_million": 6.02},
        {"id": 1082, "name": "Barnes", "position_name": "Midfielder", "team": "Newcastle", "price": 6.5, "uncertainty_percent": "38%", "overall_total": 27.0, "gw1_points": 3.0, "gw2_points": 3.0, "gw3_points": 3.5, "gw4_points": 3.5, "gw5_points": 2.9, "gw6_points": 2.4, "gw7_points": 3.3, "gw8_points": 2.7, "gw9_points": 2.8, "points_per_million": 4.15},
        {"id": 1083, "name": "Adams", "position_name": "Midfielder", "team": "Southampton", "price": 5.0, "uncertainty_percent": "21%", "overall_total": 27.0, "gw1_points": 2.9, "gw2_points": 3.3, "gw3_points": 3.0, "gw4_points": 3.1, "gw5_points": 2.9, "gw6_points": 3.0, "gw7_points": 3.0, "gw8_points": 2.8, "gw9_points": 3.0, "points_per_million": 5.40},
        {"id": 1084, "name": "Kluivert", "position_name": "Midfielder", "team": "Bournemouth", "price": 7.0, "uncertainty_percent": "37%", "overall_total": 27.0, "gw1_points": 0.0, "gw2_points": 1.1, "gw3_points": 3.6, "gw4_points": 4.0, "gw5_points": 3.6, "gw6_points": 4.0, "gw7_points": 3.8, "gw8_points": 3.1, "gw9_points": 3.8, "points_per_million": 3.86},
        {"id": 1085, "name": "Aina", "position_name": "Defender", "team": "Nottingham Forest", "price": 5.0, "uncertainty_percent": "27%", "overall_total": 27.0, "gw1_points": 3.4, "gw2_points": 2.7, "gw3_points": 3.5, "gw4_points": 2.0, "gw5_points": 3.6, "gw6_points": 3.8, "gw7_points": 2.1, "gw8_points": 3.0, "gw9_points": 2.7, "points_per_million": 5.40},
        {"id": 1086, "name": "Gabriel", "position_name": "Defender", "team": "Arsenal", "price": 6.0, "uncertainty_percent": "33%", "overall_total": 27.0, "gw1_points": 3.2, "gw2_points": 3.7, "gw3_points": 2.2, "gw4_points": 3.1, "gw5_points": 2.8, "gw6_points": 2.6, "gw7_points": 3.2, "gw8_points": 2.8, "gw9_points": 3.3, "points_per_million": 4.50},
        {"id": 1087, "name": "Kelleher", "position_name": "Goalkeeper", "team": "Liverpool", "price": 4.5, "uncertainty_percent": "25%", "overall_total": 26.9, "gw1_points": 2.3, "gw2_points": 3.2, "gw3_points": 2.3, "gw4_points": 3.4, "gw5_points": 3.0, "gw6_points": 3.8, "gw7_points": 2.4, "gw8_points": 3.2, "gw9_points": 3.1, "points_per_million": 5.98},
        {"id": 1088, "name": "L.Paquetá", "position_name": "Midfielder", "team": "West Ham", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 26.8, "gw1_points": 3.1, "gw2_points": 3.0, "gw3_points": 2.8, "gw4_points": 3.1, "gw5_points": 3.0, "gw6_points": 2.9, "gw7_points": 2.3, "gw8_points": 3.1, "gw9_points": 3.4, "points_per_million": 4.47},
        {"id": 1089, "name": "Wilson", "position_name": "Forward", "team": "Newcastle", "price": 6.0, "uncertainty_percent": "25%", "overall_total": 26.7, "gw1_points": 3.2, "gw2_points": 2.9, "gw3_points": 2.8, "gw4_points": 3.3, "gw5_points": 3.1, "gw6_points": 2.8, "gw7_points": 2.3, "gw8_points": 3.2, "gw9_points": 3.2, "points_per_million": 4.45},
        {"id": 1090, "name": "Toti", "position_name": "Defender", "team": "Wolves", "price": 4.5, "uncertainty_percent": "29%", "overall_total": 26.5, "gw1_points": 2.6, "gw2_points": 2.8, "gw3_points": 3.6, "gw4_points": 2.1, "gw5_points": 3.8, "gw6_points": 2.3, "gw7_points": 2.7, "gw8_points": 3.2, "gw9_points": 3.5, "points_per_million": 5.89},
        {"id": 1091, "name": "Henderson", "position_name": "Midfielder", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "21%", "overall_total": 26.5, "gw1_points": 2.8, "gw2_points": 3.1, "gw3_points": 3.2, "gw4_points": 2.9, "gw5_points": 2.8, "gw6_points": 3.2, "gw7_points": 2.8, "gw8_points": 2.9, "gw9_points": 2.7, "points_per_million": 5.30},
        {"id": 1092, "name": "João Pedro", "position_name": "Forward", "team": "Brighton", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 26.4, "gw1_points": 3.1, "gw2_points": 2.9, "gw3_points": 3.0, "gw4_points": 2.7, "gw5_points": 2.6, "gw6_points": 3.1, "gw7_points": 2.6, "gw8_points": 2.7, "gw9_points": 3.6, "points_per_million": 3.52},
        {"id": 1093, "name": "Potts", "position_name": "Midfielder", "team": "Luton", "price": 4.5, "uncertainty_percent": "21%", "overall_total": 26.2, "gw1_points": 3.1, "gw2_points": 2.9, "gw3_points": 2.7, "gw4_points": 3.2, "gw5_points": 3.0, "gw6_points": 2.8, "gw7_points": 2.4, "gw8_points": 3.1, "gw9_points": 3.1, "points_per_million": 5.82},
        {"id": 1094, "name": "Ekitiké", "position_name": "Forward", "team": "PSG", "price": 8.5, "uncertainty_percent": "32%", "overall_total": 26.2, "gw1_points": 3.1, "gw2_points": 2.6, "gw3_points": 2.4, "gw4_points": 3.3, "gw5_points": 2.8, "gw6_points": 3.1, "gw7_points": 2.6, "gw8_points": 2.9, "gw9_points": 3.4, "points_per_million": 3.08},
        {"id": 1095, "name": "N.Williams", "position_name": "Defender", "team": "Nottingham Forest", "price": 5.0, "uncertainty_percent": "29%", "overall_total": 26.2, "gw1_points": 3.3, "gw2_points": 2.6, "gw3_points": 3.4, "gw4_points": 2.1, "gw5_points": 3.4, "gw6_points": 3.7, "gw7_points": 2.0, "gw8_points": 2.9, "gw9_points": 2.7, "points_per_million": 5.24},
        {"id": 1096, "name": "Gündoğan", "position_name": "Midfielder", "team": "Barcelona", "price": 6.5, "uncertainty_percent": "33%", "overall_total": 26.2, "gw1_points": 3.2, "gw2_points": 3.4, "gw3_points": 2.9, "gw4_points": 3.0, "gw5_points": 2.2, "gw6_points": 3.7, "gw7_points": 2.6, "gw8_points": 2.6, "gw9_points": 2.5, "points_per_million": 4.03},
        {"id": 1097, "name": "Joelinton", "position_name": "Midfielder", "team": "Newcastle", "price": 6.0, "uncertainty_percent": "25%", "overall_total": 26.0, "gw1_points": 2.6, "gw2_points": 2.9, "gw3_points": 3.4, "gw4_points": 3.2, "gw5_points": 2.7, "gw6_points": 2.5, "gw7_points": 3.1, "gw8_points": 2.6, "gw9_points": 3.1, "points_per_million": 4.33},
        {"id": 1098, "name": "Ward-Prowse", "position_name": "Midfielder", "team": "West Ham", "price": 6.0, "uncertainty_percent": "23%", "overall_total": 26.0, "gw1_points": 3.1, "gw2_points": 2.9, "gw3_points": 2.7, "gw4_points": 3.1, "gw5_points": 3.0, "gw6_points": 2.8, "gw7_points": 2.3, "gw8_points": 3.1, "gw9_points": 3.1, "points_per_million": 4.33},
        {"id": 1099, "name": "Smith Rowe", "position_name": "Midfielder", "team": "Arsenal", "price": 6.0, "uncertainty_percent": "34%", "overall_total": 26.0, "gw1_points": 2.7, "gw2_points": 3.1, "gw3_points": 2.4, "gw4_points": 3.8, "gw5_points": 3.3, "gw6_points": 2.5, "gw7_points": 2.8, "gw8_points": 2.7, "gw9_points": 2.6, "points_per_million": 4.33},
        {"id": 1100, "name": "Senesi", "position_name": "Defender", "team": "Bournemouth", "price": 4.5, "uncertainty_percent": "31%", "overall_total": 26.0, "gw1_points": 2.3, "gw2_points": 3.3, "gw3_points": 2.5, "gw4_points": 3.2, "gw5_points": 2.6, "gw6_points": 3.2, "gw7_points": 3.1, "gw8_points": 2.7, "gw9_points": 3.0, "points_per_million": 5.78},
        {"id": 1101, "name": "Agbadou", "position_name": "Defender", "team": "Reims", "price": 4.5, "uncertainty_percent": "30%", "overall_total": 25.9, "gw1_points": 2.4, "gw2_points": 2.6, "gw3_points": 3.7, "gw4_points": 2.1, "gw5_points": 3.6, "gw6_points": 2.0, "gw7_points": 2.9, "gw8_points": 3.0, "gw9_points": 3.5, "points_per_million": 5.76},
        {"id": 1102, "name": "Roberts", "position_name": "Midfielder", "team": "Leeds", "price": 5.5, "uncertainty_percent": "27%", "overall_total": 25.8, "gw1_points": 3.2, "gw2_points": 3.2, "gw3_points": 2.9, "gw4_points": 2.6, "gw5_points": 2.7, "gw6_points": 2.7, "gw7_points": 2.9, "gw8_points": 3.1, "gw9_points": 2.5, "points_per_million": 4.69},
        {"id": 1103, "name": "Hoever", "position_name": "Defender", "team": "Wolves", "price": 4.0, "uncertainty_percent": "28%", "overall_total": 25.7, "gw1_points": 2.5, "gw2_points": 2.5, "gw3_points": 3.6, "gw4_points": 1.9, "gw5_points": 3.7, "gw6_points": 2.1, "gw7_points": 2.9, "gw8_points": 2.7, "gw9_points": 3.9, "points_per_million": 6.43},
        {"id": 1104, "name": "Schär", "position_name": "Defender", "team": "Newcastle", "price": 5.5, "uncertainty_percent": "33%", "overall_total": 25.7, "gw1_points": 2.5, "gw2_points": 2.5, "gw3_points": 3.4, "gw4_points": 3.1, "gw5_points": 2.5, "gw6_points": 2.5, "gw7_points": 3.3, "gw8_points": 2.6, "gw9_points": 3.5, "points_per_million": 4.67},
        {"id": 1105, "name": "Hladký", "position_name": "Goalkeeper", "team": "Ipswich", "price": 4.0, "uncertainty_percent": "25%", "overall_total": 25.7, "gw1_points": 3.0, "gw2_points": 3.1, "gw3_points": 3.3, "gw4_points": 3.0, "gw5_points": 2.9, "gw6_points": 3.2, "gw7_points": 1.1, "gw8_points": 3.3, "gw9_points": 2.9, "points_per_million": 6.43},
        {"id": 1106, "name": "Wan-Bissaka", "position_name": "Defender", "team": "Man United", "price": 4.5, "uncertainty_percent": "30%", "overall_total": 25.5, "gw1_points": 3.4, "gw2_points": 2.7, "gw3_points": 2.4, "gw4_points": 2.9, "gw5_points": 2.9, "gw6_points": 3.2, "gw7_points": 2.0, "gw8_points": 2.9, "gw9_points": 3.1, "points_per_million": 5.67},
        {"id": 1107, "name": "Mitoma", "position_name": "Midfielder", "team": "Brighton", "price": 6.5, "uncertainty_percent": "31%", "overall_total": 25.4, "gw1_points": 3.3, "gw2_points": 3.0, "gw3_points": 3.0, "gw4_points": 2.8, "gw5_points": 2.8, "gw6_points": 2.1, "gw7_points": 2.6, "gw8_points": 2.9, "gw9_points": 2.7, "points_per_million": 3.91},
        {"id": 1108, "name": "Gvardiol", "position_name": "Defender", "team": "Man City", "price": 6.0, "uncertainty_percent": "35%", "overall_total": 25.4, "gw1_points": 0.8, "gw2_points": 3.0, "gw3_points": 2.6, "gw4_points": 3.4, "gw5_points": 2.3, "gw6_points": 4.1, "gw7_points": 2.8, "gw8_points": 3.9, "gw9_points": 2.4, "points_per_million": 4.23},
        {"id": 1109, "name": "Wilson", "position_name": "Midfielder", "team": "Bournemouth", "price": 5.5, "uncertainty_percent": "36%", "overall_total": 25.3, "gw1_points": 2.7, "gw2_points": 3.0, "gw3_points": 2.5, "gw4_points": 4.1, "gw5_points": 3.1, "gw6_points": 2.6, "gw7_points": 2.5, "gw8_points": 2.4, "gw9_points": 2.5, "points_per_million": 4.60},
        {"id": 1110, "name": "Van den Berg", "position_name": "Defender", "team": "Liverpool", "price": 4.5, "uncertainty_percent": "29%", "overall_total": 25.3, "gw1_points": 2.6, "gw2_points": 2.8, "gw3_points": 3.3, "gw4_points": 2.8, "gw5_points": 2.5, "gw6_points": 3.3, "gw7_points": 2.6, "gw8_points": 2.9, "gw9_points": 2.5, "points_per_million": 5.62},
        {"id": 1111, "name": "C.Jones", "position_name": "Midfielder", "team": "Liverpool", "price": 5.5, "uncertainty_percent": "27%", "overall_total": 25.3, "gw1_points": 3.5, "gw2_points": 2.6, "gw3_points": 2.5, "gw4_points": 2.9, "gw5_points": 3.1, "gw6_points": 2.7, "gw7_points": 2.4, "gw8_points": 3.0, "gw9_points": 2.7, "points_per_million": 4.60},
        {"id": 1112, "name": "Buendía", "position_name": "Midfielder", "team": "Aston Villa", "price": 5.5, "uncertainty_percent": "34%", "overall_total": 25.2, "gw1_points": 3.6, "gw2_points": 2.4, "gw3_points": 2.7, "gw4_points": 2.2, "gw5_points": 3.1, "gw6_points": 2.8, "gw7_points": 3.6, "gw8_points": 2.6, "gw9_points": 2.3, "points_per_million": 4.58},
        {"id": 1113, "name": "Van Hecke", "position_name": "Defender", "team": "Brighton", "price": 4.5, "uncertainty_percent": "29%", "overall_total": 25.2, "gw1_points": 3.2, "gw2_points": 3.3, "gw3_points": 2.5, "gw4_points": 2.7, "gw5_points": 2.9, "gw6_points": 2.1, "gw7_points": 3.0, "gw8_points": 2.6, "gw9_points": 2.8, "points_per_million": 5.60},
        {"id": 1114, "name": "Højlund", "position_name": "Forward", "team": "Man United", "price": 6.5, "uncertainty_percent": "31%", "overall_total": 25.2, "gw1_points": 2.6, "gw2_points": 2.7, "gw3_points": 3.5, "gw4_points": 2.2, "gw5_points": 2.7, "gw6_points": 2.7, "gw7_points": 3.5, "gw8_points": 2.4, "gw9_points": 2.9, "points_per_million": 3.88},
        {"id": 1115, "name": "Gravenberch", "position_name": "Midfielder", "team": "Liverpool", "price": 5.5, "uncertainty_percent": "19%", "overall_total": 25.1, "gw1_points": 0.0, "gw2_points": 3.0, "gw3_points": 2.9, "gw4_points": 3.4, "gw5_points": 3.4, "gw6_points": 3.0, "gw7_points": 2.9, "gw8_points": 3.4, "gw9_points": 3.1, "points_per_million": 4.56},
        {"id": 1116, "name": "André", "position_name": "Midfielder", "team": "Flamengo", "price": 5.5, "uncertainty_percent": "18%", "overall_total": 25.1, "gw1_points": 2.6, "gw2_points": 2.8, "gw3_points": 3.0, "gw4_points": 2.6, "gw5_points": 2.9, "gw6_points": 2.7, "gw7_points": 2.8, "gw8_points": 2.6, "gw9_points": 3.1, "points_per_million": 4.56},
        {"id": 1117, "name": "White", "position_name": "Defender", "team": "Arsenal", "price": 5.5, "uncertainty_percent": "36%", "overall_total": 24.8, "gw1_points": 3.0, "gw2_points": 3.3, "gw3_points": 2.0, "gw4_points": 3.1, "gw5_points": 2.7, "gw6_points": 2.5, "gw7_points": 2.8, "gw8_points": 2.4, "gw9_points": 2.9, "points_per_million": 4.51},
        {"id": 1118, "name": "Burn", "position_name": "Defender", "team": "Newcastle", "price": 5.0, "uncertainty_percent": "32%", "overall_total": 24.6, "gw1_points": 2.3, "gw2_points": 2.4, "gw3_points": 3.4, "gw4_points": 3.0, "gw5_points": 2.5, "gw6_points": 2.5, "gw7_points": 3.1, "gw8_points": 2.4, "gw9_points": 3.0, "points_per_million": 4.92},
        {"id": 1119, "name": "Onana", "position_name": "Midfielder", "team": "Everton", "price": 5.0, "uncertainty_percent": "29%", "overall_total": 24.5, "gw1_points": 2.7, "gw2_points": 2.5, "gw3_points": 2.7, "gw4_points": 2.6, "gw5_points": 3.0, "gw6_points": 2.9, "gw7_points": 3.4, "gw8_points": 2.4, "gw9_points": 2.4, "points_per_million": 4.90},
        {"id": 1120, "name": "Bowen", "position_name": "Forward", "team": "West Ham", "price": 8.0, "uncertainty_percent": "38%", "overall_total": 24.4, "gw1_points": 3.1, "gw2_points": 2.6, "gw3_points": 2.6, "gw4_points": 3.0, "gw5_points": 2.7, "gw6_points": 2.2, "gw7_points": 2.1, "gw8_points": 2.8, "gw9_points": 3.3, "points_per_million": 3.05},
        {"id": 1121, "name": "Souček", "position_name": "Midfielder", "team": "West Ham", "price": 6.0, "uncertainty_percent": "38%", "overall_total": 24.3, "gw1_points": 3.3, "gw2_points": 2.5, "gw3_points": 2.2, "gw4_points": 3.3, "gw5_points": 2.5, "gw6_points": 2.5, "gw7_points": 2.0, "gw8_points": 3.2, "gw9_points": 2.9, "points_per_million": 4.05},
        {"id": 1122, "name": "Solanke", "position_name": "Forward", "team": "Bournemouth", "price": 7.5, "uncertainty_percent": "34%", "overall_total": 24.3, "gw1_points": 3.3, "gw2_points": 2.4, "gw3_points": 2.9, "gw4_points": 2.3, "gw5_points": 2.3, "gw6_points": 2.8, "gw7_points": 3.1, "gw8_points": 2.8, "gw9_points": 2.5, "points_per_million": 3.24},
        {"id": 1123, "name": "Aït-Nouri", "position_name": "Defender", "team": "Wolves", "price": 6.0, "uncertainty_percent": "35%", "overall_total": 24.1, "gw1_points": 2.8, "gw2_points": 2.8, "gw3_points": 2.4, "gw4_points": 3.1, "gw5_points": 1.9, "gw6_points": 3.1, "gw7_points": 2.2, "gw8_points": 3.4, "gw9_points": 2.6, "points_per_million": 4.02},
        {"id": 1124, "name": "Danso", "position_name": "Defender", "team": "Lens", "price": 4.5, "uncertainty_percent": "32%", "overall_total": 24.1, "gw1_points": 3.4, "gw2_points": 1.9, "gw3_points": 2.7, "gw4_points": 2.4, "gw5_points": 2.6, "gw6_points": 2.8, "gw7_points": 2.9, "gw8_points": 2.5, "gw9_points": 2.8, "points_per_million": 5.36},
        {"id": 1125, "name": "Cullen", "position_name": "Midfielder", "team": "Burnley", "price": 5.0, "uncertainty_percent": "22%", "overall_total": 24.0, "gw1_points": 2.7, "gw2_points": 3.1, "gw3_points": 2.6, "gw4_points": 2.6, "gw5_points": 2.7, "gw6_points": 2.3, "gw7_points": 2.4, "gw8_points": 3.0, "gw9_points": 2.6, "points_per_million": 4.80},
        {"id": 1126, "name": "Dunk", "position_name": "Defender", "team": "Brighton", "price": 4.5, "uncertainty_percent": "31%", "overall_total": 23.9, "gw1_points": 3.0, "gw2_points": 3.0, "gw3_points": 2.5, "gw4_points": 2.5, "gw5_points": 2.9, "gw6_points": 2.0, "gw7_points": 2.8, "gw8_points": 2.6, "gw9_points": 2.7, "points_per_million": 5.31},
        {"id": 1127, "name": "Piroe", "position_name": "Forward", "team": "Leeds", "price": 5.5, "uncertainty_percent": "35%", "overall_total": 23.8, "gw1_points": 2.4, "gw2_points": 2.3, "gw3_points": 2.6, "gw4_points": 2.5, "gw5_points": 2.6, "gw6_points": 2.8, "gw7_points": 3.2, "gw8_points": 2.8, "gw9_points": 2.6, "points_per_million": 4.33},
        {"id": 1128, "name": "Gyökeres", "position_name": "Forward", "team": "Sporting CP", "price": 9.0, "uncertainty_percent": "38%", "overall_total": 23.8, "gw1_points": 3.1, "gw2_points": 3.7, "gw3_points": 2.1, "gw4_points": 2.6, "gw5_points": 2.0, "gw6_points": 2.5, "gw7_points": 2.6, "gw8_points": 2.4, "gw9_points": 2.7, "points_per_million": 2.64},
        {"id": 1129, "name": "Tielemans", "position_name": "Midfielder", "team": "Aston Villa", "price": 6.0, "uncertainty_percent": "32%", "overall_total": 23.8, "gw1_points": 2.6, "gw2_points": 2.5, "gw3_points": 2.7, "gw4_points": 2.6, "gw5_points": 2.5, "gw6_points": 2.6, "gw7_points": 3.5, "gw8_points": 2.4, "gw9_points": 2.4, "points_per_million": 3.97},
        {"id": 1130, "name": "Tanaka", "position_name": "Midfielder", "team": "Feyenoord", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 23.8, "gw1_points": 2.8, "gw2_points": 2.2, "gw3_points": 2.6, "gw4_points": 2.6, "gw5_points": 2.5, "gw6_points": 2.6, "gw7_points": 2.8, "gw8_points": 2.8, "gw9_points": 2.9, "points_per_million": 4.76},
        {"id": 1131, "name": "Cunha", "position_name": "Midfielder", "team": "Wolves", "price": 8.0, "uncertainty_percent": "31%", "overall_total": 23.6, "gw1_points": 2.4, "gw2_points": 2.4, "gw3_points": 3.1, "gw4_points": 2.3, "gw5_points": 2.8, "gw6_points": 2.5, "gw7_points": 3.2, "gw8_points": 2.2, "gw9_points": 2.8, "points_per_million": 2.95},
        {"id": 1132, "name": "Lewis-Potter", "position_name": "Defender", "team": "Brentford", "price": 5.0, "uncertainty_percent": "31%", "overall_total": 23.6, "gw1_points": 2.4, "gw2_points": 2.6, "gw3_points": 2.9, "gw4_points": 2.5, "gw5_points": 2.4, "gw6_points": 3.2, "gw7_points": 2.6, "gw8_points": 2.7, "gw9_points": 2.2, "points_per_million": 4.72},
        {"id": 1133, "name": "Wharton", "position_name": "Midfielder", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "22%", "overall_total": 23.4, "gw1_points": 2.5, "gw2_points": 2.9, "gw3_points": 2.4, "gw4_points": 3.0, "gw5_points": 2.6, "gw6_points": 2.5, "gw7_points": 2.5, "gw8_points": 2.7, "gw9_points": 2.2, "points_per_million": 4.68},
        {"id": 1134, "name": "Garner", "position_name": "Midfielder", "team": "Everton", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 23.4, "gw1_points": 2.9, "gw2_points": 2.7, "gw3_points": 2.7, "gw4_points": 2.7, "gw5_points": 2.3, "gw6_points": 2.6, "gw7_points": 2.7, "gw8_points": 2.1, "gw9_points": 2.7, "points_per_million": 4.68},
        {"id": 1135, "name": "Solomon", "position_name": "Midfielder", "team": "Fulham", "price": 5.5, "uncertainty_percent": "36%", "overall_total": 23.0, "gw1_points": 0.7, "gw2_points": 2.1, "gw3_points": 3.3, "gw4_points": 2.9, "gw5_points": 2.6, "gw6_points": 2.9, "gw7_points": 3.3, "gw8_points": 2.7, "gw9_points": 2.5, "points_per_million": 4.18},
        {"id": 1136, "name": "Pope", "position_name": "Goalkeeper", "team": "Newcastle", "price": 5.0, "uncertainty_percent": "30%", "overall_total": 23.0, "gw1_points": 2.6, "gw2_points": 2.9, "gw3_points": 2.2, "gw4_points": 2.9, "gw5_points": 1.9, "gw6_points": 1.9, "gw7_points": 2.9, "gw8_points": 2.4, "gw9_points": 3.2, "points_per_million": 4.60},
        {"id": 1137, "name": "Lukić", "position_name": "Midfielder", "team": "Fulham", "price": 5.0, "uncertainty_percent": "21%", "overall_total": 22.9, "gw1_points": 2.4, "gw2_points": 2.8, "gw3_points": 2.3, "gw4_points": 3.0, "gw5_points": 2.9, "gw6_points": 2.4, "gw7_points": 2.5, "gw8_points": 2.4, "gw9_points": 2.3, "points_per_million": 4.58},
        {"id": 1138, "name": "Ugarte", "position_name": "Midfielder", "team": "PSG", "price": 5.0, "uncertainty_percent": "26%", "overall_total": 22.6, "gw1_points": 2.4, "gw2_points": 2.5, "gw3_points": 2.9, "gw4_points": 2.0, "gw5_points": 2.6, "gw6_points": 2.6, "gw7_points": 3.0, "gw8_points": 2.1, "gw9_points": 2.6, "points_per_million": 4.52},
        {"id": 1139, "name": "Baleba", "position_name": "Midfielder", "team": "Brighton", "price": 5.0, "uncertainty_percent": "25%", "overall_total": 22.6, "gw1_points": 1.6, "gw2_points": 2.7, "gw3_points": 2.4, "gw4_points": 2.7, "gw5_points": 2.7, "gw6_points": 2.4, "gw7_points": 2.9, "gw8_points": 2.6, "gw9_points": 2.6, "points_per_million": 4.52},
        {"id": 1140, "name": "Kerkez", "position_name": "Defender", "team": "Bournemouth", "price": 6.0, "uncertainty_percent": "37%", "overall_total": 22.2, "gw1_points": 2.8, "gw2_points": 2.1, "gw3_points": 2.0, "gw4_points": 3.0, "gw5_points": 3.1, "gw6_points": 2.4, "gw7_points": 1.9, "gw8_points": 2.7, "gw9_points": 2.2, "points_per_million": 3.70},
        {"id": 1141, "name": "Estève", "position_name": "Defender", "team": "Burnley", "price": 4.0, "uncertainty_percent": "32%", "overall_total": 22.2, "gw1_points": 2.2, "gw2_points": 3.5, "gw3_points": 2.4, "gw4_points": 2.3, "gw5_points": 2.7, "gw6_points": 2.0, "gw7_points": 1.8, "gw8_points": 3.0, "gw9_points": 2.3, "points_per_million": 5.55},
        {"id": 1142, "name": "De Ligt", "position_name": "Defender", "team": "Bayern Munich", "price": 5.0, "uncertainty_percent": "34%", "overall_total": 22.2, "gw1_points": 2.4, "gw2_points": 2.2, "gw3_points": 3.3, "gw4_points": 1.8, "gw5_points": 2.7, "gw6_points": 2.2, "gw7_points": 3.0, "gw8_points": 1.7, "gw9_points": 2.9, "points_per_million": 4.44},
        {"id": 1143, "name": "Trossard", "position_name": "Midfielder", "team": "Arsenal", "price": 7.0, "uncertainty_percent": "48%", "overall_total": 22.1, "gw1_points": 1.4, "gw2_points": 3.7, "gw3_points": 2.0, "gw4_points": 2.8, "gw5_points": 2.2, "gw6_points": 2.3, "gw7_points": 2.8, "gw8_points": 2.3, "gw9_points": 2.7, "points_per_million": 3.16},
        {"id": 1144, "name": "Foden", "position_name": "Midfielder", "team": "Man City", "price": 8.0, "uncertainty_percent": "45%", "overall_total": 22.1, "gw1_points": 1.4, "gw2_points": 2.8, "gw3_points": 2.4, "gw4_points": 2.9, "gw5_points": 2.1, "gw6_points": 3.1, "gw7_points": 2.3, "gw8_points": 2.7, "gw9_points": 2.4, "points_per_million": 2.76},
        {"id": 1145, "name": "J.Murphy", "position_name": "Midfielder", "team": "Newcastle", "price": 6.5, "uncertainty_percent": "41%", "overall_total": 22.0, "gw1_points": 2.2, "gw2_points": 2.3, "gw3_points": 2.7, "gw4_points": 2.7, "gw5_points": 2.5, "gw6_points": 2.0, "gw7_points": 2.6, "gw8_points": 2.3, "gw9_points": 2.8, "points_per_million": 3.38},
        {"id": 1146, "name": "Ugochukwu", "position_name": "Midfielder", "team": "Chelsea", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 21.9, "gw1_points": 2.4, "gw2_points": 2.8, "gw3_points": 2.4, "gw4_points": 2.3, "gw5_points": 2.4, "gw6_points": 2.2, "gw7_points": 2.2, "gw8_points": 2.9, "gw9_points": 2.4, "points_per_million": 4.38},
        {"id": 1147, "name": "Berge", "position_name": "Midfielder", "team": "Burnley", "price": 5.0, "uncertainty_percent": "18%", "overall_total": 21.9, "gw1_points": 2.4, "gw2_points": 2.6, "gw3_points": 2.2, "gw4_points": 2.9, "gw5_points": 2.6, "gw6_points": 2.3, "gw7_points": 2.5, "gw8_points": 2.3, "gw9_points": 2.2, "points_per_million": 4.38},
        {"id": 1148, "name": "Darlow", "position_name": "Goalkeeper", "team": "Newcastle", "price": 4.0, "uncertainty_percent": "30%", "overall_total": 21.9, "gw1_points": 2.2, "gw2_points": 2.2, "gw3_points": 2.3, "gw4_points": 2.7, "gw5_points": 1.6, "gw6_points": 2.9, "gw7_points": 2.6, "gw8_points": 2.8, "gw9_points": 2.6, "points_per_million": 5.48},
        {"id": 1149, "name": "Bassey", "position_name": "Defender", "team": "Fulham", "price": 4.5, "uncertainty_percent": "34%", "overall_total": 21.8, "gw1_points": 2.5, "gw2_points": 3.0, "gw3_points": 2.0, "gw4_points": 3.5, "gw5_points": 2.8, "gw6_points": 1.9, "gw7_points": 2.3, "gw8_points": 2.1, "gw9_points": 1.8, "points_per_million": 4.84},
        {"id": 1150, "name": "Pickford", "position_name": "Goalkeeper", "team": "Everton", "price": 5.5, "uncertainty_percent": "33%", "overall_total": 21.8, "gw1_points": 2.8, "gw2_points": 2.7, "gw3_points": 2.2, "gw4_points": 2.5, "gw5_points": 1.3, "gw6_points": 2.6, "gw7_points": 2.2, "gw8_points": 2.8, "gw9_points": 2.7, "points_per_million": 3.96},
        {"id": 1151, "name": "James", "position_name": "Midfielder", "team": "Chelsea", "price": 5.5, "uncertainty_percent": "41%", "overall_total": 21.8, "gw1_points": 2.9, "gw2_points": 1.9, "gw3_points": 2.2, "gw4_points": 2.5, "gw5_points": 2.4, "gw6_points": 2.3, "gw7_points": 2.5, "gw8_points": 2.5, "gw9_points": 2.6, "points_per_million": 3.96},
        {"id": 1152, "name": "Bellegarde", "position_name": "Midfielder", "team": "Wolves", "price": 5.5, "uncertainty_percent": "34%", "overall_total": 21.8, "gw1_points": 2.1, "gw2_points": 2.3, "gw3_points": 2.2, "gw4_points": 2.1, "gw5_points": 2.9, "gw6_points": 2.2, "gw7_points": 2.5, "gw8_points": 2.8, "gw9_points": 2.8, "points_per_million": 3.96},
        {"id": 1153, "name": "Van de Ven", "position_name": "Defender", "team": "Tottenham", "price": 4.5, "uncertainty_percent": "34%", "overall_total": 21.7, "gw1_points": 3.2, "gw2_points": 1.5, "gw3_points": 2.5, "gw4_points": 2.1, "gw5_points": 2.2, "gw6_points": 2.6, "gw7_points": 2.5, "gw8_points": 2.4, "gw9_points": 2.7, "points_per_million": 4.82},
        {"id": 1154, "name": "Sessegnon", "position_name": "Midfielder", "team": "Tottenham", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 21.6, "gw1_points": 0.8, "gw2_points": 2.9, "gw3_points": 2.5, "gw4_points": 2.9, "gw5_points": 2.9, "gw6_points": 2.3, "gw7_points": 2.7, "gw8_points": 2.3, "gw9_points": 2.4, "points_per_million": 3.93},
        {"id": 1155, "name": "Mayenda", "position_name": "Forward", "team": "Sunderland", "price": 5.5, "uncertainty_percent": "41%", "overall_total": 21.6, "gw1_points": 2.7, "gw2_points": 2.4, "gw3_points": 2.9, "gw4_points": 2.0, "gw5_points": 2.4, "gw6_points": 2.5, "gw7_points": 2.3, "gw8_points": 2.7, "gw9_points": 1.8, "points_per_million": 3.93},
        {"id": 1156, "name": "Maguire", "position_name": "Defender", "team": "Man United", "price": 4.5, "uncertainty_percent": "35%", "overall_total": 21.4, "gw1_points": 2.2, "gw2_points": 2.3, "gw3_points": 3.2, "gw4_points": 1.8, "gw5_points": 2.2, "gw6_points": 2.2, "gw7_points": 3.4, "gw8_points": 1.6, "gw9_points": 2.4, "points_per_million": 4.76},
        {"id": 1157, "name": "James", "position_name": "Defender", "team": "Chelsea", "price": 5.5, "uncertainty_percent": "36%", "overall_total": 21.3, "gw1_points": 3.0, "gw2_points": 2.4, "gw3_points": 2.5, "gw4_points": 2.1, "gw5_points": 2.1, "gw6_points": 2.7, "gw7_points": 1.8, "gw8_points": 1.8, "gw9_points": 2.8, "points_per_million": 3.87},
        {"id": 1158, "name": "Marmoush", "position_name": "Midfielder", "team": "Eintracht Frankfurt", "price": 8.5, "uncertainty_percent": "44%", "overall_total": 21.3, "gw1_points": 2.7, "gw2_points": 2.7, "gw3_points": 2.2, "gw4_points": 2.5, "gw5_points": 1.8, "gw6_points": 2.9, "gw7_points": 2.2, "gw8_points": 2.4, "gw9_points": 2.0, "points_per_million": 2.51},
        {"id": 1159, "name": "Tel", "position_name": "Midfielder", "team": "Bayern Munich", "price": 6.5, "uncertainty_percent": "46%", "overall_total": 21.3, "gw1_points": 4.5, "gw2_points": 1.6, "gw3_points": 2.2, "gw4_points": 2.0, "gw5_points": 1.9, "gw6_points": 2.4, "gw7_points": 2.5, "gw8_points": 2.2, "gw9_points": 1.9, "points_per_million": 3.28},
        {"id": 1160, "name": "Smith", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "34%", "overall_total": 21.3, "gw1_points": 1.5, "gw2_points": 3.0, "gw3_points": 1.8, "gw4_points": 2.7, "gw5_points": 1.9, "gw6_points": 2.8, "gw7_points": 2.7, "gw8_points": 2.2, "gw9_points": 2.6, "points_per_million": 4.73},
        {"id": 1161, "name": "Ballard", "position_name": "Defender", "team": "Sunderland", "price": 4.5, "uncertainty_percent": "37%", "overall_total": 21.2, "gw1_points": 3.2, "gw2_points": 3.1, "gw3_points": 3.1, "gw4_points": 2.1, "gw5_points": 2.2, "gw6_points": 1.6, "gw7_points": 2.2, "gw8_points": 2.2, "gw9_points": 1.5, "points_per_million": 4.71},
        {"id": 1162, "name": "Hume", "position_name": "Defender", "team": "Sunderland", "price": 4.5, "uncertainty_percent": "37%", "overall_total": 21.2, "gw1_points": 3.0, "gw2_points": 2.9, "gw3_points": 2.8, "gw4_points": 2.0, "gw5_points": 2.4, "gw6_points": 1.7, "gw7_points": 2.2, "gw8_points": 2.7, "gw9_points": 1.6, "points_per_million": 4.71},
        {"id": 1163, "name": "R.Gomes", "position_name": "Defender", "team": "Wolves", "price": 4.5, "uncertainty_percent": "43%", "overall_total": 21.2, "gw1_points": 2.0, "gw2_points": 2.1, "gw3_points": 2.7, "gw4_points": 1.8, "gw5_points": 3.5, "gw6_points": 1.8, "gw7_points": 2.2, "gw8_points": 2.2, "gw9_points": 2.8, "points_per_million": 4.71},
        {"id": 1164, "name": "Ederson M.", "position_name": "Goalkeeper", "team": "Man City", "price": 5.5, "uncertainty_percent": "37%", "overall_total": 21.0, "gw1_points": 2.0, "gw2_points": 2.6, "gw3_points": 2.5, "gw4_points": 2.6, "gw5_points": 2.0, "gw6_points": 2.6, "gw7_points": 1.9, "gw8_points": 2.6, "gw9_points": 2.2, "points_per_million": 3.82},
        {"id": 1165, "name": "Pau", "position_name": "Defender", "team": "Aston Villa", "price": 4.5, "uncertainty_percent": "36%", "overall_total": 21.0, "gw1_points": 2.1, "gw2_points": 2.0, "gw3_points": 2.4, "gw4_points": 2.3, "gw5_points": 2.5, "gw6_points": 2.5, "gw7_points": 3.1, "gw8_points": 1.7, "gw9_points": 2.4, "points_per_million": 4.67},
        {"id": 1166, "name": "Pedro Porro", "position_name": "Defender", "team": "Tottenham", "price": 5.5, "uncertainty_percent": "39%", "overall_total": 20.9, "gw1_points": 3.7, "gw2_points": 1.6, "gw3_points": 2.1, "gw4_points": 2.0, "gw5_points": 2.0, "gw6_points": 2.7, "gw7_points": 2.5, "gw8_points": 2.0, "gw9_points": 2.2, "points_per_million": 3.80},
        {"id": 1167, "name": "Anthony", "position_name": "Midfielder", "team": "Man United", "price": 5.5, "uncertainty_percent": "35%", "overall_total": 20.9, "gw1_points": 2.2, "gw2_points": 2.8, "gw3_points": 1.9, "gw4_points": 2.1, "gw5_points": 2.6, "gw6_points": 1.9, "gw7_points": 2.2, "gw8_points": 3.0, "gw9_points": 2.1, "points_per_million": 3.80},
        {"id": 1168, "name": "Todibo", "position_name": "Defender", "team": "Nice", "price": 4.5, "uncertainty_percent": "34%", "overall_total": 20.8, "gw1_points": 2.6, "gw2_points": 2.2, "gw3_points": 1.7, "gw4_points": 2.3, "gw5_points": 2.6, "gw6_points": 2.5, "gw7_points": 1.8, "gw8_points": 2.4, "gw9_points": 2.6, "points_per_million": 4.62},
        {"id": 1169, "name": "Odobert", "position_name": "Midfielder", "team": "Burnley", "price": 5.5, "uncertainty_percent": "44%", "overall_total": 20.6, "gw1_points": 3.4, "gw2_points": 1.7, "gw3_points": 2.8, "gw4_points": 2.1, "gw5_points": 2.0, "gw6_points": 2.3, "gw7_points": 2.3, "gw8_points": 1.9, "gw9_points": 2.0, "points_per_million": 3.75},
        {"id": 1170, "name": "Flemming", "position_name": "Forward", "team": "Millwall", "price": 5.5, "uncertainty_percent": "38%", "overall_total": 20.6, "gw1_points": 0.5, "gw2_points": 3.0, "gw3_points": 2.4, "gw4_points": 2.4, "gw5_points": 2.6, "gw6_points": 1.9, "gw7_points": 2.1, "gw8_points": 3.2, "gw9_points": 2.3, "points_per_million": 3.75},
        {"id": 1171, "name": "Sels", "position_name": "Goalkeeper", "team": "Nottingham Forest", "price": 5.0, "uncertainty_percent": "34%", "overall_total": 20.6, "gw1_points": 2.4, "gw2_points": 2.3, "gw3_points": 2.5, "gw4_points": 1.8, "gw5_points": 2.6, "gw6_points": 2.0, "gw7_points": 2.0, "gw8_points": 2.5, "gw9_points": 2.4, "points_per_million": 4.12},
        {"id": 1172, "name": "Minteh", "position_name": "Midfielder", "team": "Newcastle", "price": 6.0, "uncertainty_percent": "37%", "overall_total": 20.6, "gw1_points": 2.9, "gw2_points": 2.3, "gw3_points": 2.2, "gw4_points": 2.3, "gw5_points": 2.7, "gw6_points": 2.1, "gw7_points": 1.9, "gw8_points": 2.0, "gw9_points": 2.2, "points_per_million": 3.43},
        {"id": 1173, "name": "Kamara", "position_name": "Midfielder", "team": "Aston Villa", "price": 5.0, "uncertainty_percent": "29%", "overall_total": 20.5, "gw1_points": 2.4, "gw2_points": 2.2, "gw3_points": 2.4, "gw4_points": 2.0, "gw5_points": 2.2, "gw6_points": 2.5, "gw7_points": 2.9, "gw8_points": 2.2, "gw9_points": 1.9, "points_per_million": 4.10},
        {"id": 1174, "name": "Alcaraz", "position_name": "Midfielder", "team": "Southampton", "price": 5.5, "uncertainty_percent": "38%", "overall_total": 20.5, "gw1_points": 2.6, "gw2_points": 2.5, "gw3_points": 2.1, "gw4_points": 2.4, "gw5_points": 2.0, "gw6_points": 2.5, "gw7_points": 2.2, "gw8_points": 1.9, "gw9_points": 2.3, "points_per_million": 3.73},
        {"id": 1175, "name": "H.Bueno", "position_name": "Defender", "team": "Wolves", "price": 4.5, "uncertainty_percent": "39%", "overall_total": 20.4, "gw1_points": 1.7, "gw2_points": 2.2, "gw3_points": 2.8, "gw4_points": 1.5, "gw5_points": 3.1, "gw6_points": 1.7, "gw7_points": 2.3, "gw8_points": 2.2, "gw9_points": 2.9, "points_per_million": 4.53},
        {"id": 1176, "name": "Ødegaard", "position_name": "Midfielder", "team": "Arsenal", "price": 8.0, "uncertainty_percent": "45%", "overall_total": 20.4, "gw1_points": 2.3, "gw2_points": 2.9, "gw3_points": 1.9, "gw4_points": 2.2, "gw5_points": 2.1, "gw6_points": 2.0, "gw7_points": 2.7, "gw8_points": 2.2, "gw9_points": 2.1, "points_per_million": 2.55},
        {"id": 1177, "name": "Spence", "position_name": "Defender", "team": "Tottenham", "price": 4.5, "uncertainty_percent": "38%", "overall_total": 20.3, "gw1_points": 4.1, "gw2_points": 1.9, "gw3_points": 2.4, "gw4_points": 1.9, "gw5_points": 1.9, "gw6_points": 2.2, "gw7_points": 2.5, "gw8_points": 1.7, "gw9_points": 1.8, "points_per_million": 4.51},
        {"id": 1178, "name": "Stones", "position_name": "Defender", "team": "Man City", "price": 5.5, "uncertainty_percent": "44%", "overall_total": 20.3, "gw1_points": 2.6, "gw2_points": 2.8, "gw3_points": 2.2, "gw4_points": 2.5, "gw5_points": 1.5, "gw6_points": 3.2, "gw7_points": 1.7, "gw8_points": 2.1, "gw9_points": 1.7, "points_per_million": 3.69},
        {"id": 1179, "name": "Doku", "position_name": "Midfielder", "team": "Man City", "price": 6.5, "uncertainty_percent": "39%", "overall_total": 20.3, "gw1_points": 2.4, "gw2_points": 2.6, "gw3_points": 2.3, "gw4_points": 2.3, "gw5_points": 1.6, "gw6_points": 2.9, "gw7_points": 2.2, "gw8_points": 2.4, "gw9_points": 1.7, "points_per_million": 3.12},
        {"id": 1180, "name": "Casemiro", "position_name": "Midfielder", "team": "Man United", "price": 5.5, "uncertainty_percent": "31%", "overall_total": 20.2, "gw1_points": 2.3, "gw2_points": 1.9, "gw3_points": 2.5, "gw4_points": 1.9, "gw5_points": 2.2, "gw6_points": 2.1, "gw7_points": 2.6, "gw8_points": 2.2, "gw9_points": 2.6, "points_per_million": 3.67},
        {"id": 1181, "name": "Ekwah", "position_name": "Midfielder", "team": "Sunderland", "price": 4.5, "uncertainty_percent": "30%", "overall_total": 20.0, "gw1_points": 2.4, "gw2_points": 2.5, "gw3_points": 2.6, "gw4_points": 2.0, "gw5_points": 2.3, "gw6_points": 2.2, "gw7_points": 1.8, "gw8_points": 2.5, "gw9_points": 1.7, "points_per_million": 4.44},
        {"id": 1182, "name": "Hannibal", "position_name": "Midfielder", "team": "Man United", "price": 5.0, "uncertainty_percent": "32%", "overall_total": 19.9, "gw1_points": 2.2, "gw2_points": 2.6, "gw3_points": 2.2, "gw4_points": 2.0, "gw5_points": 2.3, "gw6_points": 1.9, "gw7_points": 1.9, "gw8_points": 2.6, "gw9_points": 2.2, "points_per_million": 3.98},
        {"id": 1183, "name": "Delap", "position_name": "Forward", "team": "Hull", "price": 6.5, "uncertainty_percent": "36%", "overall_total": 19.8, "gw1_points": 3.2, "gw2_points": 2.3, "gw3_points": 2.0, "gw4_points": 1.8, "gw5_points": 1.9, "gw6_points": 2.2, "gw7_points": 2.1, "gw8_points": 1.9, "gw9_points": 2.5, "points_per_million": 3.05},
        {"id": 1184, "name": "Gakpo", "position_name": "Midfielder", "team": "Liverpool", "price": 7.5, "uncertainty_percent": "49%", "overall_total": 19.8, "gw1_points": 2.3, "gw2_points": 2.1, "gw3_points": 1.9, "gw4_points": 2.4, "gw5_points": 2.3, "gw6_points": 2.1, "gw7_points": 2.0, "gw8_points": 2.5, "gw9_points": 2.3, "points_per_million": 2.64},
        {"id": 1185, "name": "De Cuyper", "position_name": "Defender", "team": "Club Brugge", "price": 4.5, "uncertainty_percent": "36%", "overall_total": 19.7, "gw1_points": 2.6, "gw2_points": 2.5, "gw3_points": 2.2, "gw4_points": 2.2, "gw5_points": 2.3, "gw6_points": 1.6, "gw7_points": 2.3, "gw8_points": 1.9, "gw9_points": 2.0, "points_per_million": 4.38},
        {"id": 1186, "name": "Ayari", "position_name": "Midfielder", "team": "Brighton", "price": 5.0, "uncertainty_percent": "30%", "overall_total": 19.5, "gw1_points": 2.7, "gw2_points": 2.0, "gw3_points": 2.0, "gw4_points": 2.1, "gw5_points": 2.3, "gw6_points": 1.8, "gw7_points": 2.0, "gw8_points": 2.3, "gw9_points": 2.2, "points_per_million": 3.90},
        {"id": 1187, "name": "Tete", "position_name": "Defender", "team": "Fulham", "price": 4.5, "uncertainty_percent": "39%", "overall_total": 19.4, "gw1_points": 2.3, "gw2_points": 2.4, "gw3_points": 1.9, "gw4_points": 3.0, "gw5_points": 2.0, "gw6_points": 1.8, "gw7_points": 2.4, "gw8_points": 2.0, "gw9_points": 1.7, "points_per_million": 4.31},
        {"id": 1188, "name": "Edwards", "position_name": "Midfielder", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "30%", "overall_total": 19.4, "gw1_points": 1.9, "gw2_points": 2.5, "gw3_points": 2.1, "gw4_points": 2.0, "gw5_points": 2.2, "gw6_points": 1.8, "gw7_points": 2.0, "gw8_points": 2.8, "gw9_points": 2.0, "points_per_million": 3.88},
        {"id": 1189, "name": "Bogle", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "39%", "overall_total": 19.3, "gw1_points": 2.8, "gw2_points": 1.0, "gw3_points": 1.9, "gw4_points": 1.8, "gw5_points": 1.9, "gw6_points": 2.3, "gw7_points": 2.0, "gw8_points": 2.7, "gw9_points": 2.8, "points_per_million": 4.29},
        {"id": 1190, "name": "Jensen", "position_name": "Midfielder", "team": "Brentford", "price": 5.0, "uncertainty_percent": "31%", "overall_total": 19.3, "gw1_points": 1.9, "gw2_points": 2.3, "gw3_points": 2.3, "gw4_points": 2.2, "gw5_points": 1.9, "gw6_points": 2.3, "gw7_points": 2.0, "gw8_points": 2.3, "gw9_points": 2.0, "points_per_million": 3.86},
        {"id": 1191, "name": "Gyabi", "position_name": "Midfielder", "team": "Leeds", "price": 4.5, "uncertainty_percent": "29%", "overall_total": 19.1, "gw1_points": 2.2, "gw2_points": 1.6, "gw3_points": 2.1, "gw4_points": 2.0, "gw5_points": 2.0, "gw6_points": 2.2, "gw7_points": 2.2, "gw8_points": 2.4, "gw9_points": 2.3, "points_per_million": 4.24},
        {"id": 1192, "name": "Bernardo", "position_name": "Midfielder", "team": "Brighton", "price": 6.5, "uncertainty_percent": "40%", "overall_total": 19.0, "gw1_points": 2.1, "gw2_points": 2.4, "gw3_points": 2.2, "gw4_points": 2.5, "gw5_points": 1.9, "gw6_points": 2.6, "gw7_points": 1.6, "gw8_points": 2.0, "gw9_points": 1.7, "points_per_million": 2.92},
        {"id": 1193, "name": "Damsgaard", "position_name": "Midfielder", "team": "Brentford", "price": 6.0, "uncertainty_percent": "36%", "overall_total": 19.0, "gw1_points": 2.4, "gw2_points": 2.4, "gw3_points": 2.3, "gw4_points": 1.9, "gw5_points": 1.9, "gw6_points": 2.2, "gw7_points": 1.7, "gw8_points": 2.2, "gw9_points": 2.0, "points_per_million": 3.17},
        {"id": 1194, "name": "J.Palhinha", "position_name": "Midfielder", "team": "Fulham", "price": 5.5, "uncertainty_percent": "34%", "overall_total": 18.9, "gw1_points": 2.6, "gw2_points": 1.5, "gw3_points": 2.4, "gw4_points": 2.0, "gw5_points": 2.0, "gw6_points": 2.2, "gw7_points": 2.2, "gw8_points": 1.7, "gw9_points": 2.2, "points_per_million": 3.44},
        {"id": 1195, "name": "Hughes", "position_name": "Midfielder", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "27%", "overall_total": 18.8, "gw1_points": 2.0, "gw2_points": 2.5, "gw3_points": 1.9, "gw4_points": 2.6, "gw5_points": 2.0, "gw6_points": 1.8, "gw7_points": 2.0, "gw8_points": 2.1, "gw9_points": 1.9, "points_per_million": 3.76},
        {"id": 1196, "name": "Kudus", "position_name": "Midfielder", "team": "West Ham", "price": 6.5, "uncertainty_percent": "45%", "overall_total": 18.8, "gw1_points": 2.6, "gw2_points": 1.4, "gw3_points": 1.9, "gw4_points": 2.1, "gw5_points": 1.9, "gw6_points": 2.3, "gw7_points": 2.6, "gw8_points": 2.2, "gw9_points": 1.9, "points_per_million": 2.89},
        {"id": 1197, "name": "O'Brien", "position_name": "Defender", "team": "Nottingham Forest", "price": 5.0, "uncertainty_percent": "41%", "overall_total": 18.8, "gw1_points": 2.6, "gw2_points": 2.4, "gw3_points": 1.9, "gw4_points": 2.0, "gw5_points": 1.5, "gw6_points": 2.2, "gw7_points": 2.1, "gw8_points": 1.7, "gw9_points": 2.3, "points_per_million": 3.76},
        {"id": 1198, "name": "Rodon", "position_name": "Defender", "team": "Leeds", "price": 4.0, "uncertainty_percent": "36%", "overall_total": 18.7, "gw1_points": 2.8, "gw2_points": 1.3, "gw3_points": 1.8, "gw4_points": 1.9, "gw5_points": 1.8, "gw6_points": 2.3, "gw7_points": 1.9, "gw8_points": 2.4, "gw9_points": 2.5, "points_per_million": 4.68},
        {"id": 1199, "name": "Sangaré", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 5.0, "uncertainty_percent": "30%", "overall_total": 18.7, "gw1_points": 2.4, "gw2_points": 2.1, "gw3_points": 2.3, "gw4_points": 1.5, "gw5_points": 2.3, "gw6_points": 2.3, "gw7_points": 1.7, "gw8_points": 1.9, "gw9_points": 2.1, "points_per_million": 3.74},
        {"id": 1200, "name": "Munetsi", "position_name": "Midfielder", "team": "Reims", "price": 5.5, "uncertainty_percent": "44%", "overall_total": 18.5, "gw1_points": 1.8, "gw2_points": 1.7, "gw3_points": 2.2, "gw4_points": 1.6, "gw5_points": 2.6, "gw6_points": 1.8, "gw7_points": 1.9, "gw8_points": 2.1, "gw9_points": 2.6, "points_per_million": 3.36},
        {"id": 1201, "name": "Travers", "position_name": "Goalkeeper", "team": "Bournemouth", "price": 4.5, "uncertainty_percent": "38%", "overall_total": 18.3, "gw1_points": 2.7, "gw2_points": 1.6, "gw3_points": 1.7, "gw4_points": 1.7, "gw5_points": 2.6, "gw6_points": 1.9, "gw7_points": 2.0, "gw8_points": 2.5, "gw9_points": 1.7, "points_per_million": 4.07},
        {"id": 1202, "name": "Livramento", "position_name": "Defender", "team": "Newcastle", "price": 5.0, "uncertainty_percent": "40%", "overall_total": 18.2, "gw1_points": 1.7, "gw2_points": 1.6, "gw3_points": 2.5, "gw4_points": 2.3, "gw5_points": 1.9, "gw6_points": 1.9, "gw7_points": 2.4, "gw8_points": 1.7, "gw9_points": 2.3, "points_per_million": 3.64},
        {"id": 1203, "name": "Lucas Pires", "position_name": "Defender", "team": "Brest", "price": 4.0, "uncertainty_percent": "37%", "overall_total": 18.1, "gw1_points": 1.6, "gw2_points": 3.0, "gw3_points": 1.9, "gw4_points": 1.6, "gw5_points": 2.3, "gw6_points": 1.4, "gw7_points": 1.4, "gw8_points": 2.8, "gw9_points": 2.0, "points_per_million": 4.53},
        {"id": 1204, "name": "Szoboszlai", "position_name": "Midfielder", "team": "Liverpool", "price": 6.5, "uncertainty_percent": "41%", "overall_total": 18.0, "gw1_points": 2.6, "gw2_points": 1.8, "gw3_points": 1.7, "gw4_points": 2.2, "gw5_points": 2.1, "gw6_points": 1.8, "gw7_points": 1.8, "gw8_points": 2.1, "gw9_points": 1.9, "points_per_million": 2.77},
        {"id": 1205, "name": "Areola", "position_name": "Goalkeeper", "team": "West Ham", "price": 4.5, "uncertainty_percent": "36%", "overall_total": 17.7, "gw1_points": 1.4, "gw2_points": 2.4, "gw3_points": 1.9, "gw4_points": 1.3, "gw5_points": 2.1, "gw6_points": 2.3, "gw7_points": 2.1, "gw8_points": 2.2, "gw9_points": 2.0, "points_per_million": 3.93},
        {"id": 1206, "name": "Byram", "position_name": "Defender", "team": "Leeds", "price": 4.0, "uncertainty_percent": "37%", "overall_total": 17.7, "gw1_points": 2.7, "gw2_points": 1.1, "gw3_points": 1.7, "gw4_points": 1.7, "gw5_points": 1.7, "gw6_points": 2.2, "gw7_points": 1.9, "gw8_points": 2.3, "gw9_points": 2.5, "points_per_million": 4.43},
        {"id": 1207, "name": "Shaw", "position_name": "Defender", "team": "Man United", "price": 4.5, "uncertainty_percent": "39%", "overall_total": 17.5, "gw1_points": 1.8, "gw2_points": 2.0, "gw3_points": 2.6, "gw4_points": 1.5, "gw5_points": 1.8, "gw6_points": 1.7, "gw7_points": 2.3, "gw8_points": 1.3, "gw9_points": 2.5, "points_per_million": 3.89},
        {"id": 1208, "name": "Tavernier", "position_name": "Midfielder", "team": "Bournemouth", "price": 5.5, "uncertainty_percent": "44%", "overall_total": 17.5, "gw1_points": 2.3, "gw2_points": 2.0, "gw3_points": 1.5, "gw4_points": 1.9, "gw5_points": 2.0, "gw6_points": 2.0, "gw7_points": 2.2, "gw8_points": 1.6, "gw9_points": 2.0, "points_per_million": 3.18},
        {"id": 1209, "name": "Merino", "position_name": "Midfielder", "team": "Real Sociedad", "price": 6.0, "uncertainty_percent": "49%", "overall_total": 17.5, "gw1_points": 1.8, "gw2_points": 2.6, "gw3_points": 1.6, "gw4_points": 2.1, "gw5_points": 1.7, "gw6_points": 1.8, "gw7_points": 2.1, "gw8_points": 1.7, "gw9_points": 2.0, "points_per_million": 2.92},
        {"id": 1210, "name": "Wieffer", "position_name": "Midfielder", "team": "Feyenoord", "price": 5.0, "uncertainty_percent": "30%", "overall_total": 17.3, "gw1_points": 2.3, "gw2_points": 2.2, "gw3_points": 1.7, "gw4_points": 1.9, "gw5_points": 2.0, "gw6_points": 1.6, "gw7_points": 1.8, "gw8_points": 1.9, "gw9_points": 1.9, "points_per_million": 3.46},
        {"id": 1211, "name": "Trafford", "position_name": "Goalkeeper", "team": "Burnley", "price": 5.0, "uncertainty_percent": "43%", "overall_total": 17.3, "gw1_points": 1.9, "gw2_points": 1.5, "gw3_points": 1.4, "gw4_points": 2.7, "gw5_points": 1.3, "gw6_points": 2.6, "gw7_points": 1.5, "gw8_points": 2.4, "gw9_points": 1.9, "points_per_million": 3.46},
        {"id": 1212, "name": "Christie", "position_name": "Midfielder", "team": "Bournemouth", "price": 5.0, "uncertainty_percent": "30%", "overall_total": 17.1, "gw1_points": 0.0, "gw2_points": 0.9, "gw3_points": 2.4, "gw4_points": 2.4, "gw5_points": 2.2, "gw6_points": 2.4, "gw7_points": 2.4, "gw8_points": 2.0, "gw9_points": 2.5, "points_per_million": 3.42},
        {"id": 1213, "name": "Jota", "position_name": "Midfielder", "team": "Liverpool", "price": 5.5, "uncertainty_percent": "44%", "overall_total": 16.5, "gw1_points": 2.5, "gw2_points": 2.4, "gw3_points": 2.8, "gw4_points": 1.2, "gw5_points": 1.6, "gw6_points": 1.9, "gw7_points": 1.4, "gw8_points": 1.5, "gw9_points": 1.2, "points_per_million": 3.00},
        {"id": 1214, "name": "J.Ramsey", "position_name": "Midfielder", "team": "Aston Villa", "price": 5.5, "uncertainty_percent": "43%", "overall_total": 16.1, "gw1_points": 2.0, "gw2_points": 1.8, "gw3_points": 1.8, "gw4_points": 1.6, "gw5_points": 1.9, "gw6_points": 1.9, "gw7_points": 1.8, "gw8_points": 1.8, "gw9_points": 1.5, "points_per_million": 2.93},
        {"id": 1215, "name": "Struijk", "position_name": "Defender", "team": "Leeds", "price": 4.5, "uncertainty_percent": "45%", "overall_total": 16.1, "gw1_points": 2.1, "gw2_points": 1.0, "gw3_points": 1.8, "gw4_points": 1.7, "gw5_points": 1.6, "gw6_points": 1.9, "gw7_points": 1.8, "gw8_points": 2.0, "gw9_points": 2.1, "points_per_million": 3.58},
        {"id": 1216, "name": "Kiwior", "position_name": "Defender", "team": "Arsenal", "price": 5.5, "uncertainty_percent": "51%", "overall_total": 16.0, "gw1_points": 1.7, "gw2_points": 2.2, "gw3_points": 1.4, "gw4_points": 1.9, "gw5_points": 1.7, "gw6_points": 1.5, "gw7_points": 2.1, "gw8_points": 1.7, "gw9_points": 1.9, "points_per_million": 2.91},
        {"id": 1217, "name": "Garnacho", "position_name": "Midfielder", "team": "Man United", "price": 6.5, "uncertainty_percent": "50%", "overall_total": 16.0, "gw1_points": 1.5, "gw2_points": 1.7, "gw3_points": 2.2, "gw4_points": 1.4, "gw5_points": 1.8, "gw6_points": 1.8, "gw7_points": 2.4, "gw8_points": 1.4, "gw9_points": 1.9, "points_per_million": 2.46},
        {"id": 1218, "name": "Onyeka", "position_name": "Midfielder", "team": "Brentford", "price": 5.0, "uncertainty_percent": "39%", "overall_total": 15.9, "gw1_points": 2.2, "gw2_points": 1.6, "gw3_points": 1.8, "gw4_points": 1.8, "gw5_points": 1.8, "gw6_points": 1.8, "gw7_points": 1.7, "gw8_points": 1.7, "gw9_points": 1.5, "points_per_million": 3.18},
        {"id": 1219, "name": "Maatsen", "position_name": "Defender", "team": "Chelsea", "price": 4.5, "uncertainty_percent": "50%", "overall_total": 15.9, "gw1_points": 2.0, "gw2_points": 1.6, "gw3_points": 2.1, "gw4_points": 1.6, "gw5_points": 1.7, "gw6_points": 1.9, "gw7_points": 2.4, "gw8_points": 1.2, "gw9_points": 1.3, "points_per_million": 3.53},
        {"id": 1220, "name": "Doherty", "position_name": "Defender", "team": "Wolves", "price": 4.5, "uncertainty_percent": "46%", "overall_total": 15.8, "gw1_points": 1.7, "gw2_points": 1.4, "gw3_points": 2.0, "gw4_points": 1.4, "gw5_points": 2.1, "gw6_points": 1.3, "gw7_points": 1.6, "gw8_points": 1.9, "gw9_points": 2.4, "points_per_million": 3.51},
        {"id": 1221, "name": "Amad", "position_name": "Midfielder", "team": "Man United", "price": 6.5, "uncertainty_percent": "55%", "overall_total": 15.7, "gw1_points": 1.5, "gw2_points": 1.6, "gw3_points": 2.2, "gw4_points": 1.3, "gw5_points": 1.8, "gw6_points": 1.7, "gw7_points": 2.3, "gw8_points": 1.4, "gw9_points": 1.8, "points_per_million": 2.42},
        {"id": 1222, "name": "Gruev", "position_name": "Midfielder", "team": "Leeds", "price": 5.0, "uncertainty_percent": "31%", "overall_total": 15.5, "gw1_points": 1.7, "gw2_points": 1.4, "gw3_points": 1.6, "gw4_points": 1.7, "gw5_points": 1.8, "gw6_points": 1.6, "gw7_points": 1.8, "gw8_points": 1.8, "gw9_points": 2.0, "points_per_million": 3.10},
        {"id": 1223, "name": "Georginio", "position_name": "Midfielder", "team": "Ajax", "price": 6.0, "uncertainty_percent": "50%", "overall_total": 15.5, "gw1_points": 2.1, "gw2_points": 1.5, "gw3_points": 1.7, "gw4_points": 1.8, "gw5_points": 1.9, "gw6_points": 1.3, "gw7_points": 1.9, "gw8_points": 2.1, "gw9_points": 1.2, "points_per_million": 2.58},
        {"id": 1224, "name": "Isidor", "position_name": "Forward", "team": "Lens", "price": 5.5, "uncertainty_percent": "49%", "overall_total": 15.3, "gw1_points": 1.9, "gw2_points": 1.8, "gw3_points": 1.8, "gw4_points": 1.5, "gw5_points": 1.7, "gw6_points": 1.6, "gw7_points": 1.6, "gw8_points": 2.0, "gw9_points": 1.4, "points_per_million": 2.78},
        {"id": 1225, "name": "Xhaka", "position_name": "Midfielder", "team": "Bayer Leverkusen", "price": 5.0, "uncertainty_percent": "35%", "overall_total": 15.2, "gw1_points": 1.9, "gw2_points": 1.9, "gw3_points": 1.7, "gw4_points": 1.6, "gw5_points": 1.9, "gw6_points": 1.4, "gw7_points": 1.1, "gw8_points": 2.0, "gw9_points": 1.7, "points_per_million": 3.04},
        {"id": 1226, "name": "Gordon", "position_name": "Midfielder", "team": "Newcastle", "price": 7.5, "uncertainty_percent": "53%", "overall_total": 15.1, "gw1_points": 1.0, "gw2_points": 1.6, "gw3_points": 2.0, "gw4_points": 2.0, "gw5_points": 1.6, "gw6_points": 1.5, "gw7_points": 1.9, "gw8_points": 1.6, "gw9_points": 1.9, "points_per_million": 2.01},
        {"id": 1227, "name": "Dewsbury-Hall", "position_name": "Midfielder", "team": "Leicester", "price": 5.0, "uncertainty_percent": "45%", "overall_total": 15.1, "gw1_points": 1.8, "gw2_points": 1.7, "gw3_points": 1.4, "gw4_points": 1.7, "gw5_points": 1.2, "gw6_points": 2.1, "gw7_points": 2.0, "gw8_points": 1.5, "gw9_points": 1.9, "points_per_million": 3.02},
        {"id": 1228, "name": "Adingra", "position_name": "Midfielder", "team": "Brighton", "price": 5.5, "uncertainty_percent": "43%", "overall_total": 15.0, "gw1_points": 1.8, "gw2_points": 1.8, "gw3_points": 1.9, "gw4_points": 1.8, "gw5_points": 1.7, "gw6_points": 1.5, "gw7_points": 1.3, "gw8_points": 1.9, "gw9_points": 1.4, "points_per_million": 2.73},
        {"id": 1229, "name": "N.Jackson", "position_name": "Forward", "team": "Chelsea", "price": 6.5, "uncertainty_percent": "52%", "overall_total": 15.0, "gw1_points": 0.0, "gw2_points": 1.6, "gw3_points": 1.9, "gw4_points": 2.0, "gw5_points": 1.5, "gw6_points": 2.0, "gw7_points": 1.6, "gw8_points": 1.6, "gw9_points": 2.7, "points_per_million": 2.31},
        {"id": 1230, "name": "Earthy", "position_name": "Midfielder", "team": "West Ham", "price": 4.5, "uncertainty_percent": "47%", "overall_total": 15.0, "gw1_points": 1.8, "gw2_points": 1.7, "gw3_points": 1.6, "gw4_points": 1.7, "gw5_points": 1.9, "gw6_points": 1.6, "gw7_points": 1.2, "gw8_points": 1.6, "gw9_points": 2.0, "points_per_million": 3.33},
        {"id": 1231, "name": "Kayode", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "46%", "overall_total": 14.9, "gw1_points": 1.5, "gw2_points": 1.6, "gw3_points": 1.8, "gw4_points": 1.7, "gw5_points": 1.6, "gw6_points": 2.3, "gw7_points": 1.5, "gw8_points": 1.7, "gw9_points": 1.3, "points_per_million": 3.31},
        {"id": 1232, "name": "Adama", "position_name": "Midfielder", "team": "Fulham", "price": 5.5, "uncertainty_percent": "47%", "overall_total": 14.9, "gw1_points": 1.8, "gw2_points": 1.9, "gw3_points": 1.3, "gw4_points": 2.0, "gw5_points": 1.9, "gw6_points": 1.5, "gw7_points": 1.7, "gw8_points": 1.4, "gw9_points": 1.6, "points_per_million": 2.71},
        {"id": 1233, "name": "Emerson", "position_name": "Defender", "team": "West Ham", "price": 4.5, "uncertainty_percent": "48%", "overall_total": 14.8, "gw1_points": 1.9, "gw2_points": 1.6, "gw3_points": 1.5, "gw4_points": 1.8, "gw5_points": 1.8, "gw6_points": 1.7, "gw7_points": 1.1, "gw8_points": 1.8, "gw9_points": 1.6, "points_per_million": 3.29},
        {"id": 1234, "name": "Hee Chan", "position_name": "Midfielder", "team": "Wolves", "price": 6.0, "uncertainty_percent": "57%", "overall_total": 14.7, "gw1_points": 1.4, "gw2_points": 1.3, "gw3_points": 1.4, "gw4_points": 1.7, "gw5_points": 2.3, "gw6_points": 1.5, "gw7_points": 1.4, "gw8_points": 1.8, "gw9_points": 1.9, "points_per_million": 2.45},
        {"id": 1235, "name": "Yates", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 5.0, "uncertainty_percent": "42%", "overall_total": 14.5, "gw1_points": 2.1, "gw2_points": 1.6, "gw3_points": 2.0, "gw4_points": 1.4, "gw5_points": 1.6, "gw6_points": 1.7, "gw7_points": 1.4, "gw8_points": 1.5, "gw9_points": 1.2, "points_per_million": 2.90},
        {"id": 1236, "name": "Mazraoui", "position_name": "Defender", "team": "Bayern Munich", "price": 5.0, "uncertainty_percent": "49%", "overall_total": 14.4, "gw1_points": 0.0, "gw2_points": 1.7, "gw3_points": 2.4, "gw4_points": 1.4, "gw5_points": 1.8, "gw6_points": 1.7, "gw7_points": 2.3, "gw8_points": 1.2, "gw9_points": 2.0, "points_per_million": 2.88},
        {"id": 1237, "name": "Aaronson", "position_name": "Midfielder", "team": "Union Berlin", "price": 5.5, "uncertainty_percent": "44%", "overall_total": 14.2, "gw1_points": 1.6, "gw2_points": 1.3, "gw3_points": 1.6, "gw4_points": 1.5, "gw5_points": 1.5, "gw6_points": 1.6, "gw7_points": 1.6, "gw8_points": 1.7, "gw9_points": 1.7, "points_per_million": 2.58},
        {"id": 1238, "name": "Ramazani", "position_name": "Midfielder", "team": "Antwerp", "price": 5.0, "uncertainty_percent": "52%", "overall_total": 14.2, "gw1_points": 1.8, "gw2_points": 1.1, "gw3_points": 1.6, "gw4_points": 1.5, "gw5_points": 1.5, "gw6_points": 2.0, "gw7_points": 1.7, "gw8_points": 1.7, "gw9_points": 1.5, "points_per_million": 2.84},
        {"id": 1239, "name": "McGinn", "position_name": "Midfielder", "team": "Aston Villa", "price": 5.5, "uncertainty_percent": "45%", "overall_total": 14.2, "gw1_points": 1.6, "gw2_points": 1.5, "gw3_points": 1.6, "gw4_points": 1.5, "gw5_points": 1.7, "gw6_points": 1.6, "gw7_points": 1.9, "gw8_points": 1.4, "gw9_points": 1.4, "points_per_million": 2.58},
        {"id": 1240, "name": "N.Gonzalez", "position_name": "Midfielder", "team": "Fiorentina", "price": 6.0, "uncertainty_percent": "44%", "overall_total": 14.2, "gw1_points": 1.9, "gw2_points": 2.1, "gw3_points": 1.5, "gw4_points": 1.7, "gw5_points": 1.4, "gw6_points": 1.8, "gw7_points": 1.4, "gw8_points": 1.4, "gw9_points": 1.0, "points_per_million": 2.37},
        {"id": 1241, "name": "Elanga", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 7.0, "uncertainty_percent": "55%", "overall_total": 14.2, "gw1_points": 1.5, "gw2_points": 1.3, "gw3_points": 2.0, "gw4_points": 1.8, "gw5_points": 1.3, "gw6_points": 1.4, "gw7_points": 1.8, "gw8_points": 1.5, "gw9_points": 1.6, "points_per_million": 2.03},
        {"id": 1242, "name": "E.Le Fée", "position_name": "Midfielder", "team": "Rennes", "price": 5.0, "uncertainty_percent": "51%", "overall_total": 14.0, "gw1_points": 1.7, "gw2_points": 1.6, "gw3_points": 1.6, "gw4_points": 1.3, "gw5_points": 1.5, "gw6_points": 1.5, "gw7_points": 1.8, "gw8_points": 1.6, "gw9_points": 1.4, "points_per_million": 2.80},
        {"id": 1243, "name": "Dorgu", "position_name": "Defender", "team": "Lecce", "price": 4.5, "uncertainty_percent": "54%", "overall_total": 13.9, "gw1_points": 1.4, "gw2_points": 1.4, "gw3_points": 2.2, "gw4_points": 1.1, "gw5_points": 1.6, "gw6_points": 1.4, "gw7_points": 2.1, "gw8_points": 1.0, "gw9_points": 1.7, "points_per_million": 3.09},
        {"id": 1244, "name": "Hill", "position_name": "Defender", "team": "Blackburn", "price": 4.0, "uncertainty_percent": "51%", "overall_total": 13.9, "gw1_points": 1.1, "gw2_points": 1.7, "gw3_points": 1.4, "gw4_points": 1.6, "gw5_points": 1.6, "gw6_points": 1.8, "gw7_points": 1.8, "gw8_points": 1.4, "gw9_points": 1.5, "points_per_million": 3.48},
        {"id": 1245, "name": "Dalot", "position_name": "Defender", "team": "Man United", "price": 4.5, "uncertainty_percent": "51%", "overall_total": 13.7, "gw1_points": 1.8, "gw2_points": 1.4, "gw3_points": 2.0, "gw4_points": 0.9, "gw5_points": 1.6, "gw6_points": 1.4, "gw7_points": 2.0, "gw8_points": 1.0, "gw9_points": 1.6, "points_per_million": 3.04},
        {"id": 1246, "name": "Digne", "position_name": "Defender", "team": "Aston Villa", "price": 4.5, "uncertainty_percent": "52%", "overall_total": 13.7, "gw1_points": 1.5, "gw2_points": 1.1, "gw3_points": 1.4, "gw4_points": 1.6, "gw5_points": 1.7, "gw6_points": 1.5, "gw7_points": 2.0, "gw8_points": 1.2, "gw9_points": 1.7, "points_per_million": 3.04},
        {"id": 1247, "name": "Akanji", "position_name": "Defender", "team": "Man City", "price": 5.5, "uncertainty_percent": "50%", "overall_total": 13.7, "gw1_points": 1.7, "gw2_points": 1.5, "gw3_points": 1.4, "gw4_points": 1.7, "gw5_points": 1.1, "gw6_points": 1.9, "gw7_points": 1.4, "gw8_points": 1.7, "gw9_points": 1.3, "points_per_million": 2.49},
        {"id": 1248, "name": "P.M.Sarr", "position_name": "Midfielder", "team": "Tottenham", "price": 5.0, "uncertainty_percent": "49%", "overall_total": 13.6, "gw1_points": 1.8, "gw2_points": 1.2, "gw3_points": 1.6, "gw4_points": 1.4, "gw5_points": 1.4, "gw6_points": 1.7, "gw7_points": 1.7, "gw8_points": 1.5, "gw9_points": 1.4, "points_per_million": 2.72},
        {"id": 1249, "name": "Lerma", "position_name": "Midfielder", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "39%", "overall_total": 13.4, "gw1_points": 1.4, "gw2_points": 1.5, "gw3_points": 1.4, "gw4_points": 1.7, "gw5_points": 1.5, "gw6_points": 1.5, "gw7_points": 1.5, "gw8_points": 1.5, "gw9_points": 1.3, "points_per_million": 2.68},
        {"id": 1250, "name": "Rigg", "position_name": "Midfielder", "team": "Sunderland", "price": 5.0, "uncertainty_percent": "45%", "overall_total": 13.4, "gw1_points": 1.6, "gw2_points": 1.6, "gw3_points": 1.6, "gw4_points": 1.3, "gw5_points": 1.5, "gw6_points": 1.4, "gw7_points": 1.4, "gw8_points": 1.6, "gw9_points": 1.3, "points_per_million": 2.68},
        {"id": 1251, "name": "Muniz", "position_name": "Forward", "team": "Fulham", "price": 5.5, "uncertainty_percent": "51%", "overall_total": 13.3, "gw1_points": 1.4, "gw2_points": 1.5, "gw3_points": 1.3, "gw4_points": 1.9, "gw5_points": 1.8, "gw6_points": 1.4, "gw7_points": 1.3, "gw8_points": 1.3, "gw9_points": 1.3, "points_per_million": 2.42},
        {"id": 1252, "name": "O'Nien", "position_name": "Defender", "team": "Sunderland", "price": 4.0, "uncertainty_percent": "47%", "overall_total": 13.2, "gw1_points": 0.0, "gw2_points": 0.0, "gw3_points": 0.0, "gw4_points": 2.1, "gw5_points": 2.4, "gw6_points": 1.9, "gw7_points": 2.2, "gw8_points": 2.9, "gw9_points": 1.7, "points_per_million": 3.30},
        {"id": 1253, "name": "Castagne", "position_name": "Defender", "team": "Fulham", "price": 4.5, "uncertainty_percent": "50%", "overall_total": 13.2, "gw1_points": 1.5, "gw2_points": 1.8, "gw3_points": 1.1, "gw4_points": 1.9, "gw5_points": 2.0, "gw6_points": 1.3, "gw7_points": 1.2, "gw8_points": 1.3, "gw9_points": 1.0, "points_per_million": 2.93},
        {"id": 1254, "name": "J.Timber", "position_name": "Defender", "team": "Arsenal", "price": 5.5, "uncertainty_percent": "56%", "overall_total": 13.1, "gw1_points": 1.3, "gw2_points": 2.1, "gw3_points": 1.1, "gw4_points": 1.4, "gw5_points": 1.2, "gw6_points": 1.1, "gw7_points": 2.0, "gw8_points": 1.4, "gw9_points": 1.6, "points_per_million": 2.38},
        {"id": 1255, "name": "Gunn", "position_name": "Goalkeeper", "team": "Norwich", "price": 4.0, "uncertainty_percent": "47%", "overall_total": 13.0, "gw1_points": 1.9, "gw2_points": 1.8, "gw3_points": 1.2, "gw4_points": 1.0, "gw5_points": 1.6, "gw6_points": 1.8, "gw7_points": 1.5, "gw8_points": 1.1, "gw9_points": 1.0, "points_per_million": 3.25},
        {"id": 1256, "name": "Udogie", "position_name": "Defender", "team": "Tottenham", "price": 4.5, "uncertainty_percent": "50%", "overall_total": 12.9, "gw1_points": 0.0, "gw2_points": 0.0, "gw3_points": 1.8, "gw4_points": 1.6, "gw5_points": 1.7, "gw6_points": 1.9, "gw7_points": 1.9, "gw8_points": 1.9, "gw9_points": 2.1, "points_per_million": 2.87},
        {"id": 1257, "name": "Bergvall", "position_name": "Midfielder", "team": "Djurgården", "price": 5.5, "uncertainty_percent": "45%", "overall_total": 12.9, "gw1_points": 1.8, "gw2_points": 1.2, "gw3_points": 1.1, "gw4_points": 1.3, "gw5_points": 1.3, "gw6_points": 1.6, "gw7_points": 1.5, "gw8_points": 1.6, "gw9_points": 1.4, "points_per_million": 2.35},
        {"id": 1258, "name": "Havertz", "position_name": "Forward", "team": "Arsenal", "price": 7.5, "uncertainty_percent": "54%", "overall_total": 12.8, "gw1_points": 1.5, "gw2_points": 2.0, "gw3_points": 1.1, "gw4_points": 1.8, "gw5_points": 1.3, "gw6_points": 1.0, "gw7_points": 1.0, "gw8_points": 1.3, "gw9_points": 1.6, "points_per_million": 1.71},
        {"id": 1259, "name": "Ampadu", "position_name": "Midfielder", "team": "Leeds", "price": 5.0, "uncertainty_percent": "37%", "overall_total": 12.8, "gw1_points": 1.6, "gw2_points": 1.5, "gw3_points": 1.3, "gw4_points": 1.3, "gw5_points": 1.4, "gw6_points": 1.5, "gw7_points": 1.2, "gw8_points": 1.5, "gw9_points": 1.6, "points_per_million": 2.56},
        {"id": 1260, "name": "Savinho", "position_name": "Midfielder", "team": "Girona", "price": 7.0, "uncertainty_percent": "56%", "overall_total": 12.6, "gw1_points": 1.4, "gw2_points": 1.8, "gw3_points": 1.3, "gw4_points": 1.6, "gw5_points": 1.2, "gw6_points": 1.5, "gw7_points": 1.4, "gw8_points": 1.4, "gw9_points": 1.1, "points_per_million": 1.80},
        {"id": 1261, "name": "Hermansen", "position_name": "Goalkeeper", "team": "Leicester", "price": 4.5, "uncertainty_percent": "46%", "overall_total": 12.6, "gw1_points": 2.1, "gw2_points": 0.9, "gw3_points": 1.0, "gw4_points": 2.0, "gw5_points": 1.0, "gw6_points": 1.1, "gw7_points": 2.1, "gw8_points": 1.5, "gw9_points": 1.1, "points_per_million": 2.80},
        {"id": 1262, "name": "Bamford", "position_name": "Forward", "team": "Leeds", "price": 5.0, "uncertainty_percent": "45%", "overall_total": 12.6, "gw1_points": 1.5, "gw2_points": 1.0, "gw3_points": 1.6, "gw4_points": 1.3, "gw5_points": 1.3, "gw6_points": 1.5, "gw7_points": 1.2, "gw8_points": 1.5, "gw9_points": 1.7, "points_per_million": 2.52},
        {"id": 1263, "name": "Nwaneri", "position_name": "Midfielder", "team": "Arsenal", "price": 5.5, "uncertainty_percent": "63%", "overall_total": 12.4, "gw1_points": 1.3, "gw2_points": 1.8, "gw3_points": 1.1, "gw4_points": 1.5, "gw5_points": 1.2, "gw6_points": 1.3, "gw7_points": 1.5, "gw8_points": 1.2, "gw9_points": 1.4, "points_per_million": 2.25},
        {"id": 1264, "name": "O'Riley", "position_name": "Midfielder", "team": "Celtic", "price": 5.5, "uncertainty_percent": "52%", "overall_total": 12.4, "gw1_points": 1.6, "gw2_points": 1.3, "gw3_points": 1.3, "gw4_points": 1.4, "gw5_points": 1.4, "gw6_points": 1.2, "gw7_points": 1.4, "gw8_points": 1.4, "gw9_points": 1.3, "points_per_million": 2.25},
        {"id": 1265, "name": "Bentancur", "position_name": "Midfielder", "team": "Tottenham", "price": 5.5, "uncertainty_percent": "49%", "overall_total": 12.3, "gw1_points": 1.6, "gw2_points": 1.1, "gw3_points": 1.4, "gw4_points": 1.4, "gw5_points": 1.3, "gw6_points": 1.4, "gw7_points": 1.6, "gw8_points": 1.3, "gw9_points": 1.2, "points_per_million": 2.24},
        {"id": 1266, "name": "Scott", "position_name": "Midfielder", "team": "Bristol City", "price": 5.0, "uncertainty_percent": "41%", "overall_total": 12.2, "gw1_points": 2.1, "gw2_points": 2.6, "gw3_points": 1.0, "gw4_points": 1.1, "gw5_points": 1.1, "gw6_points": 1.2, "gw7_points": 1.1, "gw8_points": 1.0, "gw9_points": 1.1, "points_per_million": 2.44},
        {"id": 1267, "name": "Harrison", "position_name": "Midfielder", "team": "Everton", "price": 5.5, "uncertainty_percent": "51%", "overall_total": 12.1, "gw1_points": 1.3, "gw2_points": 0.9, "gw3_points": 1.4, "gw4_points": 1.2, "gw5_points": 1.2, "gw6_points": 1.5, "gw7_points": 1.6, "gw8_points": 1.3, "gw9_points": 1.7, "points_per_million": 2.20},
        {"id": 1268, "name": "Hinshelwood", "position_name": "Midfielder", "team": "Brighton", "price": 5.5, "uncertainty_percent": "45%", "overall_total": 12.0, "gw1_points": 0.9, "gw2_points": 1.4, "gw3_points": 1.3, "gw4_points": 1.4, "gw5_points": 1.5, "gw6_points": 1.2, "gw7_points": 1.5, "gw8_points": 1.5, "gw9_points": 1.4, "points_per_million": 2.18},
        {"id": 1269, "name": "Andreas", "position_name": "Midfielder", "team": "Fulham", "price": 5.5, "uncertainty_percent": "56%", "overall_total": 12.0, "gw1_points": 1.3, "gw2_points": 1.5, "gw3_points": 1.2, "gw4_points": 1.8, "gw5_points": 1.5, "gw6_points": 1.2, "gw7_points": 1.2, "gw8_points": 1.2, "gw9_points": 1.2, "points_per_million": 2.18},
        {"id": 1270, "name": "Robertson", "position_name": "Defender", "team": "Liverpool", "price": 6.0, "uncertainty_percent": "60%", "overall_total": 11.9, "gw1_points": 1.4, "gw2_points": 1.1, "gw3_points": 1.2, "gw4_points": 1.6, "gw5_points": 1.6, "gw6_points": 1.2, "gw7_points": 1.1, "gw8_points": 1.6, "gw9_points": 1.2, "points_per_million": 1.98},
        {"id": 1271, "name": "Gray", "position_name": "Midfielder", "team": "Leeds", "price": 5.0, "uncertainty_percent": "48%", "overall_total": 11.8, "gw1_points": 1.5, "gw2_points": 1.1, "gw3_points": 1.3, "gw4_points": 1.3, "gw5_points": 1.2, "gw6_points": 1.4, "gw7_points": 1.4, "gw8_points": 1.3, "gw9_points": 1.3, "points_per_million": 2.36},
        {"id": 1272, "name": "Delcroix", "position_name": "Defender", "team": "Union SG", "price": 4.0, "uncertainty_percent": "53%", "overall_total": 11.5, "gw1_points": 1.9, "gw2_points": 1.7, "gw3_points": 1.4, "gw4_points": 1.0, "gw5_points": 1.3, "gw6_points": 0.8, "gw7_points": 0.8, "gw8_points": 1.4, "gw9_points": 1.2, "points_per_million": 2.88},
        {"id": 1273, "name": "Dominguez", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 5.0, "uncertainty_percent": "48%", "overall_total": 11.5, "gw1_points": 0.0, "gw2_points": 0.0, "gw3_points": 0.0, "gw4_points": 1.6, "gw5_points": 1.9, "gw6_points": 2.4, "gw7_points": 1.7, "gw8_points": 1.9, "gw9_points": 1.9, "points_per_million": 2.30},
        {"id": 1274, "name": "Chirewa", "position_name": "Midfielder", "team": "Wolves", "price": 4.5, "uncertainty_percent": "62%", "overall_total": 11.4, "gw1_points": 1.1, "gw2_points": 1.1, "gw3_points": 1.7, "gw4_points": 1.0, "gw5_points": 1.3, "gw6_points": 1.1, "gw7_points": 1.4, "gw8_points": 1.4, "gw9_points": 1.4, "points_per_million": 2.53},
        {"id": 1275, "name": "Mount", "position_name": "Midfielder", "team": "Man United", "price": 6.0, "uncertainty_percent": "59%", "overall_total": 11.3, "gw1_points": 1.1, "gw2_points": 1.2, "gw3_points": 1.6, "gw4_points": 1.0, "gw5_points": 1.3, "gw6_points": 1.3, "gw7_points": 1.6, "gw8_points": 1.0, "gw9_points": 1.3, "points_per_million": 1.88},
        {"id": 1276, "name": "Philip", "position_name": "Midfielder", "team": "Bristol City", "price": 5.0, "uncertainty_percent": "47%", "overall_total": 11.1, "gw1_points": 2.3, "gw2_points": 2.4, "gw3_points": 0.8, "gw4_points": 0.9, "gw5_points": 1.0, "gw6_points": 1.2, "gw7_points": 0.8, "gw8_points": 0.7, "gw9_points": 0.9, "points_per_million": 2.22},
        {"id": 1277, "name": "Cook", "position_name": "Midfielder", "team": "Bournemouth", "price": 5.0, "uncertainty_percent": "46%", "overall_total": 11.1, "gw1_points": 0.0, "gw2_points": 0.0, "gw3_points": 1.6, "gw4_points": 1.6, "gw5_points": 1.5, "gw6_points": 1.7, "gw7_points": 1.6, "gw8_points": 1.5, "gw9_points": 1.6, "points_per_million": 2.22},
        {"id": 1278, "name": "Longstaff", "position_name": "Midfielder", "team": "Newcastle", "price": 5.0, "uncertainty_percent": "43%", "overall_total": 11.1, "gw1_points": 1.4, "gw2_points": 1.3, "gw3_points": 1.3, "gw4_points": 1.0, "gw5_points": 1.1, "gw6_points": 1.3, "gw7_points": 1.2, "gw8_points": 1.2, "gw9_points": 1.1, "points_per_million": 2.22},
        {"id": 1279, "name": "Davies", "position_name": "Defender", "team": "Tottenham", "price": 4.5, "uncertainty_percent": "58%", "overall_total": 11.0, "gw1_points": 1.6, "gw2_points": 0.8, "gw3_points": 1.2, "gw4_points": 1.1, "gw5_points": 1.1, "gw6_points": 1.3, "gw7_points": 1.4, "gw8_points": 1.2, "gw9_points": 1.3, "points_per_million": 2.44},
        {"id": 1280, "name": "Roberts", "position_name": "Defender", "team": "Leeds", "price": 4.5, "uncertainty_percent": "56%", "overall_total": 11.0, "gw1_points": 0.3, "gw2_points": 1.9, "gw3_points": 1.3, "gw4_points": 1.1, "gw5_points": 1.5, "gw6_points": 0.9, "gw7_points": 0.9, "gw8_points": 1.9, "gw9_points": 1.3, "points_per_million": 2.44},
        {"id": 1281, "name": "Bradley", "position_name": "Defender", "team": "Liverpool", "price": 5.0, "uncertainty_percent": "60%", "overall_total": 10.9, "gw1_points": 0.0, "gw2_points": 0.5, "gw3_points": 1.3, "gw4_points": 1.7, "gw5_points": 1.8, "gw6_points": 1.4, "gw7_points": 1.2, "gw8_points": 1.8, "gw9_points": 1.3, "points_per_million": 2.18},
        {"id": 1282, "name": "Yoro", "position_name": "Defender", "team": "Lille", "price": 4.5, "uncertainty_percent": "56%", "overall_total": 10.8, "gw1_points": 1.3, "gw2_points": 1.0, "gw3_points": 1.5, "gw4_points": 0.9, "gw5_points": 1.3, "gw6_points": 1.1, "gw7_points": 1.8, "gw8_points": 0.8, "gw9_points": 1.2, "points_per_million": 2.40},
        {"id": 1283, "name": "Nkunku", "position_name": "Midfielder", "team": "Chelsea", "price": 6.0, "uncertainty_percent": "64%", "overall_total": 10.7, "gw1_points": 1.5, "gw2_points": 1.3, "gw3_points": 1.2, "gw4_points": 1.0, "gw5_points": 1.3, "gw6_points": 1.2, "gw7_points": 1.0, "gw8_points": 0.9, "gw9_points": 1.4, "points_per_million": 1.78},
        {"id": 1284, "name": "Gruda", "position_name": "Midfielder", "team": "Mainz", "price": 5.5, "uncertainty_percent": "55%", "overall_total": 10.6, "gw1_points": 1.3, "gw2_points": 1.1, "gw3_points": 1.1, "gw4_points": 1.1, "gw5_points": 1.3, "gw6_points": 1.1, "gw7_points": 1.2, "gw8_points": 1.3, "gw9_points": 1.1, "points_per_million": 1.93},
        {"id": 1285, "name": "Ajer", "position_name": "Defender", "team": "Brentford", "price": 4.5, "uncertainty_percent": "49%", "overall_total": 10.5, "gw1_points": 1.0, "gw2_points": 1.4, "gw3_points": 1.3, "gw4_points": 1.2, "gw5_points": 1.1, "gw6_points": 1.1, "gw7_points": 1.2, "gw8_points": 1.2, "gw9_points": 1.1, "points_per_million": 2.33},
        {"id": 1286, "name": "Mainoo", "position_name": "Midfielder", "team": "Man United", "price": 5.0, "uncertainty_percent": "53%", "overall_total": 10.5, "gw1_points": 1.1, "gw2_points": 1.1, "gw3_points": 1.4, "gw4_points": 1.0, "gw5_points": 1.1, "gw6_points": 1.2, "gw7_points": 1.5, "gw8_points": 1.0, "gw9_points": 1.2, "points_per_million": 2.10},
        {"id": 1287, "name": "Füllkrug", "position_name": "Forward", "team": "Borussia Dortmund", "price": 6.0, "uncertainty_percent": "54%", "overall_total": 10.4, "gw1_points": 1.3, "gw2_points": 1.1, "gw3_points": 1.1, "gw4_points": 1.2, "gw5_points": 1.2, "gw6_points": 1.1, "gw7_points": 0.9, "gw8_points": 1.3, "gw9_points": 1.3, "points_per_million": 1.73},
        {"id": 1288, "name": "Cirkin", "position_name": "Defender", "team": "Sunderland", "price": 4.0, "uncertainty_percent": "57%", "overall_total": 10.4, "gw1_points": 0.0, "gw2_points": 0.0, "gw3_points": 0.0, "gw4_points": 1.8, "gw5_points": 1.9, "gw6_points": 1.5, "gw7_points": 1.8, "gw8_points": 2.1, "gw9_points": 1.3, "points_per_million": 2.60},
        {"id": 1289, "name": "Richarlison", "position_name": "Forward", "team": "Tottenham", "price": 6.5, "uncertainty_percent": "64%", "overall_total": 10.4, "gw1_points": 1.4, "gw2_points": 0.7, "gw3_points": 1.0, "gw4_points": 1.3, "gw5_points": 1.1, "gw6_points": 1.5, "gw7_points": 1.3, "gw8_points": 1.1, "gw9_points": 0.9, "points_per_million": 1.60},
        {"id": 1290, "name": "Botman", "position_name": "Defender", "team": "Newcastle", "price": 5.0, "uncertainty_percent": "55%", "overall_total": 10.1, "gw1_points": 1.0, "gw2_points": 1.0, "gw3_points": 1.3, "gw4_points": 1.3, "gw5_points": 1.1, "gw6_points": 1.0, "gw7_points": 1.3, "gw8_points": 1.0, "gw9_points": 1.2, "points_per_million": 2.02},
        {"id": 1291, "name": "Malacia", "position_name": "Defender", "team": "Man United", "price": 4.0, "uncertainty_percent": "60%", "overall_total": 10.1, "gw1_points": 1.4, "gw2_points": 0.7, "gw3_points": 1.5, "gw4_points": 0.8, "gw5_points": 1.2, "gw6_points": 1.1, "gw7_points": 1.5, "gw8_points": 0.8, "gw9_points": 1.2, "points_per_million": 2.53},
        {"id": 1292, "name": "Bayindir", "position_name": "Goalkeeper", "team": "Man United", "price": 5.0, "uncertainty_percent": "54%", "overall_total": 10.1, "gw1_points": 2.3, "gw2_points": 0.7, "gw3_points": 1.1, "gw4_points": 0.6, "gw5_points": 0.8, "gw6_points": 0.7, "gw7_points": 1.0, "gw8_points": 2.0, "gw9_points": 0.9, "points_per_million": 2.02},
        {"id": 1293, "name": "Gnonto", "position_name": "Midfielder", "team": "Leeds", "price": 5.5, "uncertainty_percent": "69%", "overall_total": 9.8, "gw1_points": 1.1, "gw2_points": 0.9, "gw3_points": 1.1, "gw4_points": 1.0, "gw5_points": 1.0, "gw6_points": 1.1, "gw7_points": 1.1, "gw8_points": 1.2, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1294, "name": "Laurent", "position_name": "Midfielder", "team": "Nice", "price": 5.0, "uncertainty_percent": "43%", "overall_total": 9.8, "gw1_points": 1.0, "gw2_points": 1.2, "gw3_points": 1.1, "gw4_points": 1.0, "gw5_points": 1.1, "gw6_points": 0.9, "gw7_points": 1.0, "gw8_points": 1.3, "gw9_points": 1.1, "points_per_million": 1.96},
        {"id": 1295, "name": "O'Reilly", "position_name": "Defender", "team": "Celtic", "price": 5.0, "uncertainty_percent": "66%", "overall_total": 9.8, "gw1_points": 1.1, "gw2_points": 1.1, "gw3_points": 1.0, "gw4_points": 1.2, "gw5_points": 0.8, "gw6_points": 1.3, "gw7_points": 1.0, "gw8_points": 1.2, "gw9_points": 1.0, "points_per_million": 1.96},
        {"id": 1296, "name": "Jordan", "position_name": "Defender", "team": "Crystal Palace", "price": 4.0, "uncertainty_percent": "57%", "overall_total": 9.7, "gw1_points": 0.0, "gw2_points": 1.8, "gw3_points": 1.1, "gw4_points": 1.0, "gw5_points": 1.3, "gw6_points": 0.9, "gw7_points": 0.9, "gw8_points": 1.7, "gw9_points": 1.0, "points_per_million": 2.43},
        {"id": 1297, "name": "Lewis", "position_name": "Defender", "team": "Man City", "price": 5.0, "uncertainty_percent": "72%", "overall_total": 9.5, "gw1_points": 0.9, "gw2_points": 0.9, "gw3_points": 1.1, "gw4_points": 1.3, "gw5_points": 0.6, "gw6_points": 1.3, "gw7_points": 0.9, "gw8_points": 1.5, "gw9_points": 1.1, "points_per_million": 1.90},
        {"id": 1298, "name": "Elliott", "position_name": "Midfielder", "team": "Liverpool", "price": 5.5, "uncertainty_percent": "67%", "overall_total": 9.5, "gw1_points": 1.1, "gw2_points": 1.0, "gw3_points": 0.9, "gw4_points": 1.1, "gw5_points": 1.1, "gw6_points": 1.0, "gw7_points": 1.0, "gw8_points": 1.1, "gw9_points": 1.1, "points_per_million": 1.73},
        {"id": 1299, "name": "Scarles", "position_name": "Defender", "team": "West Ham", "price": 4.5, "uncertainty_percent": "66%", "overall_total": 9.3, "gw1_points": 1.1, "gw2_points": 1.0, "gw3_points": 0.9, "gw4_points": 1.1, "gw5_points": 1.1, "gw6_points": 1.1, "gw7_points": 0.7, "gw8_points": 1.1, "gw9_points": 1.2, "points_per_million": 2.07},
        {"id": 1300, "name": "Kalajdžić", "position_name": "Forward", "team": "Wolves", "price": 5.0, "uncertainty_percent": "63%", "overall_total": 9.3, "gw1_points": 1.0, "gw2_points": 1.2, "gw3_points": 0.8, "gw4_points": 1.1, "gw5_points": 1.1, "gw6_points": 1.0, "gw7_points": 0.8, "gw8_points": 1.1, "gw9_points": 1.3, "points_per_million": 1.86},
        {"id": 1301, "name": "Foster", "position_name": "Forward", "team": "Watford", "price": 5.0, "uncertainty_percent": "55%", "overall_total": 9.3, "gw1_points": 1.6, "gw2_points": 1.2, "gw3_points": 0.9, "gw4_points": 0.9, "gw5_points": 0.9, "gw6_points": 0.8, "gw7_points": 0.9, "gw8_points": 1.1, "gw9_points": 1.0, "points_per_million": 1.86},
        {"id": 1302, "name": "Mings", "position_name": "Defender", "team": "Aston Villa", "price": 4.5, "uncertainty_percent": "66%", "overall_total": 9.3, "gw1_points": 0.9, "gw2_points": 0.9, "gw3_points": 1.3, "gw4_points": 1.1, "gw5_points": 1.1, "gw6_points": 1.0, "gw7_points": 1.4, "gw8_points": 0.8, "gw9_points": 0.8, "points_per_million": 2.07},
        {"id": 1303, "name": "Brooks", "position_name": "Midfielder", "team": "Southampton", "price": 5.0, "uncertainty_percent": "55%", "overall_total": 9.2, "gw1_points": 1.0, "gw2_points": 1.5, "gw3_points": 0.9, "gw4_points": 1.1, "gw5_points": 0.8, "gw6_points": 1.0, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.84},
        {"id": 1304, "name": "Mavropanos", "position_name": "Defender", "team": "West Ham", "price": 4.5, "uncertainty_percent": "61%", "overall_total": 9.1, "gw1_points": 1.2, "gw2_points": 0.9, "gw3_points": 0.9, "gw4_points": 1.0, "gw5_points": 1.0, "gw6_points": 1.1, "gw7_points": 0.8, "gw8_points": 1.0, "gw9_points": 1.1, "points_per_million": 2.02},
        {"id": 1305, "name": "Cornet", "position_name": "Midfielder", "team": "West Ham", "price": 5.0, "uncertainty_percent": "65%", "overall_total": 9.1, "gw1_points": 0.9, "gw2_points": 1.1, "gw3_points": 0.9, "gw4_points": 1.0, "gw5_points": 1.1, "gw6_points": 1.0, "gw7_points": 1.0, "gw8_points": 1.2, "gw9_points": 0.8, "points_per_million": 1.82},
        {"id": 1306, "name": "Sambi", "position_name": "Midfielder", "team": "Luton", "price": 4.5, "uncertainty_percent": "63%", "overall_total": 9.0, "gw1_points": 1.0, "gw2_points": 1.2, "gw3_points": 0.8, "gw4_points": 0.9, "gw5_points": 0.8, "gw6_points": 1.0, "gw7_points": 1.3, "gw8_points": 1.0, "gw9_points": 1.0, "points_per_million": 2.00},
        {"id": 1307, "name": "Awoniyi", "position_name": "Forward", "team": "Nottingham Forest", "price": 5.5, "uncertainty_percent": "59%", "overall_total": 8.9, "gw1_points": 1.2, "gw2_points": 1.0, "gw3_points": 1.0, "gw4_points": 0.7, "gw5_points": 0.8, "gw6_points": 1.4, "gw7_points": 1.0, "gw8_points": 0.9, "gw9_points": 1.0, "points_per_million": 1.62},
        {"id": 1308, "name": "Sancho", "position_name": "Midfielder", "team": "Man United", "price": 6.0, "uncertainty_percent": "62%", "overall_total": 8.9, "gw1_points": 1.0, "gw2_points": 1.0, "gw3_points": 1.2, "gw4_points": 0.7, "gw5_points": 0.9, "gw6_points": 1.0, "gw7_points": 1.1, "gw8_points": 0.9, "gw9_points": 1.1, "points_per_million": 1.48},
        {"id": 1309, "name": "Patterson", "position_name": "Defender", "team": "Everton", "price": 4.5, "uncertainty_percent": "70%", "overall_total": 8.9, "gw1_points": 1.0, "gw2_points": 1.0, "gw3_points": 1.1, "gw4_points": 0.9, "gw5_points": 0.6, "gw6_points": 1.4, "gw7_points": 1.2, "gw8_points": 0.9, "gw9_points": 0.9, "points_per_million": 1.98},
        {"id": 1310, "name": "Gusto", "position_name": "Defender", "team": "Chelsea", "price": 5.0, "uncertainty_percent": "54%", "overall_total": 8.8, "gw1_points": 1.2, "gw2_points": 0.9, "gw3_points": 1.1, "gw4_points": 0.8, "gw5_points": 0.9, "gw6_points": 1.0, "gw7_points": 0.8, "gw8_points": 1.0, "gw9_points": 1.1, "points_per_million": 1.76},
        {"id": 1311, "name": "Tsimikas", "position_name": "Defender", "team": "Liverpool", "price": 5.0, "uncertainty_percent": "75%", "overall_total": 8.5, "gw1_points": 1.0, "gw2_points": 0.8, "gw3_points": 0.8, "gw4_points": 1.1, "gw5_points": 1.1, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 1.1, "gw9_points": 0.9, "points_per_million": 1.70},
        {"id": 1312, "name": "Ramsdale", "position_name": "Goalkeeper", "team": "Arsenal", "price": 5.0, "uncertainty_percent": "60%", "overall_total": 8.3, "gw1_points": 0.6, "gw2_points": 0.5, "gw3_points": 1.7, "gw4_points": 0.9, "gw5_points": 1.7, "gw6_points": 1.1, "gw7_points": 0.8, "gw8_points": 0.5, "gw9_points": 0.6, "points_per_million": 1.66},
        {"id": 1313, "name": "Seelt", "position_name": "Defender", "team": "Sunderland", "price": 4.0, "uncertainty_percent": "59%", "overall_total": 8.3, "gw1_points": 2.3, "gw2_points": 2.2, "gw3_points": 2.0, "gw4_points": 0.3, "gw5_points": 0.3, "gw6_points": 0.4, "gw7_points": 0.3, "gw8_points": 0.4, "gw9_points": 0.3, "points_per_million": 2.08},
        {"id": 1314, "name": "Tuanzebe", "position_name": "Defender", "team": "Ipswich", "price": 4.0, "uncertainty_percent": "66%", "overall_total": 8.3, "gw1_points": 1.0, "gw2_points": 1.5, "gw3_points": 0.8, "gw4_points": 0.7, "gw5_points": 1.0, "gw6_points": 0.6, "gw7_points": 0.6, "gw8_points": 1.1, "gw9_points": 1.0, "points_per_million": 2.08},
        {"id": 1315, "name": "Hall", "position_name": "Defender", "team": "Chelsea", "price": 5.5, "uncertainty_percent": "73%", "overall_total": 8.2, "gw1_points": 0.8, "gw2_points": 0.9, "gw3_points": 1.0, "gw4_points": 1.2, "gw5_points": 0.8, "gw6_points": 0.7, "gw7_points": 0.9, "gw8_points": 0.8, "gw9_points": 1.2, "points_per_million": 1.49},
        {"id": 1316, "name": "McAtee", "position_name": "Midfielder", "team": "Sheffield United", "price": 5.5, "uncertainty_percent": "77%", "overall_total": 8.1, "gw1_points": 1.1, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.9, "gw5_points": 0.6, "gw6_points": 1.2, "gw7_points": 0.9, "gw8_points": 0.9, "gw9_points": 0.7, "points_per_million": 1.47},
        {"id": 1317, "name": "Baldock", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1318, "name": "Bogle", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1319, "name": "Osborn", "position_name": "Midfielder", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1320, "name": "Fleck", "position_name": "Midfielder", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1321, "name": "Norwood", "position_name": "Midfielder", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1322, "name": "Stevens", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1323, "name": "Sharp", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1324, "name": "McGoldrick", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1325, "name": "Basham", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1326, "name": "Egan", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1327, "name": "Robinson", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1328, "name": "Jagielka", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1329, "name": "Lundstram", "position_name": "Midfielder", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1330, "name": "Duffy", "position_name": "Defender", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1331, "name": "Moore", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1332, "name": "Mousset", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1333, "name": "McBurnie", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1334, "name": "Brewster", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1335, "name": "Burke", "position_name": "Midfielder", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1336, "name": "McGoldrick", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1337, "name": "McGoldrick", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1338, "name": "McGoldrick", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1339, "name": "McGoldrick", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1340, "name": "McGoldrick", "position_name": "Forward", "team": "Sheffield United", "price": 4.5, "uncertainty_percent": "67%", "overall_total": 8.0, "gw1_points": 1.0, "gw2_points": 0.9, "gw3_points": 0.8, "gw4_points": 0.8, "gw5_points": 0.8, "gw6_points": 0.9, "gw7_points": 0.8, "gw8_points": 0.9, "gw9_points": 1.2, "points_per_million": 1.78},
        {"id": 1341, "name": "Richards", "position_name": "Defender", "team": "Crystal Palace", "price": 4.5, "uncertainty_percent": "25%", "overall_total": 3.0, "gw1_points": 0.3, "gw2_points": 0.3, "gw3_points": 0.3, "gw4_points": 0.3, "gw5_points": 0.3, "gw6_points": 0.3, "gw7_points": 0.3, "gw8_points": 0.3, "gw9_points": 0.3, "points_per_million": 0.67},
        {"id": 1342, "name": "M.Salah", "position_name": "Midfielder", "team": "Liverpool", "price": 14.5, "uncertainty_percent": "24%", "overall_total": 57.0, "gw1_points": 6.7, "gw2_points": 6.1, "gw3_points": 5.6, "gw4_points": 7.0, "gw5_points": 6.6, "gw6_points": 5.7, "gw7_points": 5.7, "gw8_points": 7.4, "gw9_points": 6.2, "points_per_million": 3.93},
        {"id": 1343, "name": "Haaland", "position_name": "Forward", "team": "Man City", "price": 14.0, "uncertainty_percent": "24%", "overall_total": 47.0, "gw1_points": 5.1, "gw2_points": 6.3, "gw3_points": 5.1, "gw4_points": 5.8, "gw5_points": 3.8, "gw6_points": 6.6, "gw7_points": 4.8, "gw8_points": 5.1, "gw9_points": 4.4, "points_per_million": 3.36},
        {"id": 1344, "name": "Palmer", "position_name": "Midfielder", "team": "Chelsea", "price": 10.5, "uncertainty_percent": "28%", "overall_total": 45.8, "gw1_points": 5.1, "gw2_points": 4.9, "gw3_points": 5.5, "gw4_points": 4.6, "gw5_points": 4.3, "gw6_points": 5.9, "gw7_points": 4.4, "gw8_points": 4.3, "gw9_points": 6.7, "points_per_million": 4.36},
        {"id": 1345, "name": "Watkins", "position_name": "Forward", "team": "Aston Villa", "price": 9.0, "uncertainty_percent": "24%", "overall_total": 44.9, "gw1_points": 5.2, "gw2_points": 4.6, "gw3_points": 4.8, "gw4_points": 4.1, "gw5_points": 5.7, "gw6_points": 5.2, "gw7_points": 6.6, "gw8_points": 4.5, "gw9_points": 4.1, "points_per_million": 4.99},
        {"id": 1346, "name": "Isak", "position_name": "Forward", "team": "Newcastle", "price": 10.5, "uncertainty_percent": "24%", "overall_total": 44.6, "gw1_points": 4.4, "gw2_points": 4.5, "gw3_points": 5.8, "gw4_points": 5.7, "gw5_points": 4.7, "gw6_points": 4.1, "gw7_points": 5.4, "gw8_points": 4.7, "gw9_points": 5.4, "points_per_million": 4.25},
        {"id": 1347, "name": "Wood", "position_name": "Forward", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 40.3, "gw1_points": 4.8, "gw2_points": 3.9, "gw3_points": 5.2, "gw4_points": 3.2, "gw5_points": 4.8, "gw6_points": 5.8, "gw7_points": 3.9, "gw8_points": 4.6, "gw9_points": 4.0, "points_per_million": 5.37},
        {"id": 1348, "name": "Eze", "position_name": "Midfielder", "team": "Crystal Palace", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 39.4, "gw1_points": 4.1, "gw2_points": 4.8, "gw3_points": 4.0, "gw4_points": 5.8, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 4.0, "gw8_points": 4.9, "gw9_points": 3.4, "points_per_million": 5.25},
        {"id": 1349, "name": "Saka", "position_name": "Midfielder", "team": "Arsenal", "price": 10.0, "uncertainty_percent": "29%", "overall_total": 37.8, "gw1_points": 3.9, "gw2_points": 5.9, "gw3_points": 3.3, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.7, "gw7_points": 4.6, "gw8_points": 3.6, "gw9_points": 4.5, "points_per_million": 3.78},
        {"id": 1350, "name": "Evanilson", "position_name": "Forward", "team": "Porto", "price": 7.0, "uncertainty_percent": "24%", "overall_total": 36.9, "gw1_points": 3.4, "gw2_points": 4.6, "gw3_points": 3.9, "gw4_points": 4.2, "gw5_points": 4.3, "gw6_points": 4.7, "gw7_points": 4.0, "gw8_points": 3.6, "gw9_points": 4.2, "points_per_million": 5.27},
        {"id": 1351, "name": "Wissa", "position_name": "Forward", "team": "Brentford", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 36.6, "gw1_points": 3.8, "gw2_points": 4.4, "gw3_points": 4.7, "gw4_points": 4.0, "gw5_points": 3.7, "gw6_points": 4.5, "gw7_points": 3.8, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 4.88},
        {"id": 1352, "name": "B.Fernandes", "position_name": "Midfielder", "team": "Man United", "price": 9.0, "uncertainty_percent": "29%", "overall_total": 35.4, "gw1_points": 3.4, "gw2_points": 3.7, "gw3_points": 4.9, "gw4_points": 3.1, "gw5_points": 4.1, "gw6_points": 3.8, "gw7_points": 5.3, "gw8_points": 2.9, "gw9_points": 4.1, "points_per_million": 3.93},
        {"id": 1353, "name": "Virgil", "position_name": "Defender", "team": "Liverpool", "price": 6.0, "uncertainty_percent": "24%", "overall_total": 35.1, "gw1_points": 4.2, "gw2_points": 3.2, "gw3_points": 3.5, "gw4_points": 4.4, "gw5_points": 4.6, "gw6_points": 3.7, "gw7_points": 3.3, "gw8_points": 4.4, "gw9_points": 3.8, "points_per_million": 5.85},
        {"id": 1354, "name": "Gibbs-White", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 35.1, "gw1_points": 4.3, "gw2_points": 3.5, "gw3_points": 4.4, "gw4_points": 2.9, "gw5_points": 4.2, "gw6_points": 5.2, "gw7_points": 3.4, "gw8_points": 3.9, "gw9_points": 3.4, "points_per_million": 4.68},
        {"id": 1355, "name": "Strand Larsen", "position_name": "Forward", "team": "Celta Vigo", "price": 6.5, "uncertainty_percent": "25%", "overall_total": 34.8, "gw1_points": 3.2, "gw2_points": 3.5, "gw3_points": 3.7, "gw4_points": 3.4, "gw5_points": 5.1, "gw6_points": 3.5, "gw7_points": 3.8, "gw8_points": 4.3, "gw9_points": 4.4, "points_per_million": 5.35},
        {"id": 1356, "name": "Rice", "position_name": "Midfielder", "team": "Arsenal", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 34.4, "gw1_points": 3.7, "gw2_points": 5.0, "gw3_points": 3.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.5, "gw7_points": 4.1, "gw8_points": 3.6, "gw9_points": 4.0, "points_per_million": 5.29},
        {"id": 1357, "name": "Rogers", "position_name": "Midfielder", "team": "Aston Villa", "price": 7.0, "uncertainty_percent": "28%", "overall_total": 33.7, "gw1_points": 1.1, "gw2_points": 4.0, "gw3_points": 4.2, "gw4_points": 3.7, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 5.2, "gw8_points": 3.7, "gw9_points": 3.3, "points_per_million": 4.81},
        {"id": 1358, "name": "Sánchez", "position_name": "Goalkeeper", "team": "Chelsea", "price": 5.0, "uncertainty_percent": "22%", "overall_total": 33.7, "gw1_points": 4.0, "gw2_points": 3.7, "gw3_points": 4.0, "gw4_points": 3.5, "gw5_points": 3.7, "gw6_points": 3.9, "gw7_points": 3.3, "gw8_points": 3.3, "gw9_points": 4.3, "points_per_million": 6.74},
        {"id": 1359, "name": "Welbeck", "position_name": "Forward", "team": "Brighton", "price": 6.5, "uncertainty_percent": "26%", "overall_total": 33.5, "gw1_points": 4.1, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.4, "gw5_points": 4.1, "gw6_points": 3.3, "gw7_points": 4.0, "gw8_points": 4.2, "gw9_points": 3.5, "points_per_million": 5.15},
        {"id": 1360, "name": "Mac Allister", "position_name": "Midfielder", "team": "Liverpool", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.4, "gw1_points": 4.0, "gw2_points": 3.5, "gw3_points": 3.2, "gw4_points": 4.0, "gw5_points": 3.9, "gw6_points": 3.6, "gw7_points": 3.2, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 5.14},
        {"id": 1361, "name": "Petrović", "position_name": "Goalkeeper", "team": "Chelsea", "price": 4.5, "uncertainty_percent": "21%", "overall_total": 33.3, "gw1_points": 3.4, "gw2_points": 3.9, "gw3_points": 3.3, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 3.8, "gw7_points": 3.8, "gw8_points": 3.9, "gw9_points": 3.8, "points_per_million": 7.40},
        {"id": 1362, "name": "Muñoz", "position_name": "Defender", "team": "Crystal Palace", "price": 5.5, "uncertainty_percent": "28%", "overall_total": 33.3, "gw1_points": 2.9, "gw2_points": 4.2, "gw3_points": 3.2, "gw4_points": 5.3, "gw5_points": 3.7, "gw6_points": 3.3, "gw7_points": 3.9, "gw8_points": 4.3, "gw9_points": 2.7, "points_per_million": 6.05},
        {"id": 1363, "name": "Bruno G.", "position_name": "Midfielder", "team": "Newcastle", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.0, "gw1_points": 3.4, "gw2_points": 3.5, "gw3_points": 4.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.1, "gw7_points": 3.9, "gw8_points": 3.5, "gw9_points": 3.9, "points_per_million": 5.08},
        {"id": 1364, "name": "Schade", "position_name": "Midfielder", "team": "Brentford", "price": 7.0, "uncertainty_percent": "27%", "overall_total": 33.0, "gw1_points": 1.6, "gw2_points": 4.2, "gw3_points": 4.5, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 4.4, "gw7_points": 3.5, "gw8_points": 3.8, "gw9_points": 3.5, "points_per_million": 4.71},
        {"id": 1365, "name": "Saliba", "position_name": "Defender", "team": "Arsenal", "price": 6.0, "uncertainty_percent": "25%", "overall_total": 32.8, "gw1_points": 3.4, "gw2_points": 4.7, "gw3_points": 2.8, "gw4_points": 3.9, "gw5_points": 3.5, "gw6_points": 3.1, "gw7_points": 4.2, "gw8_points": 3.5, "gw9_points": 3.9, "points_per_million": 5.47},
        {"id": 1366, "name": "Leno", "position_name": "Goalkeeper", "team": "Fulham", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 32.7, "gw1_points": 3.8, "gw2_points": 4.1, "gw3_points": 3.5, "gw4_points": 4.2, "gw5_points": 3.8, "gw6_points": 3.2, "gw7_points": 3.9, "gw8_points": 3.3, "gw9_points": 3.0, "points_per_million": 6.54},
        {"id": 1367, "name": "Murillo", "position_name": "Defender", "team": "Nottingham Forest", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.6, "gw1_points": 3.9, "gw2_points": 3.4, "gw3_points": 3.9, "gw4_points": 3.0, "gw5_points": 4.0, "gw6_points": 4.6, "gw7_points": 2.8, "gw8_points": 3.4, "gw9_points": 3.5, "points_per_million": 5.93},
        {"id": 1368, "name": "Raya", "position_name": "Goalkeeper", "team": "Arsenal", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.5, "gw1_points": 3.3, "gw2_points": 4.3, "gw3_points": 3.3, "gw4_points": 3.7, "gw5_points": 3.5, "gw6_points": 3.1, "gw7_points": 4.3, "gw8_points": 3.3, "gw9_points": 3.8, "points_per_million": 5.91},
        {"id": 1369, "name": "Milenković", "position_name": "Defender", "team": "Fiorentina", "price": 5.5, "uncertainty_percent": "27%", "overall_total": 32.5, "gw1_points": 4.0, "gw2_points": 3.2, "gw3_points": 4.1, "gw4_points": 2.7, "gw5_points": 4.1, "gw6_points": 4.7, "gw7_points": 2.7, "gw8_points": 3.5, "gw9_points": 3.4, "points_per_million": 5.91},
        {"id": 1370, "name": "Branthwaite", "position_name": "Defender", "team": "Everton", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.0, "gw1_points": 4.0, "gw2_points": 3.8, "gw3_points": 3.5, "gw4_points": 3.5, "gw5_points": 3.0, "gw6_points": 3.9, "gw7_points": 3.7, "gw8_points": 3.0, "gw9_points": 3.5, "points_per_million": 5.82},
        {"id": 1371, "name": "Martinelli", "position_name": "Midfielder", "team": "Arsenal", "price": 7.0, "uncertainty_percent": "32%", "overall_total": 31.7, "gw1_points": 3.1, "gw2_points": 4.6, "gw3_points": 2.9, "gw4_points": 3.8, "gw5_points": 3.2, "gw6_points": 3.0, "gw7_points": 4.0, "gw8_points": 3.4, "gw9_points": 3.7, "points_per_million": 4.53},
        {"id": 1372, "name": "Sarr", "position_name": "Midfielder", "team": "Watford", "price": 6.5, "uncertainty_percent": "27%", "overall_total": 31.6, "gw1_points": 3.1, "gw2_points": 3.9, "gw3_points": 3.1, "gw4_points": 4.7, "gw5_points": 3.7, "gw6_points": 3.3, "gw7_points": 3.3, "gw8_points": 3.7, "gw9_points": 2.8, "points_per_million": 4.86},
        {"id": 1373, "name": "Lacroix", "position_name": "Defender", "team": "Wolfsburg", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 31.5, "gw1_points": 2.8, "gw2_points": 3.6, "gw3_points": 3.0, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.3, "gw7_points": 3.9, "gw8_points": 3.7, "gw9_points": 3.0, "points_per_million": 6.30},
        {"id": 1374, "name": "Tarkowski", "position_name": "Defender", "team": "Everton", "price": 5.5, "uncertainty_percent": "26%", "overall_total": 31.2, "gw1_points": 3.9, "gw2_points": 3.6, "gw3_points": 3.5, "gw4_points": 3.6, "gw5_points": 3.0, "gw6_points": 3.6, "gw7_points": 3.8, "gw8_points": 2.7, "gw9_points": 3.4, "points_per_million": 5.67},
        {"id": 1375, "name": "Mykolenko", "position_name": "Defender", "team": "Everton", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 31.0, "gw1_points": 4.0, "gw2_points": 3.6, "gw3_points": 3.4, "gw4_points": 3.5, "gw5_points": 2.6, "gw6_points": 3.9, "gw7_points": 3.8, "gw8_points": 2.7, "gw9_points": 3.5, "points_per_million": 6.20},
        {"id": 1376, "name": "McNeil", "position_name": "Midfielder", "team": "Everton", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 30.7, "gw1_points": 4.0, "gw2_points": 3.6, "gw3_points": 3.3, "gw4_points": 3.7, "gw5_points": 2.7, "gw6_points": 3.6, "gw7_points": 3.5, "gw8_points": 2.7, "gw9_points": 3.6, "points_per_million": 5.12},
        {"id": 1377, "name": "Tonali", "position_name": "Midfielder", "team": "Newcastle", "price": 5.5, "uncertainty_percent": "23%", "overall_total": 30.7, "gw1_points": 3.2, "gw2_points": 3.3, "gw3_points": 3.7, "gw4_points": 3.8, "gw5_points": 3.3, "gw6_points": 3.0, "gw7_points": 3.6, "gw8_points": 3.2, "gw9_points": 3.5, "points_per_million": 5.58},
        {"id": 1378, "name": "Johnson", "position_name": "Midfielder", "team": "Tottenham", "price": 7.0, "uncertainty_percent": "35%", "overall_total": 30.6, "gw1_points": 4.7, "gw2_points": 2.5, "gw3_points": 3.3, "gw4_points": 3.1, "gw5_points": 3.1, "gw6_points": 3.4, "gw7_points": 3.9, "gw8_points": 3.6, "gw9_points": 3.0, "points_per_million": 4.37},
        {"id": 1379, "name": "Konaté", "position_name": "Defender", "team": "Liverpool", "price": 5.5, "uncertainty_percent": "25%", "overall_total": 30.6, "gw1_points": 3.8, "gw2_points": 2.8, "gw3_points": 3.1, "gw4_points": 3.8, "gw5_points": 4.2, "gw6_points": 3.1, "gw7_points": 2.6, "gw8_points": 3.9, "gw9_points": 3.2, "points_per_million": 5.56},
        {"id": 1380, "name": "José Sá", "position_name": "Goalkeeper", "team": "Wolves", "price": 4.5, "uncertainty_percent": "23%", "overall_total": 30.3, "gw1_points": 3.5, "gw2_points": 3.6, "gw3_points": 3.9, "gw4_points": 1.9, "gw5_points": 3.3, "gw6_points": 3.1, "gw7_points": 3.6, "gw8_points": 3.5, "gw9_points": 4.0, "points_per_million": 6.73},
        {"id": 1381, "name": "Cucurella", "position_name": "Defender", "team": "Chelsea", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 30.3, "gw1_points": 3.7, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.1, "gw5_points": 3.0, "gw6_points": 3.6, "gw7_points": 2.7, "gw8_points": 2.8, "gw9_points": 4.5, "points_per_million": 5.05},
        {"id": 1382, "name": "Henderson", "position_name": "Goalkeeper", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 30.2, "gw1_points": 3.2, "gw2_points": 3.4, "gw3_points": 3.0, "gw4_points": 4.2, "gw5_points": 3.1, "gw6_points": 3.3, "gw7_points": 3.1, "gw8_points": 3.8, "gw9_points": 3.0, "points_per_million": 6.04},
        {"id": 1383, "name": "Verbruggen", "position_name": "Goalkeeper", "team": "Brighton", "price": 4.5, "uncertainty_percent": "23%", "overall_total": 30.1, "gw1_points": 3.6, "gw2_points": 3.8, "gw3_points": 3.2, "gw4_points": 3.5, "gw5_points": 3.4, "gw6_points": 2.8, "gw7_points": 3.3, "gw8_points": 3.1, "gw9_points": 3.4, "points_per_million": 6.69},
        {"id": 1384, "name": "Richards", "position_name": "Defender", "team": "Crystal Palace", "price": 4.5, "uncertainty_percent": "25%", "overall_total": 3.0, "gw1_points": 0.3, "gw2_points": 0.3, "gw3_points": 0.3, "gw4_points": 0.3, "gw5_points": 0.3, "gw6_points": 0.3, "gw7_points": 0.3, "gw8_points": 0.3, "gw9_points": 0.3, "points_per_million": 0.67},
        {"id": 1385, "name": "M.Salah", "position_name": "Midfielder", "team": "Liverpool", "price": 14.5, "uncertainty_percent": "24%", "overall_total": 57.0, "gw1_points": 6.7, "gw2_points": 6.1, "gw3_points": 5.6, "gw4_points": 7.0, "gw5_points": 6.6, "gw6_points": 5.7, "gw7_points": 5.7, "gw8_points": 7.4, "gw9_points": 6.2, "points_per_million": 3.93},
        {"id": 1386, "name": "Haaland", "position_name": "Forward", "team": "Man City", "price": 14.0, "uncertainty_percent": "24%", "overall_total": 47.0, "gw1_points": 5.1, "gw2_points": 6.3, "gw3_points": 5.1, "gw4_points": 5.8, "gw5_points": 3.8, "gw6_points": 6.6, "gw7_points": 4.8, "gw8_points": 5.1, "gw9_points": 4.4, "points_per_million": 3.36},
        {"id": 1387, "name": "Palmer", "position_name": "Midfielder", "team": "Chelsea", "price": 10.5, "uncertainty_percent": "28%", "overall_total": 45.8, "gw1_points": 5.1, "gw2_points": 4.9, "gw3_points": 5.5, "gw4_points": 4.6, "gw5_points": 4.3, "gw6_points": 5.9, "gw7_points": 4.4, "gw8_points": 4.3, "gw9_points": 6.7, "points_per_million": 4.36},
        {"id": 1388, "name": "Watkins", "position_name": "Forward", "team": "Aston Villa", "price": 9.0, "uncertainty_percent": "24%", "overall_total": 44.9, "gw1_points": 5.2, "gw2_points": 4.6, "gw3_points": 4.8, "gw4_points": 4.1, "gw5_points": 5.7, "gw6_points": 5.2, "gw7_points": 6.6, "gw8_points": 4.5, "gw9_points": 4.1, "points_per_million": 4.99},
        {"id": 1389, "name": "Isak", "position_name": "Forward", "team": "Newcastle", "price": 10.5, "uncertainty_percent": "24%", "overall_total": 44.6, "gw1_points": 4.4, "gw2_points": 4.5, "gw3_points": 5.8, "gw4_points": 5.7, "gw5_points": 4.7, "gw6_points": 4.1, "gw7_points": 5.4, "gw8_points": 4.7, "gw9_points": 5.4, "points_per_million": 4.25},
        {"id": 1390, "name": "Wood", "position_name": "Forward", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 40.3, "gw1_points": 4.8, "gw2_points": 3.9, "gw3_points": 5.2, "gw4_points": 3.2, "gw5_points": 4.8, "gw6_points": 5.8, "gw7_points": 3.9, "gw8_points": 4.6, "gw9_points": 4.0, "points_per_million": 5.37},
        {"id": 1391, "name": "Eze", "position_name": "Midfielder", "team": "Crystal Palace", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 39.4, "gw1_points": 4.1, "gw2_points": 4.8, "gw3_points": 4.0, "gw4_points": 5.8, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 4.0, "gw8_points": 4.9, "gw9_points": 3.4, "points_per_million": 5.25},
        {"id": 1392, "name": "Saka", "position_name": "Midfielder", "team": "Arsenal", "price": 10.0, "uncertainty_percent": "29%", "overall_total": 37.8, "gw1_points": 3.9, "gw2_points": 5.9, "gw3_points": 3.3, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.7, "gw7_points": 4.6, "gw8_points": 3.6, "gw9_points": 4.5, "points_per_million": 3.78},
        {"id": 1393, "name": "Evanilson", "position_name": "Forward", "team": "Porto", "price": 7.0, "uncertainty_percent": "24%", "overall_total": 36.9, "gw1_points": 3.4, "gw2_points": 4.6, "gw3_points": 3.9, "gw4_points": 4.2, "gw5_points": 4.3, "gw6_points": 4.7, "gw7_points": 4.0, "gw8_points": 3.6, "gw9_points": 4.2, "points_per_million": 5.27},
        {"id": 1394, "name": "Wissa", "position_name": "Forward", "team": "Brentford", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 36.6, "gw1_points": 3.8, "gw2_points": 4.4, "gw3_points": 4.7, "gw4_points": 4.0, "gw5_points": 3.7, "gw6_points": 4.5, "gw7_points": 3.8, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 4.88},
        {"id": 1395, "name": "B.Fernandes", "position_name": "Midfielder", "team": "Man United", "price": 9.0, "uncertainty_percent": "29%", "overall_total": 35.4, "gw1_points": 3.4, "gw2_points": 3.7, "gw3_points": 4.9, "gw4_points": 3.1, "gw5_points": 4.1, "gw6_points": 3.8, "gw7_points": 5.3, "gw8_points": 2.9, "gw9_points": 4.1, "points_per_million": 3.93},
        {"id": 1396, "name": "Virgil", "position_name": "Defender", "team": "Liverpool", "price": 6.0, "uncertainty_percent": "24%", "overall_total": 35.1, "gw1_points": 4.2, "gw2_points": 3.2, "gw3_points": 3.5, "gw4_points": 4.4, "gw5_points": 4.6, "gw6_points": 3.7, "gw7_points": 3.3, "gw8_points": 4.4, "gw9_points": 3.8, "points_per_million": 5.85},
        {"id": 1397, "name": "Gibbs-White", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 35.1, "gw1_points": 4.3, "gw2_points": 3.5, "gw3_points": 4.4, "gw4_points": 2.9, "gw5_points": 4.2, "gw6_points": 5.2, "gw7_points": 3.4, "gw8_points": 3.9, "gw9_points": 3.4, "points_per_million": 4.68},
        {"id": 1398, "name": "Strand Larsen", "position_name": "Forward", "team": "Celta Vigo", "price": 6.5, "uncertainty_percent": "25%", "overall_total": 34.8, "gw1_points": 3.2, "gw2_points": 3.5, "gw3_points": 3.7, "gw4_points": 3.4, "gw5_points": 5.1, "gw6_points": 3.5, "gw7_points": 3.8, "gw8_points": 4.3, "gw9_points": 4.4, "points_per_million": 5.35},
        {"id": 1399, "name": "Rice", "position_name": "Midfielder", "team": "Arsenal", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 34.4, "gw1_points": 3.7, "gw2_points": 5.0, "gw3_points": 3.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.5, "gw7_points": 4.1, "gw8_points": 3.6, "gw9_points": 4.0, "points_per_million": 5.29},
        {"id": 1400, "name": "Rogers", "position_name": "Midfielder", "team": "Aston Villa", "price": 7.0, "uncertainty_percent": "28%", "overall_total": 33.7, "gw1_points": 1.1, "gw2_points": 4.0, "gw3_points": 4.2, "gw4_points": 3.7, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 5.2, "gw8_points": 3.7, "gw9_points": 3.3, "points_per_million": 4.81},
        {"id": 1401, "name": "Sánchez", "position_name": "Goalkeeper", "team": "Chelsea", "price": 5.0, "uncertainty_percent": "22%", "overall_total": 33.7, "gw1_points": 4.0, "gw2_points": 3.7, "gw3_points": 4.0, "gw4_points": 3.5, "gw5_points": 3.7, "gw6_points": 3.9, "gw7_points": 3.3, "gw8_points": 3.3, "gw9_points": 4.3, "points_per_million": 6.74},
        {"id": 1402, "name": "Welbeck", "position_name": "Forward", "team": "Brighton", "price": 6.5, "uncertainty_percent": "26%", "overall_total": 33.5, "gw1_points": 4.1, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.4, "gw5_points": 4.1, "gw6_points": 3.3, "gw7_points": 4.0, "gw8_points": 4.2, "gw9_points": 3.5, "points_per_million": 5.15},
        {"id": 1403, "name": "Mac Allister", "position_name": "Midfielder", "team": "Liverpool", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.4, "gw1_points": 4.0, "gw2_points": 3.5, "gw3_points": 3.2, "gw4_points": 4.0, "gw5_points": 3.9, "gw6_points": 3.6, "gw7_points": 3.2, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 5.14},
        {"id": 1404, "name": "Petrović", "position_name": "Goalkeeper", "team": "Chelsea", "price": 4.5, "uncertainty_percent": "21%", "overall_total": 33.3, "gw1_points": 3.4, "gw2_points": 3.9, "gw3_points": 3.3, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 3.8, "gw7_points": 3.8, "gw8_points": 3.9, "gw9_points": 3.8, "points_per_million": 7.40},
        {"id": 1405, "name": "Muñoz", "position_name": "Defender", "team": "Crystal Palace", "price": 5.5, "uncertainty_percent": "28%", "overall_total": 33.3, "gw1_points": 2.9, "gw2_points": 4.2, "gw3_points": 3.2, "gw4_points": 5.3, "gw5_points": 3.7, "gw6_points": 3.3, "gw7_points": 3.9, "gw8_points": 4.3, "gw9_points": 2.7, "points_per_million": 6.05},
        {"id": 1406, "name": "Bruno G.", "position_name": "Midfielder", "team": "Newcastle", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.0, "gw1_points": 3.4, "gw2_points": 3.5, "gw3_points": 4.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.1, "gw7_points": 3.9, "gw8_points": 3.5, "gw9_points": 3.9, "points_per_million": 5.08},
        {"id": 1407, "name": "Schade", "position_name": "Midfielder", "team": "Brentford", "price": 7.0, "uncertainty_percent": "27%", "overall_total": 33.0, "gw1_points": 1.6, "gw2_points": 4.2, "gw3_points": 4.5, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 4.4, "gw7_points": 3.5, "gw8_points": 3.8, "gw9_points": 3.5, "points_per_million": 4.71},
        {"id": 1408, "name": "Saliba", "position_name": "Defender", "team": "Arsenal", "price": 6.0, "uncertainty_percent": "25%", "overall_total": 32.8, "gw1_points": 3.4, "gw2_points": 4.7, "gw3_points": 2.8, "gw4_points": 3.9, "gw5_points": 3.5, "gw6_points": 3.1, "gw7_points": 4.2, "gw8_points": 3.5, "gw9_points": 3.9, "points_per_million": 5.47},
        {"id": 1409, "name": "Leno", "position_name": "Goalkeeper", "team": "Fulham", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 32.7, "gw1_points": 3.8, "gw2_points": 4.1, "gw3_points": 3.5, "gw4_points": 4.2, "gw5_points": 3.8, "gw6_points": 3.2, "gw7_points": 3.9, "gw8_points": 3.3, "gw9_points": 3.0, "points_per_million": 6.54},
        {"id": 1410, "name": "Murillo", "position_name": "Defender", "team": "Nottingham Forest", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.6, "gw1_points": 3.9, "gw2_points": 3.4, "gw3_points": 3.9, "gw4_points": 3.0, "gw5_points": 4.0, "gw6_points": 4.6, "gw7_points": 2.8, "gw8_points": 3.4, "gw9_points": 3.5, "points_per_million": 5.93},
        {"id": 1411, "name": "Raya", "position_name": "Goalkeeper", "team": "Arsenal", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.5, "gw1_points": 3.3, "gw2_points": 4.3, "gw3_points": 3.3, "gw4_points": 3.7, "gw5_points": 3.5, "gw6_points": 3.1, "gw7_points": 4.3, "gw8_points": 3.3, "gw9_points": 3.8, "points_per_million": 5.91},
        {"id": 1412, "name": "Milenković", "position_name": "Defender", "team": "Fiorentina", "price": 5.5, "uncertainty_percent": "27%", "overall_total": 32.5, "gw1_points": 4.0, "gw2_points": 3.2, "gw3_points": 4.1, "gw4_points": 2.7, "gw5_points": 4.1, "gw6_points": 4.7, "gw7_points": 2.7, "gw8_points": 3.5, "gw9_points": 3.4, "points_per_million": 5.91},
        {"id": 1413, "name": "Branthwaite", "position_name": "Defender", "team": "Everton", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.0, "gw1_points": 4.0, "gw2_points": 3.8, "gw3_points": 3.5, "gw4_points": 3.5, "gw5_points": 3.0, "gw6_points": 3.9, "gw7_points": 3.7, "gw8_points": 3.0, "gw9_points": 3.5, "points_per_million": 5.82},
        {"id": 1414, "name": "Martinelli", "position_name": "Midfielder", "team": "Arsenal", "price": 7.0, "uncertainty_percent": "32%", "overall_total": 31.7, "gw1_points": 3.1, "gw2_points": 4.6, "gw3_points": 2.9, "gw4_points": 3.8, "gw5_points": 3.2, "gw6_points": 3.0, "gw7_points": 4.0, "gw8_points": 3.4, "gw9_points": 3.7, "points_per_million": 4.53},
        {"id": 1415, "name": "Sarr", "position_name": "Midfielder", "team": "Watford", "price": 6.5, "uncertainty_percent": "27%", "overall_total": 31.6, "gw1_points": 3.1, "gw2_points": 3.9, "gw3_points": 3.1, "gw4_points": 4.7, "gw5_points": 3.7, "gw6_points": 3.3, "gw7_points": 3.3, "gw8_points": 3.7, "gw9_points": 2.8, "points_per_million": 4.86},
        {"id": 1416, "name": "Lacroix", "position_name": "Defender", "team": "Wolfsburg", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 31.5, "gw1_points": 2.8, "gw2_points": 3.6, "gw3_points": 3.0, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.3, "gw7_points": 3.9, "gw8_points": 3.7, "gw9_points": 3.0, "points_per_million": 6.30},
        {"id": 1417, "name": "Tarkowski", "position_name": "Defender", "team": "Everton", "price": 5.5, "uncertainty_percent": "26%", "overall_total": 31.2, "gw1_points": 3.9, "gw2_points": 3.6, "gw3_points": 3.5, "gw4_points": 3.6, "gw5_points": 3.0, "gw6_points": 3.6, "gw7_points": 3.8, "gw8_points": 2.7, "gw9_points": 3.4, "points_per_million": 5.67},
        {"id": 1418, "name": "Mykolenko", "position_name": "Defender", "team": "Everton", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 31.0, "gw1_points": 4.0, "gw2_points": 3.6, "gw3_points": 3.4, "gw4_points": 3.5, "gw5_points": 2.6, "gw6_points": 3.9, "gw7_points": 3.8, "gw8_points": 2.7, "gw9_points": 3.5, "points_per_million": 6.20},
        {"id": 1419, "name": "McNeil", "position_name": "Midfielder", "team": "Everton", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 30.7, "gw1_points": 4.0, "gw2_points": 3.6, "gw3_points": 3.3, "gw4_points": 3.7, "gw5_points": 2.7, "gw6_points": 3.6, "gw7_points": 3.5, "gw8_points": 2.7, "gw9_points": 3.6, "points_per_million": 5.12},
        {"id": 1420, "name": "Tonali", "position_name": "Midfielder", "team": "Newcastle", "price": 5.5, "uncertainty_percent": "23%", "overall_total": 30.7, "gw1_points": 3.2, "gw2_points": 3.3, "gw3_points": 3.7, "gw4_points": 3.8, "gw5_points": 3.3, "gw6_points": 3.0, "gw7_points": 3.6, "gw8_points": 3.2, "gw9_points": 3.5, "points_per_million": 5.58},
        {"id": 1421, "name": "Johnson", "position_name": "Midfielder", "team": "Tottenham", "price": 7.0, "uncertainty_percent": "35%", "overall_total": 30.6, "gw1_points": 4.7, "gw2_points": 2.5, "gw3_points": 3.3, "gw4_points": 3.1, "gw5_points": 3.1, "gw6_points": 3.4, "gw7_points": 3.9, "gw8_points": 3.6, "gw9_points": 3.0, "points_per_million": 4.37},
        {"id": 1422, "name": "Konaté", "position_name": "Defender", "team": "Liverpool", "price": 5.5, "uncertainty_percent": "25%", "overall_total": 30.6, "gw1_points": 3.8, "gw2_points": 2.8, "gw3_points": 3.1, "gw4_points": 3.8, "gw5_points": 4.2, "gw6_points": 3.1, "gw7_points": 2.6, "gw8_points": 3.9, "gw9_points": 3.2, "points_per_million": 5.56},
        {"id": 1423, "name": "José Sá", "position_name": "Goalkeeper", "team": "Wolves", "price": 4.5, "uncertainty_percent": "23%", "overall_total": 30.3, "gw1_points": 3.5, "gw2_points": 3.6, "gw3_points": 3.9, "gw4_points": 1.9, "gw5_points": 3.3, "gw6_points": 3.1, "gw7_points": 3.6, "gw8_points": 3.5, "gw9_points": 4.0, "points_per_million": 6.73},
        {"id": 1424, "name": "Cucurella", "position_name": "Defender", "team": "Chelsea", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 30.3, "gw1_points": 3.7, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.1, "gw5_points": 3.0, "gw6_points": 3.6, "gw7_points": 2.7, "gw8_points": 2.8, "gw9_points": 4.5, "points_per_million": 5.05},
        {"id": 1425, "name": "Henderson", "position_name": "Goalkeeper", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 30.2, "gw1_points": 3.2, "gw2_points": 3.4, "gw3_points": 3.0, "gw4_points": 4.2, "gw5_points": 3.1, "gw6_points": 3.3, "gw7_points": 3.1, "gw8_points": 3.8, "gw9_points": 3.0, "points_per_million": 6.04},
        {"id": 1426, "name": "Verbruggen", "position_name": "Goalkeeper", "team": "Brighton", "price": 4.5, "uncertainty_percent": "23%", "overall_total": 30.1, "gw1_points": 3.6, "gw2_points": 3.8, "gw3_points": 3.2, "gw4_points": 3.5, "gw5_points": 3.4, "gw6_points": 2.8, "gw7_points": 3.3, "gw8_points": 3.1, "gw9_points": 3.4, "points_per_million": 6.69},
        {"id": 1427, "name": "Richards", "position_name": "Defender", "team": "Crystal Palace", "price": 4.5, "uncertainty_percent": "25%", "overall_total": 3.0, "gw1_points": 0.3, "gw2_points": 0.3, "gw3_points": 0.3, "gw4_points": 0.3, "gw5_points": 0.3, "gw6_points": 0.3, "gw7_points": 0.3, "gw8_points": 0.3, "gw9_points": 0.3, "points_per_million": 0.67},
        {"id": 1428, "name": "M.Salah", "position_name": "Midfielder", "team": "Liverpool", "price": 14.5, "uncertainty_percent": "24%", "overall_total": 57.0, "gw1_points": 6.7, "gw2_points": 6.1, "gw3_points": 5.6, "gw4_points": 7.0, "gw5_points": 6.6, "gw6_points": 5.7, "gw7_points": 5.7, "gw8_points": 7.4, "gw9_points": 6.2, "points_per_million": 3.93},
        {"id": 1429, "name": "Haaland", "position_name": "Forward", "team": "Man City", "price": 14.0, "uncertainty_percent": "24%", "overall_total": 47.0, "gw1_points": 5.1, "gw2_points": 6.3, "gw3_points": 5.1, "gw4_points": 5.8, "gw5_points": 3.8, "gw6_points": 6.6, "gw7_points": 4.8, "gw8_points": 5.1, "gw9_points": 4.4, "points_per_million": 3.36},
        {"id": 1430, "name": "Palmer", "position_name": "Midfielder", "team": "Chelsea", "price": 10.5, "uncertainty_percent": "28%", "overall_total": 45.8, "gw1_points": 5.1, "gw2_points": 4.9, "gw3_points": 5.5, "gw4_points": 4.6, "gw5_points": 4.3, "gw6_points": 5.9, "gw7_points": 4.4, "gw8_points": 4.3, "gw9_points": 6.7, "points_per_million": 4.36},
        {"id": 1431, "name": "Watkins", "position_name": "Forward", "team": "Aston Villa", "price": 9.0, "uncertainty_percent": "24%", "overall_total": 44.9, "gw1_points": 5.2, "gw2_points": 4.6, "gw3_points": 4.8, "gw4_points": 4.1, "gw5_points": 5.7, "gw6_points": 5.2, "gw7_points": 6.6, "gw8_points": 4.5, "gw9_points": 4.1, "points_per_million": 4.99},
        {"id": 1432, "name": "Isak", "position_name": "Forward", "team": "Newcastle", "price": 10.5, "uncertainty_percent": "24%", "overall_total": 44.6, "gw1_points": 4.4, "gw2_points": 4.5, "gw3_points": 5.8, "gw4_points": 5.7, "gw5_points": 4.7, "gw6_points": 4.1, "gw7_points": 5.4, "gw8_points": 4.7, "gw9_points": 5.4, "points_per_million": 4.25},
        {"id": 1433, "name": "Wood", "position_name": "Forward", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 40.3, "gw1_points": 4.8, "gw2_points": 3.9, "gw3_points": 5.2, "gw4_points": 3.2, "gw5_points": 4.8, "gw6_points": 5.8, "gw7_points": 3.9, "gw8_points": 4.6, "gw9_points": 4.0, "points_per_million": 5.37},
        {"id": 1434, "name": "Eze", "position_name": "Midfielder", "team": "Crystal Palace", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 39.4, "gw1_points": 4.1, "gw2_points": 4.8, "gw3_points": 4.0, "gw4_points": 5.8, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 4.0, "gw8_points": 4.9, "gw9_points": 3.4, "points_per_million": 5.25},
        {"id": 1435, "name": "Saka", "position_name": "Midfielder", "team": "Arsenal", "price": 10.0, "uncertainty_percent": "29%", "overall_total": 37.8, "gw1_points": 3.9, "gw2_points": 5.9, "gw3_points": 3.3, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.7, "gw7_points": 4.6, "gw8_points": 3.6, "gw9_points": 4.5, "points_per_million": 3.78},
        {"id": 1436, "name": "Evanilson", "position_name": "Forward", "team": "Porto", "price": 7.0, "uncertainty_percent": "24%", "overall_total": 36.9, "gw1_points": 3.4, "gw2_points": 4.6, "gw3_points": 3.9, "gw4_points": 4.2, "gw5_points": 4.3, "gw6_points": 4.7, "gw7_points": 4.0, "gw8_points": 3.6, "gw9_points": 4.2, "points_per_million": 5.27},
        {"id": 1437, "name": "Wissa", "position_name": "Forward", "team": "Brentford", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 36.6, "gw1_points": 3.8, "gw2_points": 4.4, "gw3_points": 4.7, "gw4_points": 4.0, "gw5_points": 3.7, "gw6_points": 4.5, "gw7_points": 3.8, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 4.88},
        {"id": 1438, "name": "B.Fernandes", "position_name": "Midfielder", "team": "Man United", "price": 9.0, "uncertainty_percent": "29%", "overall_total": 35.4, "gw1_points": 3.4, "gw2_points": 3.7, "gw3_points": 4.9, "gw4_points": 3.1, "gw5_points": 4.1, "gw6_points": 3.8, "gw7_points": 5.3, "gw8_points": 2.9, "gw9_points": 4.1, "points_per_million": 3.93},
        {"id": 1439, "name": "Virgil", "position_name": "Defender", "team": "Liverpool", "price": 6.0, "uncertainty_percent": "24%", "overall_total": 35.1, "gw1_points": 4.2, "gw2_points": 3.2, "gw3_points": 3.5, "gw4_points": 4.4, "gw5_points": 4.6, "gw6_points": 3.7, "gw7_points": 3.3, "gw8_points": 4.4, "gw9_points": 3.8, "points_per_million": 5.85},
        {"id": 1440, "name": "Gibbs-White", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 35.1, "gw1_points": 4.3, "gw2_points": 3.5, "gw3_points": 4.4, "gw4_points": 2.9, "gw5_points": 4.2, "gw6_points": 5.2, "gw7_points": 3.4, "gw8_points": 3.9, "gw9_points": 3.4, "points_per_million": 4.68},
        {"id": 1441, "name": "Strand Larsen", "position_name": "Forward", "team": "Celta Vigo", "price": 6.5, "uncertainty_percent": "25%", "overall_total": 34.8, "gw1_points": 3.2, "gw2_points": 3.5, "gw3_points": 3.7, "gw4_points": 3.4, "gw5_points": 5.1, "gw6_points": 3.5, "gw7_points": 3.8, "gw8_points": 4.3, "gw9_points": 4.4, "points_per_million": 5.35},
        {"id": 1442, "name": "Rice", "position_name": "Midfielder", "team": "Arsenal", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 34.4, "gw1_points": 3.7, "gw2_points": 5.0, "gw3_points": 3.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.5, "gw7_points": 4.1, "gw8_points": 3.6, "gw9_points": 4.0, "points_per_million": 5.29},
        {"id": 1443, "name": "Rogers", "position_name": "Midfielder", "team": "Aston Villa", "price": 7.0, "uncertainty_percent": "28%", "overall_total": 33.7, "gw1_points": 1.1, "gw2_points": 4.0, "gw3_points": 4.2, "gw4_points": 3.7, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 5.2, "gw8_points": 3.7, "gw9_points": 3.3, "points_per_million": 4.81},
        {"id": 1444, "name": "Sánchez", "position_name": "Goalkeeper", "team": "Chelsea", "price": 5.0, "uncertainty_percent": "22%", "overall_total": 33.7, "gw1_points": 4.0, "gw2_points": 3.7, "gw3_points": 4.0, "gw4_points": 3.5, "gw5_points": 3.7, "gw6_points": 3.9, "gw7_points": 3.3, "gw8_points": 3.3, "gw9_points": 4.3, "points_per_million": 6.74},
        {"id": 1445, "name": "Welbeck", "position_name": "Forward", "team": "Brighton", "price": 6.5, "uncertainty_percent": "26%", "overall_total": 33.5, "gw1_points": 4.1, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.4, "gw5_points": 4.1, "gw6_points": 3.3, "gw7_points": 4.0, "gw8_points": 4.2, "gw9_points": 3.5, "points_per_million": 5.15},
        {"id": 1446, "name": "Mac Allister", "position_name": "Midfielder", "team": "Liverpool", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.4, "gw1_points": 4.0, "gw2_points": 3.5, "gw3_points": 3.2, "gw4_points": 4.0, "gw5_points": 3.9, "gw6_points": 3.6, "gw7_points": 3.2, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 5.14},
        {"id": 1447, "name": "Petrović", "position_name": "Goalkeeper", "team": "Chelsea", "price": 4.5, "uncertainty_percent": "21%", "overall_total": 33.3, "gw1_points": 3.4, "gw2_points": 3.9, "gw3_points": 3.3, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 3.8, "gw7_points": 3.8, "gw8_points": 3.9, "gw9_points": 3.8, "points_per_million": 7.40},
        {"id": 1448, "name": "Muñoz", "position_name": "Defender", "team": "Crystal Palace", "price": 5.5, "uncertainty_percent": "28%", "overall_total": 33.3, "gw1_points": 2.9, "gw2_points": 4.2, "gw3_points": 3.2, "gw4_points": 5.3, "gw5_points": 3.7, "gw6_points": 3.3, "gw7_points": 3.9, "gw8_points": 4.3, "gw9_points": 2.7, "points_per_million": 6.05},
        {"id": 1449, "name": "Bruno G.", "position_name": "Midfielder", "team": "Newcastle", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.0, "gw1_points": 3.4, "gw2_points": 3.5, "gw3_points": 4.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.1, "gw7_points": 3.9, "gw8_points": 3.5, "gw9_points": 3.9, "points_per_million": 5.08},
        {"id": 1450, "name": "Schade", "position_name": "Midfielder", "team": "Brentford", "price": 7.0, "uncertainty_percent": "27%", "overall_total": 33.0, "gw1_points": 1.6, "gw2_points": 4.2, "gw3_points": 4.5, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 4.4, "gw7_points": 3.5, "gw8_points": 3.8, "gw9_points": 3.5, "points_per_million": 4.71},
        {"id": 1451, "name": "Saliba", "position_name": "Defender", "team": "Arsenal", "price": 6.0, "uncertainty_percent": "25%", "overall_total": 32.8, "gw1_points": 3.4, "gw2_points": 4.7, "gw3_points": 2.8, "gw4_points": 3.9, "gw5_points": 3.5, "gw6_points": 3.1, "gw7_points": 4.2, "gw8_points": 3.5, "gw9_points": 3.9, "points_per_million": 5.47},
        {"id": 1452, "name": "Leno", "position_name": "Goalkeeper", "team": "Fulham", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 32.7, "gw1_points": 3.8, "gw2_points": 4.1, "gw3_points": 3.5, "gw4_points": 4.2, "gw5_points": 3.8, "gw6_points": 3.2, "gw7_points": 3.9, "gw8_points": 3.3, "gw9_points": 3.0, "points_per_million": 6.54},
        {"id": 1453, "name": "Murillo", "position_name": "Defender", "team": "Nottingham Forest", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.6, "gw1_points": 3.9, "gw2_points": 3.4, "gw3_points": 3.9, "gw4_points": 3.0, "gw5_points": 4.0, "gw6_points": 4.6, "gw7_points": 2.8, "gw8_points": 3.4, "gw9_points": 3.5, "points_per_million": 5.93},
        {"id": 1454, "name": "Raya", "position_name": "Goalkeeper", "team": "Arsenal", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.5, "gw1_points": 3.3, "gw2_points": 4.3, "gw3_points": 3.3, "gw4_points": 3.7, "gw5_points": 3.5, "gw6_points": 3.1, "gw7_points": 4.3, "gw8_points": 3.3, "gw9_points": 3.8, "points_per_million": 5.91},
        {"id": 1455, "name": "Milenković", "position_name": "Defender", "team": "Fiorentina", "price": 5.5, "uncertainty_percent": "27%", "overall_total": 32.5, "gw1_points": 4.0, "gw2_points": 3.2, "gw3_points": 4.1, "gw4_points": 2.7, "gw5_points": 4.1, "gw6_points": 4.7, "gw7_points": 2.7, "gw8_points": 3.5, "gw9_points": 3.4, "points_per_million": 5.91},
        {"id": 1456, "name": "Branthwaite", "position_name": "Defender", "team": "Everton", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.0, "gw1_points": 4.0, "gw2_points": 3.8, "gw3_points": 3.5, "gw4_points": 3.5, "gw5_points": 3.0, "gw6_points": 3.9, "gw7_points": 3.7, "gw8_points": 3.0, "gw9_points": 3.5, "points_per_million": 5.82},
        {"id": 1457, "name": "Martinelli", "position_name": "Midfielder", "team": "Arsenal", "price": 7.0, "uncertainty_percent": "32%", "overall_total": 31.7, "gw1_points": 3.1, "gw2_points": 4.6, "gw3_points": 2.9, "gw4_points": 3.8, "gw5_points": 3.2, "gw6_points": 3.0, "gw7_points": 4.0, "gw8_points": 3.4, "gw9_points": 3.7, "points_per_million": 4.53},
        {"id": 1458, "name": "Sarr", "position_name": "Midfielder", "team": "Watford", "price": 6.5, "uncertainty_percent": "27%", "overall_total": 31.6, "gw1_points": 3.1, "gw2_points": 3.9, "gw3_points": 3.1, "gw4_points": 4.7, "gw5_points": 3.7, "gw6_points": 3.3, "gw7_points": 3.3, "gw8_points": 3.7, "gw9_points": 2.8, "points_per_million": 4.86},
        {"id": 1459, "name": "Lacroix", "position_name": "Defender", "team": "Wolfsburg", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 31.5, "gw1_points": 2.8, "gw2_points": 3.6, "gw3_points": 3.0, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.3, "gw7_points": 3.9, "gw8_points": 3.7, "gw9_points": 3.0, "points_per_million": 6.30},
        {"id": 1460, "name": "Tarkowski", "position_name": "Defender", "team": "Everton", "price": 5.5, "uncertainty_percent": "26%", "overall_total": 31.2, "gw1_points": 3.9, "gw2_points": 3.6, "gw3_points": 3.5, "gw4_points": 3.6, "gw5_points": 3.0, "gw6_points": 3.6, "gw7_points": 3.8, "gw8_points": 2.7, "gw9_points": 3.4, "points_per_million": 5.67},
        {"id": 1461, "name": "Mykolenko", "position_name": "Defender", "team": "Everton", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 31.0, "gw1_points": 4.0, "gw2_points": 3.6, "gw3_points": 3.4, "gw4_points": 3.5, "gw5_points": 2.6, "gw6_points": 3.9, "gw7_points": 3.8, "gw8_points": 2.7, "gw9_points": 3.5, "points_per_million": 6.20},
        {"id": 1462, "name": "McNeil", "position_name": "Midfielder", "team": "Everton", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 30.7, "gw1_points": 4.0, "gw2_points": 3.6, "gw3_points": 3.3, "gw4_points": 3.7, "gw5_points": 2.7, "gw6_points": 3.6, "gw7_points": 3.5, "gw8_points": 2.7, "gw9_points": 3.6, "points_per_million": 5.12},
        {"id": 1463, "name": "Tonali", "position_name": "Midfielder", "team": "Newcastle", "price": 5.5, "uncertainty_percent": "23%", "overall_total": 30.7, "gw1_points": 3.2, "gw2_points": 3.3, "gw3_points": 3.7, "gw4_points": 3.8, "gw5_points": 3.3, "gw6_points": 3.0, "gw7_points": 3.6, "gw8_points": 3.2, "gw9_points": 3.5, "points_per_million": 5.58},
        {"id": 1464, "name": "Johnson", "position_name": "Midfielder", "team": "Tottenham", "price": 7.0, "uncertainty_percent": "35%", "overall_total": 30.6, "gw1_points": 4.7, "gw2_points": 2.5, "gw3_points": 3.3, "gw4_points": 3.1, "gw5_points": 3.1, "gw6_points": 3.4, "gw7_points": 3.9, "gw8_points": 3.6, "gw9_points": 3.0, "points_per_million": 4.37},
        {"id": 1465, "name": "Konaté", "position_name": "Defender", "team": "Liverpool", "price": 5.5, "uncertainty_percent": "25%", "overall_total": 30.6, "gw1_points": 3.8, "gw2_points": 2.8, "gw3_points": 3.1, "gw4_points": 3.8, "gw5_points": 4.2, "gw6_points": 3.1, "gw7_points": 2.6, "gw8_points": 3.9, "gw9_points": 3.2, "points_per_million": 5.56},
        {"id": 1466, "name": "José Sá", "position_name": "Goalkeeper", "team": "Wolves", "price": 4.5, "uncertainty_percent": "23%", "overall_total": 30.3, "gw1_points": 3.5, "gw2_points": 3.6, "gw3_points": 3.9, "gw4_points": 1.9, "gw5_points": 3.3, "gw6_points": 3.1, "gw7_points": 3.6, "gw8_points": 3.5, "gw9_points": 4.0, "points_per_million": 6.73},
        {"id": 1467, "name": "Cucurella", "position_name": "Defender", "team": "Chelsea", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 30.3, "gw1_points": 3.7, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.1, "gw5_points": 3.0, "gw6_points": 3.6, "gw7_points": 2.7, "gw8_points": 2.8, "gw9_points": 4.5, "points_per_million": 5.05},
        {"id": 1468, "name": "Henderson", "position_name": "Goalkeeper", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 30.2, "gw1_points": 3.2, "gw2_points": 3.4, "gw3_points": 3.0, "gw4_points": 4.2, "gw5_points": 3.1, "gw6_points": 3.3, "gw7_points": 3.1, "gw8_points": 3.8, "gw9_points": 3.0, "points_per_million": 6.04},
        {"id": 1469, "name": "Verbruggen", "position_name": "Goalkeeper", "team": "Brighton", "price": 4.5, "uncertainty_percent": "23%", "overall_total": 30.1, "gw1_points": 3.6, "gw2_points": 3.8, "gw3_points": 3.2, "gw4_points": 3.5, "gw5_points": 3.4, "gw6_points": 2.8, "gw7_points": 3.3, "gw8_points": 3.1, "gw9_points": 3.4, "points_per_million": 6.69},
        {"id": 1470, "name": "Richards", "position_name": "Defender", "team": "Crystal Palace", "price": 4.5, "uncertainty_percent": "25%", "overall_total": 3.0, "gw1_points": 0.3, "gw2_points": 0.3, "gw3_points": 0.3, "gw4_points": 0.3, "gw5_points": 0.3, "gw6_points": 0.3, "gw7_points": 0.3, "gw8_points": 0.3, "gw9_points": 0.3, "points_per_million": 0.67},
        {"id": 1471, "name": "M.Salah", "position_name": "Midfielder", "team": "Liverpool", "price": 14.5, "uncertainty_percent": "24%", "overall_total": 57.0, "gw1_points": 6.7, "gw2_points": 6.1, "gw3_points": 5.6, "gw4_points": 7.0, "gw5_points": 6.6, "gw6_points": 5.7, "gw7_points": 5.7, "gw8_points": 7.4, "gw9_points": 6.2, "points_per_million": 3.93},
        {"id": 1472, "name": "Haaland", "position_name": "Forward", "team": "Man City", "price": 14.0, "uncertainty_percent": "24%", "overall_total": 47.0, "gw1_points": 5.1, "gw2_points": 6.3, "gw3_points": 5.1, "gw4_points": 5.8, "gw5_points": 3.8, "gw6_points": 6.6, "gw7_points": 4.8, "gw8_points": 5.1, "gw9_points": 4.4, "points_per_million": 3.36},
        {"id": 1473, "name": "Palmer", "position_name": "Midfielder", "team": "Chelsea", "price": 10.5, "uncertainty_percent": "28%", "overall_total": 45.8, "gw1_points": 5.1, "gw2_points": 4.9, "gw3_points": 5.5, "gw4_points": 4.6, "gw5_points": 4.3, "gw6_points": 5.9, "gw7_points": 4.4, "gw8_points": 4.3, "gw9_points": 6.7, "points_per_million": 4.36},
        {"id": 1474, "name": "Watkins", "position_name": "Forward", "team": "Aston Villa", "price": 9.0, "uncertainty_percent": "24%", "overall_total": 44.9, "gw1_points": 5.2, "gw2_points": 4.6, "gw3_points": 4.8, "gw4_points": 4.1, "gw5_points": 5.7, "gw6_points": 5.2, "gw7_points": 6.6, "gw8_points": 4.5, "gw9_points": 4.1, "points_per_million": 4.99},
        {"id": 1475, "name": "Isak", "position_name": "Forward", "team": "Newcastle", "price": 10.5, "uncertainty_percent": "24%", "overall_total": 44.6, "gw1_points": 4.4, "gw2_points": 4.5, "gw3_points": 5.8, "gw4_points": 5.7, "gw5_points": 4.7, "gw6_points": 4.1, "gw7_points": 5.4, "gw8_points": 4.7, "gw9_points": 5.4, "points_per_million": 4.25},
        {"id": 1476, "name": "Wood", "position_name": "Forward", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 40.3, "gw1_points": 4.8, "gw2_points": 3.9, "gw3_points": 5.2, "gw4_points": 3.2, "gw5_points": 4.8, "gw6_points": 5.8, "gw7_points": 3.9, "gw8_points": 4.6, "gw9_points": 4.0, "points_per_million": 5.37},
        {"id": 1477, "name": "Eze", "position_name": "Midfielder", "team": "Crystal Palace", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 39.4, "gw1_points": 4.1, "gw2_points": 4.8, "gw3_points": 4.0, "gw4_points": 5.8, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 4.0, "gw8_points": 4.9, "gw9_points": 3.4, "points_per_million": 5.25},
        {"id": 1478, "name": "Saka", "position_name": "Midfielder", "team": "Arsenal", "price": 10.0, "uncertainty_percent": "29%", "overall_total": 37.8, "gw1_points": 3.9, "gw2_points": 5.9, "gw3_points": 3.3, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.7, "gw7_points": 4.6, "gw8_points": 3.6, "gw9_points": 4.5, "points_per_million": 3.78},
        {"id": 1479, "name": "Evanilson", "position_name": "Forward", "team": "Porto", "price": 7.0, "uncertainty_percent": "24%", "overall_total": 36.9, "gw1_points": 3.4, "gw2_points": 4.6, "gw3_points": 3.9, "gw4_points": 4.2, "gw5_points": 4.3, "gw6_points": 4.7, "gw7_points": 4.0, "gw8_points": 3.6, "gw9_points": 4.2, "points_per_million": 5.27},
        {"id": 1480, "name": "Wissa", "position_name": "Forward", "team": "Brentford", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 36.6, "gw1_points": 3.8, "gw2_points": 4.4, "gw3_points": 4.7, "gw4_points": 4.0, "gw5_points": 3.7, "gw6_points": 4.5, "gw7_points": 3.8, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 4.88},
        {"id": 1481, "name": "B.Fernandes", "position_name": "Midfielder", "team": "Man United", "price": 9.0, "uncertainty_percent": "29%", "overall_total": 35.4, "gw1_points": 3.4, "gw2_points": 3.7, "gw3_points": 4.9, "gw4_points": 3.1, "gw5_points": 4.1, "gw6_points": 3.8, "gw7_points": 5.3, "gw8_points": 2.9, "gw9_points": 4.1, "points_per_million": 3.93},
        {"id": 1482, "name": "Virgil", "position_name": "Defender", "team": "Liverpool", "price": 6.0, "uncertainty_percent": "24%", "overall_total": 35.1, "gw1_points": 4.2, "gw2_points": 3.2, "gw3_points": 3.5, "gw4_points": 4.4, "gw5_points": 4.6, "gw6_points": 3.7, "gw7_points": 3.3, "gw8_points": 4.4, "gw9_points": 3.8, "points_per_million": 5.85},
        {"id": 1483, "name": "Gibbs-White", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 35.1, "gw1_points": 4.3, "gw2_points": 3.5, "gw3_points": 4.4, "gw4_points": 2.9, "gw5_points": 4.2, "gw6_points": 5.2, "gw7_points": 3.4, "gw8_points": 3.9, "gw9_points": 3.4, "points_per_million": 4.68},
        {"id": 1484, "name": "Strand Larsen", "position_name": "Forward", "team": "Celta Vigo", "price": 6.5, "uncertainty_percent": "25%", "overall_total": 34.8, "gw1_points": 3.2, "gw2_points": 3.5, "gw3_points": 3.7, "gw4_points": 3.4, "gw5_points": 5.1, "gw6_points": 3.5, "gw7_points": 3.8, "gw8_points": 4.3, "gw9_points": 4.4, "points_per_million": 5.35},
        {"id": 1485, "name": "Rice", "position_name": "Midfielder", "team": "Arsenal", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 34.4, "gw1_points": 3.7, "gw2_points": 5.0, "gw3_points": 3.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.5, "gw7_points": 4.1, "gw8_points": 3.6, "gw9_points": 4.0, "points_per_million": 5.29},
        {"id": 1486, "name": "Rogers", "position_name": "Midfielder", "team": "Aston Villa", "price": 7.0, "uncertainty_percent": "28%", "overall_total": 33.7, "gw1_points": 1.1, "gw2_points": 4.0, "gw3_points": 4.2, "gw4_points": 3.7, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 5.2, "gw8_points": 3.7, "gw9_points": 3.3, "points_per_million": 4.81},
        {"id": 1487, "name": "Sánchez", "position_name": "Goalkeeper", "team": "Chelsea", "price": 5.0, "uncertainty_percent": "22%", "overall_total": 33.7, "gw1_points": 4.0, "gw2_points": 3.7, "gw3_points": 4.0, "gw4_points": 3.5, "gw5_points": 3.7, "gw6_points": 3.9, "gw7_points": 3.3, "gw8_points": 3.3, "gw9_points": 4.3, "points_per_million": 6.74},
        {"id": 1488, "name": "Welbeck", "position_name": "Forward", "team": "Brighton", "price": 6.5, "uncertainty_percent": "26%", "overall_total": 33.5, "gw1_points": 4.1, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.4, "gw5_points": 4.1, "gw6_points": 3.3, "gw7_points": 4.0, "gw8_points": 4.2, "gw9_points": 3.5, "points_per_million": 5.15},
        {"id": 1489, "name": "Mac Allister", "position_name": "Midfielder", "team": "Liverpool", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.4, "gw1_points": 4.0, "gw2_points": 3.5, "gw3_points": 3.2, "gw4_points": 4.0, "gw5_points": 3.9, "gw6_points": 3.6, "gw7_points": 3.2, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 5.14},
        {"id": 1490, "name": "Petrović", "position_name": "Goalkeeper", "team": "Chelsea", "price": 4.5, "uncertainty_percent": "21%", "overall_total": 33.3, "gw1_points": 3.4, "gw2_points": 3.9, "gw3_points": 3.3, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 3.8, "gw7_points": 3.8, "gw8_points": 3.9, "gw9_points": 3.8, "points_per_million": 7.40},
        {"id": 1491, "name": "Muñoz", "position_name": "Defender", "team": "Crystal Palace", "price": 5.5, "uncertainty_percent": "28%", "overall_total": 33.3, "gw1_points": 2.9, "gw2_points": 4.2, "gw3_points": 3.2, "gw4_points": 5.3, "gw5_points": 3.7, "gw6_points": 3.3, "gw7_points": 3.9, "gw8_points": 4.3, "gw9_points": 2.7, "points_per_million": 6.05},
        {"id": 1492, "name": "Bruno G.", "position_name": "Midfielder", "team": "Newcastle", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.0, "gw1_points": 3.4, "gw2_points": 3.5, "gw3_points": 4.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.1, "gw7_points": 3.9, "gw8_points": 3.5, "gw9_points": 3.9, "points_per_million": 5.08},
        {"id": 1493, "name": "Schade", "position_name": "Midfielder", "team": "Brentford", "price": 7.0, "uncertainty_percent": "27%", "overall_total": 33.0, "gw1_points": 1.6, "gw2_points": 4.2, "gw3_points": 4.5, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 4.4, "gw7_points": 3.5, "gw8_points": 3.8, "gw9_points": 3.5, "points_per_million": 4.71},
        {"id": 1494, "name": "Saliba", "position_name": "Defender", "team": "Arsenal", "price": 6.0, "uncertainty_percent": "25%", "overall_total": 32.8, "gw1_points": 3.4, "gw2_points": 4.7, "gw3_points": 2.8, "gw4_points": 3.9, "gw5_points": 3.5, "gw6_points": 3.1, "gw7_points": 4.2, "gw8_points": 3.5, "gw9_points": 3.9, "points_per_million": 5.47},
        {"id": 1495, "name": "Leno", "position_name": "Goalkeeper", "team": "Fulham", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 32.7, "gw1_points": 3.8, "gw2_points": 4.1, "gw3_points": 3.5, "gw4_points": 4.2, "gw5_points": 3.8, "gw6_points": 3.2, "gw7_points": 3.9, "gw8_points": 3.3, "gw9_points": 3.0, "points_per_million": 6.54},
        {"id": 1496, "name": "Murillo", "position_name": "Defender", "team": "Nottingham Forest", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.6, "gw1_points": 3.9, "gw2_points": 3.4, "gw3_points": 3.9, "gw4_points": 3.0, "gw5_points": 4.0, "gw6_points": 4.6, "gw7_points": 2.8, "gw8_points": 3.4, "gw9_points": 3.5, "points_per_million": 5.93},
        {"id": 1497, "name": "Raya", "position_name": "Goalkeeper", "team": "Arsenal", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.5, "gw1_points": 3.3, "gw2_points": 4.3, "gw3_points": 3.3, "gw4_points": 3.7, "gw5_points": 3.5, "gw6_points": 3.1, "gw7_points": 4.3, "gw8_points": 3.3, "gw9_points": 3.8, "points_per_million": 5.91},
        {"id": 1498, "name": "Milenković", "position_name": "Defender", "team": "Fiorentina", "price": 5.5, "uncertainty_percent": "27%", "overall_total": 32.5, "gw1_points": 4.0, "gw2_points": 3.2, "gw3_points": 4.1, "gw4_points": 2.7, "gw5_points": 4.1, "gw6_points": 4.7, "gw7_points": 2.7, "gw8_points": 3.5, "gw9_points": 3.4, "points_per_million": 5.91},
        {"id": 1499, "name": "Branthwaite", "position_name": "Defender", "team": "Everton", "price": 5.5, "uncertainty_percent": "24%", "overall_total": 32.0, "gw1_points": 4.0, "gw2_points": 3.8, "gw3_points": 3.5, "gw4_points": 3.5, "gw5_points": 3.0, "gw6_points": 3.9, "gw7_points": 3.7, "gw8_points": 3.0, "gw9_points": 3.5, "points_per_million": 5.82},
        {"id": 1500, "name": "Martinelli", "position_name": "Midfielder", "team": "Arsenal", "price": 7.0, "uncertainty_percent": "32%", "overall_total": 31.7, "gw1_points": 3.1, "gw2_points": 4.6, "gw3_points": 2.9, "gw4_points": 3.8, "gw5_points": 3.2, "gw6_points": 3.0, "gw7_points": 4.0, "gw8_points": 3.4, "gw9_points": 3.7, "points_per_million": 4.53},
        {"id": 1501, "name": "Sarr", "position_name": "Midfielder", "team": "Watford", "price": 6.5, "uncertainty_percent": "27%", "overall_total": 31.6, "gw1_points": 3.1, "gw2_points": 3.9, "gw3_points": 3.1, "gw4_points": 4.7, "gw5_points": 3.7, "gw6_points": 3.3, "gw7_points": 3.3, "gw8_points": 3.7, "gw9_points": 2.8, "points_per_million": 4.86},
        {"id": 1502, "name": "Lacroix", "position_name": "Defender", "team": "Wolfsburg", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 31.5, "gw1_points": 2.8, "gw2_points": 3.6, "gw3_points": 3.0, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.3, "gw7_points": 3.9, "gw8_points": 3.7, "gw9_points": 3.0, "points_per_million": 6.30},
        {"id": 1503, "name": "Tarkowski", "position_name": "Defender", "team": "Everton", "price": 5.5, "uncertainty_percent": "26%", "overall_total": 31.2, "gw1_points": 3.9, "gw2_points": 3.6, "gw3_points": 3.5, "gw4_points": 3.6, "gw5_points": 3.0, "gw6_points": 3.6, "gw7_points": 3.8, "gw8_points": 2.7, "gw9_points": 3.4, "points_per_million": 5.67},
        {"id": 1504, "name": "Mykolenko", "position_name": "Defender", "team": "Everton", "price": 5.0, "uncertainty_percent": "24%", "overall_total": 31.0, "gw1_points": 4.0, "gw2_points": 3.6, "gw3_points": 3.4, "gw4_points": 3.5, "gw5_points": 2.6, "gw6_points": 3.9, "gw7_points": 3.8, "gw8_points": 2.7, "gw9_points": 3.5, "points_per_million": 6.20},
        {"id": 1505, "name": "McNeil", "position_name": "Midfielder", "team": "Everton", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 30.7, "gw1_points": 4.0, "gw2_points": 3.6, "gw3_points": 3.3, "gw4_points": 3.7, "gw5_points": 2.7, "gw6_points": 3.6, "gw7_points": 3.5, "gw8_points": 2.7, "gw9_points": 3.6, "points_per_million": 5.12},
        {"id": 1506, "name": "Tonali", "position_name": "Midfielder", "team": "Newcastle", "price": 5.5, "uncertainty_percent": "23%", "overall_total": 30.7, "gw1_points": 3.2, "gw2_points": 3.3, "gw3_points": 3.7, "gw4_points": 3.8, "gw5_points": 3.3, "gw6_points": 3.0, "gw7_points": 3.6, "gw8_points": 3.2, "gw9_points": 3.5, "points_per_million": 5.58},
        {"id": 1507, "name": "Johnson", "position_name": "Midfielder", "team": "Tottenham", "price": 7.0, "uncertainty_percent": "35%", "overall_total": 30.6, "gw1_points": 4.7, "gw2_points": 2.5, "gw3_points": 3.3, "gw4_points": 3.1, "gw5_points": 3.1, "gw6_points": 3.4, "gw7_points": 3.9, "gw8_points": 3.6, "gw9_points": 3.0, "points_per_million": 4.37},
        {"id": 1508, "name": "Konaté", "position_name": "Defender", "team": "Liverpool", "price": 5.5, "uncertainty_percent": "25%", "overall_total": 30.6, "gw1_points": 3.8, "gw2_points": 2.8, "gw3_points": 3.1, "gw4_points": 3.8, "gw5_points": 4.2, "gw6_points": 3.1, "gw7_points": 2.6, "gw8_points": 3.9, "gw9_points": 3.2, "points_per_million": 5.56},
        {"id": 1509, "name": "José Sá", "position_name": "Goalkeeper", "team": "Wolves", "price": 4.5, "uncertainty_percent": "23%", "overall_total": 30.3, "gw1_points": 3.5, "gw2_points": 3.6, "gw3_points": 3.9, "gw4_points": 1.9, "gw5_points": 3.3, "gw6_points": 3.1, "gw7_points": 3.6, "gw8_points": 3.5, "gw9_points": 4.0, "points_per_million": 6.73},
        {"id": 1510, "name": "Cucurella", "position_name": "Defender", "team": "Chelsea", "price": 6.0, "uncertainty_percent": "28%", "overall_total": 30.3, "gw1_points": 3.7, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.1, "gw5_points": 3.0, "gw6_points": 3.6, "gw7_points": 2.7, "gw8_points": 2.8, "gw9_points": 4.5, "points_per_million": 5.05},
        {"id": 1511, "name": "Henderson", "position_name": "Goalkeeper", "team": "Crystal Palace", "price": 5.0, "uncertainty_percent": "23%", "overall_total": 30.2, "gw1_points": 3.2, "gw2_points": 3.4, "gw3_points": 3.0, "gw4_points": 4.2, "gw5_points": 3.1, "gw6_points": 3.3, "gw7_points": 3.1, "gw8_points": 3.8, "gw9_points": 3.0, "points_per_million": 6.04},
        {"id": 1512, "name": "Verbruggen", "position_name": "Goalkeeper", "team": "Brighton", "price": 4.5, "uncertainty_percent": "23%", "overall_total": 30.1, "gw1_points": 3.6, "gw2_points": 3.8, "gw3_points": 3.2, "gw4_points": 3.5, "gw5_points": 3.4, "gw6_points": 2.8, "gw7_points": 3.3, "gw8_points": 3.1, "gw9_points": 3.4, "points_per_million": 6.69},
        {"id": 1513, "name": "Richards", "position_name": "Defender", "team": "Crystal Palace", "price": 4.5, "uncertainty_percent": "25%", "overall_total": 3.0, "gw1_points": 0.3, "gw2_points": 0.3, "gw3_points": 0.3, "gw4_points": 0.3, "gw5_points": 0.3, "gw6_points": 0.3, "gw7_points": 0.3, "gw8_points": 0.3, "gw9_points": 0.3, "points_per_million": 0.67},
        {"id": 1514, "name": "M.Salah", "position_name": "Midfielder", "team": "Liverpool", "price": 14.5, "uncertainty_percent": "24%", "overall_total": 57.0, "gw1_points": 6.7, "gw2_points": 6.1, "gw3_points": 5.6, "gw4_points": 7.0, "gw5_points": 6.6, "gw6_points": 5.7, "gw7_points": 5.7, "gw8_points": 7.4, "gw9_points": 6.2, "points_per_million": 3.93},
        {"id": 1515, "name": "Haaland", "position_name": "Forward", "team": "Man City", "price": 14.0, "uncertainty_percent": "24%", "overall_total": 47.0, "gw1_points": 5.1, "gw2_points": 6.3, "gw3_points": 5.1, "gw4_points": 5.8, "gw5_points": 3.8, "gw6_points": 6.6, "gw7_points": 4.8, "gw8_points": 5.1, "gw9_points": 4.4, "points_per_million": 3.36},
        {"id": 1516, "name": "Palmer", "position_name": "Midfielder", "team": "Chelsea", "price": 10.5, "uncertainty_percent": "28%", "overall_total": 45.8, "gw1_points": 5.1, "gw2_points": 4.9, "gw3_points": 5.5, "gw4_points": 4.6, "gw5_points": 4.3, "gw6_points": 5.9, "gw7_points": 4.4, "gw8_points": 4.3, "gw9_points": 6.7, "points_per_million": 4.36},
        {"id": 1517, "name": "Watkins", "position_name": "Forward", "team": "Aston Villa", "price": 9.0, "uncertainty_percent": "24%", "overall_total": 44.9, "gw1_points": 5.2, "gw2_points": 4.6, "gw3_points": 4.8, "gw4_points": 4.1, "gw5_points": 5.7, "gw6_points": 5.2, "gw7_points": 6.6, "gw8_points": 4.5, "gw9_points": 4.1, "points_per_million": 4.99},
        {"id": 1518, "name": "Isak", "position_name": "Forward", "team": "Newcastle", "price": 10.5, "uncertainty_percent": "24%", "overall_total": 44.6, "gw1_points": 4.4, "gw2_points": 4.5, "gw3_points": 5.8, "gw4_points": 5.7, "gw5_points": 4.7, "gw6_points": 4.1, "gw7_points": 5.4, "gw8_points": 4.7, "gw9_points": 5.4, "points_per_million": 4.25},
        {"id": 1519, "name": "Wood", "position_name": "Forward", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 40.3, "gw1_points": 4.8, "gw2_points": 3.9, "gw3_points": 5.2, "gw4_points": 3.2, "gw5_points": 4.8, "gw6_points": 5.8, "gw7_points": 3.9, "gw8_points": 4.6, "gw9_points": 4.0, "points_per_million": 5.37},
        {"id": 1520, "name": "Eze", "position_name": "Midfielder", "team": "Crystal Palace", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 39.4, "gw1_points": 4.1, "gw2_points": 4.8, "gw3_points": 4.0, "gw4_points": 5.8, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 4.0, "gw8_points": 4.9, "gw9_points": 3.4, "points_per_million": 5.25},
        {"id": 1521, "name": "Saka", "position_name": "Midfielder", "team": "Arsenal", "price": 10.0, "uncertainty_percent": "29%", "overall_total": 37.8, "gw1_points": 3.9, "gw2_points": 5.9, "gw3_points": 3.3, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.7, "gw7_points": 4.6, "gw8_points": 3.6, "gw9_points": 4.5, "points_per_million": 3.78}
    ]
    
    try:
        import sqlite3
        conn = sqlite3.connect("fpl_oos.db")
        
        # Check if players already exist to avoid duplicates
        cursor = conn.execute("SELECT COUNT(*) FROM players")
        existing_count = cursor.fetchone()[0]
        
        if existing_count == 0:
            # Loop through all players and add them
            for player in players_data:
                                             conn.execute("""
                                 INSERT INTO players (id, name, position_name, team, price, availability, uncertainty_percent, overall_total,
                                                    gw1_points, gw2_points, gw3_points, gw4_points, gw5_points, gw6_points, gw7_points, gw8_points, gw9_points,
                                                    points_per_million, chance_of_playing_next_round)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                             """, (
                                 player["id"], player["name"], player["position_name"], player["team"], player["price"], 
                                 "Available", player["uncertainty_percent"], player["overall_total"],
                                 player["gw1_points"], player["gw2_points"], player["gw3_points"], player["gw4_points"], 
                                 player["gw5_points"], player["gw6_points"], player["gw7_points"], player["gw8_points"], 
                                 player["gw9_points"], player["points_per_million"], 100
                             ))
            
            conn.commit()
            print(f"Successfully added {len(players_data)} players to database via SQL")
        else:
            print("Players already exist in database, no need to add")
        
        conn.close()
        
    except Exception as e:
        print(f"Error adding players via SQL: {e}")
        

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
    
    # Save to unified database
    try:
        conn = sqlite3.connect("fpl_oos.db")
        df.to_sql("fdr_with_opponents", conn, if_exists="replace")
        conn.close()
        print("FDR data saved to unified database successfully")
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

    # Get list of teams for dropdown
    teams_list = sorted(df.index.tolist())

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
                        <select id="teamFilter" class="form-select">
                            <option value="">All Teams</option>
                        </select>
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
                // Populate team filter dropdown
                var teams = {{ teams_list|tojson }};
                var teamSelect = $('#teamFilter');
                teams.forEach(function(team) {
                    teamSelect.append($('<option></option>').val(team).text(team));
                });
                
                // Initialize DataTable
                var table = $('#fdrTable').DataTable({
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
                
                // Team filter functionality
                $('#teamFilter').on('change', function() {
                    var selectedTeam = $(this).val();
                    
                    // Clear any existing filters
                    table.search('').columns().search('').draw();
                    
                    if (selectedTeam) {
                        // Filter by team name (first column)
                        table.column(0).search(selectedTeam).draw();
                    }
                });
            });
        </script>
    </body>
    </html>
    """, table=html_table, gw_from=gw_from, gw_to=gw_to, team_filter=team_filter, teams_list=teams_list)

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
                    transition: background-color 0.2s ease;
                    user-select: none;
                }
                
                #playersTable thead th:hover {
                    background-color: #f8f9fa;
                    box-shadow: inset 0 0 0 2px #007bff;
                }
                
                #playersTable thead th.sorting:hover {
                    background-color: #e9ecef;
                }
                
                /* Make it clear headers are clickable */
                #playersTable thead th::after {
                    content: '↕';
                    position: absolute;
                    right: 8px;
                    top: 50%;
                    transform: translateY(-50%);
                    color: #6c757d;
                    font-size: 12px;
                    opacity: 0.6;
                }
                
                /* Sort order info styling */
                #sortOrderInfo {
                    font-size: 0.9em;
                    padding: 5px 10px;
                    background: #f8f9fa;
                    border-radius: 5px;
                    border-left: 3px solid #007bff;
                }
                
                /* Sort pills styling */
                .sort-pill {
                    display: inline-flex;
                    align-items: center;
                    background: linear-gradient(135deg, #007bff, #0056b3);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 16px;
                    font-size: 12px;
                    font-weight: 500;
                    box-shadow: 0 2px 4px rgba(0,123,255,0.3);
                    transition: all 0.2s ease;
                    cursor: default;
                    user-select: none;
                }
                
                .sort-pill:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 8px rgba(0,123,255,0.4);
                }
                
                .sort-pill .pill-text {
                    margin-right: 6px;
                }
                
                .sort-pill .remove-btn {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    border-radius: 50%;
                    width: 16px;
                    height: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    font-size: 10px;
                    transition: all 0.2s ease;
                }
                
                .sort-pill .remove-btn:hover {
                    background: rgba(255,255,255,0.3);
                    transform: scale(1.1);
                }
                
                .sort-pill.asc {
                    background: linear-gradient(135deg, #28a745, #1e7e34);
                }
                
                .sort-pill.desc {
                    background: linear-gradient(135deg, #dc3545, #c82333);
                }
                
                /* Sort level number styling */
                .sort-level-number {
                    position: absolute;
                    bottom: -20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #007bff;
                    color: white;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 10px;
                    font-weight: bold;
                    box-shadow: 0 2px 4px rgba(0,123,255,0.3);
                    z-index: 10;
                    border: 2px solid white;
                }
                
                /* Debug: Make sure numbers are visible */
                .sort-level-number::before {
                    content: attr(data-number);
                }
                
                /* Ensure headers have relative positioning for absolute positioning of numbers */
                #playersTable thead th {
                    position: relative;
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
                        <a class="nav-link" href="/squad">Squad</a>
                    </div>
                </div>
            </nav>
            
            <div class="container-fluid">
                <h1 class="mb-4">FPL Players - Expected Points (GW1-9)</h1>
                
                <!-- Filters Section -->
                <div class="row mb-4">
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
                
                <div class="row mb-3">
                    <div class="col-12">
                        <button id="clearFilters" class="btn btn-outline-secondary btn-sm">Clear All Filters</button>
                        <span id="filterInfo" class="ms-3 text-muted"></span>
                        <div class="mt-2">
                            <small class="text-muted">
                                <strong>Sorting:</strong> Use ↑/↓ buttons directly above each column to add sort levels • Each button adds to existing sorts • Numbers show sort order below column headers • Remove individual sorts with X button on pills
                            </small>
                        </div>

                        
                        <div id="sortPills" class="mt-2 d-flex flex-wrap gap-1">
                            <!-- Sort pills will be dynamically added here -->
                        </div>
                        <div class="mt-1">
                            <span id="sortOrderInfo" class="text-info fw-bold"></span>
                            <button id="clearSort" class="btn btn-outline-warning btn-sm ms-2">Clear Sort</button>
                            <button id="testSort" class="btn btn-outline-info btn-sm ms-2">Test Sort</button>
                            <div class="mt-2">
                                <input type="text" id="viewName" class="form-control form-control-sm d-inline-block" style="width: 200px;" placeholder="Enter view name...">
                                <button id="saveView" class="btn btn-success btn-sm ms-2">Save View</button>
                                <select id="loadView" class="form-select form-select-sm d-inline-block ms-2" style="width: 200px;">
                                    <option value="">Load Saved View...</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Table Controls - Above sort buttons -->
                <div class="mb-3">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <label for="pageLength" class="form-label mb-1">Show players per page:</label>
                            <select id="pageLength" class="form-select form-select-sm">
                                <option value="10">10</option>
                                <option value="25" selected>25</option>
                                <option value="50">50</option>
                                <option value="100">100</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label for="searchPlayers" class="form-label mb-1">Search players:</label>
                            <input type="text" id="searchPlayers" class="form-control form-control-sm" placeholder="Type to search...">
                        </div>
                    </div>
                </div>
                
                <!-- Sort Controls - Positioned directly above the table -->
                <div class="mb-2">
                    <div class="table-responsive">
                        <table class="table table-sm table-bordered sort-controls-table" style="width: 100%; margin-bottom: 0;">
                            <thead>
                                <tr>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(0, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(0, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(1, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(1, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(2, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(2, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(3, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(3, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(4, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(4, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(5, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(5, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(6, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(6, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(7, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(7, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(8, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(8, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(9, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(9, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(10, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(10, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(11, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(11, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(12, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(12, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(13, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(13, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(14, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(14, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(15, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(15, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(16, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(16, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                    <th style="text-align: center; padding: 2px;">
                                        <button class="btn btn-sm btn-outline-primary" onclick="addSortLevel(17, 'asc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↑</button>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="addSortLevel(17, 'desc')" style="width: 20px; height: 20px; padding: 0; font-size: 10px;">↓</button>
                                    </th>
                                </tr>
                            </thead>
                        </table>
                    </div>
                </div>
                
                <div class="table-responsive">
                    <table id="playersTable" class="table table-striped table-bordered">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Player<br>Name</th>
                                <th>Pos</th>
                                <th>Team</th>
                                <th>Price<br>(£M)</th>
                                <th>Form</th>
                                <th>Total<br>(GW1-9)</th>
                                <th>Points<br>/£</th>
                                <th>Chance<br>of Playing</th>
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
                                <td class="player-name"><strong>{{ player.name }}</strong></td>
                                <td>
                                    <span class="position-badge 
                                        {% if player.position_name == 'Goalkeeper' %}gk
                                        {% elif player.position_name == 'Defender' %}def
                                        {% elif player.position_name == 'Midfielder' %}mid
                                        {% else %}fwd{% endif %}">
                                        {{ player.position_name[:3] }}
                                    </span>
                                </td>
                                <td class="team-name">{{ player.team }}</td>
                                <td class="price-column">£{{ "%.1f"|format(player.price) }}M</td>
                                <td class="form-column">{{ player.form }}</td>
                                <td class="total-column"><strong>{{ "%.1f"|format(player.total_gw1_9) }}</strong></td>
                                <td class="points-per-pound">{{ "%.2f"|format(player.points_per_million) }}</td>
                                <td class="chance-column">
                                    {% if player.chance_of_playing_next_round and player.chance_of_playing_next_round < 100 %}
                                        <span class="chance-playing injured">
                                            <i class="fas fa-exclamation-triangle"></i> {{ player.chance_of_playing_next_round }}%
                                        </span>
                                    {% else %}
                                        <span class="chance-playing healthy">{{ player.chance_of_playing_next_round or 100 }}%</span>
                                    {% endif %}
                                </td>
                                <td class="gw-column">{{ "%.1f"|format(player.gw1_9_points[0]) }}</td>
                                <td class="gw-column">{{ "%.1f"|format(player.gw1_9_points[1]) }}</td>
                                <td class="gw-column">{{ "%.1f"|format(player.gw1_9_points[2]) }}</td>
                                <td class="gw-column">{{ "%.1f"|format(player.gw1_9_points[3]) }}</td>
                                <td class="gw-column">{{ "%.1f"|format(player.gw1_9_points[4]) }}</td>
                                <td class="gw-column">{{ "%.1f"|format(player.gw1_9_points[5]) }}</td>
                                <td class="gw-column">{{ "%.1f"|format(player.gw1_9_points[6]) }}</td>
                                <td class="gw-column">{{ "%.1f"|format(player.gw1_9_points[7]) }}</td>
                                <td class="gw-column">{{ "%.1f"|format(player.gw1_9_points[8]) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <script>
                $(document).ready(function() {
                    // Custom sorting for numbers with potential string values
                    $.extend($.fn.dataTable.ext.type.order, {
                        "num-pre": function (a) {
                            var x = String(a).replace(/[\d,]/g, '');
                            var y = String(a).replace(/[^\d,.-]/g, '');
                            var z = y.replace(/,/g, '');
                            return ((x == '-') ? -1 : 1) * parseFloat(z);
                        },
                        "num-asc": function (a, b) {
                            return ((a < b) ? -1 : ((a > b) ? 1 : 0));
                        },
                        "num-desc": function (a, b) {
                            return ((a < b) ? 1 : ((a > b) ? -1 : 0));
                        }
                    });
                    
                    // Populate team filter dropdown
                    var teams = [...new Set({{ players|tojson }}.map(p => p.team))].sort();
                    var teamSelect = $('#teamFilter');
                    teams.forEach(function(team) {
                        teamSelect.append($('<option></option>').val(team).text(team));
                    });
                    
                    var table = $('#playersTable').DataTable({
                        paging: true,
                        pageLength: 25,
                        ordering: true, // Enable default DataTable ordering
                        info: true,
                        searching: true,
                        order: [], // Start with no default sort
                        scrollX: true,
                        columnDefs: [
                            { targets: [0], orderable: true, width: '40px', type: 'num' }, // Rank column sortable
                            { targets: [1], orderable: true, width: '120px', type: 'string' }, // Name
                            { targets: [2], orderable: true, width: '60px', type: 'string' }, // Position
                            { targets: [3], orderable: true, width: '80px', type: 'string' }, // Team
                            { targets: [4], orderable: true, type: 'num', width: '70px' }, // Price
                            { targets: [5], orderable: true, type: 'num', width: '50px' }, // Form
                            { targets: [6], orderable: true, type: 'num', width: '80px' }, // Total
                            { targets: [7], orderable: true, type: 'num', width: '70px' }, // Points/£
                            { targets: [8], orderable: true, width: '80px' }, // Chance of Playing
                            { targets: [9, 10, 11, 12, 13, 14, 15, 16, 17], orderable: true, type: 'num', width: '45px' } // GW columns
                        ],
                        language: {
                            search: "Search players:",
                            lengthMenu: "Show _MENU_ players per page",
                            info: "Showing _START_ to _END_ of _TOTAL_ players"
                        },
                        autoWidth: false,
                        orderClasses: true, // Enable default order classes
                        pageLength: 25,
                        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
                        // Enable multi-column sorting for our custom implementation
                        orderMulti: true,
                        // Hide default DataTable controls since we have custom ones above
                        dom: 't<"bottom"i>'
                    });
                    
                    // Enhanced multi-column sorting functionality
                    var currentSortOrder = [];
                    
                    // Custom controls event handlers
                    $('#pageLength').on('change', function() {
                        var newLength = parseInt($(this).val());
                        table.page.len(newLength).draw();
                    });
                    
                    $('#searchPlayers').on('keyup', function() {
                        var searchTerm = $(this).val();
                        table.search(searchTerm).draw();
                    });
                    
                    // Function to update sort indicators and create sort pills
                    function updateSortIndicators() {
                        console.log('updateSortIndicators called with currentSortOrder:', JSON.stringify(currentSortOrder));
                        
                        // Remove all existing sort indicators and level numbers
                        $('#playersTable thead th').removeClass('sorting_asc sorting_desc').addClass('sorting');
                        $('.sort-level-number').remove();
                        
                        // Clear existing sort pills
                        $('#sortPills').empty();
                        
                        // Add sort indicators for current sort order and create pills
                        currentSortOrder.forEach(function(sort, index) {
                            var columnIndex = sort[0];
                            var direction = sort[1];
                            var header = $('#playersTable thead th').eq(columnIndex);
                            
                            console.log('Processing sort:', index, 'column:', columnIndex, 'direction:', direction);
                            
                            if (direction === 'asc') {
                                header.removeClass('sorting').addClass('sorting_asc');
                            } else {
                                header.removeClass('sorting').addClass('sorting_desc');
                            }
                            
                            // Add sort level number under the header
                            header.append('<div class="sort-level-number">' + (index + 1) + '</div>');
                            console.log('Added sort level number:', index + 1, 'to column:', columnIndex);
                            
                            // Create sort pill
                            var columnNames = ['Rank', 'Player Name', 'Pos', 'Team', 'Price', 'Form', 'Total (GW1-9)', 'Points/£', 'Chance of Playing', 'GW1', 'GW2', 'GW3', 'GW4', 'GW5', 'GW6', 'GW7', 'GW8', 'GW9'];
                            var columnName = columnNames[columnIndex];
                            var directionText = direction === 'asc' ? '↑' : '↓';
                            
                            var pillHtml = '<div class="sort-pill ' + direction + '" data-column="' + columnIndex + '" data-index="' + index + '">' +
                                '<span class="pill-text">' + columnName + ' ' + directionText + '</span>' +
                                '<button class="remove-btn" onclick="removeSortPill(' + columnIndex + ')">×</button>' +
                                '</div>';
                            
                            $('#sortPills').append(pillHtml);
                            console.log('Added pill for:', columnName, directionText);
                        });
                        
                        console.log('updateSortIndicators completed');
                    }
                    
                    // Remove the order.dt event listener to prevent conflicts with manual sorting
                    // We'll handle all sorting manually through our click handlers
                    
                    // Function to add a new sort level
                    window.addSortLevel = function(columnIndex, direction) {
                        console.log('Adding sort level:', columnIndex, direction);
                        console.log('Current sort order before:', JSON.stringify(currentSortOrder));
                        
                        // Always add this column as a new sort level
                        currentSortOrder.push([columnIndex, direction]);
                        
                        console.log('Current sort order after adding:', JSON.stringify(currentSortOrder));
                        
                        // Limit to 5 sort levels for performance
                        if (currentSortOrder.length > 5) {
                            currentSortOrder = currentSortOrder.slice(0, 5);
                            console.log('Limited to 5 levels:', JSON.stringify(currentSortOrder));
                        }
                        
                        // Apply the new sort order
                        table.order(currentSortOrder).draw();
                        
                        // Update visual indicators manually
                        updateSortIndicators();
                        updateSortOrderInfo();
                        
                        console.log('Visual indicators updated');
                    };
                    
                    // Function to remove a specific sort column
                    window.removeSortPill = function(columnIndex) {
                        currentSortOrder = currentSortOrder.filter(sort => sort[0] !== columnIndex);
                        table.order(currentSortOrder).draw();
                        
                        // Update visual indicators manually
                        updateSortIndicators();
                        updateSortOrderInfo();
                    };
                    
                    // Function to display current sort order
                    function updateSortOrderInfo() {
                        var sortInfo = '';
                        if (currentSortOrder.length > 0) {
                            var columnNames = ['Rank', 'Player Name', 'Pos', 'Team', 'Price', 'Form', 'Total (GW1-9)', 'Points/£', 'Chance of Playing', 'GW1', 'GW2', 'GW3', 'GW4', 'GW5', 'GW6', 'GW7', 'GW8', 'GW9'];
                            sortInfo = 'Sorting by: ';
                            currentSortOrder.forEach(function(sort, index) {
                                var columnName = columnNames[sort[0]];
                                var direction = sort[1] === 'asc' ? '↑' : '↓';
                                sortInfo += columnName + ' ' + direction;
                                if (index < currentSortOrder.length - 1) {
                                    sortInfo += ' → ';
                                }
                            });
                        }
                        $('#sortOrderInfo').text(sortInfo);
                    }
                    
                    // Initialize sort indicators with a delay to ensure DataTable is ready
                    setTimeout(function() {
                        console.log('Initializing sort indicators...');
                        updateSortIndicators();
                        updateSortOrderInfo();
                        
                        console.log('Initialization complete');
                    }, 1000); // Wait 1 second for DataTable to be fully ready
                    
                    // Clear sort button handler
                    $('#clearSort').on('click', function() {
                        currentSortOrder = [];
                        table.order([]).draw();
                        updateSortIndicators();
                        updateSortOrderInfo();
                    });
                    
                    // Test sort button handler
                    $('#testSort').on('click', function() {
                        console.log('Test sort button clicked');
                        alert('Test sort button working! Current sorts: ' + currentSortOrder.length);
                        
                        // Add a test sort
                        currentSortOrder.push([7, 'asc']); // Add Points/£ column
                        table.order(currentSortOrder).draw();
                        updateSortIndicators();
                        updateSortOrderInfo();
                        
                        console.log('Test sort applied:', JSON.stringify(currentSortOrder));
                    });
                    
                    // Save view functionality
                    var savedViews = JSON.parse(localStorage.getItem('fplSavedViews') || '{}');
                    
                    // Function to save current view
                    $('#saveView').on('click', function() {
                        var viewName = $('#viewName').val().trim();
                        if (!viewName) {
                            alert('Please enter a name for this view');
                            return;
                        }
                        
                        if (currentSortOrder.length === 0) {
                            alert('No sorting applied to save');
                            return;
                        }
                        
                        // Save the current sort order with the view name
                        savedViews[viewName] = {
                            sortOrder: currentSortOrder,
                            timestamp: new Date().toISOString()
                        };
                        
                        localStorage.setItem('fplSavedViews', JSON.stringify(savedViews));
                        
                        // Update the load view dropdown
                        updateLoadViewDropdown();
                        
                        // Clear the input and show success message
                        $('#viewName').val('');
                        alert('View "' + viewName + '" saved successfully!');
                    });
                    
                    // Function to load a saved view
                    $('#loadView').on('change', function() {
                        var selectedView = $(this).val();
                        if (!selectedView) return;
                        
                        var viewData = savedViews[selectedView];
                        if (viewData && viewData.sortOrder) {
                            currentSortOrder = viewData.sortOrder;
                            table.order(currentSortOrder).draw();
                            updateSortIndicators();
                            updateSortOrderInfo();
                            
                            // Reset dropdown
                            $(this).val('');
                        }
                    });
                    
                    // Function to update the load view dropdown
                    function updateLoadViewDropdown() {
                        var loadSelect = $('#loadView');
                        loadSelect.find('option:not(:first)').remove();
                        
                        Object.keys(savedViews).forEach(function(viewName) {
                            var viewData = savedViews[viewName];
                            var timestamp = new Date(viewData.timestamp).toLocaleDateString();
                            var sortInfo = viewData.sortOrder.map(function(sort, index) {
                                var columnNames = ['Rank', 'Player Name', 'Pos', 'Team', 'Price', 'Form', 'Total (GW1-9)', 'Points/£', 'Chance of Playing', 'GW1', 'GW2', 'GW3', 'GW4', 'GW5', 'GW6', 'GW7', 'GW8', 'GW9'];
                                var direction = sort[1] === 'asc' ? '↑' : '↓';
                                return columnNames[sort[0]] + ' ' + direction;
                            }).join(' → ');
                            
                            loadSelect.append($('<option></option>').val(viewName).text(viewName + ' (' + sortInfo + ') - ' + timestamp));
                        });
                    }
                    
                    // Initialize the load view dropdown
                    updateLoadViewDropdown();
                    
                    // Set default sort order
                    currentSortOrder = [[6, 'desc'], [7, 'desc']]; // Total (GW1-9) then by Points/£
                    table.order(currentSortOrder).draw();
                    updateSortIndicators();
                    updateSortOrderInfo();
                    
                    // Custom filtering function
                    function customFilter() {
                        table.draw();
                    }
                    
                    // Position filter
                    $('#positionFilter').on('change', function() {
                        var position = $(this).val();
                        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                            if (position === '') return true;
                            return data[2].includes(position);
                        });
                        customFilter();
                    });
                    
                    // Team filter
                    $('#teamFilter').on('change', function() {
                        var team = $(this).val();
                        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                            if (team === '') return true;
                            return data[3] === team;
                        });
                        customFilter();
                    });
                    
                    // Price filter
                    $('#priceFilter').on('input', function() {
                        var maxPrice = parseFloat($(this).val());
                        if (isNaN(maxPrice)) return;
                        
                        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                            var price = parseFloat(data[4].replace('£', '').replace('M', ''));
                            return price <= maxPrice;
                        });
                        customFilter();
                    });
                    
                    // Chance of playing filter
                    $('#chanceFilter').on('input', function() {
                        var minChance = parseInt($(this).val());
                        if (isNaN(minChance)) return;
                        
                        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                            var chanceText = data[8];
                            var chance = parseInt(chanceText.match(/\d+/)[0]);
                            return chance >= minChance;
                        });
                        customFilter();
                    });
                    
                    // Points/£ filter
                    $('#pointsPerPoundFilter').on('input', function() {
                        var minPointsPerPound = parseFloat($(this).val());
                        if (isNaN(minPointsPerPound)) return;
                        
                        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                            var pointsPerPound = parseFloat(data[7]);
                            return pointsPerPound >= minPointsPerPound;
                        });
                        customFilter();
                    });
                    
                    // Total Points filter
                    $('#totalPointsFilter').on('input', function() {
                        var minTotalPoints = parseFloat($(this).val());
                        if (isNaN(minTotalPoints)) return;
                        
                        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                            var totalPoints = parseFloat(data[6]);
                            return totalPoints >= minTotalPoints;
                        });
                        customFilter();
                    });
                    
                    // Form filter
                    $('#formFilter').on('input', function() {
                        var minForm = parseFloat($(this).val());
                        if (isNaN(minForm)) return;
                        
                        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                            var form = parseFloat(data[5]);
                            return form >= minForm;
                        });
                        customFilter();
                    });
                    
                    // Ownership filter
                    $('#ownershipFilter').on('input', function() {
                        var minOwnership = parseFloat($(this).val());
                        if (isNaN(minOwnership)) return;
                        
                        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                            // Extract ownership percentage from player data
                            var player = {{ players|tojson }}.find(p => p.name === data[1]);
                            if (player && player.ownership) {
                                var ownership = parseFloat(player.ownership.replace('%', ''));
                                return ownership >= minOwnership;
                            }
                            return true; // If no ownership data, don't filter out
                        });
                        customFilter();
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
                        updateFilterInfo();
                    });
                    
                    // Update filter info
                    function updateFilterInfo() {
                        var visibleRows = table.rows({search: 'applied'}).count();
                        var totalRows = table.rows().count();
                        $('#filterInfo').text('Showing ' + visibleRows + ' of ' + totalRows + ' players');
                    }
                    
                    // Initial filter info
                    updateFilterInfo();
                    
                    // Update filter info after filtering
                    table.on('draw', function() {
                        updateFilterInfo();
                    });
                });
            </script>
        </body>
        </html>
        """, players=players_data)
        
    except Exception as e:
        return f"Error generating players table: {str(e)}"

def optimize_squad_for_gw1_9():
    """Use the alternative strategy with budget-compliant squad and weekly transfers"""
    # This is the alternative strategy provided by the user
    # It's budget-compliant and shows realistic FPL management
    
    # Define the strategy data
    strategy_data = {
        1: {  # GW1
            "starting_xi": [
                {"name": "Sánchez", "position": "Goalkeeper", "team": "Chelsea", "price": 5.0, "points": 4.0, "captain": False},
                {"name": "Virgil", "position": "Defender", "team": "Liverpool", "price": 6.0, "points": 4.2, "captain": False},
                {"name": "Mepham", "position": "Defender", "team": "Bournemouth", "price": 4.0, "points": 3.0, "captain": False},
                {"name": "Muñoz", "position": "Defender", "team": "Crystal Palace", "price": 5.5, "points": 2.9, "captain": False},
                {"name": "Palmer", "position": "Midfielder", "team": "Chelsea", "price": 10.5, "points": 5.1, "captain": False},
                {"name": "Eze", "position": "Midfielder", "team": "Crystal Palace", "price": 7.5, "points": 4.1, "captain": False},
                {"name": "Mac Allister", "position": "Midfielder", "team": "Liverpool", "price": 6.5, "points": 4.0, "captain": False},
                {"name": "Rice", "position": "Midfielder", "team": "Arsenal", "price": 6.5, "points": 3.7, "captain": False},
                {"name": "Watkins", "position": "Forward", "team": "Aston Villa", "price": 9.0, "points": 10.4, "captain": True},
                {"name": "Wood", "position": "Forward", "team": "Nottingham Forest", "price": 7.5, "points": 4.8, "captain": False},
                {"name": "Evanilson", "position": "Forward", "team": "Manchester United", "price": 7.0, "points": 3.4, "captain": False}
            ],
            "bench": [
                {"name": "Petrović", "position": "Goalkeeper", "team": "Chelsea", "price": 4.5, "points": 3.4, "captain": False},
                {"name": "Lacroix", "position": "Defender", "team": "Wolves", "price": 5.0, "points": 2.8, "captain": False},
                {"name": "Richards", "position": "Defender", "team": "Nottingham Forest", "price": 4.5, "points": 2.6, "captain": False},
                {"name": "Tonali", "position": "Midfielder", "team": "Newcastle", "price": 5.5, "points": 3.2, "captain": False}
            ]
        },
        2: {  # GW2
            "starting_xi": [
                {"name": "Sánchez", "position": "Goalkeeper", "team": "Chelsea", "price": 5.0, "points": 3.7, "captain": False},
                {"name": "Muñoz", "position": "Defender", "team": "Crystal Palace", "price": 5.5, "points": 4.2, "captain": False},
                {"name": "Mepham", "position": "Defender", "team": "Bournemouth", "price": 4.0, "points": 3.5, "captain": False},
                {"name": "Virgil", "position": "Defender", "team": "Liverpool", "price": 6.0, "points": 3.2, "captain": False},
                {"name": "M.Salah", "position": "Midfielder", "team": "Liverpool", "price": 14.5, "points": 12.2, "captain": True},
                {"name": "Rice", "position": "Midfielder", "team": "Arsenal", "price": 6.5, "points": 5.0, "captain": False},
                {"name": "Eze", "position": "Midfielder", "team": "Crystal Palace", "price": 7.5, "points": 4.8, "captain": False},
                {"name": "Mac Allister", "position": "Midfielder", "team": "Liverpool", "price": 6.5, "points": 3.5, "captain": False},
                {"name": "Watkins", "position": "Forward", "team": "Aston Villa", "price": 9.0, "points": 4.6, "captain": False},
                {"name": "Evanilson", "position": "Forward", "team": "Manchester United", "price": 7.0, "points": 4.6, "captain": False},
                {"name": "Wood", "position": "Forward", "team": "Nottingham Forest", "price": 7.5, "points": 3.9, "captain": False}
            ],
            "bench": [
                {"name": "Petrović", "position": "Goalkeeper", "team": "Chelsea", "price": 4.5, "points": 3.9, "captain": False},
                {"name": "Lacroix", "position": "Defender", "team": "Wolves", "price": 5.0, "points": 3.6, "captain": False},
                {"name": "Richards", "position": "Defender", "team": "Nottingham Forest", "price": 4.5, "points": 3.5, "captain": False},
                {"name": "Palmer", "position": "Midfielder", "team": "Chelsea", "price": 10.5, "points": 4.9, "captain": False, "status": "OUT"},
                {"name": "Tonali", "position": "Midfielder", "team": "Newcastle", "price": 5.5, "points": 3.3, "captain": False}
            ],
            "transfers": {"in": ["M.Salah"], "out": ["Palmer"]}
        },
        3: {  # GW3
            "starting_xi": [
                {"name": "Sánchez", "position": "Goalkeeper", "team": "Chelsea", "price": 5.0, "points": 4.0, "captain": False},
                {"name": "Virgil", "position": "Defender", "team": "Liverpool", "price": 6.0, "points": 3.5, "captain": False},
                {"name": "Muñoz", "position": "Defender", "team": "Crystal Palace", "price": 5.5, "points": 3.2, "captain": False},
                {"name": "Mepham", "position": "Defender", "team": "Bournemouth", "price": 4.0, "points": 3.0, "captain": False},
                {"name": "M.Salah", "position": "Midfielder", "team": "Liverpool", "price": 14.5, "points": 11.2, "captain": True},
                {"name": "Eze", "position": "Midfielder", "team": "Crystal Palace", "price": 7.5, "points": 4.0, "captain": False},
                {"name": "Mac Allister", "position": "Midfielder", "team": "Liverpool", "price": 6.5, "points": 3.2, "captain": False},
                {"name": "Rice", "position": "Midfielder", "team": "Arsenal", "price": 6.5, "points": 3.1, "captain": False},
                {"name": "Wood", "position": "Forward", "team": "Nottingham Forest", "price": 7.5, "points": 5.2, "captain": False},
                {"name": "Watkins", "position": "Forward", "team": "Aston Villa", "price": 9.0, "points": 4.8, "captain": False},
                {"name": "Evanilson", "position": "Forward", "team": "Manchester United", "price": 7.0, "points": 3.9, "captain": False}
            ],
            "bench": [
                {"name": "Petrović", "position": "Goalkeeper", "team": "Chelsea", "price": 4.5, "points": 3.3, "captain": False},
                {"name": "Lacroix", "position": "Defender", "team": "Wolves", "price": 5.0, "points": 3.0, "captain": False},
                {"name": "Richards", "position": "Defender", "team": "Nottingham Forest", "price": 4.5, "points": 2.9, "captain": False},
                {"name": "Rogers", "position": "Midfielder", "team": "Aston Villa", "price": 7.0, "points": 4.2, "captain": False},
                {"name": "Tonali", "position": "Midfielder", "team": "Newcastle", "price": 5.5, "points": 3.7, "captain": False, "status": "OUT"}
            ],
            "transfers": {"in": ["Rogers"], "out": ["Tonali"]}
        },
        4: {  # GW4
            "starting_xi": [
                {"name": "Sánchez", "position": "Goalkeeper", "team": "Chelsea", "price": 5.0, "points": 3.5, "captain": False},
                {"name": "Muñoz", "position": "Defender", "team": "Crystal Palace", "price": 5.5, "points": 5.3, "captain": False},
                {"name": "Virgil", "position": "Defender", "team": "Liverpool", "price": 6.0, "points": 4.4, "captain": False},
                {"name": "Mepham", "position": "Defender", "team": "Bournemouth", "price": 4.0, "points": 3.5, "captain": False},
                {"name": "M.Salah", "position": "Midfielder", "team": "Liverpool", "price": 14.5, "points": 14.0, "captain": True},
                {"name": "Eze", "position": "Midfielder", "team": "Crystal Palace", "price": 7.5, "points": 5.8, "captain": False},
                {"name": "Rice", "position": "Midfielder", "team": "Arsenal", "price": 6.5, "points": 4.1, "captain": False},
                {"name": "Mac Allister", "position": "Midfielder", "team": "Liverpool", "price": 6.5, "points": 4.0, "captain": False},
                {"name": "Evanilson", "position": "Forward", "team": "Manchester United", "price": 7.0, "points": 4.2, "captain": False},
                {"name": "Watkins", "position": "Forward", "team": "Aston Villa", "price": 9.0, "points": 4.1, "captain": False},
                {"name": "Wood", "position": "Forward", "team": "Nottingham Forest", "price": 7.5, "points": 3.2, "captain": False}
            ],
            "bench": [
                {"name": "Petrović", "position": "Goalkeeper", "team": "Chelsea", "price": 4.5, "points": 4.0, "captain": False},
                {"name": "Lacroix", "position": "Defender", "team": "Wolves", "price": 5.0, "points": 4.8, "captain": False},
                {"name": "Richards", "position": "Defender", "team": "Nottingham Forest", "price": 4.5, "points": 4.5, "captain": False, "status": "OUT"},
                {"name": "Tosin", "position": "Defender", "team": "Chelsea", "price": 4.5, "points": 3.1, "captain": False},
                {"name": "Rogers", "position": "Midfielder", "team": "Aston Villa", "price": 7.0, "points": 3.7, "captain": False}
            ],
            "transfers": {"in": ["Tosin"], "out": ["Richards"]}
        },
        5: {  # GW5
            "starting_xi": [
                {"name": "Sánchez", "position": "Goalkeeper", "team": "Chelsea", "price": 5.0, "points": 3.7, "captain": False},
                {"name": "Virgil", "position": "Defender", "team": "Liverpool", "price": 6.0, "points": 4.6, "captain": False},
                {"name": "Milenković", "position": "Defender", "team": "Nottingham Forest", "price": 5.5, "points": 4.1, "captain": False},
                {"name": "Mepham", "position": "Defender", "team": "Bournemouth", "price": 4.0, "points": 2.9, "captain": False},
                {"name": "M.Salah", "position": "Midfielder", "team": "Liverpool", "price": 14.5, "points": 13.2, "captain": True},
                {"name": "Eze", "position": "Midfielder", "team": "Crystal Palace", "price": 7.5, "points": 4.4, "captain": False},
                {"name": "Mac Allister", "position": "Midfielder", "team": "Liverpool", "price": 6.5, "points": 3.9, "captain": False},
                {"name": "Rice", "position": "Midfielder", "team": "Arsenal", "price": 6.5, "points": 3.4, "captain": False},
                {"name": "Watkins", "position": "Forward", "team": "Aston Villa", "price": 9.0, "points": 5.7, "captain": False},
                {"name": "Wood", "position": "Forward", "team": "Nottingham Forest", "price": 7.5, "points": 4.8, "captain": False},
                {"name": "Evanilson", "position": "Forward", "team": "Manchester United", "price": 7.0, "points": 4.3, "captain": False}
            ],
            "bench": [
                {"name": "Petrović", "position": "Goalkeeper", "team": "Chelsea", "price": 4.5, "points": 3.5, "captain": False},
                {"name": "Muñoz", "position": "Defender", "team": "Crystal Palace", "price": 5.5, "points": 3.7, "captain": False, "status": "OUT"},
                {"name": "Lacroix", "position": "Defender", "team": "Wolves", "price": 5.0, "points": 3.4, "captain": False},
                {"name": "Tosin", "position": "Defender", "team": "Chelsea", "price": 4.5, "points": 2.9, "captain": False},
                {"name": "Rogers", "position": "Midfielder", "team": "Aston Villa", "price": 7.0, "points": 4.4, "captain": False}
            ],
            "transfers": {"in": ["Milenković"], "out": ["Muñoz"]}
        },
        6: {  # GW6
            "starting_xi": [
                {"name": "Martinez", "position": "Goalkeeper", "team": "Aston Villa", "price": 5.0, "points": 3.9, "captain": False},
                {"name": "Milenković", "position": "Defender", "team": "Nottingham Forest", "price": 5.5, "points": 4.7, "captain": False},
                {"name": "Virgil", "position": "Defender", "team": "Liverpool", "price": 6.0, "points": 3.7, "captain": False},
                {"name": "Mepham", "position": "Defender", "team": "Bournemouth", "price": 4.0, "points": 3.6, "captain": False},
                {"name": "M.Salah", "position": "Midfielder", "team": "Liverpool", "price": 14.5, "points": 5.7, "captain": False},
                {"name": "Eze", "position": "Midfielder", "team": "Crystal Palace", "price": 7.5, "points": 4.2, "captain": False},
                {"name": "Mac Allister", "position": "Midfielder", "team": "Liverpool", "price": 6.5, "points": 3.6, "captain": False},
                {"name": "Rice", "position": "Midfielder", "team": "Arsenal", "price": 6.5, "points": 3.5, "captain": False},
                {"name": "Wood", "position": "Forward", "team": "Nottingham Forest", "price": 7.5, "points": 11.6, "captain": True},
                {"name": "Watkins", "position": "Forward", "team": "Aston Villa", "price": 9.0, "points": 5.2, "captain": False},
                {"name": "Evanilson", "position": "Forward", "team": "Manchester United", "price": 7.0, "points": 4.7, "captain": False}
            ],
            "bench": [
                {"name": "Sánchez", "position": "Goalkeeper", "team": "Chelsea", "price": 5.0, "points": 3.9, "captain": False, "status": "OUT"},
                {"name": "Petrović", "position": "Goalkeeper", "team": "Chelsea", "price": 4.5, "points": 3.8, "captain": False},
                {"name": "Tosin", "position": "Defender", "team": "Chelsea", "price": 4.5, "points": 3.5, "captain": False},
                {"name": "Lacroix", "position": "Defender", "team": "Wolves", "price": 5.0, "points": 3.3, "captain": False},
                {"name": "Rogers", "position": "Midfielder", "team": "Aston Villa", "price": 7.0, "points": 4.2, "captain": False}
            ],
            "transfers": {"in": ["Martinez"], "out": ["Sánchez"]}
        },
        7: {  # GW7
            "starting_xi": [
                {"name": "Martinez", "position": "Goalkeeper", "team": "Aston Villa", "price": 5.0, "points": 4.4, "captain": False},
                {"name": "Muñoz", "position": "Defender", "team": "Crystal Palace", "price": 5.5, "points": 3.9, "captain": False},
                {"name": "Mepham", "position": "Defender", "team": "Bournemouth", "price": 4.0, "points": 3.4, "captain": False},
                {"name": "Virgil", "position": "Defender", "team": "Liverpool", "price": 6.0, "points": 3.3, "captain": False},
                {"name": "M.Salah", "position": "Midfielder", "team": "Liverpool", "price": 14.5, "points": 5.7, "captain": False},
                {"name": "Rice", "position": "Midfielder", "team": "Arsenal", "price": 6.5, "points": 4.1, "captain": False},
                {"name": "Eze", "position": "Midfielder", "team": "Crystal Palace", "price": 7.5, "points": 4.0, "captain": False},
                {"name": "Mac Allister", "position": "Midfielder", "team": "Liverpool", "price": 6.5, "points": 3.2, "captain": False},
                {"name": "Watkins", "position": "Forward", "team": "Aston Villa", "price": 9.0, "points": 13.2, "captain": True},
                {"name": "Evanilson", "position": "Forward", "team": "Manchester United", "price": 7.0, "points": 4.0, "captain": False},
                {"name": "Wood", "position": "Forward", "team": "Nottingham Forest", "price": 7.5, "points": 3.9, "captain": False}
            ],
            "bench": [
                {"name": "Petrović", "position": "Goalkeeper", "team": "Chelsea", "price": 4.5, "points": 3.8, "captain": False},
                {"name": "Lacroix", "position": "Defender", "team": "Wolves", "price": 5.0, "points": 3.9, "captain": False},
                {"name": "Tosin", "position": "Defender", "team": "Chelsea", "price": 4.5, "points": 2.7, "captain": False},
                {"name": "Milenković", "position": "Defender", "team": "Nottingham Forest", "price": 5.5, "points": 2.7, "captain": False, "status": "OUT"},
                {"name": "Rogers", "position": "Midfielder", "team": "Aston Villa", "price": 7.0, "points": 5.2, "captain": False}
            ],
            "transfers": {"in": ["Muñoz"], "out": ["Milenković"]}
        },
        8: {  # GW8
            "starting_xi": [
                {"name": "Martinez", "position": "Goalkeeper", "team": "Aston Villa", "price": 5.0, "points": 3.0, "captain": False},
                {"name": "Virgil", "position": "Defender", "team": "Liverpool", "price": 6.0, "points": 4.4, "captain": False},
                {"name": "Muñoz", "position": "Defender", "team": "Crystal Palace", "price": 5.5, "points": 4.3, "captain": False},
                {"name": "Mepham", "position": "Defender", "team": "Bournemouth", "price": 4.0, "points": 3.1, "captain": False},
                {"name": "M.Salah", "position": "Midfielder", "team": "Liverpool", "price": 14.5, "points": 14.8, "captain": True},
                {"name": "Eze", "position": "Midfielder", "team": "Crystal Palace", "price": 7.5, "points": 4.9, "captain": False},
                {"name": "Mac Allister", "position": "Midfielder", "team": "Liverpool", "price": 6.5, "points": 4.1, "captain": False},
                {"name": "Rice", "position": "Midfielder", "team": "Arsenal", "price": 6.5, "points": 3.6, "captain": False},
                {"name": "Wood", "position": "Forward", "team": "Nottingham Forest", "price": 7.5, "points": 4.6, "captain": False},
                {"name": "Watkins", "position": "Forward", "team": "Aston Villa", "price": 9.0, "points": 4.5, "captain": False},
                {"name": "Strand Larsen", "position": "Forward", "team": "Brighton", "price": 6.5, "points": 4.3, "captain": False}
            ],
            "bench": [
                {"name": "Petrović", "position": "Goalkeeper", "team": "Chelsea", "price": 4.5, "points": 3.9, "captain": False},
                {"name": "Lacroix", "position": "Defender", "team": "Wolves", "price": 5.0, "points": 3.7, "captain": False},
                {"name": "Tosin", "position": "Defender", "team": "Chelsea", "price": 4.5, "points": 2.7, "captain": False},
                {"name": "Rogers", "position": "Midfielder", "team": "Aston Villa", "price": 7.0, "points": 3.7, "captain": False},
                {"name": "Evanilson", "position": "Forward", "team": "Manchester United", "price": 7.0, "points": 3.6, "captain": False, "status": "OUT"}
            ],
            "transfers": {"in": ["Strand Larsen"], "out": ["Evanilson"]}
        },
        9: {  # GW9
            "starting_xi": [
                {"name": "Martinez", "position": "Goalkeeper", "team": "Aston Villa", "price": 5.0, "points": 3.6, "captain": False},
                {"name": "Cucurella", "position": "Defender", "team": "Chelsea", "price": 6.0, "points": 4.5, "captain": False},
                {"name": "Virgil", "position": "Defender", "team": "Liverpool", "price": 6.0, "points": 3.8, "captain": False},
                {"name": "Mepham", "position": "Defender", "team": "Bournemouth", "price": 4.0, "points": 3.3, "captain": False},
                {"name": "M.Salah", "position": "Midfielder", "team": "Liverpool", "price": 14.5, "points": 12.4, "captain": True},
                {"name": "Rice", "position": "Midfielder", "team": "Arsenal", "price": 6.5, "points": 4.0, "captain": False},
                {"name": "Mac Allister", "position": "Midfielder", "team": "Liverpool", "price": 6.5, "points": 3.7, "captain": False},
                {"name": "Eze", "position": "Midfielder", "team": "Crystal Palace", "price": 7.5, "points": 3.4, "captain": False},
                {"name": "Strand Larsen", "position": "Forward", "team": "Brighton", "price": 6.5, "points": 4.4, "captain": False},
                {"name": "Watkins", "position": "Forward", "team": "Aston Villa", "price": 9.0, "points": 4.1, "captain": False},
                {"name": "Wood", "position": "Forward", "team": "Nottingham Forest", "price": 7.5, "points": 4.0, "captain": False}
            ],
            "bench": [
                {"name": "Petrović", "position": "Goalkeeper", "team": "Chelsea", "price": 4.5, "points": 3.8, "captain": False},
                {"name": "Tosin", "position": "Defender", "team": "Chelsea", "price": 4.5, "points": 4.4, "captain": False},
                {"name": "Lacroix", "position": "Defender", "team": "Wolves", "price": 5.0, "points": 3.0, "captain": False},
                {"name": "Muñoz", "position": "Defender", "team": "Crystal Palace", "price": 5.5, "points": 2.7, "captain": False, "status": "OUT"},
                {"name": "Rogers", "position": "Midfielder", "team": "Aston Villa", "price": 7.0, "points": 3.3, "captain": False}
            ],
            "transfers": {"in": ["Cucurella"], "out": ["Muñoz"]}
        }
    }
    
    return strategy_data

def get_position_limit(position):
    """Get the maximum number of players allowed for a position"""
    limits = {
        "Goalkeeper": 2,
        "Defender": 5,
        "Midfielder": 5,
        "Forward": 3
    }
    return limits.get(position, 0)

def get_position_order(position):
    """Get position order for sorting (GK=1, DEF=2, MID=3, FWD=4)"""
    order = {
        "Goalkeeper": 1,
        "Defender": 2,
        "Midfielder": 3,
        "Forward": 4
    }
    return order.get(position, 5)

def get_optimal_team_for_gw(squad, gw_index):
    """Get optimal starting XI and bench for a specific gameweek"""
    if not squad:
        return [], []
    
    # Sort squad by expected points for this GW
    gw_squad = sorted(squad, key=lambda x: x["gw1_9_points"][gw_index], reverse=True)
    
    # Select starting XI (best 11 players)
    starting_xi = []
    bench = []
    
    # Must have at least 1 GK, 3 DEF, 3 MID, 1 FWD in starting XI
    min_requirements = {"Goalkeeper": 1, "Defender": 3, "Midfielder": 3, "Forward": 1}
    position_counts = {"Goalkeeper": 0, "Defender": 0, "Midfielder": 0, "Forward": 0}
    
    # First pass: add required minimum players
    for player in gw_squad:
        if len(starting_xi) >= 11:
            break
            
        if position_counts[player["position_name"]] < min_requirements[player["position_name"]]:
            starting_xi.append(player)
            position_counts[player["position_name"]] += 1
    
    # Second pass: fill remaining spots with best available players
    for player in gw_squad:
        if len(starting_xi) >= 11:
            break
            
        if player not in starting_xi:
            starting_xi.append(player)
    
    # Remaining players go to bench
    bench = [p for p in gw_squad if p not in starting_xi]
    
    return starting_xi, bench

def calculate_weekly_transfers(squad, gw_index):
    """Calculate transfers needed for optimal performance in this GW"""
    if gw_index == 0:  # GW1 - no transfers needed
        return [], []
    
    # Get current optimal team for this GW
    current_xi, current_bench = get_optimal_team_for_gw(squad, gw_index)
    
    # Get previous GW optimal team
    prev_xi, prev_bench = get_optimal_team_for_gw(squad, gw_index - 1)
    
    # Find players coming in and out of the STARTING XI only
    # (not bench-to-starting XI moves, which are just team selection changes)
    transfers_in = [p for p in current_xi if p not in prev_xi and p not in prev_bench]
    transfers_out = [p for p in prev_xi if p not in current_xi and p not in current_bench]
    
    return transfers_in, transfers_out

@app.route("/squad")
def squad_page():
    """Display the alternative FPL strategy for GW1-9"""
    try:
        # Get alternative strategy data
        strategy_data = optimize_squad_for_gw1_9()
        
        if not strategy_data:
            return "Error: Could not generate strategy data. Please try again later."
        
        # Process strategy data
        weekly_data = []
        total_points = 0
        total_transfers = 0
        
        for gw in range(1, 10):  # GW1-9
            gw_data = strategy_data[gw]
            starting_xi = gw_data["starting_xi"]
            bench = gw_data["bench"]
            
            # Calculate points for this GW
            gw_points = sum(player["points"] for player in starting_xi)
            total_points += gw_points
            
            # Get transfer information
            transfers_in = gw_data.get("transfers", {}).get("in", [])
            transfers_out = gw_data.get("transfers", {}).get("out", [])
            
            if gw > 1:  # GW1 has no transfers
                total_transfers += len(transfers_in)
            
            # Create transfer mapping (who replaced whom)
            transfer_mapping = {}
            if gw > 1 and len(transfers_in) > 0 and len(transfers_out) > 0:
                # Map transfers in to transfers out (assuming they correspond in order)
                for i, player_in in enumerate(transfers_in):
                    if i < len(transfers_out):
                        # Transfers are stored as strings (player names)
                        transfer_mapping[player_in] = transfers_out[i]
                    else:
                        transfer_mapping[player_in] = "Unknown player"
                

            
            # Calculate bench promotions/demotions
            bench_promotions = []
            bench_demotions = []
            if gw > 1:
                prev_gw_data = strategy_data[gw - 1]
                prev_xi = prev_gw_data["starting_xi"]
                prev_bench = prev_gw_data["bench"]
                
                # Find players promoted from bench to starting XI
                bench_promotions = [p for p in starting_xi if p["name"] in [bp["name"] for bp in prev_bench]]
                
                # Find players demoted from starting XI to bench
                bench_demotions = [p for p in bench if p["name"] in [px["name"] for px in prev_xi]]
            
            weekly_data.append({
                "gw": gw,
                "starting_xi": starting_xi,
                "bench": bench,
                "transfers_in": transfers_in,
                "transfers_out": transfers_out,
                "transfer_mapping": transfer_mapping,
                "bench_promotions": bench_promotions,
                "bench_demotions": bench_demotions,
                "points": gw_points,
                "formation": get_formation_from_strategy(starting_xi)
            })
        
        # Calculate total squad value (use GW1 as reference)
        gw1_data = strategy_data[1]
        all_players = gw1_data["starting_xi"] + gw1_data["bench"]
        total_value = sum(player["price"] for player in all_players)
        remaining_budget = 100.0 - total_value
        
        return render_template_string("""
        <html>
        <head>
            <title>FPL Optimal Squad - GW1-9</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
                }
                .gw-card {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 2rem;
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
                .transfer-in { background-color: #d4edda; border-left: 4px solid #28a745; }
                .transfer-out { background-color: #f8d7da; border-left: 4px solid #dc3545; }
                .no-transfer { background-color: #f8f9fa; border-left: 4px solid #6c757d; }
                .player-row { padding: 8px; margin: 2px 0; border-radius: 5px; }
                .formation-display { font-weight: bold; color: #2c3e50; }
                .points-display { font-size: 1.2em; font-weight: bold; color: #28a745; }
                .budget-info { font-size: 1.1em; color: #6c757d; }
                .nav-tabs .nav-link { color: #495057; }
                .nav-tabs .nav-link.active { color: #007bff; font-weight: 600; }
                .transfer-summary {
                    background: #f8f9fa;
                    padding: 8px;
                    border-radius: 5px;
                    margin-top: 5px;
                    border-left: 3px solid #28a745;
                }
                .transfer-summary small {
                    font-size: 0.85em;
                    line-height: 1.4;
                }
                .football-pitch {
                    background: linear-gradient(135deg, #2d5a27 0%, #4a7c59 50%, #2d5a27 100%);
                    border: 3px solid #ffffff;
                    border-radius: 15px;
                    padding: 20px;
                    margin: 20px 0;
                    position: relative;
                    min-height: 600px;
                }
                .pitch-lines {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    pointer-events: none;
                }
                .center-circle {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 100px;
                    height: 100px;
                    border: 2px solid rgba(255,255,255,0.3);
                    border-radius: 50%;
                }
                .center-line {
                    position: absolute;
                    top: 0;
                    left: 50%;
                    width: 2px;
                    height: 100%;
                    background: rgba(255,255,255,0.3);
                }
                .penalty-area {
                    position: absolute;
                    top: 10%;
                    left: 5%;
                    width: 20%;
                    height: 80%;
                    border: 2px solid rgba(255,255,255,0.2);
                    border-radius: 10px;
                }
                .penalty-area.right {
                    left: 75%;
                }
                .player-position {
                    position: absolute;
                    width: 120px;
                    text-align: center;
                }
                .player-card {
                    background: white;
                    border-radius: 10px;
                    padding: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    border: 2px solid transparent;
                    transition: all 0.3s ease;
                }
                .player-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 6px 12px rgba(0,0,0,0.3);
                }
                .player-card.transfer-in {
                    border-color: #28a745;
                    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                }
                .player-card.transfer-out {
                    border-color: #dc3545;
                    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                }
                .player-card.no-transfer {
                    border-color: #6c757d;
                }
                .player-name {
                    font-weight: bold;
                    font-size: 0.9em;
                    margin-bottom: 5px;
                    color: #2c3e50;
                }
                .player-team {
                    font-size: 0.8em;
                    color: #6c757d;
                    margin-bottom: 5px;
                }
                .player-stats {
                    font-size: 0.75em;
                    color: #495057;
                    line-height: 1.3;
                }
                .player-price {
                    font-weight: bold;
                    color: #28a745;
                }
                .player-points {
                    font-weight: bold;
                    color: #007bff;
                }
                .captain-badge {
                    position: absolute;
                    top: -5px;
                    right: -5px;
                    background: #ffc107;
                    color: #212529;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.7em;
                    font-weight: bold;
                }
                .formation-label {
                    position: absolute;
                    top: -15px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #2c3e50;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    font-weight: bold;
                }
                .substitutes-section {
                    background: #f8f9fa;
                    border-radius: 10px;
                    padding: 20px;
                    margin-top: 20px;
                }
                .substitute-player {
                    background: white;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 8px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    border-left: 4px solid #6c757d;
                }
                .substitute-player.transfer-in {
                    border-left-color: #28a745;
                }
                .substitute-player.transfer-out {
                    border-left-color: #dc3545;
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
                <h1 class="text-center mb-4">FPL Optimal Squad - GW1-9</h1>
                
                <!-- Summary Section -->
                <div class="summary-card">
                    <div class="row">
                        <div class="col-md-3">
                            <h4>Total Points (GW1-9)</h4>
                            <div class="points-display">{{ "%.1f"|format(total_points) }}</div>
                        </div>
                        <div class="col-md-3">
                            <h4>Total Transfers</h4>
                            <div class="points-display">{{ total_transfers }}</div>
                        </div>
                        <div class="col-md-3">
                            <h4>Squad Value</h4>
                            <div class="budget-info">£{{ "%.1f"|format(total_value) }}M</div>
                        </div>
                        <div class="col-md-3">
                            <h4>Remaining Budget</h4>
                            <div class="budget-info">£{{ "%.1f"|format(remaining_budget) }}M</div>
                        </div>
                    </div>
                </div>
                
                <!-- Weekly Tabs -->
                <ul class="nav nav-tabs" id="gwTabs" role="tablist">
                    {% for gw in weekly_data %}
                    <li class="nav-item" role="presentation">
                        <button class="nav-link {% if loop.first %}active{% endif %}" 
                                id="gw{{ gw.gw }}-tab" 
                                data-bs-toggle="tab" 
                                data-bs-target="#gw{{ gw.gw }}" 
                                type="button" 
                                role="tab">
                            GW{{ gw.gw }}
                        </button>
                    </li>
                    {% endfor %}
                </ul>
                
                <!-- Weekly Content -->
                <div class="tab-content" id="gwTabContent">
                    {% for gw in weekly_data %}
                    <div class="tab-pane fade {% if loop.first %}show active{% endif %}" 
                         id="gw{{ gw.gw }}" 
                         role="tabpanel">
                        
                        <div class="gw-card">
                            <div class="row mb-3">
                                <div class="col-md-4">
                                    <h3>GW{{ gw.gw }} - {{ gw.formation }}</h3>
                                </div>
                                <div class="col-md-4">
                                    <h4>Expected Points: <span class="points-display">{{ "%.1f"|format(gw.points) }}</span></h4>
                                </div>
                                <div class="col-md-4">
                                    <h4>Transfers: {{ gw.transfers_in|length }} IN, {{ gw.transfers_out|length }} OUT</h4>
                                    {% if gw.transfers_in|length > 0 %}
                                    <div class="transfer-summary">
                                        <small class="text-success">
                                            {% for player_in in gw.transfers_in %}
                                            <i class="fas fa-arrow-right"></i> {{ player_in }} → {{ gw.transfer_mapping.get(player_in, "Unknown player") }}<br>
                                            {% endfor %}
                                        </small>
                                    </div>
                                    {% endif %}
                                    {% if gw.bench_promotions|length > 0 or gw.bench_demotions|length > 0 %}
                                    <div>
                                        {% if gw.bench_promotions|length > 0 %}
                                        <small class="text-info">{{ gw.bench_promotions|length }} promoted from bench</small>
                                        {% endif %}
                                        {% if gw.bench_demotions|length > 0 %}
                                        {% if gw.bench_promotions|length > 0 %}<br>{% endif %}
                                        <small class="text-warning">{{ gw.bench_demotions|length }} demoted to bench</small>
                                        {% endif %}
                                    </div>
                                    {% endif %}
                                </div>
                            </div>
                            
                            <!-- Football Formation Layout -->
                            <div class="football-pitch">
                                <div class="formation-label">{{ gw.formation }}</div>
                                
                                <!-- Pitch Lines -->
                                <div class="pitch-lines">
                                    <div class="center-circle"></div>
                                    <div class="center-line"></div>
                                    <div class="penalty-area"></div>
                                    <div class="penalty-area right"></div>
                                </div>
                                
                                <!-- Starting XI positioned on pitch -->
                                {% set gk_players = gw.starting_xi | selectattr("position", "equalto", "Goalkeeper") | list %}
                                {% set def_players = gw.starting_xi | selectattr("position", "equalto", "Defender") | list %}
                                {% set mid_players = gw.starting_xi | selectattr("position", "equalto", "Midfielder") | list %}
                                {% set fwd_players = gw.starting_xi | selectattr("position", "equalto", "Forward") | list %}
                                
                                <!-- Goalkeeper -->
                                {% if gk_players %}
                                {% set gk = gk_players[0] %}
                                <div class="player-position" style="top: 85%; left: 50%; transform: translateX(-50%);">
                                    <div class="player-card {% if gk.name in gw.transfers_in %}transfer-in{% elif gk.name in gw.transfers_out %}transfer-out{% else %}no-transfer{% endif %}">
                                        {% if gk.captain %}
                                        <div class="captain-badge">C</div>
                                        {% endif %}
                                        <div class="player-name">{{ gk.name }}</div>
                                        <div class="player-team">{{ gk.team }}</div>
                                        <div class="player-stats">
                                            <div class="player-price">£{{ "%.1f"|format(gk.price) }}M</div>
                                            <div class="player-points">{{ "%.1f"|format(gk.points) }} pts</div>
                                        </div>
                                        {% if gk.name in gw.transfers_in %}
                                        <small class="text-success"><i class="fas fa-plus-circle"></i> IN ({{ gw.transfer_mapping.get(gk.name, "Unknown") }})</small>
                                        {% elif gk.name in gw.transfers_out %}
                                        <small class="text-danger"><i class="fas fa-minus-circle"></i> OUT</small>
                                        {% elif gk in gw.bench_promotions %}
                                        <small class="text-info"><i class="fas fa-arrow-up"></i> ↑</small>
                                        {% endif %}
                                    </div>
                                </div>
                                {% endif %}
                                
                                <!-- Defenders -->
                                {% for def in def_players %}
                                {% set top_pos = 70 - (loop.index0 * 12) %}
                                {% set left_pos = 20 + (loop.index0 * 15) %}
                                <div class="player-position" style="top: {{ top_pos }}%; left: {{ left_pos }}%;">
                                    <div class="player-card {% if def.name in gw.transfers_in %}transfer-in{% elif def.name in gw.transfers_out %}transfer-out{% else %}no-transfer{% endif %}">
                                        {% if def.captain %}
                                        <div class="captain-badge">C</div>
                                        {% endif %}
                                        <div class="player-name">{{ def.name }}</div>
                                        <div class="player-team">{{ def.team }}</div>
                                        <div class="player-stats">
                                            <div class="player-price">£{{ "%.1f"|format(def.price) }}M</div>
                                            <div class="player-points">{{ "%.1f"|format(def.points) }} pts</div>
                                        </div>
                                        {% if def.name in gw.transfers_in %}
                                        <small class="text-success"><i class="fas fa-plus-circle"></i> IN ({{ gw.transfer_mapping.get(def.name, "Unknown") }})</small>
                                        {% elif def.name in gw.transfers_out %}
                                        <small class="text-danger"><i class="fas fa-minus-circle"></i> OUT</small>
                                        {% elif def in gw.bench_promotions %}
                                        <small class="text-info"><i class="fas fa-arrow-up"></i> ↑</small>
                                        {% endif %}
                                    </div>
                                </div>
                                {% endfor %}
                                
                                <!-- Midfielders -->
                                {% for mid in mid_players %}
                                {% set top_pos = 45 - (loop.index0 * 10) %}
                                {% set left_pos = 25 + (loop.index0 * 12) %}
                                <div class="player-position" style="top: {{ top_pos }}%; left: {{ left_pos }}%;">
                                    <div class="player-card {% if mid.name in gw.transfers_in %}transfer-in{% elif mid.name in gw.transfers_out %}transfer-out{% else %}no-transfer{% endif %}">
                                        {% if mid.captain %}
                                        <div class="captain-badge">C</div>
                                        {% endif %}
                                        <div class="player-name">{{ mid.name }}</div>
                                        <div class="player-team">{{ mid.team }}</div>
                                        <div class="player-stats">
                                            <div class="player-price">£{{ "%.1f"|format(mid.price) }}M</div>
                                            <div class="player-points">{{ "%.1f"|format(mid.points) }} pts</div>
                                        </div>
                                        {% if mid.name in gw.transfers_in %}
                                        <small class="text-success"><i class="fas fa-plus-circle"></i> IN ({{ gw.transfer_mapping.get(mid.name, "Unknown") }})</small>
                                        {% elif mid.name in gw.transfers_out %}
                                        <small class="text-danger"><i class="fas fa-minus-circle"></i> OUT</small>
                                        {% elif mid in gw.bench_promotions %}
                                        <small class="text-info"><i class="fas fa-arrow-up"></i> ↑</small>
                                        {% endif %}
                                    </div>
                                </div>
                                {% endfor %}
                                
                                <!-- Forwards -->
                                {% for fwd in fwd_players %}
                                {% set top_pos = 20 - (loop.index0 * 8) %}
                                {% set left_pos = 35 + (loop.index0 * 20) %}
                                <div class="player-position" style="top: {{ top_pos }}%; left: {{ left_pos }}%;">
                                    <div class="player-card {% if fwd.name in gw.transfers_in %}transfer-in{% elif fwd.name in gw.transfers_out %}transfer-out{% else %}no-transfer{% endif %}">
                                        {% if fwd.captain %}
                                        <div class="captain-badge">C</div>
                                        {% endif %}
                                        <div class="player-name">{{ fwd.name }}</div>
                                        <div class="player-team">{{ fwd.team }}</div>
                                        <div class="player-stats">
                                            <div class="player-price">£{{ "%.1f"|format(fwd.price) }}M</div>
                                            <div class="player-points">{{ "%.1f"|format(fwd.points) }} pts</div>
                                        </div>
                                        {% if fwd.name in gw.transfers_in %}
                                        <small class="text-success"><i class="fas fa-plus-circle"></i> IN ({{ gw.transfer_mapping.get(fwd.name, "Unknown") }})</small>
                                        {% elif fwd.name in gw.transfers_out %}
                                        <small class="text-danger"><i class="fas fa-minus-circle"></i> OUT</small>
                                        {% elif fwd in gw.bench_promotions %}
                                        {% endif %}
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                            
                            <!-- Substitutes Section -->
                            <div class="substitutes-section">
                                <h4><i class="fas fa-users"></i> Substitutes</h4>
                                <div class="row">
                                    {% for player in gw.bench %}
                                    <div class="col-md-6 col-lg-3 mb-2">
                                        <div class="substitute-player {% if player.name in gw.transfers_in %}transfer-in{% elif player.name in gw.transfers_out %}transfer-out{% else %}no-transfer{% endif %}">
                                            <div class="d-flex justify-content-between align-items-start">
                                                <div>
                                                    <div class="player-name">{{ player.name }}</div>
                                                    <div class="player-team">{{ player.team }}</div>
                                                    <div class="player-stats">
                                                        <span class="player-price">£{{ "%.1f"|format(player.price) }}M</span> | 
                                                        <span class="player-points">{{ "%.1f"|format(player.points) }} pts</span>
                                                    </div>
                                                </div>
                                                <span class="position-badge 
                                                    {% if player.position == 'Goalkeeper' %}gk
                                                    {% elif player.position == 'Defender' %}def
                                                    {% elif player.position == 'Midfielder' %}mid
                                                    {% else %}fwd{% endif %}">
                                                    {{ player.position[:3] }}
                                                </span>
                                            </div>
                                            {% if player.name in gw.transfers_in %}
                                            <small class="text-success"><i class="fas fa-plus-circle"></i> TRANSFER IN ({{ gw.transfer_mapping.get(player.name, "Unknown") }})</small>
                                            {% elif player in gw.bench_demotions %}
                                            <small class="text-danger"><i class="fas fa-minus-circle"></i> Demoted to Bench</small>
                                            {% endif %}
                                        </div>
                                    </div>
                                    {% endfor %}
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """, weekly_data=weekly_data, total_points=total_points, 
             total_transfers=total_transfers, total_value=total_value, remaining_budget=remaining_budget)
        
    except Exception as e:
        return f"Error generating squad page: {str(e)}"

def get_formation_from_strategy(starting_xi):
    """Get formation string from starting XI in strategy format"""
    if not starting_xi:
        return "Unknown"
    
    gk_count = sum(1 for p in starting_xi if p["position"] == "Goalkeeper")
    def_count = sum(1 for p in starting_xi if p["position"] == "Defender")
    mid_count = sum(1 for p in starting_xi if p["position"] == "Midfielder")
    fwd_count = sum(1 for p in starting_xi if p["position"] == "Forward")
    
    return f"{def_count}-{mid_count}-{fwd_count}"

def get_formation(starting_xi):
    """Get formation string from starting XI"""
    if not starting_xi:
        return "Unknown"
    
    gk_count = sum(1 for p in starting_xi if p["position_name"] == "Goalkeeper")
    def_count = sum(1 for p in starting_xi if p["position_name"] == "Defender")
    mid_count = sum(1 for p in starting_xi if p["position_name"] == "Midfielder")
    fwd_count = sum(1 for p in starting_xi if p["position_name"] == "Forward")
    
    return f"{def_count}-{mid_count}-{fwd_count}"

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "FPL FDR service is running"}

if __name__ == "__main__":
    print("Starting FPL FDR application...")
    
    # Clear players table and add fresh data
    print("Clearing players table...")
    clear_players_table()
    print("Adding players to database...")
    add_players_via_sql()
    
    print("Building FDR data...")
    df = build_fdr_dataframe()
    if not df.empty:
        print(f"FDR data loaded successfully for {len(df)} teams")
        print("Available gameweeks: 1-38")
        print("Starting Flask server on http://127.0.0.1:8001")
    else:
        print("Warning: Could not load FDR data")
    
    app.run(host="127.0.0.1", port=8003, debug=True)
