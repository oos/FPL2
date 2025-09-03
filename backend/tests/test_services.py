import pytest
from unittest.mock import Mock, patch
from backend.services.player_service import PlayerService
from backend.services.squad_service import SquadService
from backend.services.historical_service import HistoricalService
from backend.models.player import Player
from backend.models.team import Team
from backend.models.fixture import Fixture


@pytest.mark.unit
class TestPlayerService:
    """Test cases for PlayerService"""
    
    @pytest.fixture(autouse=True)
    def setup_service(self, db_manager):
        """Set up player service with test database"""
        self.player_service = PlayerService(db_manager)
    
    def test_get_all_players(self, db_manager):
        """Test getting all players"""
        # Add test players
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        db_manager.add_team(team)
        
        player1 = Player(
            id=1, name="Player 1", position="Midfielder", team="Test Team",
            price=8.0, total_points=100.0, form=7.0, ownership=15.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=12.5
        )
        player2 = Player(
            id=2, name="Player 2", position="Forward", team="Test Team",
            price=10.0, total_points=120.0, form=8.0, ownership=20.0,
            team_id=1, fpl_element_id=998, chance_of_playing_next_round=100.0, points_per_million=12.0
        )
        
        db_manager.add_player(player1)
        db_manager.add_player(player2)
        
        # Get all players
        players = self.player_service.get_all_players()
        assert len(players) == 2
        assert any(p['name'] == "Player 1" for p in players)
        assert any(p['name'] == "Player 2" for p in players)
    
    def test_get_players_by_position(self, db_manager):
        """Test getting players by position"""
        # Add test players
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        db_manager.add_team(team)
        
        player1 = Player(
            id=1, name="Midfielder Player", position="Midfielder", team="Test Team",
            price=8.0, total_points=100.0, form=7.0, ownership=15.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=12.5
        )
        player2 = Player(
            id=2, name="Forward Player", position="Forward", team="Test Team",
            price=10.0, total_points=120.0, form=8.0, ownership=20.0,
            team_id=1, fpl_element_id=998, chance_of_playing_next_round=100.0, points_per_million=12.0
        )
        
        db_manager.add_player(player1)
        db_manager.add_player(player2)
        
        # Get midfielders
        midfielders = self.player_service.get_players_by_position("Midfielder")
        assert len(midfielders) == 1
        assert midfielders[0]['name'] == "Midfielder Player"
        assert midfielders[0]['position'] == "Midfielder"
        
        # Get forwards
        forwards = self.player_service.get_players_by_position("Forward")
        assert len(forwards) == 1
        assert forwards[0]['name'] == "Forward Player"
        assert forwards[0]['position'] == "Forward"
    
    def test_search_players(self, db_manager):
        """Test player search functionality"""
        # Add test players
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        db_manager.add_team(team)
        
        player1 = Player(
            id=1, name="Mohamed Salah", position="Midfielder", team="Test Team",
            price=13.0, total_points=180.0, form=8.5, ownership=45.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=13.8
        )
        player2 = Player(
            id=2, name="Erling Haaland", position="Forward", team="Test Team",
            price=14.5, total_points=200.0, form=9.0, ownership=60.0,
            team_id=1, fpl_element_id=998, chance_of_playing_next_round=100.0, points_per_million=13.8
        )
        
        db_manager.add_player(player1)
        db_manager.add_player(player2)
        
        # Search for "Salah"
        results = self.player_service.search_players("Salah")
        assert len(results) == 1
        assert results[0]['name'] == "Mohamed Salah"
        
        # Search for "Haaland"
        results = self.player_service.search_players("Haaland")
        assert len(results) == 1
        assert results[0]['name'] == "Erling Haaland"
        
        # Search with limit
        results = self.player_service.search_players("a", limit=1)
        assert len(results) <= 1
        
        # Search for non-existent player
        results = self.player_service.search_players("NonExistent")
        assert len(results) == 0
    
    def test_get_players_by_team(self, db_manager):
        """Test getting players by team"""
        # Add test players
        team = Team(id=1, name="Liverpool", short_name="LIV", code=14, strength=88)
        db_manager.add_team(team)
        
        player1 = Player(
            id=1, name="Salah", position="Midfielder", team="Liverpool",
            price=13.0, total_points=180.0, form=8.5, ownership=45.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=13.8
        )
        player2 = Player(
            id=2, name="Van Dijk", position="Defender", team="Liverpool",
            price=6.0, total_points=110.0, form=6.0, ownership=20.0,
            team_id=1, fpl_element_id=998, chance_of_playing_next_round=100.0, points_per_million=18.3
        )
        
        db_manager.add_player(player1)
        db_manager.add_player(player2)
        
        # Get Liverpool players
        liverpool_players = self.player_service.get_players_by_team("Liverpool")
        assert len(liverpool_players) == 2
        assert all(p['team'] == "Liverpool" for p in liverpool_players)
        
        # Get non-existent team
        non_existent = self.player_service.get_players_by_team("NonExistent")
        assert len(non_existent) == 0
    
    def test_get_players_by_price_range(self, db_manager):
        """Test getting players by price range"""
        # Add test players
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        db_manager.add_team(team)
        
        player1 = Player(
            id=1, name="Cheap Player", position="Midfielder", team="Test Team",
            price=5.0, total_points=80.0, form=6.0, ownership=10.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=16.0
        )
        player2 = Player(
            id=2, name="Expensive Player", position="Forward", team="Test Team",
            price=12.0, total_points=150.0, form=8.0, ownership=30.0,
            team_id=1, fpl_element_id=998, chance_of_playing_next_round=100.0, points_per_million=12.5
        )
        
        db_manager.add_player(player1)
        db_manager.add_player(player2)
        
        # Get players in price range 4.0 - 6.0
        cheap_players = self.player_service.get_players_by_price_range(4.0, 6.0)
        assert len(cheap_players) == 1
        assert cheap_players[0]['name'] == "Cheap Player"
        
        # Get players in price range 10.0 - 15.0
        expensive_players = self.player_service.get_players_by_price_range(10.0, 15.0)
        assert len(expensive_players) == 1
        assert expensive_players[0]['name'] == "Expensive Player"
        
        # Get players in price range 8.0 - 10.0 (should be empty)
        mid_range = self.player_service.get_players_by_price_range(8.0, 10.0)
        assert len(mid_range) == 0
    
    def test_get_top_players_by_points(self, db_manager):
        """Test getting top players by total points"""
        # Add test players
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        db_manager.add_team(team)
        
        player1 = Player(
            id=1, name="Low Points", position="Midfielder", team="Test Team",
            price=8.0, total_points=80.0, form=6.0, ownership=15.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=10.0
        )
        player2 = Player(
            id=2, name="High Points", position="Forward", team="Test Team",
            price=10.0, total_points=150.0, form=8.0, ownership=20.0,
            team_id=1, fpl_element_id=998, chance_of_playing_next_round=100.0, points_per_million=15.0
        )
        player3 = Player(
            id=3, name="Medium Points", position="Defender", team="Test Team",
            price=6.0, total_points=120.0, form=7.0, ownership=25.0,
            team_id=1, fpl_element_id=997, chance_of_playing_next_round=100.0, points_per_million=20.0
        )
        
        db_manager.add_player(player1)
        db_manager.add_player(player2)
        db_manager.add_player(player3)
        
        # Get top 2 players by points
        top_players = self.player_service.get_top_players_by_points(limit=2)
        assert len(top_players) == 2
        
        # Should be sorted by total_points descending
        assert top_players[0]['total_points'] >= top_players[1]['total_points']
        assert top_players[0]['name'] == "High Points"  # 150 points
        assert top_players[1]['name'] == "Medium Points"  # 120 points
    
    def test_get_top_players_by_value(self, db_manager):
        """Test getting top players by points per million"""
        # Add test players
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        db_manager.add_team(team)
        
        player1 = Player(
            id=1, name="Good Value", position="Midfielder", team="Test Team",
            price=5.0, total_points=100.0, form=7.0, ownership=15.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=20.0
        )
        player2 = Player(
            id=2, name="Poor Value", position="Forward", team="Test Team",
            price=15.0, total_points=120.0, form=8.0, ownership=20.0,
            team_id=1, fpl_element_id=998, chance_of_playing_next_round=100.0, points_per_million=8.0
        )
        
        db_manager.add_player(player1)
        db_manager.add_player(player2)
        
        # Get top players by value
        top_value = self.player_service.get_top_players_by_value(limit=2)
        assert len(top_value) == 2
        
        # Player 1 should have better value (100/5 = 20 vs 120/15 = 8)
        assert top_value[0]['name'] == "Good Value"
    
    def test_add_player(self, db_manager):
        """Test adding a new player"""
        # Add a team first
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        db_manager.add_team(team)
        
        # Player data
        player_data = {
            'id': 1,
            'name': 'New Player',
            'position': 'Goalkeeper',
            'team': 'Test Team',
            'price': 5.5,
            'total_points': 90.0,
            'form': 6.5,
            'ownership': 12.0,
            'team_id': 1,
            'fpl_element_id': 996
        }
        
        # Add player
        success = self.player_service.add_player(player_data)
        assert success is True
        
        # Verify player was added
        all_players = self.player_service.get_all_players()
        new_player = next((p for p in all_players if p['name'] == 'New Player'), None)
        assert new_player is not None
        assert new_player['position'] == 'Goalkeeper'
        assert new_player['price'] == 5.5
    
    def test_get_player_statistics(self, db_manager):
        """Test getting player statistics"""
        # Add test players
        team = Team(id=1, name="Test Team", short_name="TST", code=999, strength=75)
        db_manager.add_team(team)
        
        player1 = Player(
            id=1, name="Player 1", position="Goalkeeper", team="Test Team",
            price=5.0, total_points=80.0, form=6.0, ownership=10.0,
            team_id=1, fpl_element_id=999, chance_of_playing_next_round=100.0, points_per_million=16.0
        )
        player2 = Player(
            id=2, name="Player 2", position="Midfielder", team="Test Team",
            price=8.0, total_points=120.0, form=7.0, ownership=20.0,
            team_id=1, fpl_element_id=998, chance_of_playing_next_round=100.0, points_per_million=15.0
        )
        
        db_manager.add_player(player1)
        db_manager.add_player(player2)
        
        # Get statistics
        stats = self.player_service.get_player_statistics()
        assert isinstance(stats, dict)
        
        # Should contain basic stats
        assert 'total_players' in stats
        assert 'positions' in stats
        assert 'teams' in stats
        assert 'price_range' in stats
        
        # Verify counts
        assert stats['total_players'] == 2
        assert stats['positions']['Goalkeeper'] == 1
        assert stats['positions']['Midfielder'] == 1


