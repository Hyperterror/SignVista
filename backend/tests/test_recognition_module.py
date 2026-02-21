"""
Tests for Recognition Module.

Tests the LSTM-based temporal sequence analysis for word-level recognition
(Hello, How are you, Thank you) - 3 classes.
"""

import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock

from ml.modules.recognition import RecognitionModule
from ml.modules import ModulePrediction
from ml.model_loader import ModelLoader
from ml.config_manager import ConfigurationManager


@pytest.fixture
def model_loader():
    """Create model loader instance."""
    return ModelLoader()


@pytest.fixture
def config_manager():
    """Create configuration manager instance."""
    return ConfigurationManager()


@pytest.fixture
def recognition_model(model_loader):
    """Load recognition model."""
    model = model_loader.load_recognition_model()
    if model is None:
        pytest.skip("Recognition model not available")
    return model


@pytest.fixture
def module_config(config_manager):
    """Get recognition module configuration."""
    module_config = config_manager.get_module_config("recognition")
    if module_config is None:
        pytest.skip("Recognition module not configured")
    
    return {
        "confidence_threshold": module_config.confidence_threshold,
        "preprocessing_params": module_config.preprocessing_params
    }


@pytest.fixture
def recognition_module(recognition_model, module_config):
    """Create recognition module instance."""
    return RecognitionModule(recognition_model, module_config)


@pytest.fixture
def test_frame():
    """Create a test frame with a person."""
    # Create a simple test frame (640x480 BGR)
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    return frame


@pytest.fixture
def empty_frame():
    """Create an empty black frame."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


class TestRecognitionModule:
    """Test suite for Recognition Module."""
    
    def test_module_initialization(self, recognition_module):
        """Test that recognition module initializes correctly."""
        assert recognition_module is not None
        assert recognition_module.model is not None
        assert recognition_module.buffer_size == 45
        assert 0.0 <= recognition_module.confidence_threshold <= 1.0
    
    def test_extract_pose_keypoints(self, recognition_module, test_frame):
        """Test pose keypoint extraction."""
        keypoints = recognition_module.extract_pose_keypoints(test_frame)
        
        # Should return 258 features or None
        if keypoints is not None:
            assert keypoints.shape == (258,)
            assert keypoints.dtype == np.float32
    
    def test_predict_buffer_not_ready(self, recognition_module, test_frame):
        """Test prediction returns None when buffer not ready."""
        # Use a unique session ID
        session_id = "test_session_buffer_not_ready"
        
        # First frame should return None (buffer not ready)
        prediction = recognition_module.predict(test_frame, session_id)
        assert prediction is None
    
    def test_predict_structure(self, recognition_module, test_frame):
        """Test prediction structure when buffer is full."""
        session_id = "test_session_structure"
        
        # Fill buffer with 45 frames
        for i in range(45):
            prediction = recognition_module.predict(test_frame, session_id)
        
        # After 45 frames, should get a prediction (or None if confidence too low)
        if prediction is not None:
            assert isinstance(prediction, ModulePrediction)
            assert prediction.module_name == "recognition"
            assert 0 <= prediction.class_index <= 2  # 3 classes (0, 1, 2)
            assert 0.0 <= prediction.confidence <= 1.0
            assert prediction.word in ["hello", "how_are_you", "thank_you"]
            assert prediction.display_name in ["Hello", "How Are You", "Thank You"]
            assert "buffer_size" in prediction.metadata
    
    def test_should_clear_buffer(self, recognition_module):
        """Test buffer clearing logic."""
        # High confidence should trigger buffer clear
        assert recognition_module.should_clear_buffer(0.9) == True
        
        # Low confidence should not trigger buffer clear
        assert recognition_module.should_clear_buffer(0.5) == False
    
    def test_confidence_threshold_filtering(self, recognition_module, test_frame):
        """Test that predictions below threshold are filtered out."""
        # Set a very high threshold
        recognition_module.confidence_threshold = 0.99
        
        session_id = "test_session_threshold"
        
        # Fill buffer
        for i in range(45):
            prediction = recognition_module.predict(test_frame, session_id)
        
        # With very high threshold, should return None
        # (unless the model is extremely confident, which is unlikely with random frames)
        # This test verifies the threshold logic works
        if prediction is not None:
            assert prediction.confidence >= 0.99
    
    def test_word_mapping(self, recognition_module):
        """Test that all three word classes can be mapped."""
        from ml.vocabulary import get_word_by_module_index, get_display_name
        
        # Test all three classes
        for class_idx in range(3):
            word = get_word_by_module_index("recognition", class_idx)
            assert word in ["hello", "how_are_you", "thank_you"]
            
            display = get_display_name(word, "recognition")
            assert display in ["Hello", "How Are You", "Thank You"]
