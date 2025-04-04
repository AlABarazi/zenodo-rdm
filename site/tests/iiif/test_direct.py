#!/usr/bin/env python3
"""
Simplified direct test script for IIPServer functionality.
This script tests direct access to the IIPServer instance.
"""

import os
import sys
import requests
import json

# Hardcoded configuration
IIPSERVER_URL = "http://localhost:8080/fcgi-bin/iipsrv.fcgi"
TEST_IMAGE = "test_image.png"  # Regular PNG file in the public directory

def test_iipserver_direct():
    """Test direct access to the IIPServer for the test image."""
    print(f"\nTesting direct IIPServer access for: {TEST_IMAGE}")
    
    # Test direct IIP access
    direct_url = f"{IIPSERVER_URL}?FIF=/{TEST_IMAGE}"
    try:
        print(f"Checking direct IIPServer access: {direct_url}")
        response = requests.get(direct_url, timeout=10)
        
        print(f"  Status code: {response.status_code}")
        print(f"  Content type: {response.headers.get('Content-Type', 'unknown')}")
        
        if response.status_code != 200:
            print(f"❌ Could not access IIPServer directly: {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            return False
        
        print(f"✓ IIPServer is directly accessible")
        
        # Test a basic operation - get image info
        info_url = f"{IIPSERVER_URL}?FIF=/{TEST_IMAGE}&OBJ=Basic-Info"
        print(f"\nChecking image info: {info_url}")
        info_response = requests.get(info_url, timeout=10)
        
        if info_response.status_code == 200:
            print(f"✓ Image info is accessible")
            print(f"  Response: {info_response.text}")
            return True
        else:
            print(f"❌ Could not access image info: {info_response.status_code}")
            print(f"  Response: {info_response.text[:200]}...")
            return False
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing IIPServer: {e}")
        return False

def check_files():
    """Provide instructions to check the files in the IIPServer container."""
    print(f"\nTo check the files in the IIPServer container:")
    print(f"Run: docker-compose exec iipserver ls -la /images/public/")
    print(f"\nTo check the environment variables for the IIPServer container:")
    print(f"Run: docker-compose exec iipserver env | grep FILESYSTEM")

def run_tests():
    """Run all tests and provide a summary."""
    print("\n=== IIPServer Direct Test ===\n")
    print("Configuration:")
    print(f"- IIPServer URL: {IIPSERVER_URL}")
    print(f"- Test Image: {TEST_IMAGE}")
    
    iipserver_accessible = test_iipserver_direct()
    
    print("\n=== Summary ===")
    print(f"IIPServer accessible: {'✓' if iipserver_accessible else '❌'}")
    
    check_files()
    
    print("\n=== Next Steps ===")
    if not iipserver_accessible:
        print("1. Check if the IIPServer container is running: docker-compose ps | grep iipserver")
        print("2. Check if the test image exists in the public directory")
        print("3. Check IIPServer logs: docker-compose logs iipserver")
        print("4. Restart the IIPServer if needed: docker-compose restart iipserver")
    else:
        print("IIPServer is functioning correctly with the test image.")
        print("\nFor full IIIF functionality:")
        print("1. Set up a worker service for PTIF conversion")
        print("2. Configure PTIF creation for uploaded files")
    
    return 0 if iipserver_accessible else 1

if __name__ == "__main__":
    sys.exit(run_tests()) 