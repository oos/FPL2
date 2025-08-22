import pytest
import tempfile
import os
from backend.app import create_app
from backend.database.manager import DatabaseManager
from backend.models.player import Player
from backend.models.team import Team
from backend.models.fixture import Fixture


@pytest.fixture(scope="function")
def app():
    """Create and configure a new app instance for each test function."""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'DATABASE_PATH': ':memory:',
        'DATABASE_TIMEOUT': 5
    })
    
    # Create tables and populate with test data
    with app.app_context():
        db_manager = DatabaseManager(':memory:')
        _populate_test_data(db_manager)
        # Update the app's db_manager to use the populated database
        app.db_manager = db_manager
    
    yield app


@pytest.fixture(scope="function")
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_manager():
    """Create a fresh in-memory database for each test."""
    db_manager = DatabaseManager(':memory:')
    return db_manager


def _populate_test_data(db_manager):
    """Populate database with test data."""
    # Create test teams
    teams = [
        Team(id=1, name="Arsenal", short_name="ARS", code=3, strength=85),
        Team(id=2, name="Chelsea", short_name="CHE", code=8, strength=80),
        Team(id=3, name="Liverpool", short_name="LIV", code=14, strength=88),
        Team(id=4, name="Manchester City", short_name="MCI", code=43, strength=90),
        Team(id=5, name="Manchester United", short_name="MUN", code=1, strength=82)
    ]
    
    for team in teams:
        db_manager.add_team(team)
    
            # Create test players
        players = [
            Player(
                id=1, name="Mohamed Salah", position="Midfielder", team="Liverpool",
                price=13.0, total_points=180.0, form=8.5, ownership=45.0,
                team_id=3, fpl_element_id=233, chance_of_playing_next_round=100.0, points_per_million=13.8
            ),
            Player(
                id=2, name="Erling Haaland", position="Forward", team="Manchester City",
                price=14.5, total_points=200.0, form=9.0, ownership=60.0,
                team_id=4, fpl_element_id=355, chance_of_playing_next_round=100.0, points_per_million=13.8
            ),
            Player(
                id=3, name="Bukayo Saka", position="Midfielder", team="Arsenal",
                price=8.5, total_points=150.0, form=7.5, ownership=35.0,
                team_id=1, fpl_element_id=388, chance_of_playing_next_round=100.0, points_per_million=17.6
            ),
            Player(
                id=4, name="Alisson", position="Goalkeeper", team="Liverpool",
                price=5.5, total_points=120.0, form=6.5, ownership=25.0,
                team_id=3, fpl_element_id=1, chance_of_playing_next_round=100.0, points_per_million=21.8
            ),
            Player(
                id=5, name="Virgil van Dijk", position="Defender", team="Liverpool",
                price=6.0, total_points=110.0, form=6.0, ownership=20.0,
                team_id=3, fpl_element_id=2, chance_of_playing_next_round=100.0, points_per_million=18.3
            )
        ]
    
    for player in players:
        db_manager.add_player(player)
    
    # Create test fixtures
    fixtures = [
        Fixture(
            id=1, home_team="Arsenal", away_team="Chelsea",
            home_difficulty=2, away_difficulty=3, gameweek=1
        ),
        Fixture(
            id=2, home_team="Liverpool", away_team="Manchester City",
            home_difficulty=4, away_difficulty=4, gameweek=1
        ),
        Fixture(
            id=3, home_team="Manchester United", away_team="Arsenal",
            home_difficulty=3, away_difficulty=2, gameweek=2
        )
    ]
    
    for fixture in fixtures:
        db_manager.add_fixture(fixture)


@pytest.fixture(scope="function")
def sample_player_data():
    """Sample player data for testing."""
    return {
        'id': 999,
        'name': 'Test Player',
        'position': 'Midfielder',
        'team': 'Test Team',
        'price': 8.0,
        'total_points': 100.0,
        'form': 7.0,
        'ownership': 15.0,
        'team_id': 1,
        'fpl_element_id': 999,
        'chance_of_playing_next_round': 100.0,
        'points_per_million': 12.5
    }


@pytest.fixture(scope="function")
def sample_team_data():
    """Sample team data for testing."""
    return {
        'id': 999,
        'name': 'Test Team',
        'short_name': 'TST',
        'code': 999,
        'strength': 75
    }
