"""
Model Loader for ISL Unified Models Integration.

This module handles discovery, loading, validation, and management of ML model instances
for the detection, recognition, and translation modules.
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Lazy imports to avoid loading heavy dependencies at module level
_tf = None
_cv2 = None


def _import_tensorflow():
    """Lazy import TensorFlow."""
    global _tf
    if _tf is None:
        import tensorflow as tf
        _tf = tf
    return _tf


def _import_cv2():
    """Lazy import OpenCV."""
    global _cv2
    if _cv2 is None:
        import cv2
        _cv2 = cv2
    return _cv2


class ModelLoader:
    """
    Manages loading and validation of ISL Unified Project models.
    
    Supports:
    - Detection FNN model (gesture_classifier.h5)
    - Recognition LSTM model (lstm_word_model.hdf5)
    - Translation SqueezeNet model (squeezenet_model directory)
    - YOLO hand detector (cross-hands.cfg and weights)
    """
    
    def __init__(self, base_path: str = "../ISL-Unified-Project/models/"):
        """
        Initialize model loader.
        
        Args:
            base_path: Base directory containing model subdirectories
        """
        self.base_path = base_path
        self.models: Dict[str, Any] = {}
        self.model_info: Dict[str, Dict[str, Any]] = {}
        self._gpu_available = None
        
    def _check_gpu_availability(self) -> bool:
        """Check if GPU acceleration is available."""
        if self._gpu_available is not None:
            return self._gpu_available
            
        try:
            tf = _import_tensorflow()
            gpus = tf.config.list_physical_devices('GPU')
            self._gpu_available = len(gpus) > 0
            if self._gpu_available:
                logger.info(f"✅ GPU acceleration available: {len(gpus)} GPU(s) detected")
                # Enable memory growth to avoid OOM errors
                for gpu in gpus:
                    try:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    except RuntimeError as e:
                        logger.warning(f"Could not set memory growth for GPU: {e}")
            else:
                logger.info("ℹ️ No GPU detected, using CPU for inference")
        except Exception as e:
            logger.warning(f"Error checking GPU availability: {e}")
            self._gpu_available = False
            
        return self._gpu_available
    
    def load_detection_model(self) -> Optional[Any]:
        """
        Load FNN gesture classifier for detection module.
        
        Returns:
            Loaded Keras model or None if loading fails
        """
        model_path = os.path.join(self.base_path, "detection", "gesture_classifier.h5").replace("\\", "/")
        
        if not os.path.exists(model_path):
            logger.warning(f"⚠️ Detection model not found at {model_path}")
            return None
        
        try:
            tf = _import_tensorflow()
            
            # Check GPU availability
            self._check_gpu_availability()
            
            # Load model
            model = tf.keras.models.load_model(model_path)
            
            # Validate model
            test_input = np.random.randn(1, 42).astype(np.float32)
            if not self.validate_model(model, test_input, expected_shape=(1, 35)):
                logger.error(f"❌ Detection model validation failed")
                return None
            
            self.models["detection"] = model
            self.model_info["detection"] = {
                "path": model_path,
                "input_shape": (1, 42),
                "output_shape": (1, 35),
                "num_classes": 35,
                "type": "FNN",
                "loaded": True
            }
            
            logger.info(f"✅ Detection model loaded from {model_path}")
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to load detection model: {e}")
            return None
    
    def load_recognition_model(self) -> Optional[Any]:
        """
        Load LSTM word recognition model.
        
        Returns:
            Loaded Keras model or None if loading fails
        """
        model_path = os.path.join(self.base_path, "recognition", "lstm_word_model.hdf5").replace("\\", "/")
        
        if not os.path.exists(model_path):
            logger.warning(f"⚠️ Recognition model not found at {model_path}")
            return None
        
        try:
            tf = _import_tensorflow()
            
            # Check GPU availability
            self._check_gpu_availability()
            
            # Load model
            model = tf.keras.models.load_model(model_path)
            
            # Validate model
            test_input = np.random.randn(1, 45, 258).astype(np.float32)
            if not self.validate_model(model, test_input, expected_shape=(1, 3)):
                logger.error(f"❌ Recognition model validation failed")
                return None
            
            self.models["recognition"] = model
            self.model_info["recognition"] = {
                "path": model_path,
                "input_shape": (1, 45, 258),
                "output_shape": (1, 3),
                "num_classes": 3,
                "type": "LSTM",
                "loaded": True
            }
            
            logger.info(f"✅ Recognition model loaded from {model_path}")
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to load recognition model: {e}")
            return None
    
    def load_translation_model(self) -> Optional[Any]:
        """
        Load SqueezeNet classifier for translation module.
        
        Returns:
            Loaded model or None if loading fails
        """
        model_path = os.path.join(self.base_path, "translation", "squeezenet_model").replace("\\", "/")
        
        if not os.path.exists(model_path):
            logger.warning(f"⚠️ Translation model not found at {model_path}")
            return None
        
        try:
            tf = _import_tensorflow()
            
            # Check GPU availability
            self._check_gpu_availability()
            
            # Load SavedModel format
            model = tf.keras.models.load_model(model_path)
            
            # Validate model
            test_input = np.random.randn(1, 224, 224, 3).astype(np.float32)
            if not self.validate_model(model, test_input, expected_shape=(1, 10)):
                logger.error(f"❌ Translation model validation failed")
                return None
            
            self.models["translation"] = model
            self.model_info["translation"] = {
                "path": model_path,
                "input_shape": (1, 224, 224, 3),
                "output_shape": (1, 10),
                "num_classes": 10,
                "type": "SqueezeNet",
                "loaded": True
            }
            
            logger.info(f"✅ Translation model loaded from {model_path}")
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to load translation model: {e}")
            return None
    
    def load_yolo_detector(
        self, 
        config_path: str = "../ISL-Unified-Project/config/yolo/cross-hands.cfg",
        weights_path: str = "../ISL-Unified-Project/config/yolo/cross-hands.weights"
    ) -> Optional[Any]:
        """
        Load YOLO hand detector using OpenCV DNN backend.
        
        Args:
            config_path: Path to YOLO configuration file
            weights_path: Path to YOLO weights file
            
        Returns:
            Loaded YOLO net or None if loading fails
        """
        if not os.path.exists(config_path):
            logger.warning(f"⚠️ YOLO config not found at {config_path}")
            return None
        
        if not os.path.exists(weights_path):
            logger.warning(f"⚠️ YOLO weights not found at {weights_path}")
            logger.info(f"ℹ️ YOLO weights file is large and may need to be downloaded separately")
            return None
        
        try:
            cv2 = _import_cv2()
            
            # Load YOLO using OpenCV DNN
            net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
            
            # Try to use GPU if available
            if self._check_gpu_availability():
                try:
                    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                    logger.info("✅ YOLO using GPU acceleration")
                except Exception as e:
                    logger.warning(f"Could not enable GPU for YOLO: {e}, using CPU")
                    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            else:
                net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            
            self.models["yolo"] = net
            self.model_info["yolo"] = {
                "config_path": config_path,
                "weights_path": weights_path,
                "type": "YOLO-v3",
                "loaded": True
            }
            
            logger.info(f"✅ YOLO detector loaded from {config_path}")
            return net
            
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO detector: {e}")
            return None
    
    def validate_model(
        self, 
        model: Any, 
        test_input: np.ndarray,
        expected_shape: Optional[Tuple[int, ...]] = None
    ) -> bool:
        """
        Validate model produces expected output shape.
        
        Args:
            model: Model to validate
            test_input: Test input array
            expected_shape: Expected output shape (optional)
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            output = model.predict(test_input, verbose=0)
            
            # Check output is not None
            if output is None:
                logger.error("Model validation failed: output is None")
                return False
            
            # Check output shape if specified
            if expected_shape is not None:
                if output.shape != expected_shape:
                    logger.error(
                        f"Model validation failed: expected shape {expected_shape}, "
                        f"got {output.shape}"
                    )
                    return False
            
            # Check output values are in valid range (for softmax outputs)
            if len(output.shape) == 2:  # Classification output
                if not np.all((output >= 0) & (output <= 1)):
                    logger.warning("Model output contains values outside [0, 1] range")
                
                # Check if probabilities sum to ~1 (softmax)
                row_sums = np.sum(output, axis=1)
                if not np.allclose(row_sums, 1.0, atol=0.01):
                    logger.warning(f"Model output probabilities don't sum to 1: {row_sums}")
            
            logger.debug(f"Model validation passed: output shape {output.shape}")
            return True
            
        except Exception as e:
            logger.error(f"Model validation failed with exception: {e}")
            return False
    
    def get_model(self, module_name: str) -> Optional[Any]:
        """
        Get loaded model by module name.
        
        Args:
            module_name: Name of module (detection, recognition, translation, yolo)
            
        Returns:
            Loaded model or None if not loaded
        """
        return self.models.get(module_name)
    
    def get_model_info(self, module_name: str) -> Dict[str, Any]:
        """
        Get metadata about loaded model.
        
        Args:
            module_name: Name of module
            
        Returns:
            Dictionary with model metadata
        """
        return self.model_info.get(module_name, {"loaded": False})
    
    def load_all_models(self, enabled_modules: list) -> Dict[str, bool]:
        """
        Load all models for enabled modules.
        
        Args:
            enabled_modules: List of module names to load
            
        Returns:
            Dictionary mapping module names to load success status
        """
        results = {}
        
        if "detection" in enabled_modules:
            model = self.load_detection_model()
            results["detection"] = model is not None
        
        if "recognition" in enabled_modules:
            model = self.load_recognition_model()
            results["recognition"] = model is not None
        
        if "translation" in enabled_modules:
            model = self.load_translation_model()
            results["translation"] = model is not None
            
            # Also load YOLO for translation module
            if results["translation"]:
                yolo = self.load_yolo_detector()
                results["yolo"] = yolo is not None
                if not results["yolo"]:
                    logger.warning(
                        "⚠️ Translation module loaded but YOLO detector unavailable. "
                        "Translation module may not work correctly."
                    )
        
        # Log summary
        loaded_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        logger.info(f"📊 Model loading summary: {loaded_count}/{total_count} models loaded successfully")
        
        return results
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all loaded models.
        
        Returns:
            Dictionary with health information
        """
        return {
            "models_loaded": list(self.models.keys()),
            "model_info": self.model_info,
            "gpu_available": self._gpu_available,
            "total_models": len(self.models)
        }
