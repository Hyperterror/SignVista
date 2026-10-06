"""Tests for POST /api/learn/attempt."""

from tests.conftest import make_fake_frame


def test_learn_requires_auth(client):
    response = client.post("/api/learn/attempt", json={"targetWord": "hello", "frame": make_fake_frame()})
    assert response.status_code == 401


def test_learn_attempt_valid(auth_client):
    response = auth_client.post("/api/learn/attempt", json={"targetWord": "hello", "frame": make_fake_frame()})
    assert response.status_code == 200
    data = response.json()
    assert {"predicted", "correct", "proficiency", "fault", "confidence"} <= data.keys()


def test_learn_attempt_unrecognizable_word(auth_client):
    response = auth_client.post("/api/learn/attempt", json={
        "targetWord": "nonexistent_word_xyz",
        "frame": make_fake_frame(),
    })
    assert response.status_code == 400
    assert "can't be practiced" in response.json()["detail"]


def test_empty_frames_are_not_counted_as_failed_attempts(auth_client):
    """Frames without hands / while the buffer fills must not lower proficiency."""
    for _ in range(5):
        response = auth_client.post("/api/learn/attempt", json={"targetWord": "hello", "frame": make_fake_frame()})
        assert response.status_code == 200
        assert response.json()["attempts"] == 0

    stats = auth_client.get(f"/api/stats/{auth_client.user_id}").json()
    assert stats["total_attempts"] == 0


def test_learn_rejects_foreign_session(auth_client):
    response = auth_client.post("/api/learn/attempt", json={
        "sessionId": "not-me", "targetWord": "hello", "frame": make_fake_frame(),
    })
    assert response.status_code == 403
