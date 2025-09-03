#!/usr/bin/env python3

from backend.app import create_app
from backend.services.squad_service import SquadService

def test_squad_service():
    try:
        print("Creating app...")
        app = create_app()
        print("App created successfully")
        
        with app.app_context():
            print("Creating SquadService...")
            service = SquadService(app.db_manager)
            print("SquadService created successfully")
            
            print("Testing squad generation...")
            data = service.get_optimal_squad_for_gw1_9()
            print(f"Squad data: {len(data) if data else 'None'}")
            
            if data:
                print(f"GW1 starting XI: {len(data[1]['starting_xi'])} players")
                print(f"GW1 bench: {len(data[1]['bench'])} players")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_squad_service()
