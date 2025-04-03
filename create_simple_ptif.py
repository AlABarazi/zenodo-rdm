#!/usr/bin/env python
"""
Script to create a simple PTIF file for a PDF.
This will create a PTIF file for the first page of a PDF only.

Run this script with:
  source .venv/bin/activate && python create_simple_ptif.py
"""

import os
import sys
import json
import subprocess
import shutil
from invenio_app.factory import create_api
from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from flask import current_app

# Create Flask application
app = create_api()

def create_simple_ptif():
    """Create a simple PTIF file for PDFs."""
    with app.app_context():
        from invenio_rdm_records.records.api import RDMRecord
        
        # Record IDs with PDF files
        record_ids = [
            "b8902cb3-eaaf-4201-89c6-f6475085c0c3",
            "d8ca5052-6704-41e7-aadf-4d021b7f4bdd"
        ]
        
        for record_id in record_ids:
            try:
                record = RDMRecord.get_record(record_id)
                if not record or not record.media_files.enabled:
                    print(f"Record {record_id} does not exist or media files not enabled")
                    continue
                
                # Check for PDF files in the record
                pdf_files = [f for f in record.files.keys() if f.lower().endswith('.pdf')]
                if not pdf_files:
                    print(f"No PDF files found in record {record_id}")
                    continue
                
                for pdf_filename in pdf_files:
                    print(f"Processing {pdf_filename} from record {record_id}")
                    
                    # Check if the PTIF file already exists
                    ptif_filename = f"{pdf_filename}.ptif"
                    if ptif_filename in record.media_files:
                        print(f"{ptif_filename} already exists in record {record_id}")
                        continue
                    
                    # Original PDF file path
                    pdf_file = record.files[pdf_filename]
                    pdf_obj = record.files.get_file_object(pdf_filename)
                    pdf_path = pdf_obj.file.uri
                    
                    # Create temporary directory for processing
                    temp_dir = os.path.join(current_app.instance_path, "temp_ptif_files")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Output file paths
                    temp_tiff_path = os.path.join(temp_dir, f"{pdf_filename}.temp.tiff")
                    ptif_path = os.path.join(temp_dir, ptif_filename)
                    
                    # Get DPI from config
                    iiif_config = current_app.config.get("IIIF_TILES_CONVERTER_PARAMS", {})
                    dpi = iiif_config.get("dpi", 300)
                    
                    try:
                        # Command to convert PDF to TIFF
                        cmd1 = [
                            "vips", "pdfload", pdf_path, temp_tiff_path,
                            f"--dpi={dpi}", "--page=0"  # Only convert first page
                        ]
                        
                        # Command to convert TIFF to PTIF
                        cmd2 = [
                            "vips", "tiffsave", temp_tiff_path, ptif_path,
                            "--tile", "--pyramid", "--compression=jpeg",
                            "--tile-width=256", "--tile-height=256"
                        ]
                        
                        # Execute commands
                        print(f"Running command: {' '.join(cmd1)}")
                        result1 = subprocess.run(cmd1, check=True, capture_output=True, text=True)
                        
                        print(f"Running command: {' '.join(cmd2)}")
                        result2 = subprocess.run(cmd2, check=True, capture_output=True, text=True)
                        
                        # Check if PTIF file was created successfully
                        if os.path.exists(ptif_path) and os.path.getsize(ptif_path) > 0:
                            print(f"PTIF file created successfully: {ptif_path}")
                            print(f"PTIF file size: {os.path.getsize(ptif_path)} bytes")
                            
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
                            print(f"Successfully registered {ptif_filename} for record {record_id}")
                        else:
                            print(f"Failed to create PTIF file for {pdf_filename}")
                            
                    except subprocess.CalledProcessError as e:
                        print(f"Error converting {pdf_filename}: {e}")
                        print(f"Command output: {e.stdout}")
                        print(f"Command error: {e.stderr}")
                    
                    except Exception as e:
                        print(f"Error processing {pdf_filename}: {str(e)}")
                    
                    finally:
                        # Clean up temporary files
                        for temp_file in [temp_tiff_path, ptif_path]:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                                print(f"Removed temporary file: {temp_file}")
            
            except Exception as e:
                print(f"Error processing record {record_id}: {str(e)}")

if __name__ == "__main__":
    create_simple_ptif() 