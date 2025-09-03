import pytest
import tempfile
import os
from backend.database.manager import DatabaseManager
from backend.models.player import Player
from backend.models.team import Team
from backend.models.fixture import Fixture


@pytest.mark.database
class TestDatabaseManager:
    """Test cases for DatabaseManager"""
    
    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Set up temporary database for each test"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.db_manager = DatabaseManager(self.db_path)
        yield
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_database_creation(self):
        """Test database creation and table setup"""
        # Database should be created automatically
        assert os.path.exists(self.db_path)
        
        # Check that tables exist by querying them
        players = self.db_manager.get_all_players()
        teams = self.db_manager.get_all_teams()
        fixtures = self.db_manager.get_all_fixtures()
        
        # Tables should exist (even if empty)
        assert isinstance(players, list)
        assert isinstance(teams, list)
        assert isinstance(fixtures, list)
    
    def test_team_operations(self):
        """Test team CRUD operations"""
        # Create test team
        team = Team(
            id=1, name="Test Team", short_name="TST", 
            code=999, strength=75
        )
        
        # Add team
        success = self.db_manager.add_team(team)
        assert success is True
        
        # Get team by ID
        retrieved_team = self.db_manager.get_team_by_id(1)
        assert retrieved_team is not None
        assert retrieved_team.name == "Test Team"
        assert retrieved_team.short_name == "TST"
        assert retrieved_team.code == 999
        assert retrieved_team.strength == 75
        
        # Get all teams
        all_teams = self.db_manager.get_all_teams()
        assert len(all_teams) == 1
        assert all_teams[0].name == "Test Team"
    
    def test_player_operations(self):
        """Test player CRUD operations"""
        # First add a team (required for foreign key)
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        self.db_manager.add_team(team)
        
        # Create test player
        player = Player(
            id=1, name="Test Player", position="Midfielder", team="Test Team",
            price=8.0, total_points=100.0, form=7.0, ownership=15.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=12.5
        )
        
        # Add player
        success = self.db_manager.add_player(player)
        assert success is True
        
        # Get player by ID
        retrieved_player = self.db_manager.get_player_by_id(1)
        assert retrieved_player is not None
        assert retrieved_player.name == "Test Player"
        assert retrieved_player.position == "Midfielder"
        assert retrieved_player.team == "Test Team"
        assert retrieved_player.price == 8.0
        assert retrieved_player.total_points == 100.0
        assert retrieved_player.form == 7.0
        assert retrieved_player.ownership == 15.0
        assert retrieved_player.team_id == 1
        assert retrieved_player.fpl_element_id == 999
        
        # Get player by FPL element ID
        fpl_player = self.db_manager.get_player_by_fpl_element_id(999)
        assert fpl_player is not None
        assert fpl_player.id == 1
        
        # Get players by position
        midfielders = self.db_manager.get_players_by_position("Midfielder")
        assert len(midfielders) == 1
        assert midfielders[0].name == "Test Player"
        
        # Get all players
        all_players = self.db_manager.get_all_players()
        assert len(all_players) == 1
        assert all_players[0].name == "Test Player"
    
    def test_fixture_operations(self):
        """Test fixture CRUD operations"""
        # Create test fixture
        fixture = Fixture(
            id=1, home_team="Home Team", away_team="Away Team",
            home_difficulty=2, away_difficulty=4, gameweek=1
        )
        
        # Add fixture
        success = self.db_manager.add_fixture(fixture)
        assert success is True
        
        # Get all fixtures
        all_fixtures = self.db_manager.get_all_fixtures()
        assert len(all_fixtures) == 1
        assert all_fixtures[0].home_team == "Home Team"
        assert all_fixtures[0].away_team == "Away Team"
        assert all_fixtures[0].home_difficulty == 2
        assert all_fixtures[0].away_difficulty == 4
        assert all_fixtures[0].gameweek == 1
        
        # Get fixtures by gameweek
        gw1_fixtures = self.db_manager.get_fixtures_by_gameweek(1)
        assert len(gw1_fixtures) == 1
        assert gw1_fixtures[0].home_team == "Home Team"
    
    def test_bulk_operations(self):
        """Test bulk operations"""
        # Add a team first
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        self.db_manager.add_team(team)
        
        # Create multiple players
        players_data = [
            {
                'name': 'Player 1', 'position': 'Goalkeeper', 'team': 'Test Team',
                'price': 5.0, 'total_points': 80.0, 'form': 6.0, 'ownership': 10.0,
                'team_id': 1, 'gw1_points': 6.0, 'gw2_points': 7.0, 'gw3_points': 8.0,
                'gw4_points': 6.0, 'gw5_points': 7.0, 'gw6_points': 8.0, 'gw7_points': 6.0,
                'gw8_points': 7.0, 'gw9_points': 8.0
            },
            {
                'name': 'Player 2', 'position': 'Defender', 'team': 'Test Team',
                'price': 6.0, 'total_points': 90.0, 'form': 7.0, 'ownership': 15.0,
                'team_id': 1, 'gw1_points': 7.0, 'gw2_points': 8.0, 'gw3_points': 9.0,
                'gw4_points': 7.0, 'gw5_points': 8.0, 'gw6_points': 9.0, 'gw7_points': 7.0,
                'gw8_points': 8.0, 'gw9_points': 9.0
            }
        ]
        
        # Bulk insert
        inserted_count = self.db_manager.bulk_insert_players(players_data)
        assert inserted_count == 2
        
        # Verify players were inserted
        all_players = self.db_manager.get_all_players()
        assert len(all_players) == 2
        
        # Check specific players
        player_names = [p.name for p in all_players]
        assert 'Player 1' in player_names
        assert 'Player 2' in player_names
    
    def test_watchlist_operations(self):
        """Test watchlist operations"""
        # Add a team and player first
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        self.db_manager.add_team(team)
        
        player = Player(
            id=1, name="Test Player", position="Midfielder", team="Test Team",
            price=8.0, total_points=100.0, form=7.0, ownership=15.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=12.5
        )
        self.db_manager.add_player(player)
        
        # Test watchlist operations
        # Add to watchlist
        success = self.db_manager.add_to_watchlist(1)
        assert success is True
        
        # Check if on watchlist
        is_on_watchlist = self.db_manager.is_on_watchlist(1)
        assert is_on_watchlist is True
        
        # Get watchlist IDs
        watchlist_ids = self.db_manager.get_watchlist_ids()
        assert 1 in watchlist_ids
        
        # Get watchlist players
        watchlist_players = self.db_manager.get_watchlist_players()
        assert len(watchlist_players) == 1
        assert watchlist_players[0].name == "Test Player"
        
        # Remove from watchlist
        success = self.db_manager.remove_from_watchlist(1)
        assert success is True
        
        # Check if removed
        is_on_watchlist = self.db_manager.is_on_watchlist(1)
        assert is_on_watchlist is False
    
    def test_historical_operations(self):
        """Test historical data operations"""
        # Record historical run
        self.db_manager.record_historical_run("2024/25")
        
        # Get last run
        last_run = self.db_manager.get_last_historical_run("2024/25")
        assert last_run is not None
        
        # Test historical player stats
        stats_data = [
            {
                'fpl_element_id': 999,
                'season': '2024/25',
                'gameweek': 1,
                'minutes': 90,
                'total_points': 8,
                'goals_scored': 1,
                'assists': 0,
                'clean_sheets': 0,
                'raw_json': '{"test": "data"}'
            }
        ]
        
        # Upsert historical stats
        inserted = self.db_manager.upsert_historical_player_stats(stats_data)
        assert inserted > 0
        
        # Get historical summary
        summary = self.db_manager.get_historical_summary("2024/25")
        assert summary['season'] == "2024/25"
        assert summary['total_rows'] > 0
        
        # Get gameweek stats
        gw_stats = self.db_manager.get_historical_gw_stats("2024/25", 1)
        assert len(gw_stats) > 0
        assert gw_stats[0]['fpl_element_id'] == 999
        assert gw_stats[0]['total_points'] == 8
    
    def test_user_profile_operations(self):
        """Test user profile operations"""
        # Save user profile
        profile_id = self.db_manager.save_user_profile(
            fpl_team_id=12345,
            team_name="My FPL Team",
            manager_name="Test Manager"
        )
        assert profile_id is not None
        
        # Get user profile
        profile = self.db_manager.get_user_profile(12345)
        assert profile is not None
        assert profile['fpl_team_id'] == 12345
        assert profile['team_name'] == "My FPL Team"
        assert profile['manager_name'] == "Test Manager"
        
        # Get all profiles
        all_profiles = self.db_manager.get_all_user_profiles()
        assert len(all_profiles) == 1
        assert all_profiles[0]['fpl_team_id'] == 12345
        
        # Add a player first (required for squad operations)
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        self.db_manager.add_team(team)
        
        player = Player(
            id=1, name="Test Player", position="Midfielder", team="Test Team",
            price=8.0, total_points=100.0, form=7.0, ownership=15.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=12.5
        )
        self.db_manager.add_player(player)
        
        # Test squad operations
        squad_data = [
            {
                'player_id': 1,
                'position': 'GKP',
                'is_captain': False,
                'is_vice_captain': False,
                'is_bench': False,
                'transfer_in': False,
                'transfer_out': False
            }
        ]
        
        self.db_manager.save_user_squad(12345, 1, squad_data)
        
        # Get squad
        squad = self.db_manager.get_user_squad(12345, 1)
        assert len(squad) == 1
        
        # Test league standings
        standing_data = {
            'total_points': 100,
            'gameweek_points': 8,
            'overall_rank': 50000,
            'gameweek_rank': 25000,
            'transfers_made': 1,
            'transfer_cost': 4
        }
        
        self.db_manager.save_user_league_standing(12345, 1, standing_data)
        
        # Get standings
        standings = self.db_manager.get_user_league_standings(12345)
        assert len(standings) == 1
        assert standings[0]['total_points'] == 100
        
        # Clean up
        self.db_manager.delete_user_profile(12345)
        profiles_after = self.db_manager.get_all_user_profiles()
        assert len(profiles_after) == 0
    
    def test_database_statistics(self):
        """Test database statistics"""
        # Add some test data first
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        self.db_manager.add_team(team)
        
        player = Player(
            id=1, name="Test Player", position="Midfielder", team="Test Team",
            price=8.0, total_points=100.0, form=7.0, ownership=15.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=12.5
        )
        self.db_manager.add_player(player)
        
        fixture = Fixture(
            id=1, home_team="Home Team", away_team="Away Team",
            home_difficulty=2, away_difficulty=4, gameweek=1
        )
        self.db_manager.add_fixture(fixture)
        
        # Get database stats
        stats = self.db_manager.get_database_stats()
        assert stats['players'] == 1
        assert stats['teams'] == 1
        assert stats['fixtures'] == 1
        assert stats['database_path'] == self.db_path
        assert stats['database_size_mb'] > 0
    
    def test_database_cleanup(self):
        """Test database cleanup operations"""
        # Add some test data
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        self.db_manager.add_team(team)
        
        player = Player(
            id=1, name="Test Player", position="Midfielder", team="Test Team",
            price=8.0, total_points=100.0, form=7.0, ownership=15.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=12.5
        )
        self.db_manager.add_player(player)
        
        # Verify data exists
        assert len(self.db_manager.get_all_teams()) == 1
        assert len(self.db_manager.get_all_players()) == 1
        
        # Clear all data
        self.db_manager.clear_all_data()
        
        # Verify data is cleared
        assert len(self.db_manager.get_all_teams()) == 0
        assert len(self.db_manager.get_all_players()) == 0
        
        # Clear historical data
        self.db_manager.clear_historical_data()
        # Should not raise an error even if tables don't exist
    
    def test_database_connection_management(self):
        """Test database connection management"""
        # Test context manager
        with self.db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
        
        # Test direct connection
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
        finally:
            conn.close()
    
    def test_fixture_team_name_resolution(self):
        """Test fixture team name resolution with both string and numeric team IDs"""
        # Add teams
        team1 = Team(id=1, name="Arsenal", short_name="ARS", code=3, strength=85)
        team2 = Team(id=2, name="Chelsea", short_name="CHE", code=8, strength=80)
        self.db_manager.add_team(team1)
        self.db_manager.add_team(team2)
        
        # Test fixture with team names (string)
        fixture1 = Fixture(
            id=1, home_team="Arsenal", away_team="Chelsea",
            home_difficulty=2, away_difficulty=3, gameweek=1
        )
        self.db_manager.add_fixture(fixture1)
        
        # Test fixture with team IDs (numeric as text)
        fixture2 = Fixture(
            id=2, home_team="1", away_team="2",  # Team IDs as strings
            home_difficulty=3, away_difficulty=4, gameweek=2
        )
        self.db_manager.add_fixture(fixture2)
        
        # Get all fixtures - should resolve team names correctly
        all_fixtures = self.db_manager.get_all_fixtures()
        assert len(all_fixtures) == 2
        
        # First fixture should have team names
        assert all_fixtures[0].home_team == "Arsenal"
        assert all_fixtures[0].away_team == "Chelsea"
        
        # Second fixture should have resolved team names
        assert all_fixtures[1].home_team == "Arsenal"
        assert all_fixtures[1].away_team == "Chelsea"
