from dataclasses import dataclass
from typing import Optional

@dataclass
class Fixture:
    """Fixture model representing a football match"""
    id: int
    home_team: str
    away_team: str
    home_difficulty: int
    away_difficulty: int
    gameweek: int
    
    def to_dict(self) -> dict:
        """Convert fixture to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'home_difficulty': self.home_difficulty,
            'away_difficulty': self.away_difficulty,
            'gameweek': self.gameweek
        }
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Fixture':
        """Create Fixture instance from database row"""
        return cls(
            id=row[0],
            home_team=row[1],
            away_team=row[2],
            home_difficulty=row[3],
            away_difficulty=row[4],
            gameweek=row[5]
        )
