import pytest
import os

@pytest.fixture(scope="session")
def base_url():
    """Return the base URL for API requests."""
    return os.environ.get("ZENODO_BASE_URL", "http://localhost:5001")

@pytest.fixture(scope="session")
def record_id():
    """Return a test record ID with images."""
    return os.environ.get("TEST_RECORD_ID", "YOUR_RECORD_ID")  # Replace with your test record ID

@pytest.fixture(scope="session")
def public_record_id():
    """Return a public test record ID with images."""
    return os.environ.get("PUBLIC_RECORD_ID", "YOUR_PUBLIC_RECORD_ID")  # Replace with your public test record ID

@pytest.fixture(scope="session")
def restricted_record_id():
    """Return a restricted test record ID with images."""
    return os.environ.get("RESTRICTED_RECORD_ID", "YOUR_RESTRICTED_RECORD_ID")  # Replace with your restricted test record ID

@pytest.fixture(scope="session")
def auth_token():
    """Return an authentication token for restricted resources."""
    return os.environ.get("AUTH_TOKEN", "")  # Replace with your auth token 