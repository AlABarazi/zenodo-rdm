#!/usr/bin/env python3
"""
Register PTIF files with PDF records

This script checks for PTIF files in the IIIF directory that correspond to PDF files
in records, and ensures they are properly connected in the IIIF manifest.

Usage:
    python register_ptif.py [--record-id ID]

Arguments:
    --record-id ID    Register PTIF for a specific record ID
"""

import os
import sys
import json
import glob
import argparse
import subprocess
from pathlib import Path

# Configuration
INSTANCE_PATH = ".venv/var/instance"
IIIF_DIR = os.path.join(INSTANCE_PATH, "images", "public")
RECORD_DEFAULT = "216"  # Default record ID to process

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Register PTIF files with PDF records")
    parser.add_argument("--record-id", type=str, default=RECORD_DEFAULT,
                        help="Register PTIF for a specific record ID")
    return parser.parse_args()

def find_ptif_files(record_id=RECORD_DEFAULT):
    """
    Search for PTIF files in the IIIF directory that match the record ID pattern.
    Returns a list of PTIF file paths.
    """
    ptif_files = []
    
    # Check common directory patterns for the record ID
    # For example, record ID 216 might be in directories 21/6_/_/ or 20/6_/_/
    
    # First try the exact prefix
    record_prefix = record_id[:2]
    record_suffix = record_id[2:] + "_/_"
    pattern = os.path.join(IIIF_DIR, record_prefix, record_suffix, "*.ptif")
    print(f"Checking directory: {os.path.join(IIIF_DIR, record_prefix, record_suffix)}")
    ptif_files.extend(glob.glob(pattern))
    
    # Try alternative prefix (one less)
    alt_prefix = str(int(record_prefix) - 1)
    if len(alt_prefix) == 1:
        alt_prefix = "0" + alt_prefix
    pattern = os.path.join(IIIF_DIR, alt_prefix, record_suffix, "*.ptif")
    print(f"Checking directory: {os.path.join(IIIF_DIR, alt_prefix, record_suffix)}")
    ptif_files.extend(glob.glob(pattern))
    
    if ptif_files:
        print(f"Found {len(ptif_files)} PTIF files")
        for ptif in ptif_files:
            # Get dimensions of the PTIF file
            try:
                result = subprocess.run(
                    ["vips", "header", "-f", "width", ptif], 
                    capture_output=True, text=True, check=True
                )
                width = int(result.stdout.strip())
                
                result = subprocess.run(
                    ["vips", "header", "-f", "height", ptif], 
                    capture_output=True, text=True, check=True
                )
                height = int(result.stdout.strip())
                
                print(f"PTIF file {os.path.basename(ptif)}: {width}x{height}")
            except subprocess.CalledProcessError:
                print(f"Could not get dimensions for {ptif}")
                # Use default dimensions
                width, height = 1200, 1800
    else:
        print("No PTIF files found")
    
    return ptif_files

def create_manifest(record_id, ptif_files):
    """
    Create a IIIF manifest for the record with the PTIF files.
    Returns a manifest JSON object.
    """
    # Base manifest structure
    manifest = {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@type": "sc:Manifest",
        "@id": f"https://127.0.0.1:5000/api/iiif/record:{record_id}/manifest",
        "label": "PDF Document",
        "metadata": [
            {
                "label": "Publication Date",
                "value": "2025-04-03"
            }
        ],
        "description": "Manifest generated for PDF document",
        "sequences": [
            {
                "@id": f"https://127.0.0.1:5000/api/iiif/record:{record_id}/sequence/default",
                "@type": "sc:Sequence",
                "label": "Current Page Order",
                "viewingDirection": "left-to-right",
                "viewingHint": "individuals",
                "canvases": []
            }
        ]
    }
    
    # Add a canvas for each PTIF file
    canvases = []
    for ptif_path in ptif_files:
        try:
            # Get dimensions of the PTIF file
            result = subprocess.run(
                ["vips", "header", "-f", "width", ptif_path], 
                capture_output=True, text=True, check=True
            )
            width = int(result.stdout.strip())
            
            result = subprocess.run(
                ["vips", "header", "-f", "height", ptif_path], 
                capture_output=True, text=True, check=True
            )
            height = int(result.stdout.strip())
        except subprocess.CalledProcessError:
            # Use default dimensions
            width, height = 1200, 1800
        
        # Get the filename and create a canvas
        filename = os.path.basename(ptif_path)
        
        # Convert the full path to the IIIF URL path
        # Example: /path/to/instance/images/public/21/6_/_/file.ptif -> /api/iiif/21/6_/_/file.ptif
        rel_path = os.path.relpath(ptif_path, IIIF_DIR)
        dir_parts = os.path.split(rel_path)[0].split(os.path.sep)
        if len(dir_parts) >= 2:
            iiif_path = f"/api/iiif/{dir_parts[0]}/{dir_parts[1]}/{filename}"
        else:
            # Fallback if the path structure is not as expected
            iiif_path = f"/api/iiif/{record_id[:2]}/{record_id[2:]}_/_/{filename}"
        
        canvas = {
            "@id": f"https://127.0.0.1:5000/api/iiif/record:{record_id}/canvas/{filename}",
            "@type": "sc:Canvas",
            "label": f"Page from {filename}",
            "width": width,
            "height": height,
            "images": [
                {
                    "@id": f"https://127.0.0.1:5000/api/iiif/record:{record_id}/canvas/{filename}/image",
                    "@type": "oa:Annotation",
                    "motivation": "sc:painting",
                    "resource": {
                        "@id": f"https://127.0.0.1:5000{iiif_path}/full/full/0/default.jpg",
                        "@type": "dctypes:Image",
                        "format": "image/jpeg",
                        "width": width,
                        "height": height,
                        "service": {
                            "@id": f"https://127.0.0.1:5000{iiif_path}",
                            "@context": "http://iiif.io/api/image/2/context.json",
                            "profile": "http://iiif.io/api/image/2/level1.json"
                        }
                    },
                    "on": f"https://127.0.0.1:5000/api/iiif/record:{record_id}/canvas/{filename}"
                }
            ]
        }
        canvases.append(canvas)
    
    manifest["sequences"][0]["canvases"] = canvases
    return manifest

