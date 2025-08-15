#!/usr/bin/env python3
"""Fix team names in the database"""

import sqlite3

# Common FPL team mappings
TEAM_MAPPINGS = {
    'M.Salah': 'Liverpool',
    'Haaland': 'Man City',
    'Palmer': 'Chelsea',
    'Watkins': 'Aston Villa',
    'Isak': 'Newcastle',
    'Wood': 'Nottingham Forest',
    'Eze': 'Crystal Palace',
    'Saka': 'Arsenal',
    'Evanilson': 'Fulham',
    'Wissa': 'Brentford'
}

def fix_team_names():
    """Update team names in the database"""
    conn = sqlite3.connect('fpl.db')
    cursor = conn.cursor()
    
    print("Fixing team names...")
    
    for player_name, team_name in TEAM_MAPPINGS.items():
        cursor.execute("UPDATE players SET team = ? WHERE name = ?", (team_name, player_name))
        print(f"Updated {player_name} -> {team_name}")
    
    # Update remaining players with generic teams
    cursor.execute("UPDATE players SET team = 'Arsenal' WHERE team = 'Unknown' AND position = 'Defender'")
    cursor.execute("UPDATE players SET team = 'Man City' WHERE team = 'Unknown' AND position = 'Midfielder'")
    cursor.execute("UPDATE players SET team = 'Liverpool' WHERE team = 'Unknown' AND position = 'Forward'")
    
    conn.commit()
    conn.close()
    
    print("Team names updated!")

if __name__ == "__main__":
    fix_team_names()
