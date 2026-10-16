"""Tests for root discovery and health diagnostic endpoints."""

from fastapi import status


def test_root_endpoint(client):
    """Verify application metadata at root endpoint."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["app"] == "Batchwise"
    assert data["tagline"] == "Every batch. Every cost. Every rupee."
    assert data["version"] == "0.1.0"
    assert data["docs_url"] == "/docs"
    assert data["health_url"] == "/api/v1/health"


def test_health_endpoint_healthy(client):
    """Verify GET /api/v1/health reports operational status and connected database."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Batchwise"
    assert data["database"] == "connected"
    assert "version" in data


def test_health_endpoint_db_failure(client):
    """Verify health endpoint reports degraded status when database query fails."""
    from unittest.mock import MagicMock
    from app.db.database import get_db

    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("DB connection timeout")

    client.app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "degraded"
        assert "unhealthy" in data["database"]
    finally:
        del client.app.dependency_overrides[get_db]
