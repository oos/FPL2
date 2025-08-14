#!/usr/bin/env python3
"""
Script to remove all players from database and repopulate from FFF Players CSV
"""

import logging
import sys
from pathlib import Path
from backend.database.manager import DatabaseManager
from backend.services.csv_service import CSVService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to repopulate players from CSV"""
    
    # Configuration
    csv_file_path = "./misc/MASTER - FFF Players Predicted Points.csv"
    db_path = "fpl.db"  # Update this path to your database file
    batch_size = 1000  # Process 1000 records at a time
    
    # Check if CSV file exists
    if not Path(csv_file_path).exists():
        logger.error(f"CSV file not found: {csv_file_path}")
        sys.exit(1)
    
    try:
        # Initialize database manager
        logger.info("Initializing database manager...")
        db_manager = DatabaseManager(db_path)
        
        # Initialize CSV service
        logger.info("Initializing CSV service...")
        csv_service = CSVService(db_manager)
        
        # Get current player count
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM players")
        current_count = cursor.fetchone()[0]
        logger.info(f"Current players in database: {current_count}")
        
        # Remove all players
        logger.info("Removing all players from database...")
        cursor.execute("DELETE FROM players")
        conn.commit()
        logger.info(f"Removed {current_count} players from database")
        
        # Verify removal
        cursor.execute("SELECT COUNT(*) FROM players")
        remaining_count = cursor.fetchone()[0]
        logger.info(f"Players remaining after deletion: {remaining_count}")
        
        if remaining_count > 0:
            logger.error("Failed to remove all players!")
            sys.exit(1)
        
        # Process FFF Players CSV file
        logger.info(f"Processing FFF Players CSV file: {csv_file_path}")
        logger.info(f"Batch size: {batch_size}")
        
        # Check CSV for duplicates before processing
        import pandas as pd
        df = pd.read_csv(csv_file_path)
        logger.info(f"📁 CSV file contains {len(df)} rows")
        logger.info(f"🔍 CSV file contains {df['Name'].nunique()} unique player names")
        logger.info(f"⚠️  CSV file contains {len(df) - df['Name'].nunique()} duplicate entries")
        
        total_inserted = csv_service.process_fff_players_csv(csv_file_path, batch_size)
        
        logger.info(f"✅ Successfully repopulated players table!")
        logger.info(f"📊 Total players inserted: {total_inserted}")
        
        # Verify the new data
        logger.info("Verifying inserted data...")
        cursor.execute("SELECT COUNT(*) FROM players")
        new_total = cursor.fetchone()[0]
        logger.info(f"📈 Total players in database: {new_total}")
        
        # Show sample data
        cursor.execute("SELECT name, position, price, total_points FROM players LIMIT 5")
        sample_players = cursor.fetchall()
        logger.info("🔍 Sample players:")
        for player in sample_players:
            logger.info(f"   - {player[0]} ({player[1]}) - £{player[2]}M - {player[3]} pts")
        
        # Show position breakdown
        cursor.execute("SELECT position, COUNT(*) FROM players GROUP BY position")
        position_counts = cursor.fetchall()
        logger.info("📊 Position breakdown:")
        for position, count in position_counts:
            logger.info(f"   - {position}: {count} players")
        
        logger.info("🎉 Database repopulation complete!")
        
    except Exception as e:
        logger.error(f"Error repopulating players: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
