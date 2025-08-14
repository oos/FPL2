#!/usr/bin/env python3
"""
Simple Data Migration Script for FPL Application
"""

import sqlite3

def migrate_players():
    """Migrate player data to the new database structure"""
    conn = sqlite3.connect("fpl_oos.db")
    
    try:
        # Clear existing players table
        conn.execute("DELETE FROM players")
        
        # Insert player data directly
        players = [
            {"id": 1001, "name": "M.Salah", "position_name": "Midfielder", "team": "Liverpool", "price": 14.5, "uncertainty_percent": "24%", "overall_total": 57.0, "gw1_points": 6.7, "gw2_points": 6.1, "gw3_points": 5.6, "gw4_points": 7.0, "gw5_points": 6.6, "gw6_points": 5.7, "gw7_points": 5.7, "gw8_points": 7.4, "gw9_points": 6.2, "points_per_million": 3.93},
            {"id": 1002, "name": "Haaland", "position_name": "Forward", "team": "Man City", "price": 14.0, "uncertainty_percent": "24%", "overall_total": 47.0, "gw1_points": 5.1, "gw2_points": 6.3, "gw3_points": 5.1, "gw4_points": 5.8, "gw5_points": 3.8, "gw6_points": 6.6, "gw7_points": 4.8, "gw8_points": 5.1, "gw9_points": 4.4, "points_per_million": 3.36},
            {"id": 1003, "name": "Palmer", "position_name": "Midfielder", "team": "Chelsea", "price": 10.5, "uncertainty_percent": "28%", "overall_total": 45.8, "gw1_points": 5.1, "gw2_points": 4.9, "gw3_points": 5.5, "gw4_points": 4.6, "gw5_points": 4.3, "gw6_points": 5.9, "gw7_points": 4.4, "gw8_points": 4.3, "gw9_points": 6.7, "points_per_million": 4.36},
            {"id": 1004, "name": "Watkins", "position_name": "Forward", "team": "Aston Villa", "price": 9.0, "uncertainty_percent": "24%", "overall_total": 44.9, "gw1_points": 5.2, "gw2_points": 4.6, "gw3_points": 4.8, "gw4_points": 4.1, "gw5_points": 5.7, "gw6_points": 5.2, "gw7_points": 6.6, "gw8_points": 4.5, "gw9_points": 4.1, "points_per_million": 4.99},
            {"id": 1005, "name": "Isak", "position_name": "Forward", "team": "Newcastle", "price": 10.5, "uncertainty_percent": "24%", "overall_total": 44.6, "gw1_points": 4.4, "gw2_points": 4.5, "gw3_points": 5.8, "gw4_points": 5.7, "gw5_points": 4.7, "gw6_points": 4.1, "gw7_points": 5.4, "gw8_points": 4.7, "gw9_points": 5.4, "points_per_million": 4.25},
            {"id": 1006, "name": "Wood", "position_name": "Forward", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 40.3, "gw1_points": 4.8, "gw2_points": 3.9, "gw3_points": 5.2, "gw4_points": 3.2, "gw5_points": 4.8, "gw6_points": 5.8, "gw7_points": 3.9, "gw8_points": 4.6, "gw9_points": 4.0, "points_per_million": 5.37},
            {"id": 1007, "name": "Eze", "position_name": "Midfielder", "team": "Crystal Palace", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 39.4, "gw1_points": 4.1, "gw2_points": 4.8, "gw3_points": 4.0, "gw4_points": 5.8, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 4.0, "gw8_points": 4.9, "gw9_points": 3.4, "points_per_million": 5.25},
            {"id": 1008, "name": "Saka", "position_name": "Midfielder", "team": "Arsenal", "price": 10.0, "uncertainty_percent": "29%", "overall_total": 37.8, "gw1_points": 3.9, "gw2_points": 5.9, "gw3_points": 3.3, "gw4_points": 4.8, "gw5_points": 3.4, "gw6_points": 3.7, "gw7_points": 4.6, "gw8_points": 3.6, "gw9_points": 4.5, "points_per_million": 3.78},
            {"id": 1009, "name": "Evanilson", "position_name": "Forward", "team": "Fulham", "price": 7.0, "uncertainty_percent": "24%", "overall_total": 36.9, "gw1_points": 3.4, "gw2_points": 4.6, "gw3_points": 3.9, "gw4_points": 4.2, "gw5_points": 4.3, "gw6_points": 4.7, "gw7_points": 4.0, "gw8_points": 3.6, "gw9_points": 4.2, "points_per_million": 5.27},
            {"id": 1010, "name": "Wissa", "position_name": "Forward", "team": "Brentford", "price": 7.5, "uncertainty_percent": "26%", "overall_total": 36.6, "gw1_points": 3.8, "gw2_points": 4.4, "gw3_points": 4.7, "gw4_points": 4.0, "gw5_points": 3.7, "gw6_points": 4.5, "gw7_points": 3.8, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 4.88}
        ]
        
        for player in players:
            conn.execute("""
                INSERT INTO players (
                    id, name, position_name, team, price, uncertainty_percent, overall_total,
                    gw1_points, gw2_points, gw3_points, gw4_points, gw5_points, 
                    gw6_points, gw7_points, gw8_points, gw9_points, points_per_million
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player['id'], player['name'], player['position_name'], player['team'], 
                player['price'], player['uncertainty_percent'], player['overall_total'],
                player['gw1_points'], player['gw2_points'], player['gw3_points'], 
                player['gw4_points'], player['gw5_points'], player['gw6_points'], 
                player['gw7_points'], player['gw8_points'], player['gw9_points'], 
                player['points_per_million']
            ))
        
        conn.commit()
        print(f"Successfully migrated {len(players)} players to database")
        
    except Exception as e:
        print(f"Error migrating data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_players()
