#!/usr/bin/env python3
"""
Data Migration Script for FPL Application
Moves hardcoded player data from FPL_oos.py to the new database structure
"""

import sqlite3
import re
from typing import List, Dict, Any

def extract_player_data_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Extract player data from the old FPL_oos.py file"""
    players = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Find the players_data array in the add_players_via_sql function
        pattern = r'players_data\s*=\s*\[(.*?)\]'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("Could not find players_data array in file")
            return []
        
        data_content = match.group(1)
        
        # Extract individual player entries
        player_pattern = r'\{[^}]+\}'
        player_matches = re.findall(player_pattern, data_content)
        
        for player_str in player_matches:
            try:
                # Extract key-value pairs
                player_data = {}
                
                # Extract id
                id_match = re.search(r'"id":\s*(\d+)', player_str)
                if id_match:
                    player_data['id'] = int(id_match.group(1))
                
                # Extract name
                name_match = re.search(r'"name":\s*"([^"]+)"', player_str)
                if name_match:
                    player_data['name'] = name_match.group(1)
                
                # Extract position_name
                pos_match = re.search(r'"position_name":\s*"([^"]+)"', player_str)
                if pos_match:
                    player_data['position_name'] = pos_match.group(1)
                
                # Extract team
                team_match = re.search(r'"team":\s*"([^"]+)"', player_str)
                if team_match:
                    player_data['team'] = team_match.group(1)
                
                # Extract price
                price_match = re.search(r'"price":\s*([\d.]+)', player_str)
                if price_match:
                    player_data['price'] = float(price_match.group(1))
                
                # Extract uncertainty_percent
                unc_match = re.search(r'"uncertainty_percent":\s*"([^"]+)"', player_str)
                if unc_match:
                    player_data['uncertainty_percent'] = unc_match.group(1)
                
                # Extract overall_total
                total_match = re.search(r'"overall_total":\s*([\d.]+)', player_str)
                if total_match:
                    player_data['overall_total'] = float(total_match.group(1))
                
                # Extract GW points
                gw_points = []
                for i in range(1, 10):
                    gw_match = re.search(f'"gw{i}_points":\\s*([\\d.]+)', player_str)
                    if gw_match:
                        gw_points.append(float(gw_match.group(1)))
                    else:
                        gw_points.append(0.0)
                player_data['gw_points'] = gw_points
                
                # Extract points_per_million
                ppm_match = re.search(r'"points_per_million":\s*([\d.]+)', player_str)
                if ppm_match:
                    player_data['points_per_million'] = float(ppm_match.group(1))
                else:
                    player_data['points_per_million'] = 0.0
                
                # Only add if we have the essential fields
                if all(key in player_data for key in ['id', 'name', 'position_name', 'team', 'price']):
                    players.append(player_data)
                
            except Exception as e:
                print(f"Error parsing player: {e}")
                continue
        
        print(f"Extracted {len(players)} players from file")
        return players
        
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def migrate_players_to_database(players: List[Dict[str, Any]], db_path: str):
    """Migrate player data to the new database structure"""
    conn = sqlite3.connect(db_path)
    
    try:
        # Clear existing players table
        conn.execute("DELETE FROM players")
        
        # Insert new player data
        for player in players:
            conn.execute("""
                INSERT INTO players (
                    id, name, position_name, team, price, uncertainty_percent, overall_total,
                    gw1_points, gw2_points, gw3_points, gw4_points, gw5_points, 
                    gw6_points, gw7_points, gw8_points, gw9_points, points_per_million
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player['id'],
                player['name'],
                player['position_name'],
                player['team'],
                player['price'],
                player.get('uncertainty_percent', '24%'),
                player.get('overall_total', 0.0),
                player['gw_points'][0] if len(player['gw_points']) > 0 else 0.0,
                player['gw_points'][1] if len(player['gw_points']) > 1 else 0.0,
                player['gw_points'][2] if len(player['gw_points']) > 2 else 0.0,
                player['gw_points'][3] if len(player['gw_points']) > 3 else 0.0,
                player['gw_points'][4] if len(player['gw_points']) > 4 else 0.0,
                player['gw_points'][5] if len(player['gw_points']) > 5 else 0.0,
                player['gw_points'][6] if len(player['gw_points']) > 6 else 0.0,
                player['gw_points'][7] if len(player['gw_points']) > 7 else 0.0,
                player['gw_points'][8] if len(player['gw_points']) > 8 else 0.0,
                player['points_per_million']
            ))
        
        conn.commit()
        print(f"Successfully migrated {len(players)} players to database")
        
    except Exception as e:
        print(f"Error migrating data: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main migration function"""
    print("Starting FPL data migration...")
    
    # Extract data from old file
    old_file = "FPL_oos.py"
    players = extract_player_data_from_file(old_file)
    
    if not players:
        print("No players found to migrate")
        return
    
    # Migrate to database
    db_path = "fpl_oos.db"
    migrate_players_to_database(players, db_path)
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    main()
