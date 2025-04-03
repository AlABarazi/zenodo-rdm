#!/usr/bin/env python
"""
Script to register PTIF files and generate JSON data for the manifest.
This script provides a simpler way to handle PTIF files for PDF display
without relying on extensions.

Run this script with:
  source .venv/bin/activate && python simple_pdf_viewer.py
"""

import os
import sys
import json
import time
import pyvips
import subprocess
from urllib3.exceptions import InsecureRequestWarning
import requests
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Record ID to process
RECORD_ID = "216"
INSTANCE_PATH = ".venv/var/instance"

def find_ptif_files():
    """Find PTIF files for a PDF document."""
    # Check the IIIF directory for PTIF files
    images_dir = os.path.join(INSTANCE_PATH, "images", "public")
    
    # Look for PTIF files
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
    
    return ptif_files

def create_manifest(ptif_files):
    """Create a manifest with canvases for PTIF files."""
    # Basic manifest structure
    manifest = {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@type": "sc:Manifest",
        "@id": f"https://127.0.0.1:5000/api/iiif/record:{RECORD_ID}/manifest",
        "label": "PDF Document",
        "metadata": [
            {
                "label": "Publication Date",
                "value": time.strftime("%Y-%m-%d")
            }
        ],
        "description": "Manifest generated for PDF document",
        "sequences": [
            {
                "@id": f"https://127.0.0.1:5000/api/iiif/record:{RECORD_ID}/sequence/default",
                "@type": "sc:Sequence",
                "label": "Current Page Order",
                "viewingDirection": "left-to-right",
                "viewingHint": "individuals",
                "canvases": []
            }
        ]
    }
    
    # Add canvases for each PTIF file
    canvases = []
    for ptif_file in ptif_files:
        try:
            filename = ptif_file["filename"]
            pattern_prefix = ptif_file["dir_pattern"]
            ptif_path = ptif_file["path"]
            
            # Get PTIF dimensions
            image = pyvips.Image.new_from_file(ptif_path)
            width = image.width
            height = image.height
            print(f"PTIF file {filename}: {width}x{height}")
            
            # Create canvas for this PTIF file
            canvas_id = f"https://127.0.0.1:5000/api/iiif/record:{RECORD_ID}/canvas/{filename}"
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
            
            canvases.append(canvas)
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    # Add canvases to manifest
    manifest["sequences"][0]["canvases"] = canvases
    
    return manifest

def register_ptif_files():
    """Register PTIF files with the record using invenio-cli."""
    # Create registration command
    register_cmd = f"""
    from invenio_app.factory import create_api
    from invenio_db import db
    from invenio_files_rest.models import ObjectVersion
    from invenio_rdm_records.records.api import RDMRecord
    
    app = create_api()
    
    with app.app_context():
        record = RDMRecord.pid.resolve("{RECORD_ID}")
        
        if not record.media_files.enabled:
            print("Media files not enabled")
            exit(1)
            
        # Check for PDF files
        pdf_files = [f for f in record.files.keys() if f.lower().endswith('.pdf')]
        
        for pdf_filename in pdf_files:
            ptif_filename = f"{{pdf_filename}}.ptif"
            
            # Check the IIIF directory for PTIF files
            images_dir = "{INSTANCE_PATH}/images/public"
            
            # Find PTIF file path
            ptif_path = None
            for prefix in ["21", "20"]:
                dir_pattern = f"{{images_dir}}/{{prefix}}/6_/_"
                path = f"{{dir_pattern}}/{{ptif_filename}}"
                if os.path.exists(path):
                    ptif_path = path
                    break
                    
            if not ptif_path:
                print(f"No PTIF file found for {{pdf_filename}}")
                continue
                
            # Register PTIF file if not already registered
            if ptif_filename not in record.media_files:
                bucket_id = record.media_files.bucket_id
                with open(ptif_path, 'rb') as f:
                    obj = ObjectVersion.create(bucket_id, ptif_filename, stream=f)
                    
                obj_dict = {{
                    "key": ptif_filename,
                    "object_version_id": str(obj.version_id),
                    "processor": {{
                        "status": "finished"
                    }}
                }}
                record.media_files.add(obj_dict)
                record.commit()
                db.session.commit()
                print(f"Registered {{ptif_filename}}")
    """
    
    # Save registration script
    with open("register_ptif.py", "w") as f:
        f.write(register_cmd)
    
    # Run registration script
    print("Registering PTIF files...")
    subprocess.run(["source", ".venv/bin/activate", "&&", "python", "register_ptif.py"], shell=True)

def main():
    """Main function."""
    # Find PTIF files
    ptif_files = find_ptif_files()
    
    if not ptif_files:
        print("No PTIF files found")
        return
    
    print(f"Found {len(ptif_files)} PTIF files")
    
    # Create manifest
    manifest = create_manifest(ptif_files)
    
    # Save manifest
    output_file = f"manifest_{RECORD_ID}.json"
    with open(output_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Saved manifest to {output_file}")
    
    # Output JavaScript to paste in browser console
    js_code = f"""
// Function to replace the PDF manifest with our custom manifest
function replacePDFManifest() {{
  // The manifest data
  const customManifest = {json.dumps(manifest, indent=2)};
  
  // Find the Mirador instance
  const miradorInstanceElement = document.getElementById('m3-dist');
  if (!miradorInstanceElement) {{
    console.error('Mirador instance not found');
    return;
  }}
  
  // Get the manifest URL from the data attribute
  const manifestUrl = miradorInstanceElement.getAttribute('data-manifest');
  console.log('Manifest URL:', manifestUrl);
  
  // Create a new manifest URL using the same URL but with a timestamp to bypass cache
  const newManifestUrl = manifestUrl + '?t=' + Date.now();
  
  // Override the fetch function to return our custom manifest for the manifest URL
  const originalFetch = window.fetch;
  window.fetch = function(url, options) {{
    if (url.startsWith(manifestUrl)) {{
      console.log('Intercepting fetch request for manifest URL:', url);
      return Promise.resolve({{
        ok: true,
        status: 200,
        json: () => Promise.resolve(customManifest)
      }});
    }}
    return originalFetch(url, options);
  }};
  
  // Set the new manifest URL and trigger a reload
  miradorInstanceElement.setAttribute('data-manifest', newManifestUrl);
  
  // Create a new event to trigger a reload
  const event = new Event('manifestChanged');
  miradorInstanceElement.dispatchEvent(event);
  
  console.log('Manifest replaced successfully');
}}

// Run the function
replacePDFManifest();
"""
    
    js_file = "inject_manifest.js"
    with open(js_file, "w") as f:
        f.write(js_code)
    
    print(f"Saved JavaScript to {js_file}")
    print("\nInstructions:")
    print(f"1. Start the Invenio server: source .venv/bin/activate && invenio-cli run")
    print(f"2. Visit https://127.0.0.1:5000/records/{RECORD_ID} to view the record")
    print(f"3. Open the browser developer console (F12)")
    print(f"4. Copy the contents of {js_file} and paste it into the console")
    print(f"5. The PDF should now display with the PTIF file in the Mirador viewer")

if __name__ == "__main__":
    main() 