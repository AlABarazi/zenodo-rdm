# PTIF Conversion Guide for IIIF in Zenodo-RDM

This guide documents the process of implementing PTIF (Pyramid TIFF) image conversion for enabling IIIF functionality in Zenodo-RDM. PTIF files are essential for the IIPServer to serve images via the IIIF protocol.

## The Problem: Missing PTIF Conversion

When deploying Zenodo-RDM locally, we encountered an issue with the IIIF functionality. The IIPServer was running correctly, but it couldn't serve images via the IIIF protocol because:

1. The IIPServer requires PTIF format images
2. There was no worker service to convert uploaded images to PTIF format
3. The volume mounting was configured correctly, but no PTIF files existed

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  User uploads │     │  ✗ MISSING ✗  │     │  IIPServer    │
│  image files  │────>│  PTIF         │────>│  can't serve  │
│  (.jpg, .png) │     │  Conversion   │     │  IIIF images  │
└───────────────┘     └───────────────┘     └───────────────┘
```

## The Solution: Manual PTIF Conversion

Without modifying the core Zenodo-RDM codebase, we implemented a solution to manually convert images to PTIF format:

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  User uploads │     │ Our converter │     │  IIPServer    │
│  image files  │────>│ script creates│────>│  serves IIIF  │
│  (.jpg, .png) │     │ .ptif files   │     │  images       │
└───────────────┘     └───────────────┘     └───────────────┘
```

## Implementation Steps

### Step 1: Create a Conversion Script

We created a shell script (`convert_images.sh`) that uses the `vips` tool to convert image files to PTIF format:

```bash
#!/bin/bash
# Simple script to convert images to PTIF format for IIPServer
# Requires vips to be installed: apt-get install -y libvips-tools

set -e

# Default image directory
IMAGE_DIR="./data/images"

# Check if vips is installed
if ! command -v vips &> /dev/null; then
    echo "Error: vips is not installed. Please install with 'apt-get install -y libvips-tools' or 'brew install vips'"
    exit 1
fi

# Ensure the directory structure exists
mkdir -p "$IMAGE_DIR/public" "$IMAGE_DIR/private"

# Process all PNG, JPG, and TIF files
echo "Searching for image files in $IMAGE_DIR..."
find "$IMAGE_DIR" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.tif" -o -name "*.tiff" \) | while read img; do
    # Generate output filename with .ptif extension
    ptif_file="${img%.*}.ptif"
    
    # Skip if already converted
    if [ -f "$ptif_file" ]; then
        echo "Skipping already converted: $img"
        continue
    fi
    
    echo "Converting $img to $ptif_file"
    vips tiffsave "$img" "$ptif_file" --tile --pyramid || echo "Failed to convert $img"
done

echo "Conversion complete"
echo "Make sure docker volume mounting is working correctly with:"
echo "  docker-compose exec iipserver ls -la /images/public/"
echo ""
echo "Test a PTIF file with:"
echo "  curl \"http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/path/to/image.ptif/info.json\""
```

### Step 2: Make the Script Executable

```bash
chmod +x convert_images.sh
```

### Step 3: Install Prerequisites

The script requires `vips` to be installed on your local system:

```bash
# On macOS
brew install vips

# On Ubuntu/Debian
sudo apt-get install -y libvips-tools
```

### Step 4: Run the Conversion Script

```bash
./convert_images.sh
```

This will:
1. Find all image files in the `./data/images` directory
2. Convert them to PTIF format with the same basename but `.ptif` extension
3. Skip files that have already been converted

Example output:
```
Searching for image files in ./data/images...
Converting ./data/images/test_image.png to ./data/images/test_image.ptif
Skipping already converted: ./data/images/public/10/0_/_/test_image.png
Conversion complete
```

### Step 5: Copy PTIF Files to the Public Directory

The IIPServer is configured to serve files from the `/images/public` directory, so we need to copy our PTIF files there:

```bash
cp data/images/*.ptif data/images/public/
```

### Step 6: Verify Files in the IIPServer Container

```bash
docker-compose exec iipserver ls -la /images/public/
```

