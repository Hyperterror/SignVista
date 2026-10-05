"""Tests for POST /api/recognize-frame."""

from tests.conftest import make_fake_frame, make_invalid_base64


def test_recognize_frame_requires_auth(client):
    response = client.post("/api/recognize-frame", json={"frame": make_fake_frame()})
    assert response.status_code == 401


def test_recognize_frame_valid(auth_client):
    response = auth_client.post("/api/recognize-frame", json={"frame": make_fake_frame()})
    assert response.status_code == 200
    data = response.json()
    assert {"word", "confidence", "buffer_status", "history"} <= data.keys()
    assert isinstance(data["confidence"], (int, float))


def test_recognize_frame_rejects_foreign_session_id(auth_client):
    response = auth_client.post("/api/recognize-frame", json={
        "sessionId": "someone-else",
        "frame": make_fake_frame(),
    })
    assert response.status_code == 403


def test_recognize_frame_invalid_base64(auth_client):
    response = auth_client.post("/api/recognize-frame", json={"frame": make_invalid_base64()})
    assert response.status_code == 400


def test_recognize_frame_missing_fields(auth_client):
    response = auth_client.post("/api/recognize-frame", json={})
    assert response.status_code == 422


def test_translate_history_builds_up(auth_client):
    for _ in range(3):
        response = auth_client.post("/api/recognize-frame", json={"frame": make_fake_frame()})
        assert response.status_code == 200
    assert isinstance(response.json()["history"], list)


def test_blank_frame_never_reports_a_word(auth_client):
    """A frame with nobody in it must not produce a (mock) prediction."""
    data = auth_client.post("/api/recognize-frame", json={"frame": make_fake_frame()}).json()
    assert data["word"] is None
    assert data["buffer_status"] != "mock_ready"


def test_recognize_frame_without_module_details(auth_client):
    response = auth_client.post("/api/recognize-frame", json={"frame": make_fake_frame()})
    assert response.json().get("module_details") is None


def test_recognize_frame_module_details_structure(auth_client):
    response = auth_client.post(
        "/api/recognize-frame?return_module_details=true",
        json={"frame": make_fake_frame()},
    )
    assert response.status_code == 200
    details = response.json().get("module_details")
    if details is not None:
        assert isinstance(details["active_modules"], list)
        assert isinstance(details["predictions"], list)
        confidences = [p["confidence"] for p in details["predictions"]]
        assert confidences == sorted(confidences, reverse=True)
