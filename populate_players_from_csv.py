#!/usr/bin/env python3
"""
Script to populate players table from CSV file using the CSV service
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
    """Main function to populate players from CSV"""
    
    # Configuration
    csv_file_path = "misc/MASTER - FFF Players Predicted Points.csv"  # Updated path to the correct CSV file
    db_path = "backend/fpl.db"  # Updated path to the correct database file
    batch_size = 1000  # Process 1000 records at a time
    
    # Check if CSV file exists
    if not Path(csv_file_path).exists():
        logger.error(f"CSV file not found: {csv_file_path}")
        logger.info("Please update the csv_file_path variable to point to your CSV file")
        sys.exit(1)
    
    try:
        # Initialize database manager
        logger.info("Initializing database manager...")
        db_manager = DatabaseManager(db_path)
        
        # Initialize CSV service
        logger.info("Initializing CSV service...")
        csv_service = CSVService(db_manager)
        
        # Process CSV file
        logger.info(f"Processing CSV file: {csv_file_path}")
        logger.info(f"Batch size: {batch_size}")
        
        # Use the FFF-specific CSV processing method
        logger.info("Using FFF Players CSV processing method...")
        total_inserted = csv_service.process_fff_players_csv(csv_file_path, batch_size)
        
        logger.info(f"✅ Successfully processed CSV file!")
        logger.info(f"📊 Total players inserted: {total_inserted}")
        
        # Verify the data
        logger.info("Verifying inserted data...")
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM players")
        total_players = cursor.fetchone()[0]
        logger.info(f"📈 Total players in database: {total_players}")
        
        # Show sample data
        cursor.execute("SELECT name, position, team, price FROM players LIMIT 5")
        sample_players = cursor.fetchall()
        logger.info("🔍 Sample players:")
        for player in sample_players:
            logger.info(f"   - {player[0]} ({player[1]}) - {player[2]} - £{player[3]}M")
        
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
