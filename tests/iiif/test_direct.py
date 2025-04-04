#!/usr/bin/env python3
"""
Simplified direct test script for IIIF functionality.
This script uses hardcoded values rather than loading from .env
"""

import os
import sys
import requests
import json

# Hardcoded configuration - using HTTPS
WEB_URL = "https://127.0.0.1:5000"
API_URL = f"{WEB_URL}/api"
API_TOKEN = "j5hiARxsptWfANKCqv0gGS3uPlJZQ092ut5rSWVWkWo8bGWoUcZqUEPTyitk"

# You'll need to manually provide a record ID with images
RECORD_ID = os.environ.get('TEST_RECORD_ID', '202')

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
        response = requests.get(record_url, headers=headers, timeout=10, verify=False)
        
        if response.status_code != 200:
            print(f"❌ Could not access record: {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            return False
        
        print(f"✓ Record is accessible")
        try:
            record_data = response.json()
            print(f"  Record title: {record_data.get('metadata', {}).get('title', 'Unknown')}")
            
            # Check if record has files
            files = record_data.get('files', [])
            if files:
                print(f"  Record has {len(files)} files:")
                for i, file in enumerate(files[:5]):  # Show first 5 files
                    print(f"   - {file.get('key')} ({file.get('size')} bytes)")
                if len(files) > 5:
                    print(f"   ... and {len(files) - 5} more files")
            else:
                print("  Record has no files")
        except json.JSONDecodeError:
            print("  Could not decode record JSON")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing record: {e}")
        return False
    
    # Test the IIIF manifest endpoint - try both API and direct paths
    for manifest_url in [
        f"{API_URL}/iiif/record:{RECORD_ID}/manifest",
        f"{WEB_URL}/iiif/{RECORD_ID}/manifest"
    ]:
        try:
            print(f"\nChecking IIIF manifest: {manifest_url}")
            response = requests.get(manifest_url, headers=headers, timeout=10, verify=False)
            
            print(f"  Status code: {response.status_code}")
            print(f"  Content type: {response.headers.get('Content-Type', 'unknown')}")
            
            if response.status_code != 200:
                print(f"❌ Could not access IIIF manifest: {response.status_code}")
                print(f"  Response: {response.text[:200]}...")
                continue
            
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
                    continue
                
                sequence = sequences[0]
                canvases = sequence.get('canvases', [])
                if not canvases:
                    print("❌ Sequence does not contain any canvases")
                    print("  This suggests that PTIF conversion has not been completed")
                    continue
                
                print(f"  Number of canvases (images): {len(canvases)}")
                
                # Test the first canvas
                if canvases:
                    canvas = canvases[0]
                    print(f"\nTesting first canvas: {canvas.get('@id', 'Unknown')}")
                    
                    # Check for images in the canvas
                    images = canvas.get('images', [])
                    if not images:
                        print("❌ Canvas does not contain any images")
                        continue
                    
                    image = images[0]
                    resource = image.get('resource', {})
                    service = resource.get('service', {})
                    
                    if not service:
                        print("❌ Image resource does not have a service")
                        continue
                    
                    # Test the image service
                    service_url = service.get('@id', '')
                    if service_url:
                        print(f"  Image service URL: {service_url}")
                        print(f"  Testing image info: {service_url}/info.json")
                        
                        try:
                            img_response = requests.get(
                                f"{service_url}/info.json", 
                                headers=headers, 
                                timeout=10,
                                verify=False
                            )
                            if img_response.status_code == 200:
                                print(f"✓ Image info is accessible")
                                
                                # Try to get a small thumbnail to verify image serving
                                thumb_url = f"{service_url}/full/100,/0/default.jpg"
                                print(f"  Testing thumbnail: {thumb_url}")
                                thumb_response = requests.get(
                                    thumb_url, 
                                    headers=headers, 
                                    timeout=10,
                                    verify=False
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
                continue
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error accessing IIIF manifest: {e}")
            continue
    
    print("\n❌ No working IIIF manifest URL found")
    return False

def check_ptif_files():
    """Provide instructions to check if PTIF files exist for this record."""
    print(f"\nTo check for PTIF files")
    print(f"Run: docker-compose exec iipserver ls -la /images/private/{RECORD_ID}/")
    print("\nOr check worker logs for PTIF conversion:")
    print("Run: docker-compose logs worker | grep PTIF")
    print("\nNote: PTIF conversion happens asynchronously after file upload")
    print("You may need to wait for the conversion to complete")

def run_tests():
    """Run all tests and provide a summary."""
    print("\n=== IIIF Authentication Test (Direct) ===\n")
    print("Configuration:")
    print(f"- Web URL: {WEB_URL}")
    print(f"- Record ID: {RECORD_ID}")
    print(f"- API Token: {'[SET]' if API_TOKEN else '[NOT SET]'}")
    
    manifest_accessible = test_manifest_access()
    
    print("\n=== Summary ===")
    print(f"Record ID: {RECORD_ID}")
    print(f"IIIF manifest accessible: {'✓' if manifest_accessible else '❌'}")
    
    check_ptif_files()
    
    print("\n=== Next Steps ===")
    if not manifest_accessible:
        print("1. Check if the record exists and contains image files")
        print("2. Ensure the images have been converted to PTIF format")
        print("3. Check the worker logs to see if conversion is in progress")
    else:
        print("To test the Mirador viewer:")
        print(f"1. Open {WEB_URL}/records/{RECORD_ID} in your browser")
        print("2. Look for the IIIF button and click it")
        print("3. Verify that the images load correctly in the viewer")
    
    return 0 if manifest_accessible else 1

if __name__ == "__main__":
    # Suppress InsecureRequestWarning for https URLs with self-signed certificates
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    sys.exit(run_tests()) 