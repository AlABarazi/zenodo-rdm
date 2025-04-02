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