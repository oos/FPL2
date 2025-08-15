#!/usr/bin/env python3
"""
FPL Squad Optimization Service
Finds the optimal squad for GW1-9 considering FPL rules, expected points, and transfer strategy
"""

import logging
import itertools
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from backend.models.player import Player
from backend.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

@dataclass
class SquadConstraints:
    """FPL squad constraints and rules"""
    max_players_per_team: int = 3
    max_players_per_position: Dict[str, int] = None
    min_players_per_position: Dict[str, int] = None
    max_transfers_per_week: int = 2  # Including free transfer
    max_hits_per_week: int = 1  # Additional hits beyond free transfer
    
    def __post_init__(self):
        if self.max_players_per_position is None:
            self.max_players_per_position = {
                'Goalkeeper': 2,
                'Defender': 5,
                'Midfielder': 5,
                'Forward': 3
            }
        if self.min_players_per_position is None:
            self.min_players_per_position = {
                'Goalkeeper': 1,
                'Defender': 3,
                'Midfielder': 3,
                'Forward': 1
            }

@dataclass
class Transfer:
    """Represents a transfer between gameweeks"""
    gameweek: int
    player_out: Player
    player_in: Player
    hit_cost: int = 0  # -4 points for each hit

@dataclass
class SquadState:
    """Represents squad state at a specific gameweek"""
    gameweek: int
    players: List[Player]
    transfers: List[Transfer]
    total_points: float
    total_hits: int
    formation: str

