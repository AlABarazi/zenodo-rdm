"""
Simple test to check if IIPServer is running and accepting connections.
This test doesn't require PTIF files or authentication.
"""

import os
import requests

# Simple configuration
IIPSERVER_URL = os.environ.get("IIPSERVER_URL", "http://localhost:8080")

def test_iipserver_is_running():
    """Test that the IIPServer is running and responding to requests."""
    
    print(f"Testing if IIPServer is running at {IIPSERVER_URL}")
    
    # Try to connect to the IIPServer root URL
    try:
        response = requests.get(IIPSERVER_URL, timeout=5)
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        # Check for any response - even an error page means the server is running
        if response.status_code:
            print("✅ IIPServer is running and accepting connections")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to IIPServer - server may be down")
        return False
    except Exception as e:
        print(f"❌ Error checking IIPServer: {e}")
        return False

def test_fcgi_endpoint_exists():
    """Test that the FastCGI endpoint exists on IIPServer."""
    
    print(f"Testing if FastCGI endpoint exists at {IIPSERVER_URL}/fcgi-bin/iipsrv.fcgi")
    
    # Try the FCG endpoint
    try:
        response = requests.get(f"{IIPSERVER_URL}/fcgi-bin/iipsrv.fcgi", timeout=5)
        print(f"Response status code: {response.status_code}")
        
        # Even a 500 error is okay - it means the endpoint exists but needs parameters
        if response.status_code in [200, 400, 500]:
            print("✅ IIPServer FCGI endpoint exists")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking FCGI endpoint: {e}")
        return False

def summarize_test_findings():
    """Summarize the test findings in a report."""
    
    print("\n=====================")
    print("IIPServer Test Report")
    print("=====================\n")
    
    server_running = test_iipserver_is_running()
    fcgi_exists = test_fcgi_endpoint_exists()
    
    print("\n=====================")
    print("Summary:")
    print("=====================")
    print(f"IIPServer Running: {'✅ Yes' if server_running else '❌ No'}")
    print(f"FCGI Endpoint Available: {'✅ Yes' if fcgi_exists else '❌ No'}")
    
    print("\nRecommendations:")
    if not server_running:
        print("- Restart the IIPServer container using 'docker-compose restart iipserver'")
        print("- Check IIPServer logs with 'docker-compose logs iipserver'")
    elif not fcgi_exists:
        print("- Check IIPServer configuration in the container")
        print("- Verify URL patterns in the documentation")
    else:
        print("- IIPServer is running correctly")
        print("- To test image serving, you'll need to:")
        print("  1. Create PTIF files using the full stack")
        print("  2. Get authentication credentials")
        print("  3. Use the test scripts with real record IDs")

# Run the test when script is executed directly
if __name__ == "__main__":
    print("Running simple IIPServer test")
    summarize_test_findings() 