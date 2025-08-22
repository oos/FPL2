from flask import Blueprint, jsonify, request, current_app
from ..services.player_service import PlayerService

# Create blueprint for players routes
players_bp = Blueprint('players', __name__)

def get_services():
    """Get service instances using the app's database manager"""
    db_manager = current_app.db_manager
    player_service = PlayerService(db_manager)
    return db_manager, player_service

@players_bp.route('/api/players', methods=['GET'])
def get_players():
    """Get all players"""
    try:
        _, player_service = get_services()
        players = player_service.get_all_players()
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@players_bp.route('/api/players/<position>', methods=['GET'])
def get_players_by_position(position):
    """Get players by position"""
    try:
        _, player_service = get_services()
        players = player_service.get_players_by_position(position)
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@players_bp.route('/api/players/search/<query>', methods=['GET'])
def search_players(query):
    """Search players by name"""
    try:
        _, player_service = get_services()
        limit = request.args.get('limit', 50, type=int)
        players = player_service.search_players(query, limit)
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@players_bp.route('/api/players/team/<team_name>', methods=['GET'])
def get_players_by_team(team_name):
    """Get players by team"""
    try:
        _, player_service = get_services()
        players = player_service.get_players_by_team(team_name)
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@players_bp.route('/api/players/price-range', methods=['GET'])
def get_players_by_price_range():
    """Get players within a price range"""
    try:
        _, player_service = get_services()
        min_price = request.args.get('min', 0.0, type=float)
        max_price = request.args.get('max', 20.0, type=float)
        players = player_service.get_players_by_price_range(min_price, max_price)
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@players_bp.route('/api/players/top/points', methods=['GET'])
def get_top_players_by_points():
    """Get top players by total points"""
    try:
        _, player_service = get_services()
        limit = request.args.get('limit', 20, type=int)
        players = player_service.get_top_players_by_points(limit)
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@players_bp.route('/api/players/top/value', methods=['GET'])
def get_top_players_by_value():
    """Get top players by points per million"""
    try:
        _, player_service = get_services()
        limit = request.args.get('limit', 20, type=int)
        players = player_service.get_top_players_by_value(limit)
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@players_bp.route('/api/players', methods=['POST'])
def add_player():
    """Add a new player"""
    try:
        _, player_service = get_services()
        player_data = request.get_json()
        
        # Check if data is provided and is a dictionary
        if not player_data or not isinstance(player_data, dict):
            return jsonify({'error': 'No data provided or invalid format'}), 400
        
        # Check if required fields are present
        required_fields = ['id', 'name', 'position', 'team', 'price']
        missing_fields = [field for field in required_fields if field not in player_data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        success = player_service.add_player(player_data)
        if success:
            return jsonify({'message': 'Player added successfully'}), 201
        else:
            return jsonify({'error': 'Failed to add player'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@players_bp.route('/api/players/statistics', methods=['GET'])
def get_player_statistics():
    """Get player statistics"""
    try:
        _, player_service = get_services()
        stats = player_service.get_player_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
