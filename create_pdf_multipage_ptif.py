#!/usr/bin/env python
"""
Script to create multi-page PDF PTIF files for Mirador viewing.

This script extracts each page from a PDF and creates separate PTIF files
for each page to enable proper multi-page viewing in Mirador.

Run this script with:
  source .venv/bin/activate && python create_pdf_multipage_ptif.py
"""

import os
import sys
import time
import json
import subprocess
import traceback
from invenio_app.factory import create_api
from invenio_db import db
from flask import current_app

# Create Flask application
app = create_api()

def get_pdf_page_count(pdf_path):
    """Get the number of pages in a PDF file using pdfinfo."""
    try:
        result = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith('Pages:'):
                    return int(line.split(':')[1].strip())
        return 1  # Default to 1 if we can't determine
    except Exception as e:
        print(f"Error getting PDF page count: {e}")
        return 1

def create_multipage_pdf_ptif_files():
    """Create PTIF files for each page of PDF documents (read-only approach)."""
    print("Starting multi-page PDF PTIF creation (read-only mode)...")
    
    start_time = time.time()
    
    # Stats counters
    total_records = 0
    records_with_media_files = 0
    pdf_records = 0
    multi_page_pdfs = 0
    total_pdf_pages = 0
    ptif_files_created = 0
    errors = 0
    
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
        
        # Check for pdfinfo command availability
        try:
            result = subprocess.run(['pdfinfo', '-v'], capture_output=True, text=True)
            if result.returncode == 0:
                print("pdfinfo is available!")
            else:
                print("ERROR: pdfinfo command not found. Install poppler-utils package!")
                return
        except Exception as e:
            print(f"ERROR: Failed to check pdfinfo availability: {str(e)}")
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
        
        # Create an output directory for our manually created files
        manual_output_path = os.path.join(current_app.instance_path, "manual_ptif_files")
        if not os.path.exists(manual_output_path):
            os.makedirs(manual_output_path, exist_ok=True)
            print(f"Created manual output path: {manual_output_path}")
        
        # Also create a file for registration commands
        registration_script = os.path.join(manual_output_path, "register_ptif_files.py")
        with open(registration_script, 'w') as f:
            f.write('''#!/usr/bin/env python
"""
Script to register the manually created PTIF files.
Run this script with:
  source .venv/bin/activate && python register_ptif_files.py
"""

import os
import sys
from invenio_app.factory import create_api
from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from flask import current_app

# Create Flask application
app = create_api()

def register_ptif_files():
    """Register the manually created PTIF files."""
    with app.app_context():
        from invenio_rdm_records.records.api import RDMRecord
        
        # Add your registration commands below
''')
            
        records = RDMRecord.model_cls.query.all()
        total_records = len(records)
        
        print(f"Found {total_records} records to check")
        
        # Keep track of registration commands
        registration_commands = []
        
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
                        
                        # Get original file to convert
                        original_file = record.files[filename]
                        original_file_uri = original_file.file.uri
                        print(f"  Original file path: {original_file_uri}")
                        
                        # Get the number of pages
                        page_count = get_pdf_page_count(original_file_uri)
                        print(f"  PDF has {page_count} pages")
                        total_pdf_pages += page_count
                        
                        if page_count > 1:
                            multi_page_pdfs += 1
                        
                        # Process each page of the PDF
                        manual_record_dir = os.path.join(manual_output_path, record_id)
                        if not os.path.exists(manual_record_dir):
                            os.makedirs(manual_record_dir, exist_ok=True)
                            
                        # Create a manifest file
                        manifest_path = os.path.join(manual_record_dir, f"{filename}.manifest.json")
                        manifest_data = {
                            "pdf_filename": filename,
                            "total_pages": page_count,
                            "page_files": [f"{filename}.page-{p}.ptif" for p in range(1, page_count + 1)],
                            "record_id": record_id,
                            "bucket_id": str(record.media_files.bucket_id)  # Convert UUID to string
                        }
                        
                        # Add registration commands to the script
                        for page_num in range(1, page_count + 1):
                            page_ptif_filename = f"{filename}.page-{page_num}.ptif"
                            manual_file_path = os.path.join(manual_record_dir, page_ptif_filename)
                            registration_command = f'''
        # Register PTIF for {filename} page {page_num} from record {record_id}
        record = RDMRecord.get_record("{record_id}")
        if record and record.media_files.enabled:
            page_ptif_filename = "{page_ptif_filename}"
            manual_file_path = "{manual_file_path}"
            
            # Check if file already exists
            if page_ptif_filename not in record.media_files:
                try:
                    # Create ObjectVersion for the new file
                    print(f"Registering {{page_ptif_filename}} for record {record_id}")
                    bucket_id = record.media_files.bucket_id
                    obj = ObjectVersion.create(bucket_id, page_ptif_filename, stream=open(manual_file_path, 'rb'))
                    db.session.add(obj)
                    db.session.commit()
                    
                    # Add metadata to record
                    obj_dict = {{
                        "key": page_ptif_filename,
                        "object_version_id": str(obj.version_id),
                        "processor": {{
                            "status": "finished",
                            "pdf_page": {page_num},
                            "pdf_total_pages": {page_count}
                        }}
                    }}
                    record.media_files.add(obj_dict)
                    record.commit()
                    db.session.commit()
                    print(f"Successfully registered {{page_ptif_filename}}")
                except Exception as e:
                    print(f"Error registering {{page_ptif_filename}}: {{str(e)}}")
            else:
                print(f"{{page_ptif_filename}} already exists in record {record_id}")
'''
                            registration_commands.append(registration_command)
                        
                        # Write the manifest file
                        with open(manifest_path, 'w') as f:
                            json.dump(manifest_data, f, indent=2)
                        
                        print(f"  Created manifest file at {manifest_path}")
                        
                        # Process only a few pages for testing if the PDF is large
                        max_pages_to_process = min(page_count, 10) if page_count > 20 else page_count
                        print(f"  Will process {max_pages_to_process} pages out of {page_count}")
                        
                        for page_num in range(1, max_pages_to_process + 1):
                            page_ptif_filename = f"{filename}.page-{page_num}.ptif"
                            print(f"  Processing page {page_num}/{page_count}: {page_ptif_filename}")
                            
                            # Save the page PTIF file to our manual directory
                            manual_file_path = os.path.join(manual_record_dir, page_ptif_filename)
                            
                            # First convert PDF page to temporary TIFF
                            temp_tiff = f"{manual_file_path}.temp.tiff"
                            
                            # Command to extract and convert a specific page (page-1 means 0-indexed)
                            cmd1 = [
                                "vips", "pdfload", original_file_uri,
                                temp_tiff,
                                f"--dpi={iiif_config.get('dpi', 300)}",
                                f"--page={page_num-1}"  # vips uses 0-indexed pages
                            ]
                            print(f"  Running command (PDF page to TIFF): {' '.join(cmd1)}")
                            result1 = subprocess.run(cmd1, capture_output=True, text=True)
                            
                            if result1.returncode != 0:
                                print(f"  ERROR: vips pdfload command failed: {result1.stderr}")
                                errors += 1
                                continue
                            
                            # Convert TIFF to PTIF (pyramidal TIFF)
                            cmd2 = [
                                "vips", "tiffsave", temp_tiff,
                                manual_file_path,
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
                            if not os.path.exists(manual_file_path):
                                print(f"  ERROR: Output file was not created: {manual_file_path}")
                                errors += 1
                                continue
                                
                            print(f"  Successfully created PTIF file for page {page_num}: {manual_file_path}")
                            print(f"  File size: {os.path.getsize(manual_file_path)} bytes")
                            ptif_files_created += 1
                
            except Exception as e:
                print(f"Error processing record {record_id}: {str(e)}")
                traceback.print_exc()
                errors += 1
        
        # Write registration commands to the script
        with open(registration_script, 'a') as f:
            for cmd in registration_commands:
                f.write(cmd)
            
            # Add main call
            f.write('''
if __name__ == "__main__":
    register_ptif_files()
''')
        
        print(f"\nCreated registration script: {registration_script}")
        print("You can run this script later to register the PTIF files with the records.")
    
    elapsed_time = time.time() - start_time
    
    print("\n===== Multi-page PDF PTIF Creation Summary =====")
    print(f"Total records: {total_records}")
    print(f"Records with media files enabled: {records_with_media_files}")
    print(f"Records with PDF files: {pdf_records}")
    print(f"Multi-page PDFs found: {multi_page_pdfs}")
    print(f"Total PDF pages processed: {total_pdf_pages}")
    print(f"PTIF files created: {ptif_files_created}")
    print(f"Errors encountered: {errors}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print("===============================================")

if __name__ == "__main__":
    create_multipage_pdf_ptif_files() 