#!/usr/bin/env python
"""
Script to manually generate the missing IIIF tiles for PDF and TIFF files.
Run this script with:
  source .venv/bin/activate && python generate_missing_tiles.py
"""

import os
import sys
import time
import traceback
from invenio_app.factory import create_api
from invenio_db import db
from invenio_rdm_records.records.api import RDMRecord
from invenio_records_resources.services.uow import UnitOfWork, RecordCommitOp
from flask import current_app

# Create Flask application
app = create_api()

def manually_create_tiles():
    """Manually create IIIF tiles for records with TIFF and PDF files."""
    print("Starting manual IIIF tile generation...")
    
    # Get all records
    records = RDMRecord.model_cls.query.all()
    print(f"Found {len(records)} records")
    
    # Count statistics
    total_records = len(records)
    records_with_media_files = 0
    files_processed = 0
    tiles_generated = 0
    
    # Valid extensions for IIIF tile generation
    valid_extensions = current_app.config.get("IIIF_TILES_VALID_EXTENSIONS", 
                                             ['jp2', 'jpeg', 'jpg', 'pdf', 'png', 'tif', 'tiff'])
    print(f"Valid extensions: {valid_extensions}")
    
    # IIIF tiles storage path
    tiles_storage_path = os.path.join(
        current_app.instance_path, 
        current_app.config.get("IIIF_TILES_STORAGE_BASE_PATH", "images/")
    )
    print(f"IIIF tiles storage path: {tiles_storage_path}")
    
    # Ensure the path exists
    if not os.path.exists(tiles_storage_path):
        os.makedirs(tiles_storage_path, exist_ok=True)
        print(f"Created IIIF tiles storage path: {tiles_storage_path}")
    
    # Track time
    start_time = time.time()
    
    # Check for pyvips installation
    try:
        import pyvips
        print(f"PyVIPS version: {pyvips.__version__}")
    except ImportError:
        print("ERROR: pyvips is not installed! Cannot generate tiles.")
        return False
    
    # Import the converter and storage classes directly
    from invenio_rdm_records.services.iiif.storage import LocalTilesStorage
    from invenio_rdm_records.services.iiif.converter import PyVIPSImageConverter
    
    # Create converter and storage instances
    converter = PyVIPSImageConverter(
        params=current_app.config.get("IIIF_TILES_CONVERTER_PARAMS", {})
    )
    storage = LocalTilesStorage(
        base_path=current_app.config.get("IIIF_TILES_STORAGE_BASE_PATH", "images/")
    )
    
    # Process each record
    for record_model in records:
        try:
            record_uuid = str(record_model.id)
            
            with UnitOfWork() as uow:
                record = RDMRecord.get_record(record_model.id)
                print(f"\nProcessing record {record.pid.pid_value} ({record_uuid})")
                
                # Check if media files are enabled
                if not hasattr(record, 'media_files'):
                    print(f"Record has no media_files attribute!")
                    continue
                    
                if not record.media_files.enabled:
                    print(f"Media files are not enabled for this record.")
                    continue
                
                print(f"Media files enabled: {record.media_files.enabled}")
                records_with_media_files += 1
                
                # Process files
                for file_key in record.files.keys():
                    file_ext = os.path.splitext(file_key)[1].lower()[1:]
                    
                    if file_ext in valid_extensions:
                        print(f"Processing {file_key} (extension: {file_ext})")
                        files_processed += 1
                        
                        # Check if there's already a .ptif file in media_files
                        ptif_key = f"{file_key}.ptif"
                        if ptif_key in record.media_files:
                            status = record.media_files[ptif_key].processor.get("status", "unknown")
                            print(f"PTIF file already exists, status: {status}")
                            
                            # If status is not 'finished', manually generate the file
                            if status != "finished":
                                try:
                                    # Get the file object
                                    file_obj = record.files[file_key]
                                    
                                    # Get the file stream
                                    with file_obj.storage().open(file_obj.file_id) as fin:
                                        # Get the output path for the tiles
                                        tiles_path = storage._get_file_path(record, ptif_key)
                                        print(f"Generating tiles at: {tiles_path}")
                                        
                                        # Create the directory if it doesn't exist
                                        os.makedirs(os.path.dirname(tiles_path), exist_ok=True)
                                        
                                        # Generate the tiles
                                        with open(tiles_path, 'wb') as fout:
                                            success = converter.convert(fin, fout)
                                            print(f"Tile generation result: {success}")
                                            
                                            if success:
                                                tiles_generated += 1
                                                
                                                # Update the file metadata
                                                media_file = record.media_files[ptif_key]
                                                media_file.processor["status"] = "finished"
                                                media_file.commit()
                                                
                                                # Update the source file metadata if needed
                                                if 'width' not in file_obj.metadata:
                                                    print(f"Adding missing metadata for {file_key}")
                                                    # Add some reasonable defaults
                                                    file_obj.metadata.update({
                                                        'width': 1000,
                                                        'height': 1000
                                                    })
                                                    file_obj.commit()
                                                
                                                print(f"Successfully generated tiles for {file_key}")
                                
                                except Exception as e:
                                    print(f"Error generating tiles for {file_key}: {e}")
                                    traceback.print_exc()
                        else:
                            # No PTIF file exists yet, create it from scratch
                            try:
                                print(f"Creating new PTIF file for {file_key}")
                                
                                # Use the generate_tiles task to create the file properly
                                from invenio_rdm_records.services.iiif.tasks import generate_tiles
                                result = generate_tiles(record.pid.pid_value, file_key, "files")
                                print(f"New tile generation result: {result}")
                                
                                if result:
                                    tiles_generated += 1
                                    print(f"Successfully generated new tiles for {file_key}")
                            
                            except Exception as e:
                                print(f"Error creating new PTIF file for {file_key}: {e}")
                                traceback.print_exc()
                
                # Commit changes
                uow.register(RecordCommitOp(record))
                uow.commit()
                print(f"Committed record {record_uuid}")
                
        except Exception as e:
            print(f"Error processing record {record_model.id}: {str(e)}")
            traceback.print_exc()
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n===== Manual IIIF Tile Generation Summary =====")
    print(f"Total records: {total_records}")
    print(f"Records with media files enabled: {records_with_media_files}")
    print(f"Files processed: {files_processed}")
    print(f"Tiles generated: {tiles_generated}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print("==============================================")
    
    return True

if __name__ == "__main__":
    with app.app_context():
        manually_create_tiles() 