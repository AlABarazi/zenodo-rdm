#!/usr/bin/env python
"""
Script to manually generate IIIF tiles for existing files.
Run this script with:
  source .venv/bin/activate && python process_iiif_tiles.py
"""

import os
import sys
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

def generate_iiif_tiles_for_all_records():
    """Generate IIIF tiles for all records."""
    with app.app_context():
        # Print current configuration
        print("Media files enabled:", current_app.config.get("RDM_RECORDS_MEDIA_FILES_ENABLED", False))
        print("IIIF tiles enabled:", current_app.config.get("IIIF_TILES_GENERATION_ENABLED", False))
        print("IIIF storage path:", os.path.join(current_app.instance_path, 
                                               current_app.config.get("IIIF_TILES_STORAGE_BASE_PATH", "images/")))
        
        # Ensure storage directory exists
        storage_path = os.path.join(current_app.instance_path, 
                                    current_app.config.get("IIIF_TILES_STORAGE_BASE_PATH", "images/"))
        os.makedirs(storage_path, exist_ok=True)
        
        # Get all records
        records = RDMRecord.model_cls.query.all()
        print(f"Found {len(records)} records")
        
        # Create processors
        processor = TilesProcessor()
        image_metadata_extractor = ImageMetadataExtractor()
        
        # Process each record
        for record_model in records:
            try:
                record_uuid = str(record_model.id)
                print(f"Processing record {record_uuid}")
                
                with UnitOfWork() as uow:
                    record = RDMRecord.get_record(record_model.id)
                    print(f"Record ID: {record.pid.pid_value}, Files: {list(record.files.keys())}")
                    
                    # Check if media files are enabled
                    if hasattr(record, 'media_files') and record.media_files.enabled:
                        # Call the processor on the record
                        processor(None, record, uow=uow)
                        uow.register(RecordCommitOp(record))
                        
                        # Calculate image dimensions for each supported image file
                        for file_key in record.files.keys():
                            file_record = record.files[file_key]
                            print(f"Processing file {file_key}")
                            
                            if image_metadata_extractor.can_process(file_record):
                                print(f"Extracting metadata for {file_key}")
                                image_metadata_extractor.process(file_record)
                                file_record.commit()
                            
                            # Force IIIF tile generation for this file
                            if hasattr(record, 'media_files') and record.media_files.enabled:
                                file_ext = os.path.splitext(file_key)[1].lower()[1:]
                                valid_extensions = current_app.config.get("IIIF_TILES_VALID_EXTENSIONS", [])
                                
                                if file_ext in valid_extensions:
                                    print(f"Generating IIIF tiles for {file_key}")
                                    # Create ptif file in media_files if it doesn't exist
                                    ptif_key = f"{file_key}.ptif"
                                    if ptif_key not in record.media_files:
                                        # Manually generate tiles for this file
                                        from invenio_rdm_records.services.iiif.tasks import generate_tiles
                                        generate_tiles(record.pid.pid_value, file_key)
                                        print(f"Generated tiles for {file_key}")
                        
                        uow.commit()
                        print(f"Committed record {record_uuid}")
            except Exception as e:
                print(f"Error processing record {record_model.id}: {str(e)}")
                
    print("IIIF tile generation complete.")

if __name__ == "__main__":
    generate_iiif_tiles_for_all_records() 