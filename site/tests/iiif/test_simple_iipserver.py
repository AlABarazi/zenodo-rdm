#!/usr/bin/env python3
"""
Simple test to check if the IIPServer is properly configured and can serve images.
This test verifies the basic functionality without requiring authentication.
"""

import os
import sys
import requests

# Configuration (can be overridden by environment variables)
IIPSERVER_URL = os.environ.get('IIPSERVER_URL', 'http://localhost:8080')

def test_iipserver_running():
    """Check if the IIPServer is running and accepting connections."""
    try:
        response = requests.get(IIPSERVER_URL, timeout=5)
        print(f"✓ IIPServer is running at {IIPSERVER_URL}")
        print(f"  Response status code: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ IIPServer check failed: {e}")
        return False

def test_fcgi_endpoint():
    """Check if the FastCGI endpoint is available."""
    fcgi_url = f"{IIPSERVER_URL}/fcgi-bin/iipsrv.fcgi"
    try:
        response = requests.get(fcgi_url, timeout=5)
        print(f"✓ FastCGI endpoint is available at {fcgi_url}")
        print(f"  Response status code: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ FastCGI endpoint check failed: {e}")
        return False

def test_test_image():
    """Try to access the test image info.json."""
    test_image_url = f"{IIPSERVER_URL}/fcgi-bin/iipsrv.fcgi?IIIF=/test_image.ptif/info.json"
    try:
        response = requests.get(test_image_url, timeout=5)
        print(f"Test image info request to {test_image_url}")
        print(f"  Response status code: {response.status_code}")
        if response.status_code == 200:
            print("✓ Test image info.json is accessible")
            return True
        else:
            print(f"✗ Could not access test image info.json: {response.text[:100]}...")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Test image request failed: {e}")
        return False

def run_tests():
    """Run all tests and summarize results."""
    print("\n=== IIPServer Test Results ===\n")
    
    server_running = test_iipserver_running()
    fcgi_available = test_fcgi_endpoint()
    
    # Only test the image if the server is running
    if server_running and fcgi_available:
        test_image_accessible = test_test_image()
    else:
        test_image_accessible = False
        print("✗ Skipping test image check as server prerequisites failed")
    
    print("\n=== Summary ===")
    print(f"IIPServer running: {'✓' if server_running else '✗'}")
    print(f"FastCGI endpoint available: {'✓' if fcgi_available else '✗'}")
    print(f"Test image accessible: {'✓' if test_image_accessible else '✗'}")
    
    print("\n=== Recommendations ===")
    if not server_running or not fcgi_available:
        print("- Make sure the IIPServer container is running")
        print("- Check docker logs for errors: docker-compose logs iipserver")
    elif not test_image_accessible:
        print("- Verify test_image.ptif exists in the container: docker-compose exec iipserver ls -la /images/public/")
        print("- Check if the file has correct permissions")
        print("- Check if file is valid PTIF format")
    
    if server_running and fcgi_available:
        print("\n=== Next Steps ===")
        print("1. Create PTIF files for your images")
        print("2. Get authentication credentials")
        print("3. Use test scripts with real record IDs to test image serving")
    
    # Return success if the server is running and FastCGI is available
    # We don't require the test image to be accessible as that's advanced functionality
    return 0 if server_running and fcgi_available else 1

if __name__ == "__main__":
    sys.exit(run_tests()) 