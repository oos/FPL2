    @app.route('/squad-live')
    def squad_live_page():
        """Live squad page showing actual FPL squad with GW tabs"""
        db_manager = current_app.db_manager

        # Get the first user profile (assuming single user for now)
        profiles = db_manager.get_all_user_profiles()
        if not profiles:
            return render_template('squad-live.html', profile=None, squad=None, standings=None, weekly_data=None)

        profile = profiles[0]
        fpl_team_id = profile['fpl_team_id']

        # Get current gameweek
        live_service = LiveFPLService(db_manager)
        current_gw = live_service.get_current_gameweek()
        
        # Sync all historical squads if requested
        if request.args.get('sync_historical') == 'true':
            try:
                live_service.sync_all_historical_squads(fpl_team_id)
            except Exception as e:
                print(f"Historical sync failed: {e}")

        # Get squad data for current gameweek
        squad = live_service.get_squad_for_gameweek(fpl_team_id, current_gw)

        # Generate weekly data for all gameweeks (1-9)
        weekly_data = []
        
        for gw in range(1, 10):
            # Determine status based on gameweek
            if gw < current_gw:
                status = "Historical"
                # Get historical squad data
                gw_squad = live_service.get_squad_for_gameweek(fpl_team_id, gw)
            elif gw == current_gw:
                status = "Current"
                # Use current squad data
                gw_squad = squad
            else:
                status = "Predicted"
                # For future gameweeks, we'll generate predictions
                gw_squad = None
            
            # Enrich squad data if available
            enriched_squad = []
            if gw_squad:
                for squad_player in gw_squad:
                    player = db_manager.get_player_by_id(squad_player['player_id'])
                    if player:
                        enriched_player = {
                            'id': squad_player['player_id'],
                            'name': str(player.name) if player.name else 'Unknown',
                            'web_name': str(player.name) if player.name else 'Unknown',
                            'team': str(player.team) if player.team else 'Unknown',
                            'position': str(player.position) if player.position else 'Unknown',
                            'price': float(player.price) if player.price else 0.0,
                            'is_captain': bool(squad_player['is_captain']),
                            'is_vice_captain': bool(squad_player['is_vice_captain']),
                            'is_bench': bool(squad_player['is_bench']),
                            'bench_position': squad_player['bench_position'],
                            'transfer_in': bool(squad_player['transfer_in']),
                            'transfer_out': bool(squad_player['transfer_out']),
                            'actual_points': float(squad_player.get('actual_points', 0) or 0.0),
                            'multiplier': int(squad_player.get('multiplier', 1) or 1),
                            # Preserve all gameweek points for transfer analysis
                            'gw1_points': float(squad_player.get('gw1_points', 0) or 0.0),
                            'gw2_points': float(squad_player.get('gw2_points', 0) or 0.0),
                            'gw3_points': float(squad_player.get('gw3_points', 0) or 0.0),
                            'gw4_points': float(squad_player.get('gw4_points', 0) or 0.0),
                            'gw5_points': float(squad_player.get('gw5_points', 0) or 0.0),
                            'gw6_points': float(squad_player.get('gw6_points', 0) or 0.0),
                            'gw7_points': float(squad_player.get('gw7_points', 0) or 0.0),
                            'gw8_points': float(squad_player.get('gw8_points', 0) or 0.0),
                            'gw9_points': float(squad_player.get('gw9_points', 0) or 0.0),
                            'total_points': float(squad_player.get('total_points', 0) or 0.0)
                        }
                        enriched_squad.append(enriched_player)
            
            # Create weekly data entry
            gw_data = {
                "gw": gw,
                "status": status,
                "starting_xi": [p for p in enriched_squad if not p['is_bench']] if enriched_squad else [],
                "bench": [p for p in enriched_squad if p['is_bench']] if enriched_squad else [],
                "transfers_in": [],
                "transfers_out": [],
                "points": 0,
                "captain_name": next((p['web_name'] for p in enriched_squad if p['is_captain']), None) if enriched_squad else None,
                "vice_captain_name": next((p['web_name'] for p in enriched_squad if p['is_vice_captain']), None) if enriched_squad else None,
                "hits_points": 0,
                "total_with_captain_and_hits": 0,
                "squad_value": sum(p['price'] for p in enriched_squad) if enriched_squad else 0,
                "formation": "Unknown"
            }
            
            # Calculate formation if we have starting XI
            if gw_data["starting_xi"]:
                try:
                    from backend.services.squad_service import SquadService
                    squad_service = SquadService(db_manager)
                    gw_data["formation"] = squad_service.get_formation(gw_data["starting_xi"])
                except:
                    pass
            
            weekly_data.append(gw_data)

        standings = db_manager.get_user_league_standings(fpl_team_id)

        return render_template('squad-live.html', profile=profile, squad=squad, standings=standings, weekly_data=weekly_data)
