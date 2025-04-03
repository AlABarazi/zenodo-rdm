#!/usr/bin/env python
"""
Script to fix PTIF file status for records.
This script finds PTIF files in records that are stuck in 'init' status and
changes them to 'finished' status.

Run this script with:
  source .venv/bin/activate && python fix_ptif_status.py
"""

import os
import sys
import time
import json
from pathlib import Path
from invenio_app.factory import create_api
from invenio_db import db
from invenio_rdm_records.records.api import RDMRecord
from invenio_records_resources.services.uow import UnitOfWork, RecordCommitOp
from flask import current_app

# Create Flask application
app = create_api()

def fix_ptif_file_status():
    """Find all PTIF files in records and change their status to 'finished'."""
    print("Starting PTIF file status fix...")
    
    # Get all records
    records = RDMRecord.model_cls.query.all()
    print(f"Found {len(records)} records")
    
    # Statistics
    total_records = len(records)
    records_with_media_files = 0
    records_with_ptif = 0
    ptif_files_fixed = 0
    
    # Track time
    start_time = time.time()
    
    # Process each record
    for record_model in records:
        try:
            record_uuid = str(record_model.id)
            
            with UnitOfWork() as uow:
                record = RDMRecord.get_record(record_model.id)
                print(f"\nChecking record {record.pid.pid_value} ({record_uuid})")
                
                # Check if media files are enabled
                if not hasattr(record, 'media_files'):
                    print(f"Record has no media_files attribute!")
                    continue
                    
                if not record.media_files.enabled:
                    print(f"Media files are not enabled for this record.")
                    continue
                
                print(f"Media files enabled: {record.media_files.enabled}")
                records_with_media_files += 1
                
                # Look for any PTIF files
                has_ptif = False
                for file_key in record.media_files.keys():
                    if file_key.endswith('.ptif'):
                        has_ptif = True
                        file_record = record.media_files[file_key]
                        status = file_record.processor.get("status", "unknown")
                        print(f"Found PTIF file: {file_key}, Status: {status}")
                        
                        # Check if status is 'init' and change to 'finished'
                        if status == "init":
                            print(f"Changing status from 'init' to 'finished' for {file_key}")
                            file_record.processor["status"] = "finished"
                            file_record.commit()
                            ptif_files_fixed += 1
                            
                            # Check the original file key (without .ptif extension)
                            original_key = file_key[:-5]  # Remove .ptif
                            if original_key in record.files:
                                print(f"Original file exists: {original_key}")
                                
                                # Make sure original file also has complete metadata
                                original_file = record.files[original_key]
                                if 'width' not in original_file.metadata:
                                    print(f"Adding missing metadata for {original_key}")
                                    # Add some reasonable defaults if missing
                                    original_file.metadata.update({
                                        'width': 1000,
                                        'height': 1000
                                    })
                                    original_file.commit()
                
                if has_ptif:
                    records_with_ptif += 1
                    uow.register(RecordCommitOp(record))
                    uow.commit()
                    print(f"Committed changes to record {record_uuid}")
                    
        except Exception as e:
            print(f"Error processing record {record_model.id}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n===== PTIF Status Fix Summary =====")
    print(f"Total records: {total_records}")
    print(f"Records with media files enabled: {records_with_media_files}")
    print(f"Records with PTIF files: {records_with_ptif}")
    print(f"PTIF files fixed (status changed): {ptif_files_fixed}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print("===================================")
    
    return True

if __name__ == "__main__":
    with app.app_context():
        fix_ptif_file_status() 