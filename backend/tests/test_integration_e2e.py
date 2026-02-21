"""
End-to-end integration tests for ISL Unified Models Integration.

Tests the complete flow from application startup through prediction.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from ml.inference import (
    are_isl_modules_initialized,
    get_isl_modules_status,
    is_model_loaded,
    initialize_isl_modules
)
from ml.vocabulary import (
    get_unified_vocabulary,
    get_word_by_module_index,
    get_display_name
)


@pytest.fixture(scope="module")
def client():
    """Create test client with lifespan context."""
    # Initialize ISL modules manually for testing since TestClient
    # doesn't always trigger lifespan events properly
    initialize_isl_modules()
    
    with TestClient(app) as test_client:
        yield test_client


def test_application_startup_initializes_all_components(client):
    """
    Test that application startup properly initializes:
    - ConfigurationManager
    - ModelLoader
    - VocabularyManager
    - InferenceEngine with all modules
    """
    # Check that ISL modules are initialized
    assert are_isl_modules_initialized(), "ISL modules should be initialized at startup"
    
    # Get module status
    status = get_isl_modules_status()
    assert status["initialized"], "ISL modules should be marked as initialized"
    assert "enabled_modules" in status, "Status should include enabled modules list"
    assert "configuration" in status, "Status should include configuration"
    assert "modules" in status, "Status should include module details"
    
    # Check that at least one module is configured (even if not loaded due to missing models)
    assert len(status["modules"]) == 3, "Should have status for all 3 modules"
    assert "detection" in status["modules"], "Should have detection module status"
    assert "recognition" in status["modules"], "Should have recognition module status"
    assert "translation" in status["modules"], "Should have translation module status"


def test_health_endpoint_exposes_module_details(client):
    """
    Test that health endpoint properly exposes ISL module details.
    """
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "isl_modules" in data, "Health endpoint should include ISL module status"
    
    isl_modules = data["isl_modules"]
    assert "initialized" in isl_modules
    assert "enabled_modules" in isl_modules
    assert "configuration" in isl_modules
    assert "modules" in isl_modules
    
    # Check module details structure
    modules = isl_modules["modules"]
    for module_name in ["detection", "recognition", "translation"]:
        assert module_name in modules, f"Should have {module_name} module status"
        module_info = modules[module_name]
        assert "enabled" in module_info
        assert "loaded" in module_info
        # confidence_threshold and priority may be None if module is disabled


def test_vocabulary_manager_has_all_module_vocabularies():
    """
    Test that VocabularyManager has registered all module vocabularies.
    """
    # Get unified vocabulary
    unified_vocab = get_unified_vocabulary()
    assert len(unified_vocab) > 0, "Unified vocabulary should not be empty"
    
    # Check that we have entries from different modules
    modules_present = set(entry["module"] for entry in unified_vocab)
    assert "detection" in modules_present or "recognition" in modules_present or "translation" in modules_present, \
        "Unified vocabulary should include entries from ISL modules"
    
    # Test module-specific index mapping
    # Detection module: 35 classes (0-34)
    detection_word = get_word_by_module_index("detection", 0)
    assert detection_word != "unknown", "Detection module should map index 0 to a word"
    
    # Recognition module: 3 classes (0-2)
    recognition_word = get_word_by_module_index("recognition", 0)
    assert recognition_word != "unknown", "Recognition module should map index 0 to a word"
    
    # Translation module: 10 classes (0-9)
    translation_word = get_word_by_module_index("translation", 0)
    assert translation_word != "unknown", "Translation module should map index 0 to a word"


def test_api_route_supports_module_details(client):
    """
    Test that /api/recognize-frame endpoint supports module_details parameter.
    """
    # Create a simple test frame (1x1 black pixel as base64 JPEG)
    import base64
    import io
    from PIL import Image
    
    # Create a small test image
    img = Image.new('RGB', (100, 100), color='black')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # Test without module_details
    response = client.post(
        "/api/recognize-frame",
        json={
            "sessionId": "test-session-e2e",
            "frame": f"data:image/jpeg;base64,{img_base64}"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "word" in data
    assert "confidence" in data
    assert "buffer_status" in data
    # module_details should be None when not requested
    assert data.get("module_details") is None
    
    # Test with module_details=true
    response = client.post(
        "/api/recognize-frame?return_module_details=true",
        json={
            "sessionId": "test-session-e2e-2",
            "frame": f"data:image/jpeg;base64,{img_base64}"
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # When module_details is requested, it should be present
    # (even if empty due to no face detected or no predictions)
    # The key should exist in the response
    assert "module_details" in data


def test_inference_engine_uses_modules_based_on_configuration():
    """
    Test that InferenceEngine respects configuration for module enable/disable.
    """
    status = get_isl_modules_status()
    
    if not status["initialized"]:
        pytest.skip("ISL modules not initialized, skipping configuration test")
    
    enabled_modules = status["enabled_modules"]
    modules = status["modules"]
    
    # Verify that enabled_modules list matches individual module enabled flags
    for module_name in ["detection", "recognition", "translation"]:
        is_enabled = modules[module_name]["enabled"]
        if is_enabled:
            assert module_name in enabled_modules, \
                f"Enabled module {module_name} should be in enabled_modules list"
        else:
            assert module_name not in enabled_modules, \
                f"Disabled module {module_name} should not be in enabled_modules list"


def test_complete_end_to_end_flow_with_all_modules_enabled(client):
    """
    Test complete end-to-end flow:
    1. Application starts and initializes all components
    2. Health endpoint shows module status
    3. API endpoint processes frame with module details
    4. Vocabulary manager provides correct mappings
    """
    # Step 1: Verify initialization
    assert are_isl_modules_initialized(), "ISL modules should be initialized"
    
    # Step 2: Check health endpoint
    health_response = client.get("/health")
    assert health_response.status_code == 200
    health_data = health_response.json()
    assert health_data["status"] == "ok"
    assert "isl_modules" in health_data
    
    # Step 3: Process a frame
    import base64
    import io
    from PIL import Image
    
    img = Image.new('RGB', (640, 480), color='blue')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    frame_response = client.post(
        "/api/recognize-frame?return_module_details=true",
        json={
            "sessionId": "test-e2e-complete",
            "frame": f"data:image/jpeg;base64,{img_base64}"
        }
    )
    assert frame_response.status_code == 200
    frame_data = frame_response.json()
    
    # Verify response structure
    assert "word" in frame_data
    assert "confidence" in frame_data
    assert "buffer_status" in frame_data
    assert "history" in frame_data
    assert "module_details" in frame_data
    
    # Step 4: Verify vocabulary mappings work
    unified_vocab = get_unified_vocabulary()
    assert len(unified_vocab) > 0
    
    # Test display name retrieval
    display_name = get_display_name("hello")
    assert display_name is not None
    assert display_name != ""
    
    print("✅ Complete end-to-end flow test passed!")
