import sqlite3

def fix_team_references():
    """Fix team_id references after updating teams table"""
    conn = sqlite3.connect("fpl_oos.db")
    cursor = conn.cursor()
    
    try:
        print("Fixing team_id references...")
        
        # Clear all team_id references
        cursor.execute("UPDATE players SET team_id = NULL")
        print("Cleared all team_id references")
        
        # Get all teams for mapping
        cursor.execute("SELECT id, name FROM teams")
        team_mapping = {row[1]: row[0] for row in cursor.fetchall()}
        
        print(f"Found {len(team_mapping)} teams for mapping")
        
        # Update players with team_id
        cursor.execute("SELECT id, team FROM players")
        players_to_update = cursor.fetchall()
        
        updated_count = 0
        not_found_count = 0
        for player_id, team_name in players_to_update:
            if team_name in team_mapping:
                cursor.execute("UPDATE players SET team_id = ? WHERE id = ?", 
                             (team_mapping[team_name], player_id))
                updated_count += 1
            else:
                not_found_count += 1
                print(f"Warning: Team '{team_name}' not found in teams table for player {player_id}")
        
        print(f"Updated {updated_count} players with team_id")
        print(f"Players without matching team: {not_found_count}")
        
        # Commit changes
        conn.commit()
        print("Team references fixed successfully!")
        
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
        print(f"Error fixing team references: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_team_references()