def save_manifest(manifest, record_id):
    """Save the manifest to a file."""
    manifest_file = f"manifest_{record_id}.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved manifest to {manifest_file}")
    
    # Create JavaScript to inject the manifest
    js_file = "inject_manifest.js"
    with open(js_file, "w") as f:
        f.write("\n// Function to replace the PDF manifest with our custom manifest\n")
        f.write("function replacePDFManifest() {\n")
        f.write("  // The manifest data\n")
        f.write(f"  const customManifest = {json.dumps(manifest, indent=2)};\n")
        f.write("  \n")
        f.write("  // Find the Mirador instance\n")
        f.write("  const miradorInstanceElement = document.getElementById('m3-dist');\n")
        f.write("  if (!miradorInstanceElement) {\n")
        f.write("    console.error('Mirador instance not found');\n")
        f.write("    return;\n")
        f.write("  }\n")
        f.write("  \n")
        f.write("  // Get the manifest URL from the data attribute\n")
        f.write("  const manifestUrl = miradorInstanceElement.getAttribute('data-manifest');\n")
        f.write("  console.log('Manifest URL:', manifestUrl);\n")
        f.write("  \n")
        f.write("  // Create a new manifest URL using the same URL but with a timestamp to bypass cache\n")
        f.write("  const newManifestUrl = manifestUrl + '?t=' + Date.now();\n")
        f.write("  \n")
        f.write("  // Override the fetch function to return our custom manifest for the manifest URL\n")
        f.write("  const originalFetch = window.fetch;\n")
        f.write("  window.fetch = function(url, options) {\n")
        f.write("    if (url.startsWith(manifestUrl)) {\n")
        f.write("      console.log('Intercepting fetch request for manifest URL:', url);\n")
        f.write("      return Promise.resolve({\n")
        f.write("        ok: true,\n")
        f.write("        status: 200,\n")
        f.write("        json: () => Promise.resolve(customManifest)\n")
        f.write("      });\n")
        f.write("    }\n")
        f.write("    return originalFetch(url, options);\n")
        f.write("  };\n")
        f.write("  \n")
        f.write("  // Set the new manifest URL and trigger a reload\n")
        f.write("  miradorInstanceElement.setAttribute('data-manifest', newManifestUrl);\n")
        f.write("  \n")
        f.write("  // Create a new event to trigger a reload\n")
        f.write("  const event = new Event('manifestChanged');\n")
        f.write("  miradorInstanceElement.dispatchEvent(event);\n")
        f.write("  \n")
        f.write("  console.log('Manifest replaced successfully');\n")
        f.write("}\n")
        f.write("\n")
        f.write("// Run the function\n")
        f.write("replacePDFManifest();\n")
    
    print(f"Saved JavaScript to {js_file}")
    
    # Print instructions
    print("\nInstructions:")
    print(f"1. Start the Invenio server: source .venv/bin/activate && invenio-cli run")
    print(f"2. Visit https://127.0.0.1:5000/records/{record_id} to view the record")
    print("3. Open the browser developer console (F12)")
    print(f"4. Copy the contents of {js_file} and paste it into the console")
    print("5. The PDF should now display with the PTIF file in the Mirador viewer")

def main():
    """Main function."""
    args = parse_args()
    record_id = args.record_id
    
    # Find PTIF files for the record
    ptif_files = find_ptif_files(record_id)
    
    if not ptif_files:
        print(f"No PTIF files found for record {record_id}")
        return
    
    # Create a manifest for the PTIF files
    manifest = create_manifest(record_id, ptif_files)
    
    # Save the manifest and create an injection script
    save_manifest(manifest, record_id)

if __name__ == "__main__":
    main() 