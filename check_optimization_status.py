#!/usr/bin/env python3
"""Check optimization status"""

import os
import time
from pathlib import Path

def check_status():
    """Check the current status of the optimization"""
    print("🔍 FPL Optimization Status Check")
    print("=" * 40)
    
    # Check if process is running
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'run_comprehensive_optimization.py' in result.stdout:
            print("✅ Optimization is RUNNING")
            
            # Get process info
            lines = result.stdout.split('\n')
            for line in lines:
                if 'run_comprehensive_optimization.py' in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        print(f"📊 Process ID: {pid}")
                        break
        else:
            print("❌ Optimization is NOT running")
            return
    except:
        print("❌ Could not check process status")
        return
    
    # Check latest log
    log_dir = Path("logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("comprehensive_optimization_*.log"))
        if log_files:
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            print(f"📝 Latest log: {latest_log.name}")
            
            # Show last few lines
            try:
                with open(latest_log, 'r') as f:
                    lines = f.readlines()
                    print("\n📋 Last 10 log entries:")
                    for line in lines[-10:]:
                        print(f"   {line.strip()}")
            except:
                print("   Could not read log file")
    
    # Check results
    results_dir = Path("results")
    if results_dir.exists():
        result_files = list(results_dir.glob("comprehensive_optimization_*.json"))
        if result_files:
            print(f"\n📁 Results files: {len(result_files)}")
            for rf in result_files[-3:]:  # Show last 3
                print(f"   {rf.name}")
        else:
            print("\n📁 No results files yet")
    
    # Check output log
    if Path("optimization_output.log").exists():
        print(f"\n📄 Output log: optimization_output.log")
        try:
            with open("optimization_output.log", 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"   Last line: {lines[-1].strip()}")
        except:
            print("   Could not read output log")

if __name__ == "__main__":
    check_status()
