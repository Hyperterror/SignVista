"""Tests for POST /api/recognize-frame."""

from tests.conftest import make_fake_frame, make_invalid_base64


def test_recognize_frame_valid(client):
    """Valid frame should return a response with correct shape."""
    response = client.post("/api/recognize-frame", json={
        "sessionId": "test-session-1",
        "frame": make_fake_frame(),
    })
    assert response.status_code == 200
    data = response.json()
    assert "word" in data
    assert "confidence" in data
    assert "buffer_status" in data
    assert "history" in data
    assert isinstance(data["confidence"], (int, float))


def test_recognize_frame_missing_session_id(client):
    """Missing sessionId should return 400."""
    response = client.post("/api/recognize-frame", json={
        "sessionId": "",
        "frame": make_fake_frame(),
    })
    assert response.status_code == 400


def test_recognize_frame_invalid_base64(client):
    """Invalid base64 should return 400."""
    response = client.post("/api/recognize-frame", json={
        "sessionId": "test-session-2",
        "frame": make_invalid_base64(),
    })
    assert response.status_code == 400


def test_recognize_frame_missing_fields(client):
    """Missing required fields should return 422."""
    response = client.post("/api/recognize-frame", json={
        "sessionId": "test-session-3",
    })
    assert response.status_code == 422


def test_translate_history_builds_up(client):
    """Multiple calls should build up word history."""
    for i in range(3):
        response = client.post("/api/recognize-frame", json={
            "sessionId": "history-test",
            "frame": make_fake_frame(),
        })
        assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data["history"], list)
