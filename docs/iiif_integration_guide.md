# IIIF Integration Guide for Zenodo-RDM

This document provides a comprehensive guide to implementing IIIF (International Image Interoperability Framework) functionality in Zenodo-RDM.

## Table of Contents

1. [Introduction](#introduction)
2. [Key Components](#key-components)
3. [Problems & Solutions](#problems--solutions)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Command Reference](#command-reference)
6. [Troubleshooting](#troubleshooting)

## Introduction

IIIF is a set of open standards for delivering high-quality, attributed digital objects online at scale. For Zenodo-RDM, it enables:

- High-resolution image viewing with zoom capabilities
- Image manipulation (rotation, scaling, etc.)
- Interoperability with other IIIF-compatible viewers and tools
- Annotation capabilities

**Architecture Overview:**

```
┌─────────────────┐     ┌───────────────┐     ┌─────────────┐
│                 │     │               │     │             │
│  Zenodo-RDM     │────▶│  IIPServer    │────▶│  Browser    │
│  (Web App)      │     │  (IIIF Server)│     │  (Viewer)   │
│                 │     │               │     │             │
└─────────────────┘     └───────────────┘     └─────────────┘
        │                       ▲
        │                       │
        ▼                       │
┌─────────────────┐     ┌───────────────┐
│                 │     │               │
│  Original       │────▶│  PTIF Images  │
│  Image Files    │     │  (Pyramid TIF)│
│                 │     │               │
└─────────────────┘     └───────────────┘
```

## Key Components

1. **IIPServer**: A Fast CGI server that serves IIIF-compliant images.
2. **PTIF Format**: Pyramid TIFF format that enables efficient delivery of multi-resolution images.
3. **Conversion Tools**: Custom scripts to convert standard image formats to PTIF.
4. **Web Viewers**: JavaScript components that display IIIF images with zoom functionality.

## Problems & Solutions

### Problem 1: Missing PTIF Files

**Problem**: Zenodo-RDM expects image files to be converted to PTIF format for IIIF functionality, but this conversion isn't happening automatically.

**Symptoms**:
- IIIF manifest URLs return 404 errors
- Attempting to view images with zoom functionality fails
- No PTIF files in the IIPServer directory

**Solution**:
- Create conversion tools to transform standard images to PTIF format
- Implement a single-file converter and a batch processor for entire records
- Ensure converted files are placed in the correct location for IIPServer access

### Problem 2: IIPServer Configuration

**Problem**: IIPServer expects files in a specific location with a specific naming convention, but files aren't being placed there.

**Symptoms**:
- Error message: "/images/public/private/202/page-001.ptif is neither a file nor part of an image sequence"
- IIPServer can't find the PTIF files even though they exist

**Solution**:
- Check the IIPServer environment to determine its filesystem prefix
- Adjust file paths to match IIPServer's expected location (typically `/images/public`)
- Implement a naming convention that works with the IIPServer configuration

### Problem 3: IIIF Manifest Access

**Problem**: The IIIF manifest endpoints in Zenodo-RDM are not working correctly.

**Symptoms**:
- IIIF manifest URLs return 406 (Invalid Accept header) or 404 errors
- Viewer can't load manifests even when individual images are accessible

**Solution**:
- Implement direct access to individual IIIF image files
- Create a custom viewer that doesn't rely on the manifest
- Document the correct Accept headers for API calls

## Step-by-Step Implementation

### 1. Setup Testing Environment

First, we need to verify that Zenodo-RDM is running and accessible:

```bash
# Check if the web interface is accessible
curl -k https://127.0.0.1:5000

# Check if a specific record is accessible
curl -k https://127.0.0.1:5000/api/records/202
```

### 2. Create Image Conversion Scripts

We need two main scripts:

1. **Single File Converter**: Converts one image file to PTIF format
2. **Batch Processor**: Processes all images in a record

#### Single File Converter (`convert_to_ptif.py`)

This script:
- Takes an input file path and record ID
- Converts the image to PTIF format using `kdu_compress`
- Copies the result to the IIPServer's accessible location
- Prints IIIF URLs for testing

#### Batch Processor (`batch_convert.py`)

This script:
- Takes a record ID as input
- Fetches all image files from the record
- Downloads and converts each file
- Places converted files in the IIPServer location
- Verifies IIIF access after conversion

### 3. Check IIPServer Configuration

We need to ensure files are placed where IIPServer expects them:

```bash
# Check the IIPServer filesystem prefix
docker-compose exec iipserver env | grep -i filesystem
```

The output revealed that IIPServer is configured to look in `/images/public`.

### 4. Create a Custom IIIF Viewer

To test the IIIF functionality, we created a custom viewer using OpenSeadragon:

- `iiif_viewer.html`: A standalone HTML page for viewing IIIF images
- `serve_viewer.py`: A simple HTTP server to serve the viewer

The viewer allows:
- Loading images by record ID and filename
- Viewing thumbnails for all images in a record
- Examining IIIF metadata for each image

## Command Reference

### Converting a Single Image

```bash
python convert_to_ptif.py data/images/private/202/page-001.tif 202
```

This command:
1. Converts `page-001.tif` to PTIF format
2. Copies the result to the IIPServer
3. Prints IIIF URLs for testing

### Batch Converting All Images in a Record

```bash
python batch_convert.py 202
```

This command:
1. Fetches all images from record 202
2. Downloads and converts each image
3. Places all PTIF files in the IIPServer
4. Verifies IIIF functionality

### Checking IIPServer Files

```bash
docker-compose exec iipserver ls -la /images/
docker-compose exec iipserver ls -la /images/private/202/
```

These commands verify the existence and permissions of files in the IIPServer container.

### Testing IIIF Access

```bash
# Get IIIF metadata
curl "http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/private_202_page-001.ptif/info.json" | jq

# Get a thumbnail
curl "http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/private_202_page-001.ptif/full/200,/0/default.jpg" --output page-001-thumbnail.jpg
```

These commands test direct access to IIIF functionality.

### Launching the Custom Viewer

```bash
python serve_viewer.py
```

This starts a web server at http://localhost:3000/ to serve the custom IIIF viewer.

## Troubleshooting

### Common Errors

1. **"File not found" from IIPServer**
   - **Cause**: IIPServer can't locate the PTIF file
   - **Check**: File path in IIPServer container
   - **Solution**: Ensure file is copied to `/images/public` with the correct name

2. **IIIF Manifest Not Accessible**
   - **Cause**: Zenodo-RDM's IIIF implementation has issues with manifests
   - **Check**: Try different Accept headers
   - **Solution**: Use direct IIIF image access instead of manifests

3. **PTIF Conversion Fails**
   - **Cause**: Missing kdu_compress or bad input file
   - **Check**: kdu_compress installation and input file format
   - **Solution**: Ensure kdu_compress is installed and input is a valid image

4. **Connection Refused to IIPServer**
   - **Cause**: IIPServer not running or port mapping issue
   - **Check**: Docker containers and port mappings
   - **Solution**: Ensure IIPServer container is running and port 8080 is mapped

### Tips for Successful Implementation

1. Always verify PTIF conversion success by checking file size
2. Test IIIF functionality with direct URLs before integrating with viewers
3. Use hardcoded values initially to isolate potential issues
4. Implement proper error handling in conversion scripts 