import sqlite3
import requests

def update_current_teams():
    """Update teams table to only include current Premier League teams"""
    conn = sqlite3.connect("fpl_oos.db")
    cursor = conn.cursor()
    
    try:
        print("Updating teams table with current Premier League teams...")
        
        # Fetch current teams from FPL API
        response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
        if response.status_code == 200:
            data = response.json()
            current_teams = data.get('teams', [])
            
            print(f"Found {len(current_teams)} current Premier League teams")
            
            # Clear existing teams data
            cursor.execute("DELETE FROM teams")
            
            # Insert current teams
            for team in current_teams:
                cursor.execute("""
                    INSERT INTO teams (id, name, short_name, code, strength)
                    VALUES (?, ?, ?, ?, ?)
                """, (team['id'], team['name'], team['short_name'], team['code'], 0))
            
            print(f"Inserted {len(current_teams)} current teams into database")
            
            # Show current teams
            print("\nCurrent Premier League teams:")
            for team in current_teams:
                print(f"  {team['id']}: {team['name']} ({team['short_name']})")
            
            # Commit changes
            conn.commit()
            print("\nTeams table updated successfully!")
            
        else:
            print(f"Error fetching teams from API: {response.status_code}")
            
    except Exception as e:
        print(f"Error updating teams: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    update_current_teams()
