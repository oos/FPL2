import sqlite3

def add_missing_fields():
    conn = sqlite3.connect("fpl_oos.db")
    try:
        # Add missing fields to players table
        conn.execute("ALTER TABLE players ADD COLUMN chance_of_playing_next_round REAL DEFAULT 100.0")
        conn.execute("ALTER TABLE players ADD COLUMN ownership REAL DEFAULT 0.0")
        conn.execute("ALTER TABLE players ADD COLUMN form REAL DEFAULT 0.0")
        
        # Update existing players with default values
        conn.execute("UPDATE players SET chance_of_playing_next_round = 100.0 WHERE chance_of_playing_next_round IS NULL")
        conn.execute("UPDATE players SET ownership = 0.0 WHERE ownership IS NULL")
        conn.execute("UPDATE players SET form = points_per_million WHERE form IS NULL")
        
        conn.commit()
        print("Successfully added missing fields to database")
        
        # Show table structure
        cursor = conn.execute("PRAGMA table_info(players)")
        columns = cursor.fetchall()
        print("\nCurrent table structure:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"Error adding fields: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_missing_fields()
