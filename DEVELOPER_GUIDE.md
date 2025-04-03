# Zenodo RDM Developer Guide

This guide explains the process of adapting the CERN Zenodo RDM application for local development environments. It covers the key modifications made, why they were necessary, and how to further adapt the application for your needs.

## Understanding the Project Architecture

Zenodo RDM is built on the InvenioRDM framework, a modern repository platform for managing and publishing research data. Here's a high-level overview of the architecture:

```
┌───────────────────────────────────────────┐
│              Web Browser                  │
└───────────────┬───────────────────────────┘
                │
┌───────────────▼───────────────────────────┐
│           Nginx (Frontend)                │
└─┬─────────────────────────┬───────────────┘
  │                         │
┌─▼──────────────┐  ┌───────▼──────────┐
│    Web UI      │  │      API         │
└─┬──────────────┘  └───────┬──────────┘
  │                         │
┌─▼─────────────────────────▼──────────────┐
│        InvenioRDM Framework               │
└─┬─────────────┬──────────┬───────────────┘
  │             │          │
┌─▼───────┐  ┌──▼────┐  ┌──▼──────┐  ┌──────────┐
│PostgreSQL│  │Redis  │  │RabbitMQ │  │OpenSearch│
└─────────┘  └───────┘  └─────────┘  └──────────┘
```

## Key Modifications for Local Development

### 1. Docker Images & Registry Changes

**Problem:** The original Zenodo RDM project uses CERN's private Docker registry which is not accessible for local development.

**Solution:** Replace all Docker image references to use publicly available images from Docker Hub.

#### Before:
```yaml
# Original docker-services.yml
services:
  cache:
    image: registry.cern.ch/docker.io/library/redis
    # ...
  db:
    image: registry.cern.ch/docker.io/library/postgres:12.4
    # ...
```

#### After:
```yaml
# Modified docker-services.yml
services:
  cache:
    image: redis:latest
    # ...
  db:
    image: postgres:12.4
    # ...
```

### 2. Dockerfile Simplification

**Problem:** The original Dockerfile contains CERN-specific dependencies and configurations.

**Solution:** Simplify the Dockerfile to use a standard Alpine Linux base image and only include essential dependencies.

#### Before:
```dockerfile
FROM registry.cern.ch/inveniosoftware/almalinux:1

# XRootD
ARG xrootd_version="5.5.5"
# Repo required to find all the releases of XRootD
RUN dnf config-manager --add-repo https://cern.ch/xrootd/xrootd.repo
RUN if [ ! -z "$xrootd_version" ] ; then XROOTD_V="-$xrootd_version" ; else XROOTD_V="" ; fi && \
    echo "Will install xrootd version: $XROOTD_V (latest if empty)" && \
    dnf install -y xrootd"$XROOTD_V" python3-xrootd"$XROOTD_V"
# ...
```

#### After:
```dockerfile
FROM python:3.9-alpine

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    libxml2-dev \
    libxslt-dev \
    jpeg-dev \
    git \
    curl \
    nodejs \
    npm \
    bash
    
# Install additional dependencies
RUN pip install pipenv
# ...
```

### 3. HTTP vs HTTPS for Local Development

**Problem:** The original application forces HTTPS, which requires certificates that are difficult to set up locally.

**Solution:** Modify the security settings to allow HTTP for local development.

#### Before:
```python
# invenio.cfg
APP_DEFAULT_SECURE_HEADERS = {
    # ...
    "force_https": True,
    "session_cookie_secure": True,
    "strict_transport_security": True,
    # ...
}
```

#### After:
```python
# invenio.cfg
APP_DEFAULT_SECURE_HEADERS = {
    # ...
    "force_https": False,  # Changed to False for local development
    "session_cookie_secure": False,  # Changed to False for local development
    "strict_transport_security": False,  # Changed to False for local development
    # ...
}
```

### 4. Service URLs and Endpoints

**Problem:** All services were configured to use HTTPS URLs.

**Solution:** Update service URLs to use HTTP and appropriate ports for local access.

#### Before:
```python
# Environment variables in docker-services.yml
- "INVENIO_SITE_UI_URL=https://127.0.0.1"
- "INVENIO_SITE_API_URL=https://127.0.0.1/api"
```

#### After:
```python
# Environment variables in docker-services.yml
- "INVENIO_SITE_UI_URL=http://127.0.0.1:5000"
- "INVENIO_SITE_API_URL=http://127.0.0.1:5000/api"
```

