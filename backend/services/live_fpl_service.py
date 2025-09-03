import requests
import logging
from typing import Dict, List, Optional
from backend.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

class LiveFPLService:
    """Service for fetching live FPL data from the official API"""
    
    BASE_URL = "https://fantasy.premierleague.com/api"
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def fetch_team_data(self, fpl_team_id: int) -> Optional[Dict]:
        """Fetch team data from FPL API"""
        try:
            url = f"{self.BASE_URL}/entry/{fpl_team_id}/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch team data for {fpl_team_id}: {e}")
            return None
    
    def fetch_team_history(self, fpl_team_id: int) -> Optional[Dict]:
        """Fetch team history from FPL API"""
        try:
            url = f"{self.BASE_URL}/entry/{fpl_team_id}/history/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch team history for {fpl_team_id}: {e}")
            return None
    
    def fetch_current_squad(self, fpl_team_id: int, gameweek: int = None) -> Optional[Dict]:
        """Fetch current squad from FPL API"""
        try:
            if gameweek is None:
                gameweek = self.get_current_gameweek()
            url = f"{self.BASE_URL}/entry/{fpl_team_id}/event/{gameweek}/picks/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch current squad for {fpl_team_id} GW{gameweek}: {e}")
            return None
    
    def fetch_gameweek_picks(self, fpl_team_id: int, gameweek: int) -> Optional[Dict]:
        """Fetch squad picks for a specific gameweek"""
        try:
            url = f"{self.BASE_URL}/entry/{fpl_team_id}/event/{gameweek}/picks/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch GW{gameweek} picks for {fpl_team_id}: {e}")
            return None
    
    def sync_user_profile(self, fpl_team_id: int) -> bool:
        """Sync user profile data from FPL API"""
        try:
            team_data = self.fetch_team_data(fpl_team_id)
            if not team_data:
                return False
            
            # Extract team name and manager name from the API response
            team_name = team_data.get('name', '')
            player_first_name = team_data.get('player_first_name', '')
            player_last_name = team_data.get('player_last_name', '')
            
            # Combine first and last name, handling cases where either might be missing
            manager_name = ''
            if player_first_name and player_last_name:
                manager_name = f"{player_first_name} {player_last_name}"
            elif player_first_name:
                manager_name = player_first_name
            elif player_last_name:
                manager_name = player_last_name
            
            # Save profile to database
            self.db_manager.save_user_profile(
                fpl_team_id=fpl_team_id,
                team_name=team_name,
                manager_name=manager_name
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to sync user profile for {fpl_team_id}: {e}")
            return False
    
    def sync_user_squad(self, fpl_team_id: int, gameweek: int) -> bool:
        """Sync user squad data for a specific gameweek"""
        try:
            picks_data = self.fetch_gameweek_picks(fpl_team_id, gameweek)
            if not picks_data:
                return False
            
            # Get player picks
            picks = picks_data.get('picks', [])
            if not picks:
                return False
            
            # Convert picks to squad data format
            squad_data = []
            for pick in picks:
                element_id = pick['element']
                
                # Find player in our database by FPL element ID
                player = self.db_manager.get_player_by_fpl_element_id(element_id)
                if player:
                    squad_data.append({
                        'player_id': player.id,
                        'position': pick['position'],
                        'is_captain': pick.get('is_captain', False),
                        'is_vice_captain': pick.get('is_vice_captain', False),
                        'is_bench': pick['position'] > 11,
                        'bench_position': pick['position'] - 11 if pick['position'] > 11 else None,
                        'transfer_in': pick.get('multiplier', 0) > 0,
                        'transfer_out': pick.get('multiplier', 0) < 0,
                        'actual_points': pick.get('points', 0),  # Store actual points from FPL API
                        'multiplier': pick.get('multiplier', 1)  # Store multiplier (captain = 2, etc.)
                    })
            
            # Save squad data
            if squad_data:
                self.db_manager.save_user_squad(fpl_team_id, gameweek, squad_data)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to sync user squad for {fpl_team_id} GW{gameweek}: {e}")
            return False
    
    def sync_user_league_standings(self, fpl_team_id: int) -> bool:
        """Sync user league standings from FPL API"""
        try:
            history_data = self.fetch_team_history(fpl_team_id)
            if not history_data:
                return False
            
            # Get current and history data
            current = history_data.get('current', [])
            
            for gw_data in current:
                gameweek = gw_data.get('event')
                if gameweek:
                    standing_data = {
                        'total_points': gw_data.get('total_points', 0),
                        'gameweek_points': gw_data.get('points', 0),
                        'overall_rank': gw_data.get('overall_rank'),
                        'gameweek_rank': gw_data.get('rank'),
                        'transfers_made': gw_data.get('event_transfers', 0),
                        'transfer_cost': gw_data.get('event_transfers_cost', 0)
                    }
                    
                    self.db_manager.save_user_league_standing(fpl_team_id, gameweek, standing_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to sync user league standings for {fpl_team_id}: {e}")
            return False
    
    def get_current_gameweek(self) -> int:
        """Get the current gameweek from FPL API"""
        try:
            url = f"{self.BASE_URL}/bootstrap-static/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Find the current gameweek
            for event in data.get('events', []):
                if event.get('is_current'):
                    return event.get('id', 1)
            
            # Fallback to the latest gameweek if no current one
            events = data.get('events', [])
            if events:
                return max(event.get('id', 1) for event in events)
            
            return 1  # Default fallback
        except Exception as e:
            logger.error(f"Failed to get current gameweek: {e}")
            return 1  # Default fallback

    def sync_all_user_data(self, fpl_team_id: int) -> Dict[str, bool]:
        """Sync all user data from FPL API"""
        current_gw = self.get_current_gameweek()
        results = {
            'profile': self.sync_user_profile(fpl_team_id),
            'squad': self.sync_user_squad(fpl_team_id, current_gw),  # Current GW
            'standings': self.sync_user_league_standings(fpl_team_id)
        }
        
        return results
    
    def sync_all_historical_squads(self, fpl_team_id: int) -> Dict[int, bool]:
        """Sync historical squad data for all past gameweeks"""
        current_gw = self.get_current_gameweek()
        results = {}
        
        # Sync squads for all past gameweeks (1 to current_gw-1)
        for gw in range(1, current_gw):
            try:
                success = self.sync_user_squad(fpl_team_id, gw)
                results[gw] = success
                logger.info(f"Synced historical squad for GW{gw}: {'Success' if success else 'Failed'}")
            except Exception as e:
                logger.error(f"Failed to sync historical squad for GW{gw}: {e}")
                results[gw] = False
        
        return results
    
    def get_squad_for_gameweek(self, fpl_team_id: int, gameweek: int) -> Optional[List[Dict]]:
        """Get squad data for a specific gameweek, syncing if not available"""
        # First try to get existing squad data
        squad = self.db_manager.get_user_squad(fpl_team_id, gameweek)
        
        # If no squad data exists, try to sync from FPL API
        if not squad:
            try:
                success = self.sync_user_squad(fpl_team_id, gameweek)
                if success:
                    squad = self.db_manager.get_user_squad(fpl_team_id, gameweek)
            except Exception as e:
                logger.error(f"Failed to sync squad for GW{gameweek}: {e}")
        
        return squad
