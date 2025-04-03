#!/usr/bin/env python
"""
Script to check media files for records.
Run this script with:
  source .venv/bin/activate && python check_media_files.py
"""

from invenio_app.factory import create_api
from invenio_rdm_records.records.api import RDMRecord

# Create Flask application
app = create_api()

def check_media_files():
    """Check media files for records."""
    with app.app_context():
        record_ids = [
            "b8902cb3-eaaf-4201-89c6-f6475085c0c3",
            "d8ca5052-6704-41e7-aadf-4d021b7f4bdd"
        ]
        
        for record_id in record_ids:
            record = RDMRecord.get_record(record_id)
            print(f"Record ID: {record.id}")
            print(f"Record bucket ID: {record.media_files.bucket_id}")
            print(f"Record files: {list(record.files.keys())}")
            print(f"Record media files: {list(record.media_files.keys())}")
            print(f"Media files enabled: {record.media_files.enabled}")
            print("---")
            
            # Check each media file
            for filename in record.media_files.keys():
                file_obj = record.media_files[filename]
                processor = file_obj.get('processor', {})
                print(f"Media file: {filename}")
                print(f"  Processor status: {processor.get('status', 'unknown')}")
                print(f"  File metadata: {file_obj}")
                print()

if __name__ == "__main__":
    check_media_files() 