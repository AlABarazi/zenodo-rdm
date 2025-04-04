import pytest
import requests
from PIL import Image
import io
import os
import re

# Configuration
BASE_URL = os.environ.get("ZENODO_BASE_URL", "http://localhost:5001")
RECORD_ID = os.environ.get("TEST_RECORD_ID", "YOUR_RECORD_ID")  # Replace with a real record ID

def test_url_structure():
    """Test that IIIF URLs follow the expected structure and routing."""
    # First get the manifest to find an image filename
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
    
    # Test the sequence endpoint
    sequence_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}/sequence/default"
    sequence_response = requests.get(sequence_url, headers={"Accept": "application/json"})
    assert sequence_response.status_code == 200, f"Sequence request failed with status {sequence_response.status_code}"
    
    # Test the canvas endpoint
    canvas_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}/canvas/{filename}"
    canvas_response = requests.get(canvas_url, headers={"Accept": "application/json"})
    assert canvas_response.status_code == 200, f"Canvas request failed with status {canvas_response.status_code}"
    
    # Test the image info endpoint
    info_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/info.json"
    info_response = requests.get(info_url, headers={"Accept": "application/json"})
    assert info_response.status_code == 200, f"Image info request failed with status {info_response.status_code}"
    
    # Test the image API endpoints with different parameters
    
    # 1. Full image
    full_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/full/full/0/default.jpg"
    full_response = requests.get(full_url)
    assert full_response.status_code == 200, f"Full image request failed with status {full_response.status_code}"
    assert full_response.headers.get('Content-Type', '').startswith('image/'), "Full image response is not an image"
    
    # 2. Thumbnail (width = 200px)
    thumb_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/full/200,/0/default.jpg"
    thumb_response = requests.get(thumb_url)
    assert thumb_response.status_code == 200, f"Thumbnail request failed with status {thumb_response.status_code}"
    
    # Verify thumbnail dimensions
    thumb_img = Image.open(io.BytesIO(thumb_response.content))
    assert thumb_img.width <= 200, f"Thumbnail width ({thumb_img.width}) exceeds 200px"
    
    # 3. Region
    region_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/100,100,300,300/full/0/default.jpg"
    region_response = requests.get(region_url)
    assert region_response.status_code == 200, f"Region request failed with status {region_response.status_code}"
    
    # 4. Rotation
    rotation_url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}:{filename}/full/full/90/default.jpg"
    rotation_response = requests.get(rotation_url)
    assert rotation_response.status_code == 200, f"Rotation request failed with status {rotation_response.status_code}"
    
    print(f"Successfully validated IIIF URL structure for record {RECORD_ID}")

# Run the test when script is executed directly
if __name__ == "__main__":
    print(f"Testing IIIF URL structure for record ID: {RECORD_ID}")
    print(f"Using base URL: {BASE_URL}")
    try:
        test_url_structure()
        print("✅ All tests passed!")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"❌ Error during test: {e}") 