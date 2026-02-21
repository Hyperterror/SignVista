"""
Unit tests for inference engine multi-module orchestration.

Tests the execute_modules_parallel, select_final_prediction, and
predict_from_raw_frame functions with multi-module support.
"""

import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from ml.inference import (
    execute_modules_parallel,
    select_final_prediction,
    predict_from_raw_frame,
)
from ml.modules import ModulePrediction
from ml.config_manager import ConfigurationManager, ModuleConfig


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager."""
    config_mgr = Mock(spec=ConfigurationManager)
    
    # Default configuration
    config_mgr.get_confidence_threshold.side_effect = lambda module: {
        "detection": 0.7,
        "recognition": 0.6,
        "translation": 0.7
    }.get(module, 0.7)
    
    config_mgr.get_prediction_strategy.return_value = "priority"
    
    config_mgr.get_module_config.side_effect = lambda module: ModuleConfig(
        enabled=True,
        priority={"detection": 2, "recognition": 1, "translation": 3}.get(module, 999),
        confidence_threshold=0.7,
        model_path="",
        preprocessing_params={}
    )
    
    return config_mgr


@pytest.fixture
def sample_predictions():
    """Create sample predictions for testing."""
    return [
        ModulePrediction(
            module_name="detection",
            class_index=0,
            word="A",
            display_name="A",
            confidence=0.85,
            preprocessing_time=0.015,
            inference_time=0.008,
            metadata={},
            timestamp=time.time()
        ),
        ModulePrediction(
            module_name="recognition",
            class_index=0,
            word="hello",
            display_name="Hello",
            confidence=0.92,
            preprocessing_time=0.023,
            inference_time=0.012,
            metadata={},
            timestamp=time.time()
        )
    ]



@pytest.fixture
def sample_frame():
    """Create a sample frame for testing."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


# ─── Tests for select_final_prediction ────────────────────────────────


def test_select_final_prediction_priority_strategy(sample_predictions, mock_config_manager):
    """Test priority-based selection strategy."""
    with patch('ml.inference._config_manager', mock_config_manager):
        selected = select_final_prediction(sample_predictions, "priority")
        
        # Recognition has priority 1 (highest), should be selected
        assert selected is not None
        assert selected.module_name == "recognition"
        assert selected.word == "hello"


def test_select_final_prediction_highest_confidence(sample_predictions):
    """Test highest confidence selection strategy."""
    selected = select_final_prediction(sample_predictions, "highest_confidence")
    
    # Recognition has confidence 0.92 (highest), should be selected
    assert selected is not None
    assert selected.module_name == "recognition"
    assert selected.confidence == 0.92


def test_select_final_prediction_voting_strategy(sample_predictions):
    """Test voting selection strategy."""
    # Add another prediction for "A" to create a tie
    sample_predictions.append(
        ModulePrediction(
            module_name="translation",
            class_index=0,
            word="A",
            display_name="A",
            confidence=0.80,
            preprocessing_time=0.020,
            inference_time=0.010,
            metadata={},
            timestamp=time.time()
        )
    )
    
    selected = select_final_prediction(sample_predictions, "voting")
    
    # "A" has 2 votes, should be selected (detection + translation)
    assert selected is not None
    assert selected.word == "A"


def test_select_final_prediction_empty_list():
    """Test selection with empty predictions list."""
    selected = select_final_prediction([], "priority")
    assert selected is None


def test_select_final_prediction_single_prediction(sample_predictions):
    """Test selection with single prediction."""
    single = [sample_predictions[0]]
    selected = select_final_prediction(single, "priority")
    
    assert selected is not None
    assert selected.module_name == "detection"


def test_select_final_prediction_unknown_strategy(sample_predictions):
    """Test selection with unknown strategy falls back to highest_confidence."""
    selected = select_final_prediction(sample_predictions, "unknown_strategy")
    
    # Should fall back to highest confidence
    assert selected is not None
    assert selected.module_name == "recognition"


# ─── Tests for execute_modules_parallel ───────────────────────────────


@patch('ml.inference._detection_module')
@patch('ml.inference._recognition_module')
@patch('ml.inference._translation_module')
@patch('ml.inference._config_manager')
def test_execute_modules_parallel_all_enabled(
    mock_config, mock_translation, mock_recognition, mock_detection, 
    sample_frame, sample_predictions
):
    """Test executing all enabled modules."""
    # Setup mocks
    mock_config.get_confidence_threshold.side_effect = lambda m: 0.5
    mock_detection.predict.return_value = sample_predictions[0]
    mock_recognition.predict.return_value = sample_predictions[1]
    mock_translation.predict.return_value = None  # Below threshold
    
    # Execute
    predictions = execute_modules_parallel(
        sample_frame, 
        "test_session", 
        ["detection", "recognition", "translation"]
    )
    
    # Verify
    assert len(predictions) == 2  # Only detection and recognition above threshold
    assert predictions[0].module_name == "detection"
    assert predictions[1].module_name == "recognition"


@patch('ml.inference._detection_module')
@patch('ml.inference._config_manager')
def test_execute_modules_parallel_single_module(
    mock_config, mock_detection, sample_frame, sample_predictions
):
    """Test executing single module."""
    mock_config.get_confidence_threshold.return_value = 0.5
    mock_detection.predict.return_value = sample_predictions[0]
    
    predictions = execute_modules_parallel(
        sample_frame, 
        "test_session", 
        ["detection"]
    )
    
    assert len(predictions) == 1
    assert predictions[0].module_name == "detection"


