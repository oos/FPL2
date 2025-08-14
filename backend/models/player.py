from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Player:
    """Player model representing a football player"""
    id: int
    name: str
    position: str
    team: str
    price: float
    chance_of_playing_next_round: float
    points_per_million: float
    total_points: float
    form: float = 0.0  # Default to 0.0 since it's not in database
    ownership: float = 0.0  # Default to 0.0 since it's not in database
    team_id: Optional[int] = None
    
    # Gameweek points
    gw1_points: float = 0.0
    gw2_points: float = 0.0
    gw3_points: float = 0.0
    gw4_points: float = 0.0
    gw5_points: float = 0.0
    gw6_points: float = 0.0
    gw7_points: float = 0.0
    gw8_points: float = 0.0
    gw9_points: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert player to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'team': self.team,
            'price': self.price,
            'chance_of_playing_next_round': self.chance_of_playing_next_round,
            'points_per_million': self.points_per_million,
            'total_points': self.total_points,
            'form': self.form,
            'ownership': self.ownership,
            'team_id': self.team_id,
            'gw1_points': self.gw1_points,
            'gw2_points': self.gw2_points,
            'gw3_points': self.gw3_points,
            'gw4_points': self.gw4_points,
            'gw5_points': self.gw5_points,
            'gw6_points': self.gw6_points,
            'gw7_points': self.gw7_points,
            'gw8_points': self.gw8_points,
            'gw9_points': self.gw9_points
        }
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Player':
        """Create Player instance from database row"""
        return cls(
            id=row[0],
            name=row[1],
            position=row[2],  # position_name from database
            team=row[3],
            price=row[4],
            chance_of_playing_next_round=row[18] or 100.0,  # chance_of_playing_next_round from database
            points_per_million=row[17] or 0.0,  # points_per_million from database
            total_points=row[7] or 0.0,  # overall_total from database
            form=0.0,  # Default value since not in database
            ownership=0.0,  # Default value since not in database
            team_id=row[19] if len(row) > 19 else None,
            gw1_points=row[8] if len(row) > 8 else 0.0,
            gw2_points=row[9] if len(row) > 9 else 0.0,
            gw3_points=row[10] if len(row) > 10 else 0.0,
            gw4_points=row[11] if len(row) > 11 else 0.0,
            gw5_points=row[12] if len(row) > 12 else 0.0,
            gw6_points=row[13] if len(row) > 13 else 0.0,
            gw7_points=row[14] if len(row) > 14 else 0.0,
            gw8_points=row[15] if len(row) > 15 else 0.0,
            gw9_points=row[16] if len(row) > 16 else 0.0
        )
