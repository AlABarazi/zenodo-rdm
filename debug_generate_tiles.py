#!/usr/bin/env python
"""
Debug script to test the IIIF tile storage directly with a mock record.
"""

import io
import os
import sys
from pathlib import Path
from invenio_app.factory import create_api
from invenio_rdm_records.services.iiif.storage import LocalTilesStorage
from invenio_rdm_records.services.iiif.converter import HAS_VIPS

# Create Flask application
app = create_api()

class MockFileRecord:
    """Mock file record for testing."""
    
    def __init__(self, filename):
        self.key = filename
        self.processor = {"status": "init"}
        self.file = type('obj', (object,), {"file_model": type('obj', (object,), {"uri": ""})})
        self._filename = filename
        
    def open_stream(self, mode):
        """Open file stream."""
        return open(self._filename, mode)
        
    def commit(self):
        """Mock commit."""
        print(f"Committing file record. Status: {self.processor.get('status')}")
        return True

class MockProtection:
    """Mock protection for testing."""
    
    def __init__(self):
        self.files = "public"

class MockAccess:
    """Mock access for testing."""
    
    def __init__(self):
        self.protection = MockProtection()

class MockRecord:
    """Mock record for testing."""
    
    def __init__(self, id, pid_value, filename):
        self.id = id
        self.pid = type('obj', (object,), {"pid_value": pid_value})
        self._files = {filename: MockFileRecord(filename)}
        self._media_files = {f"{filename}.ptif": MockFileRecord(f"{filename}.ptif")}
        self.media_files = self._media_files
        self.access = MockAccess()
        
    @property
    def files(self):
        """Get files."""
        return self._files

def test_tiles_storage():
    """Test the LocalTilesStorage directly."""
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
        
        # Create test image path
        test_image = 'test.tif'
        if not os.path.exists(test_image):
            print(f"\nTest image {test_image} not found!")
            return
        
        # Create test output directory
        output_dir = os.path.join(current_app.instance_path, 'images/test')
        os.makedirs(output_dir, exist_ok=True)
        
        # Create mock record
        record_id = 'test-record-id'
        pid_value = '1000'
        mock_record = MockRecord(record_id, pid_value, test_image)
        
        # Create a custom tiles storage instance with our test path
        tiles_storage = LocalTilesStorage(base_path=output_dir)
        
        try:
            # Show tiles storage instance details
            print("\nTiles storage instance details:")
            print(f"base_path: {tiles_storage.base_path}")
            print(f"converter type: {type(tiles_storage.converter)}")
            
            # Call save method directly
            print(f"\nCalling tiles_storage.save directly...")
            result = tiles_storage.save(mock_record, test_image, "files")
            print(f"Save result: {result}")
            
            # Check if file was created - using the path format based on the storage implementation
            expected_path = os.path.join(output_dir, "public")
            print(f"Looking for output in directory: {expected_path}")
            
            if os.path.exists(expected_path):
                print(f"Output directory exists")
                # Check if any files were created in the output directory
                files_found = False
                for root, dirs, files in os.walk(expected_path):
                    for file in files:
                        if file.endswith('.ptif'):
                            path = os.path.join(root, file)
                            print(f"Found file: {path} (size: {os.path.getsize(path)} bytes)")
                            files_found = True
                
                if not files_found:
                    print("No .ptif files found in the output directory")
            else:
                print(f"Output directory was not created")
        except Exception as e:
            print(f"Error during tiles_storage.save: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_tiles_storage() 