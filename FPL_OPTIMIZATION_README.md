# 🏆 FPL Squad Optimization System

## Overview

This system provides comprehensive FPL (Fantasy Premier League) squad optimization for GW1-9, including:

- **Squad Optimization**: Finds the best 15-player squad considering FPL rules
- **Transfer Strategy**: Optimizes transfers over 9 gameweeks considering hits vs. benefits
- **Rule Compliance**: Ensures all FPL rules are followed (3 players max per team, position limits, etc.)

## 🚀 Quick Start

### Option 1: Simple Launcher (Recommended)
```bash
python start_overnight_optimization.py
```
This will start the optimization in the background and continue running overnight.

### Option 2: Direct Run
```bash
python run_comprehensive_optimization.py
```
This runs the optimization in the foreground (terminal must stay open).

### Option 3: Individual Components
```bash
# Squad optimization only
python backend/services/squad_optimizer.py

# Transfer optimization only  
python backend/services/transfer_optimizer.py
```

## 📁 Output Files

The system creates several output files:

- **`logs/`** - Detailed optimization logs with timestamps
- **`results/`** - JSON files with complete optimization results
- **`optimization_output.log`** - Immediate console output (if using launcher)

## 🎯 What the System Does

### Phase 1: Squad Optimization
1. **Loads all players** with their expected points for GW1-9
2. **Applies FPL rules**:
   - Max 3 players per team
   - Position limits (1-2 GK, 3-5 DEF, 3-5 MID, 1-3 FWD)
   - Squad size: exactly 15 players
3. **Optimizes player selection** using iterative improvement
4. **Calculates formation** based on starting XI
5. **Validates squad compliance** with all FPL rules

### Phase 2: Transfer Optimization
1. **Analyzes each gameweek** (GW1-9)
2. **Considers transfer options**:
   - Free transfer each week
   - Additional hits (-4 points each)
   - Rolling over transfers when beneficial
3. **Calculates net benefit** of each transfer
4. **Optimizes transfer timing** to maximize total points
5. **Provides weekly transfer recommendations**

## 📊 Expected Results

The system will output:

- **Optimal Squad**: 15 players with positions and teams
- **Starting XI**: Best 11 players for each gameweek
- **Formation**: Tactical formation (e.g., "1-4-4-2")
- **Transfer Strategy**: Weekly transfer recommendations
- **Points Projection**: Expected points for each gameweek
- **Total Projection**: Cumulative points across GW1-9

## ⚙️ Configuration

### FPL Rules (Configurable)
```python
@dataclass
class SquadConstraints:
    max_players_per_team: int = 3
    max_players_per_position: Dict[str, int] = {
        'Goalkeeper': 2,
        'Defender': 5,
        'Midfielder': 5,
        'Forward': 3
    }
    min_players_per_position: Dict[str, int] = {
        'Goalkeeper': 1,
        'Defender': 3,
        'Midfielder': 3,
        'Forward': 1
    }
    max_transfers_per_week: int = 2
    max_hits_per_week: int = 1
```

### Optimization Parameters
```python
# In squad_optimizer.py
result = optimizer.optimize_squad(max_iterations=50000)

# In transfer_optimizer.py  
strategy = transfer_optimizer.optimize_transfers(initial_squad, max_hits_total=8)
```

## 🔧 Technical Details

### Algorithm
- **Squad Optimization**: Iterative improvement with random player swaps
- **Transfer Optimization**: Dynamic programming approach considering all transfer combinations
- **Rule Validation**: Constraint checking at each optimization step

### Performance
- **Expected Runtime**: 2-4 hours depending on data size
- **Memory Usage**: Moderate (loads all players into memory)
- **Scalability**: Handles 500+ players efficiently

### Data Requirements
- **Player Database**: Must contain expected points for GW1-9
- **Position Data**: Must be one of: Goalkeeper, Defender, Midfielder, Forward
- **Team Data**: Must match FPL team names
- **Price Data**: Player values for budget considerations

## 📋 Example Output

```
🎯 COMPREHENSIVE OPTIMIZATION COMPLETE!
======================================================================
Total Runtime: 12745.32 seconds (3.5 hours)
Results saved to: results/comprehensive_optimization_20241201_235959.json
Log file: logs/comprehensive_optimization_20241201_235959.log

🏆 OPTIMAL SQUAD SUMMARY:
----------------------------------------
Total Expected Points (GW1-9): 847.3
Formation: 1-4-4-2
Starting XI: 11 players
Bench: 4 players

🔄 TRANSFER STRATEGY SUMMARY:
----------------------------------------
Total Hits Taken: 6
Total Net Benefit: 23.7 points
Final Expected Points: 871.0

📊 GAMEWEEK BREAKDOWN:
----------------------------------------
GW 1: No transfers,  94.2 pts (+ 94.2)
GW 2: 1 transfers,  96.8 pts (+  2.6)
    M.Salah → K.De Bruyne (+3.2)
GW 3: No transfers,  98.1 pts (+  1.3)
...
```

## 🚨 Troubleshooting

### Common Issues

1. **"No players found"**
   - Check database has player data
   - Verify expected points columns exist (gw1_points, gw2_points, etc.)

2. **"Invalid squad"**
   - Check FPL rule compliance
   - Verify position and team data is correct

3. **"Optimization too slow"**
   - Reduce max_iterations parameter
   - Check system resources

### Debug Mode
Enable detailed logging by modifying log levels in the scripts.

## 🔮 Future Enhancements

- **Captain Selection**: Optimize captain choices for each gameweek
- **Bench Boost**: Consider bench boost chip usage
- **Wildcard**: Plan wildcard usage strategically
- **Fixture Difficulty**: Weight points by fixture difficulty
- **Form Trends**: Consider recent form in optimization

## 📞 Support

If you encounter issues:
1. Check the log files in `logs/` directory
2. Verify database contains required data
3. Check FPL rule compliance
4. Review error messages in console output

---

**Good luck with your FPL season! 🏆⚽**
