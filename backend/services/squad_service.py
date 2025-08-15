from typing import List, Dict, Any
from ..database.manager import DatabaseManager
import random

class SquadService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_optimal_squad_for_gw1_9(self) -> Dict[int, Dict[str, Any]]:
        """Generate optimal squad strategy for GW1-9"""
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
                    # GW2-9: Apply transfers and optimize
                    strategy_data[gw] = self._create_optimized_gw_squad(
                        strategy_data[gw-1], unique_players, gw
                    )
            
            return strategy_data
            
        except Exception as e:
            print(f"Error generating squad strategy: {e}")
            return {}
    
    def _create_gw1_squad(self, players_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create initial 15-player squad for GW1 enforcing FPL rules"""
        # Desired squad composition and limits
        target_by_position = {
            'Goalkeeper': 2,
            'Defender': 5,
            'Midfielder': 5,
            'Forward': 3,
        }
        max_players_per_team = 3
        budget_cap_millions = 100.0

        # Sort all players by total expected points (desc)
        sorted_players = sorted(
            players_data,
            key=lambda x: x.get('total_points', 0) or 0,
            reverse=True,
        )

        # Compute cheapest price available to assure we can always fill remaining slots within budget
        try:
            min_price_overall = min(float(p.get('price') or 0.0) for p in players_data if p.get('price') is not None)
        except ValueError:
            min_price_overall = 3.5  # sensible fallback

        # Build 15-player squad under constraints
        squad: List[Dict[str, Any]] = []
        position_counts = {k: 0 for k in target_by_position.keys()}
        team_counts: Dict[str, int] = {}
        total_budget = 0.0
        used_ids = set()

        for player in sorted_players:
            if len(squad) >= 15:
                break
            pid = player.get('id')
            if pid in used_ids:
                continue
            pos = player.get('position')
            if pos not in target_by_position:
                continue
            # Enforce per-position target
            if position_counts[pos] >= target_by_position[pos]:
                continue
            # Enforce team limit
            team_name = player.get('team') or 'Unknown'
            # Enforce team cap except for Unknown (don't block filling on unknown teams)
            if team_name != 'Unknown' and team_counts.get(team_name, 0) >= max_players_per_team:
                continue
            # Enforce budget cap with feasibility: ensure enough budget remains to fill the rest with cheapest
            price = float(player.get('price') or 0.0)
            remaining_slots_if_added = (15 - (len(squad) + 1))
            required_min_budget = remaining_slots_if_added * min_price_overall
            if total_budget + price + required_min_budget > budget_cap_millions:
                continue

            # Add player
            squad.append(player)
            used_ids.add(pid)
            position_counts[pos] += 1
            team_counts[team_name] = team_counts.get(team_name, 0) + 1
            total_budget += price

        # If we couldn't reach 15, fill missing positions to meet exact position targets first
        if len(squad) < 15:
            for pos_needed, target in target_by_position.items():
                while len(squad) < 15 and position_counts.get(pos_needed, 0) < target:
                    candidate = None
                    for player in sorted_players:
                        pid = player.get('id')
                        if pid in used_ids:
                            continue
                        if player.get('position') != pos_needed:
                            continue
                        team_name = player.get('team') or 'Unknown'
                        if team_name != 'Unknown' and team_counts.get(team_name, 0) >= max_players_per_team:
                            continue
                        price = float(player.get('price') or 0.0)
                        remaining_slots_if_added = (15 - (len(squad) + 1))
                        required_min_budget = remaining_slots_if_added * min_price_overall
                        if total_budget + price + required_min_budget > budget_cap_millions:
                            continue
                        candidate = player
                        break
                    if candidate is None:
                        break
                    squad.append(candidate)
                    used_ids.add(candidate.get('id'))
                    position_counts[pos_needed] = position_counts.get(pos_needed, 0) + 1
                    tname = candidate.get('team') or 'Unknown'
                    team_counts[tname] = team_counts.get(tname, 0) + 1
                    total_budget += float(candidate.get('price') or 0.0)

        # If still short, fill with cheapest candidates that do NOT exceed position targets
        if len(squad) < 15:
            remaining_budget = budget_cap_millions - total_budget
            cheap_candidates = sorted(
                [p for p in players_data if p.get('id') not in used_ids and position_counts.get(p.get('position'), 0) < target_by_position.get(p.get('position'), 0)],
                key=lambda x: float(x.get('price') or 0.0)
            )
            for player in cheap_candidates:
                if len(squad) >= 15:
                    break
                price = float(player.get('price') or 0.0)
                if price > remaining_budget:
                    continue
                team_name = player.get('team') or 'Unknown'
                if team_name != 'Unknown' and team_counts.get(team_name, 0) >= max_players_per_team:
                    continue
                # enforce not exceeding the exact target for the position
                pos = player.get('position')
                if position_counts.get(pos, 0) >= target_by_position.get(pos, 0):
                    continue
                squad.append(player)
                used_ids.add(player.get('id'))
                position_counts[pos] = position_counts.get(pos, 0) + 1
                team_counts[team_name] = team_counts.get(team_name, 0) + 1
                total_budget += price
                remaining_budget = budget_cap_millions - total_budget

        # Derive XI and bench (exactly 11 + 4) using GW1 points for ranking
        starting_xi = self._select_starting_xi(squad, scoring_field='gw1_points')
        # Keep bench limited to 4, pick best remaining by GW1 points then total
        remaining = [p for p in squad if p not in starting_xi]
        remaining_sorted = sorted(
            remaining,
            key=lambda x: ((x.get('gw1_points', 0) or 0), (x.get('total_points', 0) or 0)),
            reverse=True
        )
        bench = remaining_sorted[:4]

        return {
            "starting_xi": starting_xi,
            "bench": bench,
            "transfers": {"in": [], "out": []},
            "points": sum(p.get('gw1_points', 0) or 0 for p in starting_xi),
            "formation": self.get_formation(starting_xi)
        }
    
    def _create_optimized_gw_squad(self, prev_gw_data: Dict[str, Any], 
                                  all_players: List[Dict[str, Any]], 
                                  gw: int) -> Dict[str, Any]:
        """Create optimized squad for subsequent gameweeks"""
        # Get current 15-player squad (carry over)
        current_squad = list(prev_gw_data["starting_xi"]) + list(prev_gw_data["bench"])

        # Determine available free transfers with rollover (cap 5 as requested)
        prev_free = int(prev_gw_data.get("free_transfers_remaining", 1))
        available_free = min(5, prev_free + 1)
        
        # Re-optimize starting XI based on current gameweek performance
        gw_points_field = f'gw{gw}_points'
        sorted_squad = sorted(
            current_squad,
            key=lambda x: ((x.get(gw_points_field, 0) or 0), (x.get('total_points', 0) or 0)),
            reverse=True
        )

        # Plan transfers greedily to improve GW points with hits when beneficial
        updated_squad, transfers_in_names, transfers_out_names, hits_points, free_left, new_total_budget = (
            self._plan_transfers_for_gameweek(
                current_squad=current_squad,
                all_players=all_players,
                gw_points_field=gw_points_field,
                available_free_transfers=available_free,
                budget_cap=100.0,
            )
        )

        # Sort for XI selection
        sorted_squad = sorted(
            updated_squad,
            key=lambda x: ((x.get(gw_points_field, 0) or 0), (x.get('total_points', 0) or 0)),
            reverse=True,
        )

        starting_xi = self._select_starting_xi(sorted_squad, scoring_field=gw_points_field)
        # Limit bench to 4
        bench_candidates = [p for p in sorted_squad if p not in starting_xi]
        bench = bench_candidates[:4]
        
        return {
            "starting_xi": starting_xi,
            "bench": bench,
            "transfers": {"in": transfers_in_names, "out": transfers_out_names},
            "hits_points": hits_points,
            "free_transfers_remaining": free_left,
            "points": sum(p.get(gw_points_field, 0) or 0 for p in starting_xi),
            "formation": self.get_formation(starting_xi)
        }

    def _plan_transfers_for_gameweek(
        self,
        current_squad: List[Dict[str, Any]],
        all_players: List[Dict[str, Any]],
        gw_points_field: str,
        available_free_transfers: int,
        budget_cap: float,
    ) -> tuple[List[Dict[str, Any]], List[str], List[str], int, int, float]:
        """Greedy transfer planner. Returns (new_squad, in_names, out_names, hits_points, free_left, new_budget)."""
        # Compute current budget and team counts
        total_budget = sum(float(p.get('price') or 0.0) for p in current_squad)
        team_counts: Dict[str, int] = {}
        for p in current_squad:
            t = p.get('team') or 'Unknown'
            team_counts[t] = team_counts.get(t, 0) + 1

        # Build quick lookup of squad ids
        squad_ids = {p.get('id') for p in current_squad}

        # Precompute best replacement for each squad player by delta points
        candidates = []  # list of (delta, out_player, in_player)
        for out_p in current_squad:
            out_pts = float(out_p.get(gw_points_field, 0) or 0)
            pos = out_p.get('position')
            # Consider top N available by GW points in same position and globally (to allow formation flexibility)
            for in_p in all_players:
                if in_p.get('id') in squad_ids:
                    continue
                # Respect team limit of 3 (don't count Unknown for cap)
                in_team = in_p.get('team') or 'Unknown'
                if in_team != 'Unknown' and team_counts.get(in_team, 0) >= 3:
                    continue
                delta = float(in_p.get(gw_points_field, 0) or 0) - out_pts
                if delta <= 0:
                    continue
                candidates.append((delta, out_p, in_p))

        # Sort descending by gain
        candidates.sort(key=lambda x: x[0], reverse=True)

        transfers_made = 0
        hits = 0
        in_names: List[str] = []
        out_names: List[str] = []

        # Greedy apply while net positive considering hit cost
        for delta, out_p, in_p in candidates:
            # Skip if already transferred out or in
            if out_p.get('id') not in {p.get('id') for p in current_squad}:
                continue
            if in_p.get('id') in {p.get('id') for p in current_squad}:
                continue
            # Budget check
            out_price = float(out_p.get('price') or 0.0)
            in_price = float(in_p.get('price') or 0.0)
            new_budget = total_budget - out_price + in_price
            if new_budget > budget_cap:
                continue
            # Team cap check if we remove and add
            out_team = out_p.get('team') or 'Unknown'
            in_team = in_p.get('team') or 'Unknown'
            # Tentative team counts after swap
            new_team_counts = dict(team_counts)
            new_team_counts[out_team] = max(0, new_team_counts.get(out_team, 0) - 1)
            new_team_counts[in_team] = new_team_counts.get(in_team, 0) + 1
            if in_team != 'Unknown' and new_team_counts.get(in_team, 0) > 3:
                continue

            # Determine marginal hit cost for this transfer
            marginal_hit = 0
            if transfers_made + 1 > available_free_transfers:
                marginal_hit = 4
            # Apply only if net gain > marginal hit
            if delta <= marginal_hit:
                continue

            # Apply transfer
            current_squad = [p for p in current_squad if p.get('id') != out_p.get('id')]
            current_squad.append(in_p)
            total_budget = new_budget
            team_counts = new_team_counts
            squad_ids = {p.get('id') for p in current_squad}
            transfers_made += 1
            in_names.append(in_p.get('name'))
            out_names.append(out_p.get('name'))

            # Limit to a reasonable number per week (avoid excessive swaps)
            if transfers_made >= available_free_transfers + 4:
                break

        free_used = min(transfers_made, available_free_transfers)
        extra = max(0, transfers_made - available_free_transfers)
        hits_points = -4 * extra
        free_left = min(5, available_free_transfers - free_used)

        return current_squad, in_names, out_names, hits_points, free_left, total_budget
    
    def _select_starting_xi(self, players: List[Dict[str, Any]], scoring_field: str | None = None) -> List[Dict[str, Any]]:
        """Select a valid starting XI with FPL-like constraints. Always returns up to 11 players."""
        def score(p: Dict[str, Any]) -> float:
            if scoring_field is not None:
                v = p.get(scoring_field, 0)
                if v is not None:
                    return float(v)
            return float(p.get('total_points', 0) or 0)

        sorted_all = sorted(players, key=score, reverse=True)

        gk = [p for p in sorted_all if p.get('position') == 'Goalkeeper']
        defs = [p for p in sorted_all if p.get('position') == 'Defender']
        mids = [p for p in sorted_all if p.get('position') == 'Midfielder']
        fwds = [p for p in sorted_all if p.get('position') == 'Forward']

        starting_xi: List[Dict[str, Any]] = []
        used_ids = set()
        counts = {'Goalkeeper': 0, 'Defender': 0, 'Midfielder': 0, 'Forward': 0}
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

        # Minimums (enforce exactly one GK in XI)
        if gk:
            try_add(gk[0])
        for p in defs:
            if counts['Defender'] >= min_req['Defender']:
                break
            try_add(p)
        for p in mids:
            if counts['Midfielder'] >= min_req['Midfielder']:
                break
            try_add(p)
        for p in fwds:
            if counts['Forward'] >= min_req['Forward']:
                break
            try_add(p)

        # Fill remaining up to 11
        for p in sorted_all:
            if len(starting_xi) >= 11:
                break
            # Do not allow more than 1 GK
            if p.get('position') == 'Goalkeeper' and counts['Goalkeeper'] >= 1:
                continue
            try_add(p)

        # Relax caps if still short
        if len(starting_xi) < 11:
            for p in sorted_all:
                if len(starting_xi) >= 11:
                    break
                pid = p.get('id')
                if pid in used_ids:
                    continue
                if p.get('position') == 'Goalkeeper' and counts['Goalkeeper'] >= 1:
                    continue
                starting_xi.append(p)
                used_ids.add(pid)

        return starting_xi[:11]
    
    def get_formation(self, starting_xi: List[Dict[str, Any]]) -> str:
        """Get formation string from starting XI"""
        if not starting_xi:
            return "Unknown"
        
        # Count players by position, handling duplicates
        gk_count = sum(1 for p in starting_xi if p.get('position') == 'Goalkeeper')
        def_count = sum(1 for p in starting_xi if p.get('position') == 'Defender')
        mid_count = sum(1 for p in starting_xi if p.get('position') == 'Midfielder')
        fwd_count = sum(1 for p in starting_xi if p.get('position') == 'Forward')
        
        # Return the actual formation based on real positions
        if gk_count > 0:
            return f"{gk_count}-{def_count}-{mid_count}-{fwd_count}"
        else:
            return f"{def_count}-{mid_count}-{fwd_count}"
