import sqlite3
import requests
import json

def update_database_schema():
    """Update database schema to add Teams table and link to Players table"""
    conn = sqlite3.connect("fpl_oos.db")
    cursor = conn.cursor()
    
    try:
        print("Updating database schema...")
        
        # Check current teams table structure
        cursor.execute("PRAGMA table_info(teams)")
        existing_columns = {col[1]: col[2] for col in cursor.fetchall()}
        print(f"Current teams table columns: {list(existing_columns.keys())}")
        
        # Add missing columns to teams table if they don't exist
        if 'code' not in existing_columns:
            print("Adding code column to teams table...")
            cursor.execute("ALTER TABLE teams ADD COLUMN code INTEGER")
        
        if 'created_at' not in existing_columns:
            print("Adding created_at column to teams table...")
            cursor.execute("ALTER TABLE teams ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        # Check if Players table has team_id column
        cursor.execute("PRAGMA table_info(players)")
        player_columns = [col[1] for col in cursor.fetchall()]
        
        if 'team_id' not in player_columns:
            print("Adding team_id column to Players table...")
            cursor.execute("ALTER TABLE players ADD COLUMN team_id INTEGER")
            
            # Create index for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id)")
        
        # Fetch teams from FPL API
        print("Fetching teams from FPL API...")
        response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
        if response.status_code == 200:
            data = response.json()
            teams = data.get('teams', [])
            
            # Clear existing teams data
            cursor.execute("DELETE FROM teams")
            
            # Insert teams with updated structure
            for team in teams:
                cursor.execute("""
                    INSERT INTO teams (id, name, short_name, code, strength)
                    VALUES (?, ?, ?, ?, ?)
                """, (team['id'], team['name'], team['short_name'], team['code'], 0))
            
            print(f"Inserted {len(teams)} teams into database")
            
            # Update existing players to link to teams
            print("Updating existing players to link to teams...")
            
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
            
        else:
            print(f"Error fetching teams from API: {response.status_code}")
            
        # Commit changes
        conn.commit()
        print("Database schema updated successfully!")
        
        # Show final structure
        print("\nFinal database structure:")
        cursor.execute("PRAGMA table_info(teams)")
        print("Teams table columns:")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
            
        cursor.execute("PRAGMA table_info(players)")
        print("\nPlayers table columns:")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
            
        # Show sample data
        print("\nSample teams data:")
        cursor.execute("SELECT * FROM teams LIMIT 5")
        for row in cursor.fetchall():
            print(f"  {row}")
            
        print(f"\nTotal teams: {len(teams)}")
        cursor.execute("SELECT COUNT(*) FROM players WHERE team_id IS NOT NULL")
        linked_players = cursor.fetchone()[0]
        print(f"Players with team_id: {linked_players}")
        
    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema()
