import sqlite3
import os
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from backend.models.player import Player
from backend.models.team import Team
from backend.models.fixture import Fixture
from backend.config import Config

class DatabaseManager:
    """Manages all database operations for the FPL application"""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager with database path"""
        self.db_path = db_path or Config.DATABASE_PATH
        self._memory_connection = None  # For in-memory databases
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure the database file exists and has the correct schema"""
        if self.db_path == ':memory:':
            # For in-memory databases, create persistent connection and schema
            self._memory_connection = sqlite3.connect(':memory:', timeout=Config.DATABASE_TIMEOUT)
            self._memory_connection.row_factory = sqlite3.Row
            self._create_tables(self._memory_connection)
            print(f"Database created at {self.db_path}")
        elif not os.path.exists(self.db_path):
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
                fpl_element_id INTEGER,
                FOREIGN KEY (team_id) REFERENCES teams (id)
            )
        """)

        # Backward-compatible migration: add fpl_element_id if missing
        try:
            cursor.execute("PRAGMA table_info(players)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'fpl_element_id' not in cols:
                cursor.execute("ALTER TABLE players ADD COLUMN fpl_element_id INTEGER")
        except Exception:
            pass
        
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

        # Historical run logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season TEXT NOT NULL,
                run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Historical player stats (by FPL element id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fpl_element_id INTEGER NOT NULL,
                season TEXT NOT NULL,
                gameweek INTEGER NOT NULL,
                minutes INTEGER DEFAULT 0,
                total_points INTEGER DEFAULT 0,
                goals_scored INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                clean_sheets INTEGER DEFAULT 0,
                raw_json TEXT,
                UNIQUE(fpl_element_id, season, gameweek)
            )
        """)
        
        # Add user_profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fpl_team_id INTEGER UNIQUE NOT NULL,
                team_name TEXT,
                manager_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add user_squads table for storing live squad data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_squads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fpl_team_id INTEGER NOT NULL,
                gameweek INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                position TEXT NOT NULL,
                is_captain BOOLEAN DEFAULT FALSE,
                is_vice_captain BOOLEAN DEFAULT FALSE,
                is_bench BOOLEAN DEFAULT FALSE,
                bench_position INTEGER,
                transfer_in BOOLEAN DEFAULT FALSE,
                transfer_out BOOLEAN DEFAULT FALSE,
                actual_points INTEGER DEFAULT 0,
                multiplier INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fpl_team_id) REFERENCES user_profiles (fpl_team_id),
                FOREIGN KEY (player_id) REFERENCES players (id),
                UNIQUE(fpl_team_id, gameweek, player_id)
            )
        ''')
        
        # Add columns to existing table if they don't exist (for database migration)
        try:
            cursor.execute('ALTER TABLE user_squads ADD COLUMN actual_points INTEGER DEFAULT 0')
        except:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE user_squads ADD COLUMN multiplier INTEGER DEFAULT 1')
        except:
            pass  # Column already exists
        
        # Add user_league_standings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_league_standings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fpl_team_id INTEGER NOT NULL,
                gameweek INTEGER NOT NULL,
                total_points INTEGER DEFAULT 0,
                gameweek_points INTEGER DEFAULT 0,
                overall_rank INTEGER,
                gameweek_rank INTEGER,
                transfers_made INTEGER DEFAULT 0,
                transfer_cost INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fpl_team_id) REFERENCES user_profiles (fpl_team_id),
                UNIQUE(fpl_team_id, gameweek)
            )
        ''')
        
        # Create indexes for better performance (only if tables exist)
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_position ON players(position)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_team ON players(team)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_gameweek ON fixtures(gameweek)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_fpl_elem ON players(fpl_element_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_stats_elem ON historical_player_stats(fpl_element_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_stats_season_gw ON historical_player_stats(season, gameweek)")
        except sqlite3.OperationalError:
            # Tables might not exist yet, skip index creation
            pass

        # Add raw_json column if missing (migration)
        try:
            cursor.execute("PRAGMA table_info(historical_player_stats)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'raw_json' not in cols:
                cursor.execute("ALTER TABLE historical_player_stats ADD COLUMN raw_json TEXT")
        except Exception:
            pass
        
        conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        if self.db_path == ':memory:' and self._memory_connection:
            # Use persistent connection for in-memory database
            yield self._memory_connection
        else:
            conn = sqlite3.connect(self.db_path, timeout=Config.DATABASE_TIMEOUT)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
    
    def get_connection(self):
        """Get a database connection (for direct operations)"""
        if self.db_path == ':memory:' and self._memory_connection:
            return self._memory_connection
        else:
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
                       points_per_million, fpl_element_id
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
                       points_per_million, fpl_element_id
                FROM players WHERE id = ?
            """, (player_id,))
            row = cursor.fetchone()
            return Player.from_db_row(row) if row else None
    
    def get_player_by_fpl_element_id(self, fpl_element_id: int) -> Optional[Player]:
        """Get player by FPL element ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, position, team, price, total_points, 
                       form, ownership, team_id, gw1_points, gw2_points, 
                       gw3_points, gw4_points, gw5_points, gw6_points, 
                       gw7_points, gw8_points, gw9_points, chance_of_playing_next_round,
                       points_per_million, fpl_element_id
                FROM players WHERE fpl_element_id = ?
            """, (fpl_element_id,))
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
                        points_per_million, fpl_element_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player.id, player.name, player.position, player.team, player.price,
                    player.total_points, player.form, player.ownership, player.team_id,
                    player.gw1_points, player.gw2_points, player.gw3_points,
                    player.gw4_points, player.gw5_points, player.gw6_points,
                    player.gw7_points, player.gw8_points, player.gw9_points,
                    player.chance_of_playing_next_round, player.points_per_million, player.fpl_element_id
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

    def clear_historical_data(self):
        """Delete all rows from historical tables without dropping them."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM historical_player_stats")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("DELETE FROM historical_runs")
            except sqlite3.OperationalError:
                pass
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
            try:
                cursor.execute("SELECT COUNT(*) FROM historical_player_stats")
                hist_count = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                hist_count = 0
            
            return {
                'players': player_count,
                'teams': team_count,
                'fixtures': fixture_count,
                'historical_player_stats': hist_count,
                'database_path': self.db_path,
                'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
            }

    # Historical operations
    def record_historical_run(self, season: str) -> None:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO historical_runs (season) VALUES (?)", (season,))
            conn.commit()

    def get_last_historical_run(self, season: str) -> Optional[str]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT run_at FROM historical_runs WHERE season = ? ORDER BY run_at DESC LIMIT 1", (season,))
            row = cur.fetchone()
            return row[0] if row else None

    def get_max_recorded_gw(self, season: str) -> int:
        with self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT COALESCE(MAX(gameweek), 0) FROM historical_player_stats WHERE season = ?", (season,))
                val = cur.fetchone()[0]
                return int(val or 0)
            except sqlite3.OperationalError:
                return 0

    def upsert_historical_player_stats(self, rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0
        inserted = 0
        with self._get_connection() as conn:
            cur = conn.cursor()
            for r in rows:
                try:
                    cur.execute(
                        """
                        INSERT OR IGNORE INTO historical_player_stats
                        (fpl_element_id, season, gameweek, minutes, total_points, goals_scored, assists, clean_sheets, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            int(r.get('fpl_element_id')), r.get('season'), int(r.get('gameweek')),
                            int(r.get('minutes', 0)), int(r.get('total_points', 0)),
                            int(r.get('goals_scored', 0)), int(r.get('assists', 0)), int(r.get('clean_sheets', 0)),
                            r.get('raw_json')
                        )
                    )
                    inserted += cur.rowcount
                except Exception as e:
                    print(f"hist upsert error for elem {r.get('fpl_element_id')} gw {r.get('gameweek')}: {e}")
            conn.commit()
        return inserted

    def get_historical_summary(self, season: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT COUNT(*) FROM historical_player_stats WHERE season = ?", (season,))
                total_rows = cur.fetchone()[0]
                cur.execute("SELECT gameweek, COUNT(*) FROM historical_player_stats WHERE season = ? GROUP BY gameweek ORDER BY gameweek", (season,))
                by_gw = [{'gameweek': r[0], 'rows': r[1]} for r in cur.fetchall()]
                last_run = self.get_last_historical_run(season)
                return {'season': season, 'total_rows': total_rows, 'by_gw': by_gw, 'last_run': last_run}
            except sqlite3.OperationalError:
                return {'season': season, 'total_rows': 0, 'by_gw': [], 'last_run': None}

    def get_historical_gw_stats(self, season: str, gameweek: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT fpl_element_id, minutes, total_points, goals_scored, assists, clean_sheets, raw_json
                FROM historical_player_stats
                WHERE season = ? AND gameweek = ?
                ORDER BY total_points DESC, minutes DESC
                """,
                (season, gameweek),
            )
            rows = cur.fetchall()
            return [
                {
                    'fpl_element_id': row[0],
                    'minutes': row[1],
                    'total_points': row[2],
                    'goals_scored': row[3],
                    'assists': row[4],
                    'clean_sheets': row[5],
                    'raw_json': row[6] if len(row) > 6 else None,
                }
                for row in rows
            ]

    def get_historical_totals_for_season(self, season: str) -> Dict[int, Dict[str, Any]]:
        """Return mapping fpl_element_id -> {'total_points_sum': int, 'gw1_points': int}"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT fpl_element_id,
                           COALESCE(SUM(total_points),0) AS total_sum,
                           COALESCE(MAX(CASE WHEN gameweek=1 THEN total_points END),0) AS gw1
                    FROM historical_player_stats
                    WHERE season = ?
                    GROUP BY fpl_element_id
                    """,
                    (season,),
                )
                result: Dict[int, Dict[str, Any]] = {}
                for row in cur.fetchall():
                    result[int(row[0])] = {
                        'total_points_sum': int(row[1] or 0),
                        'gw1_points': int(row[2] or 0),
                    }
                return result
            except sqlite3.OperationalError:
                return {}

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
                       p.chance_of_playing_next_round, p.points_per_million, p.fpl_element_id
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

    # Players mapping helpers
    def set_player_fpl_element_id(self, player_id: int, fpl_element_id: int) -> None:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute('UPDATE players SET fpl_element_id = ? WHERE id = ?', (fpl_element_id, player_id))
            conn.commit()
    
    # User Profile Management
    def save_user_profile(self, fpl_team_id, team_name=None, manager_name=None):
        """Save or update user profile with FPL team ID"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO user_profiles (fpl_team_id, team_name, manager_name, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (fpl_team_id, team_name, manager_name))
            conn.commit()
            return cur.lastrowid
    
    def get_user_profile(self, fpl_team_id):
        """Get user profile by FPL team ID"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT fpl_team_id, team_name, manager_name, created_at, updated_at
                FROM user_profiles 
                WHERE fpl_team_id = ?
            ''', (fpl_team_id,))
            row = cur.fetchone()
            if row:
                return {
                    'fpl_team_id': row[0],
                    'team_name': row[1],
                    'manager_name': row[2],
                    'created_at': row[3],
                    'updated_at': row[4]
                }
            return None
    
    def get_all_user_profiles(self):
        """Get all user profiles"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT fpl_team_id, team_name, manager_name, created_at, updated_at
                FROM user_profiles 
                ORDER BY created_at DESC
            ''')
            return [{
                'fpl_team_id': row[0],
                'team_name': row[1],
                'manager_name': row[2],
                'created_at': row[3],
                'updated_at': row[4]
            } for row in cur.fetchall()]
    
    def save_user_squad(self, fpl_team_id, gameweek, squad_data):
        """Save user squad data for a specific gameweek"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            # Clear existing squad for this gameweek
            cur.execute('''
                DELETE FROM user_squads 
                WHERE fpl_team_id = ? AND gameweek = ?
            ''', (fpl_team_id, gameweek))
            
            # Insert new squad data
            for player in squad_data:
                cur.execute('''
                    INSERT INTO user_squads (
                        fpl_team_id, gameweek, player_id, position, 
                        is_captain, is_vice_captain, is_bench, bench_position,
                        transfer_in, transfer_out, actual_points, multiplier
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    fpl_team_id, gameweek, player['player_id'], player['position'],
                    player.get('is_captain', False), player.get('is_vice_captain', False),
                    player.get('is_bench', False), player.get('bench_position'),
                    player.get('transfer_in', False), player.get('transfer_out', False),
                    player.get('actual_points', 0), player.get('multiplier', 1)
                ))
            
            conn.commit()
    
    def get_user_squad(self, fpl_team_id, gameweek):
        """Get user squad for a specific gameweek"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT us.*, p.name, p.team, p.position as player_position, p.price,
                       p.gw1_points, p.gw2_points, p.gw3_points, p.gw4_points, p.gw5_points,
                       p.gw6_points, p.gw7_points, p.gw8_points, p.gw9_points, p.total_points
                FROM user_squads us
                JOIN players p ON us.player_id = p.id
                WHERE us.fpl_team_id = ? AND us.gameweek = ?
                ORDER BY 
                    CASE WHEN us.is_bench = 0 THEN 1 ELSE 2 END,
                    us.bench_position,
                    us.position
            ''', (fpl_team_id, gameweek))
            
            squad = []
            for row in cur.fetchall():
                squad.append({
                    'id': row[0],
                    'fpl_team_id': row[1],
                    'gameweek': row[2],
                    'player_id': row[3],
                    'position': row[4],
                    'is_captain': bool(row[5]),
                    'is_vice_captain': bool(row[6]),
                    'is_bench': bool(row[7]),
                    'bench_position': row[8],
                    'transfer_in': bool(row[9]),
                    'transfer_out': bool(row[10]),
                    'actual_points': row[11] or 0,  # New column
                    'multiplier': row[12] or 1,     # New column
                    'web_name': row[13],  # This is actually p.name (shifted by 2)
                    'team': row[14],
                    'player_position': row[15],
                    'price': row[16],
                    'gw1_points': row[17] or 0.0,
                    'gw2_points': row[18] or 0.0,
                    'gw3_points': row[19] or 0.0,
                    'gw4_points': row[20] or 0.0,
                    'gw5_points': row[21] or 0.0,
                    'gw6_points': row[22] or 0.0,
                    'gw7_points': row[23] or 0.0,
                    'gw8_points': row[24] or 0.0,
                    'gw9_points': row[25] or 0.0,
                    'total_points': row[26] or 0.0
                })
            
            return squad
    
    def save_user_league_standing(self, fpl_team_id, gameweek, standing_data):
        """Save user league standing for a specific gameweek"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO user_league_standings (
                    fpl_team_id, gameweek, total_points, gameweek_points,
                    overall_rank, gameweek_rank, transfers_made, transfer_cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fpl_team_id, gameweek, standing_data['total_points'], 
                standing_data['gameweek_points'], standing_data.get('overall_rank'),
                standing_data.get('gameweek_rank'), standing_data.get('transfers_made', 0),
                standing_data.get('transfer_cost', 0)
            ))
            conn.commit()
    
    def get_user_league_standings(self, fpl_team_id):
        """Get user league standings across all gameweeks"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT gameweek, total_points, gameweek_points, overall_rank, 
                       gameweek_rank, transfers_made, transfer_cost
                FROM user_league_standings 
                WHERE fpl_team_id = ?
                ORDER BY gameweek
            ''', (fpl_team_id,))
            
            return [{
                'gameweek': row[0],
                'total_points': row[1],
                'gameweek_points': row[2],
                'overall_rank': row[3],
                'gameweek_rank': row[4],
                'transfers_made': row[5],
                'transfer_cost': row[6]
            } for row in cur.fetchall()]
    
    def delete_user_profile(self, fpl_team_id):
        """Delete a user profile and all related data"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            # Delete related data first (due to foreign key constraints)
            cur.execute('DELETE FROM user_squads WHERE fpl_team_id = ?', (fpl_team_id,))
            cur.execute('DELETE FROM user_league_standings WHERE fpl_team_id = ?', (fpl_team_id,))
            
            # Finally delete the profile
            cur.execute('DELETE FROM user_profiles WHERE fpl_team_id = ?', (fpl_team_id,))
            
            conn.commit()
            return cur.rowcount > 0
