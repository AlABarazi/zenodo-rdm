<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://about.zenodo.org/static/img/logos/zenodo-white-border.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://about.zenodo.org/static/img/logos/zenodo-black-border.svg">
    <img alt="Zenodo logo" src="https://about.zenodo.org/static/img/logos/zenodo-white-border.svg" width="500">
  </picture>
</div>

# Zenodo RDM - Local Installation

**This repository is a modified version of the [original CERN Zenodo RDM repository](https://github.com/zenodo/zenodo-rdm) adapted to work on local development environments.**

Zenodo RDM is an Open Science Repository platform built on the [InvenioRDM framework](https://inveniosoftware.org/products/rdm/). The original project is developed for deployment on CERN's infrastructure, but this modified version allows any developer to run it locally.

## Key Features

- Research data management (RDM) platform
- Digital Object Identifier (DOI) assignment
- Versioning of publications
- Powerful search capabilities
- Community collections
- Integration with GitHub

## What's Changed in This Fork?

This repository has been modified to be easily installable on local environments by:

1. Replacing CERN-specific Docker registry references with standard Docker Hub images
2. Simplifying authentication requirements
3. Disabling HTTPS enforcement for local development
4. Adding missing dependencies
5. Providing detailed local installation documentation

## Documentation

Please check these guides for setting up and working with this repository:

- [Installation Guide](INSTALLATION.md) - Step-by-step instructions for setting up locally
- [Developer Guide](DEVELOPER_GUIDE.md) - Detailed explanation of modifications and how to work with the code

## Quick Start

```bash
# Clone this repository
git clone https://github.com/AlABarazi/zenodo-rdm.git
cd zenodo-rdm

# Create environment file
echo "INSTANCE_PATH=./data" > .env

# Install with invenio-cli
invenio-cli check-requirements --development
invenio-cli install
invenio-cli services setup
invenio-cli run
```

## License

The Zenodo platform is licensed under the [MIT License](LICENSE).

## Acknowledgements

This repository is based on the work by CERN and the Zenodo team. All modifications were made to facilitate local development and testing, while preserving the core functionality of the original software.

## Local Installation Guide

This guide will help you set up Zenodo RDM on your local machine for development and testing purposes.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- Git
- Python 3.9+
- pip and pipenv

### Quick Start for Local Development

1. Clone the repository:
   ```
   git clone <repository-url>
   cd zenodo-rdm
   ```

2. Create a local environment file:
   ```
   cat > .env << EOF
   INSTANCE_PATH=./data
   EOF
   ```

3. Start the service using Docker Compose:
   ```
   docker-compose up -d
   ```

   For a full deployment with web UI, API, and worker:
   ```
   docker-compose -f docker-compose.full.yml up -d
   ```

4. Access the application:
   - Web UI: http://localhost:5000
   - API: http://localhost:5001/api
   - OpenSearch Dashboard: http://localhost:5601
   - RabbitMQ Management: http://localhost:15672
   - pgAdmin: http://localhost:5050 (email: info@zenodo.org, password: zenodo)

5. To stop the services:
   ```
   docker-compose down
   ```

### Alternative Development Setup with invenio-cli

```
pip install invenio-cli
invenio-cli check-requirements --development
invenio-cli install
invenio-cli services setup
invenio-cli run
```

See the [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/install/)
for further installation options.

## Configuration Details

The application requires the following configuration:

``` python
# Invenio-App-RDM
RDM_RECORDS_USER_FIXTURE_PASSWORDS = {
    'admin@inveniosoftware.org': '123456'
}

# Invenio-Records-Resources
SITE_UI_URL = "http://127.0.0.1:5000"
SITE_API_URL = "http://127.0.0.1:5000/api"

# Invenio-RDM-Records
RDM_RECORDS_DOI_DATACITE_USERNAME = ""
RDM_RECORDS_DOI_DATACITE_PASSWORD = ""
RDM_RECORDS_DOI_DATACITE_PREFIX = ""

# For local development, you don't need to set up OAuth credentials
# unless you need this functionality
CERN_APP_CREDENTIALS = {
    "consumer_key": "CHANGE ME",
    "consumer_secret": "CHANGE ME",
}
ORCID_APP_CREDENTIALS = {
    "consumer_key": "CHANGE ME",
    "consumer_secret": "CHANGE ME",
}
```

### Update dependencies

To update dependencies you need to run `pipenv lock`:

```shell
pipenv lock
```

## Troubleshooting

- If you encounter permission issues with Docker volumes, you may need to run:
  ```
  mkdir -p data/images && chmod -R 777 data
  ```

- If the services fail to start, check the logs:
  ```
  docker-compose logs
  ```

- To rebuild the Docker images after configuration changes:
  ```
  docker-compose build
  ```
