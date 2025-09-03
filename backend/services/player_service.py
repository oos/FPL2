from typing import List, Optional, Dict, Any
from backend.models.player import Player
from backend.database.manager import DatabaseManager

class PlayerService:
    """Service layer for player-related business logic"""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize player service with database manager"""
        self.db_manager = db_manager
    
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players as dictionaries for API response"""
        players = self.db_manager.get_all_players()
        return [player.to_dict() for player in players]
    
    def get_players_by_position(self, position: str) -> List[Dict[str, Any]]:
        """Get players by position as dictionaries for API response"""
        players = self.db_manager.get_players_by_position(position)
        return [player.to_dict() for player in players]
    
    def get_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Get player by ID as dictionary for API response"""
        player = self.db_manager.get_player_by_id(player_id)
        return player.to_dict() if player else None
    
    def search_players(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search players by name (case-insensitive)"""
        all_players = self.db_manager.get_all_players()
        query_lower = query.lower()
        
        # Simple search - in a real app, you'd use database LIKE queries
        matching_players = [
            player for player in all_players 
            if query_lower in player.name.lower()
        ]
        
        return [player.to_dict() for player in matching_players[:limit]]
    
    def get_players_by_team(self, team_name: str) -> List[Dict[str, Any]]:
        """Get all players from a specific team"""
        all_players = self.db_manager.get_all_players()
        team_players = [
            player for player in all_players 
            if player.team.lower() == team_name.lower()
        ]
        return [player.to_dict() for player in team_players]
    
    def get_players_by_price_range(self, min_price: float, max_price: float) -> List[Dict[str, Any]]:
        """Get players within a price range"""
        all_players = self.db_manager.get_all_players()
        price_filtered = [
            player for player in all_players 
            if min_price <= player.price <= max_price
        ]
        return [player.to_dict() for player in price_filtered]
    
    def get_top_players_by_points(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top players by total points"""
        all_players = self.db_manager.get_all_players()
        sorted_players = sorted(all_players, key=lambda p: p.total_points, reverse=True)
        return [player.to_dict() for player in sorted_players[:limit]]
    
    def get_top_players_by_value(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top players by points per million"""
        all_players = self.db_manager.get_all_players()
        sorted_players = sorted(all_players, key=lambda p: p.points_per_million, reverse=True)
        return [player.to_dict() for player in sorted_players[:limit]]
    
    def add_player(self, player_data: Dict[str, Any]) -> bool:
        """Add a new player to the database"""
        try:
            player = Player(
                id=player_data['id'],
                name=player_data['name'],
                position=player_data['position'],
                team=player_data['team'],
                price=player_data['price'],
                chance_of_playing_next_round=player_data.get('chance_of_playing_next_round', 100.0),
                points_per_million=player_data.get('points_per_million', 0.0),
                total_points=player_data.get('total_points', 0.0),
                form=player_data.get('form', 0.0),
                ownership=player_data.get('ownership', 0.0),
                team_id=player_data.get('team_id'),
                gw1_points=player_data.get('gw1_points', 0.0),
                gw2_points=player_data.get('gw2_points', 0.0),
                gw3_points=player_data.get('gw3_points', 0.0),
                gw4_points=player_data.get('gw4_points', 0.0),
                gw5_points=player_data.get('gw5_points', 0.0),
                gw6_points=player_data.get('gw6_points', 0.0),
                gw7_points=player_data.get('gw7_points', 0.0),
                gw8_points=player_data.get('gw8_points', 0.0),
                gw9_points=player_data.get('gw9_points', 0.0)
            )
            return self.db_manager.add_player(player)
        except KeyError as e:
            print(f"Missing required field: {e}")
            return False
        except Exception as e:
            print(f"Error creating player: {e}")
            return False
    
    def get_player_statistics(self) -> Dict[str, Any]:
        """Get player statistics for the application"""
        all_players = self.db_manager.get_all_players()
        
        if not all_players:
            return {
                'total_players': 0,
                'positions': {},
                'teams': {},
                'price_range': {'min': 0, 'max': 0, 'avg': 0},
                'points_range': {'min': 0, 'max': 0, 'avg': 0}
            }
        
        # Position counts
        positions = {}
        for player in all_players:
            positions[player.position] = positions.get(player.position, 0) + 1
        
        # Team counts
        teams = {}
        for player in all_players:
            teams[player.team] = teams.get(player.team, 0) + 1
        
        # Price statistics
        prices = [player.price for player in all_players]
        price_range = {
            'min': min(prices),
            'max': max(prices),
            'avg': sum(prices) / len(prices)
        }
        
        # Points statistics
        points = [player.total_points for player in all_players]
        points_range = {
            'min': min(points),
            'max': max(points),
            'avg': sum(points) / len(points)
        }
        
        return {
            'total_players': len(all_players),
            'positions': positions,
            'teams': teams,
            'price_range': price_range,
            'points_range': points_range
        }
