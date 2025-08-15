import json
import pytest

from backend.app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client


def assert_keys(item: dict, required_keys: list[str]):
    for k in required_keys:
        assert k in item, f"Missing key: {k} in {item}"


def test_api_players(client):
    resp = client.get("/api/players")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    if data:
        required = [
            "id",
            "name",
            "position",
            "team",
            "price",
            "total_points",
        ]
        assert_keys(data[0], required)


def test_api_teams(client):
    resp = client.get("/api/teams")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    if data:
        required = ["id", "name", "short_name", "code", "strength"]
        assert_keys(data[0], required)


def test_api_fdr(client):
    resp = client.get("/api/fdr")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    if data:
        required = [
            "id",
            "home_team",
            "away_team",
            "home_difficulty",
            "away_difficulty",
            "gameweek",
        ]
        assert_keys(data[0], required)


def test_pages_render(client):
    for path in ["/", "/players", "/squad"]:
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} failed with {resp.status_code}"


