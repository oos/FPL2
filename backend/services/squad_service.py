from typing import List, Dict, Any
from backend.database.manager import DatabaseManager
import random

class SquadService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_optimal_squad_for_gw1_9(self, max_transfers_per_gw: int = 1) -> Dict[int, Dict[str, Any]]:
        """Generate optimal squad strategy for GW1-9 with FPL rule compliance"""
        try:
            # Get all players from database
            players_data = self.db_manager.get_all_players()
            
            # Convert to list of dictionaries and deduplicate by name
            players_dict = [player.to_dict() for player in players_data]
            
            # Remove duplicates by name (keep the first occurrence)
            seen_names = set()
            unique_players = []
            for player in players_dict:
                if player['name'] not in seen_names:
                    seen_names.add(player['name'])
                    unique_players.append(player)
            
            print(f"Original players: {len(players_dict)}, Unique players: {len(unique_players)}")
            
            # Generate strategy for each gameweek
            strategy_data = {}
            
            for gw in range(1, 10):
                if gw == 1:
                    # GW1: Select best 15 players based on overall performance
                    gw1 = self._create_gw1_squad(unique_players)
                    # Carry 1 free transfer into GW2
                    gw1["free_transfers_remaining"] = 1
                    strategy_data[gw] = gw1
                else:
                    # GW2-9: Apply transfers and optimize with FPL rule compliance
                    strategy_data[gw] = self._create_optimized_gw_squad(
                        strategy_data[gw-1], unique_players, gw, max_transfers_per_gw
                    )
            
            return strategy_data
            
        except Exception as e:
            print(f"Error generating squad strategy: {e}")
            return {}
    
    def _create_gw1_squad(self, players_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create initial 15-player squad for GW1 enforcing FPL rules strictly"""
        # FPL squad composition rules
        target_by_position = {
            'Goalkeeper': 2,  # Must have exactly 2 goalkeepers
            'Defender': 5,    # Must have exactly 5 defenders
            'Midfielder': 5,  # Must have exactly 5 midfielders
            'Forward': 3,     # Must have exactly 3 forwards
        }
        max_players_per_team = 3
        budget_cap_millions = 100.0

        # Sort all players by total expected points (desc)
        sorted_players = sorted(
            players_data,
            key=lambda x: x.get('total_points', 0) or 0,
            reverse=True,
        )

        # Build 15-player squad under strict FPL constraints
        squad: List[Dict[str, Any]] = []
        position_counts = {k: 0 for k in target_by_position.keys()}
        team_counts: Dict[str, int] = {}
        total_budget = 0.0
        used_ids = set()

        # First pass: fill mandatory positions with best available players
        for pos, required_count in target_by_position.items():
            pos_players = [p for p in sorted_players if p.get('position') == pos]
            pos_players.sort(key=lambda x: x.get('total_points', 0) or 0, reverse=True)
            
            for i in range(required_count):
                if i < len(pos_players):
                    player = pos_players[i]
                    pid = player.get('id')
                    if pid in used_ids:
                        continue
                    
                    # Check team limit
                    team_name = player.get('team') or 'Unknown'
                    if team_name != 'Unknown' and team_counts.get(team_name, 0) >= max_players_per_team:
                        continue
                    
                    # Check budget
                    price = float(player.get('price') or 0.0)
                    if total_budget + price > budget_cap_millions:
                        continue
                    
                    # Add player
                    squad.append(player)
                    used_ids.add(pid)
                    position_counts[pos] += 1
                    team_counts[team_name] = team_counts.get(team_name, 0) + 1
                    total_budget += price

        # Ensure we have exactly 15 players
        if len(squad) < 15:
            # Fill remaining slots with best available players
            remaining_players = [p for p in sorted_players if p.get('id') not in used_ids]
            remaining_players.sort(key=lambda x: x.get('total_points', 0) or 0, reverse=True)
            
            for player in remaining_players:
                if len(squad) >= 15:
                    break
                    
                pid = player.get('id')
                if pid in used_ids:
                    continue
                
                # Check team limit
                team_name = player.get('team') or 'Unknown'
                if team_name != 'Unknown' and team_counts.get(team_name, 0) >= max_players_per_team:
                    continue
                
                # Check budget
                price = float(player.get('price') or 0.0)
                if total_budget + price > budget_cap_millions:
                    continue
                
                # Add player
                squad.append(player)
                used_ids.add(pid)
                team_counts[team_name] = team_counts.get(team_name, 0) + 1
                total_budget += price

        # Select starting XI (best 11 players)
        starting_xi = self._select_starting_xi(squad)
        bench = [p for p in squad if p not in starting_xi]

        # Captain and vice-captain selection
        xi_sorted_for_captain = sorted(
            starting_xi,
            key=lambda x: (float(x.get('gw1_points', 0) or 0), float(x.get('total_points', 0) or 0)),
            reverse=True,
        )
        captain_name = xi_sorted_for_captain[0].get('name') if xi_sorted_for_captain else None
        vice_captain_name = xi_sorted_for_captain[1].get('name') if len(xi_sorted_for_captain) > 1 else None

        return {
            "starting_xi": starting_xi,
            "bench": bench,
            "transfers": {"in": [], "out": []},
            "points": sum(p.get('gw1_points', 0) or 0 for p in starting_xi),
            "formation": self.get_formation(starting_xi),
            "captain": captain_name,
            "vice_captain": vice_captain_name,
            "hits_points": 0,
            "free_transfers_remaining": 1,
        }
    
    def _create_optimized_gw_squad(self, prev_gw_data: Dict[str, Any], 
                                  all_players: List[Dict[str, Any]], 
                                  gw: int,
                                  max_transfers_per_gw: int) -> Dict[str, Any]:
        """Create optimized squad for subsequent gameweeks with strict FPL rule compliance"""
        # Get current 15-player squad (carry over)
        current_squad = list(prev_gw_data["starting_xi"]) + list(prev_gw_data["bench"])

        # Determine available free transfers with rollover (cap 2)
        prev_free = int(prev_gw_data.get("free_transfers_remaining", 1))
        available_free = min(2, prev_free + 1)  # FPL rule: max 2 free transfers
        
        # Limit transfers to user preference
        max_transfers = min(max_transfers_per_gw, available_free)
        
        # Re-optimize starting XI based on current gameweek performance
        gw_points_field = f'gw{gw}_points'
        
        # Plan transfers with strict FPL compliance
        updated_squad, transfers_in_players, transfers_out_players, hits_points, free_left, new_total_budget = (
            self._plan_transfers_for_gameweek(
                current_squad=current_squad,
                all_players=all_players,
                gw_points_field=gw_points_field,
                available_free_transfers=available_free,
                max_transfers=max_transfers,
                budget_cap=100.0,
            )
        )

        # Ensure we maintain a full 15-player squad with proper position distribution
        updated_squad = self._ensure_valid_fpl_squad(updated_squad, all_players)

        # Sort for XI selection
        sorted_squad = sorted(
            updated_squad,
            key=lambda x: ((x.get(gw_points_field, 0) or 0), (x.get('total_points', 0) or 0)),
            reverse=True,
        )

        starting_xi = self._select_starting_xi(sorted_squad, scoring_field=gw_points_field)
        # Ensure bench has exactly 4 players
        bench_candidates = [p for p in sorted_squad if p not in starting_xi]
        bench = bench_candidates[:4]
        
        # Captain and vice-captain for this GW based on gw points
        xi_sorted_for_captain = sorted(
            starting_xi,
            key=lambda x: (float(x.get(gw_points_field, 0) or 0), float(x.get('total_points', 0) or 0)),
            reverse=True,
        )
        captain_name = xi_sorted_for_captain[0].get('name') if xi_sorted_for_captain else None
        vice_captain_name = xi_sorted_for_captain[1].get('name') if len(xi_sorted_for_captain) > 1 else None

        return {
            "starting_xi": starting_xi,
            "bench": bench,
            "transfers": {"in": transfers_in_players, "out": transfers_out_players},
            "hits_points": hits_points,
            "free_transfers_remaining": free_left,
            "points": sum(p.get(gw_points_field, 0) or 0 for p in starting_xi),
            "formation": self.get_formation(starting_xi),
            "captain": captain_name,
            "vice_captain": vice_captain_name,
        }

    def _ensure_valid_fpl_squad(self, squad: List[Dict[str, Any]], all_players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure the squad meets FPL requirements: exactly 15 players with proper position distribution"""
        target_by_position = {
            'Goalkeeper': 2,
            'Defender': 5,
            'Midfielder': 5,
            'Forward': 3,
        }
        
        # Count current positions
        position_counts = {'Goalkeeper': 0, 'Defender': 0, 'Midfielder': 0, 'Forward': 0}
        for player in squad:
            pos = player.get('position')
            if pos in position_counts:
                position_counts[pos] += 1
        
        # If we have exactly 15 players with correct distribution, return as-is
        if len(squad) == 15 and all(position_counts[pos] == target_by_position[pos] for pos in target_by_position):
            return squad
        
        # If we have fewer than 15 players, add missing players
        if len(squad) < 15:
            needed = 15 - len(squad)
            available_players = [p for p in all_players if p.get('id') not in {x.get('id') for x in squad}]
            
            # Sort by total points
            available_players.sort(key=lambda x: x.get('total_points', 0) or 0, reverse=True)
            
            for player in available_players:
                if len(squad) >= 15:
                    break
                    
                pos = player.get('position')
                if pos in target_by_position and position_counts[pos] < target_by_position[pos]:
                    squad.append(player)
                    position_counts[pos] += 1
        
        # If we have more than 15 players, remove excess
        if len(squad) > 15:
            # Sort by total points and remove worst players
            squad.sort(key=lambda x: x.get('total_points', 0) or 0)
            while len(squad) > 15:
                squad.pop(0)
        
        return squad

    def _plan_transfers_for_gameweek(
        self,
        current_squad: List[Dict[str, Any]],
        all_players: List[Dict[str, Any]],
        gw_points_field: str,
        available_free_transfers: int,
        max_transfers: int,
        budget_cap: float,
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], int, int, float]:
        """Plan transfers with strict FPL rule compliance and detailed analysis"""
        # Compute current budget and team counts
        total_budget = sum(float(p.get('price') or 0.0) for p in current_squad)
        team_counts: Dict[str, int] = {}
        for p in current_squad:
            t = p.get('team') or 'Unknown'
            team_counts[t] = team_counts.get(t, 0) + 1

        # Build quick lookup of squad ids
        squad_ids = {p.get('id') for p in current_squad}

        # Find best transfer opportunities with detailed analysis
        candidates = []  # list of (delta, out_player, in_player, analysis_data)
        for out_p in current_squad:
            out_pts = float(out_p.get(gw_points_field, 0) or 0)
            pos = out_p.get('position')
            
            # Consider available players in same position
            for in_p in all_players:
                if in_p.get('id') in squad_ids:
                    continue
                    
                # Must be same position for FPL compliance
                if in_p.get('position') != pos:
                    continue
                    
                # Respect team limit of 3
                in_team = in_p.get('team') or 'Unknown'
                if in_team != 'Unknown' and team_counts.get(in_team, 0) >= 3:
                    continue
                    
                # Calculate point improvement
                delta = float(in_p.get(gw_points_field, 0) or 0) - out_pts
                if delta <= 0:
                    continue
                
                # Calculate 8-week projected points for detailed analysis
                analysis_data = self._calculate_transfer_analysis(out_p, in_p, gw_points_field, available_free_transfers)
                
                candidates.append((delta, out_p, in_p, analysis_data))

        # Sort descending by gain
        candidates.sort(key=lambda x: x[0], reverse=True)

        transfers_made = 0
        hits = 0
        in_players: List[Dict[str, Any]] = []
        out_players: List[Dict[str, Any]] = []
        updated_squad = list(current_squad)

        # Apply transfers up to the limit
        for delta, out_p, in_p, analysis_data in candidates:
            if transfers_made >= max_transfers:
                break
                
            # Skip if already processed
            if out_p.get('id') not in {p.get('id') for p in updated_squad}:
                continue
            if in_p.get('id') in {p.get('id') for p in updated_squad}:
                continue
                
            # Budget check
            out_price = float(out_p.get('price') or 0.0)
            in_price = float(in_p.get('price') or 0.0)
            new_budget = total_budget - out_price + in_price
            if new_budget > budget_cap:
                continue
                
            # Team cap check
            out_team = out_p.get('team') or 'Unknown'
            in_team = in_p.get('team') or 'Unknown'
            new_team_counts = dict(team_counts)
            new_team_counts[out_team] = max(0, new_team_counts.get(out_team, 0) - 1)
            new_team_counts[in_team] = new_team_counts.get(in_team, 0) + 1
            if in_team != 'Unknown' and new_team_counts.get(in_team, 0) > 3:
                continue

            # Apply transfer
            updated_squad = [p for p in updated_squad if p.get('id') != out_p.get('id')]
            updated_squad.append(in_p)
            total_budget = new_budget
            team_counts = new_team_counts
            transfers_made += 1
            
            # Store full player objects with analysis data
            out_player_with_analysis = dict(out_p)
            out_player_with_analysis['transfer_analysis'] = analysis_data
            
            in_player_with_analysis = dict(in_p)
            in_player_with_analysis['transfer_analysis'] = analysis_data
            
            in_players.append(in_player_with_analysis)
            out_players.append(out_player_with_analysis)

        # Calculate hits
        free_used = min(transfers_made, available_free_transfers)
        extra = max(0, transfers_made - available_free_transfers)
        hits_points = -4 * extra
        free_left = max(0, available_free_transfers - free_used)

        return updated_squad, in_players, out_players, hits_points, free_left, total_budget
    
    def _calculate_transfer_analysis(self, out_player: Dict[str, Any], in_player: Dict[str, Any], current_gw_field: str, available_free_transfers: int = 1) -> Dict[str, Any]:
        """Calculate detailed 8-week transfer analysis for two players"""
        # Extract current GW number from field name (e.g., 'gw2_points' -> 2)
        current_gw = int(current_gw_field.replace('gw', '').replace('_points', ''))
        
        # Calculate 8-week projected points for both players
        out_8week_total = 0
        in_8week_total = 0
        out_weekly_points = []
        in_weekly_points = []
        
        for gw in range(current_gw, min(current_gw + 8, 11)):  # FPL season goes to GW38, but we'll limit to GW10 for now
            gw_field = f'gw{gw}_points'
            
            # Get points for out player
            out_gw_points = float(out_player.get(gw_field, 0) or 0)
            out_8week_total += out_gw_points
            out_weekly_points.append({
                'gw': gw,
                'points': out_gw_points,
                'field': gw_field
            })
            
            # Get points for in player
            in_gw_points = float(in_player.get(gw_field, 0) or 0)
            in_8week_total += in_gw_points
            in_weekly_points.append({
                'gw': gw,
                'points': in_gw_points,
                'field': gw_field
            })
        
        # Calculate transfer impact with proper cost calculation
        point_difference = in_8week_total - out_8week_total
        
        # Calculate actual transfer cost based on available free transfers
        if available_free_transfers > 0:
            transfer_cost = 0  # Free transfer available
        else:
            transfer_cost = 4  # -4 hit cost when no free transfers
            
        net_gain = point_difference - transfer_cost
        
        # Calculate ROI (Return on Investment)
        out_price = float(out_player.get('price', 0) or 0)
        in_price = float(in_player.get('price', 0) or 0)
        price_difference = in_price - out_price
        
        # Points per million analysis
        out_ppm = out_8week_total / out_price if out_price > 0 else 0
        in_ppm = in_8week_total / in_price if in_price > 0 else 0
        ppm_improvement = in_ppm - out_ppm
        
        return {
            'out_player_8week_total': out_8week_total,
            'in_player_8week_total': in_8week_total,
            'point_difference': point_difference,
            'transfer_cost': transfer_cost,
            'net_gain': net_gain,
            'price_difference': price_difference,
            'out_ppm': out_ppm,
            'in_ppm': in_ppm,
            'ppm_improvement': ppm_improvement,
            'out_weekly_points': out_weekly_points,
            'in_weekly_points': in_weekly_points,
            'analysis_period': f"GW{current_gw}-{min(current_gw + 7, 10)}",
            'recommendation': self._generate_transfer_recommendation(net_gain, point_difference, ppm_improvement)
        }
    
    def _generate_transfer_recommendation(self, net_gain: float, point_difference: float, ppm_improvement: float) -> str:
        """Generate human-readable transfer recommendation"""
        if net_gain > 5:
            return "Strong Buy - High expected return even with transfer cost"
        elif net_gain > 0:
            return "Buy - Positive return expected over 8 weeks"
        elif point_difference > 0:
            return "Consider - Points improvement but transfer cost may outweigh benefits"
        elif ppm_improvement > 0.5:
            return "Value Buy - Better points per million ratio"
        else:
            return "Hold - Transfer may not provide sufficient improvement"
    
    def _select_starting_xi(self, players: List[Dict[str, Any]], scoring_field: str | None = None) -> List[Dict[str, Any]]:
        """Select a valid starting XI with strict FPL constraints"""
        def score(p: Dict[str, Any]) -> float:
            if scoring_field is not None:
                v = p.get(scoring_field, 0)
                if v is not None:
                    return float(v)
            return float(p.get('total_points', 0) or 0)

        sorted_all = sorted(players, key=score, reverse=True)

        # Group by position
        gk = [p for p in sorted_all if p.get('position') == 'Goalkeeper']
        defs = [p for p in sorted_all if p.get('position') == 'Defender']
        mids = [p for p in sorted_all if p.get('position') == 'Midfielder']
        fwds = [p for p in sorted_all if p.get('position') == 'Forward']

        starting_xi: List[Dict[str, Any]] = []
        used_ids = set()
        counts = {'Goalkeeper': 0, 'Defender': 0, 'Midfielder': 0, 'Forward': 0}
        
        # FPL minimum requirements
        min_req = {'Goalkeeper': 1, 'Defender': 3, 'Midfielder': 2, 'Forward': 1}
        max_allowed = {'Goalkeeper': 1, 'Defender': 5, 'Midfielder': 5, 'Forward': 3}

        def try_add(p: Dict[str, Any]) -> bool:
            pid = p.get('id')
            if pid in used_ids:
                return False
            pos = p.get('position')
            if pos in max_allowed and counts[pos] >= max_allowed[pos]:
                return False
            starting_xi.append(p)
            used_ids.add(pid)
            counts[pos] = counts.get(pos, 0) + 1
            return True

        # Fill minimum requirements first
        if gk:
            try_add(gk[0])  # Must have exactly 1 GK in starting XI
        
        # Fill minimum defenders
        for p in defs:
            if counts['Defender'] >= min_req['Defender']:
                break
            try_add(p)
            
        # Fill minimum midfielders
        for p in mids:
            if counts['Midfielder'] >= min_req['Midfielder']:
                break
            try_add(p)
            
        # Fill minimum forwards
        for p in fwds:
            if counts['Forward'] >= min_req['Forward']:
                break
            try_add(p)

        # Fill remaining slots up to 11
        for p in sorted_all:
            if len(starting_xi) >= 11:
                break
            if p.get('id') in used_ids:
                continue
            # Never add more than 1 GK to starting XI
            if p.get('position') == 'Goalkeeper' and counts['Goalkeeper'] >= 1:
                continue
            try_add(p)

        return starting_xi[:11]
    
    def get_formation(self, starting_xi: List[Dict[str, Any]]) -> str:
        """Get formation string from starting XI"""
        if not starting_xi:
            return "Unknown"
        
        # Count players by position
        gk_count = sum(1 for p in starting_xi if p.get('position') == 'Goalkeeper')
        def_count = sum(1 for p in starting_xi if p.get('position') == 'Defender')
        mid_count = sum(1 for p in starting_xi if p.get('position') == 'Midfielder')
        fwd_count = sum(1 for p in starting_xi if p.get('position') == 'Forward')
        
        # Return the standard formation format (excluding goalkeeper)
        return f"{def_count}-{mid_count}-{fwd_count}"
