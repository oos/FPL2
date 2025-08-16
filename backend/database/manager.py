import sqlite3
import os
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from ..models.player import Player
from ..models.team import Team
from ..models.fixture import Fixture
from ..config import Config

class DatabaseManager:
    """Manages all database operations for the FPL application"""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager with database path"""
        self.db_path = db_path or Config.DATABASE_PATH
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure the database file exists and has the correct schema"""
        if not os.path.exists(self.db_path):
            self._create_database()
        else:
            self._ensure_schema()
    
    def _create_database(self):
        """Create new database with schema"""
        with self._get_connection() as conn:
            self._create_tables(conn)
            print(f"Database created at {self.db_path}")
    
    def _ensure_schema(self):
        """Ensure database has the correct schema"""
        with self._get_connection() as conn:
            self._create_tables(conn)
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create all necessary tables if they don't exist"""
        cursor = conn.cursor()
        
        # Create players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                team TEXT NOT NULL,
                price REAL NOT NULL,
                chance_of_playing_next_round REAL DEFAULT 100.0,
                points_per_million REAL DEFAULT 0.0,
                total_points REAL DEFAULT 0.0,
                form REAL DEFAULT 0.0,
                ownership REAL DEFAULT 0.0,
                team_id INTEGER,
                gw1_points REAL DEFAULT 0.0,
                gw2_points REAL DEFAULT 0.0,
                gw3_points REAL DEFAULT 0.0,
                gw4_points REAL DEFAULT 0.0,
                gw5_points REAL DEFAULT 0.0,
                gw6_points REAL DEFAULT 0.0,
                gw7_points REAL DEFAULT 0.0,
                gw8_points REAL DEFAULT 0.0,
                gw9_points REAL DEFAULT 0.0,
                FOREIGN KEY (team_id) REFERENCES teams (id)
            )
        """)
        
        # Create teams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                short_name TEXT NOT NULL,
                code INTEGER NOT NULL,
                strength INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create fixtures table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fixtures (
                id INTEGER PRIMARY KEY,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_difficulty INTEGER NOT NULL,
                away_difficulty INTEGER NOT NULL,
                gameweek INTEGER NOT NULL
            )
        """)
        
        # Watchlist table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                player_id INTEGER PRIMARY KEY
            )
        """)
        
        # Create indexes for better performance (only if tables exist)
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_position ON players(position)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_team ON players(team)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_gameweek ON fixtures(gameweek)")
        except sqlite3.OperationalError:
            # Tables might not exist yet, skip index creation
            pass
        
        conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, timeout=Config.DATABASE_TIMEOUT)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get_connection(self):
        """Get a database connection (for direct operations)"""
        conn = sqlite3.connect(self.db_path, timeout=Config.DATABASE_TIMEOUT)
        conn.row_factory = sqlite3.Row
        return conn
    
    def bulk_insert_players(self, players_data: List[Dict]) -> int:
        """Efficiently insert multiple players using batch operations"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Use executemany for batch insertion
                cursor.executemany("""
                    INSERT INTO players (
                        name, position, team, price, total_points, 
                        form, ownership, team_id, gw1_points, gw2_points,
                        gw3_points, gw4_points, gw5_points, gw6_points,
                        gw7_points, gw8_points, gw9_points, chance_of_playing_next_round,
                        points_per_million
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    (
                        player['name'], player['position'], player['team'], 
                        player['price'], player['total_points'], player['form'],
                        player['ownership'], player['team_id'], player['gw1_points'],
                        player['gw2_points'], player['gw3_points'], player['gw4_points'],
                        player['gw5_points'], player['gw6_points'], player['gw7_points'],
                        player['gw8_points'], player['gw9_points'], 
                        player.get('chance_of_playing_next_round', 100),
                        player.get('points_per_million', 0.0)
                    ) for player in players_data
                ])
                
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Error in bulk insert: {e}")
            return 0
    
    # Player operations
    def get_all_players(self) -> List[Player]:
        """Get all players from database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, position, team, price, total_points, 
                       form, ownership, team_id, gw1_points, gw2_points, 
                       gw3_points, gw4_points, gw5_points, gw6_points, 
                       gw7_points, gw8_points, gw9_points, chance_of_playing_next_round,
                       points_per_million
                FROM players ORDER BY name
            """)
            rows = cursor.fetchall()
            return [Player.from_db_row(row) for row in rows]
    
    def get_players_by_position(self, position: str) -> List[Player]:
        """Get players by position"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM players WHERE position = ? ORDER BY name
            """, (position,))
            rows = cursor.fetchall()
            return [Player.from_db_row(row) for row in rows]
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """Get player by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, position, team, price, total_points, 
                       form, ownership, team_id, gw1_points, gw2_points, 
                       gw3_points, gw4_points, gw5_points, gw6_points, 
                       gw7_points, gw8_points, gw9_points, chance_of_playing_next_round,
                       points_per_million
                FROM players WHERE id = ?
            """, (player_id,))
            row = cursor.fetchone()
            return Player.from_db_row(row) if row else None
    
    def add_player(self, player: Player) -> bool:
        """Add a new player to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO players (
                        id, name, position, team, price, total_points, 
                        form, ownership, team_id, gw1_points, gw2_points, 
                        gw3_points, gw4_points, gw5_points, gw6_points,
                        gw7_points, gw8_points, gw9_points, chance_of_playing_next_round,
                        points_per_million
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player.id, player.name, player.position, player.team, player.price,
                    player.total_points, player.form, player.ownership, player.team_id,
                    player.gw1_points, player.gw2_points, player.gw3_points,
                    player.gw4_points, player.gw5_points, player.gw6_points,
                    player.gw7_points, player.gw8_points, player.gw9_points,
                    player.chance_of_playing_next_round, player.points_per_million
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding player: {e}")
            return False
    
    # Team operations
    def get_all_teams(self) -> List[Team]:
        """Get all teams from database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM teams ORDER BY name
            """)
            rows = cursor.fetchall()
            return [Team.from_db_row(row) for row in rows]
    
    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Get team by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM teams WHERE id = ?
            """, (team_id,))
            row = cursor.fetchone()
            return Team.from_db_row(row) if row else None
    
    def add_team(self, team: Team) -> bool:
        """Add a new team to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO teams (id, name, short_name, code, strength, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    team.id, team.name, team.short_name, team.code, team.strength, team.created_at
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding team: {e}")
            return False
    
    # Fixture operations
    def get_all_fixtures(self) -> List[Fixture]:
        """Get all fixtures from database.

        Handles both cases:
        - fixtures.home_team/away_team already store names
        - fixtures.home_team/away_team store numeric team IDs (as text)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    f.id,
                    COALESCE(ht.name, f.home_team) AS home_team,
                    COALESCE(at.name, f.away_team) AS away_team,
                    f.home_difficulty,
                    f.away_difficulty,
                    f.gameweek
                FROM fixtures f
                LEFT JOIN teams ht ON CAST(f.home_team AS INTEGER) = ht.id
                LEFT JOIN teams at ON CAST(f.away_team AS INTEGER) = at.id
                ORDER BY f.gameweek, home_team
                """
            )
            rows = cursor.fetchall()
            return [Fixture.from_db_row(row) for row in rows]
    
    def get_fixtures_by_gameweek(self, gameweek: int) -> List[Fixture]:
        """Get fixtures by gameweek with robust team name resolution."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    f.id,
                    COALESCE(ht.name, f.home_team) AS home_team,
                    COALESCE(at.name, f.away_team) AS away_team,
                    f.home_difficulty,
                    f.away_difficulty,
                    f.gameweek
                FROM fixtures f
                LEFT JOIN teams ht ON CAST(f.home_team AS INTEGER) = ht.id
                LEFT JOIN teams at ON CAST(f.away_team AS INTEGER) = at.id
                WHERE f.gameweek = ?
                ORDER BY home_team
                """,
                (gameweek,),
            )
            rows = cursor.fetchall()
            return [Fixture.from_db_row(row) for row in rows]
    
    def add_fixture(self, fixture: Fixture) -> bool:
        """Add a new fixture to database (expects team names)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO fixtures (
                        id, home_team, away_team, home_difficulty, away_difficulty, gameweek
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fixture.id,
                        fixture.home_team,
                        fixture.away_team,
                        fixture.home_difficulty,
                        fixture.away_difficulty,
                        fixture.gameweek,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding fixture: {e}")
            return False
    
    # Database maintenance
    def clear_all_data(self):
        """Clear all data from database (for testing/reset)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM players")
            cursor.execute("DELETE FROM teams")
            cursor.execute("DELETE FROM fixtures")
            conn.commit()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Count records in each table
            cursor.execute("SELECT COUNT(*) FROM players")
            player_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM teams")
            team_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM fixtures")
            fixture_count = cursor.fetchone()[0]
            
            return {
                'players': player_count,
                'teams': team_count,
                'fixtures': fixture_count,
                'database_path': self.db_path,
                'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
            }

    # Watchlist operations
    def get_watchlist_ids(self) -> List[int]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT player_id FROM watchlist')
            return [row[0] for row in cur.fetchall()]

    def add_to_watchlist(self, player_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute('INSERT OR IGNORE INTO watchlist (player_id) VALUES (?)', (player_id,))
                conn.commit()
                return True
        except Exception:
            return False

    def remove_from_watchlist(self, player_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute('DELETE FROM watchlist WHERE player_id = ?', (player_id,))
                conn.commit()
                return True
        except Exception:
            return False

    def get_watchlist_players(self) -> List[Player]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT p.id, p.name, p.position, p.team, p.price, p.total_points,
                       p.form, p.ownership, p.team_id, p.gw1_points, p.gw2_points, p.gw3_points,
                       p.gw4_points, p.gw5_points, p.gw6_points, p.gw7_points, p.gw8_points, p.gw9_points,
                       p.chance_of_playing_next_round, p.points_per_million
                FROM players p
                JOIN watchlist w ON w.player_id = p.id
                ORDER BY p.name
                """
            )
            return [Player.from_db_row(row) for row in cur.fetchall()]

    def is_on_watchlist(self, player_id: int) -> bool:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT 1 FROM watchlist WHERE player_id = ? LIMIT 1', (player_id,))
            return cur.fetchone() is not None
