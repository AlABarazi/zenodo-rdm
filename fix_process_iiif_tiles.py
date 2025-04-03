#!/usr/bin/env python
"""
Improved script to generate IIIF tiles for existing files.
Run this script with:
  source .venv/bin/activate && python fix_process_iiif_tiles.py
"""

import os
import sys
import time
import traceback
from pathlib import Path
from invenio_app.factory import create_api
from invenio_db import db
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.records.api import RDMRecord
from invenio_rdm_records.records.processors.tiles import TilesProcessor
from invenio_records_resources.services.files.processors.image import ImageMetadataExtractor
from invenio_records_resources.services.uow import UnitOfWork, RecordCommitOp
from flask import current_app

# Create Flask application
app = create_api()

def check_iiif_configuration():
    """Check the IIIF configuration."""
    print("Checking IIIF configuration:")
    print(f"IIIF_TILES_GENERATION_ENABLED: {current_app.config.get('IIIF_TILES_GENERATION_ENABLED', False)}")
    print(f"RDM_RECORDS_MEDIA_FILES_ENABLED: {current_app.config.get('RDM_RECORDS_MEDIA_FILES_ENABLED', False)}")
    print(f"IIIF_TILES_VALID_EXTENSIONS: {current_app.config.get('IIIF_TILES_VALID_EXTENSIONS', [])}")
    print(f"IIIF_TILES_CONVERTER_PARAMS: {current_app.config.get('IIIF_TILES_CONVERTER_PARAMS', {})}")
    
    # Check for pyvips installation
    try:
        import pyvips
        print(f"PyVIPS version: {pyvips.__version__}")
        
        from invenio_rdm_records.services.iiif.converter import HAS_VIPS
        print(f"HAS_VIPS: {HAS_VIPS}")
        
        if not HAS_VIPS:
            print("WARNING: HAS_VIPS is False despite pyvips being importable!")
            print("This suggests there might be an issue with the libvips library.")
    except ImportError:
        print("ERROR: pyvips module is not installed!")
        print("Install with: pip install pyvips")
        return False
    except Exception as e:
        print(f"ERROR checking pyvips: {e}")
        return False
    
    # Check if tiles storage path exists
    iiif_path = os.path.join(
        current_app.instance_path, 
        current_app.config.get("IIIF_TILES_STORAGE_BASE_PATH", "images/")
    )
    print(f"IIIF storage path: {iiif_path}")
    
    if not os.path.exists(iiif_path):
        os.makedirs(iiif_path, exist_ok=True)
        print(f"Created IIIF storage path: {iiif_path}")
    else:
        print(f"IIIF storage path exists.")
    
    # Test simple image conversion
    try:
        print("\nTesting IIIF tile generation with a simple image...")
        from invenio_rdm_records.services.iiif.converter import PyVIPSImageConverter
        
        # Create a simple test image if it doesn't exist
        import numpy as np
        from PIL import Image
        test_image_path = "test_vips.tif"
        
        if not os.path.exists(test_image_path):
            # Create a simple 100x100 grayscale image
            test_img = np.zeros((100, 100), dtype=np.uint8)
            test_img[25:75, 25:75] = 255  # White square in center
            Image.fromarray(test_img).save(test_image_path)
            print(f"Created test image: {test_image_path}")
        
        # Test basic conversion
        test_output_path = os.path.join(current_app.instance_path, "test_output.ptif")
        converter = PyVIPSImageConverter(
            params=current_app.config.get("IIIF_TILES_CONVERTER_PARAMS", {})
        )
        
        with open(test_image_path, 'rb') as fin, open(test_output_path, 'wb') as fout:
            result = converter.convert(fin, fout)
            print(f"Basic conversion test result: {result}")
        
        if os.path.exists(test_output_path) and os.path.getsize(test_output_path) > 0:
            print(f"Test successful: Created {test_output_path} ({os.path.getsize(test_output_path)} bytes)")
            return True
        else:
            print("Test failed: Could not create PTIF file")
            return False
    except Exception as e:
        print(f"Error during basic conversion test: {e}")
        traceback.print_exc()
        return False

