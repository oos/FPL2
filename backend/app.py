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
    
    # Dashboard (Home)
    @app.route('/')
    def dashboard():
        """Serve the dashboard page with key summaries for upcoming weeks"""
        db_manager = current_app.db_manager
        # Fixtures and upcoming GW
        fixtures = db_manager.get_all_fixtures()
        gws = sorted({f.gameweek for f in fixtures})
        # Pick the first gameweek that appears to be complete (>=10 fixtures).
        # If none meet that threshold, fall back to the earliest GW available.
        fixtures_by_gw = {}
        for f in fixtures:
            fixtures_by_gw.setdefault(f.gameweek, []).append(f)
        upcoming_gw = None
        for gw in gws:
            if len(fixtures_by_gw.get(gw, [])) >= 10:
                upcoming_gw = gw
                break
        if upcoming_gw is None:
            upcoming_gw = gws[0] if gws else 1

        # All fixtures for upcoming GW (sorted by combined difficulty)
        gw_fixtures = fixtures_by_gw.get(upcoming_gw, [])
        for_gw_sorted = sorted(
            gw_fixtures,
            key=lambda f: (f.home_difficulty + f.away_difficulty, f.home_team)
        )
        easiest = for_gw_sorted[:6]
        # Provide full, sorted list for dashboard "All Fixtures" panel
        all_fixtures = for_gw_sorted

        # Suggested XI for upcoming GW using SquadService
        squad_service = SquadService(db_manager)
        strategy = squad_service.get_optimal_squad_for_gw1_9()
        starting_xi = []
        bench = []
        formation = 'Unknown'
        gw_points = 0.0
        if strategy and upcoming_gw in strategy:
            entry = strategy[upcoming_gw]
            starting_xi = entry.get('starting_xi', [])
            bench = entry.get('bench', [])
            formation = squad_service.get_formation(starting_xi)
            gw_points = sum(p.get(f"gw{upcoming_gw}_points", 0) or 0 for p in starting_xi)

        return render_template(
            'dashboard.html',
            upcoming_gw=upcoming_gw,
            easiest=easiest,
            toughest=[],
            xi=starting_xi,
            bench=bench,
            formation=formation,
            gw_points=gw_points,
            all_fixtures=all_fixtures,
        )

    # FDR page
    @app.route('/fdr')
    def fdr_page():
        """Serve the FDR page"""
        return render_template('fdr.html')
    
    @app.route('/teams')
    def teams_page():
        """List all teams with links to their pages"""
        db_manager = current_app.db_manager
        teams = db_manager.get_all_teams()
        return render_template('teams.html', teams=[t.to_dict() for t in teams])
    
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

    @app.route('/players/individual')
    def players_individual_redirect():
        """Redirect to a default player's page (e.g., Salah) if available."""
        db = current_app.db_manager
        players = db.get_all_players()
        # Try several common variants for Salah's name
        preferred_names = [
            'Mohamed Salah', 'M. Salah', 'M.Salah', 'Salah', 'Mo Salah'
        ]
        target = None
        lower_map = {p.name.lower(): p for p in players}
        for name in preferred_names:
            p = lower_map.get(name.lower())
            if p:
                target = p
                break
        # Fallback: choose the highest total_points player if Salah not found
        if not target and players:
            target = max(players, key=lambda p: p.total_points)
        if target:
            from flask import redirect, url_for
            return redirect(url_for('player_page', player_id=target.id))
        # Last resort: go to the players list
        return render_template('players.html', players=[p.to_dict() for p in players], team_names=[t.name for t in db.get_all_teams()])
    @app.route('/player/<int:player_id>')
    def player_page(player_id: int):
        """Serve an individual player page"""
        db_manager = current_app.db_manager
        player = db_manager.get_player_by_id(player_id)
        if not player:
            return f"Player with id {player_id} not found", 404
        # Convert to dict for simple rendering
        pdata = player.to_dict() if hasattr(player, 'to_dict') else {
            'id': player.id,
            'name': player.name,
            'position': player.position,
            'team': player.team,
            'price': player.price,
            'total_points': player.total_points,
            'form': getattr(player, 'form', 0),
            'ownership': getattr(player, 'ownership', 0),
            'chance_of_playing_next_round': getattr(player, 'chance_of_playing_next_round', 100),
            'points_per_million': getattr(player, 'points_per_million', 0),
            'gw1_points': getattr(player, 'gw1_points', 0),
            'gw2_points': getattr(player, 'gw2_points', 0),
            'gw3_points': getattr(player, 'gw3_points', 0),
            'gw4_points': getattr(player, 'gw4_points', 0),
            'gw5_points': getattr(player, 'gw5_points', 0),
            'gw6_points': getattr(player, 'gw6_points', 0),
            'gw7_points': getattr(player, 'gw7_points', 0),
            'gw8_points': getattr(player, 'gw8_points', 0),
            'gw9_points': getattr(player, 'gw9_points', 0),
        }
        return render_template('player.html', player=pdata)
    
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
            
            running_cumulative_total = 0.0
            for gw in range(1, 10):  # GW1-9
                gw_data = strategy_data[gw]
                starting_xi = gw_data["starting_xi"]
                bench = gw_data["bench"]
                
                # Calculate points for this GW
                gw_points_field = f"gw{gw}_points"
                gw_points = sum(player.get(gw_points_field, 0) or 0 for player in starting_xi)
                
                # Captaincy: select best scorer in XI and add bonus equal to their GW points
                captain_player = max(starting_xi, key=lambda p: p.get(gw_points_field, 0) or 0) if starting_xi else None
                captain_name = captain_player.get("name") if captain_player else None
                captain_bonus = (captain_player.get(gw_points_field, 0) or 0) if captain_player else 0
                
                # Get transfer information
                transfers_in = gw_data.get("transfers", {}).get("in", [])
                transfers_out = gw_data.get("transfers", {}).get("out", [])
                
                if gw > 1:  # GW1 has no transfers
                    total_transfers += len(transfers_in)
                
                # Hits: -4 per transfer beyond 1 free transfer each week (GW>1)
                free_transfers = 1 if gw > 1 else 0
                hits_over_free = max(0, len(transfers_in) - free_transfers)
                hits_points = -4 * hits_over_free
                
                # Total points with captaincy and hits
                total_gw_points = gw_points + captain_bonus + hits_points
                total_points += total_gw_points
                running_cumulative_total += total_gw_points

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
                    "captain_name": captain_name,
                    "captain_bonus": captain_bonus,
                    "hits_points": hits_points,
                    "total_with_captain_and_hits": total_gw_points,
                    "squad_value": sum((p.get("price",0) or 0) for p in starting_xi + bench),
                    "cumulative_total": running_cumulative_total,
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
        # Attach a best-effort local logo path if present
        import os
        static_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
        assets_dir = os.path.join(static_root, 'assets', 'teams')
        enriched = []
        for team in teams:
            data = team.to_dict()
            short = (team.short_name or team.name).lower().replace(' ', '')
            for ext in ['svg', 'png', 'jpg', 'jpeg', 'webp']:
                candidate = os.path.join(assets_dir, f"{short}.{ext}")
                if os.path.exists(candidate):
                    data['logo_path'] = f"assets/teams/{short}.{ext}"
                    break
            enriched.append(data)
        return jsonify(enriched)

    @app.route('/team/<int:team_id>')
    def team_page(team_id: int):
        """Serve a team page with squad and fixtures"""
        db_manager = current_app.db_manager
        team = db_manager.get_team_by_id(team_id)
        if not team:
            return f"Team with id {team_id} not found", 404
        # Squad
        all_players = db_manager.get_all_players()
        squad = [p.to_dict() for p in all_players if p.team == team.name]
        # Fixtures schedule
        fixtures = [f.to_dict() for f in db_manager.get_all_fixtures() if f.home_team == team.name or f.away_team == team.name]
        # Resolve local team logo (downloaded into static/assets/teams)
        import os
        static_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
        assets_dir = os.path.join(static_root, 'assets', 'teams')
        short = (team.short_name or team.name).lower().replace(' ', '')
        possible_exts = ['svg', 'png', 'jpg', 'jpeg', 'webp']
        logo_file = None
        for ext in possible_exts:
            candidate = os.path.join(assets_dir, f"{short}.{ext}")
            if os.path.exists(candidate):
                logo_file = f"assets/teams/{short}.{ext}"
                break
        return render_template('team.html', team=team.to_dict(), squad=squad, fixtures=fixtures, team_logo_file=logo_file)
    
    @app.route('/api/fdr')
    def api_fdr():
        """Get FDR data as JSON"""
        fixtures = current_app.db_manager.get_all_fixtures()
        return jsonify([fixture.to_dict() for fixture in fixtures])
    
    return app

def run_app():
    """Run the Flask application"""
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)
