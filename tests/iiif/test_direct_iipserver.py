import pytest
import requests
from PIL import Image
import io
import os

# Configuration
IIPSERVER_URL = os.environ.get("IIPSERVER_URL", "http://localhost:8080")
TEST_IMAGE = os.environ.get("TEST_IMAGE", "test_image.png")  # Replace with a real image filename

def test_direct_iipserver_access():
    """Test direct access to IIPServer endpoints."""
    print(f"Testing IIPServer direct access to {TEST_IMAGE}")

    # Test info.json endpoint
    info_url = f"{IIPSERVER_URL}/iiif/?IIIF=/{TEST_IMAGE}/info.json"
    print(f"Testing info.json URL: {info_url}")
    info_response = requests.get(info_url, headers={"Accept": "application/json"})
    
    # This might fail if the image is not in PTIF format, but we'll check the response
    print(f"Info response status code: {info_response.status_code}")
    print(f"Info response headers: {info_response.headers}")
    print(f"Raw response content as bytes: {info_response.content}")
    
    if info_response.status_code == 200:
        content_type = info_response.headers.get('Content-Type', '')
        print(f"Content-Type: {content_type}")
        
        if content_type == 'application/json':
            try:
                info = info_response.json()
                print(f"Info response content: {info}")
            except Exception as e:
                print(f"Error parsing JSON: {e}")
        else:
            print(f"Response is not JSON. Content: {info_response.text[:500]}")
    else:
        print(f"Info response text: {info_response.text[:500]}")  # First 500 chars of response
    
    # Try a full image request
    image_url = f"{IIPSERVER_URL}/iiif/?IIIF=/{TEST_IMAGE}/full/200,/0/default.jpg"
    print(f"Testing image URL: {image_url}")
    image_response = requests.get(image_url)
    
    print(f"Image response status code: {image_response.status_code}")
    print(f"Image response headers: {image_response.headers}")
    
    # If we got an image back, save it for inspection
    if image_response.status_code == 200:
        content_type = image_response.headers.get('Content-Type', '')
        print(f"Content-Type: {content_type}")
        
        if content_type.startswith('image/'):
            try:
                img = Image.open(io.BytesIO(image_response.content))
                print(f"Successfully retrieved image: {img.format} {img.width}x{img.height}")
                img.save(f"test_output_{TEST_IMAGE}.jpg")
                print(f"Saved image to test_output_{TEST_IMAGE}.jpg")
            except Exception as e:
                print(f"Error processing image: {e}")
                print(f"Response length: {len(image_response.content)} bytes")
                print(f"First 100 bytes: {image_response.content[:100]}")
        else:
            print(f"Response is not an image. Content: {image_response.text[:500]}")
    else:
        print(f"Image response text: {image_response.text[:500]}")

# Run the test when script is executed directly
if __name__ == "__main__":
    print(f"Testing direct IIPServer access")
    print(f"Using IIPServer URL: {IIPSERVER_URL}")
    try:
        test_direct_iipserver_access()
        print("✅ Test completed!")
    except Exception as e:
        print(f"❌ Error during test: {e}") 