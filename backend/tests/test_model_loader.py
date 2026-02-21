"""
Tests for ModelLoader module.

Tests both unit test cases and property-based tests for model loading,
validation, and GPU acceleration.
"""

import pytest
import numpy as np
import os
from unittest.mock import Mock, patch, MagicMock
from backend.ml.model_loader import ModelLoader


class TestModelLoaderUnit:
    """Unit tests for ModelLoader."""
    
    @pytest.fixture
    def model_loader(self):
        """Create ModelLoader instance for testing."""
        return ModelLoader(base_path="ISL-Unified-Project/models/")
    
    def test_initialization(self, model_loader):
        """Test ModelLoader initializes with correct base path."""
        assert model_loader.base_path == "ISL-Unified-Project/models/"
        assert model_loader.models == {}
        assert model_loader.model_info == {}
        assert model_loader._gpu_available is None
    
    def test_get_model_returns_none_when_not_loaded(self, model_loader):
        """Test get_model returns None for unloaded models."""
        assert model_loader.get_model("detection") is None
        assert model_loader.get_model("recognition") is None
        assert model_loader.get_model("translation") is None
    
    def test_get_model_info_returns_not_loaded(self, model_loader):
        """Test get_model_info returns loaded=False for unloaded models."""
        info = model_loader.get_model_info("detection")
        assert info == {"loaded": False}
    
    @patch('backend.ml.model_loader._import_tensorflow')
    def test_check_gpu_availability_with_gpu(self, mock_tf_import, model_loader):
        """Test GPU detection when GPU is available."""
        mock_tf = Mock()
        mock_gpu = Mock()
        mock_tf.config.list_physical_devices.return_value = [mock_gpu]
        mock_tf.config.experimental.set_memory_growth = Mock()
        mock_tf_import.return_value = mock_tf
        
        result = model_loader._check_gpu_availability()
        
        assert result is True
        assert model_loader._gpu_available is True
        mock_tf.config.list_physical_devices.assert_called_once_with('GPU')
    
    @patch('backend.ml.model_loader._import_tensorflow')
    def test_check_gpu_availability_without_gpu(self, mock_tf_import, model_loader):
        """Test GPU detection when no GPU is available."""
        mock_tf = Mock()
        mock_tf.config.list_physical_devices.return_value = []
        mock_tf_import.return_value = mock_tf
        
        result = model_loader._check_gpu_availability()
        
        assert result is False
        assert model_loader._gpu_available is False
    
    @patch('os.path.exists')
    def test_load_detection_model_missing_file(self, mock_exists, model_loader):
        """Test load_detection_model logs warning when file missing."""
        mock_exists.return_value = False
        
        result = model_loader.load_detection_model()
        
        assert result is None
        assert "detection" not in model_loader.models
    
    @patch('os.path.exists')
    def test_load_recognition_model_missing_file(self, mock_exists, model_loader):
        """Test load_recognition_model logs warning when file missing."""
        mock_exists.return_value = False
        
        result = model_loader.load_recognition_model()
        
        assert result is None
        assert "recognition" not in model_loader.models
    
    @patch('os.path.exists')
    def test_load_translation_model_missing_file(self, mock_exists, model_loader):
        """Test load_translation_model logs warning when file missing."""
        mock_exists.return_value = False
        
        result = model_loader.load_translation_model()
        
        assert result is None
        assert "translation" not in model_loader.models
    
    @patch('os.path.exists')
    def test_load_yolo_detector_missing_config(self, mock_exists, model_loader):
        """Test load_yolo_detector logs warning when config missing."""
        mock_exists.side_effect = lambda path: False if 'cfg' in path else True
        
        result = model_loader.load_yolo_detector()
        
        assert result is None
        assert "yolo" not in model_loader.models
    
    @patch('os.path.exists')
    def test_load_yolo_detector_missing_weights(self, mock_exists, model_loader):
        """Test load_yolo_detector logs warning when weights missing."""
        mock_exists.side_effect = lambda path: False if 'weights' in path else True
        
        result = model_loader.load_yolo_detector()
        
        assert result is None
        assert "yolo" not in model_loader.models
    
    def test_validate_model_with_none_output(self, model_loader):
        """Test validate_model returns False when model output is None."""
        mock_model = Mock()
        mock_model.predict.return_value = None
        test_input = np.random.randn(1, 42)
        
        result = model_loader.validate_model(mock_model, test_input)
        
        assert result is False
    
    def test_validate_model_with_wrong_shape(self, model_loader):
        """Test validate_model returns False when output shape is wrong."""
        mock_model = Mock()
        mock_model.predict.return_value = np.random.randn(1, 10)
        test_input = np.random.randn(1, 42)
        
        result = model_loader.validate_model(
            mock_model, test_input, expected_shape=(1, 35)
        )
        
        assert result is False
    
    def test_validate_model_with_correct_shape(self, model_loader):
        """Test validate_model returns True when output shape is correct."""
        mock_model = Mock()
        # Simulate softmax output
        output = np.random.rand(1, 35)
        output = output / output.sum()  # Normalize to sum to 1
        mock_model.predict.return_value = output
        test_input = np.random.randn(1, 42)
        
        result = model_loader.validate_model(
            mock_model, test_input, expected_shape=(1, 35)
        )
        
        assert result is True
    
    def test_validate_model_exception_handling(self, model_loader):
        """Test validate_model handles exceptions gracefully."""
        mock_model = Mock()
        mock_model.predict.side_effect = Exception("Model error")
        test_input = np.random.randn(1, 42)
        
        result = model_loader.validate_model(mock_model, test_input)
        
        assert result is False
    
    @patch('backend.ml.model_loader.ModelLoader.load_detection_model')
    @patch('backend.ml.model_loader.ModelLoader.load_recognition_model')
    @patch('backend.ml.model_loader.ModelLoader.load_translation_model')
    def test_load_all_models_success(
        self, mock_trans, mock_recog, mock_detect, model_loader
    ):
        """Test load_all_models loads all enabled modules."""
        mock_detect.return_value = Mock()
        mock_recog.return_value = Mock()
        mock_trans.return_value = Mock()
        
        results = model_loader.load_all_models(
            ["detection", "recognition", "translation"]
        )
        
        assert results["detection"] is True
        assert results["recognition"] is True
        assert results["translation"] is True
        mock_detect.assert_called_once()
        mock_recog.assert_called_once()
        mock_trans.assert_called_once()
    
    @patch('backend.ml.model_loader.ModelLoader.load_detection_model')
    def test_load_all_models_partial_failure(self, mock_detect, model_loader):
        """Test load_all_models continues when some models fail."""
        mock_detect.return_value = None  # Simulate failure
        
        results = model_loader.load_all_models(["detection"])
        
        assert results["detection"] is False
    
    def test_get_health_status(self, model_loader):
        """Test get_health_status returns correct structure."""
        # Add a mock model
        model_loader.models["detection"] = Mock()
        model_loader.model_info["detection"] = {
            "path": "test/path",
            "loaded": True
        }
        model_loader._gpu_available = False
        
        status = model_loader.get_health_status()
        
        assert "models_loaded" in status
        assert "model_info" in status
        assert "gpu_available" in status
        assert "total_models" in status
        assert status["models_loaded"] == ["detection"]
        assert status["total_models"] == 1
        assert status["gpu_available"] is False


