#!/usr/bin/env python3
"""
FPL Transfer Optimization Service
Optimizes transfer strategy over multiple gameweeks considering hits vs. benefits
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from backend.models.player import Player
from backend.services.squad_optimizer import SquadOptimizer, SquadConstraints

logger = logging.getLogger(__name__)

@dataclass
class TransferDecision:
    """Represents a transfer decision for a gameweek"""
    gameweek: int
    player_out: Player
    player_in: Player
    expected_benefit: float  # Expected points gained
    hit_cost: int = 0  # -4 points for each hit
    net_benefit: float = 0  # benefit - hit_cost
    
    def __post_init__(self):
        self.net_benefit = self.expected_benefit - self.hit_cost

@dataclass
class TransferStrategy:
    """Complete transfer strategy for GW1-9"""
    gameweek_strategies: Dict[int, List[TransferDecision]]
    total_net_benefit: float
    total_hits_taken: int
    cumulative_points: Dict[int, float]

class TransferOptimizer:
    """FPL Transfer Strategy Optimizer"""
    
    def __init__(self, squad_optimizer: SquadOptimizer):
        self.squad_optimizer = squad_optimizer
        self.initial_squad = None
        self.transfer_strategies = []
        
    def optimize_transfers(self, initial_squad: List[Player], max_hits_total: int = 8) -> TransferStrategy:
        """Optimize transfer strategy over GW1-9"""
        logger.info("Starting transfer optimization...")
        
        self.initial_squad = initial_squad.copy()
        current_squad = initial_squad.copy()
        
        # Track strategy
        gameweek_strategies = {}
        cumulative_points = {}
        total_hits = 0
        total_net_benefit = 0
        
        # Calculate initial squad points
        initial_points = self.squad_optimizer.calculate_total_expected_points(current_squad)
        cumulative_points[0] = initial_points
        
        logger.info(f"Initial squad expected points: {initial_points:.1f}")
        
        for gameweek in range(1, 10):
            logger.info(f"Optimizing transfers for GW{gameweek}...")
            
            # Find best transfers for this gameweek
            transfers, hits_taken, points_gained = self._find_best_transfers_for_gameweek(
                current_squad, gameweek, max_hits_total - total_hits
            )
            
            if transfers:
                # Apply transfers
                for transfer in transfers:
                    # Remove player out
                    current_squad = [p for p in current_squad if p.id != transfer.player_out.id]
                    # Add player in
                    current_squad.append(transfer.player_in)
                
                # Update squad
                current_squad = self._rebalance_squad(current_squad)
                
                # Calculate new points
                new_points = self.squad_optimizer.calculate_total_expected_points(current_squad)
                points_gained = new_points - cumulative_points[gameweek - 1]
                
                logger.info(f"GW{gameweek}: {len(transfers)} transfers, {hits_taken} hits, +{points_gained:.1f} points")
                
                # Update tracking
                gameweek_strategies[gameweek] = transfers
                total_hits += hits_taken
                total_net_benefit += points_gained - (hits_taken * 4)
                cumulative_points[gameweek] = new_points
            else:
                logger.info(f"GW{gameweek}: No transfers needed")
                gameweek_strategies[gameweek] = []
                cumulative_points[gameweek] = cumulative_points[gameweek - 1]
        
        # Create transfer strategy
        strategy = TransferStrategy(
            gameweek_strategies=gameweek_strategies,
            total_net_benefit=total_net_benefit,
            total_hits_taken=total_hits,
            cumulative_points=cumulative_points
        )
        
        logger.info(f"Transfer optimization complete!")
        logger.info(f"Total hits taken: {total_hits}")
        logger.info(f"Total net benefit: {total_net_benefit:.1f} points")
        logger.info(f"Final expected points: {cumulative_points[9]:.1f}")
        
        return strategy
    
    def _find_best_transfers_for_gameweek(self, current_squad: List[Player], gameweek: int, remaining_hits: int) -> Tuple[List[TransferDecision], int, float]:
        """Find best transfers for a specific gameweek"""
        if remaining_hits <= 0:
            return [], 0, 0
        
        best_transfers = []
        best_net_benefit = 0
        hits_taken = 0
        
        # Get current squad expected points for this gameweek
        current_points = self.squad_optimizer.calculate_expected_points(current_squad, gameweek)
        
        # Try different transfer combinations
        for num_transfers in range(1, min(remaining_hits + 1, 4)):  # Max 3 transfers per week
            transfer_combinations = self._generate_transfer_combinations(
                current_squad, gameweek, num_transfers
            )
            
            for transfers in transfer_combinations:
                # Calculate net benefit
                total_benefit = 0
                total_hit_cost = len(transfers) * 4
                
                for transfer in transfers:
                    total_benefit += transfer.expected_benefit
                
                net_benefit = total_benefit - total_hit_cost
                
                if net_benefit > best_net_benefit:
                    best_net_benefit = net_benefit
                    best_transfers = transfers
                    hits_taken = len(transfers)
        
        return best_transfers, hits_taken, best_net_benefit
    
    def _generate_transfer_combinations(self, current_squad: List[Player], gameweek: int, num_transfers: int) -> List[List[TransferDecision]]:
        """Generate possible transfer combinations"""
        import itertools
        
        transfer_combinations = []
        
        # Get all available players not in current squad
        available_players = [p for p in self.squad_optimizer.players if p not in current_squad]
        
        # Sort by expected points for this gameweek
        available_players.sort(key=lambda p: getattr(p, f'gw{gameweek}_points', 0), reverse=True)
        
        # Generate combinations
        for out_players in itertools.combinations(current_squad, num_transfers):
            for in_players in itertools.combinations(available_players, num_transfers):
                # Check if transfer would be valid
                if self._is_valid_transfer_combination(current_squad, out_players, in_players):
                    transfers = []
                    for out_player, in_player in zip(out_players, in_players):
                        expected_benefit = getattr(in_player, f'gw{gameweek}_points', 0) - getattr(out_player, f'gw{gameweek}_points', 0)
                        
                        transfer = TransferDecision(
                            gameweek=gameweek,
                            player_out=out_player,
                            player_in=in_player,
                            expected_benefit=max(0, expected_benefit)
                        )
                        transfers.append(transfer)
                    
                    transfer_combinations.append(transfers)
        
        return transfer_combinations
    
    def _is_valid_transfer_combination(self, current_squad: List[Player], out_players: Tuple[Player, ...], in_players: Tuple[Player, ...]) -> bool:
        """Check if a transfer combination would result in a valid squad"""
        # Create temporary squad
        temp_squad = [p for p in current_squad if p not in out_players]
        temp_squad.extend(in_players)
        
        # Validate squad rules
        is_valid, _ = self.squad_optimizer.validate_squad_rules(temp_squad)
        return is_valid
    
    def _rebalance_squad(self, squad: List[Player]) -> List[Player]:
        """Rebalance squad to ensure it meets FPL requirements"""
        # Ensure we have exactly 15 players
        if len(squad) > 15:
            # Remove worst players
            squad.sort(key=lambda p: p.total_points)
            squad = squad[-15:]
        elif len(squad) < 15:
            # Add best available players
            available_players = [p for p in self.squad_optimizer.players if p not in squad]
            available_players.sort(key=lambda p: p.total_points, reverse=True)
            
            for player in available_players:
                if len(squad) >= 15:
                    break
                    
                # Check if adding this player would maintain valid squad
                temp_squad = squad + [player]
                if self.squad_optimizer.validate_squad_rules(temp_squad)[0]:
                    squad.append(player)
        
        return squad

def run_transfer_optimization():
    """Run transfer optimization"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting FPL Transfer Optimization...")
    
    try:
        # Initialize
        from backend.database.manager import DatabaseManager
        db_manager = DatabaseManager('fpl.db')
        
        # First optimize initial squad
        squad_optimizer = SquadOptimizer(db_manager)
        initial_squad = squad_optimizer._get_initial_squad()
        
        logger.info(f"Initial squad: {len(initial_squad)} players")
        
        # Then optimize transfers
        transfer_optimizer = TransferOptimizer(squad_optimizer)
        strategy = transfer_optimizer.optimize_transfers(initial_squad)
        
        # Display results
        logger.info("=" * 60)
        logger.info("TRANSFER OPTIMIZATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total hits taken: {strategy.total_hits_taken}")
        logger.info(f"Total net benefit: {strategy.total_net_benefit:.1f} points")
        logger.info("")
        
        logger.info("GAMEWEEK BREAKDOWN:")
        for gw in range(1, 10):
            transfers = strategy.gameweek_strategies.get(gw, [])
            points = strategy.cumulative_points[gw]
            points_gained = points - strategy.cumulative_points[gw - 1] if gw > 0 else points
            
            if transfers:
                logger.info(f"  GW{gw:2d}: {len(transfers)} transfers, {points:6.1f} pts (+{points_gained:5.1f})")
                for transfer in transfers:
                    logger.info(f"    {transfer.player_out.name} → {transfer.player_in.name} (+{transfer.expected_benefit:.1f})")
            else:
                logger.info(f"  GW{gw:2d}: No transfers, {points:6.1f} pts (+{points_gained:5.1f})")
        
        logger.info("")
        logger.info(f"Final expected points: {strategy.cumulative_points[9]:.1f}")
        
        return strategy
        
    except Exception as e:
        logger.error(f"Transfer optimization failed: {e}")
        raise

if __name__ == "__main__":
    run_transfer_optimization()
