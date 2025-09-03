import pytest
import json
from backend.app import create_app


@pytest.mark.api
class TestAPIEndpoints:
    """Test all API endpoints comprehensively"""
    

    
    def test_api_players(self, client):
        """Test /api/players endpoint"""
        resp = client.get("/api/players")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Test required fields
        required_fields = [
            "id", "name", "position", "team", "price", "total_points",
            "form", "ownership", "team_id", "fpl_element_id"
        ]
        for field in required_fields:
            assert field in data[0], f"Missing field: {field}"
        
        # Test data types
        assert isinstance(data[0]['id'], int)
        assert isinstance(data[0]['name'], str)
        assert isinstance(data[0]['price'], float)
        assert isinstance(data[0]['total_points'], float)
    
    def test_api_players_by_position(self, client):
        """Test /api/players/<position> endpoint"""
        positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
        
        for position in positions:
            resp = client.get(f"/api/players/{position}")
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, list)
            
            # Verify all returned players have the correct position
            for player in data:
                assert player['position'] == position
    
    def test_api_players_search(self, client):
        """Test /api/players/search/<query> endpoint"""
        # Test search for "Salah"
        resp = client.get("/api/players/search/salah")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        
        # Should find Mohamed Salah
        salah_found = any('salah' in player['name'].lower() for player in data)
        assert salah_found, "Salah should be found in search results"
        
        # Test with limit parameter
        resp = client.get("/api/players/search/a?limit=2")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) <= 2
    
    def test_api_players_by_team(self, client):
        """Test /api/players/team/<team_name> endpoint"""
        resp = client.get("/api/players/team/Liverpool")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        
        # All players should be from Liverpool
        for player in data:
            assert player['team'] == 'Liverpool'
    
    def test_api_players_price_range(self, client):
        """Test /api/players/price-range endpoint"""
        resp = client.get("/api/players/price-range?min=5.0&max=10.0")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        
        # All players should be within price range
        for player in data:
            assert 5.0 <= player['price'] <= 10.0
    
    def test_api_players_top_points(self, client):
        """Test /api/players/top/points endpoint"""
        resp = client.get("/api/players/top/points?limit=3")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) <= 3
        
        # Players should be sorted by total_points (descending)
        if len(data) > 1:
            for i in range(len(data) - 1):
                assert data[i]['total_points'] >= data[i + 1]['total_points']
    
    def test_api_players_top_value(self, client):
        """Test /api/players/top/value endpoint"""
        resp = client.get("/api/players/top/value?limit=3")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) <= 3
    
    def test_api_teams(self, client):
        """Test /api/teams endpoint"""
        resp = client.get("/api/teams")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        required_fields = ["id", "name", "short_name", "code", "strength"]
        for field in required_fields:
            assert field in data[0], f"Missing field: {field}"
    
    def test_api_fdr(self, client):
        """Test /api/fdr endpoint"""
        resp = client.get("/api/fdr")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        required_fields = [
            "id", "home_team", "away_team", "home_difficulty", 
            "away_difficulty", "gameweek"
        ]
        for field in required_fields:
            assert field in data[0], f"Missing field: {field}"
        
        # Test difficulty values are valid (1-5)
        for fixture in data:
            assert 1 <= fixture['home_difficulty'] <= 5
            assert 1 <= fixture['away_difficulty'] <= 5
    
    def test_api_players_post(self, client, sample_player_data):
        """Test POST /api/players endpoint"""
        resp = client.post("/api/players", 
                          data=json.dumps(sample_player_data),
                          content_type='application/json')
        assert resp.status_code == 201
        
        data = resp.get_json()
        assert 'message' in data
        assert 'successfully' in data['message']
    
    def test_api_players_post_invalid_data(self, client):
        """Test POST /api/players with invalid data"""
        # Test with no data (should get 400 for missing required fields)
        resp = client.post("/api/players", 
                          data='{}',
                          content_type='application/json')
        assert resp.status_code == 400
        
        # Test with empty data (should get 400 for missing required fields)
        resp = client.post("/api/players", 
                          data=json.dumps({}),
                          content_type='application/json')
        assert resp.status_code == 400
    
    def test_api_players_statistics(self, client):
        """Test /api/players/statistics endpoint"""
        resp = client.get("/api/players/statistics")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, dict)
    
    def test_api_error_handling(self, client):
        """Test API error handling"""
        # Test invalid position
        resp = client.get("/api/players/InvalidPosition")
        assert resp.status_code == 200  # Should return empty list, not error
        
        # Test invalid team
        resp = client.get("/api/players/team/InvalidTeam")
        assert resp.status_code == 200  # Should return empty list, not error


@pytest.mark.api
class TestPageRendering:
    """Test that all pages render correctly"""
    
    def test_dashboard_page(self, client):
        """Test dashboard page renders"""
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Dashboard" in resp.data or b"FPL" in resp.data
    
    def test_players_page(self, client):
        """Test players page renders"""
        resp = client.get("/players")
        assert resp.status_code == 200
        assert b"Players" in resp.data
    
    def test_players2_page(self, client):
        """Test players2 page redirects to players page"""
        resp = client.get("/players2")
        assert resp.status_code == 302  # Redirect to /players
        # Follow the redirect to verify it goes to the right place
        resp = client.get("/players2", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Players" in resp.data
    
    def test_fdr_page(self, client):
        """Test FDR page renders"""
        resp = client.get("/fdr")
        assert resp.status_code == 200
        assert b"FDR" in resp.data or b"Fixture Difficulty" in resp.data
    
    def test_teams_page(self, client):
        """Test teams page renders"""
        resp = client.get("/teams")
        assert resp.status_code == 200
        assert b"Teams" in resp.data
    
    def test_squad_page(self, client):
        """Test squad page renders"""
        resp = client.get("/squad")
        assert resp.status_code == 200
        assert b"Squad" in resp.data
    
    def test_watchlist_page(self, client):
        """Test watchlist page renders"""
        resp = client.get("/watchlist")
        assert resp.status_code == 200
        assert b"Watchlist" in resp.data


@pytest.mark.api
class TestDataValidation:
    """Test data validation and edge cases"""
    
    def test_player_data_consistency(self, client):
        """Test that player data is consistent across endpoints"""
        # Get all players
        resp = client.get("/api/players")
        all_players = resp.get_json()
        
        # Get players by position
        resp = client.get("/api/players/Midfielder")
        midfielders = resp.get_json()
        
        # Count midfielders in all players
        expected_count = len([p for p in all_players if p['position'] == 'Midfielder'])
        assert len(midfielders) == expected_count
    
    def test_team_data_consistency(self, client):
        """Test that team data is consistent"""
        resp = client.get("/api/teams")
        teams = resp.get_json()
        
        # All teams should have unique IDs
        team_ids = [team['id'] for team in teams]
        assert len(team_ids) == len(set(team_ids))
        
        # All teams should have valid strength values
        for team in teams:
            assert 0 <= team['strength'] <= 100
    
    def test_fixture_data_consistency(self, client):
        """Test that fixture data is consistent"""
        resp = client.get("/api/fdr")
        fixtures = resp.get_json()
        
        # All fixtures should have valid gameweek numbers
        for fixture in fixtures:
            assert fixture['gameweek'] > 0
            assert fixture['gameweek'] <= 38  # Maximum gameweeks in a season


