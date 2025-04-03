# PDF Viewing in IIIF Viewer

This document explains how to fix PDF display issues in Zenodo RDM's IIIF viewer (Mirador) by using PTIF files.

## Problem

By default, PDFs uploaded to Zenodo RDM display as a gray screen in the Mirador viewer because:

1. The IIIF manifest for PDF files does not include any canvases
2. The PDF file itself is not converted to a format that IIIF can display

## Solution

We've created several tools to solve this problem:

1. `create_multipage_ptif.py` - Creates PTIF files from PDF files
2. `register_ptif.py` - Registers PTIF files with PDF records
3. `simple_pdf_viewer.py` - Generates and applies a complete solution
4. `pdf_viewer_fix.js` - A JavaScript solution that can be included in the theme

## Quick Start

For a single record, run:

```bash
# Create PTIF files from PDFs
source .venv/bin/activate
python create_multipage_ptif.py

# Register PTIF files with a record (default is record ID 216)
python register_ptif.py --record-id 216

# View the record and use the JavaScript in the browser console
# The script will generate instructions for the next steps
```

## How It Works

1. **Creating PTIF Files**: 
   - The `create_multipage_ptif.py` script extracts pages from PDFs and converts them to PTIF format
   - PTIF files are stored in the IIIF directory structure based on record ID

2. **Registering PTIF Files**:
   - The `register_ptif.py` script finds PTIF files for a specific record
   - It creates a manifest JSON file with canvases for each PTIF file
   - It generates JavaScript to inject this manifest into the Mirador viewer

3. **Viewing PDFs**:
   - Visit the record page in the browser
   - Open the developer console and paste the generated JavaScript
   - The script replaces the empty manifest with one containing PTIF canvases

## Permanent Solution

For a permanent solution, include the `pdf_viewer_fix.js` script in your Zenodo RDM theme:

1. Add the file to `site/zenodo_rdm/theme/assets/js/pdf_viewer_fix.js`
2. Update your webpack configuration to include this file
3. The script will automatically detect PDF records and enhance their IIIF manifests

## Customization

You can customize the behavior of the PTIF creation:

- Modify `create_multipage_ptif.py` to control how many pages are processed
- Change the resolution of the PTIF files by modifying the VIPS commands
- Adjust the manifest generation in `register_ptif.py` to change labels or metadata

## Troubleshooting

### No PTIF Files Found

If no PTIF files are found:

1. Check if PDFs were uploaded correctly
2. Verify the file paths in `create_multipage_ptif.py`
3. Run the script with debugging enabled: `python create_multipage_ptif.py --debug`

### PDF Still Shows Gray Screen

If the PDF still shows a gray screen:

1. Check browser console for errors
2. Verify the manifest contains canvases (use `curl https://127.0.0.1:5000/api/iiif/record:216/manifest`)
3. Try clearing browser cache or using incognito mode

### VIPS Errors

If you see VIPS errors:

1. Make sure VIPS is installed: `vips --version`
2. Check the PDF file is valid: `pdfinfo <path_to_pdf>`
3. Try converting a single page manually: `vips pdfload <path_to_pdf>[0] output.ptif`

## References

- [IIIF Image API](https://iiif.io/api/image/2.1/)
- [IIIF Presentation API](https://iiif.io/api/presentation/2.1/)
- [Mirador Viewer](https://projectmirador.org/)
- [VIPS Documentation](https://libvips.github.io/libvips/) 