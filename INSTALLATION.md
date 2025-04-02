# Zenodo RDM Local Installation Guide

This guide explains how to install and run Zenodo RDM locally, based on a modified version of the CERN Zenodo repository adapted to work on local development environments.

## Prerequisites

Before you begin, make sure you have the following installed:
- Docker and Docker Compose
- Python 3.9
- pip and pipenv
- Node.js and npm
- Git

## Quick Installation

### 1. Clone the Repository

```bash
git clone https://github.com/AlABarazi/zenodo-rdm.git
cd zenodo-rdm
```

### 2. Environment Setup

Create a local environment file:

```bash
cat > .env << EOF
INSTANCE_PATH=./data
EOF
```

### 3. Install Dependencies

There are two approaches to installing the application:

#### Option A: Using invenio-cli (Recommended)

This is the preferred method for local development:

```bash
# Check requirements
invenio-cli check-requirements --development

# Install the application
invenio-cli install

# Set up services
invenio-cli services setup

# Set admin password
# This sets the password for the default admin account (admin@zenodo.org)
source .venv/bin/activate && invenio shell -c "from invenio_accounts.models import User; from flask_security.utils import hash_password; u = User.query.filter_by(email='admin@zenodo.org').first(); u.password = hash_password('password123'); from invenio_db import db; db.session.commit(); print('Password updated successfully')"

# Run the application
invenio-cli run
```

### 4. Access the Application

After successful installation, you can access:
- Web UI: http://localhost:5000
- API: http://localhost:5000/api
- OpenSearch Dashboard: http://localhost:5601
- RabbitMQ Management: http://localhost:15672 (username: guest, password: guest)
- pgAdmin: http://localhost:5050 (username: info@zenodo.org, password: zenodo)

### 5. Login with Admin Account

After setting the admin password in the installation step, you can log in to the web UI with:
- Email: admin@zenodo.org
- Password: password123 (or whatever password you set)

There are also two other default accounts created during installation:
- eu@zenodo.org
- user@demo.org

You can check all available user accounts with:
```bash
source .venv/bin/activate && invenio shell -c "from invenio_accounts.models import User; print('\n'.join([f'ID: {u.id}, Email: {u.email}, Active: {u.active}' for u in User.query.all()]))"
```