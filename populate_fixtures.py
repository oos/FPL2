#!/usr/bin/env python3
"""
Script to populate the fixtures table with real data from the FPL API
"""

import requests
import sqlite3
from datetime import datetime

def fetch_fpl_fixtures():
    """Fetch fixtures from FPL API"""
    try:
        url = "https://fantasy.premierleague.com/api/fixtures/"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching FPL fixtures: {e}")
        return None

def populate_fixtures():
    """Populate fixtures table with FPL API data"""
    # Fetch fixtures from FPL API
    fixtures = fetch_fpl_fixtures()
    if not fixtures:
        print("Failed to fetch fixtures from FPL API")
        return False
    
    # Connect to database
    conn = sqlite3.connect('fpl_oos.db')
    cursor = conn.cursor()
    
    try:
        # Clear existing fixtures
        cursor.execute("DELETE FROM fixtures")
        print("Cleared existing fixtures")
        
        # Insert new fixtures
        inserted_count = 0
        for fixture in fixtures:
            # Extract fixture data
            fixture_id = fixture.get('id')
            home_team_id = fixture.get('team_h')
            away_team_id = fixture.get('team_a')
            home_difficulty = fixture.get('team_h_difficulty')
            away_difficulty = fixture.get('team_a_difficulty')
            gameweek = fixture.get('event')
            
            # Skip if missing required data
            if not all([fixture_id, home_team_id, away_team_id, home_difficulty, away_difficulty, gameweek]):
                continue
            
            # Get team IDs from teams table using the FPL API team code
            cursor.execute("SELECT id FROM teams WHERE code = ?", (home_team_id,))
            home_team_result = cursor.fetchone()
            home_team_db_id = home_team_result[0] if home_team_result else None
            
            cursor.execute("SELECT id FROM teams WHERE code = ?", (away_team_id,))
            away_team_result = cursor.fetchone()
            away_team_db_id = away_team_result[0] if away_team_result else None
            
            # Skip if we can't find the teams
            if not home_team_db_id or not away_team_db_id:
                print(f"Warning: Skipping fixture {fixture_id} - team not found in database")
                continue
            
            # Insert fixture
            cursor.execute("""
                INSERT INTO fixtures (id, home_team_id, away_team_id, home_difficulty, away_difficulty, gameweek)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (fixture_id, home_team_db_id, away_team_db_id, home_difficulty, away_difficulty, gameweek))
            
            inserted_count += 1
        
        # Commit changes
        conn.commit()
        print(f"Successfully inserted {inserted_count} fixtures")
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM fixtures")
        total_fixtures = cursor.fetchone()[0]
        print(f"Total fixtures in database: {total_fixtures}")
        
        # Show sample data with team names
        cursor.execute("""
            SELECT f.id, ht.name as home_team, at.name as away_team, 
                   f.home_difficulty, f.away_difficulty, f.gameweek
            FROM fixtures f
            JOIN teams ht ON f.home_team_id = ht.id
            JOIN teams at ON f.away_team_id = at.id
            LIMIT 5
        """)
        sample_fixtures = cursor.fetchall()
        print("\nSample fixtures:")
        for fixture in sample_fixtures:
            print(f"  {fixture[1]} (FDR:{fixture[3]}) vs {fixture[2]} (FDR:{fixture[4]}) - GW{fixture[5]}")
        
        return True
        
    except Exception as e:
        print(f"Error populating fixtures: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🏆 Populating FPL Fixtures Database")
    print("=" * 40)
    
    success = populate_fixtures()
    
    if success:
        print("\n✅ Fixtures populated successfully!")
        print("The FDR page should now work correctly.")
    else:
        print("\n❌ Failed to populate fixtures.")
        print("Check the error messages above.")
