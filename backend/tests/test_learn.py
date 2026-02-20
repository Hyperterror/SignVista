"""Tests for POST /api/learn/attempt."""

from tests.conftest import make_fake_frame


def test_learn_attempt_valid(client):
    """Valid learn attempt should return proficiency data."""
    response = client.post("/api/learn/attempt", json={
        "sessionId": "learn-test-1",
        "targetWord": "hello",
        "frame": make_fake_frame(),
    })
    assert response.status_code == 200
    data = response.json()
    assert "predicted" in data
    assert "correct" in data
    assert "proficiency" in data
    assert "fault" in data
    assert "confidence" in data


def test_learn_attempt_invalid_word(client):
    """Non-vocabulary word should return 400."""
    response = client.post("/api/learn/attempt", json={
        "sessionId": "learn-test-2",
        "targetWord": "nonexistent_word_xyz",
        "frame": make_fake_frame(),
    })
    assert response.status_code == 400
    assert "not in the vocabulary" in response.json()["detail"]


def test_learn_proficiency_tracks(client):
    """Multiple attempts should update proficiency."""
    for i in range(5):
        response = client.post("/api/learn/attempt", json={
            "sessionId": "proficiency-test",
            "targetWord": "water",
            "frame": make_fake_frame(),
        })
        assert response.status_code == 200

    # Check stats reflect the attempts
    stats_response = client.get("/api/stats/proficiency-test")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total_attempts"] > 0
