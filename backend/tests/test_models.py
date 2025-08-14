import unittest
from ..models.player import Player
from ..models.team import Team
from ..models.fixture import Fixture

class TestPlayerModel(unittest.TestCase):
    """Test cases for Player model"""
    
    def setUp(self):
        """Set up test data"""
        self.player_data = {
            'id': 1,
            'name': 'Test Player',
            'position': 'Midfielder',
            'team': 'Test Team',
            'price': 8.5,
            'chance_of_playing_next_round': 90.0,
            'points_per_million': 75.0,
            'total_points': 150.0,
            'form': 7.5,
            'ownership': 25.0,
            'team_id': 1,
            'gw1_points': 8.0,
            'gw2_points': 7.0,
            'gw3_points': 9.0,
            'gw4_points': 6.0,
            'gw5_points': 8.0,
            'gw6_points': 7.0,
            'gw7_points': 9.0,
            'gw8_points': 8.0,
            'gw9_points': 7.0
        }
    
    def test_player_creation(self):
        """Test creating a Player instance"""
        player = Player(**self.player_data)
        self.assertEqual(player.name, 'Test Player')
        self.assertEqual(player.position, 'Midfielder')
        self.assertEqual(player.price, 8.5)
    
    def test_player_to_dict(self):
        """Test Player.to_dict() method"""
        player = Player(**self.player_data)
        player_dict = player.to_dict()
        self.assertEqual(player_dict['name'], 'Test Player')
        self.assertEqual(player_dict['position'], 'Midfielder')
        self.assertEqual(len(player_dict), 20)  # All fields should be present
    
    def test_player_from_db_row(self):
        """Test Player.from_db_row() method"""
        db_row = (1, 'Test Player', 'Midfielder', 'Test Team', 8.5, 90.0, 75.0, 150.0, 7.5, 25.0, 1, 8.0, 7.0, 9.0, 6.0, 8.0, 7.0, 9.0, 8.0, 7.0)
        player = Player.from_db_row(db_row)
        self.assertEqual(player.name, 'Test Player')
        self.assertEqual(player.position, 'Midfielder')

class TestTeamModel(unittest.TestCase):
    """Test cases for Team model"""
    
    def setUp(self):
        """Set up test data"""
        self.team_data = {
            'id': 1,
            'name': 'Test Team',
            'short_name': 'TST',
            'code': 100,
            'strength': 80,
            'created_at': '2024-01-01'
        }
    
    def test_team_creation(self):
        """Test creating a Team instance"""
        team = Team(**self.team_data)
        self.assertEqual(team.name, 'Test Team')
        self.assertEqual(team.short_name, 'TST')
        self.assertEqual(team.code, 100)
    
    def test_team_to_dict(self):
        """Test Team.to_dict() method"""
        team = Team(**self.team_data)
        team_dict = team.to_dict()
        self.assertEqual(team_dict['name'], 'Test Team')
        self.assertEqual(team_dict['code'], 100)

class TestFixtureModel(unittest.TestCase):
    """Test cases for Fixture model"""
    
    def setUp(self):
        """Set up test data"""
        self.fixture_data = {
            'id': 1,
            'home_team': 'Home Team',
            'away_team': 'Away Team',
            'home_difficulty': 2,
            'away_difficulty': 4,
            'gameweek': 1
        }
    
    def test_fixture_creation(self):
        """Test creating a Fixture instance"""
        fixture = Fixture(**self.fixture_data)
        self.assertEqual(fixture.home_team, 'Home Team')
        self.assertEqual(fixture.away_team, 'Away Team')
        self.assertEqual(fixture.gameweek, 1)
    
    def test_fixture_to_dict(self):
        """Test Fixture.to_dict() method"""
        fixture = Fixture(**self.fixture_data)
        fixture_dict = fixture.to_dict()
        self.assertEqual(fixture_dict['home_team'], 'Home Team')
        self.assertEqual(fixture_dict['away_difficulty'], 4)

if __name__ == '__main__':
    unittest.main()