Expected output:
```
total 10888
drwxr-xr-x    4 root     root           128 Apr  3 21:09 .
drwxr-xr-x    4 root     root           128 Apr  3 19:16 ..
drwxr-xr-x    3 root     root            96 Apr  3 19:12 10
-rw-r--r--    1 root     root            20 Apr  3 21:09 test.txt
-rw-r--r--    1 root     root      11142744 Apr  4 23:53 test_image.ptif
```

### Step 7: Test IIIF Functionality

Test accessing the PTIF file via the IIIF protocol:

```bash
curl "http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/test_image.ptif/info.json"
```

Expected output (IIIF image information in JSON format):
```json
{
  "@context" : "http://iiif.io/api/image/3/context.json",
  "protocol" : "http://iiif.io/api/image",
  "width" : 1000,
  "height" : 1000,
  "sizes" : [
     { "width" : 125, "height" : 125 },
     { "width" : 250, "height" : 250 },
     { "width" : 500, "height" : 500 }
  ],
  "tiles" : [
     { "width" : 128, "height" : 128, "scaleFactors" : [ 1, 2, 4, 8 ] }
  ],
  "id" : "http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/test_image.ptif",
  "type": "ImageService3",
  "profile" : "level2"
  // ... more image information ...
}
```

### Step 8: Test Requesting an Image

Test requesting a thumbnail image:

```bash
curl -s "http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/test_image.ptif/full/200,/0/default.jpg" -o test_thumbnail.jpg
```

This will save a 200px wide JPEG thumbnail of the image to `test_thumbnail.jpg`.

## Automated Solution with Docker

For a more automated solution, we can create a custom Docker container that continuously monitors and converts images:

### Step 1: Create a Dockerfile for the Converter

Create `Dockerfile.converter`:

```dockerfile
FROM debian:bullseye-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    libvips-tools \
    python3 \
    python3-pip \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /images/public /images/private

# Copy the watcher script
COPY converter-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/converter-entrypoint.sh

WORKDIR /images
ENTRYPOINT ["/usr/local/bin/converter-entrypoint.sh"]
```

### Step 2: Create an Entrypoint Script

Create `converter-entrypoint.sh`:

```bash
#!/bin/bash
# PTIF Converter entrypoint
# Watches for image files and converts them to PTIF format

set -e

echo "Starting PTIF Converter service"
echo "================================"
echo "This container watches for image files and converts them to PTIF format"
echo "It's a substitute for the Zenodo worker service during development"
echo ""

# Ensure directories exist
mkdir -p /images/public /images/private

# Function to convert image to PTIF
convert_to_ptif() {
    local img="$1"
    local ptif_file="${img%.*}.ptif"
    
    # Skip if already converted
    if [ -f "$ptif_file" ]; then
        echo "$(date): Skipping already converted: $img"
        return 0
    fi
    
    echo "$(date): Converting $img to $ptif_file"
    if vips tiffsave "$img" "$ptif_file" --tile --pyramid; then
        echo "$(date): ✓ Successfully converted $img to $ptif_file"
        return 0
    else
        echo "$(date): ✗ Failed to convert $img"
        return 1
    fi
}

# Initial conversion of existing files
echo "Scanning for existing image files..."
find /images -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.tif" -o -name "*.tiff" \) | while read img; do
    convert_to_ptif "$img"
done

# Main loop to watch for new files
echo "$(date): Watching for new image files..."
while true; do
    # Check public directory
    find /images/public -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.tif" -o -name "*.tiff" \) -not -path "*.ptif" | while read img; do
        if [ ! -f "${img%.*}.ptif" ]; then
            convert_to_ptif "$img"
        fi
    done
    
    # Check private directories (record-specific)
    find /images/private -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.tif" -o -name "*.tiff" \) -not -path "*.ptif" | while read img; do
        if [ ! -f "${img%.*}.ptif" ]; then
            convert_to_ptif "$img"
            
            # For record directories, also create a symlink to public
            # This helps with testing, but in a real system this would
            # respect access controls
            dir=$(dirname "$img")
            record_id=$(basename "$dir")
            mkdir -p "/images/public/$record_id"
            ptif_file="${img%.*}.ptif"
            ln -sf "$ptif_file" "/images/public/$record_id/$(basename "$ptif_file")" 2>/dev/null || true
        fi
    done
    
    # Wait before checking again
    sleep 5
done
```