class SquadOptimizer:
    """FPL Squad Optimization Engine"""
    
    def __init__(self, db_manager: DatabaseManager, constraints: SquadConstraints = None):
        self.db_manager = db_manager
        self.constraints = constraints or SquadConstraints()
        self.players = []
        self.best_squad = None
        self.best_total_points = 0
        
    def load_players(self) -> None:
        """Load all players with their expected points"""
        logger.info("Loading players with expected points...")
        self.players = self.db_manager.get_all_players()
        logger.info(f"Loaded {len(self.players)} players")
        
        # Filter out players with no expected points
        self.players = [p for p in self.players if p.total_points > 0]
        logger.info(f"Filtered to {len(self.players)} players with expected points")
    
    def validate_squad_rules(self, squad: List[Player]) -> Tuple[bool, List[str]]:
        """Validate squad against FPL rules"""
        errors = []
        
        # Check team distribution
        team_counts = {}
        for player in squad:
            team_counts[player.team] = team_counts.get(player.team, 0) + 1
            if team_counts[player.team] > self.constraints.max_players_per_team:
                errors.append(f"Too many players from {player.team}: {team_counts[player.team]}")
        
        # Check position distribution
        position_counts = {}
        for player in squad:
            position_counts[player.position] = position_counts.get(player.position, 0) + 1
        
        for position, min_count in self.constraints.min_players_per_position.items():
            if position_counts.get(position, 0) < min_count:
                errors.append(f"Not enough {position}s: {position_counts.get(position, 0)} < {min_count}")
        
        for position, max_count in self.constraints.max_players_per_position.items():
            if position_counts.get(position, 0) > max_count:
                errors.append(f"Too many {position}s: {position_counts.get(position, 0)} > {max_count}")
        
        return len(errors) == 0, errors
    
    def calculate_formation(self, squad: List[Player]) -> str:
        """Calculate formation string (e.g., '4-4-2')"""
        position_counts = {}
        for player in squad:
            position_counts[player.position] = position_counts.get(player.position, 0) + 1
        
        # Get starting XI (excluding bench)
        starting_xi = self.get_starting_xi(squad)
        starting_position_counts = {}
        for player in starting_xi:
            starting_position_counts[player.position] = starting_position_counts.get(player.position, 0) + 1
        
        # Format: GK-DEF-MID-FWD
        formation = f"{starting_position_counts.get('Goalkeeper', 0)}-{starting_position_counts.get('Defender', 0)}-{starting_position_counts.get('Midfielder', 0)}-{starting_position_counts.get('Forward', 0)}"
        return formation
    
    def get_starting_xi(self, squad: List[Player]) -> List[Player]:
        """Get starting XI based on expected points"""
        # Sort by total expected points
        sorted_squad = sorted(squad, key=lambda p: p.total_points, reverse=True)
        
        # Ensure we have at least one player from each required position
        starting_xi = []
        required_positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
        
        # Add best player from each required position first
        for position in required_positions:
            for player in sorted_squad:
                if player.position == position and player not in starting_xi:
                    starting_xi.append(player)
                    break
        
        # Fill remaining spots with best available players
        remaining_spots = 11 - len(starting_xi)
        for player in sorted_squad:
            if len(starting_xi) >= 11:
                break
            if player not in starting_xi:
                starting_xi.append(player)
        
        return starting_xi[:11]
    
    def calculate_expected_points(self, squad: List[Player], gameweek: int) -> float:
        """Calculate expected points for a squad in a specific gameweek"""
        starting_xi = self.get_starting_xi(squad)
        total_points = 0
        
        for player in starting_xi:
            gw_points = getattr(player, f'gw{gameweek}_points', 0)
            total_points += gw_points
        
        return total_points
    
    def calculate_total_expected_points(self, squad: List[Player]) -> float:
        """Calculate total expected points across GW1-9"""
        total_points = 0
        for gw in range(1, 10):
            total_points += self.calculate_expected_points(squad, gw)
        return total_points
    
    def optimize_squad(self, max_iterations: int = 10000) -> Dict:
        """Main optimization function"""
        logger.info("Starting squad optimization...")
        
        if not self.players:
            self.load_players()
        
        # Start with best players by total expected points
        initial_squad = self._get_initial_squad()
        logger.info(f"Initial squad total points: {self.calculate_total_expected_points(initial_squad):.1f}")
        
        best_squad = initial_squad.copy()
        best_points = self.calculate_total_expected_points(best_squad)
        
        iteration = 0
        improvements = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Generate candidate squad
            candidate_squad = self._generate_candidate_squad(best_squad)
            
            # Validate candidate
            is_valid, errors = self.validate_squad_rules(candidate_squad)
            if not is_valid:
                continue
            
            # Calculate points
            candidate_points = self.calculate_total_expected_points(candidate_squad)
            
            # Update if better
            if candidate_points > best_points:
                best_squad = candidate_squad.copy()
                best_points = candidate_points
                improvements += 1
                logger.info(f"Iteration {iteration}: New best squad with {best_points:.1f} points (improvement: +{candidate_points - best_points:.1f})")
            
            # Progress update
            if iteration % 1000 == 0:
                logger.info(f"Completed {iteration} iterations, best points: {best_points:.1f}")
        
        logger.info(f"Optimization complete! Best squad: {best_points:.1f} points after {improvements} improvements")
        
        # Build result
        result = {
            'total_expected_points': best_points,
            'squad': best_squad,
            'starting_xi': self.get_starting_xi(best_squad),
            'formation': self.calculate_formation(best_squad),
            'team_distribution': self._get_team_distribution(best_squad),
            'position_distribution': self._get_position_distribution(best_squad),
            'gameweek_breakdown': self._get_gameweek_breakdown(best_squad),
            'optimization_stats': {
                'iterations': iteration,
                'improvements': improvements
            }
        }
        
        return result
    
    def _get_initial_squad(self) -> List[Player]:
        """Get initial squad based on best expected points"""
        # Sort by total expected points
        sorted_players = sorted(self.players, key=lambda p: p.total_points, reverse=True)
        
        # Build balanced squad
        squad = []
        position_counts = {'Goalkeeper': 0, 'Defender': 0, 'Midfielder': 0, 'Forward': 0}
        team_counts = {}
        
        for player in sorted_players:
            if len(squad) >= 15:  # FPL squad size
                break
                
            # Check position limits
            if position_counts[player.position] >= self.constraints.max_players_per_position[player.position]:
                continue
                
            # Check team limits
            if team_counts.get(player.team, 0) >= self.constraints.max_players_per_team:
                continue
                
            squad.append(player)
            position_counts[player.position] += 1
            team_counts[player.team] = team_counts.get(player.team, 0) + 1
        
        return squad
    
    def _generate_candidate_squad(self, current_squad: List[Player]) -> List[Player]:
        """Generate a candidate squad by making small changes"""
        import random
        
        candidate = current_squad.copy()
        
        # Randomly swap 1-3 players
        num_swaps = random.randint(1, 3)
        
        for _ in range(num_swaps):
            if len(candidate) < 2:
                break
                
            # Pick two random positions to swap
            idx1, idx2 = random.sample(range(len(candidate)), 2)
            
            # Find replacement players
            player1 = candidate[idx1]
            player2 = candidate[idx2]
            
            # Find best available replacements
            available_players = [p for p in self.players if p not in candidate]
            if available_players:
                # Try to find better players for these positions
                for new_player in sorted(available_players, key=lambda p: p.total_points, reverse=True):
                    # Check if swap would improve squad
                    temp_squad = candidate.copy()
                    temp_squad[idx1] = new_player
                    
                    is_valid, _ = self.validate_squad_rules(temp_squad)
                    if is_valid:
                        candidate = temp_squad
                        break
        
        return candidate
    
    def _get_team_distribution(self, squad: List[Player]) -> Dict[str, int]:
        """Get team distribution in squad"""
        team_counts = {}
        for player in squad:
            team_counts[player.team] = team_counts.get(player.team, 0) + 1
        return team_counts
    
    def _get_position_distribution(self, squad: List[Player]) -> Dict[str, int]:
        """Get position distribution in squad"""
        position_counts = {}
        for player in squad:
            position_counts[player.position] = position_counts.get(player.position, 0) + 1
        return position_counts
    
    def _get_gameweek_breakdown(self, squad: List[Player]) -> Dict[int, float]:
        """Get expected points breakdown by gameweek"""
        breakdown = {}
        for gw in range(1, 10):
            breakdown[gw] = self.calculate_expected_points(squad, gw)
        return breakdown

