#!/usr/bin/env python3
"""
Test script for authenticated IIIF manifest access.
This script tests the generation and access of IIIF manifests for a specific record,
requiring authentication with a valid token.
"""

import os
import sys
import json
import requests

# Configuration (override with environment variables)
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:5000')
API_URL = os.environ.get('API_URL', f"{SITE_URL}/api")
RDM_TOKEN = os.environ.get('RDM_TOKEN', '')
RECORD_ID = os.environ.get('RECORD_ID', '')

def check_prerequisites():
    """Check if all prerequisites are met for testing."""
    if not RDM_TOKEN:
        print("❌ Error: RDM_TOKEN environment variable is required")
        print("  Use: RDM_TOKEN=<your-token> RECORD_ID=<record-id> python tests/iiif/test_authenticated_manifest.py")
        return False
    
    if not RECORD_ID:
        print("❌ Error: RECORD_ID environment variable is required")
        print("  Use: RDM_TOKEN=<your-token> RECORD_ID=<record-id> python tests/iiif/test_authenticated_manifest.py")
        return False
    
    return True

def test_manifest_access():
    """Test access to the IIIF manifest for the specified record."""
    print(f"\nTesting IIIF manifest access for record: {RECORD_ID}")
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {RDM_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    # First, verify the record exists and is accessible
    record_url = f"{API_URL}/records/{RECORD_ID}"
    try:
        print(f"Checking record accessibility: {record_url}")
        response = requests.get(record_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Could not access record: {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            return False
        
        print(f"✓ Record is accessible")
        record_data = response.json()
        print(f"  Record title: {record_data.get('metadata', {}).get('title', 'Unknown')}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing record: {e}")
        return False
    
    # Now, test the IIIF manifest endpoint
    manifest_url = f"{SITE_URL}/iiif/{RECORD_ID}/manifest"
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
            
            # Check for required IIIF fields
            required_fields = ['@context', '@id', '@type', 'label']
            missing_fields = [field for field in required_fields if field not in manifest]
            
            if missing_fields:
                print(f"❌ Manifest is missing required fields: {', '.join(missing_fields)}")
                return False
            
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
                        img_response = requests.get(f"{service_url}/info.json", headers=headers, timeout=10)
                        if img_response.status_code == 200:
                            print(f"✓ Image info is accessible")
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

def run_tests():
    """Run all tests and provide a summary."""
    if not check_prerequisites():
        return 1
    
    print("\n=== IIIF Authenticated Manifest Test ===\n")
    
    manifest_accessible = test_manifest_access()
    
    print("\n=== Summary ===")
    print(f"Record ID: {RECORD_ID}")
    print(f"IIIF manifest accessible: {'✓' if manifest_accessible else '❌'}")
    
    if not manifest_accessible:
        print("\n=== Recommendations ===")
        print("- Verify your token has the correct permissions")
        print("- Check if the record exists and contains image files")
        print("- Ensure the images have been converted to PTIF format")
        print("- Check the server logs for any errors")
    else:
        print("\nTo test the Mirador viewer:")
        print(f"1. Open {SITE_URL}/records/{RECORD_ID} in your browser")
        print("2. Look for the IIIF button and click it")
        print("3. Verify that the images load correctly in the viewer")
    
    return 0 if manifest_accessible else 1

if __name__ == "__main__":
    sys.exit(run_tests()) 