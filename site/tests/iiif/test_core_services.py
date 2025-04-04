"""
Test that core services for IIIF functionality are running.
This test only checks service availability, not specific IIIF content.
"""

import requests
import os
import sys

# Configuration
IIPSERVER_URL = os.environ.get("IIPSERVER_URL", "http://localhost:8080")
WEB_URL = os.environ.get("WEB_URL", "http://localhost:5000")

def test_iipserver_running():
    """Test that the IIPServer is running."""
    try:
        response = requests.get(IIPSERVER_URL, timeout=5)
        if response.status_code:  # Any response means the server is running
            print("✅ IIPServer is running")
            return True
        else:
            print("❌ IIPServer returned unexpected response")
            return False
    except Exception as e:
        print(f"❌ Could not connect to IIPServer: {e}")
        return False

def test_web_running():
    """Test that the web server is running."""
    try:
        response = requests.get(WEB_URL, timeout=5)
        if response.status_code:  # Any response means the server is running
            print("✅ Web server is running")
            return True
        else:
            print("❌ Web server returned unexpected response")
            return False
    except Exception as e:
        print(f"❌ Could not connect to web server: {e}")
        return False

def run_tests():
    """Run all tests."""
    print("\n=====================")
    print("Core Services Test")
    print("=====================\n")
    
    iipserver_running = test_iipserver_running()
    web_running = test_web_running()
    
    print("\n=====================")
    print("Test Results:")
    print("=====================")
    print(f"IIPServer Running: {'✅ Pass' if iipserver_running else '❌ Fail'}")
    print(f"Web Server Running: {'✅ Pass' if web_running else '❌ Fail'}")
    
    # Simple pass/fail exit for CI integration
    if iipserver_running and web_running:
        print("\n✅ ALL TESTS PASSED - Core services are running")
        return 0  # Success
    else:
        failed_services = []
        if not iipserver_running:
            failed_services.append("IIPServer")
        if not web_running:
            failed_services.append("Web Server")
        
        print(f"\n❌ TEST FAILED - The following services are not running: {', '.join(failed_services)}")
        return 1  # Failure

if __name__ == "__main__":
    print("Running core services test")
    result = run_tests()
    sys.exit(result)  # Exit with the appropriate code for CI/CD 