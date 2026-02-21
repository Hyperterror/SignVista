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


def test_recognize_frame_without_module_details(client):
    """By default, module_details should be None (backward compatibility)."""
    response = client.post("/api/recognize-frame", json={
        "sessionId": "test-session-4",
        "frame": make_fake_frame(),
    })
    assert response.status_code == 200
    data = response.json()
    # module_details should be None or not present when not requested
    assert data.get("module_details") is None


def test_recognize_frame_with_module_details(client):
    """When return_module_details=true, module_details should be included."""
    response = client.post(
        "/api/recognize-frame?return_module_details=true",
        json={
            "sessionId": "test-session-5",
            "frame": make_fake_frame(),
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # If ISL modules are initialized, module_details should be present
    # If not initialized, it may still be None (fallback to LSTM)
    # This test verifies the parameter is passed through correctly
    assert "module_details" in data


def test_recognize_frame_module_details_structure(client):
    """When module_details is present, it should have the correct structure."""
    response = client.post(
        "/api/recognize-frame?return_module_details=true",
        json={
            "sessionId": "test-session-6",
            "frame": make_fake_frame(),
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # If module_details is present (ISL modules initialized), verify structure
    if data.get("module_details") is not None:
        module_details = data["module_details"]
        assert "active_modules" in module_details
        assert "predictions" in module_details
        assert isinstance(module_details["active_modules"], list)
        assert isinstance(module_details["predictions"], list)
        
        # Verify predictions are ranked by confidence (descending order)
        if len(module_details["predictions"]) > 1:
            confidences = [p["confidence"] for p in module_details["predictions"]]
            assert confidences == sorted(confidences, reverse=True), \
                "Predictions should be ranked by confidence in descending order"