### Step 3: Make the Entrypoint Script Executable

```bash
chmod +x converter-entrypoint.sh
```

### Step 4: Build the Docker Image

```bash
docker build -f Dockerfile.converter -t ptif-converter .
```

### Step 5: Add the Converter to Docker Compose

Edit `docker-compose.yml` to add:

```yaml
services:
  # ... existing services ...
  
  converter:
    image: ptif-converter
    volumes:
      - ${INSTANCE_PATH:-./data}/images:/images
    restart: always
```

### Step 6: Start the Converter Service

```bash
docker-compose up -d converter
```

The converter service will now:
1. Run continuously in the background
2. Automatically convert any new image files to PTIF format
3. Make the PTIF files available to the IIPServer

## Common Challenges and Solutions

### Challenge 1: Missing PTIF Files

**Problem:** IIPServer returns an error: "file.ptif is neither a file nor part of an image sequence"

**Solution:**
1. Check if the PTIF file exists in the container:
   ```bash
   docker-compose exec iipserver ls -la /images/public/
   ```
2. Run the conversion script if needed:
   ```bash
   ./convert_images.sh
   ```
3. Copy PTIF files to the public directory:
   ```bash
   cp data/images/*.ptif data/images/public/
   ```

### Challenge 2: Missing the vips Tool

**Problem:** Error: "vips command not found"

**Solution:**
```bash
# On macOS
brew install vips

# On Ubuntu/Debian
sudo apt-get install -y libvips-tools
```

### Challenge 3: IIPServer Crashes with C++ Assertion Failures

**Problem:** IIPServer crashes with: "vector::_M_range_check: __n (which is X) >= this->size() (which is Y)"

**Solution:**
1. Restart the IIPServer:
   ```bash
   docker-compose restart iipserver
   ```
2. Try with a different image format or a different source image

### Challenge 4: Issues with Volume Mounting

**Problem:** Files exist on the host but aren't visible in the container

**Solution:**
1. Check volume configuration in docker-compose.yml
2. Check that local directories exist
3. Copy files manually to the container if needed:
   ```bash
   docker-compose cp data/images/test_image.ptif iipserver:/images/public/
   ```

## How PTIF and IIIF Work Together

PTIF (Pyramid TIFF) is a tiled, multi-resolution format that enables efficient access to image data at different resolutions. IIPServer reads these files and serves them via the IIIF protocol, which provides a standardized way to request images or portions of images at specific sizes.

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│  Original     │────>│  PTIF         │────>│  IIPServer    │
│  Image        │     │  Conversion   │     │  IIIF Service │
│  (.jpg, .png) │     │  (.ptif)      │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
                                                   │
                                                   ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│  Web Browser  │<────│  Mirador      │<────│  IIIF Image   │
│  Display      │     │  Viewer       │     │  API Requests │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
```

## IIIF URL Structure

The IIIF Image API uses a standardized URL pattern for requesting images:

```
http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/[image-path]/[region]/[size]/[rotation]/[quality].[format]
```

Examples:
- Full image (as JSON info): 
  ```
  http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/test_image.ptif/info.json
  ```
- 200px wide thumbnail: 
  ```
  http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/test_image.ptif/full/200,/0/default.jpg
  ```
- Region of the image (100,100 with width 200, height 200): 
  ```
  http://localhost:8080/fcgi-bin/iipsrv.fcgi?IIIF=/test_image.ptif/100,100,200,200/full/0/default.jpg
  ```

## Conclusion

By implementing PTIF conversion, we've enabled the IIPServer to serve images via the IIIF protocol, which is essential for viewing images in IIIF-compatible viewers like Mirador.

In a full Zenodo-RDM deployment, this conversion would be handled by the worker service, but our manual solution provides the same functionality for testing and development purposes.

Remember to run the conversion script whenever you add new images, or set up the automated converter service for continuous conversion. 