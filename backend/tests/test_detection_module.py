"""
Tests for Detection Module.

Tests the MediaPipe Hands-based hand landmark extraction
and FNN gesture classification.
"""

import numpy as np
import pytest
import cv2

from ml.model_loader import ModelLoader
from ml.config_manager import ConfigurationManager
from ml.modules.detection import DetectionModule


@pytest.fixture
def model_loader():
    """Create model loader instance."""
    return ModelLoader()


@pytest.fixture
def detection_model(model_loader):
    """Load detection model."""
    model = model_loader.load_detection_model()
    if model is None:
        pytest.skip("Detection model not available")
    return model


@pytest.fixture
def detection_config():
    """Get detection module configuration."""
    config_manager = ConfigurationManager()
    module_config = config_manager.get_module_config("detection")
    if module_config is None:
        pytest.skip("Detection module not configured")
    
    return {
        "confidence_threshold": module_config.confidence_threshold,
        "preprocessing_params": module_config.preprocessing_params
    }


@pytest.fixture
def detection_module(detection_model, detection_config):
    """Create detection module instance."""
    return DetectionModule(detection_model, detection_config)


@pytest.fixture
def test_frame():
    """Create a test frame with a simple hand-like shape."""
    # Create a 640x480 frame with a white background
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # Draw a simple hand-like shape (circle for palm, lines for fingers)
    center = (320, 240)
    cv2.circle(frame, center, 50, (200, 150, 100), -1)  # Palm
    
    # Draw 5 fingers
    for i in range(5):
        angle = -90 + (i * 45)
        end_x = int(center[0] + 80 * np.cos(np.radians(angle)))
        end_y = int(center[1] + 80 * np.sin(np.radians(angle)))
        cv2.line(frame, center, (end_x, end_y), (200, 150, 100), 10)
    
    return frame


@pytest.fixture
def empty_frame():
    """Create an empty frame with no hands."""
    return np.ones((480, 640, 3), dtype=np.uint8) * 255


class TestDetectionModule:
    """Test suite for Detection Module."""
    
    def test_module_initialization(self, detection_module):
        """Test that detection module initializes correctly."""
        assert detection_module is not None
        assert detection_module.model is not None
        assert detection_module.hands is not None
        assert 0.0 <= detection_module.confidence_threshold <= 1.0
    
    def test_extract_hand_landmarks_with_hands(self, detection_module, test_frame):
        """Test hand landmark extraction from frame with hands."""
        landmarks = detection_module.extract_hand_landmarks(test_frame)
        
        # May or may not detect the simple shape as a hand
        # This is expected behavior - MediaPipe is trained on real hands
        if landmarks is not None:
            assert landmarks.shape == (42,)
            assert landmarks.dtype == np.float32
    
    def test_extract_hand_landmarks_empty_frame(self, detection_module, empty_frame):
        """Test hand landmark extraction from empty frame."""
        landmarks = detection_module.extract_hand_landmarks(empty_frame)
        
        # Should return None for empty frame
        assert landmarks is None
    
    def test_preprocess_landmarks(self, detection_module):
        """Test landmark preprocessing."""
        # Create fake landmarks
        landmarks = np.random.rand(42).astype(np.float32)
        
        processed = detection_module.preprocess_landmarks(landmarks)
        
        # Check shape
        assert processed.shape == (1, 42)
        
        # Check that values are normalized
        assert np.max(np.abs(processed)) <= 1.0
        
        # Check that first landmark (wrist) is now at origin
        assert abs(processed[0, 0]) < 1e-6  # x coordinate
        assert abs(processed[0, 1]) < 1e-6  # y coordinate
    
    def test_predict_with_empty_frame(self, detection_module, empty_frame):
        """Test prediction with empty frame returns None."""
        prediction = detection_module.predict(empty_frame)
        
        # Should return None when no hands detected
        assert prediction is None
    
    def test_predict_structure(self, detection_module, test_frame):
        """Test prediction structure when hands are detected."""
        prediction = detection_module.predict(test_frame)
        
        # May or may not detect the simple shape
        if prediction is not None:
            # Verify prediction structure
            assert prediction.module_name == "detection"
            assert 0 <= prediction.class_index <= 34
            assert 0.0 <= prediction.confidence <= 1.0
            assert prediction.word is not None
            assert prediction.display_name is not None
            assert prediction.preprocessing_time >= 0
            assert prediction.inference_time >= 0
            assert "num_hands" in prediction.metadata
            assert "raw_landmarks" in prediction.metadata
    
    def test_stateless_processing(self, detection_module, test_frame):
        """Test that processing the same frame twice gives consistent results."""
        prediction1 = detection_module.predict(test_frame)
        prediction2 = detection_module.predict(test_frame)
        
        # Both should be None or both should have predictions
        assert (prediction1 is None) == (prediction2 is None)
        
        # If both have predictions, they should be identical
        if prediction1 is not None and prediction2 is not None:
            assert prediction1.class_index == prediction2.class_index
            # Confidence should be very close (within floating point tolerance)
            assert abs(prediction1.confidence - prediction2.confidence) < 1e-5
    
    def test_confidence_threshold_filtering(self, detection_module, test_frame):
        """Test that predictions below threshold are filtered out."""
        # Set a very high threshold
        original_threshold = detection_module.confidence_threshold
        detection_module.confidence_threshold = 0.99
        
        prediction = detection_module.predict(test_frame)
        
        # Should return None or have confidence >= 0.99
        if prediction is not None:
            assert prediction.confidence >= 0.99
        
        # Restore original threshold
        detection_module.confidence_threshold = original_threshold


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
