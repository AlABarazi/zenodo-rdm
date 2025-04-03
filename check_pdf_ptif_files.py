#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to check PDF PTIF files in the system.
This script checks all records, finds those with PDF files, and verifies if PTIF files
have been correctly generated for them.

Usage:
    python check_pdf_ptif_files.py

"""

import os
import sys
import time
from invenio_app.factory import create_app
from invenio_db import db
from invenio_records_resources.records.systemfields.files import FilesField
from invenio_records_resources.records.api import Record
from invenio_files_rest.models import FileInstance, ObjectVersion

# Create Flask application
app = create_app()

def check_pdf_files():
    """Check the status of PDF PTIF files."""
    start_time = time.time()
    
    # Statistics
    total_records = 0
    records_with_media_files = 0
    pdf_records = 0
    pdf_with_ptif = 0
    ptif_init_status = 0
    ptif_processing_status = 0
    ptif_finished_status = 0
    pdf_without_ptif = 0
    
    # Get all record UUIDs
    with app.app_context():
        from invenio_rdm_records.records.api import RDMRecord
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
                has_pdf = False
                for filename in record.files:
                    if filename.lower().endswith('.pdf'):
                        has_pdf = True
                        pdf_records += 1
                        print(f"  Found PDF file: {filename}")
                        
                        # Check if PTIF exists
                        ptif_filename = f"{filename}.ptif"
                        if ptif_filename in record.media_files:
                            pdf_with_ptif += 1
                            ptif_file = record.media_files[ptif_filename]
                            status = ptif_file.processor.get('status') if hasattr(ptif_file, 'processor') and ptif_file.processor else 'unknown'
                            print(f"  PTIF exists with status: {status}")
                            
                            # Track status
                            if status == 'init':
                                ptif_init_status += 1
                            elif status == 'processing':
                                ptif_processing_status += 1
                            elif status == 'finished':
                                ptif_finished_status += 1
                                
                            # Print PTIF file path
                            if hasattr(ptif_file, 'file') and ptif_file.file:
                                print(f"  PTIF file path: {ptif_file.file.uri}")
                                
                                # Check if file physically exists
                                if os.path.exists(ptif_file.file.uri):
                                    print(f"  PTIF file exists on disk")
                                    file_size = os.path.getsize(ptif_file.file.uri)
                                    print(f"  PTIF file size: {file_size} bytes")
                                else:
                                    print(f"  WARNING: PTIF file does not exist on disk!")
                        else:
                            pdf_without_ptif += 1
                            print(f"  No PTIF file found for PDF {filename}")
                
                if not has_pdf:
                    print("  No PDF files found in this record")
                    
            except Exception as e:
                print(f"Error processing record {record_id}: {str(e)}")
    
    elapsed_time = time.time() - start_time
    
    print("\n===== PDF PTIF Files Check Summary =====")
    print(f"Total records: {total_records}")
    print(f"Records with media files enabled: {records_with_media_files}")
    print(f"Records with PDF files: {pdf_records}")
    print(f"PDF files with PTIF: {pdf_with_ptif}")
    print(f"PTIF files with 'init' status: {ptif_init_status}")
    print(f"PTIF files with 'processing' status: {ptif_processing_status}")
    print(f"PTIF files with 'finished' status: {ptif_finished_status}")
    print(f"PDF files without PTIF: {pdf_without_ptif}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print("=========================================")

if __name__ == "__main__":
    check_pdf_files() 