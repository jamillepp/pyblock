""""Test configuration for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    """Fixture to create a test client for the FastAPI application."""
    with TestClient(app) as c:
        yield c
