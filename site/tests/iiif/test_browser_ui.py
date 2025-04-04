#!/usr/bin/env python3
"""
Simple test script to check if Zenodo-RDM web interface is accessible.
This can help determine the correct URLs when API access isn't working.
"""

import os
import sys
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="../../.env")

# Configuration - adjust these as needed
WEB_URLS_TO_TRY = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
]

# You'll need to manually provide a record ID
RECORD_ID = os.environ.get('TEST_RECORD_ID', '202')

def test_web_access():
    """Test if we can access the web interface."""
    print("\n=== Testing Web Interface Access ===\n")
    
    for base_url in WEB_URLS_TO_TRY:
        print(f"Trying base URL: {base_url}")
        
        # Test home page
        try:
            print(f"  Testing home page...")
            response = requests.get(base_url, timeout=5)
            print(f"  Status code: {response.status_code}")
            print(f"  Content type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"  Content length: {len(response.content)} bytes")
            if response.status_code == 200:
                print("  ✓ Home page is accessible")
            else:
                print(f"  ✗ Could not access home page: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error accessing home page: {e}")
            continue
        
        # Test record page
        record_url = urljoin(base_url, f"records/{RECORD_ID}")
        try:
            print(f"\n  Testing record page: {record_url}")
            response = requests.get(record_url, timeout=5)
            print(f"  Status code: {response.status_code}")
            print(f"  Content type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"  Content length: {len(response.content)} bytes")
            if response.status_code == 200:
                print("  ✓ Record page is accessible")
            else:
                print(f"  ✗ Could not access record page: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error accessing record page: {e}")
            continue
        
        # Test IIIF manifest URL
        iiif_url = urljoin(base_url, f"iiif/{RECORD_ID}/manifest")
        try:
            print(f"\n  Testing IIIF manifest: {iiif_url}")
            response = requests.get(iiif_url, timeout=5)
            print(f"  Status code: {response.status_code}")
            print(f"  Content type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"  Content length: {len(response.content)} bytes")
            if response.status_code == 200:
                print("  ✓ IIIF manifest is accessible")
                try:
                    manifest_data = response.json()
                    print(f"  Manifest type: {manifest_data.get('@type', 'unknown')}")
                    print(f"  Manifest ID: {manifest_data.get('@id', 'unknown')}")
                    sequences = manifest_data.get('sequences', [])
                    if sequences:
                        canvases = sequences[0].get('canvases', [])
                        print(f"  Number of canvases: {len(canvases)}")
                    else:
                        print("  No sequences found in manifest")
                except ValueError:
                    print("  Could not parse manifest as JSON")
            else:
                print(f"  ✗ Could not access IIIF manifest: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error accessing IIIF manifest: {e}")
            continue
        
        print(f"\n✓ Found working base URL: {base_url}")
        return True
    
    print("\n✗ Could not access Zenodo-RDM web interface through any of the tried URLs")
    return False

if __name__ == "__main__":
    if test_web_access():
        sys.exit(0)
    else:
        sys.exit(1) 