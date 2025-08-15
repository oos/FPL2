#!/usr/bin/env python3
"""
Comprehensive FPL Optimization Runner
Runs both squad optimization and transfer optimization overnight
"""

import logging
import json
import time
from datetime import datetime
from pathlib import Path
from backend.services.squad_optimizer import run_optimization
from backend.services.transfer_optimizer import run_transfer_optimization

def setup_logging():
    """Setup comprehensive logging"""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Setup file logging
    log_file = log_dir / f"comprehensive_optimization_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    return log_file

def save_comprehensive_results(squad_result, transfer_result, timestamp):
    """Save comprehensive optimization results to JSON file"""
    # Create results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Prepare result for JSON serialization
    comprehensive_result = {
        'timestamp': timestamp,
        'squad_optimization': {
            'total_expected_points': squad_result['total_expected_points'],
            'formation': squad_result['formation'],
            'squad': [
                {
                    'name': player.name,
                    'position': player.position,
                    'team': player.team,
                    'total_points': player.total_points,
                    'price': player.price,
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
                for player in squad_result['squad']
            ],
            'starting_xi': [
                {
                    'name': player.name,
                    'position': player.position,
                    'team': player.team,
                    'total_points': player.total_points,
                    'price': player.price,
                }
                for player in squad_result['starting_xi']
            ],
            'team_distribution': squad_result['team_distribution'],
            'position_distribution': squad_result['position_distribution'],
            'gameweek_breakdown': squad_result['gameweek_breakdown'],
            'optimization_stats': squad_result['optimization_stats']
        },
        'transfer_optimization': {
            'total_hits_taken': transfer_result.total_hits_taken,
            'total_net_benefit': transfer_result.total_net_benefit,
            'cumulative_points': transfer_result.cumulative_points,
            'gameweek_strategies': {
                gw: [
                    {
                        'player_out': {
                            'name': transfer.player_out.name,
                            'position': transfer.player_out.position,
                            'team': transfer.player_out.team
                        },
                        'player_in': {
                            'name': transfer.player_in.name,
                            'position': transfer.player_in.position,
                            'team': transfer.player_in.team
                        },
                        'expected_benefit': transfer.expected_benefit,
                        'hit_cost': transfer.hit_cost,
                        'net_benefit': transfer.net_benefit
                    }
                    for transfer in transfers
                ]
                for gw, transfers in transfer_result.gameweek_strategies.items()
            }
        }
    }
    
    # Save to JSON file
    results_file = results_dir / f"comprehensive_optimization_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(comprehensive_result, f, indent=2)
    
    return results_file

def main():
    """Main comprehensive optimization runner"""
    print("🚀 FPL Comprehensive Optimization - Overnight Run")
    print("=" * 70)
    print("This will run both squad optimization and transfer optimization")
    print("Expected runtime: 2-4 hours depending on data size")
    print("=" * 70)
    
    # Setup logging
    log_file = setup_logging()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger = logging.getLogger(__name__)
    logger.info("Starting FPL Comprehensive Optimization overnight run")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Timestamp: {timestamp}")
    
    start_time = time.time()
    
    try:
        # Phase 1: Squad Optimization
        print("\n🎯 PHASE 1: Squad Optimization")
        print("-" * 40)
        logger.info("Starting Phase 1: Squad Optimization")
        
        squad_start = time.time()
        squad_result = run_optimization()
        squad_time = time.time() - squad_start
        
        logger.info(f"Squad optimization completed in {squad_time:.2f} seconds")
        print(f"✅ Squad optimization completed in {squad_time:.2f} seconds")
        
        # Phase 2: Transfer Optimization
        print("\n🔄 PHASE 2: Transfer Optimization")
        print("-" * 40)
        logger.info("Starting Phase 2: Transfer Optimization")
        
        transfer_start = time.time()
        transfer_result = run_transfer_optimization()
        transfer_time = time.time() - transfer_start
        
        logger.info(f"Transfer optimization completed in {transfer_time:.2f} seconds")
        print(f"✅ Transfer optimization completed in {transfer_time:.2f} seconds")
        
        # Calculate total runtime
        end_time = time.time()
        total_runtime = end_time - start_time
        
        logger.info(f"Comprehensive optimization completed successfully in {total_runtime:.2f} seconds")
        
        # Save comprehensive results
        results_file = save_comprehensive_results(squad_result, transfer_result, timestamp)
        logger.info(f"Comprehensive results saved to: {results_file}")
        
        # Display comprehensive summary
        print("\n" + "=" * 70)
        print("🎯 COMPREHENSIVE OPTIMIZATION COMPLETE!")
        print("=" * 70)
        print(f"Total Runtime: {total_runtime:.2f} seconds ({total_runtime/3600:.1f} hours)")
        print(f"Results saved to: {results_file}")
        print(f"Log file: {log_file}")
        
        # Squad Summary
        print("\n🏆 OPTIMAL SQUAD SUMMARY:")
        print("-" * 40)
        print(f"Total Expected Points (GW1-9): {squad_result['total_expected_points']:.1f}")
        print(f"Formation: {squad_result['formation']}")
        print(f"Starting XI: {len(squad_result['starting_xi'])} players")
        print(f"Bench: {len(squad_result['squad']) - len(squad_result['starting_xi'])} players")
        
        # Transfer Summary
        print("\n🔄 TRANSFER STRATEGY SUMMARY:")
        print("-" * 40)
        print(f"Total Hits Taken: {transfer_result.total_hits_taken}")
        print(f"Total Net Benefit: {transfer_result.total_net_benefit:.1f} points")
        print(f"Final Expected Points: {transfer_result.cumulative_points[9]:.1f}")
        
        # Gameweek Breakdown
        print("\n📊 GAMEWEEK BREAKDOWN:")
        print("-" * 40)
        for gw in range(1, 10):
            transfers = transfer_result.gameweek_strategies.get(gw, [])
            points = transfer_result.cumulative_points[gw]
            points_gained = points - transfer_result.cumulative_points[gw - 1] if gw > 0 else points
            
            if transfers:
                print(f"GW{gw:2d}: {len(transfers)} transfers, {points:6.1f} pts (+{points_gained:5.1f})")
                for transfer in transfers:
                    print(f"    {transfer.player_out.name} → {transfer.player_in.name} (+{transfer.expected_benefit:.1f})")
            else:
                print(f"GW{gw:2d}: No transfers, {points:6.1f} pts (+{points_gained:5.1f})")
        
        # Performance Summary
        print("\n⚡ PERFORMANCE SUMMARY:")
        print("-" * 40)
        print(f"Squad Optimization: {squad_time:.2f}s")
        print(f"Transfer Optimization: {transfer_time:.2f}s")
        print(f"Total Time: {total_runtime:.2f}s")
        print(f"Improvements Found: {squad_result['optimization_stats']['improvements']}")
        
        print("\n🏁 Comprehensive optimization complete!")
        print("Check the log and results files for full details.")
        print("Your optimal FPL strategy is ready! 🎉")
        
    except Exception as e:
        logger.error(f"Comprehensive optimization failed: {e}")
        print(f"\n❌ Optimization failed: {e}")
        print("Check the log file for details.")
        raise

if __name__ == "__main__":
    main()