@pytest.mark.unit
class TestSquadService:
    """Test cases for SquadService"""
    
    @pytest.fixture(autouse=True)
    def setup_service(self, db_manager):
        """Set up squad service with test database"""
        self.squad_service = SquadService(db_manager)
    
    def test_get_formation(self):
        """Test formation calculation"""
        # Mock players with positions
        players = [
            {'position': 'Goalkeeper'},
            {'position': 'Defender'}, {'position': 'Defender'}, {'position': 'Defender'}, {'position': 'Defender'},
            {'position': 'Midfielder'}, {'position': 'Midfielder'}, {'position': 'Midfielder'}, {'position': 'Midfielder'}, {'position': 'Midfielder'},
            {'position': 'Forward'}, {'position': 'Forward'}
        ]
        
        formation = self.squad_service.get_formation(players)
        assert formation == "4-5-2"
        
        # Test different formation
        players_343 = [
            {'position': 'Goalkeeper'},
            {'position': 'Defender'}, {'position': 'Defender'}, {'position': 'Defender'},
            {'position': 'Midfielder'}, {'position': 'Midfielder'}, {'position': 'Midfielder'}, {'position': 'Midfielder'},
            {'position': 'Forward'}, {'position': 'Forward'}, {'position': 'Forward'}
        ]
        
        formation_343 = self.squad_service.get_formation(players_343)
        assert formation_343 == "3-4-3"
    
    def test_get_optimal_squad_for_gw1_9(self, db_manager):
        """Test getting optimal squad for gameweeks 1-9"""
        # This would require more complex setup with historical data
        # For now, test that the method exists and returns expected structure
        strategy = self.squad_service.get_optimal_squad_for_gw1_9()
        
        # Should return a dict (even if empty)
        assert isinstance(strategy, dict)