def generate_iiif_tiles_for_all_records():
    """Generate IIIF tiles for all records."""
    # First check the configuration
    if not check_iiif_configuration():
        print("\nIIIF configuration check failed! Please fix the issues before continuing.")
        return False
    
    print("\nStarting IIIF tile generation for all records...")
    
    # Get all records
    records = RDMRecord.model_cls.query.all()
    print(f"Found {len(records)} records")
    
    # Create processors
    processor = TilesProcessor()
    image_metadata_extractor = ImageMetadataExtractor()
    
    # Count statistics
    total_records = len(records)
    processed_records = 0
    successful_records = 0
    failed_records = 0
    files_processed = 0
    files_converted = 0
    
    # Track the time
    start_time = time.time()
    
    # Process each record
    for record_model in records:
        try:
            record_uuid = str(record_model.id)
            
            with UnitOfWork() as uow:
                record = RDMRecord.get_record(record_model.id)
                print(f"\nProcessing record {record.pid.pid_value} ({record_uuid})")
                print(f"Files: {list(record.files.keys())}")
                
                # Check if media files are enabled
                if not hasattr(record, 'media_files'):
                    print(f"Record has no media_files attribute!")
                    failed_records += 1
                    continue
                    
                if not record.media_files.enabled:
                    print(f"Media files are not enabled for this record.")
                    failed_records += 1
                    continue
                
                print(f"Media files enabled: {record.media_files.enabled}")
                
                # Call the processor on the record
                processor(None, record, uow=uow)
                uow.register(RecordCommitOp(record))
                
                # Process files
                record_success = False
                
                for file_key in record.files.keys():
                    file_record = record.files[file_key]
                    print(f"Processing file {file_key}")
                    files_processed += 1
                    
                    # Extract metadata for images
                    if image_metadata_extractor.can_process(file_record):
                        print(f"Extracting metadata for {file_key}")
                        image_metadata_extractor.process(file_record)
                        file_record.commit()
                    
                    # Generate IIIF tiles for supported file types
                    file_ext = os.path.splitext(file_key)[1].lower()[1:]
                    valid_extensions = current_app.config.get("IIIF_TILES_VALID_EXTENSIONS", [])
                    
                    if file_ext in valid_extensions:
                        print(f"Generating IIIF tiles for {file_key}")
                        # Check if ptif file already exists
                        ptif_key = f"{file_key}.ptif"
                        
                        if ptif_key in record.media_files:
                            print(f"PTIF file already exists in media_files")
                            
                            # Check the status
                            status = record.media_files[ptif_key].processor.get("status", "unknown")
                            print(f"Status: {status}")
                            
                            # Regenerate if failed
                            if status == "failed":
                                print(f"Previous generation failed, retrying...")
                                from invenio_rdm_records.services.iiif.tasks import generate_tiles
                                generate_tiles(record.pid.pid_value, file_key, "files")
                                print(f"Regenerated tiles for {file_key}")
                                files_converted += 1
                                record_success = True
                        else:
                            print(f"Creating new PTIF file for {file_key}")
                            # Manually generate tiles for this file
                            from invenio_rdm_records.services.iiif.tasks import generate_tiles
                            generate_tiles(record.pid.pid_value, file_key, "files")
                            print(f"Generated tiles for {file_key}")
                            files_converted += 1
                            record_success = True
                
                uow.commit()
                print(f"Committed record {record_uuid}")
                processed_records += 1
                
                if record_success:
                    successful_records += 1
                else:
                    failed_records += 1
                    
        except Exception as e:
            print(f"Error processing record {record_model.id}: {str(e)}")
            traceback.print_exc()
            failed_records += 1
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n===== IIIF Tile Generation Summary =====")
    print(f"Total records: {total_records}")
    print(f"Processed records: {processed_records}")
    print(f"Successful records: {successful_records}")
    print(f"Failed records: {failed_records}")
    print(f"Files processed: {files_processed}")
    print(f"Files converted: {files_converted}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print("========================================")
    
    return True

if __name__ == "__main__":
    with app.app_context():
        generate_iiif_tiles_for_all_records() 