#!/usr/bin/env python
"""
Script to inspect the generate_tiles function implementation.
"""

import inspect
from invenio_app.factory import create_api
from invenio_rdm_records.services.iiif.tasks import generate_tiles, tiles_storage
from invenio_rdm_records.services.iiif.converter import PyVIPSImageConverter

# Create Flask application
app = create_api()

def inspect_tiles_gen():
    """Inspect the generate_tiles function implementation."""
    with app.app_context():
        # Print the source code of the function
        print("generate_tiles function source code:")
        print(inspect.getsource(generate_tiles))
        
        # Print the module path
        print("\nModule path:")
        print(inspect.getmodule(generate_tiles).__file__)
        
        # Print information about the tiles_storage module
        print("\ntiles_storage type:")
        print(type(tiles_storage))
        print("\ntiles_storage dir:")
        print(dir(tiles_storage))
        
        # Try to print the save method
        if hasattr(tiles_storage, 'save'):
            print("\ntiles_storage.save method:")
            print(inspect.getsource(tiles_storage.save))
        
        # Print the tiles_storage module path
        print("\ntiles_storage module path:")
        print(inspect.getmodule(tiles_storage).__file__)
        
        # Examine the converter
        print("\ntiles_storage.converter type:")
        print(type(tiles_storage.converter))
        
        if hasattr(tiles_storage.converter, 'convert'):
            print("\ntiles_storage.converter.convert method:")
            try:
                print(inspect.getsource(tiles_storage.converter.convert))
            except (IOError, TypeError) as e:
                print(f"Could not get source code: {e}")
                print("Trying to get convert method implementation...")
                from invenio_rdm_records.services.iiif.converter import ImageConversionRunner
                try:
                    print(inspect.getsource(ImageConversionRunner.convert))
                except Exception as e:
                    print(f"Error getting source code: {e}")
        
        # Print the PyVIPSImageConverter __init__ method
        print("\nPyVIPSImageConverter __init__ method:")
        try:
            print(inspect.getsource(PyVIPSImageConverter.__init__))
        except Exception as e:
            print(f"Error getting source code: {e}")
        
        # Print the full PyVIPSImageConverter class
        print("\nPyVIPSImageConverter full class:")
        try:
            print(inspect.getsource(PyVIPSImageConverter))
        except Exception as e:
            print(f"Error getting source code: {e}")
        
        # Try to get file path and config settings
        print("\nIIIF storage settings:")
        try:
            from flask import current_app
            base_path = current_app.config.get("IIIF_TILES_STORAGE_BASE_PATH", "images/")
            instance_path = current_app.instance_path
            print(f"IIIF_TILES_STORAGE_BASE_PATH: {base_path}")
            print(f"Instance path: {instance_path}")
            print(f"Full path: {instance_path}/{base_path}")
            
            print("\nIIIF converter settings:")
            print(f"IIIF_TILES_GENERATION_ENABLED: {current_app.config.get('IIIF_TILES_GENERATION_ENABLED', False)}")
            print(f"IIIF_TILES_CONVERTER_PARAMS: {current_app.config.get('IIIF_TILES_CONVERTER_PARAMS', {})}")
            print(f"IIIF_TILES_VALID_EXTENSIONS: {current_app.config.get('IIIF_TILES_VALID_EXTENSIONS', [])}")
        except Exception as e:
            print(f"Error getting config: {e}")

if __name__ == "__main__":
    inspect_tiles_gen() 