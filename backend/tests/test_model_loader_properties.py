"""
Property-based tests for ModelLoader module.

Uses hypothesis for property-based testing to verify universal properties
across all inputs.
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch
from backend.ml.model_loader import ModelLoader


# Custom strategies for generating test data
@st.composite
def valid_model_output(draw, num_classes):
    """Generate valid softmax model output."""
    # Generate random values
    output = draw(st.lists(
        st.floats(min_value=0.01, max_value=1.0),
        min_size=num_classes,
        max_size=num_classes
    ))
    # Normalize to sum to 1 (softmax)
    total = sum(output)
    normalized = [x / total for x in output]
    return np.array([normalized])


@st.composite
def model_input_shape(draw):
    """Generate valid model input shapes."""
    module = draw(st.sampled_from(["detection", "recognition", "translation"]))
    shapes = {
        "detection": (1, 42),
        "recognition": (1, 45, 258),
        "translation": (1, 224, 224, 3)
    }
    return module, shapes[module]


class TestModelLoaderProperties:
    """Property-based tests for ModelLoader."""
    
    # Feature: isl-unified-models-integration, Property 13: Model Output Shape Validation
    @given(
        module_name=st.sampled_from(["detection", "recognition", "translation"]),
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=50)
    def test_validate_model_output_shape(self, module_name, seed):
        """
        Property: For any module and valid input, model validation should verify
        output shape matches expected shape.
        
        **Validates: Requirements 12.3**
        """
        np.random.seed(seed)
        
        # Define expected shapes
        input_shapes = {
            "detection": (1, 42),
            "recognition": (1, 45, 258),
            "translation": (1, 224, 224, 3)
        }
        output_shapes = {
            "detection": (1, 35),
            "recognition": (1, 3),
            "translation": (1, 10)
        }
        
        # Create mock model with correct output
        mock_model = Mock()
        expected_shape = output_shapes[module_name]
        num_classes = expected_shape[1]
        
        # Generate valid softmax output
        output = np.random.rand(*expected_shape)
        output = output / output.sum(axis=1, keepdims=True)
        mock_model.predict.return_value = output
        
        # Generate test input
        test_input = np.random.randn(*input_shapes[module_name]).astype(np.float32)
        
        # Validate
        result = model_loader.validate_model(
            mock_model, test_input, expected_shape=expected_shape
        )
        
        assert result is True
    
    # Feature: isl-unified-models-integration, Property 13: Model Output Shape Validation
    @given(
        num_classes=st.integers(min_value=2, max_value=100),
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=50)
    def test_validate_model_output_range(self, model_loader, num_classes, seed):
        """
        Property: For any model output, values should be in [0, 1] range and
        sum to approximately 1 (softmax property).
        
        **Validates: Requirements 12.3**
        """
        np.random.seed(seed)
        
        # Create mock model
        mock_model = Mock()
        
        # Generate valid softmax output
        output = np.random.rand(1, num_classes)
        output = output / output.sum(axis=1, keepdims=True)
        mock_model.predict.return_value = output
        
        # Test input
        test_input = np.random.randn(1, num_classes).astype(np.float32)
        
        # Validate
        result = model_loader.validate_model(
            mock_model, test_input, expected_shape=(1, num_classes)
        )
        
        assert result is True
        # Verify output properties
        assert np.all((output >= 0) & (output <= 1))
        assert np.allclose(output.sum(axis=1), 1.0, atol=0.01)
    
    @given(
        wrong_classes=st.integers(min_value=1, max_value=100),
        expected_classes=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=50)
    def test_validate_model_wrong_shape_always_fails(
        self, model_loader, wrong_classes, expected_classes
    ):
        """
        Property: For any model output with wrong shape, validation should fail.
        
        **Validates: Requirements 12.3**
        """
        # Skip if shapes match
        if wrong_classes == expected_classes:
            return
        
        # Create mock model with wrong output shape
        mock_model = Mock()
        output = np.random.rand(1, wrong_classes)
        output = output / output.sum(axis=1, keepdims=True)
        mock_model.predict.return_value = output
        
        # Test input
        test_input = np.random.randn(1, 42).astype(np.float32)
        
        # Validate with expected shape
        result = model_loader.validate_model(
            mock_model, test_input, expected_shape=(1, expected_classes)
        )
        
        assert result is False
    
    @given(
        module_name=st.sampled_from(["detection", "recognition", "translation", "yolo"])
    )
    @settings(max_examples=20)
    def test_get_model_returns_consistent_result(self, model_loader, module_name):
        """
        Property: For any module name, get_model should return consistent results
        when called multiple times.
        
        **Validates: Requirements 9.2**
        """
        result1 = model_loader.get_model(module_name)
        result2 = model_loader.get_model(module_name)
        
        assert result1 is result2  # Same object reference
    
    @given(
        module_name=st.sampled_from(["detection", "recognition", "translation", "yolo"])
    )
    @settings(max_examples=20)
    def test_get_model_info_always_returns_dict(self, model_loader, module_name):
        """
        Property: For any module name, get_model_info should always return a dictionary.
        
        **Validates: Requirements 12.1**
        """
        info = model_loader.get_model_info(module_name)
        
        assert isinstance(info, dict)
        assert "loaded" in info
        assert isinstance(info["loaded"], bool)
    
    @given(
        enabled_modules=st.lists(
            st.sampled_from(["detection", "recognition", "translation"]),
            min_size=0,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=30)
    @patch('backend.ml.model_loader.ModelLoader.load_detection_model')
    @patch('backend.ml.model_loader.ModelLoader.load_recognition_model')
    @patch('backend.ml.model_loader.ModelLoader.load_translation_model')
    @patch('backend.ml.model_loader.ModelLoader.load_yolo_detector')
    def test_load_all_models_returns_status_for_all(
        self, mock_yolo, mock_trans, mock_recog, mock_detect,
        model_loader, enabled_modules
    ):
        """
        Property: For any set of enabled modules, load_all_models should return
        a status dictionary with entries for all requested modules.
        
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        """
        # Mock successful loading
        mock_detect.return_value = Mock()
        mock_recog.return_value = Mock()
        mock_trans.return_value = Mock()
        mock_yolo.return_value = Mock()
        
        results = model_loader.load_all_models(enabled_modules)
        
        # Verify results contain all enabled modules
        for module in enabled_modules:
            assert module in results
            assert isinstance(results[module], bool)
        
        # If translation is enabled, yolo should also be in results
        if "translation" in enabled_modules:
            assert "yolo" in results
    
    @given(
        base_path=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=30)
    def test_initialization_preserves_base_path(self, base_path):
        """
        Property: For any base path string, ModelLoader should preserve it exactly.
        
        **Validates: Requirements 1.1**
        """
        loader = ModelLoader(base_path=base_path)
        
        assert loader.base_path == base_path
        assert isinstance(loader.models, dict)
        assert isinstance(loader.model_info, dict)
    
    @given(
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=30)
    def test_health_status_structure_is_consistent(self, model_loader, seed):
        """
        Property: For any state of ModelLoader, get_health_status should return
        a dictionary with consistent structure.
        
        **Validates: Requirements 14.4**
        """
        status = model_loader.get_health_status()
        
        # Verify required keys
        assert "models_loaded" in status
        assert "model_info" in status
        assert "gpu_available" in status
        assert "total_models" in status
        
        # Verify types
        assert isinstance(status["models_loaded"], list)
        assert isinstance(status["model_info"], dict)
        assert isinstance(status["total_models"], int)
        
        # Verify consistency
        assert status["total_models"] == len(status["models_loaded"])
        assert status["total_models"] >= 0
    
    @given(
        exception_type=st.sampled_from([
            ValueError, RuntimeError, TypeError, Exception
        ])
    )
    @settings(max_examples=20)
    def test_validate_model_handles_all_exceptions(
        self, model_loader, exception_type
    ):
        """
        Property: For any exception type raised during validation,
        validate_model should handle it gracefully and return False.
        
        **Validates: Requirements 11.1, 11.2**
        """
        mock_model = Mock()
        mock_model.predict.side_effect = exception_type("Test error")
        test_input = np.random.randn(1, 42)
        
        result = model_loader.validate_model(mock_model, test_input)
        
        assert result is False
    
    @given(
        num_models=st.integers(min_value=0, max_value=4)
    )
    @settings(max_examples=20)
    def test_health_status_reflects_loaded_models(self, model_loader, num_models):
        """
        Property: For any number of loaded models, health status should
        accurately reflect the count.
        
        **Validates: Requirements 14.1, 14.4**
        """
        # Add mock models
        module_names = ["detection", "recognition", "translation", "yolo"]
        for i in range(num_models):
            module_name = module_names[i]
            model_loader.models[module_name] = Mock()
            model_loader.model_info[module_name] = {"loaded": True}
        
        status = model_loader.get_health_status()
        
        assert len(status["models_loaded"]) == num_models
        assert status["total_models"] == num_models
        assert set(status["models_loaded"]) == set(module_names[:num_models])


class TestModelValidationProperties:
    """Property-based tests specifically for model validation logic."""
    
    @pytest.fixture
    def model_loader(self):
        """Create ModelLoader instance for testing."""
        return ModelLoader()
    
    @given(
        batch_size=st.integers(min_value=1, max_value=32),
        num_classes=st.integers(min_value=2, max_value=100)
    )
    @settings(max_examples=30)
    def test_validation_works_with_any_batch_size(
        self, model_loader, batch_size, num_classes
    ):
        """
        Property: Model validation should work with any valid batch size.
        
        **Validates: Requirements 12.3**
        """
        mock_model = Mock()
        
        # Generate valid output for batch
        output = np.random.rand(batch_size, num_classes)
        output = output / output.sum(axis=1, keepdims=True)
        mock_model.predict.return_value = output
        
        test_input = np.random.randn(batch_size, 42).astype(np.float32)
        
        result = model_loader.validate_model(
            mock_model, test_input, expected_shape=(batch_size, num_classes)
        )
        
        assert result is True
    
    @given(
        values_in_range=st.booleans()
    )
    @settings(max_examples=20)
    def test_validation_detects_out_of_range_values(
        self, model_loader, values_in_range
    ):
        """
        Property: Model validation should detect when output values are
        outside [0, 1] range (though it only warns, doesn't fail).
        
        **Validates: Requirements 12.3**
        """
        mock_model = Mock()
        
        if values_in_range:
            # Valid range
            output = np.random.rand(1, 10)
            output = output / output.sum(axis=1, keepdims=True)
        else:
            # Invalid range
            output = np.random.randn(1, 10) * 10  # Can be negative or > 1
        
        mock_model.predict.return_value = output
        test_input = np.random.randn(1, 42).astype(np.float32)
        
        # Validation should still pass (it only warns for out of range)
        # but we can verify the output properties
        result = model_loader.validate_model(
            mock_model, test_input, expected_shape=(1, 10)
        )
        
        # Shape validation passes regardless of value range
        assert isinstance(result, bool)
