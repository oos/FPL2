#!/usr/bin/env python3
"""
Add more realistic player data to the database
"""

import sqlite3

def add_more_players():
    """Add more realistic player data to the database"""
    conn = sqlite3.connect("fpl_oos.db")
    
    try:
        # Add more players with realistic data
        additional_players = [
            {"id": 1011, "name": "B.Fernandes", "position_name": "Midfielder", "team": "Man United", "price": 9.0, "uncertainty_percent": "29%", "overall_total": 35.4, "gw1_points": 3.4, "gw2_points": 3.7, "gw3_points": 4.9, "gw4_points": 3.1, "gw5_points": 4.1, "gw6_points": 3.8, "gw7_points": 5.3, "gw8_points": 2.9, "gw9_points": 4.1, "points_per_million": 3.93},
            {"id": 1012, "name": "Virgil", "position_name": "Defender", "team": "Liverpool", "price": 6.0, "uncertainty_percent": "24%", "overall_total": 35.1, "gw1_points": 4.2, "gw2_points": 3.2, "gw3_points": 3.5, "gw4_points": 4.4, "gw5_points": 4.6, "gw6_points": 3.7, "gw7_points": 3.3, "gw8_points": 4.4, "gw9_points": 3.8, "points_per_million": 5.85},
            {"id": 1013, "name": "Gibbs-White", "position_name": "Midfielder", "team": "Nottingham Forest", "price": 7.5, "uncertainty_percent": "25%", "overall_total": 35.1, "gw1_points": 4.3, "gw2_points": 3.5, "gw3_points": 4.4, "gw4_points": 2.9, "gw5_points": 4.2, "gw6_points": 5.2, "gw7_points": 3.4, "gw8_points": 3.9, "gw9_points": 3.4, "points_per_million": 4.68},
            {"id": 1014, "name": "Strand Larsen", "position_name": "Forward", "team": "Wolves", "price": 6.5, "uncertainty_percent": "25%", "overall_total": 34.8, "gw1_points": 3.2, "gw2_points": 3.5, "gw3_points": 3.7, "gw4_points": 3.4, "gw5_points": 5.1, "gw6_points": 3.5, "gw7_points": 3.8, "gw8_points": 4.3, "gw9_points": 4.4, "points_per_million": 5.35},
            {"id": 1015, "name": "Rice", "position_name": "Midfielder", "team": "Arsenal", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 34.4, "gw1_points": 3.7, "gw2_points": 5.0, "gw3_points": 3.1, "gw4_points": 4.1, "gw5_points": 3.4, "gw6_points": 3.5, "gw7_points": 4.1, "gw8_points": 3.6, "gw9_points": 4.0, "points_per_million": 5.29},
            {"id": 1016, "name": "Rogers", "position_name": "Midfielder", "team": "Aston Villa", "price": 7.0, "uncertainty_percent": "28%", "overall_total": 33.7, "gw1_points": 1.1, "gw2_points": 4.0, "gw3_points": 4.2, "gw4_points": 3.7, "gw5_points": 4.4, "gw6_points": 4.2, "gw7_points": 5.2, "gw8_points": 3.7, "gw9_points": 3.3, "points_per_million": 4.81},
            {"id": 1017, "name": "Sánchez", "position_name": "Goalkeeper", "team": "Chelsea", "price": 5.0, "uncertainty_percent": "22%", "overall_total": 33.7, "gw1_points": 4.0, "gw2_points": 3.7, "gw3_points": 4.0, "gw4_points": 3.5, "gw5_points": 3.7, "gw6_points": 3.9, "gw7_points": 3.3, "gw8_points": 3.3, "gw9_points": 4.3, "points_per_million": 6.74},
            {"id": 1018, "name": "Welbeck", "position_name": "Forward", "team": "Brighton", "price": 6.5, "uncertainty_percent": "26%", "overall_total": 33.5, "gw1_points": 4.1, "gw2_points": 3.3, "gw3_points": 3.6, "gw4_points": 3.4, "gw5_points": 4.1, "gw6_points": 3.3, "gw7_points": 4.0, "gw8_points": 4.2, "gw9_points": 3.5, "points_per_million": 5.15},
            {"id": 1019, "name": "Mac Allister", "position_name": "Midfielder", "team": "Liverpool", "price": 6.5, "uncertainty_percent": "23%", "overall_total": 33.4, "gw1_points": 4.0, "gw2_points": 3.5, "gw3_points": 3.2, "gw4_points": 4.0, "gw5_points": 3.9, "gw6_points": 3.6, "gw7_points": 3.2, "gw8_points": 4.1, "gw9_points": 3.7, "points_per_million": 5.14},
            {"id": 1020, "name": "Petrović", "position_name": "Goalkeeper", "team": "Chelsea", "price": 4.5, "uncertainty_percent": "21%", "overall_total": 33.3, "gw1_points": 3.4, "gw2_points": 3.9, "gw3_points": 3.3, "gw4_points": 4.0, "gw5_points": 3.5, "gw6_points": 3.8, "gw7_points": 3.8, "gw8_points": 3.9, "gw9_points": 3.8, "points_per_million": 7.40}
        ]
        
        for player in additional_players:
            conn.execute("""
                INSERT OR REPLACE INTO players (
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
        print(f"Successfully added {len(additional_players)} more players to database")
        
    except Exception as e:
        print(f"Error adding players: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_more_players()
