#!/usr/bin/env python3
"""
FPL Squad Optimization Runner
Runs the squad optimization overnight and saves results
"""

import logging
import json
import time
from datetime import datetime
from pathlib import Path
from backend.services.squad_optimizer import run_optimization

def setup_logging():
    """Setup comprehensive logging"""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Setup file logging
    log_file = log_dir / f"squad_optimization_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    return log_file

def save_results(result, timestamp):
    """Save optimization results to JSON file"""
    # Create results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Prepare result for JSON serialization
    serializable_result = {
        'timestamp': timestamp,
        'total_expected_points': result['total_expected_points'],
        'formation': result['formation'],
        'squad': [
            {
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'total_points': player.total_points,
                'price': player.price,
                'gw1_points': player.gw1_points,
                'gw2_points': player.gw2_points,
                'gw3_points': player.gw3_points,
                'gw4_points': player.gw4_points,
                'gw5_points': player.gw5_points,
                'gw6_points': player.gw6_points,
                'gw7_points': player.gw7_points,
                'gw8_points': player.gw8_points,
                'gw9_points': player.gw9_points,
            }
            for player in result['squad']
        ],
        'starting_xi': [
            {
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'total_points': player.total_points,
                'price': player.price,
            }
            for player in result['starting_xi']
        ],
        'team_distribution': result['team_distribution'],
        'position_distribution': result['position_distribution'],
        'gameweek_breakdown': result['gameweek_breakdown'],
        'optimization_stats': result['optimization_stats']
    }
    
    # Save to JSON file
    results_file = results_dir / f"optimal_squad_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(serializable_result, f, indent=2)
    
    return results_file

def main():
    """Main optimization runner"""
    print("🚀 FPL Squad Optimization - Overnight Run")
    print("=" * 60)
    
    # Setup logging
    log_file = setup_logging()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger = logging.getLogger(__name__)
    logger.info("Starting FPL Squad Optimization overnight run")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Timestamp: {timestamp}")
    
    start_time = time.time()
    
    try:
        # Run optimization
        logger.info("Initiating squad optimization...")
        result = run_optimization()
        
        # Calculate runtime
        end_time = time.time()
        runtime = end_time - start_time
        
        logger.info(f"Optimization completed successfully in {runtime:.2f} seconds")
        
        # Save results
        results_file = save_results(result, timestamp)
        logger.info(f"Results saved to: {results_file}")
        
        # Display summary
        print("\n" + "=" * 60)
        print("🎯 OPTIMIZATION COMPLETE!")
        print("=" * 60)
        print(f"Total Expected Points (GW1-9): {result['total_expected_points']:.1f}")
        print(f"Formation: {result['formation']}")
        print(f"Runtime: {runtime:.2f} seconds")
        print(f"Results saved to: {results_file}")
        print(f"Log file: {log_file}")
        
        # Display optimal squad
        print("\n🏆 OPTIMAL SQUAD:")
        print("-" * 60)
        print("STARTING XI:")
        for i, player in enumerate(result['starting_xi'], 1):
            print(f"{i:2d}. {player.name:20s} ({player.position:12s}) - {player.team:15s} - {player.total_points:5.1f} pts")
        
        print("\nBENCH:")
        bench_players = [p for p in result['squad'] if p not in result['starting_xi']]
        for i, player in enumerate(bench_players, 1):
            print(f"{i:2d}. {player.name:20s} ({player.position:12s}) - {player.team:15s} - {player.total_points:5.1f} pts")
        
        print("\n📊 GAMEWEEK BREAKDOWN:")
        for gw, points in result['gameweek_breakdown'].items():
            print(f"  GW{gw:2d}: {points:5.1f} points")
        
        print("\n🏁 Run complete! Check the log and results files for full details.")
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        print(f"\n❌ Optimization failed: {e}")
        print("Check the log file for details.")
        raise

if __name__ == "__main__":
    main()
