#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to manually create PTIF files for PDFs without modifying records.
This script checks all records, finds PDF files with missing PTIF files on disk,
and creates the PTIF files directly in the correct location.

Usage:
    python create_pdf_ptif_manual.py

"""

import os
import sys
import time
import traceback
import subprocess
import shutil
from invenio_app.factory import create_app
from flask import current_app

# Create Flask application
app = create_app()

def create_pdf_ptif_files():
    """Create PTIF files for PDFs where they are missing."""
    start_time = time.time()
    
    # Statistics
    total_records = 0
    records_with_media_files = 0
    pdf_records = 0
    ptif_files_created = 0
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
                                    print(f"  Manually creating PTIF file...")
                                    
                                    # Get original file to convert
                                    original_file = record.files[filename]
                                    original_file_uri = original_file.file.uri
                                    print(f"  Original file path: {original_file_uri}")
                                    
                                    # Create output directory structure
                                    output_dir = os.path.dirname(uri)
                                    if not os.path.exists(output_dir):
                                        os.makedirs(output_dir, exist_ok=True)
                                    
                                    # First step - convert PDF to TIFF
                                    temp_tiff = f"{uri}.temp.tiff"
                                    cmd1 = [
                                        "vips", "pdfload", original_file_uri,
                                        temp_tiff,
                                        f"--dpi={iiif_config.get('dpi', 300)}"
                                    ]
                                    print(f"  Running command (PDF to TIFF): {' '.join(cmd1)}")
                                    result1 = subprocess.run(cmd1, capture_output=True, text=True)
                                    
                                    if result1.returncode != 0:
                                        print(f"  ERROR: vips pdfload command failed: {result1.stderr}")
                                        errors += 1
                                        continue
                                    
                                    # Second step - convert TIFF to PTIF
                                    cmd2 = [
                                        "vips", "tiffsave", temp_tiff,
                                        uri,
                                        "--tile", "--pyramid", "--compression=jpeg",
                                        f"--tile-width={iiif_config.get('tile_width', 512)}",
                                        f"--tile-height={iiif_config.get('tile_height', 512)}"
                                    ]
                                    print(f"  Running command (TIFF to PTIF): {' '.join(cmd2)}")
                                    result2 = subprocess.run(cmd2, capture_output=True, text=True)
                                    
                                    # Clean up temp file
                                    if os.path.exists(temp_tiff):
                                        os.remove(temp_tiff)
                                    
                                    if result2.returncode != 0:
                                        print(f"  ERROR: vips tiffsave command failed: {result2.stderr}")
                                        errors += 1
                                        continue
                                    
                                    # Verify the output file exists
                                    if not os.path.exists(uri):
                                        print(f"  ERROR: Output file was not created: {uri}")
                                        errors += 1
                                        continue
                                    
                                    # Set proper permissions
                                    os.chmod(uri, 0o644)
                                    
                                    print(f"  Successfully created PTIF file: {uri}")
                                    print(f"  File size: {os.path.getsize(uri)} bytes")
                                    ptif_files_created += 1
                                else:
                                    print(f"  PTIF file exists on disk: {uri}")
                        else:
                            print(f"  No PTIF file metadata found for PDF {filename}")
                
            except Exception as e:
                print(f"Error processing record {record_id}: {str(e)}")
                traceback.print_exc()
                errors += 1
    
    elapsed_time = time.time() - start_time
    
    print("\n===== PDF PTIF Creation Summary =====")
    print(f"Total records: {total_records}")
    print(f"Records with media files enabled: {records_with_media_files}")
    print(f"Records with PDF files: {pdf_records}")
    print(f"PTIF files created: {ptif_files_created}")
    print(f"Errors encountered: {errors}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print("====================================")

if __name__ == "__main__":
    create_pdf_ptif_files() 