#!/usr/bin/env python
"""
Script to register PTIF files with the records.
This will make PDF files viewable in the Mirador viewer.

Run this script with:
  source .venv/bin/activate && python register_pdf_ptif.py
"""

import os
import sys
import json
import time
import subprocess
from invenio_app.factory import create_api
from invenio_db import db
from invenio_files_rest.models import ObjectVersion, Bucket

# Create Flask application
app = create_api()

def register_pdf_ptif_files():
    """Register PTIF files for PDFs with the records."""
    with app.app_context():
        from invenio_rdm_records.records.api import RDMRecord
        
        # Record IDs with PDF files
        record_ids = [
            "216",  # This is the record with ID 216
        ]
        
        # Statistics
        records_processed = 0
        ptif_files_registered = 0
        errors = 0
        
        start_time = time.time()
        
        for record_id in record_ids:
            try:
                # Get the record
                record = RDMRecord.pid.resolve(record_id)
                print(f"Processing record {record_id}")
                
                # Check if media files are enabled
                if not record.media_files.enabled:
                    print(f"Media files not enabled for record {record_id}")
                    continue
                
                # Check for PDF files
                pdf_files = []
                for filename in record.files.keys():
                    if filename.lower().endswith('.pdf'):
                        pdf_files.append(filename)
                
                if not pdf_files:
                    print(f"No PDF files found in record {record_id}")
                    continue
                
                print(f"Found {len(pdf_files)} PDF files in record {record_id}")
                
                # Check the IIIF directory for PTIF files for this record
                images_dir = os.path.join(app.instance_path, "images", "public")
                
                for pdf_filename in pdf_files:
                    ptif_filename = f"{pdf_filename}.ptif"
                    
                    # Check if PTIF file is already registered
                    if ptif_filename in record.media_files:
                        print(f"PTIF file {ptif_filename} already registered for record {record_id}")
                        continue
                    
                    # Find the PTIF file in the IIIF directory
                    ptif_path = None
                    pattern_prefix = None
                    
                    for prefix in ["21", "20"]:
                        dir_pattern = os.path.join(images_dir, prefix, "6_", "_")
                        path = os.path.join(dir_pattern, ptif_filename)
                        if os.path.exists(path) and os.path.isfile(path):
                            ptif_path = path
                            pattern_prefix = prefix
                            break
                    
                    if not ptif_path:
                        print(f"No PTIF file found for PDF {pdf_filename}")
                        continue
                    
                    print(f"Found PTIF file at {ptif_path}")
                    
                    # Register the PTIF file with the record
                    try:
                        # Create ObjectVersion for the new file
                        bucket_id = record.media_files.bucket_id
                        with open(ptif_path, 'rb') as ptif_file:
                            obj = ObjectVersion.create(bucket_id, ptif_filename, stream=ptif_file)
                            db.session.add(obj)
                            db.session.commit()
                        
                        # Add metadata to record
                        obj_dict = {
                            "key": ptif_filename,
                            "object_version_id": str(obj.version_id),
                            "processor": {
                                "status": "finished"
                            }
                        }
                        record.media_files.add(obj_dict)
                        record.commit()
                        db.session.commit()
                        
                        print(f"Successfully registered PTIF file {ptif_filename}")
                        ptif_files_registered += 1
                        
                        # Check for multi-page PTIF files
                        page_count = 1
                        while True:
                            page_ptif_filename = f"{pdf_filename}.page-{page_count}.ptif"
                            page_ptif_path = os.path.join(os.path.dirname(ptif_path), page_ptif_filename)
                            
                            if os.path.exists(page_ptif_path) and os.path.isfile(page_ptif_path):
                                # Register the page PTIF file
                                with open(page_ptif_path, 'rb') as page_ptif_file:
                                    page_obj = ObjectVersion.create(bucket_id, page_ptif_filename, stream=page_ptif_file)
                                    db.session.add(page_obj)
                                    db.session.commit()
                                
                                # Add metadata to record
                                page_obj_dict = {
                                    "key": page_ptif_filename,
                                    "object_version_id": str(page_obj.version_id),
                                    "processor": {
                                        "status": "finished",
                                        "pdf_page": page_count
                                    }
                                }
                                record.media_files.add(page_obj_dict)
                                record.commit()
                                db.session.commit()
                                
                                print(f"Registered page PTIF file {page_ptif_filename}")
                                ptif_files_registered += 1
                                page_count += 1
                            else:
                                break
                    
                    except Exception as e:
                        print(f"Error registering PTIF file {ptif_filename}: {str(e)}")
                        errors += 1
                
                records_processed += 1
                    
            except Exception as e:
                print(f"Error processing record {record_id}: {str(e)}")
                errors += 1
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Print summary
        print("\n===== PTIF Registration Summary =====")
        print(f"Total records processed: {records_processed}")
        print(f"PTIF files registered: {ptif_files_registered}")
        print(f"Errors encountered: {errors}")
        print(f"Elapsed time: {elapsed_time:.2f} seconds")
        print("=====================================")
        
        print("\nNext steps:")
        print("1. View the PDF in the record: https://127.0.0.1:5000/records/216")
        print("2. You should now see the PDF with the PTIF files in the Mirador viewer")

if __name__ == "__main__":
    register_pdf_ptif_files() 