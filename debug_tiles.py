#!/usr/bin/env python
"""
Debug script to test the IIIF tile generation functionality.
"""

import io
import os
import sys
from invenio_app.factory import create_api
from invenio_rdm_records.services.iiif.converter import PyVIPSImageConverter, HAS_VIPS

# Create Flask application
app = create_api()

def test_image_conversion():
    """Test the basic image conversion functionality."""
    with app.app_context():
        from flask import current_app
        
        # Print configuration
        print("IIIF configuration:")
        print(f"IIIF_TILES_GENERATION_ENABLED: {current_app.config.get('IIIF_TILES_GENERATION_ENABLED', False)}")
        print(f"IIIF_TILES_CONVERTER_PARAMS: {current_app.config.get('IIIF_TILES_CONVERTER_PARAMS', {})}")
        
        # Check for pyvips directly
        try:
            import pyvips
            print(f"Imported pyvips module: {pyvips}")
            print(f"pyvips.__version__: {pyvips.__version__}")
        except ImportError as e:
            print(f"Failed to import pyvips: {e}")
        except Exception as e:
            print(f"Error checking pyvips: {e}")
            
        # Print module level HAS_VIPS
        print(f"\nModule level HAS_VIPS: {HAS_VIPS}")
        
        # Create converter with configuration
        converter_params = current_app.config.get("IIIF_TILES_CONVERTER_PARAMS", {})
        converter = PyVIPSImageConverter(params=converter_params)
        
        # Print converter attributes
        print("\nConverter attributes:")
        for attr in dir(converter):
            if not attr.startswith('__'):
                try:
                    value = getattr(converter, attr)
                    print(f"  {attr}: {value}")
                except Exception as e:
                    print(f"  {attr}: Error getting value - {e}")
        
        # Create test image path
        test_image = 'test.tif'
        if not os.path.exists(test_image):
            print(f"\nTest image {test_image} not found!")
            return
        
        # Create output file
        output_path = os.path.join(current_app.instance_path, 'test_output.ptif')
        print(f"\nConverting image {test_image} to {output_path}")
        
        # Test conversion
        try:
            with open(test_image, 'rb') as fin, open(output_path, 'wb') as fout:
                # Debug the convert method
                print("\nDebugging convert method:")
                import inspect
                convert_source = inspect.getsource(converter.convert)
                print(f"Convert method source:\n{convert_source}")
                
                # Test if we get into the convert method
                result = converter.convert(fin, fout)
                print(f"Conversion result: {result}")
                
            # Check if file was created
            if os.path.exists(output_path):
                print(f"Output file exists with size: {os.path.getsize(output_path)} bytes")
            else:
                print("Output file was not created!")
        except Exception as e:
            print(f"Error during conversion: {e}")

if __name__ == "__main__":
    test_image_conversion() 