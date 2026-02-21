"""
Tests for Translation Module.

Tests the YOLO-v3 hand detection with SqueezeNet classification
for 10 sign classes (G, I, K, O, P, S, U, V, X, Y).
"""

import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from ml.modules.translation import TranslationModule
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
def translation_model(model_loader):
    """Load translation model."""
    model = model_loader.load_translation_model()
    if model is None:
        pytest.skip("Translation model not available")
    return model


@pytest.fixture
def yolo_paths():
    """Get YOLO configuration and weights paths."""
    config_path = "ISL-Unified-Project/config/yolo/cross-hands.cfg"
    weights_path = "ISL-Unified-Project/config/yolo/cross-hands.weights"
    
    if not os.path.exists(config_path):
        pytest.skip(f"YOLO config not found: {config_path}")
    
    if not os.path.exists(weights_path):
        pytest.skip(f"YOLO weights not found: {weights_path}")
    
    return config_path, weights_path


@pytest.fixture
def module_config(config_manager):
    """Get translation module configuration."""
    module_config = config_manager.get_module_config("translation")
    if module_config is None:
        pytest.skip("Translation module not configured")
    
    return {
        "confidence_threshold": module_config.confidence_threshold,
        "preprocessing_params": module_config.preprocessing_params
    }


@pytest.fixture
def translation_module(translation_model, yolo_paths, module_config):
    """Create translation module instance."""
    config_path, weights_path = yolo_paths
    return TranslationModule(translation_model, config_path, weights_path, module_config)


@pytest.fixture
def test_frame():
    """Create a test frame with hands."""
    # Create a simple test frame (640x480 BGR)
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    return frame


@pytest.fixture
def empty_frame():
    """Create an empty black frame."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


class TestTranslationModule:
    """Test suite for Translation Module."""
    
    def test_module_initialization(self, translation_module):
        """Test that translation module initializes correctly."""
        assert translation_module is not None
        assert translation_module.model is not None
        assert translation_module.yolo_net is not None
        assert 0.0 <= translation_module.confidence_threshold <= 1.0
        assert translation_module.target_size == (224, 224)
    
    def test_detect_hands(self, translation_module, test_frame):
        """Test YOLO hand detection."""
        hand_boxes = translation_module.detect_hands(test_frame)
        
        # Should return a list (may be empty if no hands detected)
        assert isinstance(hand_boxes, list)
        
        # If hands detected, verify box format
        for box in hand_boxes:
            assert len(box) == 4  # (x, y, w, h)
            x, y, w, h = box
            assert isinstance(x, int)
            assert isinstance(y, int)
            assert isinstance(w, int)
            assert isinstance(h, int)
    
    def test_segment_skin(self, translation_module, test_frame):
        """Test skin segmentation."""
        # Create a small hand region
        hand_region = test_frame[100:300, 200:400]
        
        segmented = translation_module.segment_skin(hand_region)
        
        # Should return an image of the same shape
        assert segmented.shape == hand_region.shape
        assert segmented.dtype == np.uint8
    
    def test_preprocess_for_squeezenet(self, translation_module, test_frame):
        """Test preprocessing for SqueezeNet."""
        # Create a small hand region
        hand_region = test_frame[100:300, 200:400]
        
        preprocessed = translation_module.preprocess_for_squeezenet(hand_region)
        
        # Should return (1, 224, 224, 3) shape
        assert preprocessed.shape == (1, 224, 224, 3)
        assert preprocessed.dtype == np.float32
        
        # Values should be normalized to [0, 1]
        assert np.min(preprocessed) >= 0.0
        assert np.max(preprocessed) <= 1.0
    
    def test_predict_with_empty_frame(self, translation_module, empty_frame):
        """Test prediction with empty frame returns None."""
        prediction = translation_module.predict(empty_frame)
        
        # Empty frame should not detect hands
        assert prediction is None
    
    def test_predict_structure(self, translation_module, test_frame):
        """Test prediction structure when hands are detected."""
        prediction = translation_module.predict(test_frame)
        
        # May return None if no hands detected or confidence too low
        if prediction is not None:
            assert isinstance(prediction, ModulePrediction)
            assert prediction.module_name == "translation"
            assert 0 <= prediction.class_index <= 9  # 10 classes (0-9)
            assert 0.0 <= prediction.confidence <= 1.0
            assert prediction.word in ["G", "I", "K", "O", "P", "S", "U", "V", "X", "Y"]
            assert "num_hands_detected" in prediction.metadata
            assert "hand_region" in prediction.metadata
    
    def test_stateless_processing(self, translation_module, test_frame):
        """Test that processing the same frame twice gives consistent results."""
        prediction1 = translation_module.predict(test_frame)
        prediction2 = translation_module.predict(test_frame)
        
        # Both should be None or both should have predictions
        if prediction1 is None:
            assert prediction2 is None
        else:
            assert prediction2 is not None
            # Should get same class and similar confidence
            assert prediction1.class_index == prediction2.class_index
            assert abs(prediction1.confidence - prediction2.confidence) < 1e-5
    
    def test_confidence_threshold_filtering(self, translation_module, test_frame):
        """Test that predictions below threshold are filtered out."""
        # Set a very high threshold
        translation_module.confidence_threshold = 0.99
        
        prediction = translation_module.predict(test_frame)
        
        # With very high threshold, should return None
        # (unless the model is extremely confident, which is unlikely with random frames)
        if prediction is not None:
            assert prediction.confidence >= 0.99
    
    def test_merge_hand_boxes(self, translation_module):
        """Test merging multiple hand bounding boxes."""
        # Single box
        single_box = [(100, 100, 50, 50)]
        x, y, x1, y1 = translation_module._merge_hand_boxes(single_box)
        assert x == 100
        assert y == 100
        assert x1 == 150
        assert y1 == 150
        
        # Multiple boxes
        multiple_boxes = [(100, 100, 50, 50), (200, 150, 60, 60)]
        x, y, x1, y1 = translation_module._merge_hand_boxes(multiple_boxes)
        assert x == 100  # min x
        assert y == 100  # min y
        assert x1 == 260  # max x + w
        assert y1 == 210  # max y + h
    
    def test_word_mapping(self, translation_module):
        """Test that all 10 sign classes can be mapped."""
        from ml.vocabulary import get_word_by_module_index, get_display_name
        
        # Test all 10 classes
        expected_words = ["G", "I", "K", "O", "P", "S", "U", "V", "X", "Y"]
        for class_idx in range(10):
            word = get_word_by_module_index("translation", class_idx)
            assert word in expected_words
            
            display = get_display_name(word, "translation")
            assert display in expected_words