@patch('ml.inference._detection_module')
@patch('ml.inference._recognition_module')
@patch('ml.inference._config_manager')
def test_execute_modules_parallel_module_failure_isolation(
    mock_config, mock_recognition, mock_detection, sample_frame, sample_predictions
):
    """Test that module failures are isolated and don't affect other modules."""
    mock_config.get_confidence_threshold.return_value = 0.5
    
    # Detection fails
    mock_detection.predict.side_effect = Exception("Detection failed")
    
    # Recognition succeeds
    mock_recognition.predict.return_value = sample_predictions[1]
    
    predictions = execute_modules_parallel(
        sample_frame, 
        "test_session", 
        ["detection", "recognition"]
    )
    
    # Should still get recognition prediction despite detection failure
    assert len(predictions) == 1
    assert predictions[0].module_name == "recognition"


@patch('ml.inference._detection_module')
@patch('ml.inference._config_manager')
def test_execute_modules_parallel_below_threshold(
    mock_config, mock_detection, sample_frame, sample_predictions
):
    """Test that predictions below threshold are filtered out."""
    mock_config.get_confidence_threshold.return_value = 0.95  # High threshold
    mock_detection.predict.return_value = sample_predictions[0]  # confidence 0.85
    
    predictions = execute_modules_parallel(
        sample_frame, 
        "test_session", 
        ["detection"]
    )
    
    # Should be empty because confidence 0.85 < threshold 0.95
    assert len(predictions) == 0


# ─── Tests for predict_from_raw_frame ─────────────────────────────────


@patch('ml.inference.detect_face')
@patch('ml.inference._isl_modules_initialized', True)
@patch('ml.inference._config_manager')
@patch('ml.inference.execute_modules_parallel')
@patch('ml.inference.select_final_prediction')
def test_predict_from_raw_frame_with_module_details(
    mock_select, mock_execute, mock_config, mock_detect_face, 
    sample_frame, sample_predictions
):
    """Test predict_from_raw_frame returns module details when requested."""
    # Setup mocks
    mock_detect_face.return_value = True
    mock_config.is_module_enabled.return_value = True
    mock_config.get_prediction_strategy.return_value = "priority"
    mock_execute.return_value = sample_predictions
    mock_select.return_value = sample_predictions[1]  # Recognition selected
    
    # Execute
    word, confidence, status, results, module_details = predict_from_raw_frame(
        "test_session",
        sample_frame,
        return_landmarks=False,
        return_module_details=True
    )
    
    # Verify
    assert word == "hello"
    assert confidence == 0.92
    assert status == "ready"
    assert module_details is not None
    assert "active_modules" in module_details
    assert "predictions" in module_details
    assert "selected" in module_details
    assert module_details["selected"]["module"] == "recognition"


@patch('ml.inference.detect_face')
def test_predict_from_raw_frame_no_face(sample_frame):
    """Test predict_from_raw_frame returns no_face when no face detected."""
    with patch('ml.inference.detect_face', return_value=False):
        word, confidence, status, results, module_details = predict_from_raw_frame(
            "test_session",
            sample_frame,
            return_landmarks=False,
            return_module_details=False
        )
        
        assert word is None
        assert confidence == 0.0
        assert status == "no_face"


@patch('ml.inference.detect_face')
@patch('ml.inference._isl_modules_initialized', True)
@patch('ml.inference._config_manager')
@patch('ml.inference.execute_modules_parallel')
def test_predict_from_raw_frame_low_confidence(
    mock_execute, mock_config, mock_detect_face, sample_frame
):
    """Test predict_from_raw_frame returns low_confidence when no predictions above threshold."""
    mock_detect_face.return_value = True
    mock_config.is_module_enabled.return_value = True
    mock_execute.return_value = []  # No predictions above threshold
    
    word, confidence, status, results, module_details = predict_from_raw_frame(
        "test_session",
        sample_frame,
        return_landmarks=False,
        return_module_details=True
    )
    
    assert word is None
    assert confidence == 0.0
    assert status == "low_confidence"


@patch('ml.inference.detect_face')
@patch('ml.inference._isl_modules_initialized', False)
@patch('ml.inference._config_manager')
@patch('ml.inference._model_loaded', True)
@patch('ml.inference._model')
@patch('ml.inference.extract_keypoints')
@patch('ml.inference.get_buffer')
@patch('ml.inference.get_word_by_index')
def test_predict_from_raw_frame_fallback_to_lstm(
    mock_get_word, mock_get_buffer, mock_extract, mock_model,
    mock_config, mock_detect_face, sample_frame
):
    """Test predict_from_raw_frame falls back to LSTM when ISL modules unavailable."""
    # Setup mocks
    mock_detect_face.return_value = True
    mock_config.config.fallback_to_existing_lstm = True
    
    # Mock keypoint extraction
    mock_extract.return_value = (np.zeros(258), None)
    
    # Mock buffer
    mock_buffer = Mock()
    mock_buffer.is_ready = True
    mock_buffer.get_sequence.return_value = np.zeros((1, 45, 258))
    mock_get_buffer.return_value = mock_buffer
    
    # Mock model prediction
    mock_model.predict.return_value = np.array([[0.1, 0.2, 0.95]])
    mock_get_word.return_value = "thank_you"
    
    # Execute
    word, confidence, status, results, module_details = predict_from_raw_frame(
        "test_session",
        sample_frame,
        return_landmarks=False,
        return_module_details=False
    )
    
    # Verify fallback to LSTM
    assert word == "thank_you"
    assert confidence == 0.95
    assert status == "ready"
