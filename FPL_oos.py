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
                        "form": float(player.get("form", "0.0")),
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
            
            # Add the additional top 100 players with their specific expected points
            additional_players = get_additional_top_players()
            players_data.extend(additional_players)
            
            return players_data
        else:
            print(f"Error fetching players data: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching players data: {e}")
        return []

def get_additional_top_players():
    """Get the additional top 400 players with their specific expected points"""
    return [
        # Top 20 players (existing)
        {"id": 1001, "name": "M.Salah", "position_name": "Midfielder", "team": "Liverpool", "price": 14.5, "form": 0.0, "gw1_9_points": [6.7, 6.1, 5.6, 7.0, 6.6, 5.7, 5.7, 7.4, 6.2], "total_gw1_9": 57.0, "points_per_million": 3.93, "chance_of_playing_next_round": 100, "ownership": "24%"},
        {"id": 1002, "name": "Haaland", "position_name": "Forward", "team": "Man City", "price": 14.0, "form": 0.0, "gw1_9_points": [5.1, 6.3, 5.1, 5.8, 3.8, 6.6, 4.8, 5.1, 4.4], "total_gw1_9": 47.0, "points_per_million": 3.36, "chance_of_playing_next_round": 100},
        {"id": 1003, "name": "Palmer", "position_name": "Midfielder", "team": "Chelsea", "price": 10.5, "form": 0.0, "gw1_9_points": [5.1, 4.9, 5.5, 4.6, 4.3, 5.9, 4.4, 4.3, 6.7], "total_gw1_9": 45.8, "points_per_million": 4.36, "chance_of_playing_next_round": 100},
        {"id": 1004, "name": "Watkins", "position_name": "Forward", "team": "Aston Villa", "price": 9.0, "form": 0.0, "gw1_9_points": [5.2, 4.6, 4.8, 4.1, 5.7, 5.2, 6.6, 4.5, 4.1], "total_gw1_9": 44.9, "points_per_million": 4.99, "chance_of_playing_next_round": 100},
        {"id": 1005, "name": "Isak", "position_name": "Forward", "team": "Newcastle", "price": 10.5, "form": 0.0, "gw1_9_points": [4.4, 4.5, 5.8, 5.7, 4.7, 4.1, 5.4, 4.7, 5.4], "total_gw1_9": 44.6, "points_per_million": 4.25, "chance_of_playing_next_round": 100},
        {"id": 1006, "name": "Wood", "position_name": "Forward", "team": "Nott'm Forest", "price": 7.5, "form": 0.0, "gw1_9_points": [4.8, 3.9, 5.2, 3.2, 4.8, 5.8, 3.9, 4.6, 4.0], "total_gw1_9": 40.3, "points_per_million": 5.37, "chance_of_playing_next_round": 100},
        {"id": 1007, "name": "Eze", "position_name": "Midfielder", "team": "Crystal Palace", "price": 7.5, "form": 0.0, "gw1_9_points": [4.1, 4.8, 4.0, 5.8, 4.4, 4.2, 4.0, 4.9, 3.4], "total_gw1_9": 39.4, "points_per_million": 5.25, "chance_of_playing_next_round": 100},
        {"id": 1008, "name": "Saka", "position_name": "Midfielder", "team": "Arsenal", "price": 10.0, "form": 0.0, "gw1_9_points": [3.9, 5.9, 3.3, 4.8, 3.4, 3.7, 4.6, 3.6, 4.5], "total_gw1_9": 37.8, "points_per_million": 3.78, "chance_of_playing_next_round": 100},
        {"id": 1009, "name": "Evanilson", "position_name": "Forward", "team": "Fulham", "price": 7.0, "form": 0.0, "gw1_9_points": [3.4, 4.6, 3.9, 4.2, 4.3, 4.7, 4.0, 3.6, 4.2], "total_gw1_9": 36.9, "points_per_million": 5.27, "chance_of_playing_next_round": 100},
        {"id": 1010, "name": "Wissa", "position_name": "Forward", "team": "Brentford", "price": 7.5, "form": 0.0, "gw1_9_points": [3.8, 4.4, 4.7, 4.0, 3.7, 4.5, 3.8, 4.1, 3.7], "total_gw1_9": 36.6, "points_per_million": 4.88, "chance_of_playing_next_round": 100},
        {"id": 1011, "name": "B.Fernandes", "position_name": "Midfielder", "team": "Man Utd", "price": 9.0, "form": 0.0, "gw1_9_points": [3.4, 3.7, 4.9, 3.1, 4.1, 3.8, 5.3, 2.9, 4.1], "total_gw1_9": 35.4, "points_per_million": 3.93, "chance_of_playing_next_round": 100},
        {"id": 1012, "name": "Virgil", "position_name": "Defender", "team": "Liverpool", "price": 6.0, "form": 0.0, "gw1_9_points": [4.2, 3.2, 3.5, 4.4, 4.6, 3.7, 3.3, 4.4, 3.8], "total_gw1_9": 35.1, "points_per_million": 5.85, "chance_of_playing_next_round": 100},
        {"id": 1013, "name": "Gibbs-White", "position_name": "Midfielder", "team": "Nott'm Forest", "price": 7.5, "form": 0.0, "gw1_9_points": [4.3, 3.5, 4.4, 2.9, 4.2, 5.2, 3.4, 3.9, 3.4], "total_gw1_9": 35.1, "points_per_million": 4.68, "chance_of_playing_next_round": 100},
        {"id": 1014, "name": "Strand Larsen", "position_name": "Forward", "team": "Wolves", "price": 6.5, "form": 0.0, "gw1_9_points": [3.2, 3.5, 3.7, 3.4, 5.1, 3.5, 3.8, 4.3, 4.4], "total_gw1_9": 34.8, "points_per_million": 5.35, "chance_of_playing_next_round": 100},
        {"id": 1015, "name": "Rice", "position_name": "Midfielder", "team": "Arsenal", "price": 6.5, "form": 0.0, "gw1_9_points": [3.7, 5.0, 3.1, 4.1, 3.4, 3.5, 4.1, 3.6, 4.0], "total_gw1_9": 34.4, "points_per_million": 5.29, "chance_of_playing_next_round": 100},
        {"id": 1016, "name": "Rogers", "position_name": "Midfielder", "team": "Aston Villa", "price": 7.0, "form": 0.0, "gw1_9_points": [1.1, 4.0, 4.2, 3.7, 4.4, 4.2, 5.2, 3.7, 3.3], "total_gw1_9": 33.7, "points_per_million": 4.81, "chance_of_playing_next_round": 100},
        {"id": 1017, "name": "Sánchez", "position_name": "Goalkeeper", "team": "Chelsea", "price": 5.0, "form": 0.0, "gw1_9_points": [4.0, 3.7, 4.0, 3.5, 3.7, 3.9, 3.3, 3.3, 4.3], "total_gw1_9": 33.7, "points_per_million": 6.74, "chance_of_playing_next_round": 100},
        {"id": 1018, "name": "Welbeck", "position_name": "Forward", "team": "Brighton", "price": 6.5, "form": 0.0, "gw1_9_points": [4.1, 3.3, 3.6, 3.4, 4.1, 3.3, 4.0, 4.2, 3.5], "total_gw1_9": 33.5, "points_per_million": 5.15, "chance_of_playing_next_round": 100},
        {"id": 1019, "name": "Mac Allister", "position_name": "Midfielder", "team": "Liverpool", "price": 6.5, "form": 0.0, "gw1_9_points": [4.0, 3.5, 3.2, 4.0, 3.9, 3.6, 3.2, 4.1, 3.7], "total_gw1_9": 33.4, "points_per_million": 5.14, "chance_of_playing_next_round": 100},
        {"id": 1020, "name": "Petrović", "position_name": "Goalkeeper", "team": "Chelsea", "price": 4.5, "form": 0.0, "gw1_9_points": [3.4, 3.9, 3.3, 4.0, 3.5, 3.8, 3.8, 3.9, 3.8], "total_gw1_9": 33.3, "points_per_million": 7.40, "chance_of_playing_next_round": 100},
        
        # Next 100 players (11.9 - 6.0 range)
        {"id": 1021, "name": "Rodon", "position_name": "Defender", "team": "Leeds", "price": 4.0, "form": 0.0, "gw1_9_points": [2.8, 1.3, 1.8, 1.9, 1.8, 2.3, 1.8, 1.8, 2.3], "total_gw1_9": 11.9, "points_per_million": 2.98, "chance_of_playing_next_round": 100},
        {"id": 1022, "name": "Lucas Pires", "position_name": "Defender", "team": "Bournemouth", "price": 4.0, "form": 0.0, "gw1_9_points": [1.6, 3.0, 1.9, 1.6, 2.3, 1.4, 1.6, 2.3, 1.4], "total_gw1_9": 11.9, "points_per_million": 2.98, "chance_of_playing_next_round": 100},
        {"id": 1023, "name": "Livramento", "position_name": "Defender", "team": "Newcastle", "price": 5.0, "form": 0.0, "gw1_9_points": [1.7, 1.6, 2.5, 2.3, 1.9, 1.9, 1.7, 1.6, 2.5], "total_gw1_9": 11.8, "points_per_million": 2.36, "chance_of_playing_next_round": 100},
        {"id": 1024, "name": "Bogle", "position_name": "Defender", "team": "Sheffield Utd", "price": 4.5, "form": 0.0, "gw1_9_points": [2.8, 1.0, 1.9, 1.8, 1.9, 2.3, 2.8, 1.0, 1.9], "total_gw1_9": 11.8, "points_per_million": 2.62, "chance_of_playing_next_round": 100},
        {"id": 1025, "name": "Tavernier", "position_name": "Midfielder", "team": "Bournemouth", "price": 5.5, "form": 0.0, "gw1_9_points": [2.3, 2.0, 1.5, 1.9, 2.0, 2.0, 2.3, 2.0, 1.5], "total_gw1_9": 11.8, "points_per_million": 2.15, "chance_of_playing_next_round": 100},
        {"id": 1026, "name": "Munetsi", "position_name": "Midfielder", "team": "Luton", "price": 5.5, "form": 0.0, "gw1_9_points": [1.8, 1.7, 2.2, 1.6, 2.6, 1.8, 1.8, 1.7, 2.2], "total_gw1_9": 11.8, "points_per_million": 2.15, "chance_of_playing_next_round": 100},
        {"id": 1027, "name": "Wieffer", "position_name": "Midfielder", "team": "Brighton", "price": 5.0, "form": 0.0, "gw1_9_points": [2.3, 2.2, 1.7, 1.9, 2.0, 1.6, 2.3, 2.2, 1.7], "total_gw1_9": 11.8, "points_per_million": 2.36, "chance_of_playing_next_round": 100},
        {"id": 1028, "name": "Merino", "position_name": "Midfielder", "team": "Real Sociedad", "price": 6.0, "form": 0.0, "gw1_9_points": [1.8, 2.6, 1.6, 2.1, 1.7, 1.8, 1.8, 2.6, 1.6], "total_gw1_9": 11.7, "points_per_million": 1.95, "chance_of_playing_next_round": 100},
        {"id": 1029, "name": "Shaw", "position_name": "Defender", "team": "Man Utd", "price": 4.5, "form": 0.0, "gw1_9_points": [1.8, 2.0, 2.6, 1.5, 1.8, 1.7, 1.8, 2.0, 2.6], "total_gw1_9": 11.4, "points_per_million": 2.53, "chance_of_playing_next_round": 100},
        {"id": 1030, "name": "Trafford", "position_name": "Goalkeeper", "team": "Burnley", "price": 5.0, "form": 0.0, "gw1_9_points": [1.9, 1.5, 1.4, 2.7, 1.3, 2.6, 1.9, 1.5, 1.4], "total_gw1_9": 11.4, "points_per_million": 2.28, "chance_of_playing_next_round": 100},
        
        # Continue with more players...
        {"id": 1031, "name": "Areola", "position_name": "Goalkeeper", "team": "West Ham", "price": 4.5, "form": 0.0, "gw1_9_points": [1.4, 2.4, 1.9, 1.3, 2.1, 2.3, 1.4, 2.4, 1.9], "total_gw1_9": 11.3, "points_per_million": 2.51, "chance_of_playing_next_round": 100},
        {"id": 1032, "name": "Byram", "position_name": "Defender", "team": "Leeds", "price": 4.0, "form": 0.0, "gw1_9_points": [2.7, 1.1, 1.7, 1.7, 1.7, 2.2, 2.7, 1.1, 1.7], "total_gw1_9": 11.0, "points_per_million": 2.75, "chance_of_playing_next_round": 100},
        {"id": 1033, "name": "J.Ramsey", "position_name": "Midfielder", "team": "Aston Villa", "price": 5.5, "form": 0.0, "gw1_9_points": [2.0, 1.8, 1.8, 1.6, 1.9, 1.9, 2.0, 1.8, 1.8], "total_gw1_9": 11.0, "points_per_million": 2.00, "chance_of_playing_next_round": 100},
        {"id": 1034, "name": "Onyeka", "position_name": "Midfielder", "team": "Brentford", "price": 5.0, "form": 0.0, "gw1_9_points": [2.2, 1.6, 1.8, 1.8, 1.8, 1.8, 2.2, 1.6, 1.8], "total_gw1_9": 11.0, "points_per_million": 2.20, "chance_of_playing_next_round": 100},
        {"id": 1035, "name": "Maatsen", "position_name": "Defender", "team": "Chelsea", "price": 4.5, "form": 0.0, "gw1_9_points": [2.0, 1.6, 2.1, 1.6, 1.7, 1.9, 2.0, 1.6, 2.1], "total_gw1_9": 10.9, "points_per_million": 2.42, "chance_of_playing_next_round": 100},
        
        # Continue with more players (11.0 - 6.0 range)
        {"id": 1036, "name": "Kayode", "position_name": "Defender", "team": "Crystal Palace", "price": 4.5, "form": 0.0, "gw1_9_points": [1.5, 1.6, 1.8, 1.7, 1.6, 2.3, 1.5, 1.6, 1.8], "total_gw1_9": 10.5, "points_per_million": 2.33, "chance_of_playing_next_round": 100},
        {"id": 1037, "name": "Adingra", "position_name": "Midfielder", "team": "Brighton", "price": 5.5, "form": 0.0, "gw1_9_points": [1.8, 1.8, 1.9, 1.8, 1.7, 1.5, 1.8, 1.8, 1.9], "total_gw1_9": 10.5, "points_per_million": 1.91, "chance_of_playing_next_round": 100},
        {"id": 1038, "name": "Xhaka", "position_name": "Midfielder", "team": "Bayer Leverkusen", "price": 5.0, "form": 0.0, "gw1_9_points": [1.9, 1.9, 1.7, 1.6, 1.9, 1.4, 1.9, 1.9, 1.7], "total_gw1_9": 10.4, "points_per_million": 2.08, "chance_of_playing_next_round": 100},
        {"id": 1039, "name": "Kiwior", "position_name": "Defender", "team": "Arsenal", "price": 5.5, "form": 0.0, "gw1_9_points": [1.7, 2.2, 1.4, 1.9, 1.7, 1.5, 1.7, 2.2, 1.4], "total_gw1_9": 10.4, "points_per_million": 1.89, "chance_of_playing_next_round": 100},
        {"id": 1040, "name": "Garnacho", "position_name": "Midfielder", "team": "Man Utd", "price": 6.5, "form": 0.0, "gw1_9_points": [1.5, 1.7, 2.2, 1.4, 1.8, 1.8, 1.5, 1.7, 2.2], "total_gw1_9": 10.4, "points_per_million": 1.60, "chance_of_playing_next_round": 100},
        
        # Players with 10.4 - 6.0 range
        {"id": 1041, "name": "Adama", "position_name": "Midfielder", "team": "Fulham", "price": 5.5, "form": 0.0, "gw1_9_points": [1.8, 1.9, 1.3, 2.0, 1.9, 1.5, 1.8, 1.9, 1.3], "total_gw1_9": 10.4, "points_per_million": 1.89, "chance_of_playing_next_round": 100},
        {"id": 1042, "name": "Yates", "position_name": "Midfielder", "team": "Nott'm Forest", "price": 5.0, "form": 0.0, "gw1_9_points": [2.1, 1.6, 2.0, 1.4, 1.6, 1.7, 2.1, 1.6, 2.0], "total_gw1_9": 10.4, "points_per_million": 2.08, "chance_of_playing_next_round": 100},
        {"id": 1043, "name": "Isidor", "position_name": "Forward", "team": "Lille", "price": 5.5, "form": 0.0, "gw1_9_points": [1.9, 1.8, 1.8, 1.5, 1.7, 1.6, 1.9, 1.8, 1.8], "total_gw1_9": 10.3, "points_per_million": 1.87, "chance_of_playing_next_round": 100},
        {"id": 1044, "name": "Christie", "position_name": "Midfielder", "team": "Bournemouth", "price": 5.0, "form": 0.0, "gw1_9_points": [0.0, 0.9, 2.4, 2.4, 2.2, 2.4, 0.0, 0.9, 2.4], "total_gw1_9": 10.3, "points_per_million": 2.06, "chance_of_playing_next_round": 100},
        {"id": 1045, "name": "N.Gonzalez", "position_name": "Midfielder", "team": "Fiorentina", "price": 6.0, "form": 0.0, "gw1_9_points": [1.9, 2.1, 1.5, 1.7, 1.4, 1.8, 1.9, 2.1, 1.5], "total_gw1_9": 10.3, "points_per_million": 1.72, "chance_of_playing_next_round": 100},
        
        # Continue with more players...
        {"id": 1100, "name": "Nypan", "position_name": "Midfielder", "team": "Unknown", "price": 5.0, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        {"id": 1101, "name": "Harrison", "position_name": "Goalkeeper", "team": "Unknown", "price": 4.0, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        {"id": 1102, "name": "Mee", "position_name": "Goalkeeper", "team": "Unknown", "price": 4.0, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        {"id": 1103, "name": "Martinez", "position_name": "Defender", "team": "Unknown", "price": 5.0, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        {"id": 1104, "name": "D.Leon", "position_name": "Defender", "team": "Unknown", "price": 4.5, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        {"id": 1105, "name": "Rashford", "position_name": "Midfielder", "team": "Man Utd", "price": 7.0, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        {"id": 1106, "name": "Fitzgerald", "position_name": "Midfielder", "team": "Unknown", "price": 4.5, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        {"id": 1107, "name": "J.Fletcher", "position_name": "Midfielder", "team": "Unknown", "price": 4.5, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        {"id": 1108, "name": "Kone", "position_name": "Midfielder", "team": "Unknown", "price": 4.5, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        {"id": 1109, "name": "Moorhouse", "position_name": "Midfielder", "team": "Unknown", "price": 4.5, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        {"id": 1110, "name": "Wheatley", "position_name": "Forward", "team": "Unknown", "price": 4.5, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100},
        
        # Final players with 0.0 points
        {"id": 1200, "name": "Diakité", "position_name": "Defender", "team": "Unknown", "price": 4.5, "form": 0.0, "gw1_9_points": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "total_gw1_9": 0.0, "points_per_million": 0.0, "chance_of_playing_next_round": 100}
    ]

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
                                <strong>Sorting:</strong> Use ↑/↓ buttons above to add sort levels • Each button adds to existing sorts • Numbers show sort order • Remove individual sorts with X button on pills
                            </small>
                        </div>
                        <div class="mt-3">
                            <h6>Add Sort Levels:</h6>
                            <div class="row mb-2">
                                <div class="col-auto">
                                    <small class="text-muted">Rank:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(0, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(0, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">Name:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(1, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(1, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">Position:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(2, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(2, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">Team:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(3, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(3, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">Price:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(4, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(4, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">Form:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(5, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(5, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">Total:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(6, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(6, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">Points/£:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(7, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(7, 'desc')">↓</button>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-auto">
                                    <small class="text-muted">Chance:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(8, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(8, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">GW1:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(9, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(9, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">GW2:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(10, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(10, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">GW3:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(11, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(11, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">GW4:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(12, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(12, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">GW5:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(13, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(13, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">GW6:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(14, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(14, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">GW7:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(15, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(15, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">GW8:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(16, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(16, 'desc')">↓</button>
                                </div>
                                <div class="col-auto">
                                    <small class="text-muted">GW9:</small>
                                    <button class="btn btn-sm btn-outline-primary ms-1" onclick="addSortLevel(17, 'asc')">↑</button>
                                    <button class="btn btn-sm btn-outline-secondary ms-1" onclick="addSortLevel(17, 'desc')">↓</button>
                                </div>
                            </div>
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
                        order: [[6, 'desc'], [7, 'desc']], // Default sort: Total (GW1-9) then by Points/£
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
                        // Disable default multi-column sorting since we handle it manually
                        orderMulti: false
                    });
                    
                    // Enhanced multi-column sorting functionality
                    var currentSortOrder = [];
                    
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
                        
                        // Test: Add a simple sort to verify functionality
                        console.log('Testing with initial sort...');
                        currentSortOrder = [[6, 'desc']]; // Sort by Total (GW1-9) descending
                        table.order(currentSortOrder).draw();
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
    print("Building FDR data...")
    df = build_fdr_dataframe()
    if not df.empty:
        print(f"FDR data loaded successfully for {len(df)} teams")
        print("Available gameweeks: 1-38")
        print("Starting Flask server on http://127.0.0.1:8001")
    else:
        print("Warning: Could not load FDR data")
    
    app.run(host="127.0.0.1", port=8003, debug=True)
