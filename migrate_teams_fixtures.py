#!/usr/bin/env python3
"""
Script to migrate teams and fixtures data from fpl_oos.db to fpl.db
"""

import sqlite3
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_teams_and_fixtures():
    """Migrate teams and fixtures from old database to new database"""
    
    source_db = "fpl_oos.db"
    target_db = "fpl.db"
    
    try:
        # Connect to source database
        source_conn = sqlite3.connect(source_db)
        source_cursor = source_conn.cursor()
        
        # Connect to target database
        target_conn = sqlite3.connect(target_db)
        target_cursor = target_conn.cursor()
        
        logger.info("Starting migration of teams and fixtures...")
        
        # Migrate teams
        logger.info("Migrating teams...")
        source_cursor.execute("SELECT * FROM teams")
        teams_data = source_cursor.fetchall()
        
        if teams_data:
            target_cursor.executemany("""
                INSERT INTO teams (id, name, short_name, code, strength, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, teams_data)
            logger.info(f"Migrated {len(teams_data)} teams")
        else:
            logger.warning("No teams found in source database")
        
        # Migrate fixtures
        logger.info("Migrating fixtures...")
        source_cursor.execute("SELECT * FROM fixtures")
        fixtures_data = source_cursor.fetchall()
        
        if fixtures_data:
            target_cursor.executemany("""
                INSERT INTO fixtures (id, home_team, away_team, home_difficulty, away_difficulty, gameweek)
                VALUES (?, ?, ?, ?, ?, ?)
            """, fixtures_data)
            logger.info(f"Migrated {len(fixtures_data)} fixtures")
        else:
            logger.warning("No fixtures found in source database")
        
        # Commit changes
        target_conn.commit()
        
        # Verify migration
        target_cursor.execute("SELECT COUNT(*) FROM teams")
        teams_count = target_cursor.fetchone()[0]
        
        target_cursor.execute("SELECT COUNT(*) FROM fixtures")
        fixtures_count = target_cursor.fetchone()[0]
        
        logger.info(f"Migration complete!")
        logger.info(f"Teams in target database: {teams_count}")
        logger.info(f"Fixtures in target database: {fixtures_count}")
        
        # Show sample data
        target_cursor.execute("SELECT name, short_name FROM teams LIMIT 5")
        sample_teams = target_cursor.fetchall()
        logger.info("Sample teams:")
        for team in sample_teams:
            logger.info(f"   - {team[0]} ({team[1]})")
        
        target_cursor.execute("SELECT home_team, away_team, gameweek FROM fixtures LIMIT 5")
        sample_fixtures = target_cursor.fetchall()
        logger.info("Sample fixtures:")
        for fixture in sample_fixtures:
            logger.info(f"   - {fixture[0]} vs {fixture[1]} (GW{fixture[2]})")
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        if 'target_conn' in locals():
            target_conn.rollback()
        raise
    finally:
        if 'source_conn' in locals():
            source_conn.close()
        if 'target_conn' in locals():
            target_conn.close()

if __name__ == "__main__":
    migrate_teams_and_fixtures()
