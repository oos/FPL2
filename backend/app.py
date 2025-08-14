from flask import Flask, render_template, jsonify, current_app
from .database.manager import DatabaseManager
from .services.player_service import PlayerService
from .services.squad_service import SquadService
from .routes.players import players_bp

def create_app():
    app = Flask(__name__, template_folder='../templates')
    
    # Initialize database manager
    app.db_manager = DatabaseManager()
    
    # Register blueprints
    app.register_blueprint(players_bp)
    
    # Store database manager in app context for access in routes
    with app.app_context():
        app.db_manager = DatabaseManager()
    
    # Root route - FDR page
    @app.route('/')
    def fdr_page():
        """Serve the FDR page"""
        return render_template('fdr.html')
    
    @app.route('/players')
    def players_page():
        """Serve the original players page with DataTables"""
        db_manager = current_app.db_manager # Access db_manager from app context
        players = db_manager.get_all_players()
        teams = db_manager.get_all_teams()
        
        # Convert Player objects to dictionaries for template
        players_data = [player.to_dict() for player in players]
        
        # Get unique positions and teams for dropdowns
        positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
        team_names = [team.name for team in teams]
        
        return render_template('players.html', players=players_data, team_names=team_names)
    
    @app.route('/squad')
    def squad_page():
        """Serve the Squad page with real squad data"""
        try:
            db_manager = current_app.db_manager
            squad_service = SquadService(db_manager)
            
            # Get optimal squad strategy for GW1-9
            strategy_data = squad_service.get_optimal_squad_for_gw1_9()
            
            if not strategy_data:
                return "Error: Could not generate squad data. Please try again later."
            
            # Process strategy data for template
            weekly_data = []
            total_points = 0
            total_transfers = 0
            
            for gw in range(1, 10):  # GW1-9
                gw_data = strategy_data[gw]
                starting_xi = gw_data["starting_xi"]
                bench = gw_data["bench"]
                
                # Calculate points for this GW
                gw_points = sum(player.get(f"gw{gw}_points", 0) or 0 for player in starting_xi)
                total_points += gw_points
                
                # Get transfer information
                transfers_in = gw_data.get("transfers", {}).get("in", [])
                transfers_out = gw_data.get("transfers", {}).get("out", [])
                
                if gw > 1:  # GW1 has no transfers
                    total_transfers += len(transfers_in)
                
                # Create transfer mapping (who replaced whom)
                transfer_mapping = {}
                if gw > 1 and len(transfers_in) > 0 and len(transfers_out) > 0:
                    # Map transfers in to transfers out (assuming they correspond in order)
                    for i, player_in in enumerate(transfers_in):
                        if i < len(transfers_out):
                            transfer_mapping[player_in] = transfers_out[i]
                        else:
                            transfer_mapping[player_in] = "Unknown player"
                
                # Calculate bench promotions/demotions
                bench_promotions = []
                bench_demotions = []
                if gw > 1:
                    prev_gw_data = strategy_data[gw - 1]
                    prev_xi = prev_gw_data["starting_xi"]
                    prev_bench = prev_gw_data["bench"]
                    
                    # Find players promoted from bench to starting XI
                    bench_promotions = [p for p in starting_xi if p["name"] in [bp["name"] for bp in prev_bench]]
                    
                    # Find players demoted from starting XI to bench
                    bench_demotions = [p for p in bench if p["name"] in [px["name"] for px in prev_xi]]
                
                weekly_data.append({
                    "gw": gw,
                    "starting_xi": starting_xi,
                    "bench": bench,
                    "transfers_in": transfers_in,
                    "transfers_out": transfers_out,
                    "transfer_mapping": transfer_mapping,
                    "bench_promotions": bench_promotions,
                    "bench_demotions": bench_demotions,
                    "points": gw_points,
                    "formation": squad_service.get_formation(starting_xi)
                })
            
            # Calculate total squad value (use GW1 as reference)
            gw1_data = strategy_data[1]
            all_players = gw1_data["starting_xi"] + gw1_data["bench"]
            total_value = sum(player.get("price", 0) or 0 for player in all_players)
            remaining_budget = 100.0 - total_value
            
            return render_template('squad.html', 
                                weekly_data=weekly_data, 
                                total_points=total_points, 
                                total_transfers=total_transfers, 
                                total_value=total_value, 
                                remaining_budget=remaining_budget)
            
        except Exception as e:
            return f"Error generating squad page: {str(e)}"
    
    # Legacy API routes for backward compatibility
    @app.route('/api/players')
    def api_players():
        """Get all players as JSON"""
        players = current_app.db_manager.get_all_players()
        return jsonify([player.to_dict() for player in players])
    
    @app.route('/api/teams')
    def api_teams():
        """Get all teams as JSON"""
        teams = current_app.db_manager.get_all_teams()
        return jsonify([team.to_dict() for team in teams])
    
    @app.route('/api/fdr')
    def api_fdr():
        """Get FDR data as JSON"""
        fixtures = current_app.db_manager.get_all_fixtures()
        return jsonify([fixture.to_dict() for fixture in fixtures])
    
    return app
