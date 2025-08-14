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
        {"id": 1001, "name": "M.Salah", "position_name": "Midfielder", "team": "Liverpool", "price": 14.5, "form": 0.0, "gw1_9_points": [6.7, 6.1, 5.6, 7.0, 6.6, 5.7, 5.7, 7.4, 6.2], "total_gw1_9": 57.0, "points_per_million": 3.93, "chance_of_playing_next_round": 100},
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
                    
                    $('#playersTable').DataTable({
                        paging: true,
                        pageLength: 25,
                        ordering: true,
                        info: true,
                        searching: true,
                        order: [[6, 'desc'], [7, 'desc']], // Sort by Total (GW1-9) then by Points/£
                        scrollX: true,
                        columnDefs: [
                            { targets: [0], orderable: false, width: '40px' }, // Rank column not sortable
                            { targets: [1], orderable: true, width: '120px', type: 'string' }, // Name
                            { targets: [2], orderable: true, width: '60px', type: 'string' }, // Position
                            { targets: [3], orderable: true, width: '80px', type: 'string' }, // Team
                            { targets: [4], orderable: true, type: 'num', width: '70px' }, // Price
                            { targets: [5], orderable: true, type: 'num', width: '50px' }, // Form
                            { targets: [6], orderable: true, type: 'num', width: '80px' }, // Total
                            { targets: [7], orderable: true, type: 'num', width: '70px' }, // Points/£
                            { targets: [8], orderable: false, width: '80px' }, // Chance of Playing not sortable
                            { targets: [9, 10, 11, 12, 13, 14, 15, 16, 17], orderable: true, type: 'num', width: '45px' } // GW columns
                        ],
                        language: {
                            search: "Search players:",
                            lengthMenu: "Show _MENU_ players per page",
                            info: "Showing _START_ to _END_ of _TOTAL_ players"
                        },
                        autoWidth: false,
                        orderClasses: true,
                        pageLength: 25,
                        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]]
                    });
                });
            </script>
        </body>
        </html>
        """, players=players_data)
        
    except Exception as e:
        return f"Error generating players table: {str(e)}"

def optimize_squad_for_gw1_9():
    """Optimize squad for maximum points across GW1-9 while following FPL rules"""
    players_data = fetch_players_data()
    
    if not players_data:
        return None
    
    # Sort players by total GW1-9 points (descending)
    players_data.sort(key=lambda x: x["total_gw1_9"], reverse=True)
    
    # Initialize squad with best 15 players following FPL rules
    squad = []
    team_counts = {}
    position_counts = {"Goalkeeper": 0, "Defender": 0, "Midfielder": 0, "Forward": 0}
    
    for player in players_data:
        # Check if we can add this player
        if len(squad) >= 15:
            break
            
        # Check position limits
        if position_counts[player["position_name"]] >= get_position_limit(player["position_name"]):
            continue
            
        # Check team limits (max 3 per team)
        if team_counts.get(player["team"], 0) >= 3:
            continue
            
        # Add player to squad
        squad.append(player)
        position_counts[player["position_name"]] += 1
        team_counts[player["team"]] = team_counts.get(player["team"], 0) + 1
    
    # Sort squad by position for display
    squad.sort(key=lambda x: get_position_order(x["position_name"]))
    
    return squad

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
    """Display the optimal FPL squad for GW1-9"""
    try:
        # Get optimized squad
        squad = optimize_squad_for_gw1_9()
        
        if not squad:
            return "Error: Could not generate optimal squad. Please try again later."
        
        # Calculate weekly data
        weekly_data = []
        total_points = 0
        total_transfers = 0
        
        for gw in range(9):
            starting_xi, bench = get_optimal_team_for_gw(squad, gw)
            transfers_in, transfers_out = calculate_weekly_transfers(squad, gw)
            
            # Calculate bench promotions (players moved from bench to starting XI)
            # and bench demotions (players moved from starting XI to bench)
            bench_promotions = []
            bench_demotions = []
            if gw > 0:  # GW1 has no previous week
                prev_xi, prev_bench = get_optimal_team_for_gw(squad, gw - 1)
                bench_promotions = [p for p in starting_xi if p in prev_bench]
                bench_demotions = [p for p in bench if p in prev_xi]
            
            gw_points = sum(player["gw1_9_points"][gw] for player in starting_xi)
            total_points += gw_points
            
            weekly_data.append({
                "gw": gw + 1,
                "starting_xi": starting_xi,
                "bench": bench,
                "transfers_in": transfers_in,
                "transfers_out": transfers_out,
                "bench_promotions": bench_promotions,
                "bench_demotions": bench_demotions,
                "points": gw_points,
                "formation": get_formation(starting_xi)
            })
            
            if gw > 0:  # GW1 has no transfers
                total_transfers += len(transfers_in)
        
        # Calculate total squad value
        total_value = sum(player["price"] for player in squad)
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
                            
                            <!-- Starting XI -->
                            <h4>Starting XI</h4>
                            <div class="row">
                                {% for player in gw.starting_xi %}
                                <div class="col-md-6">
                                    <div class="player-row {% if player in gw.transfers_in %}transfer-in{% elif player in gw.transfers_out %}transfer-out{% else %}no-transfer{% endif %}">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <strong>{{ player.name }}</strong>
                                                <span class="position-badge 
                                                    {% if player.position_name == 'Goalkeeper' %}gk
                                                    {% elif player.position_name == 'Defender' %}def
                                                    {% elif player.position_name == 'Midfielder' %}mid
                                                    {% else %}fwd{% endif %}">
                                                    {{ player.position_name[:3] }}
                                                </span>
                                                <small class="text-muted">{{ player.team }}</small>
                                            </div>
                                            <div class="text-end">
                                                <div>£{{ "%.1f"|format(player.price) }}M</div>
                                                <div class="text-success">{{ "%.1f"|format(player.gw1_9_points[gw.gw-1]) }} pts</div>
                                            </div>
                                        </div>
                                        {% if player in gw.transfers_in %}
                                        <small class="text-success"><i class="fas fa-plus-circle"></i> TRANSFER IN (New to Squad)</small>
                                        {% elif player in gw.transfers_out %}
                                        <small class="text-danger"><i class="fas fa-minus-circle"></i> TRANSFER OUT (Removed from Squad)</small>
                                        {% elif player in gw.bench_promotions %}
                                        <small class="text-info"><i class="fas fa-arrow-up"></i> Promoted from Bench</small>
                                        {% endif %}
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                            
                            <!-- Bench -->
                            <h4 class="mt-3">Bench</h4>
                            <div class="row">
                                {% for player in gw.bench %}
                                <div class="col-md-6">
                                    <div class="player-row {% if player in gw.bench_demotions %}transfer-out{% else %}no-transfer{% endif %}">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <strong>{{ player.name }}</strong>
                                                <span class="position-badge 
                                                    {% if player.position_name == 'Goalkeeper' %}gk
                                                    {% elif player.position_name == 'Defender' %}def
                                                    {% elif player.position_name == 'Midfielder' %}mid
                                                    {% else %}fwd{% endif %}">
                                                    {{ player.position_name[:3] }}
                                                </span>
                                                <small class="text-muted">{{ player.team }}</small>
                                            </div>
                                            <div class="text-end">
                                                <div>£{{ "%.1f"|format(player.price) }}M</div>
                                                <div class="text-muted">{{ "%.1f"|format(player.gw1_9_points[gw.gw-1]) }} pts</div>
                                            </div>
                                        </div>
                                        {% if player in gw.bench_demotions %}
                                        <small class="text-warning"><i class="fas fa-arrow-down"></i> Demoted to Bench</small>
                                        {% endif %}
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """, squad=squad, weekly_data=weekly_data, total_points=total_points, 
             total_transfers=total_transfers, total_value=total_value, remaining_budget=remaining_budget)
        
    except Exception as e:
        return f"Error generating squad page: {str(e)}"

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
