# IIIF Integration for Zenodo-RDM

This document outlines the implementation and usage of IIIF (International Image Interoperability Framework) integration for Zenodo-RDM.

## Overview

The integration enables viewing high-resolution images through IIIF, allowing users to zoom, pan, and annotate images directly in the browser. This implementation uses:

1. **IIPServer** - A Fast CGI server for serving high-resolution IIIF images
2. **PTIF format** - Pyramid TIFF format for efficient image tiling and multi-resolution access
3. **Mirador** - A configurable, extensible, and easy-to-integrate IIIF viewer

## Components

### IIPServer

IIPServer is deployed as a Docker container and configured to serve IIIF-compliant images. The server looks for images in the `/images/public` directory within the container.

### Image Conversion

Images are converted from standard formats (TIFF, JPG, PNG) to PTIF format using the Kakadu JPEG2000 library's `kdu_compress` tool. The conversion process is handled by:

1. `convert_to_ptif.py` - Converts a single image file to PTIF format
2. `batch_convert.py` - Batch processes all image files within a specific record

## Using the Tools

### Single File Conversion

To convert a single image file to PTIF format:

```bash
python convert_to_ptif.py [input_file_path] [record_id]
```

Example:
```bash
python convert_to_ptif.py data/images/private/202/page-001.tif 202
```

### Batch Conversion

To convert all image files within a record:

```bash
python batch_convert.py [record_id]
```

Example:
```bash
python batch_convert.py 202
```

## File Naming and Storage

- Original image files are stored in `data/images/private/[record_id]/`
- PTIF files must be placed in the IIPServer's accessible location, which is mapped to `/images/public/` in the container
- The naming convention for IIIF URLs is `private_[record_id]_[filename]` (e.g., `private_202_page-001.ptif`)

## IIIF URLs

After conversion, images are accessible through IIIF at the following URLs:

- Metadata: `http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/private_[record_id]_[filename].ptif/info.json`
- Thumbnail: `http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/private_[record_id]_[filename].ptif/full/200,/0/default.jpg`
- Image region: `http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/private_[record_id]_[filename].ptif/0,0,100,100/full/0/default.jpg`

Example for record 202, file page-001.tif:
```
http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/private_202_page-001.ptif/info.json
```

## Troubleshooting

### Common Issues

1. **"File not found" Error from IIPServer**
   - Ensure the PTIF file has been correctly placed in the IIPServer's accessible location
   - Check that the file path matches the URL path exactly

2. **IIIF Manifest Not Accessible**
   - The Zenodo-RDM IIIF manifest endpoint may require specific Accept headers
   - Currently, the manifest endpoint is not fully functional but individual images are accessible

3. **Image Not Displaying in Viewer**
   - Verify the PTIF conversion was successful by checking the file size
   - Try accessing the image directly through the IIPServer URL

## Known Limitations

1. The IIIF manifest endpoint (`/iiif/[record_id]/manifest`) is not currently working properly in Zenodo-RDM
2. External viewers may need to be configured to access individual image files rather than the manifest

## Future Improvements

1. Fix the manifest endpoint to properly serve IIIF manifests
2. Implement automatic PTIF conversion upon file upload
3. Support annotation storage and retrieval
4. Add configuration options for IIIF presentation API 