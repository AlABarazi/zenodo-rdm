#!/usr/bin/env python
"""
Script to directly modify the IIIF manifest to include PTIF files for PDF files.
This is a more direct approach that can be used when other methods fail.

Run this script with:
  source .venv/bin/activate && python modify_manifest.py
"""

import os
import sys
import json
import requests
import pyvips
from urllib3.exceptions import InsecureRequestWarning
import time
from datetime import datetime
from invenio_app.factory import create_api

# Suppress only the single warning from urllib3 needed
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Create Flask application
app = create_api()

def modify_manifest_for_pdf():
    """Modify the IIIF manifest to include PTIF files for PDF files."""
    with app.app_context():
        # Record IDs with PDF files
        record_ids = ["216"]
        
        for record_id in record_ids:
            try:
                # Get the current manifest
                manifest_url = f"https://127.0.0.1:5000/api/iiif/record:{record_id}/manifest"
                response = requests.get(manifest_url, verify=False)
                if response.status_code != 200:
                    print(f"Failed to get manifest for record {record_id}: {response.status_code}")
                    continue
                
                manifest = response.json()
                print(f"Got manifest for record {record_id}")
                
                # Check if the manifest has any canvases
                sequence = manifest.get("sequences", [{}])[0]
                canvases = sequence.get("canvases", [])
                
                print(f"Found {len(canvases)} canvases in manifest")
                
                # Check the IIIF directory for PTIF files for this record
                images_dir = os.path.join(app.instance_path, "images", "public")
                
                # Look for PTIF files
                ptif_files = []
                for pattern_prefix in ["21", "20"]:
                    dir_pattern = os.path.join(images_dir, pattern_prefix, "6_", "_")
                    if os.path.exists(dir_pattern):
                        for filename in os.listdir(dir_pattern):
                            if filename.endswith(".ptif") and os.path.isfile(os.path.join(dir_pattern, filename)):
                                ptif_files.append({
                                    "filename": filename,
                                    "path": os.path.join(dir_pattern, filename),
                                    "dir_pattern": pattern_prefix
                                })
                
                print(f"Found {len(ptif_files)} PTIF files")
                
                # If we have PTIF files but no canvases, we need to manually create them
                if ptif_files and not canvases:
                    print("Creating canvases for PTIF files...")
                    
                    for ptif_file in ptif_files:
                        filename = ptif_file["filename"]
                        pattern_prefix = ptif_file["dir_pattern"]
                        ptif_path = ptif_file["path"]
                        
                        try:
                            # Get PTIF dimensions using pyvips
                            image = pyvips.Image.new_from_file(ptif_path)
                            width = image.width
                            height = image.height
                            print(f"PTIF dimensions: {width}x{height}")
                            
                            # Create a canvas for this PTIF file
                            canvas_id = f"https://127.0.0.1:5000/api/iiif/record:{record_id}/canvas/{filename}"
                            iiif_base_url = f"https://127.0.0.1:5000/api/iiif/{pattern_prefix}/6_/_/{filename}"
                            
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
                            print(f"Added canvas for {filename}")
                            
                        except Exception as e:
                            print(f"Error processing PTIF file {filename}: {str(e)}")
                    
                    # Check for multi-page PTIF files
                    pdf_filenames = [f["filename"][:-5] for f in ptif_files if f["filename"].endswith(".ptif")]
                    
                    for pdf_filename in pdf_filenames:
                        pattern_prefix = ptif_files[0]["dir_pattern"]  # Use the first pattern
                        dir_pattern = os.path.join(images_dir, pattern_prefix, "6_", "_")
                        
                        page_count = 1
                        while True:
                            page_ptif_filename = f"{pdf_filename}.page-{page_count}.ptif"
                            page_ptif_path = os.path.join(dir_pattern, page_ptif_filename)
                            
                            if os.path.exists(page_ptif_path) and os.path.isfile(page_ptif_path):
                                try:
                                    # Get PTIF dimensions
                                    page_image = pyvips.Image.new_from_file(page_ptif_path)
                                    page_width = page_image.width
                                    page_height = page_image.height
                                    
                                    page_canvas_id = f"https://127.0.0.1:5000/api/iiif/record:{record_id}/canvas/{page_ptif_filename}"
                                    page_iiif_base_url = f"https://127.0.0.1:5000/api/iiif/{pattern_prefix}/6_/_/{page_ptif_filename}"
                                    
                                    page_canvas = {
                                        "@id": page_canvas_id,
                                        "@type": "sc:Canvas",
                                        "label": f"Page {page_count} from {pdf_filename}",
                                        "width": page_width,
                                        "height": page_height,
                                        "images": [
                                            {
                                                "@id": f"{page_canvas_id}/image",
                                                "@type": "oa:Annotation",
                                                "motivation": "sc:painting",
                                                "resource": {
                                                    "@id": f"{page_iiif_base_url}/full/full/0/default.jpg",
                                                    "@type": "dctypes:Image",
                                                    "format": "image/jpeg",
                                                    "width": page_width,
                                                    "height": page_height,
                                                    "service": {
                                                        "@id": page_iiif_base_url,
                                                        "@context": "http://iiif.io/api/image/2/context.json",
                                                        "profile": "http://iiif.io/api/image/2/level1.json",
                                                    },
                                                },
                                                "on": page_canvas_id,
                                            }
                                        ],
                                    }
                                    
                                    canvases.append(page_canvas)
                                    print(f"Added canvas for {page_ptif_filename}")
                                    page_count += 1
                                
                                except Exception as e:
                                    print(f"Error processing page PTIF file {page_ptif_filename}: {str(e)}")
                                    break
                            else:
                                break
                    
                    # Update the manifest with the new canvases
                    manifest["sequences"][0]["canvases"] = canvases
                    
                    # Write the updated manifest to a file
                    output_file = f"updated_manifest_{record_id}.json"
                    with open(output_file, "w") as f:
                        json.dump(manifest, f, indent=2)
                    
                    print(f"Updated manifest written to {output_file}")
                    
                    # Create a monkeypatch function to serve our custom manifest
                    print("Creating monkey patch to serve custom manifest...")
                    
                    manifest_cache = {}
                    manifest_cache[record_id] = manifest
                    
                    def monkeypatch_iiif_manifest(record_id):
                        if record_id in manifest_cache:
                            print(f"Serving cached manifest for record {record_id}")
                            return manifest_cache[record_id]
                    
                    # Instructions for installing the monkey patch
                    print(f"Manifest has been updated with PTIF files and saved to {output_file}")
                    print("To use this updated manifest:")
                    print("1. Start the Invenio server: source .venv/bin/activate && invenio-cli run")
                    print("2. Visit https://127.0.0.1:5000/records/216 to view the record")
                    print("3. If needed, you can copy the manifest.json to the browser console")
                    print("   Copy the content from the file and use it to update the manifest")
                    print("   in the JavaScript console of the browser")
                
            except Exception as e:
                print(f"Error processing record {record_id}: {str(e)}")

if __name__ == "__main__":
    modify_manifest_for_pdf() 