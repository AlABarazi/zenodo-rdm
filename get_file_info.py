#!/usr/bin/env python
"""
Script to get information about the PDF files in the records.
Run this script with:
  source .venv/bin/activate && python get_file_info.py
"""

import os
import re
from invenio_app.factory import create_api
from flask import current_app

# Create Flask application
app = create_api()

def get_file_info():
    """Get information about the PDF files in the records."""
    with app.app_context():
        from invenio_rdm_records.records.api import RDMRecord
        from invenio_files_rest.models import Bucket, ObjectVersion
        
        record_ids = [
            "b8902cb3-eaaf-4201-89c6-f6475085c0c3",
            "d8ca5052-6704-41e7-aadf-4d021b7f4bdd"
        ]
        
        # Print general information
        print(f"Instance path: {current_app.instance_path}")
        data_dir = os.path.join(current_app.instance_path, "data")
        print(f"Data directory: {data_dir}")
        images_dir = os.path.join(current_app.instance_path, "images")
        print(f"Images directory: {images_dir}")
        
        for record_id in record_ids:
            try:
                record = RDMRecord.get_record(record_id)
                print(f"\nRecord ID: {record.id}")
                
                # Get file bucket information
                files_bucket_id = record.files.bucket_id
                media_bucket_id = record.media_files.bucket_id
                print(f"Files bucket ID: {files_bucket_id}")
                print(f"Media files bucket ID: {media_bucket_id}")
                
                # Print list of files
                files = list(record.files.keys())
                print(f"Files: {files}")
                media_files = list(record.media_files.keys())
                print(f"Media files: {media_files}")
                
                # Get bucket objects
                files_bucket = Bucket.query.filter_by(id=files_bucket_id).one()
                media_bucket = Bucket.query.filter_by(id=media_bucket_id).one()
                
                # Get files from buckets
                file_objects = ObjectVersion.query.filter_by(bucket_id=files_bucket_id, is_head=True).all()
                media_objects = ObjectVersion.query.filter_by(bucket_id=media_bucket_id, is_head=True).all()
                
                print("\nFile objects:")
                for obj in file_objects:
                    print(f"  {obj.key} - {obj.file.uri if obj.file else 'No file'}")
                
                print("\nMedia objects:")
                for obj in media_objects:
                    print(f"  {obj.key} - {obj.file.uri if obj.file else 'No file'}")
                
                # Try a direct check for the bucket directories
                # This assumes the file storage is using a direct bucket storage pattern
                bucket_pattern = r"[0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                
                print(f"\nLooking for bucket directories for {files_bucket_id}...")
                files_bucket_str = str(files_bucket_id)
                bucket_dir_pattern = f"{files_bucket_str[:2]}/{files_bucket_str[2:4]}/{files_bucket_str}"
                print(f"Bucket directory pattern: {bucket_dir_pattern}")
                
                # Search for PDF files in the data directory
                print(f"\nSearching for PDF files in {data_dir}...")
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            path = os.path.join(root, file)
                            print(f"Found PDF: {path}")
                
                # If using vips, check if PTIF files exist
                print(f"\nChecking for existing PTIF files in {images_dir}...")
                if os.path.exists(images_dir):
                    for root, dirs, files in os.walk(images_dir):
                        for file in files:
                            if file.lower().endswith('.ptif'):
                                path = os.path.join(root, file)
                                print(f"Found PTIF: {path}")
                else:
                    print(f"Images directory not found: {images_dir}")
                
            except Exception as e:
                print(f"Error processing record {record_id}: {str(e)}")

if __name__ == "__main__":
    get_file_info() 