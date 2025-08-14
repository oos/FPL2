#!/usr/bin/env python3
"""
Integration tests for the FPL backend
"""
import sys
import os
import time
import requests
import subprocess
import signal

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def start_backend():
    """Start the backend server"""
    print("🚀 Starting backend server...")
    
    try:
        # Start the backend process
        process = subprocess.Popen(
            [sys.executable, 'run_backend.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(5)
        
        return process
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def test_api_endpoints():
    """Test all API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:5001"
    tests = []
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint: PASS")
            tests.append(True)
        else:
            print(f"❌ Health endpoint: FAIL (Status: {response.status_code})")
            tests.append(False)
    except Exception as e:
        print(f"❌ Health endpoint: FAIL ({e})")
        tests.append(False)
    
    # Test players endpoint
    try:
        response = requests.get(f"{base_url}/api/players", timeout=10)
        if response.status_code == 200:
            print("✅ Players API endpoint: PASS")
            tests.append(True)
        else:
            print(f"❌ Players API endpoint: FAIL (Status: {response.status_code})")
            tests.append(False)
    except Exception as e:
        print(f"❌ Players API endpoint: FAIL ({e})")
        tests.append(False)
    
    # Test teams endpoint
    try:
        response = requests.get(f"{base_url}/api/teams", timeout=10)
        if response.status_code == 200:
            print("✅ Teams API endpoint: PASS")
            tests.append(True)
        else:
            print(f"❌ Teams API endpoint: FAIL (Status: {response.status_code})")
            tests.append(False)
    except Exception as e:
        print(f"❌ Teams API endpoint: FAIL ({e})")
        tests.append(False)
    
    # Test FDR endpoint
    try:
        response = requests.get(f"{base_url}/api/fdr", timeout=10)
        if response.status_code == 200:
            print("✅ FDR API endpoint: PASS")
            tests.append(True)
        else:
            print(f"❌ FDR API endpoint: FAIL (Status: {response.status_code})")
            tests.append(False)
    except Exception as e:
        print(f"❌ FDR API endpoint: FAIL ({e})")
        tests.append(False)
    
    return tests

def test_web_pages():
    """Test web page rendering"""
    print("\n📄 Testing Web Pages...")
    
    base_url = "http://localhost:5001"
    tests = []
    
    # Test FDR page
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200 and "Fixture Difficulty Ratings" in response.text:
            print("✅ FDR page: PASS")
            tests.append(True)
        else:
            print(f"❌ FDR page: FAIL (Status: {response.status_code})")
            tests.append(False)
    except Exception as e:
        print(f"❌ FDR page: FAIL ({e})")
        tests.append(False)
    
    # Test Players page
    try:
        response = requests.get(f"{base_url}/players", timeout=10)
        if response.status_code == 200 and "FPL Players" in response.text:
            print("✅ Players page: PASS")
            tests.append(True)
        else:
            print(f"❌ Players page: FAIL (Status: {response.status_code})")
            tests.append(False)
    except Exception as e:
        print(f"❌ Players page: FAIL ({e})")
        tests.append(False)
    
    # Test Squad page
    try:
        response = requests.get(f"{base_url}/squad", timeout=10)
        if response.status_code == 200 and "FPL Optimal Squad" in response.text:
            print("✅ Squad page: PASS")
            tests.append(True)
        else:
            print(f"❌ Squad page: FAIL (Status: {response.status_code})")
            tests.append(False)
    except Exception as e:
        print(f"❌ Squad page: FAIL ({e})")
        tests.append(False)
    
    return tests

def stop_backend(process):
    """Stop the backend server"""
    if process:
        print("\n🛑 Stopping backend server...")
        process.terminate()
        process.wait()
        print("✅ Backend server stopped")

def main():
    """Main integration test runner"""
    print("🚀 FPL Backend Integration Testing Suite")
    print("=" * 60)
    
    backend_process = None
    
    try:
        # Start backend
        backend_process = start_backend()
        if not backend_process:
            print("❌ Cannot proceed without backend server")
            return 1
        
        # Test API endpoints
        api_tests = test_api_endpoints()
        
        # Test web pages
        page_tests = test_web_pages()
        
        # Combine all tests
        all_tests = api_tests + page_tests
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Integration Test Results:")
        
        passed = sum(all_tests)
        total = len(all_tests)
        
        print(f"  API Endpoints: {sum(api_tests)}/{len(api_tests)} passed")
        print(f"  Web Pages: {sum(page_tests)}/{len(page_tests)} passed")
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All integration tests passed! The backend is fully functional.")
            return 0
        else:
            print("⚠️ Some integration tests failed. Please check the output above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Integration testing failed: {e}")
        return 1
    finally:
        # Always stop the backend
        stop_backend(backend_process)

if __name__ == '__main__':
    sys.exit(main())
