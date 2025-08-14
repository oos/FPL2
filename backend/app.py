from flask import Flask, render_template, jsonify
from .config import config
from .database.manager import DatabaseManager
from .routes.players import players_bp
import os

def create_app(config_name='default'):
    """Application factory pattern for creating Flask app"""
    app = Flask(__name__, 
                template_folder='../templates',  # Templates are in parent directory
                static_folder='../static')       # Static files are in parent directory
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize database
    db_manager = DatabaseManager()
    
    # Register blueprints
    app.register_blueprint(players_bp)
    
    # Store database manager in app context for access in routes
    app.db_manager = db_manager
    
    # Root route - FDR page
    @app.route('/')
    def index():
        """Serve the FDR page (original UI)"""
        return render_template('fdr.html')
    
    # Players page route
    @app.route('/players')
    def players_page():
        """Serve the original players page with DataTables"""
        players = db_manager.get_all_players()
        teams = db_manager.get_all_teams()
        
        # Get unique positions and teams for dropdowns
        positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
        team_names = [team.name for team in teams]
        
        return render_template('players.html', players=players, team_names=team_names)
    
    # Squad page route
    @app.route('/squad')
    def squad_page():
        """Serve the original squad page"""
        return render_template('squad.html')
    
    # Legacy API routes for backward compatibility
    @app.route('/api/players', methods=['GET'])
    def get_players():
        """Get all players - legacy route"""
        players = db_manager.get_all_players()
        return jsonify([player.to_dict() for player in players])
    
    @app.route('/api/players/<position>', methods=['GET'])
    def get_players_by_position(position):
        """Get players by position - legacy route"""
        players = db_manager.get_players_by_position(position)
        return jsonify([player.to_dict() for player in players])
    
    @app.route('/api/teams', methods=['GET'])
    def get_teams():
        """Get all teams - legacy route"""
        teams = db_manager.get_all_teams()
        return jsonify([team.to_dict() for team in teams])
    
    @app.route('/api/fdr', methods=['GET'])
    def get_fdr():
        """Get FDR data - legacy route"""
        fixtures = db_manager.get_all_fixtures()
        return jsonify([fixture.to_dict() for fixture in fixtures])
    
    # Health check route
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            stats = db_manager.get_database_stats()
            return jsonify({
                'status': 'healthy',
                'database': stats,
                'timestamp': '2024-01-01T00:00:00Z'  # In real app, use datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

def run_app():
    """Run the Flask application"""
    # Get configuration from environment
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    # Create and run app
    app = create_app(config_name)
    
    print("Database initialized successfully")
    app.run(
        host='0.0.0.0',
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )

if __name__ == '__main__':
    run_app()
