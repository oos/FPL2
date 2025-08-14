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
                    strategy_data[gw] = self._create_gw1_squad(unique_players)
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
        """Create initial squad for GW1"""
        # Sort players by overall performance (using total_points field)
        sorted_players = sorted(
            players_data, 
            key=lambda x: x.get('total_points', 0) or 0, 
            reverse=True
        )
        
        # Select more players to ensure position variety (top 100 instead of just 15)
        # This ensures we have enough players of each position to fill the starting XI
        selected_players = sorted_players[:100]
        
        # Separate into starting XI and bench
        starting_xi = self._select_starting_xi(selected_players)
        bench = [p for p in selected_players if p not in starting_xi]
        
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
        # Get current squad (copy to avoid modifying original)
        current_squad = prev_gw_data["starting_xi"] + prev_gw_data["bench"]
        
        # Simulate some transfers (random for demo purposes)
        transfers_in = []
        transfers_out = []
        
        if random.random() < 0.3:  # 30% chance of transfer
            # Find a player to transfer out (random selection)
            transfer_out_player = random.choice(current_squad)
            transfers_out.append(transfer_out_player["name"])
            
            # Find a replacement player (ensure they're not already in the squad)
            available_players = [p for p in all_players if p["id"] not in [cp["id"] for cp in current_squad]]
            if available_players:
                transfer_in_player = random.choice(available_players)
                transfers_in.append(transfer_in_player["name"])
                
                # Update squad - remove old player, add new one
                current_squad = [p for p in current_squad if p["id"] != transfer_out_player["id"]]
                current_squad.append(transfer_in_player)
        
        # Re-optimize starting XI based on current gameweek performance
        gw_points_field = f'gw{gw}_points'
        sorted_squad = sorted(
            current_squad, 
            key=lambda x: x.get(gw_points_field, 0) or 0, 
            reverse=True
        )
        
        starting_xi = self._select_starting_xi(sorted_squad)
        bench = [p for p in sorted_squad if p not in starting_xi]
        
        return {
            "starting_xi": starting_xi,
            "bench": bench,
            "transfers": {"in": transfers_in, "out": transfers_out},
            "points": sum(p.get(gw_points_field, 0) or 0 for p in starting_xi),
            "formation": self.get_formation(starting_xi)
        }
    
    def _select_starting_xi(self, players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select starting XI from available players"""
        # Group players by position
        gk = [p for p in players if p.get('position') == 'Goalkeeper']
        defs = [p for p in players if p.get('position') == 'Defender']
        mids = [p for p in players if p.get('position') == 'Midfielder']
        fwds = [p for p in players if p.get('position') == 'Forward']
        
        # Select best players for each position
        starting_xi = []
        used_player_ids = set()
        
        # 1 goalkeeper (if available, otherwise use best available player)
        if gk:
            best_gk = max(gk, key=lambda x: x.get('total_points', 0) or 0)
            starting_xi.append(best_gk)
            used_player_ids.add(best_gk['id'])
        else:
            # No goalkeeper available, use best available player
            best_available = max(players, key=lambda x: x.get('total_points', 0) or 0)
            starting_xi.append(best_available)
            used_player_ids.add(best_available['id'])
        
        # 4-5 defenders
        defs_sorted = sorted(defs, key=lambda x: x.get('total_points', 0) or 0, reverse=True)
        for def_player in defs_sorted[:4]:
            if def_player['id'] not in used_player_ids:
                starting_xi.append(def_player)
                used_player_ids.add(def_player['id'])
        
        # 4-5 midfielders
        mids_sorted = sorted(mids, key=lambda x: x.get('total_points', 0) or 0, reverse=True)
        for mid_player in mids_sorted[:4]:
            if mid_player['id'] not in used_player_ids:
                starting_xi.append(mid_player)
                used_player_ids.add(mid_player['id'])
        
        # 1-2 forwards
        fwds_sorted = sorted(fwds, key=lambda x: x.get('total_points', 0) or 0, reverse=True)
        for fwd_player in fwds_sorted[:2]:
            if fwd_player['id'] not in used_player_ids:
                starting_xi.append(fwd_player)
                used_player_ids.add(fwd_player['id'])
        
        # Return whatever players we have (should be 11 with the increased player pool)
        # If we still don't have 11, that's fine - we'll show what we have
        return starting_xi
    
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
