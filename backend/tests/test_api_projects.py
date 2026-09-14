"""Tests for project endpoints."""


import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    """Test health check endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root():
    """Test root endpoint."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.skip(reason="Requires Supabase connection - test in integration environment")
def test_create_project():
    """Test create project endpoint."""
    pass


@pytest.mark.skip(reason="Requires Supabase connection - test in integration environment")
def test_get_project():
    """Test get project endpoint."""
    pass


@pytest.mark.skip(reason="Requires Supabase connection - test in integration environment")
def test_get_project_not_found():
    """Test get project returns 404 when not found."""
    pass


@pytest.mark.skip(reason="Requires Supabase connection - test in integration environment")
def test_get_project_facts():
    """Test get project facts endpoint."""
    pass