#!/usr/bin/env python3
"""
Launcher script for the new modular FPL backend
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import run_app

if __name__ == '__main__':
    run_app()
