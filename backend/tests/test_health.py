"""Tests for health and root endpoints."""


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data
    assert "active_sessions" in data
    assert "vocabulary_size" in data
    assert data["version"] == "1.0.0"


def test_root_returns_info(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
