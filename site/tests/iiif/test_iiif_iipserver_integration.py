import pytest
import requests
import re
import os

# Configuration
BASE_URL = os.environ.get("ZENODO_BASE_URL", "http://localhost:5001")
RECORD_ID = os.environ.get("TEST_RECORD_ID", "YOUR_RECORD_ID")  # Replace with a real record ID

def test_iipserver_integration():
    """Test integration between IIIF manifest generation and IIPServer."""
    # First get the manifest to find an image
    manifest_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}/manifest"
    manifest_response = requests.get(manifest_url, headers={"Accept": "application/json"})
    
    assert manifest_response.status_code == 200, f"Manifest request failed with status {manifest_response.status_code}"
    
    manifest = manifest_response.json()
    
    # Get the first canvas
    sequence = manifest["sequences"][0]
    canvas = sequence["canvases"][0]
    
    # Extract the filename from the canvas ID
    canvas_id = canvas["@id"]
    filename_match = re.search(r'/canvas/(.+)$', canvas_id)
    assert filename_match, f"Could not extract filename from canvas ID: {canvas_id}"
    
    filename = filename_match.group(1)
    
    # Test image info from IIPServer
    info_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/info.json"
    info_response = requests.get(info_url, headers={"Accept": "application/json"})
    assert info_response.status_code == 200, f"Image info request failed with status {info_response.status_code}"
    
    # Verify info content (should come from IIPServer)
    info = info_response.json()
    assert "@context" in info, "Info missing @context field"
    assert "protocol" in info, "Info missing protocol field"
    assert info["protocol"] == "http://iiif.io/api/image", f"Incorrect protocol: {info['protocol']}"
    assert "width" in info, "Info missing width field"
    assert "height" in info, "Info missing height field"
    assert "tiles" in info, "Info missing tiles field (should be provided by IIPServer)"
    
    # Test different tile requests that should be handled by IIPServer
    
    # 1. Full image
    full_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/full/full/0/default.jpg"
    full_response = requests.get(full_url)
    assert full_response.status_code == 200, f"Full image request failed with status {full_response.status_code}"
    
    # 2. Specific region
    tile_size = info["tiles"][0]["width"]
    region_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/0,0,{tile_size},{tile_size}/full/0/default.jpg"
    region_response = requests.get(region_url)
    assert region_response.status_code == 200, f"Region request failed with status {region_response.status_code}"
    
    # 3. Test a bogus region that should return an error
    bad_region_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/invalid/full/0/default.jpg"
    bad_region_response = requests.get(bad_region_url)
    assert bad_region_response.status_code != 200, f"Invalid region request should fail but returned {bad_region_response.status_code}"
    
    print(f"Successfully validated IIPServer integration for record {RECORD_ID}")

# Run the test when script is executed directly
if __name__ == "__main__":
    print(f"Testing IIIF IIPServer integration for record ID: {RECORD_ID}")
    print(f"Using base URL: {BASE_URL}")
    try:
        test_iipserver_integration()
        print("✅ All tests passed!")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"❌ Error during test: {e}") 