from dataclasses import dataclass
from typing import Optional

@dataclass
class Team:
    """Team model representing a Premier League team"""
    id: int
    name: str
    short_name: str
    code: int
    strength: int
    created_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert team to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'code': self.code,
            'strength': self.strength,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Team':
        """Create Team instance from database row"""
        return cls(
            id=row[0],
            name=row[1],
            short_name=row[2],
            code=row[3] if len(row) > 3 else 0,
            strength=row[4] if len(row) > 4 else 0,
            created_at=row[5] if len(row) > 5 else None
        )
