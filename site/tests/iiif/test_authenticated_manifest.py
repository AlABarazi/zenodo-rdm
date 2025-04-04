"""
Test IIIF manifest access with authentication.
This test requires an authentication token and a valid record ID.
"""

import os
import json
import requests

# Configuration
BASE_URL = os.environ.get("ZENODO_BASE_URL", "http://localhost:5000")
RECORD_ID = os.environ.get("TEST_RECORD_ID", "YOUR_RECORD_ID")  # Replace with a real record ID
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")  # Your authentication token

def test_authenticated_manifest_access():
    """Test accessing a IIIF manifest with authentication."""
    
    print(f"Testing authenticated IIIF manifest access for record {RECORD_ID}")
    
    if not AUTH_TOKEN:
        print("❌ No authentication token provided. Please set the AUTH_TOKEN environment variable.")
        return False
    
    manifest_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}/manifest"
    print(f"Requesting manifest from: {manifest_url}")
    
    # Set up headers with authentication
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    try:
        # Make the request with authentication
        response = requests.get(manifest_url, headers=headers)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            # Parse and validate the manifest
            manifest = response.json()
            print("✅ Successfully retrieved manifest")
            
            # Basic validation of manifest structure
            if "@context" in manifest and "@type" in manifest:
                print("✅ Manifest has proper IIIF structure")
                
                # Check if the manifest has sequences and canvases
                if "sequences" in manifest and len(manifest["sequences"]) > 0:
                    sequence = manifest["sequences"][0]
                    if "canvases" in sequence and len(sequence["canvases"]) > 0:
                        canvas_count = len(sequence["canvases"])
                        print(f"✅ Manifest contains {canvas_count} canvas(es)")
                        
                        # Extract the first filename for further testing
                        first_canvas = sequence["canvases"][0]
                        filename = first_canvas["@id"].split("/")[-1]
                        print(f"First image filename: {filename}")
                        
                        # Return success along with the filename for further testing
                        return True, filename
                    else:
                        print("❌ Manifest has no canvases")
                else:
                    print("❌ Manifest has no sequences")
            else:
                print("❌ Response is not a valid IIIF manifest")
        elif response.status_code == 403:
            print("❌ Authentication failed - invalid or expired token")
        elif response.status_code == 404:
            print("❌ Record not found - check your record ID")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response content: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Error during request: {e}")
    
    return False, None

def test_authenticated_image_access(filename):
    """Test accessing a IIIF image with authentication."""
    
    if not filename:
        print("❌ No filename provided. Skipping image access test.")
        return False
    
    print(f"\nTesting authenticated IIIF image access for file {filename}")
    
    info_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/info.json"
    print(f"Requesting image info from: {info_url}")
    
    # Set up headers with authentication
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    try:
        # Make the request with authentication
        response = requests.get(info_url, headers=headers)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            # Try to parse the response as JSON
            try:
                info = response.json()
                print("✅ Successfully retrieved image info")
                
                # Check if the info has basic IIIF image API structure
                if "width" in info and "height" in info:
                    width = info["width"]
                    height = info["height"]
                    print(f"✅ Image dimensions: {width}x{height}")
                    
                    # Try to get a thumbnail of the image
                    thumb_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/full/200,/0/default.jpg"
                    print(f"Requesting thumbnail from: {thumb_url}")
                    
                    thumb_response = requests.get(thumb_url, headers=headers)
                    if thumb_response.status_code == 200:
                        print("✅ Successfully retrieved thumbnail")
                        return True
                    else:
                        print(f"❌ Failed to retrieve thumbnail: {thumb_response.status_code}")
                else:
                    print("❌ Response is not a valid IIIF image info")
            except json.JSONDecodeError:
                print("❌ Response is not valid JSON")
                print(f"Response content: {response.text[:500]}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response content: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Error during request: {e}")
    
    return False

def run_all_tests():
    """Run all authentication tests."""
    
    print("\n=====================")
    print("IIIF Authentication Tests")
    print("=====================\n")
    
    print(f"Base URL: {BASE_URL}")
    print(f"Record ID: {RECORD_ID}")
    print(f"Auth Token: {'Provided' if AUTH_TOKEN else 'Not provided'}\n")
    
    success, filename = test_authenticated_manifest_access()
    
    if success and filename:
        image_success = test_authenticated_image_access(filename)
    else:
        image_success = False
    
    print("\n=====================")
    print("Summary:")
    print("=====================")
    print(f"Manifest Access: {'✅ Successful' if success else '❌ Failed'}")
    print(f"Image Access: {'✅ Successful' if image_success else '❌ Failed'}")
    
    print("\nRecommendations:")
    if not AUTH_TOKEN:
        print("- Provide an authentication token via the AUTH_TOKEN environment variable")
    elif not success:
        print("- Check that your token has the correct permissions")
        print("- Verify that the record ID exists and contains images")
    elif not image_success:
        print("- Check if PTIF conversion has completed for this record")
        print("- Verify IIPServer is running correctly")
    else:
        print("- All tests passed! The IIIF authentication is working correctly")
        print("- You can use these credentials in the more advanced tests")

# Run the test when script is executed directly
if __name__ == "__main__":
    print("Running authenticated IIIF tests")
    run_all_tests() 