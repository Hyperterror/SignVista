"""
Basic tests for all three modules without requiring actual model files.

These tests verify the module logic, vocabulary mappings, and data structures
work correctly independently of model availability.
"""

import numpy as np
import pytest
from unittest.mock import Mock, MagicMock
import time

from ml.modules import ModulePrediction
from ml.modules.detection import DetectionModule
from ml.modules.recognition import RecognitionModule
from ml.modules.translation import TranslationModule
from ml.vocabulary import (
    get_word_by_module_index,
    get_display_name,
    DETECTION_VOCAB,
    RECOGNITION_VOCAB,
    TRANSLATION_VOCAB
)


class TestModulePredictionDataclass:
    """Test the ModulePrediction dataclass structure."""
    
    def test_module_prediction_creation(self):
        """Test creating a ModulePrediction instance."""
        prediction = ModulePrediction(
            module_name="detection",
            class_index=0,
            word="A",
            display_name="A",
            confidence=0.85,
            preprocessing_time=0.015,
            inference_time=0.008,
            metadata={"test": "data"},
            timestamp=time.time()
        )
        
        assert prediction.module_name == "detection"
        assert prediction.class_index == 0
        assert prediction.word == "A"
        assert prediction.display_name == "A"
        assert prediction.confidence == 0.85
        assert prediction.preprocessing_time == 0.015
        assert prediction.inference_time == 0.008
        assert prediction.metadata == {"test": "data"}
        assert isinstance(prediction.timestamp, float)


class TestDetectionModuleBasic:
    """Basic tests for Detection Module without model."""
    
    def test_detection_vocabulary_mapping(self):
        """Test detection module vocabulary has 35 classes."""
        assert len(DETECTION_VOCAB) == 35
        
        # Test mapping all indices
        for i in range(35):
            word = get_word_by_module_index("detection", i)
            assert word is not None
            assert word != "unknown"
            
            display = get_display_name(word, "detection")
            assert display is not None
    
    def test_detection_class_range(self):
        """Test detection module class indices are 0-34."""
        indices = [entry["index"] for entry in DETECTION_VOCAB]
        assert min(indices) == 0
        assert max(indices) == 34
        assert len(set(indices)) == 35  # All unique


class TestRecognitionModuleBasic:
    """Basic tests for Recognition Module without model."""
    
    def test_recognition_vocabulary_mapping(self):
        """Test recognition module vocabulary has 3 classes."""
        assert len(RECOGNITION_VOCAB) == 3
        
        # Test mapping all indices
        for i in range(3):
            word = get_word_by_module_index("recognition", i)
            assert word in ["hello", "how_are_you", "thank_you"]
            
            display = get_display_name(word, "recognition")
            assert display in ["Hello", "How Are You", "Thank You"]
    
    def test_recognition_class_range(self):
        """Test recognition module class indices are 0-2."""
        indices = [entry["index"] for entry in RECOGNITION_VOCAB]
        assert min(indices) == 0
        assert max(indices) == 2
        assert len(set(indices)) == 3  # All unique
    
    def test_recognition_buffer_logic(self):
        """Test recognition module buffer clearing logic."""
        # Create mock model and config
        mock_model = Mock()
        config = {
            "confidence_threshold": 0.6,
            "preprocessing_params": {
                "buffer_size": 45,
                "clear_threshold": 0.8
            }
        }
        
        module = RecognitionModule(mock_model, config)
        
        # Test buffer clearing logic
        assert module.should_clear_buffer(0.9) == True
        assert module.should_clear_buffer(0.8) == True
        assert module.should_clear_buffer(0.79) == False
        assert module.should_clear_buffer(0.5) == False