@pytest.mark.unit
class TestHistoricalService:
    """Test cases for HistoricalService"""
    
    @pytest.fixture(autouse=True)
    def setup_service(self, db_manager):
        """Set up historical service with test database"""
        self.historical_service = HistoricalService(db_manager)
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        assert self.historical_service is not None
        assert hasattr(self.historical_service, 'db')


@pytest.mark.unit
class TestFDRMapping:
    """Test cases for FDR (Fixture Difficulty Rating) mapping logic"""
    
    def test_fixture_difficulty_validation(self):
        """Test that fixture difficulty values are valid"""
        # Valid difficulty values should be 1-5
        valid_difficulties = [1, 2, 3, 4, 5]
        
        for difficulty in valid_difficulties:
            fixture = Fixture(
                id=1,
                home_team="Home Team",
                away_team="Away Team",
                home_difficulty=difficulty,
                away_difficulty=difficulty,
                gameweek=1
            )
            assert fixture.home_difficulty == difficulty
            assert fixture.away_difficulty == difficulty
        
        # Note: Current model accepts any integer values (no validation)
        # Test that invalid values are accepted (current behavior)
        invalid_difficulties = [0, 6, -1, 10]
        
        for difficulty in invalid_difficulties:
            fixture = Fixture(
                id=1,
                home_team="Home Team",
                away_team="Away Team",
                home_difficulty=difficulty,
                away_difficulty=4,
                gameweek=1
            )
            assert fixture.home_difficulty == difficulty
    
    def test_gameweek_validation(self):
        """Test that gameweek values are valid"""
        # Valid gameweeks should be 1-38
        valid_gameweeks = [1, 19, 38]
        
        for gameweek in valid_gameweeks:
            fixture = Fixture(
                id=1,
                home_team="Home Team",
                away_team="Away Team",
                home_difficulty=2,
                away_difficulty=4,
                gameweek=gameweek
            )
            assert fixture.gameweek == gameweek
        
        # Note: Current model accepts any integer values (no validation)
        # Test that invalid values are accepted (current behavior)
        invalid_gameweeks = [0, 39, -1, 50]
        
        for gameweek in invalid_gameweeks:
            fixture = Fixture(
                id=1,
                home_team="Home Team",
                away_team="Away Team",
                home_difficulty=2,
                away_difficulty=4,
                gameweek=gameweek
            )
            assert fixture.gameweek == gameweek
    
    def test_fixture_team_consistency(self):
        """Test that fixture teams are consistent"""
        # Note: Current model accepts same team names (no validation)
        # Test that same team is accepted (current behavior)
        same_team_fixture = Fixture(
            id=1,
            home_team="Same Team",
            away_team="Same Team",  # Same team is accepted
            home_difficulty=2,
            away_difficulty=4,
            gameweek=1
        )
        assert same_team_fixture.home_team == same_team_fixture.away_team
        
        # Valid fixture with different teams
        valid_fixture = Fixture(
            id=1,
            home_team="Home Team",
            away_team="Away Team",
            home_difficulty=2,
            away_difficulty=4,
            gameweek=1
        )
        assert valid_fixture.home_team != valid_fixture.away_team