### 5. Port Exposure and Mapping

**Problem:** Docker Compose files didn't expose all necessary ports for local development.

**Solution:** Expose all required service ports with appropriate host mappings.

#### Before:
```yaml
# Original docker-compose.yml with minimal port exposure
services:
  db:
    extends:
      file: docker-services.yml
      service: db
  # No explicit port mapping
```

#### After:
```yaml
# Modified docker-compose.yml with explicit port mappings
services:
  db:
    extends:
      file: docker-services.yml
      service: db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 6. Missing Dependencies

**Problem:** The application had missing dependencies when running locally.

**Solution:** Add required dependencies like `greenlet` to the Pipfile.

#### Before:
```
# Original Pipfile missing some dependencies
[packages]
# ... existing dependencies
```

#### After:
```
# Updated Pipfile with additional dependencies
[packages]
# ... existing dependencies
greenlet = ">=1.0.0"  # Required by SQLAlchemy with asyncio support
```

## Step-by-Step Project Modification Walkthrough

### Step 1: Examining the Original Configuration

First, we analyzed all configuration files to understand dependencies and service relationships:

1. **Dockerfile**: Contains build instructions and dependencies
2. **docker-services.yml**: Defines service configurations
3. **docker-compose.yml**: Orchestrates services together
4. **.invenio**: Contains project configuration
5. **invenio.cfg**: Application configuration settings

### Step 2: Identifying CERN-Specific Components

We identified all CERN-specific components that would need modification:

- Docker registry references
- XRootD dependencies
- Kerberos authentication
- HTTPS requirements
- Authentication providers

### Step 3: Creating Local Configuration Alternatives

For each identified component, we created local alternatives:

1. **Docker Images**: Replaced with public Docker Hub equivalents
2. **Authentication**: Simplified to use local authentication
3. **Protocol**: Changed from HTTPS to HTTP
4. **Dependencies**: Used Alpine-compatible packages

### Step 4: Updating Port Mappings

Ensured all services had proper port mappings for local access:

```yaml
services:
  cache:
    ports:
      - "6379:6379"
  db:
    ports:
      - "5432:5432"
  mq:
    ports:
      - "15672:15672"
      - "5672:5672"
  search:
    ports:
      - "9200:9200"
      - "9300:9300"
```

### Step 5: Creating Local Environment File

Added a `.env` file to set local paths:

```
INSTANCE_PATH=./data
```

### Step 6: Updating Documentation

Updated README.md and created detailed installation guides.

## Common Development Tasks

### Adding a New Dependency

When you need to add a new Python dependency:

```bash
# Add to Pipfile with pipenv
pipenv install package-name

# Update the lock file
pipenv lock

# Reinstall dependencies
invenio-cli install
```

### Modifying Configuration

To change application configuration:

1. Edit `local.cfg` with your changes
2. Restart the services:
   ```bash
   invenio-cli run
   ```

### Accessing Service Logs

To see logs for debugging:

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs -f db
```

### Accessing Database

Connect to PostgreSQL database:

```bash
docker-compose exec db psql -U zenodo -d zenodo
```

### Rebuilding After Changes

After modifying Docker-related files:

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Common Git and GitHub Issues

When working with this repository, you may encounter several Git and GitHub issues. Here are solutions to the most common problems:

### Branch Naming Issues

**Problem:** Git error "src refspec main does not match any" when trying to push.

**Cause:** This happens when you try to push to a branch (like `main`) that doesn't exist locally. The repository may be using `master` as the default branch name.

**Solution:**

1. Check your current branch:
   ```bash
   git branch
   ```

2. Either push to the correct branch name:
   ```bash
   # If your local branch is 'master'
   git push -u origin master
   ```

3. Or rename your branch to match the expected name:
   ```bash
   # Rename from 'master' to 'main'
   git branch -m master main
   git push -u origin main
   ```

### Large File Issues

**Problem:** HTTP 400 errors or "remote: error: File X is Y MB; this exceeds GitHub's file size limit of 100 MB" when pushing.

**Cause:** GitHub has a hard limit of 100MB per file and will reject pushes containing larger files.

**Solution:**

1. Identify large files:
   ```bash
   find . -type f -size +50M
   ```

2. Add these files to your `.gitignore`:
   ```bash
   echo "path/to/large/file" >> .gitignore
   ```

