import sqlite3

def fix_team_names():
    """Fix team name mismatches between players and teams tables"""
    conn = sqlite3.connect("fpl_oos.db")
    cursor = conn.cursor()
    
    try:
        print("Fixing team name mismatches...")
        
        # Team name mapping from players table to teams table
        team_mapping = {
            'Man United': 'Man Utd',
            'Nottingham Forest': 'Nott\'m Forest',
            'Tottenham': 'Spurs',
            'Manchester City': 'Man City',
            'Manchester United': 'Man Utd',
            'Sheffield United': 'Sheffield Utd',
            'Leicester City': 'Leicester',
            'West Brom': 'West Brom',
            'Cardiff': 'Cardiff',
            'Huddersfield': 'Huddersfield',
            'Watford': 'Watford',
            'Norwich': 'Norwich',
            'Brentford': 'Brentford',
            'Brighton': 'Brighton',
            'Burnley': 'Burnley',
            'Crystal Palace': 'Crystal Palace',
            'Everton': 'Everton',
            'Fulham': 'Fulham',
            'Leeds': 'Leeds',
            'Liverpool': 'Liverpool',
            'Newcastle': 'Newcastle',
            'Southampton': 'Southampton',
            'West Ham': 'West Ham',
            'Wolves': 'Wolves',
            'Arsenal': 'Arsenal',
            'Aston Villa': 'Aston Villa',
            'Bournemouth': 'Bournemouth',
            'Chelsea': 'Chelsea'
        }
        
        # Update players table with corrected team names
        updated_count = 0
        for old_name, new_name in team_mapping.items():
            cursor.execute("""
                UPDATE players 
                SET team = ? 
                WHERE team = ?
            """, (new_name, old_name))
            
            rows_affected = cursor.rowcount
            if rows_affected > 0:
                print(f"Updated {rows_affected} players: '{old_name}' -> '{new_name}'")
                updated_count += rows_affected
        
        print(f"Total players updated: {updated_count}")
        
        # Now update team_id for all players
        print("Updating team_id for all players...")
        
        # Get all teams for mapping
        cursor.execute("SELECT id, name FROM teams")
        team_mapping = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Update players with team_id
        cursor.execute("SELECT id, team FROM players WHERE team_id IS NULL")
        players_to_update = cursor.fetchall()
        
        updated_count = 0
        for player_id, team_name in players_to_update:
            if team_name in team_mapping:
                cursor.execute("UPDATE players SET team_id = ? WHERE id = ?", 
                             (team_mapping[team_name], player_id))
                updated_count += 1
            else:
                print(f"Warning: Team '{team_name}' not found in teams table for player {player_id}")
        
        print(f"Updated {updated_count} players with team_id")
        
        # Commit changes
        conn.commit()
        print("Team names fixed successfully!")
        
        # Show final status
        cursor.execute("SELECT COUNT(*) FROM players WHERE team_id IS NOT NULL")
        linked_players = cursor.fetchone()[0]
        print(f"Players with team_id: {linked_players}")
        
        # Show sample of linked players
        cursor.execute("""
            SELECT p.name, p.team, t.name as team_name, p.team_id
            FROM players p
            JOIN teams t ON p.team_id = t.id
            LIMIT 10
        """)
        
        print("\nSample of linked players:")
        for row in cursor.fetchall():
            print(f"  {row[0]} -> {row[1]} (ID: {row[3]})")
        
    except Exception as e:
        print(f"Error fixing team names: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_team_names()
