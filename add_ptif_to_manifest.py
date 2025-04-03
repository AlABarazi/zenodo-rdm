#!/usr/bin/env python
"""
Script to add PTIF files to IIIF manifest for PDF files.
This script manually modifies the IIIF manifest resource to include PDF PTIF files.

Run this script with:
  source .venv/bin/activate && python add_ptif_to_manifest.py
"""

import os
import sys
import json
import requests
from flask import current_app
from invenio_app.factory import create_api

# Create Flask application
app = create_api()

def add_ptif_to_manifest():
    """Add PTIF files to IIIF manifest for PDF files."""
    with app.app_context():
        # Record IDs with PDF files that we want to check
        record_ids = ["216"]
        
        for record_id in record_ids:
            try:
                # Get the current manifest to see what's there
                manifest_url = f"https://127.0.0.1:5000/api/iiif/record:{record_id}/manifest"
                
                # Allow self-signed certificates for local development
                response = requests.get(manifest_url, verify=False)
                if response.status_code != 200:
                    print(f"Failed to get manifest for record {record_id}: {response.status_code}")
                    continue
                
                manifest = response.json()
                print(f"Got manifest for record {record_id}")
                print(f"Manifest: {json.dumps(manifest, indent=2)}")
                
                # Check if the manifest has any canvases
                sequence = manifest.get("sequences", [{}])[0]
                canvases = sequence.get("canvases", [])
                
                print(f"Found {len(canvases)} canvases in manifest")
                
                # Check the IIIF directory for PTIF files for this record
                images_dir = os.path.join(current_app.instance_path, "images", "public")
                
                # Check all possible directory patterns where we might find PTIF files
                ptif_files = []
                for pattern_prefix in ["21", "20"]:
                    dir_pattern = os.path.join(images_dir, pattern_prefix, "6_", "_")
                    if os.path.exists(dir_pattern):
                        print(f"Checking directory: {dir_pattern}")
                        for filename in os.listdir(dir_pattern):
                            if filename.endswith(".ptif") and os.path.isfile(os.path.join(dir_pattern, filename)):
                                ptif_files.append({
                                    "filename": filename,
                                    "path": os.path.join(dir_pattern, filename),
                                    "dir_pattern": pattern_prefix
                                })
                
                print(f"Found {len(ptif_files)} PTIF files: {ptif_files}")
                
                # If we have PTIF files but no canvases, we need to manually create them
                if ptif_files and not canvases:
                    print("Creating canvases for PTIF files...")
                    
                    # For each PTIF file, we need to create a canvas in the manifest
                    from invenio_iiif.utils import iiif_image_key
                    
                    for ptif_file in ptif_files:
                        filename = ptif_file["filename"]
                        # Get PTIF file dimensions
                        import pyvips
                        try:
                            image = pyvips.Image.new_from_file(ptif_file["path"])
                            width = image.width
                            height = image.height
                            print(f"PTIF dimensions: {width}x{height}")
                            
                            # Create a canvas for this PTIF file
                            canvas_id = f"https://127.0.0.1:5000/api/iiif/record:{record_id}/canvas/{filename}"
                            iiif_base_url = f"https://127.0.0.1:5000/api/iiif/{ptif_file['dir_pattern']}/6_/_/{filename}"
                            
                            canvas = {
                                "@id": canvas_id,
                                "@type": "sc:Canvas",
                                "label": f"Page from {filename}",
                                "width": width,
                                "height": height,
                                "images": [
                                    {
                                        "@id": f"{canvas_id}/image",
                                        "@type": "oa:Annotation",
                                        "motivation": "sc:painting",
                                        "resource": {
                                            "@id": f"{iiif_base_url}/full/full/0/default.jpg",
                                            "@type": "dctypes:Image",
                                            "format": "image/jpeg",
                                            "width": width,
                                            "height": height,
                                            "service": {
                                                "@id": iiif_base_url,
                                                "@context": "http://iiif.io/api/image/2/context.json",
                                                "profile": "http://iiif.io/api/image/2/level1.json"
                                            }
                                        },
                                        "on": canvas_id
                                    }
                                ]
                            }
                            
                            # Add the canvas to the manifest
                            canvases.append(canvas)
                            
                        except Exception as e:
                            print(f"Error processing PTIF file {filename}: {str(e)}")
                    
                    # Update the manifest with the new canvases
                    manifest["sequences"][0]["canvases"] = canvases
                    
                    # Write the updated manifest to a file
                    output_file = f"manifest_{record_id}.json"
                    with open(output_file, "w") as f:
                        json.dump(manifest, f, indent=2)
                    
                    print(f"Updated manifest written to {output_file}")
                    print("Next steps:")
                    print("1. Start the Invenio server: source .venv/bin/activate && invenio-cli run")
                    print(f"2. Visit https://127.0.0.1:5000/records/{record_id} to view the record")
                    print("3. You should now see the PDF with the PTIF files in the Mirador viewer")
                
            except Exception as e:
                print(f"Error processing record {record_id}: {str(e)}")

if __name__ == "__main__":
    add_ptif_to_manifest() 