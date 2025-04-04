import pytest
import requests
import json
import os

# Configuration
BASE_URL = os.environ.get("ZENODO_BASE_URL", "http://localhost:5001")
RECORD_ID = os.environ.get("TEST_RECORD_ID", "YOUR_RECORD_ID")  # Replace with a real record ID

def test_manifest_endpoint():
    """Test that the manifest endpoint returns a valid IIIF manifest."""
    url = f"{BASE_URL}/api/iiif/record:{RECORD_ID}/manifest"
    response = requests.get(url, headers={"Accept": "application/json"})
    
    assert response.status_code == 200, f"Manifest request failed with status {response.status_code}"
    
    # Parse the response as JSON
    manifest = response.json()
    
    # Check for required IIIF manifest fields
    assert "@context" in manifest, "Manifest missing @context field"
    assert "@type" in manifest, "Manifest missing @type field"
    assert manifest["@type"] == "sc:Manifest", f"Incorrect manifest type: {manifest['@type']}"
    assert "label" in manifest, "Manifest missing label field"
    assert "sequences" in manifest, "Manifest missing sequences field"
    
    # Check that we have at least one sequence
    assert len(manifest["sequences"]) > 0, "Manifest has no sequences"
    
    # Check that the sequence has canvases
    sequence = manifest["sequences"][0]
    assert "canvases" in sequence, "Sequence missing canvases field"
    assert len(sequence["canvases"]) > 0, "Sequence has no canvases"
    
    # Check basic canvas structure for the first canvas
    canvas = sequence["canvases"][0]
    assert "@id" in canvas, "Canvas missing @id field"
    assert "@type" in canvas, "Canvas missing @type field"
    assert canvas["@type"] == "sc:Canvas", f"Incorrect canvas type: {canvas['@type']}"
    assert "label" in canvas, "Canvas missing label field"
    assert "width" in canvas, "Canvas missing width field"
    assert "height" in canvas, "Canvas missing height field"
    assert "images" in canvas, "Canvas missing images field"
    
    # Check image annotation structure
    assert len(canvas["images"]) > 0, "Canvas has no image annotations"
    image = canvas["images"][0]
    assert "@type" in image, "Image annotation missing @type field"
    assert image["@type"] == "oa:Annotation", f"Incorrect annotation type: {image['@type']}"
    assert "motivation" in image, "Image annotation missing motivation field"
    assert "resource" in image, "Image annotation missing resource field"
    
    # Check image resource structure
    resource = image["resource"]
    assert "@id" in resource, "Image resource missing @id field"
    assert "service" in resource, "Image resource missing service field"
    
    # Check service structure
    service = resource["service"]
    assert "@context" in service, "Service missing @context field"
    assert "@id" in service, "Service missing @id field"
    assert "profile" in service, "Service missing profile field"
    
    print(f"Successfully validated manifest for record {RECORD_ID}")

# Run the test when script is executed directly
if __name__ == "__main__":
    print(f"Testing IIIF manifest for record ID: {RECORD_ID}")
    print(f"Using base URL: {BASE_URL}")
    try:
        test_manifest_endpoint()
        print("✅ All tests passed!")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"❌ Error during test: {e}") 