class TestModelLoaderIntegration:
    """Integration tests that require actual model files."""
    
    @pytest.fixture
    def model_loader(self):
        """Create ModelLoader instance for integration testing."""
        return ModelLoader(base_path="ISL-Unified-Project/models/")
    
    @pytest.mark.skipif(
        not os.path.exists("ISL-Unified-Project/models/detection/gesture_classifier.h5"),
        reason="Detection model file not available"
    )
    def test_load_detection_model_real(self, model_loader):
        """Test loading actual detection model if available."""
        model = model_loader.load_detection_model()
        
        if model is not None:
            assert "detection" in model_loader.models
            info = model_loader.get_model_info("detection")
            assert info["loaded"] is True
            assert info["num_classes"] == 35
            assert info["type"] == "FNN"
    
    @pytest.mark.skipif(
        not os.path.exists("ISL-Unified-Project/models/recognition/lstm_word_model.hdf5"),
        reason="Recognition model file not available"
    )
    def test_load_recognition_model_real(self, model_loader):
        """Test loading actual recognition model if available."""
        model = model_loader.load_recognition_model()
        
        if model is not None:
            assert "recognition" in model_loader.models
            info = model_loader.get_model_info("recognition")
            assert info["loaded"] is True
            assert info["num_classes"] == 3
            assert info["type"] == "LSTM"
    
    @pytest.mark.skipif(
        not os.path.exists("ISL-Unified-Project/models/translation/squeezenet_model"),
        reason="Translation model file not available"
    )
    def test_load_translation_model_real(self, model_loader):
        """Test loading actual translation model if available."""
        model = model_loader.load_translation_model()
        
        if model is not None:
            assert "translation" in model_loader.models
            info = model_loader.get_model_info("translation")
            assert info["loaded"] is True
            assert info["num_classes"] == 10
            assert info["type"] == "SqueezeNet"
    
    @pytest.mark.skipif(
        not (os.path.exists("ISL-Unified-Project/config/yolo/cross-hands.cfg") and
             os.path.exists("ISL-Unified-Project/config/yolo/cross-hands.weights")),
        reason="YOLO config or weights not available"
    )
    def test_load_yolo_detector_real(self, model_loader):
        """Test loading actual YOLO detector if available."""
        yolo = model_loader.load_yolo_detector()
        
        if yolo is not None:
            assert "yolo" in model_loader.models
            info = model_loader.get_model_info("yolo")
            assert info["loaded"] is True
            assert info["type"] == "YOLO-v3"
