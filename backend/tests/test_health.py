"""Health check endpoint tests."""
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/api/v1/health/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data


def test_detailed_health_check(client: TestClient):
    """Test detailed health check endpoint."""
    response = client.get("/api/v1/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "checks" in data
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] == "healthy"


def test_readiness_check(client: TestClient):
    """Test readiness check endpoint."""
    response = client.get("/api/v1/health/readiness")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "timestamp" in data


def test_liveness_check(client: TestClient):
    """Test liveness check endpoint."""
    response = client.get("/api/v1/health/liveness")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data