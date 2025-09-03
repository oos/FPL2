import csv
import logging
from typing import List, Dict, Any, Iterator
from pathlib import Path
import pandas as pd
from backend.models.player import Player
from backend.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

class CSVService:
    """Service for efficiently processing CSV files and populating the database"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def process_csv_file(self, csv_path: str, batch_size: int = 1000) -> int:
        """
        Process CSV file and populate database efficiently using batching
        
        Args:
            csv_path: Path to CSV file
            batch_size: Number of records to process in each batch
            
        Returns:
            Total number of players inserted
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        logger.info(f"Processing CSV file: {csv_path}")
        
        # Use pandas for efficient CSV reading
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from CSV")
        
        total_inserted = 0
        
        # Process in batches for memory efficiency
        for batch_start in range(0, len(df), batch_size):
            batch_end = min(batch_start + batch_size, len(df))
            batch_df = df.iloc[batch_start:batch_end]
            
            # Convert batch to Player objects
            players_batch = self._convert_dataframe_to_players(batch_df)
            
            # Insert batch into database
            inserted_count = self.db_manager.bulk_insert_players(players_batch)
            total_inserted += inserted_count
            
            logger.info(f"Processed batch {batch_start//batch_size + 1}: "
                       f"{inserted_count} players inserted")
        
        logger.info(f"CSV processing complete. Total players inserted: {total_inserted}")
        return total_inserted
    
    def _convert_dataframe_to_players(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert pandas DataFrame to list of player dictionaries"""
        players = []
        
        for _, row in df.iterrows():
            try:
                player_dict = {
                    'name': str(row.get('name', '')),
                    'position': str(row.get('position', '')),
                    'team': str(row.get('team', '')),
                    'price': float(row.get('price', 0)),
                    'total_points': float(row.get('total_points', 0)),
                    'form': float(row.get('form', 0.0)),
                    'ownership': float(row.get('ownership', 0.0)),
                    'team_id': row.get('team_id'),
                    'gw1_points': float(row.get('gw1_points', 0)),
                    'gw2_points': float(row.get('gw2_points', 0)),
                    'gw3_points': float(row.get('gw3_points', 0)),
                    'gw4_points': float(row.get('gw4_points', 0)),
                    'gw5_points': float(row.get('gw5_points', 0)),
                    'gw6_points': float(row.get('gw6_points', 0)),
                    'gw7_points': float(row.get('gw7_points', 0)),
                    'gw8_points': float(row.get('gw8_points', 0)),
                    'gw9_points': float(row.get('gw9_points', 0)),
                    'chance_of_playing_next_round': int(row.get('chance_of_playing_next_round', 100)),
                    'points_per_million': float(row.get('points_per_million', 0))
                }
                players.append(player_dict)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing row {row.get('name', 'Unknown')}: {e}")
                continue
        
        return players
    
    def process_csv_streaming(self, csv_path: str, batch_size: int = 1000) -> int:
        """
        Process CSV file using streaming approach for very large files
        
        Args:
            csv_path: Path to CSV file
            batch_size: Number of records to process in each batch
            
        Returns:
            Total number of players inserted
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        logger.info(f"Processing CSV file (streaming): {csv_path}")
        
        total_inserted = 0
        current_batch = []
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    player_dict = self._convert_csv_row_to_dict(row)
                    current_batch.append(player_dict)
                    
                    # Process batch when it reaches batch_size
                    if len(current_batch) >= batch_size:
                        inserted_count = self.db_manager.bulk_insert_players(current_batch)
                        total_inserted += inserted_count
                        logger.info(f"Processed batch: {inserted_count} players inserted")
                        current_batch = []
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing row {row.get('name', 'Unknown')}: {e}")
                    continue
            
            # Process remaining records in final batch
            if current_batch:
                inserted_count = self.db_manager.bulk_insert_players(current_batch)
                total_inserted += inserted_count
                logger.info(f"Final batch: {inserted_count} players inserted")
        
        logger.info(f"CSV processing complete. Total players inserted: {total_inserted}")
        return total_inserted
    
    def _convert_csv_row_to_dict(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Convert CSV row to player dictionary with proper type conversion"""
        return {
            'name': str(row.get('name', '')),
            'position': str(row.get('position', '')),
            'team': str(row.get('team', '')),
            'price': float(row.get('price', 0)),
            'total_points': float(row.get('total_points', 0)),
            'form': float(row.get('form', 0.0)),
            'ownership': float(row.get('ownership', 0.0)),
            'team_id': row.get('team_id'),
            'gw1_points': float(row.get('gw1_points', 0)),
            'gw2_points': float(row.get('gw2_points', 0)),
            'gw3_points': float(row.get('gw3_points', 0)),
            'gw4_points': float(row.get('gw4_points', 0)),
            'gw5_points': float(row.get('gw5_points', 0)),
            'gw6_points': float(row.get('gw6_points', 0)),
            'gw7_points': float(row.get('gw7_points', 0)),
            'gw8_points': float(row.get('gw8_points', 0)),
            'gw9_points': float(row.get('gw9_points', 0)),
            'chance_of_playing_next_round': int(row.get('chance_of_playing_next_round', 100)),
            'points_per_million': float(row.get('points_per_million', 0))
        }
    
    def validate_csv_structure(self, csv_path: str) -> bool:
        """Validate that CSV has required columns"""
        required_columns = ['name', 'position', 'team', 'price', 'total_points']
        
        try:
            df = pd.read_csv(csv_path, nrows=1)  # Just read header
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False
            
            logger.info("CSV structure validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating CSV structure: {e}")
            return False
    
    def process_fff_players_csv(self, csv_path: str, batch_size: int = 1000) -> int:
        """
        Process the specific FFF Players CSV format
        
        Args:
            csv_path: Path to FFF Players CSV file
            batch_size: Number of records to process in each batch
            
        Returns:
            Total number of players inserted
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        logger.info(f"Processing FFF Players CSV file: {csv_path}")
        
        # Read CSV with pandas
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from FFF Players CSV")
        
        # Remove duplicates by name (keep the first occurrence)
        df_clean = df.drop_duplicates(subset=['Name'], keep='first')
        logger.info(f"After removing duplicates: {len(df_clean)} unique players")
        
        total_inserted = 0
        
        # Process in batches for memory efficiency
        for batch_start in range(0, len(df_clean), batch_size):
            batch_end = min(batch_start + batch_size, len(df_clean))
            batch_df = df_clean.iloc[batch_start:batch_end]
            
            # Convert batch to player dictionaries
            players_batch = self._convert_fff_csv_to_players(batch_df)
            
            # Insert batch into database
            inserted_count = self.db_manager.bulk_insert_players(players_batch)
            total_inserted += inserted_count
            
            logger.info(f"Processed batch {batch_start//batch_size + 1}: "
                       f"{inserted_count} players inserted")
        
        logger.info(f"FFF Players CSV processing complete. Total players inserted: {total_inserted}")
        return total_inserted
    
    def _convert_fff_csv_to_players(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert FFF Players CSV DataFrame to list of player dictionaries"""
        players = []
        
        for _, row in df.iterrows():
            try:
                # Extract price value (remove £ symbol and convert to float)
                price_str = str(row.get('Price', '0'))
                price = float(price_str.replace('£', '').replace(',', ''))
                
                # Extract gameweek points
                gw_points = {}
                for i in range(1, 10):
                    gw_key = f'GW {i}'
                    if gw_key in row:
                        try:
                            gw_points[f'gw{i}_points'] = float(row[gw_key])
                        except (ValueError, TypeError):
                            gw_points[f'gw{i}_points'] = 0.0
                    else:
                        gw_points[f'gw{i}_points'] = 0.0
                
                # Calculate total points from gameweeks
                total_points = sum(gw_points.values())
                
                # Calculate points per million
                points_per_million = total_points / price if price > 0 else 0.0
                
                player_dict = {
                    'name': str(row.get('Name', '')),
                    'position': str(row.get('Position', '')),
                    'team': 'Unknown',  # FFF CSV doesn't have team info
                    'price': price,
                    'total_points': total_points,
                    'form': 0.0,  # Not available in FFF CSV
                    'ownership': 0.0,  # Not available in FFF CSV
                    'team_id': None,
                    'chance_of_playing_next_round': 100,
                    'points_per_million': points_per_million,
                    **gw_points  # Unpack all gameweek points
                }
                
                players.append(player_dict)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing row {row.get('Name', 'Unknown')}: {e}")
                continue
        
        return players
