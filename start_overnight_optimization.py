#!/usr/bin/env python3
"""
FPL Overnight Optimization Launcher
Simple script to start the comprehensive optimization
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the overnight optimization"""
    print("🚀 FPL Overnight Optimization Launcher")
    print("=" * 50)
    print("This will start the comprehensive FPL optimization")
    print("The process will run in the background and continue overnight")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("❌ Error: Please run this from the FPL project root directory")
        sys.exit(1)
    
    # Check if the optimization script exists
    optimization_script = Path("run_comprehensive_optimization.py")
    if not optimization_script.exists():
        print("❌ Error: Optimization script not found")
        sys.exit(1)
    
    print("\n📋 Starting optimization...")
    print("⏰ This will run overnight (2-4 hours expected)")
    print("📁 Results will be saved in 'results/' directory")
    print("📝 Logs will be saved in 'logs/' directory")
    print("\n💡 You can check progress by:")
    print("   - Looking at the log files in 'logs/' directory")
    print("   - Checking the results in 'results/' directory")
    print("   - The process will continue even if you close this terminal")
    
    # Confirm before starting
    response = input("\n🚀 Start optimization now? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Optimization cancelled")
        sys.exit(0)
    
    try:
        # Start the optimization in the background
        print("\n🚀 Launching optimization...")
        
        # Use nohup to keep it running even if terminal is closed
        cmd = [
            "nohup", 
            sys.executable, 
            str(optimization_script),
            ">", 
            "optimization_output.log", 
            "2>&1", 
            "&"
        ]
        
        # For Windows compatibility, use different approach
        if os.name == 'nt':  # Windows
            cmd = [
                "start", 
                "/B", 
                sys.executable, 
                str(optimization_script)
            ]
            subprocess.run(cmd, shell=True)
        else:  # Unix/Linux/macOS
            subprocess.run(" ".join(cmd), shell=True)
        
        print("✅ Optimization started successfully!")
        print("📁 Check 'optimization_output.log' for immediate output")
        print("📁 Check 'logs/' directory for detailed logs")
        print("📁 Check 'results/' directory for final results")
        print("\n🏁 You can now close this terminal and go to sleep!")
        print("   The optimization will continue running in the background")
        
    except Exception as e:
        print(f"❌ Failed to start optimization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
