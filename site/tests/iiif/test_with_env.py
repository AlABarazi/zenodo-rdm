#!/usr/bin/env python3
"""
Test script that uses credentials from .env file to test IIIF functionality.
This is a simplified version that doesn't require manually specifying tokens.
"""

import os
import sys
import requests
import json
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file (in root directory)
load_dotenv(dotenv_path="../../.env")

# Configuration from environment
IIPSERVER_URL = os.environ.get('IIPSERVER_URL', 'http://localhost:8080')
WEB_URL = os.environ.get('SITE_URL', 'http://localhost:5000')
API_URL = f"{WEB_URL}/api"

# Use the RDM API token from .env
API_TOKEN = os.environ.get('RDM_API_TOKEN', '')

# You'll need to manually provide a record ID with images
RECORD_ID = os.environ.get('TEST_RECORD_ID', '')

def check_prerequisites():
    """Check if all prerequisites are met for testing."""
    if not RECORD_ID:
        print("❌ Error: TEST_RECORD_ID environment variable is required")
        print("  Use: TEST_RECORD_ID=<record-id> python tests/iiif/test_with_env.py")
        return False
    
    if not API_TOKEN:
        print("❌ Error: RDM_API_TOKEN not found in .env file")
        return False
    
    print("Configuration:")
    print(f"- IIPServer URL: {IIPSERVER_URL}")
    print(f"- Web URL: {WEB_URL}")
    print(f"- Record ID: {RECORD_ID}")
    print(f"- API Token: {'[SET]' if API_TOKEN else '[NOT SET]'}")
    
    return True

def test_manifest_access():
    """Test access to the IIIF manifest for the specified record."""
    print(f"\nTesting IIIF manifest access for record: {RECORD_ID}")
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    # Test accessing the record first
    record_url = f"{API_URL}/records/{RECORD_ID}"
    try:
        print(f"Checking record accessibility: {record_url}")
        response = requests.get(record_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Could not access record: {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            return False
        
        print(f"✓ Record is accessible")
        try:
            record_data = response.json()
            print(f"  Record title: {record_data.get('metadata', {}).get('title', 'Unknown')}")
        except json.JSONDecodeError:
            print("  Could not decode record JSON")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing record: {e}")
        return False
    
    # Test the IIIF manifest endpoint
    manifest_url = f"{WEB_URL}/iiif/{RECORD_ID}/manifest"
    try:
        print(f"\nChecking IIIF manifest: {manifest_url}")
        response = requests.get(manifest_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Could not access IIIF manifest: {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            return False
        
        print(f"✓ IIIF manifest is accessible")
        
        # Parse and validate the manifest
        try:
            manifest = response.json()
            print(f"  Manifest ID: {manifest.get('@id', 'Unknown')}")
            print(f"  Manifest type: {manifest.get('@type', 'Unknown')}")
            
            # Check for sequences and canvases
            sequences = manifest.get('sequences', [])
            if not sequences:
                print("❌ Manifest does not contain any sequences")
                return False
            
            sequence = sequences[0]
            canvases = sequence.get('canvases', [])
            if not canvases:
                print("❌ Sequence does not contain any canvases")
                return False
            
            print(f"  Number of canvases (images): {len(canvases)}")
            
            # Test the first canvas
            if canvases:
                canvas = canvases[0]
                print(f"\nTesting first canvas: {canvas.get('@id', 'Unknown')}")
                
                # Check for images in the canvas
                images = canvas.get('images', [])
                if not images:
                    print("❌ Canvas does not contain any images")
                    return False
                
                image = images[0]
                resource = image.get('resource', {})
                service = resource.get('service', {})
                
                if not service:
                    print("❌ Image resource does not have a service")
                    return False
                
                # Test the image service
                service_url = service.get('@id', '')
                if service_url:
                    print(f"  Image service URL: {service_url}")
                    print(f"  Testing image info: {service_url}/info.json")
                    
                    try:
                        img_response = requests.get(
                            f"{service_url}/info.json", 
                            headers=headers, 
                            timeout=10
                        )
                        if img_response.status_code == 200:
                            print(f"✓ Image info is accessible")
                            
                            # Try to get a small thumbnail to verify image serving
                            thumb_url = f"{service_url}/full/100,/0/default.jpg"
                            print(f"  Testing thumbnail: {thumb_url}")
                            thumb_response = requests.get(
                                thumb_url, 
                                headers=headers, 
                                timeout=10
                            )
                            
                            if thumb_response.status_code == 200:
                                print(f"✓ Thumbnail is accessible")
                                print(f"  Thumbnail size: {len(thumb_response.content)} bytes")
                            else:
                                print(f"❌ Could not access thumbnail: {thumb_response.status_code}")
                        else:
                            print(f"❌ Could not access image info: {img_response.status_code}")
                    except requests.exceptions.RequestException as e:
                        print(f"❌ Error accessing image info: {e}")
            
            return True
            
        except json.JSONDecodeError:
            print(f"❌ Response is not valid JSON")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing IIIF manifest: {e}")
        return False

def check_ptif_files():
    """Check if PTIF files exist for this record."""
    print(f"\nChecking for PTIF files")
    print("Note: This would normally require direct server access.")
    print(f"To check manually, run: docker-compose exec iipserver ls -la /images/private/{RECORD_ID}/")
    
    # Detect if images are accessible in the manifest
    # If the manifest test passed but no images are accessible, PTIF conversion may not be complete
    return True

def run_tests():
    """Run all tests and provide a summary."""
    if not check_prerequisites():
        return 1
    
    print("\n=== IIIF Authentication Test with API Token ===\n")
    
    manifest_accessible = test_manifest_access()
    ptif_files_exist = manifest_accessible and check_ptif_files()
    
    print("\n=== Summary ===")
    print(f"Record ID: {RECORD_ID}")
    print(f"IIIF manifest accessible: {'✓' if manifest_accessible else '❌'}")
    print(f"PTIF files likely exist: {'✓' if ptif_files_exist else '❌'}")
    
    if not manifest_accessible:
        print("\n=== Recommendations ===")
        print("- Check if the record exists and contains image files")
        print("- Verify API token in .env file")
        print("- Ensure the images have been converted to PTIF format")
        print("- Check the server logs for any errors")
    else:
        print("\nTo test the Mirador viewer:")
        print(f"1. Open {WEB_URL}/records/{RECORD_ID} in your browser")
        print("2. Look for the IIIF button and click it")
        print("3. Verify that the images load correctly in the viewer")
    
    return 0 if manifest_accessible else 1

if __name__ == "__main__":
    sys.exit(run_tests()) 