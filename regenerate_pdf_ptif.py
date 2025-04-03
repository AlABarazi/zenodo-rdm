#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to regenerate PTIF files for PDFs in the system.
This script checks all records, finds PDF files with missing PTIF files on disk,
and regenerates the PTIF files.

Usage:
    python regenerate_pdf_ptif.py

"""

import os
import sys
import time
import traceback
import subprocess
from invenio_app.factory import create_app
from invenio_db import db
from flask import current_app
from invenio_files_rest.models import FileInstance, ObjectVersion

# Create Flask application
app = create_app()

def regenerate_pdf_ptif_files():
    """Regenerate PTIF files for PDFs where they are missing."""
    start_time = time.time()
    
    # Statistics
    total_records = 0
    records_with_media_files = 0
    pdf_records = 0
    ptif_files_regenerated = 0
    errors = 0
    
    # Get all record UUIDs
    with app.app_context():
        from invenio_rdm_records.records.api import RDMRecord
        
        # Check for vips command availability
        try:
            result = subprocess.run(['vips', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"VIPS is available! Version: {result.stdout.strip()}")
            else:
                print("ERROR: vips command not found or error running it!")
                return
        except Exception as e:
            print(f"ERROR: Failed to check vips availability: {str(e)}")
            return
        
        # Get IIIF configuration
        iiif_config = current_app.config.get("IIIF_TILES_CONVERTER_PARAMS", {})
        storage_path = current_app.config.get(
            "IIIF_TILES_STORAGE_PATH",
            os.path.join(current_app.instance_path, "images")
        )
        
        print(f"IIIF storage path: {storage_path}")
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, exist_ok=True)
            print(f"Created storage path: {storage_path}")
        
        records = RDMRecord.model_cls.query.all()
        total_records = len(records)
        
        print(f"Found {total_records} records to check")
        
        for record_model in records:
            try:
                # Load the record
                record_id = str(record_model.id)
                record = RDMRecord.get_record(record_model.id)
                print(f"\nChecking record: {record_id}")
                
                # Check if media files are enabled
                if not hasattr(record, 'media_files') or not record.media_files.enabled:
                    print("  Media files not enabled")
                    continue
                
                records_with_media_files += 1
                
                # Look for PDF files
                for filename in record.files:
                    if filename.lower().endswith('.pdf'):
                        pdf_records += 1
                        print(f"  Found PDF file: {filename}")
                        
                        # Check if PTIF exists
                        ptif_filename = f"{filename}.ptif"
                        if ptif_filename in record.media_files:
                            ptif_file = record.media_files[ptif_filename]
                            status = ptif_file.processor.get('status') if hasattr(ptif_file, 'processor') and ptif_file.processor else 'unknown'
                            print(f"  PTIF exists with status: {status}")
                            
                            # Check if file physically exists
                            if hasattr(ptif_file, 'file') and ptif_file.file:
                                uri = ptif_file.file.uri
                                if not os.path.exists(uri) or os.path.getsize(uri) == 0:
                                    print(f"  PTIF file doesn't exist or is empty on disk: {uri}")
                                    print(f"  Regenerating PTIF file...")
                                    
                                    # Delete the existing PTIF file record
                                    print(f"  Deleting existing PTIF record in media_files...")
                                    record.media_files.delete(ptif_filename)
                                    db.session.commit()
                                    
                                    # Get original file to convert
                                    original_file = record.files[filename]
                                    original_file_uri = original_file.file.uri
                                    print(f"  Original file path: {original_file_uri}")
                                    
                                    # Create output directory structure
                                    output_path = os.path.join(storage_path, "public", record_id[0:2], record_id[2:4], "_", ptif_filename)
                                    output_dir = os.path.dirname(output_path)
                                    if not os.path.exists(output_dir):
                                        os.makedirs(output_dir, exist_ok=True)
                                        
                                    print(f"  Output path: {output_path}")
                                    
                                    # Use vips to generate PTIF from PDF
                                    cmd = [
                                        "vips", "pdfload", original_file_uri, 
                                        output_path, 
                                        f"--dpi={iiif_config.get('dpi', 300)}",
                                        "--layout=openslide"
                                    ]
                                    print(f"  Running command: {' '.join(cmd)}")
                                    result = subprocess.run(cmd, capture_output=True, text=True)
                                    
                                    if result.returncode != 0:
                                        print(f"  ERROR: vips command failed: {result.stderr}")
                                        errors += 1
                                        continue
                                    
                                    # Verify the output file exists
                                    if not os.path.exists(output_path):
                                        print(f"  ERROR: Output file was not created: {output_path}")
                                        errors += 1
                                        continue
                                    
                                    # Add the new PTIF file to media_files
                                    print(f"  Adding new PTIF file to media_files...")
                                    try:
                                        # Create ObjectVersion for the new file
                                        bucket_id = record.media_files.bucket_id
                                        obj = ObjectVersion.create(bucket_id, ptif_filename, stream=open(output_path, 'rb'))
                                        db.session.add(obj)
                                        db.session.commit()
                                        
                                        # Update metadata in record
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
                                        
                                        print(f"  Successfully regenerated PTIF file!")
                                        ptif_files_regenerated += 1
                                    except Exception as e:
                                        print(f"  ERROR: Failed to add new media file: {str(e)}")
                                        traceback.print_exc()
                                        errors += 1
                                else:
                                    print(f"  PTIF file exists on disk: {uri}")
                        else:
                            print(f"  No PTIF file found for PDF {filename}")
                
            except Exception as e:
                print(f"Error processing record {record_id}: {str(e)}")
                traceback.print_exc()
                errors += 1
    
    elapsed_time = time.time() - start_time
    
    print("\n===== PDF PTIF Regeneration Summary =====")
    print(f"Total records: {total_records}")
    print(f"Records with media files enabled: {records_with_media_files}")
    print(f"Records with PDF files: {pdf_records}")
    print(f"PTIF files regenerated: {ptif_files_regenerated}")
    print(f"Errors encountered: {errors}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print("==========================================")

if __name__ == "__main__":
    regenerate_pdf_ptif_files() 