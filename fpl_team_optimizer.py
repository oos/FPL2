import requests
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

class FPLTeamOptimizer:
    def __init__(self):
        self.players_data = self._load_players_data()
        self.teams_data = self._fetch_teams_data()
        
    def _load_players_data(self) -> pd.DataFrame:
        """Load the provided players data"""
        data = [
            ["M.Salah", "Midfielder", 14.5, 24, 57, 6.7, 6.1, 5.6, 7, 6.6, 5.7, 5.7, 7.4, 6.2],
            ["Haaland", "Forward", 14.0, 24, 47, 5.1, 6.3, 5.1, 5.8, 3.8, 6.6, 4.8, 5.1, 4.4],
            ["Palmer", "Midfielder", 10.5, 28, 45.8, 5.1, 4.9, 5.5, 4.6, 4.3, 5.9, 4.4, 4.3, 6.7],
            ["Watkins", "Forward", 9.0, 24, 44.9, 5.2, 4.6, 4.8, 4.1, 5.7, 5.2, 6.6, 4.5, 4.1],
            ["Isak", "Forward", 10.5, 24, 44.6, 4.4, 4.5, 5.8, 5.7, 4.7, 4.1, 5.4, 4.7, 5.4],
            ["Wood", "Forward", 7.5, 25, 40.3, 4.8, 3.9, 5.2, 3.2, 4.8, 5.8, 3.9, 4.6, 4],
            ["Eze", "Midfielder", 7.5, 26, 39.4, 4.1, 4.8, 4, 5.8, 4.4, 4.2, 4, 4.9, 3.4],
            ["Saka", "Midfielder", 10.0, 29, 37.8, 3.9, 5.9, 3.3, 4.8, 3.4, 3.7, 4.6, 3.6, 4.5],
            ["Evanilson", "Forward", 7.0, 24, 36.9, 3.4, 4.6, 3.9, 4.2, 4.3, 4.7, 4, 3.6, 4.2],
            ["Wissa", "Forward", 7.5, 26, 36.6, 3.8, 4.4, 4.7, 4, 3.7, 4.5, 3.8, 4.1, 3.7],
            ["B.Fernandes", "Midfielder", 9.0, 29, 35.4, 3.4, 3.7, 4.9, 3.1, 4.1, 3.8, 5.3, 2.9, 4.1],
            ["Virgil", "Defender", 6.0, 24, 35.1, 4.2, 3.2, 3.5, 4.4, 4.6, 3.7, 3.3, 4.4, 3.8],
            ["Gibbs-White", "Midfielder", 7.5, 25, 35.1, 4.3, 3.5, 4.4, 2.9, 4.2, 5.2, 3.4, 3.9, 3.4],
            ["Strand Larsen", "Forward", 6.5, 25, 34.8, 3.2, 3.5, 3.7, 3.4, 5.1, 3.5, 3.8, 4.3, 4.4],
            ["Rice", "Midfielder", 6.5, 23, 34.4, 3.7, 5, 3.1, 4.1, 3.4, 3.5, 4.1, 3.6, 4],
            ["Rogers", "Midfielder", 7.0, 28, 33.7, 1.1, 4, 4.2, 3.7, 4.4, 4.2, 5.2, 3.7, 3.3],
            ["Sánchez", "Goalkeeper", 5.0, 22, 33.7, 4, 3.7, 4, 3.5, 3.7, 3.9, 3.3, 3.3, 4.3],
            ["Welbeck", "Forward", 6.5, 26, 33.5, 4.1, 3.3, 3.6, 3.4, 4.1, 3.3, 4, 4.2, 3.5],
            ["Mac Allister", "Midfielder", 6.5, 23, 33.4, 4, 3.5, 3.2, 4, 3.9, 3.6, 3.2, 4.1, 3.7],
            ["Petrović", "Goalkeeper", 4.5, 21, 33.3, 3.4, 3.9, 3.3, 4, 3.5, 3.8, 3.8, 3.9, 3.8],
            ["Muñoz", "Defender", 5.5, 28, 33.3, 2.9, 4.2, 3.2, 5.3, 3.7, 3.3, 3.9, 4.3, 2.7],
            ["Bruno G.", "Midfielder", 6.5, 23, 33, 3.4, 3.5, 4.1, 4.1, 3.4, 3.1, 3.9, 3.5, 3.9],
            ["Schade", "Midfielder", 7.0, 27, 33, 1.6, 4.2, 4.5, 4, 3.5, 4.4, 3.5, 3.8, 3.5],
            ["Saliba", "Defender", 6.0, 25, 32.8, 3.4, 4.7, 2.8, 3.9, 3.5, 3.1, 4.2, 3.5, 3.9],
            ["Leno", "Goalkeeper", 5.0, 23, 32.7, 3.8, 4.1, 3.5, 4.2, 3.8, 3.2, 3.9, 3.3, 3],
            ["Murillo", "Defender", 5.5, 24, 32.6, 3.9, 3.4, 3.9, 3, 4, 4.6, 2.8, 3.4, 3.5],
            ["Raya", "Goalkeeper", 5.5, 24, 32.5, 3.3, 4.3, 3.3, 3.7, 3.5, 3.1, 4.3, 3.3, 3.8],
            ["Milenković", "Defender", 5.5, 27, 32.5, 4, 3.2, 4.1, 2.7, 4.1, 4.7, 2.7, 3.5, 3.4],
            ["Branthwaite", "Defender", 5.5, 24, 32, 4, 3.8, 3.5, 3.5, 3, 3.9, 3.7, 3, 3.5],
            ["Martinelli", "Midfielder", 7.0, 32, 31.7, 3.1, 4.6, 2.9, 3.8, 3.2, 3, 4, 3.4, 3.7],
            ["Sarr", "Midfielder", 6.5, 27, 31.6, 3.1, 3.9, 3.1, 4.7, 3.7, 3.3, 3.3, 3.7, 2.8],
            ["Lacroix", "Defender", 5.0, 24, 31.5, 2.8, 3.6, 3, 4.8, 3.4, 3.3, 3.9, 3.7, 3],
            ["Tarkowski", "Defender", 5.5, 26, 31.2, 3.9, 3.6, 3.5, 3.6, 3, 3.6, 3.8, 2.7, 3.4],
            ["Mykolenko", "Defender", 5.0, 24, 31, 4, 3.6, 3.4, 3.5, 2.6, 3.9, 3.8, 2.7, 3.5],
            ["McNeil", "Midfielder", 6.0, 28, 30.7, 4, 3.6, 3.3, 3.7, 2.7, 3.6, 3.5, 2.7, 3.6],
            ["Tonali", "Midfielder", 5.5, 23, 30.7, 3.2, 3.3, 3.7, 3.8, 3.3, 3, 3.6, 3.2, 3.5],
            ["Johnson", "Midfielder", 7.0, 35, 30.6, 4.7, 2.5, 3.3, 3.1, 3.1, 3.4, 3.9, 3.6, 3],
            ["Konaté", "Defender", 5.5, 25, 30.6, 3.8, 2.8, 3.1, 3.8, 4.2, 3.1, 2.6, 3.9, 3.2],
            ["José Sá", "Goalkeeper", 4.5, 23, 30.3, 3.5, 3.6, 3.9, 1.9, 3.3, 3.1, 3.6, 3.5, 4],
            ["Cucurella", "Defender", 6.0, 28, 30.3, 3.7, 3.3, 3.6, 3.1, 3, 3.6, 2.7, 2.8, 4.5],
            ["Henderson", "Goalkeeper", 5.0, 23, 30.2, 3.2, 3.4, 3, 4.2, 3.1, 3.3, 3.1, 3.8, 3],
            ["Verbruggen", "Goalkeeper", 4.5, 23, 30.1, 3.6, 3.8, 3.2, 3.5, 3.4, 2.8, 3.3, 3.1, 3.4],
            ["Richards", "Defender", 4.5, 25, 30, 2.6, 3.5, 2.9, 4.5, 3.3, 3.1, 3.7, 3.7, 2.8],
            ["A.Becker", "Goalkeeper", 5.5, 25, 30, 3.9, 2.7, 2.8, 3.6, 4, 3.4, 2.2, 4.1, 3.4],
            ["Beto", "Forward", 5.5, 24, 29.9, 3.8, 3.4, 3.2, 3.5, 2.8, 3.6, 3.4, 2.7, 3.6],
            ["Vicario", "Goalkeeper", 5.0, 24, 29.7, 3.9, 2.9, 3.4, 3, 3.2, 3.3, 3.5, 3.2, 3.4],
            ["Rúben", "Defender", 5.5, 26, 29.7, 3.4, 3.5, 3.1, 3.7, 2.5, 4, 3, 3.7, 2.8],
            ["Mitchell", "Defender", 5.0, 27, 29.7, 2.7, 3.6, 2.9, 4.6, 3.2, 2.9, 3.5, 3.8, 2.4],
            ["Guéhi", "Defender", 4.5, 27, 29.7, 2.6, 3.5, 2.8, 4.6, 3.2, 3, 3.6, 3.7, 2.7],
            ["Ndiaye", "Midfielder", 6.5, 28, 29.6, 3.8, 3.3, 3.5, 3.5, 2.6, 3.5, 3.5, 2.5, 3.5],
            ["Tosin", "Defender", 4.5, 27, 29.6, 3.5, 3.3, 3.6, 3.1, 2.9, 3.5, 2.7, 2.7, 4.4],
            ["Collins", "Defender", 5.0, 26, 29.5, 3, 3.2, 4, 3.1, 3.2, 3.6, 3.1, 3.3, 3],
            ["Iwobi", "Midfielder", 6.5, 30, 29.5, 3, 3.5, 2.9, 4.3, 3.9, 3.1, 3.1, 2.8, 3],
            ["Wirtz", "Midfielder", 8.5, 29, 29.4, 3.6, 3.1, 2.8, 3.5, 3.4, 3.1, 2.9, 3.6, 3.4],
            ["Matheus N.", "Defender", 5.5, 30, 29.4, 3.3, 3.7, 2.9, 3.8, 2.4, 4.2, 2.9, 3.7, 2.5],
            ["Martinez", "Goalkeeper", 5.0, 22, 29.3, 0, 3.2, 3.9, 3.8, 3.5, 3.9, 4.4, 3, 3.6],
            ["Mepham", "Defender", 4.0, 25, 29.3, 3, 3.5, 3, 3.5, 2.9, 3.6, 3.4, 3.1, 3.3],
            ["Chalobah", "Defender", 5.0, 26, 29.3, 3.5, 3.2, 3.5, 3.1, 2.9, 3.4, 2.7, 2.7, 4.3],
            ["Neto", "Midfielder", 7.0, 29, 29.2, 3.5, 3, 3.3, 3, 3.1, 3.4, 2.6, 2.9, 4.3],
            ["Frimpong", "Defender", 6.0, 27, 29, 3.9, 2.7, 2.7, 3.8, 4, 2.8, 2.3, 3.7, 3.1],
            ["Nørgaard", "Midfielder", 5.5, 24, 29, 2.8, 3.7, 2.9, 3.5, 2.9, 3.1, 3.7, 3, 3.4],
            ["Anderson", "Midfielder", 5.5, 21, 29, 3.6, 3.1, 3.6, 2.6, 3.4, 3.5, 2.8, 3.2, 3.1],
            ["Enzo", "Midfielder", 6.5, 28, 29, 3.6, 3.2, 3.3, 2.9, 2.8, 3.3, 2.9, 2.8, 4.1],
            ["Andersen", "Defender", 4.5, 26, 28.9, 3.3, 3.6, 2.7, 4, 3.7, 2.7, 3.4, 3, 2.4],
            ["Gana", "Midfielder", 5.5, 21, 28.6, 3.3, 3.4, 3.1, 3.3, 2.8, 3.5, 3.1, 2.6, 3.4],
            ["Mateta", "Forward", 7.5, 27, 28.4, 3, 3.5, 3.1, 4, 3.4, 3.2, 2.9, 3, 2.2],
            ["Lewis-Skelly", "Defender", 5.5, 29, 28.4, 2.9, 4, 2.2, 3.5, 2.9, 2.7, 3.7, 2.9, 3.5],
            ["Hudson-Odoi", "Midfielder", 6.0, 28, 28.2, 3.5, 2.9, 3.7, 2.4, 3.4, 3.9, 2.7, 3.1, 2.7],
            ["Trippier", "Defender", 5.0, 29, 28.1, 2.7, 2.6, 3.8, 3.6, 2.7, 2.7, 3.6, 2.7, 3.6],
            ["Konsa", "Defender", 4.5, 28, 28, 2.9, 2.6, 3.5, 3.1, 3.3, 3.4, 4, 2.3, 2.9],
            ["Raúl", "Forward", 6.5, 34, 27.9, 3, 3.5, 2.6, 4.1, 3.4, 2.8, 3, 2.7, 2.8],
            ["Gomes", "Midfielder", 5.5, 21, 27.6, 2.7, 3, 3.2, 2.8, 3.4, 3, 3, 2.9, 3.5],
            ["Onana", "Goalkeeper", 5.0, 25, 27.6, 0.9, 3.1, 3.9, 3.1, 3.6, 3, 3.1, 2.9, 3.8],
            ["Kilman", "Defender", 4.5, 27, 27.5, 3.7, 2.6, 2.6, 3, 3, 3.5, 2.6, 3.3, 3.3],
            ["Neil", "Midfielder", 5.0, 20, 27.5, 3.2, 3.2, 3.2, 2.9, 3.1, 2.9, 3, 3.2, 2.7],
            ["Semenyo", "Midfielder", 7.0, 35, 27.5, 2.5, 3.3, 3.1, 3.2, 3.1, 3.4, 2.8, 2.8, 3.2],
            ["Caicedo", "Midfielder", 5.5, 24, 27.4, 3.4, 3.1, 3.2, 2.9, 2.9, 3.1, 2.9, 2.7, 3.2],
            ["Patterson", "Goalkeeper", 4.5, 26, 27.3, 3.3, 3.4, 3, 3.1, 3, 2.5, 3.1, 3, 2.9],
            ["O.Dango", "Midfielder", 6.0, 25, 27.3, 2.6, 3.1, 3.1, 3, 3.2, 3.4, 3.2, 2.7, 3],
            ["Mbeumo", "Midfielder", 8.0, 27, 27.1, 2.6, 2.9, 3.8, 2.5, 3, 2.9, 3.8, 2.5, 3.2],
            ["Cash", "Defender", 4.5, 29, 27.1, 2.8, 2.6, 3.4, 3, 2.9, 3.3, 4.3, 2.2, 2.7],
            ["Barnes", "Midfielder", 6.5, 38, 27, 3, 3, 3.5, 3.5, 2.9, 2.4, 3.3, 2.7, 2.8],
            ["Adams", "Midfielder", 5.0, 21, 27, 2.9, 3.3, 3, 3.1, 2.9, 3, 3, 2.8, 3],
            ["Kluivert", "Midfielder", 7.0, 37, 27, 0, 1.1, 3.6, 4, 3.6, 4, 3.8, 3.1, 3.8],
            ["Aina", "Defender", 5.0, 27, 27, 3.4, 2.7, 3.5, 2, 3.6, 3.8, 2.1, 3, 2.7],
            ["Gabriel", "Defender", 6.0, 33, 27, 3.2, 3.7, 2.2, 3.1, 2.8, 2.6, 3.2, 2.8, 3.3],
            ["Kelleher", "Goalkeeper", 4.5, 25, 26.9, 2.3, 3.2, 2.3, 3.4, 3, 3.8, 2.4, 3.2, 3.1],
            ["L.Paquetá", "Midfielder", 6.0, 28, 26.8, 3.1, 3, 2.8, 3.1, 3, 2.9, 2.3, 3.1, 3.4],
            ["Wilson", "Forward", 6.0, 25, 26.7, 3.2, 2.9, 2.8, 3.3, 3.1, 2.8, 2.3, 3.2, 3.2],
            ["Toti", "Defender", 4.5, 29, 26.5, 2.6, 2.8, 3.6, 2.1, 3.8, 2.3, 2.7, 3.2, 3.5],
            ["Henderson", "Midfielder", 5.0, 21, 26.5, 2.8, 3.1, 3.2, 2.9, 2.8, 3.2, 2.8, 2.9, 2.7],
            ["João Pedro", "Forward", 7.5, 26, 26.4, 3.1, 2.9, 3, 2.7, 2.6, 3.1, 2.6, 2.7, 3.6],
            ["Potts", "Midfielder", 4.5, 21, 26.2, 3.1, 2.9, 2.7, 3.2, 3, 2.8, 2.4, 3.1, 3.1],
            ["Ekitiké", "Forward", 8.5, 32, 26.2, 3.1, 2.6, 2.4, 3.3, 2.8, 3.1, 2.6, 2.9, 3.4],
            ["N.Williams", "Defender", 5.0, 29, 26.2, 3.3, 2.6, 3.4, 2.1, 3.4, 3.7, 2, 2.9, 2.7],
            ["Gündoğan", "Midfielder", 6.5, 33, 26.2, 3.2, 3.4, 2.9, 3, 2.2, 3.7, 2.6, 2.6, 2.5],
            ["Joelinton", "Midfielder", 6.0, 25, 26, 2.6, 2.9, 3.4, 3.2, 2.7, 2.5, 3.1, 2.6, 3.1],
            ["Ward-Prowse", "Midfielder", 6.0, 23, 26, 3.1, 2.9, 2.7, 3.1, 3, 2.8, 2.3, 3.1, 3.1],
            ["Smith Rowe", "Midfielder", 6.0, 34, 26, 2.7, 3.1, 2.4, 3.8, 3.3, 2.5, 2.8, 2.7, 2.6],
            ["Senesi", "Defender", 4.5, 31, 26, 2.3, 3.3, 2.5, 3.2, 2.6, 3.2, 3.1, 2.7, 3]
        ]
        
        columns = ["Name", "Position", "Price", "Uncertainty", "Overall", "GW 1", "GW 2", "GW 3", "GW 4", "GW 5", "GW 6", "GW 7", "GW 8", "GW 9"]
        df = pd.DataFrame(data, columns=columns)
        return df
    
    def _fetch_teams_data(self) -> Dict:
        """Fetch team data from FPL API"""
        try:
            response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
            if response.status_code == 200:
                data = response.json()
                teams = {t["id"]: t["name"] for t in data["teams"]}
                return teams
            else:
                print(f"Failed to fetch teams data: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Error fetching teams data: {e}")
            return {}
    
    def get_optimal_team(self, budget: float = 100.0) -> Dict:
        """Get optimal FPL team within budget constraints following official FPL rules"""
        # Official FPL squad composition rules
        # Must have exactly: 2 GKs, 5 DEFs, 5 MIDs, 3 FWDs = 15 players total
        formation_constraints = {
            "Goalkeeper": (2, 2),      # Must have exactly 2 GKs
            "Defender": (5, 5),         # Must have exactly 5 DEFs
            "Midfielder": (5, 5),       # Must have exactly 5 MIDs
            "Forward": (3, 3)           # Must have exactly 3 FWDs
        }
        
        # Calculate total expected points for first 9 weeks
        gw_columns = [f"GW {i}" for i in range(1, 10)]
        self.players_data["Total_GW1_9"] = self.players_data[gw_columns].sum(axis=1)
        
        # Sort by total expected points (descending)
        sorted_players = self.players_data.sort_values("Total_GW1_9", ascending=False)
        
        selected_players = []
        remaining_budget = budget
        position_counts = {pos: 0 for pos in formation_constraints.keys()}
        
        # First pass: select best players for each position to meet minimum requirements
        for _, player in sorted_players.iterrows():
            name = player["Name"]
            position = player["Position"]
            price = player["Price"]
            total_points = player["Total_GW1_9"]
            
            # Check budget
            if price > remaining_budget:
                continue
                
            # Check position constraints
            min_pos, max_pos = formation_constraints[position]
            if position_counts[position] >= max_pos:
                continue
                
            # Check if we already have this player
            if name in [p["Name"] for p in selected_players]:
                continue
                
            # Add player
            selected_players.append({
                "Name": name,
                "Position": position,
                "Price": price,
                "Total_Points": total_points,
                "Team": "Unknown",  # Will be filled later
                "GW1_9_Breakdown": [player[f"GW {i}"] for i in range(1, 10)]
            })
            
            remaining_budget -= price
            position_counts[position] += 1
            
            # Stop if we have 15 players
            if len(selected_players) >= 15:
                break
        
        # Ensure we have exactly 15 players by filling remaining slots
        while len(selected_players) < 15:
            for _, player in sorted_players.iterrows():
                name = player["Name"]
                position = player["Position"]
                price = player["Price"]
                total_points = player["Total_GW1_9"]
                
                # Skip if already selected
                if name in [p["Name"] for p in selected_players]:
                    continue
                    
                # Check budget
                if price > remaining_budget:
                    continue
                    
                # Check position constraints
                min_pos, max_pos = formation_constraints[position]
                if position_counts[position] >= max_pos:
                    continue
                
                # Add player
                selected_players.append({
                    "Name": name,
                    "Position": position,
                    "Price": price,
                    "Total_Points": total_points,
                    "Team": "Unknown",
                    "GW1_9_Breakdown": [player[f"GW {i}"] for i in range(1, 10)]
                })
                
                remaining_budget -= price
                position_counts[position] += 1
                break
        
        # Determine starting XI vs bench (4 players)
        # Sort players by total points within each position
        starting_players = []
        bench_players = []
        
        for position in ["Goalkeeper", "Defender", "Midfielder", "Forward"]:
            pos_players = [p for p in selected_players if p["Position"] == position]
            pos_players.sort(key=lambda x: x["Total_Points"], reverse=True)
            
            if position == "Goalkeeper":
                # 1st GK starts, 2nd GK on bench
                starting_players.append(pos_players[0])
                bench_players.append(pos_players[1])
            elif position == "Defender":
                # First 3-4 DEFs start (depending on formation), rest on bench
                def_count = min(4, len(pos_players))
                starting_players.extend(pos_players[:def_count])
                bench_players.extend(pos_players[def_count:])
            elif position == "Midfielder":
                # First 4-5 MIDs start (depending on formation), rest on bench
                mid_count = min(5, len(pos_players))
                starting_players.extend(pos_players[:mid_count])
                bench_players.extend(pos_players[mid_count:])
            elif position == "Forward":
                # First 1-2 FWDs start (depending on formation), rest on bench
                fwd_count = min(2, len(pos_players))
                starting_players.extend(pos_players[:fwd_count])
                bench_players.extend(pos_players[fwd_count:])
        
        # Add status to all players
        for player in starting_players:
            player["Status"] = "Starting"
        for player in bench_players:
            player["Status"] = "Bench"
        
        # Combine all players (starting first, then bench)
        all_players = starting_players + bench_players
        
        # Calculate total expected points
        total_expected_points = sum(p["Total_Points"] for p in all_players)
        
        return {
            "players": all_players,
            "starting_xi": starting_players,
            "bench": bench_players,
            "total_expected_points": total_expected_points,
            "remaining_budget": remaining_budget,
            "formation": f"{position_counts.get('Defender', 0)}-{position_counts.get('Midfielder', 0)}-{position_counts.get('Forward', 0)}"
        }
