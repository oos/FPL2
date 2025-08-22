#!/usr/bin/env python3
"""
Entry point for running the Flask application
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from backend.app import create_app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"Starting FPL application on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Database path: {app.config['DATABASE_PATH']}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