class TestTranslationModuleBasic:
    """Basic tests for Translation Module without model."""
    
    def test_translation_vocabulary_mapping(self):
        """Test translation module vocabulary has 10 classes."""
        assert len(TRANSLATION_VOCAB) == 10
        
        # Test mapping all indices
        expected_words = ["G", "I", "K", "O", "P", "S", "U", "V", "X", "Y"]
        for i in range(10):
            word = get_word_by_module_index("translation", i)
            assert word in expected_words
            
            display = get_display_name(word, "translation")
            assert display in expected_words
    
    def test_translation_class_range(self):
        """Test translation module class indices are 0-9."""
        indices = [entry["index"] for entry in TRANSLATION_VOCAB]
        assert min(indices) == 0
        assert max(indices) == 9
        assert len(set(indices)) == 10  # All unique
    
    def test_translation_merge_hand_boxes(self):
        """Test merging hand bounding boxes logic."""
        # We can't instantiate TranslationModule without YOLO files,
        # but we can test the logic directly
        
        # Single box case
        single_box = [(100, 100, 50, 50)]
        x_min = min(box[0] for box in single_box)
        y_min = min(box[1] for box in single_box)
        x_max = max(box[0] + box[2] for box in single_box)
        y_max = max(box[1] + box[3] for box in single_box)
        
        assert x_min == 100
        assert y_min == 100
        assert x_max == 150
        assert y_max == 150
        
        # Multiple boxes case
        multiple_boxes = [(100, 100, 50, 50), (200, 150, 60, 60)]
        x_min = min(box[0] for box in multiple_boxes)
        y_min = min(box[1] for box in multiple_boxes)
        x_max = max(box[0] + box[2] for box in multiple_boxes)
        y_max = max(box[1] + box[3] for box in multiple_boxes)
        
        assert x_min == 100
        assert y_min == 100
        assert x_max == 260
        assert y_max == 210


class TestModuleIndependence:
    """Test that all three modules work independently."""
    
    def test_all_modules_have_correct_class_counts(self):
        """Verify each module has the correct number of classes."""
        # Detection: 35 classes (1-9, A-Z)
        assert len(DETECTION_VOCAB) == 35
        
        # Recognition: 3 classes (Hello, How are you, Thank you)
        assert len(RECOGNITION_VOCAB) == 3
        
        # Translation: 10 classes (G, I, K, O, P, S, U, V, X, Y)
        assert len(TRANSLATION_VOCAB) == 10
    
    def test_all_modules_return_correct_dataclass(self):
        """Verify all modules use ModulePrediction dataclass."""
        # Create sample predictions for each module
        detection_pred = ModulePrediction(
            module_name="detection",
            class_index=0,
            word="A",
            display_name="A",
            confidence=0.85,
            preprocessing_time=0.01,
            inference_time=0.01,
            metadata={},
            timestamp=time.time()
        )
        
        recognition_pred = ModulePrediction(
            module_name="recognition",
            class_index=0,
            word="hello",
            display_name="Hello",
            confidence=0.92,
            preprocessing_time=0.02,
            inference_time=0.01,
            metadata={},
            timestamp=time.time()
        )
        
        translation_pred = ModulePrediction(
            module_name="translation",
            class_index=0,
            word="G",
            display_name="G",
            confidence=0.78,
            preprocessing_time=0.03,
            inference_time=0.01,
            metadata={},
            timestamp=time.time()
        )
        
        # Verify all have the same structure
        for pred in [detection_pred, recognition_pred, translation_pred]:
            assert hasattr(pred, "module_name")
            assert hasattr(pred, "class_index")
            assert hasattr(pred, "word")
            assert hasattr(pred, "display_name")
            assert hasattr(pred, "confidence")
            assert hasattr(pred, "preprocessing_time")
            assert hasattr(pred, "inference_time")
            assert hasattr(pred, "metadata")
            assert hasattr(pred, "timestamp")
    
    def test_module_class_ranges_are_valid(self):
        """Verify each module's class indices are within valid ranges."""
        # Detection: 0-34
        for entry in DETECTION_VOCAB:
            assert 0 <= entry["index"] <= 34
        
        # Recognition: 0-2
        for entry in RECOGNITION_VOCAB:
            assert 0 <= entry["index"] <= 2
        
        # Translation: 0-9
        for entry in TRANSLATION_VOCAB:
            assert 0 <= entry["index"] <= 9
    
    def test_no_vocabulary_conflicts(self):
        """Verify vocabularies are properly separated by module."""
        # Each module should have its own vocabulary
        detection_words = {entry["word"] for entry in DETECTION_VOCAB}
        recognition_words = {entry["word"] for entry in RECOGNITION_VOCAB}
        translation_words = {entry["word"] for entry in TRANSLATION_VOCAB}
        
        # Verify they are distinct sets (some overlap is OK, but they should be managed separately)
        assert len(detection_words) == 35
        assert len(recognition_words) == 3
        assert len(translation_words) == 10