def run_optimization():
    """Run the squad optimization"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting FPL Squad Optimization...")
    
    try:
        # Initialize
        db_manager = DatabaseManager('fpl.db')
        optimizer = SquadOptimizer(db_manager)
        
        # Run optimization
        result = optimizer.optimize_squad(max_iterations=50000)
        
        # Display results
        logger.info("=" * 60)
        logger.info("OPTIMIZATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Expected Points (GW1-9): {result['total_expected_points']:.1f}")
        logger.info(f"Formation: {result['formation']}")
        logger.info("")
        
        logger.info("STARTING XI:")
        for i, player in enumerate(result['starting_xi'], 1):
            logger.info(f"{i:2d}. {player.name:20s} ({player.position:12s}) - {player.team:15s} - {player.total_points:5.1f} pts")
        
        logger.info("")
        logger.info("BENCH:")
        bench_players = [p for p in result['squad'] if p not in result['starting_xi']]
        for i, player in enumerate(bench_players, 1):
            logger.info(f"{i:2d}. {player.name:20s} ({player.position:12s}) - {player.team:15s} - {player.total_points:5.1f} pts")
        
        logger.info("")
        logger.info("TEAM DISTRIBUTION:")
        for team, count in sorted(result['team_distribution'].items()):
            logger.info(f"  {team:15s}: {count} players")
        
        logger.info("")
        logger.info("POSITION DISTRIBUTION:")
        for position, count in sorted(result['position_distribution'].items()):
            logger.info(f"  {position:12s}: {count} players")
        
        logger.info("")
        logger.info("GAMEWEEK BREAKDOWN:")
        for gw, points in result['gameweek_breakdown'].items():
            logger.info(f"  GW{gw:2d}: {points:5.1f} points")
        
        logger.info("")
        logger.info("OPTIMIZATION STATS:")
        logger.info(f"  Iterations: {result['optimization_stats']['iterations']:,}")
        logger.info(f"  Improvements: {result['optimization_stats']['improvements']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise

if __name__ == "__main__":
    run_optimization()