3. Remove them from Git tracking (if they're already tracked):
   ```bash
   git rm --cached path/to/large/file
   ```

4. Commit the change:
   ```bash
   git commit -m "Remove large files from tracking"
   ```

### Virtual Environment Issues

**Problem:** Repository size becomes too large when `.venv` directory is included.

**Cause:** Virtual environments contain compiled binaries and numerous dependencies that shouldn't be in Git.

**Solution:**

1. Always include `.venv/` in your `.gitignore`:
   ```bash
   echo ".venv/" >> .gitignore
   ```

2. If already committed, remove it from tracking:
   ```bash
   git rm -r --cached .venv/
   git commit -m "Remove virtual environment from Git tracking"
   ```

### HTTPS vs SSH Authentication

If you encounter authentication issues when pushing to GitHub:

```bash
# Change to SSH authentication (more reliable than HTTPS)
git remote set-url origin git@github.com:username/repository.git

# Verify the change
git remote -v
```

### Important Files to Exclude from Git

For Zenodo RDM specifically, these files/directories should never be committed:

```
# Virtual environments
.venv/
env/
venv/

# Generated files
__pycache__/
*.pyc
node_modules/

# User data
data/
instance/

# Generated assets
static/
app_data/static/
app_data/images/
app_data/files/
```

Ensure your `.gitignore` file contains these entries to prevent repository bloat and GitHub errors.

## Understanding the Dependency Stack

Zenodo RDM has a complex dependency stack:

```
┌───────────────────────────┐
│     Zenodo RDM            │
└───────────┬───────────────┘
            │
┌───────────▼───────────────┐
│     InvenioRDM             │
└───────────┬───────────────┘
            │
┌───────────▼───────────────┐
│     Invenio Framework      │
└───────────┬───────────────┘
            │
┌───────────▼───────────────┐
│     Flask                  │
└───────────────────────────┘
```

## Conclusion

By making these modifications, we've transformed a CERN-specific application into one that can be run locally on standard development environments. The main changes focused on:

1. Using publicly accessible Docker images
2. Simplifying authentication and security
3. Exposing services for local access
4. Adding missing dependencies
5. Creating documentation for local development

These modifications maintain the core functionality while making the application accessible to a wider audience of developers.

# Developer Guide: Integrating PDFs with IIIF in Zenodo RDM

This guide explains how to make PDF files viewable in the IIIF-based Mirador viewer within Zenodo RDM. It covers the entire process from understanding the problem to implementing and testing the solution.

## Table of Contents

1. [Understanding the Problem](#understanding-the-problem)
2. [Solution Overview](#solution-overview)
3. [Step 1: Creating PTIF Files from PDFs](#step-1-creating-ptif-files-from-pdfs)
4. [Step 2: Registering PTIF Files with Records](#step-2-registering-ptif-files-with-records)
5. [Step 3: Enhancing IIIF Manifests](#step-3-enhancing-iiif-manifests)
6. [Step 4: Client-Side Integration](#step-4-client-side-integration)
7. [Common Challenges and Solutions](#common-challenges-and-solutions)
8. [Debugging and Troubleshooting](#debugging-and-troubleshooting)
9. [Full Implementation Example](#full-implementation-example)
10. [Frequently Asked Questions](#frequently-asked-questions)

## Understanding the Problem

### What is IIIF?

The International Image Interoperability Framework (IIIF) is a set of standards for delivering images over the web. It enables rich zoom, pan, and annotation features through viewers like Mirador.

```
     ┌───────────────────────────────────┐
     │                                   │
     │          IIIF Standard            │
     │                                   │
     └───────────┬───────────────┬───────┘
                 │               │
        ┌────────▼────────┐     │     ┌────────────────────┐
        │                 │     │     │                    │
        │  Image API      │     │     │  Presentation API  │
        │                 │     │     │                    │
        └────────┬────────┘     │     └─────────┬──────────┘
                 │              │               │
                 │     ┌────────▼─────────┐     │
                 │     │                  │     │
                 └─────►    IIIF Server   ◄─────┘
                       │                  │
                       └────────┬─────────┘
                                │
                       ┌────────▼─────────┐
                       │                  │
                       │  Mirador Viewer  │
                       │                  │
                       └──────────────────┘
```

### What is Mirador?

Mirador is a multi-window image viewing platform that implements the IIIF standards, allowing users to:
- View high-resolution images
- Compare images side by side
- Annotate images
- Share views with others

### The PDF Viewing Problem

When a PDF is uploaded to Zenodo RDM, the system attempts to display it using the Mirador viewer, but fails with a gray screen because:

1. **Missing Canvases**: The IIIF manifest for PDF records doesn't contain any canvases (the essential elements needed for displaying images)
2. **Format Incompatibility**: PDFs need to be converted to an IIIF-compatible format
3. **Disconnected Components**: The connection between PDF files and their image representations is missing

Here's what users see:

```
┌───────────────────── Zenodo RDM UI ─────────────────────┐
│                                                         │
│  ┌───────────── Record View ─────────────────┐          │
│  │                                           │          │
│  │  Title: Sample Document                   │          │
│  │  Authors: John Smith                      │          │
│  │                                           │          │
│  │  ┌─────────── Mirador Viewer ──────────┐  │          │
│  │  │                                     │  │          │
│  │  │  ┌─────────────────────────────┐   │  │        │
│  │  │  │                             │   │  │        │
│  │  │  │                             │   │  │        │
│  │  │  │         PDF Page            │   │  │        │
│  │  │  │     Displayed as Image      │   │  │        │
│  │  │  │                             │   │  │        │
│  │  │  │                             │   │  │        │
│  │  │  └─────────────────────────────┘   │  │        │
│  │  │                                     │  │        │
│  │  │            ◀ Page 1/20 ▶            │  │        │
│  │  │                                     │  │        │
│  │  └─────────────────────────────────────┘  │        │
│  │                                           │        │
│  └───────────────────────────────────────────┘        │
│                                                       │
└─────────────────────────────────────────────────────────┘
```

### Comparison: PDF vs PTIF Formats

| Feature | PDF | PTIF (Pyramid TIFF) |
|---------|-----|---------------------|
| **Structure** | Page-based document format | Multi-resolution tiled image format |
| **IIIF Compatibility** | Not directly compatible | Fully compatible |
| **Tiling Support** | No built-in tiling | Pre-tiled for efficient viewing |
| **Zoom Levels** | Requires rasterization | Multiple resolutions built-in |
| **Annotation Support** | Limited in IIIF | Full support in IIIF |
| **Server Requirements** | PDF.js or similar | Standard IIIF image server |
| **File Size** | Varies | Larger than source |
| **Creation Complexity** | N/A (source format) | Requires conversion |

## Solution Overview

Our solution involves four key components:

1. **PTIF Conversion**: Convert PDF pages to Pyramid TIFF (PTIF) format, which IIIF can work with
2. **PTIF Registration**: Link PTIF files to their respective records
3. **Manifest Enhancement**: Add canvases to IIIF manifests that reference the PTIF files
4. **Client Integration**: Implement JavaScript that enhances the viewer at runtime

Here's the workflow diagram:

```
┌─────────┐    ┌─────────┐    ┌─────────────┐    ┌───────────────┐
│  PDF    │    │  PDF    │    │    PTIF     │    │ PTIF Files    │
│ Upload  ├───►│ Storage ├───►│ Conversion  ├───►│ Registration  │
└─────────┘    └─────────┘    └─────────────┘    └───────┬───────┘
                                                         │
┌─────────┐    ┌─────────────┐    ┌────────────┐         │
│ Display │    │  Manifest   │    │ User Views │         │
│   in    │◄───┤ Enhancement │◄───┤   Record   │◄────────┘
│ Mirador │    │             │    │            │
└─────────┘    └─────────────┘    └────────────┘
```

## Step 1: Creating PTIF Files from PDFs

### What is a PTIF File?

A Pyramid TIFF (PTIF) is a multi-resolution tiled TIFF image format that allows efficient access to portions of an image at different zoom levels. It's ideal for IIIF because:

- It's pre-tiled for efficient delivery
- It contains multiple resolutions for zooming
- It can be served through the IIIF Image API

```
┌─────────────────── PTIF Structure ───────────────────┐
│                                                      │
│  ┌─────────┐                                         │
│  │ Level 0 │ Full Resolution                         │
│  └─────────┘                                         │
│                                                      │
│  ┌─────┐                                             │
│  │ L1  │ 1/2 Resolution                              │
│  └─────┘                                             │
│                                                      │
│  ┌───┐                                               │
│  │L2 │ 1/4 Resolution                                │
│  └───┘                                               │
│                                                      │
│  ┌─┐                                                 │
│  │L3│ 1/8 Resolution                                 │
│  └─┘                                                 │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Creating PTIF Files

We use the `vips` library to convert PDF pages to PTIF format:

```python
# Example command:
vips pdfload input.pdf[0] output.ptif
```

This loads page 0 of the PDF and saves it as a PTIF file.

### Implementation: `create_multipage_ptif.py`

This script:
1. Finds PDF files in records
2. Extracts pages from the PDFs
3. Converts each page to PTIF format
4. Saves the PTIF files in the IIIF directory structure

Key components:

```python
# Core PTIF conversion function
def create_ptif_from_pdf_page(pdf_path, page_num, output_path):
    """Create a PTIF file from a specific PDF page."""
    cmd = [
        "vips", "pdfload", 
        f"{pdf_path}[{page_num}]",  # Specify page number
        output_path,  # Output PTIF file
        "--dpi=300"   # Set resolution
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"Created PTIF: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating PTIF: {e}")
        return False
```

### PTIF Directory Structure

PTIF files are stored in a specific directory structure based on the record ID:

```
.venv/var/instance/images/public/
  └── 21/
      └── 6_/_/         # For record ID 216
          └── filename.pdf.ptif
```

## Step 2: Registering PTIF Files with Records

After creating PTIF files, we need to associate them with the corresponding records.

### Implementation: `register_ptif.py`

This script:
1. Searches for PTIF files that match a record ID
2. Gets dimensions and other metadata for each PTIF file
3. Creates a mapping between records and their PTIF files

Key functions:

```python
def find_ptif_files(record_id):
    """Find PTIF files for a specific record ID."""
    ptif_files = []
    
    # Check common directory patterns
    record_prefix = record_id[:2]
    record_suffix = record_id[2:] + "_/_"
    
    # Path pattern like: images/public/21/6_/_/*.ptif
    pattern = os.path.join(IIIF_DIR, record_prefix, record_suffix, "*.ptif")
    ptif_files.extend(glob.glob(pattern))
    
    return ptif_files
```

## Step 3: Enhancing IIIF Manifests

IIIF uses JSON manifests to describe the structure and content of digital objects. We need to enhance these manifests to include our PTIF files.

### IIIF Manifest Structure

A simplified IIIF manifest looks like this:

```
┌─────────────────── IIIF Manifest Structure ─────────────────────┐
│                                                                 │
│  {                                                              │
│    "@context": "http://iiif.io/api/presentation/2/context.json",│
│    "@type": "sc:Manifest",                                      │
│    "@id": "https://example.org/iiif/record:123/manifest",       │
│    "label": "PDF Document",                                     │
│                                                                 │
│    "sequences": [                  ┌─────────────────┐          │
│      {                             │    Sequence     │          │
│        "canvases": [               └────────┬────────┘          │
│          {                                  │                   │
│            "@id": ".../canvas/1",  ┌────────▼───────┐           │
│            "width": 1000,          │     Canvas     │           │
│            "height": 1500,         └────────┬───────┘           │
│            "images": [                      │                   │
│              {                     ┌────────▼───────┐           │
│                "resource": {       │      Image     │           │
│                  "@id": ".../1",   └────────┬───────┘           │
│                  "service": {               │                   │
│                    "@id": ".."    ┌─────────▼──────┐            │
│                  }                │     Service    │            │
│                }                  └────────────────┘            │
│              }                                                  │
│            ]                                                    │
│          }                                                      │
│        ]                                                        │
│      }                                                          │
│    ]                                                            │
│  }                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

The key parts are:
- **Canvases**: Represent the pages or images
- **Images**: The actual image data displayed on canvases
- **Service**: Specifies where to get the image data from

### Creating Enhanced Manifests

Our `create_manifest` function builds a proper IIIF manifest with canvases for each PTIF file:

```python
def create_manifest(record_id, ptif_files):
    """Create a IIIF manifest with the PTIF files."""
    manifest = {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@type": "sc:Manifest",
        "@id": f"https://127.0.0.1:5000/api/iiif/record:{record_id}/manifest",
        "label": "PDF Document",
        "sequences": [{
            "canvases": []
        }]
    }
    
    # Add a canvas for each PTIF file
    for ptif_path in ptif_files:
        filename = os.path.basename(ptif_path)
        # Create canvas with image data
        canvas = {
            "@id": f"../canvas/{filename}",
            "width": width,
            "height": height,
            "images": [{
                "resource": {
                    "@id": f"/api/iiif/path/to/ptif/full/full/0/default.jpg"
                }
            }]
        }
        manifest["sequences"][0]["canvases"].append(canvas)
    
    return manifest
```

## Step 4: Client-Side Integration

The final step is to integrate our solution into the Zenodo RDM interface. We do this with JavaScript that:

1. Detects when a PDF is being viewed
2. Fetches or constructs an enhanced manifest
3. Injects it into the Mirador viewer

### Implementation: `pdf_viewer_fix.js`

```javascript
// Core function to fix PDF viewing
async function fixPDFViewer() {
    // 1. Detect if we're on a PDF record page
    if (!isPDFRecordPage()) return;
    
    // 2. Get the record ID from the URL
    const recordId = extractRecordID(window.location.href);
    
    // 3. Fetch information about PTIF files
    const ptifInfo = await fetchPTIFInfo(recordId);
    
    // 4. Fetch the original manifest
    const originalManifest = await fetchManifest();
    
    // 5. Enhance the manifest with PTIF canvases
    const enhancedManifest = enhanceManifestWithPTIF(originalManifest, ptifInfo);
    
    // 6. Override fetch for the manifest URL to return our enhanced version
    overrideManifestFetch(enhancedManifest);
    
    // 7. Trigger reload of the viewer
    reloadMiradorViewer();
}
```

```
┌─────────────────── Client-Side Integration Flow ───────────────────┐
│                                                                    │
│  ┌──────────────┐     ┌───────────────┐     ┌────────────────┐     │
│  │  Detect PDF  │     │ Get Record ID │     │  Fetch PTIF    │     │
│  │  Record Page ├────►│ from URL      ├────►│  Information   │     │
│  └──────────────┘     └───────────────┘     └────────┬───────┘     │
│                                                      │              │
│  ┌──────────────┐     ┌───────────────┐     ┌────────▼───────┐     │
│  │   Reload     │     │    Override   │     │    Enhance     │     │
│  │   Mirador    │◄────┤    Fetch      │◄────┤    Manifest    │     │
│  └──────────────┘     └───────────────┘     └────────────────┘     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Common Challenges and Solutions

### Challenge 1: Missing VIPS Library

**Problem**: The VIPS library is required for PDF to PTIF conversion.

**Error message**:
```
Command '['vips', 'pdfload', ...]' returned non-zero exit status 127
```

**Solution**:
1. Install VIPS:
   ```bash
   # macOS
   brew install vips

   # Ubuntu/Debian
   apt-get install libvips-tools
   ```

2. Verify installation:
   ```bash
   vips --version
   ```

### Challenge 2: File Path Issues

**Problem**: Incorrect paths to PDF files in the storage system.

**Error message**:
```
FileNotFoundError: [Errno 2] No such file or directory: '/path/to/file.pdf'
```

**Solution**:
1. Use the Invenio API to get the correct file paths:
   ```python
   def get_pdf_file_path(record_id):
       """Get the correct file path for a PDF in a record."""
       with current_app.app_context():
           # Get the record
           record = RDMRecord.get_record(record_id)
           # Get the files bucket
           bucket_id = record.files.bucket_id
           bucket = Bucket.get(bucket_id)
           # Find PDF files
           for obj in ObjectVersion.get_by_bucket(bucket):
               if obj.key.endswith('.pdf'):
                   return obj.file.uri
   ```

### Challenge 3: Empty IIIF Manifests

**Problem**: IIIF manifests for PDF records don't contain any canvases.

**Error message**:
None, but the manifest lacks canvases:
```json
{
  "sequences": [
    {
      "canvases": []
    }
  ]
}
```

**Solution**:
Use client-side JavaScript to enhance the manifest:
```javascript
// Override fetch for manifest URLs
const originalFetch = window.fetch;
window.fetch = function(url, options) {
  if (url.includes('/api/iiif/record:')) {
    return Promise.resolve({
      json: () => Promise.resolve(enhancedManifest)
    });
  }
  return originalFetch(url, options);
};
```

### Challenge 4: Invenio Extension Errors

**Problem**: Errors when creating custom Invenio extensions.

**Error message**:
```
ModuleNotFoundError: No module named 'invenio_iiif'
```

**Solution**:
Instead of creating a full extension, use a simpler client-side approach:
1. Add JavaScript to the theme
2. Handle manifest enhancement in the browser
3. Avoid server-side changes that require complex extensions

## Debugging and Troubleshooting

### Troubleshooting Flowchart

```
┌─────────────────────────┐
│ PDF not showing in IIIF │
└───────────┬─────────────┘
            │
            ▼
┌───────────────────────┐    No    ┌───────────────────────┐
│ Is VIPS installed?    ├─────────►│ Install VIPS          │
└───────────┬───────────┘          └───────────────────────┘
            │ Yes
            ▼
┌───────────────────────┐    No    ┌───────────────────────┐
│ Can PDFs be found?    ├─────────►│ Fix file paths        │
└───────────┬───────────┘          └───────────────────────┘
            │ Yes
            ▼
┌───────────────────────┐    No    ┌───────────────────────┐
│ Are PTIF files        ├─────────►│ Create PTIF files     │
│ created?              │          └───────────────────────┘
└───────────┬───────────┘
            │ Yes
            ▼
┌───────────────────────┐    No    ┌───────────────────────┐
│ Does manifest have    ├─────────►│ Enhance manifest      │
│ canvases?             │          └───────────────────────┘
└───────────┬───────────┘
            │ Yes
            ▼
┌───────────────────────┐    No    ┌───────────────────────┐
│ Is JavaScript         ├─────────►│ Fix JavaScript        │
│ loading?              │          └───────────────────────┘
└───────────┬───────────┘
            │ Yes
            ▼
┌───────────────────────┐
│ PDF should now show   │
└───────────────────────┘
```

### Checking IIIF Configuration

```bash
# View the IIIF manifest for a record
curl -k https://127.0.0.1:5000/api/iiif/record:216/manifest
```

### Inspecting PTIF Files

```bash
# Check if PTIF exists
ls -la .venv/var/instance/images/public/21/6_/_/

# Get PTIF dimensions
vips header -f width file.ptif
vips header -f height file.ptif
```

### Validating Manifests

Use the [IIIF Validator](https://iiif.io/api/presentation/validator/) to check your manifests.

### Browser Developer Tools

1. Open the browser developer console (F12)
2. Look for errors related to IIIF or Mirador
3. Check network requests for manifest fetching

## Full Implementation Example

Here's a complete implementation example that ties everything together:

### 1. Set up the environment

```bash
# Activate the virtual environment
source .venv/bin/activate

# Make sure VIPS is installed
vips --version
```

### 2. Create PTIF files from PDFs

```bash
# Run the script to create PTIF files
python create_multipage_ptif.py
```

### 3. Register PTIF files with records

```bash
# Register PTIF files for record 216
python register_ptif.py --record-id 216
```

### 4. View the enhanced manifest

```bash
# Open the record in the browser
# Visit: https://127.0.0.1:5000/records/216
```

### 5. Apply the JavaScript fix

```javascript
// In the browser console, paste the contents of inject_manifest.js
```

The PDF should now display properly in the Mirador viewer:

```
┌─────────────────── Zenodo RDM UI ─────────────────────┐
│                                                       │
│  ┌───────────── Record View ─────────────────┐        │
│  │                                           │        │
│  │  Title: Sample Document                   │        │
│  │  Authors: John Smith                      │        │
│  │                                           │        │
│  │  ┌─────────── Mirador Viewer ──────────┐  │        │
│  │  │                                     │  │        │
│  │  │  ┌─────────────────────────────┐   │  │        │
│  │  │  │                             │   │  │        │
│  │  │  │                             │   │  │        │
│  │  │  │         PDF Page            │   │  │        │
│  │  │  │     Displayed as Image      │   │  │        │
│  │  │  │                             │   │  │        │
│  │  │  │                             │   │  │        │
│  │  │  └─────────────────────────────┘   │  │        │
│  │  │                                     │  │        │
│  │  │            ◀ Page 1/20 ▶            │  │        │
│  │  │                                     │  │        │
│  │  └─────────────────────────────────────┘  │        │
│  │                                           │        │
│  └───────────────────────────────────────────┘        │
│                                                       │
└───────────────────────────────────────────────────────┘
```

## Conclusion

You now understand how to make PDFs viewable in the IIIF-based Mirador viewer in Zenodo RDM. The solution involves:

1. Converting PDFs to PTIF format
2. Registering PTIF files with records
3. Enhancing IIIF manifests with canvases for the PTIF files
4. Implementing client-side JavaScript to integrate everything

By following this guide, you can ensure that PDFs are properly displayed, enhancing the user experience of your Zenodo RDM instance.

Remember to test thoroughly, as the exact file paths and record IDs will depend on your specific installation and data.

## Frequently Asked Questions

### General Questions

**Q: Why not just use PDF.js to display PDFs?**  
A: While PDF.js is excellent for standard PDF viewing, using IIIF and Mirador provides additional benefits like consistent UI, annotations, comparison of multiple documents, and zooming capabilities.

**Q: How much disk space do PTIF files require?**  
A: PTIF files are typically larger than the original PDF pages because they contain multiple resolution levels. Expect 2-5x the size of a rasterized PDF page.

**Q: Is this solution compatible with all Zenodo RDM versions?**  
A: This solution has been tested with recent versions of Zenodo RDM. The core concepts should work across versions, but specific implementation details may need adjustment.

### Technical Questions

**Q: Can I convert multiple pages from a PDF?**  
A: Yes, the `create_multipage_ptif.py` script can process multiple pages. You can adjust the `MAX_PAGES` variable to control how many pages are converted.

**Q: How do I add this to my production environment?**  
A: For production, we recommend:
1. Running the PTIF conversion as a background task when PDFs are uploaded
2. Including the JavaScript fix in your theme
3. Adding proper error handling and logging

**Q: Can I modify the PTIF resolution?**  
A: Yes, adjust the `--dpi` parameter in the VIPS command to change the resolution:
```python
cmd = ["vips", "pdfload", f"{pdf_path}[{page_num}]", output_path, "--dpi=600"]
```

**Q: What if my PDFs have hundreds of pages?**  
A: For very large PDFs, consider:
1. Only converting the first few pages (most users only view the beginning)
2. Implementing a lazy-loading strategy where pages are converted on demand
3. Using a queuing system for background processing

### Troubleshooting Questions

**Q: Why do I get "Output file format not recognized" errors?**  
A: This typically means VIPS doesn't recognize the output file extension. Make sure your output path ends with `.ptif` and VIPS supports this format.

**Q: The manifest shows canvases but the images don't load, why?**  
A: Check that:
1. The PTIF file paths in the manifest are correct
2. The IIIF server can access those files
3. The service URL is correct for your instance

**Q: How can I debug the JavaScript integration?**  
A: Add console.log statements to track the process:
```javascript
console.log('Manifest before:', originalManifest);
console.log('Enhanced manifest:', enhancedManifest);
console.log('PTIF info:', ptifInfo);
``` 

## Security Considerations and Best Practices

### Security Considerations

When implementing PDF viewing with IIIF, keep these security considerations in mind:

1. **Input Validation**: Always validate and sanitize file inputs:
   - Check that PDFs are valid before processing
   - Limit the maximum file size
   - Scan for malware before processing

2. **File Path Security**:
   - Never use user-supplied paths directly in commands
   - Use path sanitization to prevent path traversal attacks
   - Avoid exposing internal filesystem paths in URLs

3. **Command Execution**:
   - Never use shell=True with subprocess
   - Validate all command parameters
   - Use absolute paths to executables when possible

4. **API Security**:
   - Ensure IIIF endpoints require proper authentication
   - Implement rate limiting to prevent DDoS attacks
   - Log access to sensitive resources

### Best Practices

Follow these best practices for a robust implementation:

1. **Performance Optimization**:
   - Process PDFs asynchronously with a task queue
   - Implement caching for IIIF manifests
   - Consider CDN deployment for PTIF files

2. **Monitoring and Maintenance**:
   - Log PTIF creation errors for troubleshooting
   - Monitor disk usage as PTIF files grow
   - Implement cleanup for unused PTIF files

3. **User Experience**:
   - Show loading indicators during PTIF generation
   - Provide fallback options if PTIF generation fails
   - Include clear error messages for users

4. **Deployment**:
   - Use a separate service for CPU-intensive PTIF conversion
   - Implement health checks for the IIIF service
   - Create automated tests for the PDF viewing pipeline

5. **Documentation**:
   - Document the PTIF conversion process for operators
   - Provide troubleshooting guides
   - Include API documentation for developers

By addressing these security considerations and following best practices, your implementation will be more secure, maintainable, and user-friendly.