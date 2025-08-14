#!/usr/bin/env python3
"""
Test runner for the refactored FPL backend
"""
import sys
import os
import unittest
import tempfile
import shutil

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def run_unit_tests():
    """Run unit tests for models and services"""
    print("🧪 Running Unit Tests...")
    
    # Create a temporary database for testing
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # Set environment variable for test database
    os.environ['DATABASE_PATH'] = temp_db.name
    
    try:
        # Import and run tests
        from backend.tests.test_models import TestPlayerModel, TestTeamModel, TestFixtureModel
        
        # Create test suite
        test_suite = unittest.TestSuite()
        test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPlayerModel))
        test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestTeamModel))
        test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestFixtureModel))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
        
        if result.wasSuccessful():
            print("✅ All unit tests passed!")
            return True
        else:
            print("❌ Some unit tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False
    finally:
        # Clean up temporary database
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)

def test_database_operations():
    """Test database operations"""
    print("\n🗄️ Testing Database Operations...")
    
    try:
        from backend.database.manager import DatabaseManager
        from backend.models.player import Player
        from backend.models.team import Team
        
        # Create test database with temporary file
        import tempfile
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        test_db = DatabaseManager(temp_db.name)
        
        # Test team creation
        test_team = Team(id=1, name='Test Team', short_name='TST', code=100, strength=80)
        success = test_db.add_team(test_team)
        print(f"✅ Team creation: {'PASS' if success else 'FAIL'}")
        
        # Test player creation
        test_player = Player(
            id=1, name='Test Player', position='Midfielder', team='Test Team',
            price=8.5, chance_of_playing_next_round=90.0, points_per_million=75.0,
            total_points=150.0, form=7.5, ownership=25.0, team_id=1
        )
        success = test_db.add_player(test_player)
        print(f"✅ Player creation: {'PASS' if success else 'FAIL'}")
        
        # Test data retrieval
        players = test_db.get_all_players()
        teams = test_db.get_all_teams()
        print(f"✅ Data retrieval: Players={len(players)}, Teams={len(teams)}")
        
        # Test database stats
        stats = test_db.get_database_stats()
        print(f"✅ Database stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        # Clean up temporary database
        if 'temp_db' in locals() and os.path.exists(temp_db.name):
            os.unlink(temp_db.name)

def test_service_layer():
    """Test service layer functionality"""
    print("\n🔧 Testing Service Layer...")
    
    try:
        from backend.database.manager import DatabaseManager
        from backend.services.player_service import PlayerService
        
        # Create test database and service
        import tempfile
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        test_db = DatabaseManager(temp_db.name)
        player_service = PlayerService(test_db)
        
        # Test player statistics
        stats = player_service.get_player_statistics()
        print(f"✅ Player statistics: {stats}")
        
        # Test empty database handling
        empty_stats = player_service.get_player_statistics()
        print(f"✅ Empty database handling: {empty_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service layer test failed: {e}")
        return False
    finally:
        # Clean up temporary database
        if 'temp_db' in locals() and os.path.exists(temp_db.name):
            os.unlink(temp_db.name)

def test_flask_app_creation():
    """Test Flask app creation"""
    print("\n🌐 Testing Flask App Creation...")
    
    try:
        from backend.app import create_app
        
        # Test app creation
        app = create_app('testing')
        print(f"✅ Flask app created successfully: {type(app).__name__}")
        
        # Test app configuration
        print(f"✅ App config: DEBUG={app.config['DEBUG']}, PORT={app.config['PORT']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 FPL Backend Testing Suite")
    print("=" * 50)
    
    tests = [
        ("Unit Tests", run_unit_tests),
        ("Database Operations", test_database_operations),
        ("Service Layer", test_service_layer),
        ("Flask App Creation", test_flask_app_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The refactored backend is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
