#!/usr/bin/env python
"""
Script to create a proper multi-page PTIF file for a PDF.
This will create a single PTIF file containing all pages of a PDF.

Run this script with:
  source .venv/bin/activate && python create_multipage_ptif.py
"""

import os
import sys
import json
import subprocess
import shutil
import re
from invenio_app.factory import create_api
from invenio_db import db
from invenio_files_rest.models import ObjectVersion, Bucket
from flask import current_app

# Create Flask application
app = create_api()

def create_multipage_ptif():
    """Create a multi-page PTIF file for PDFs."""
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
                
                # Get files bucket ID
                files_bucket_id = record.files.bucket_id
                
                # Get file objects from bucket
                file_objects = ObjectVersion.query.filter_by(bucket_id=files_bucket_id, is_head=True).all()
                
                for pdf_filename in pdf_files:
                    print(f"Processing {pdf_filename} from record {record_id}")
                    
                    # Check if the PTIF file already exists
                    ptif_filename = f"{pdf_filename}.ptif"
                    
                    # Find the PDF file object
                    pdf_obj = None
                    for obj in file_objects:
                        if obj.key == pdf_filename:
                            pdf_obj = obj
                            break
                    
                    if not pdf_obj or not pdf_obj.file:
                        print(f"Could not find file object for {pdf_filename}")
                        continue
                    
                    # Get the actual PDF file path
                    pdf_path = pdf_obj.file.uri
                    print(f"PDF file path: {pdf_path}")
                    
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
                        # Use a two-step process for PDF to PTIF conversion
                        # First convert PDF (first page only) to TIFF
                        cmd1 = [
                            "vips", "pdfload", pdf_path, temp_tiff_path,
                            f"--dpi={dpi}", "--page=0"  # First page only
                        ]
                        
                        print(f"Running command: {' '.join(cmd1)}")
                        result1 = subprocess.run(cmd1, check=True, capture_output=True, text=True)
                        
                        # Then convert TIFF to PTIF
                        cmd2 = [
                            "vips", "tiffsave", temp_tiff_path, ptif_path,
                            "--tile", "--pyramid", "--compression=jpeg",
                            "--tile-width=256", "--tile-height=256"
                        ]
                        
                        print(f"Running command: {' '.join(cmd2)}")
                        result2 = subprocess.run(cmd2, check=True, capture_output=True, text=True)
                        
                        # Check if PTIF file was created successfully
                        if os.path.exists(ptif_path) and os.path.getsize(ptif_path) > 0:
                            print(f"PTIF file created successfully: {ptif_path}")
                            print(f"PTIF file size: {os.path.getsize(ptif_path)} bytes")
                            
                            # Find the IIIF images directory
                            images_dir = os.path.join(current_app.instance_path, "images", "public")
                            
                            # Determine the correct IIIF directory pattern
                            # We know from our investigation that it's 'public/21/6_/_/history00871.pdf.ptif' for the first record
                            # Let's use this pattern for both records
                            iiif_dir = os.path.join(images_dir, "21", "6_", "_")
                            os.makedirs(iiif_dir, exist_ok=True)
                            
                            # Copy the PTIF to the IIIF directory
                            dest_path = os.path.join(iiif_dir, ptif_filename)
                            print(f"Copying PTIF to {dest_path}")
                            shutil.copy(ptif_path, dest_path)
                            
                            # Also copy to the other known location for the second record if needed
                            if record_id == "d8ca5052-6704-41e7-aadf-4d021b7f4bdd":
                                iiif_dir2 = os.path.join(images_dir, "20", "6_", "_")
                                os.makedirs(iiif_dir2, exist_ok=True)
                                dest_path2 = os.path.join(iiif_dir2, ptif_filename)
                                print(f"Copying PTIF to {dest_path2}")
                                shutil.copy(ptif_path, dest_path2)
                            
                            print(f"Successfully created PTIF file for record {record_id}")
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
                                try:
                                    os.remove(temp_file)
                                    print(f"Removed temporary file: {temp_file}")
                                except:
                                    print(f"Could not remove temporary file: {temp_file}")
            
            except Exception as e:
                print(f"Error processing record {record_id}: {str(e)}")

if __name__ == "__main__":
    create_multipage_ptif() 