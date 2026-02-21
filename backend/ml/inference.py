"""
SignVista ML Inference Engine

Main orchestrator that ties together:
1. Face detection (gate)
2. Keypoint extraction (Mediapipe Holistic - 258 features)
3. Frame buffering (45-frame window)
4. LSTM prediction (Keras/TensorFlow)
5. Multi-module ISL integration (detection, recognition, translation)
"""

import logging
import os
import time
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

from app.config import settings
from ml.buffer_manager import get_buffer
from ml.face_detector import detect_face
from ml.keypoint_extractor import extract_keypoints
from ml.vocabulary import (
    NUM_CLASSES,
    get_word_by_index,
)
from ml.config_manager import ConfigurationManager
from ml.model_loader import ModelLoader
from ml.modules import ModulePrediction
from ml.modules.detection import DetectionModule
from ml.modules.recognition import RecognitionModule
from ml.modules.translation import TranslationModule

logger = logging.getLogger(__name__)

# ─── Global Model Instance ────────────────────────────────────────

_model = None
_model_loaded: bool = False

# ─── ISL Multi-Module Instances ───────────────────────────────────

_config_manager: Optional[ConfigurationManager] = None
_model_loader: Optional[ModelLoader] = None
_detection_module: Optional[DetectionModule] = None
_recognition_module: Optional[RecognitionModule] = None
_translation_module: Optional[TranslationModule] = None
_isl_modules_initialized: bool = False

def create_lstm_model(num_classes: int):
    """Manually define the Keras LSTM architecture to match weights."""
    model = Sequential([
        LSTM(64, return_sequences=True, activation='relu', input_shape=(45, 258)),
        LSTM(128, return_sequences=True, activation='relu'),
        LSTM(64, return_sequences=False, activation='relu'),
        Dense(64, activation='relu'),
        Dense(32, activation='relu'),
        Dense(num_classes, activation='softmax')
    ])
    return model

def initialize_model():
    """Load the Keras LSTM model weights at startup."""
    global _model, _model_loaded

    model_path = settings.MODEL_PATH
    if not os.path.exists(model_path):
        logger.warning(f"⚠️ Model weights not found at {model_path}")
        return

    try:
        # Create architecture (3 classes for "Hello", "How are you", "Thank you")
        _model = create_lstm_model(num_classes=NUM_CLASSES)
        _model.load_weights(model_path)
        _model_loaded = True
        logger.info(f"✅ Keras LSTM weights loaded from {model_path}")
    except Exception as e:
        logger.error(f"❌ Failed to load Keras model: {e}")
        _model = None
        _model_loaded = False

def is_model_loaded() -> bool:
    return _model_loaded

def initialize_isl_modules():
    """
    Initialize ISL Unified Project modules (detection, recognition, translation).
    
    This function:
    1. Loads configuration from file/environment
    2. Loads models for enabled modules
    3. Initializes module instances
    4. Handles missing models gracefully
    """
    global _config_manager, _model_loader
    global _detection_module, _recognition_module, _translation_module
    global _isl_modules_initialized
    
    try:
        # Initialize configuration manager
        _config_manager = ConfigurationManager()
        is_valid, errors = _config_manager.validate()
        
        if not is_valid:
            logger.warning(f"⚠️ Configuration validation errors: {errors}")
            logger.info("Continuing with available configuration...")
        
        # Initialize model loader
        _model_loader = ModelLoader()
        
        # Get enabled modules
        enabled_modules = [
            name for name in ["detection", "recognition", "translation"]
            if _config_manager.is_module_enabled(name)
        ]
        
        if not enabled_modules:
            logger.info("ℹ️ No ISL modules enabled in configuration")
            _isl_modules_initialized = True
            return
        
        logger.info(f"📦 Loading ISL modules: {enabled_modules}")
        
        # Load models for enabled modules
        load_results = _model_loader.load_all_models(enabled_modules)
        
        # Initialize detection module
        if _config_manager.is_module_enabled("detection") and load_results.get("detection"):
            try:
                detection_model = _model_loader.get_model("detection")
                detection_config = _config_manager.get_module_config("detection")
                _detection_module = DetectionModule(
                    model=detection_model,
                    config=detection_config.preprocessing_params
                )
                logger.info("✅ Detection module initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize detection module: {e}")
        
        # Initialize recognition module
        if _config_manager.is_module_enabled("recognition") and load_results.get("recognition"):
            try:
                recognition_model = _model_loader.get_model("recognition")
                recognition_config = _config_manager.get_module_config("recognition")
                _recognition_module = RecognitionModule(
                    model=recognition_model,
                    config=recognition_config.preprocessing_params,
                    buffer_manager=None  # Will use global buffer manager
                )
                logger.info("✅ Recognition module initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize recognition module: {e}")
        
        # Initialize translation module
        if _config_manager.is_module_enabled("translation") and load_results.get("translation"):
            try:
                translation_model = _model_loader.get_model("translation")
                translation_config = _config_manager.get_module_config("translation")
                
                # Get YOLO paths from config
                yolo_config = "../ISL-Unified-Project/config/yolo/cross-hands.cfg"
                yolo_weights = "../ISL-Unified-Project/config/yolo/cross-hands.weights"
                
                _translation_module = TranslationModule(
                    model=translation_model,
                    yolo_config=yolo_config,
                    yolo_weights=yolo_weights,
                    config=translation_config.preprocessing_params
                )
                logger.info("✅ Translation module initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize translation module: {e}")
        
        _isl_modules_initialized = True
        logger.info("🎉 ISL modules initialization complete")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize ISL modules: {e}")
        _isl_modules_initialized = False

def are_isl_modules_initialized() -> bool:
    """Check if ISL modules have been initialized."""
    return _isl_modules_initialized

def get_isl_modules_status() -> Dict[str, Any]:
    """
    Get status information about ISL modules for health endpoint.
    
    Returns:
        Dictionary with module status, configuration, and health information
    """
    if not _isl_modules_initialized or _config_manager is None:
        return {
            "initialized": False,
            "enabled_modules": [],
            "configuration": {},
            "modules": {}
        }
    
    enabled_modules = [
        name for name in ["detection", "recognition", "translation"]
        if _config_manager.is_module_enabled(name)
    ]
    
    module_status = {}
    for module_name in ["detection", "recognition", "translation"]:
        is_enabled = _config_manager.is_module_enabled(module_name)
        module_instance = None
        
        if module_name == "detection":
            module_instance = _detection_module
        elif module_name == "recognition":
            module_instance = _recognition_module
        elif module_name == "translation":
            module_instance = _translation_module
        
        module_status[module_name] = {
            "enabled": is_enabled,
            "loaded": module_instance is not None,
            "confidence_threshold": _config_manager.get_confidence_threshold(module_name) if is_enabled else None,
            "priority": _config_manager.get_module_config(module_name).priority if is_enabled else None
        }
    
    return {
        "initialized": True,
        "enabled_modules": enabled_modules,
        "configuration": {
            "prediction_strategy": _config_manager.get_prediction_strategy(),
            "fallback_to_lstm": _config_manager.config.fallback_to_existing_lstm
        },
        "modules": module_status
    }

def execute_modules_parallel(
    frame: np.ndarray,
    session_id: str,
    enabled_modules: List[str]
) -> List[ModulePrediction]:
    """
    Execute all enabled modules and collect predictions.
    
    This function runs enabled modules sequentially (parallel execution can be
    added later) and collects predictions that exceed confidence thresholds.
    Preprocessing failures are isolated - if one module fails, others continue.
    
    Args:
        frame: Input frame (numpy array)
        session_id: Session identifier for buffer management
        enabled_modules: List of module names to execute
        
    Returns:
        List of ModulePrediction objects from successful modules
    """
    predictions = []
    
    # Execute detection module
    if "detection" in enabled_modules and _detection_module is not None:
        try:
            start_time = time.time()
            prediction = _detection_module.predict(frame)
            elapsed = time.time() - start_time
            
            if prediction is not None:
                threshold = _config_manager.get_confidence_threshold("detection")
                if prediction.confidence >= threshold:
                    predictions.append(prediction)
                    logger.debug(
                        f"Detection: {prediction.word} "
                        f"(conf={prediction.confidence:.3f}, time={elapsed:.3f}s)"
                    )
                else:
                    logger.debug(
                        f"Detection prediction below threshold: "
                        f"{prediction.confidence:.3f} < {threshold}"
                    )
        except Exception as e:
            logger.error(f"Detection module failed: {e}", exc_info=True)
            # Continue with other modules
    
    # Execute recognition module
    if "recognition" in enabled_modules and _recognition_module is not None:
        try:
            start_time = time.time()
            prediction = _recognition_module.predict(frame, session_id)
            elapsed = time.time() - start_time
            
            if prediction is not None:
                threshold = _config_manager.get_confidence_threshold("recognition")
                if prediction.confidence >= threshold:
                    predictions.append(prediction)
                    logger.debug(
                        f"Recognition: {prediction.word} "
                        f"(conf={prediction.confidence:.3f}, time={elapsed:.3f}s)"
                    )
                else:
                    logger.debug(
                        f"Recognition prediction below threshold: "
                        f"{prediction.confidence:.3f} < {threshold}"
                    )
        except Exception as e:
            logger.error(f"Recognition module failed: {e}", exc_info=True)
            # Continue with other modules
    
    # Execute translation module
    if "translation" in enabled_modules and _translation_module is not None:
        try:
            start_time = time.time()
            prediction = _translation_module.predict(frame)
            elapsed = time.time() - start_time
            
            if prediction is not None:
                threshold = _config_manager.get_confidence_threshold("translation")
                if prediction.confidence >= threshold:
                    predictions.append(prediction)
                    logger.debug(
                        f"Translation: {prediction.word} "
                        f"(conf={prediction.confidence:.3f}, time={elapsed:.3f}s)"
                    )
                else:
                    logger.debug(
                        f"Translation prediction below threshold: "
                        f"{prediction.confidence:.3f} < {threshold}"
                    )
        except Exception as e:
            logger.error(f"Translation module failed: {e}", exc_info=True)
            # Continue with other modules
    
    return predictions

def select_final_prediction(
    predictions: List[ModulePrediction],
    strategy: str
) -> Optional[ModulePrediction]:
    """
    Apply selection strategy to choose final prediction from multiple modules.
    
    Strategies:
    - "priority": Select from highest priority module (lowest priority number)
    - "highest_confidence": Select prediction with highest confidence
    - "voting": If multiple modules predict same word, boost confidence; 
                select by vote count then confidence
    
    Args:
        predictions: List of ModulePrediction objects
        strategy: Selection strategy name
        
    Returns:
        Selected ModulePrediction or None if no predictions
    """
    if not predictions:
        return None
    
    if len(predictions) == 1:
        return predictions[0]
    
    if strategy == "priority":
        # Get module priorities from config
        module_priorities = {}
        for pred in predictions:
            config = _config_manager.get_module_config(pred.module_name)
            if config:
                module_priorities[pred.module_name] = config.priority
            else:
                module_priorities[pred.module_name] = 999  # Low priority for unknown
        
        # Sort by priority (lower number = higher priority)
        sorted_preds = sorted(predictions, key=lambda p: module_priorities[p.module_name])
        selected = sorted_preds[0]
        logger.debug(f"Priority strategy selected: {selected.module_name} (priority={module_priorities[selected.module_name]})")
        return selected
    
    elif strategy == "highest_confidence":
        # Select prediction with highest confidence
        selected = max(predictions, key=lambda p: p.confidence)
        logger.debug(f"Highest confidence strategy selected: {selected.module_name} (conf={selected.confidence:.3f})")
        return selected
    
    elif strategy == "voting":
        # Count votes for each word
        word_votes: Dict[str, List[ModulePrediction]] = {}
        for pred in predictions:
            if pred.word not in word_votes:
                word_votes[pred.word] = []
            word_votes[pred.word].append(pred)
        
        # Find word with most votes
        max_votes = max(len(preds) for preds in word_votes.values())
        words_with_max_votes = [
            word for word, preds in word_votes.items() 
            if len(preds) == max_votes
        ]
        
        # If tie in votes, select by highest confidence
        if len(words_with_max_votes) == 1:
            word = words_with_max_votes[0]
            selected = max(word_votes[word], key=lambda p: p.confidence)
        else:
            # Multiple words with same vote count, select highest confidence overall
            selected = max(predictions, key=lambda p: p.confidence)
        
        logger.debug(
            f"Voting strategy selected: {selected.module_name} "
            f"(word={selected.word}, votes={len(word_votes[selected.word])}, conf={selected.confidence:.3f})"
        )
        return selected
    
    else:
        logger.warning(f"Unknown selection strategy: {strategy}, using highest_confidence")
        return max(predictions, key=lambda p: p.confidence)

def predict_from_raw_frame(
    session_id: str,
    frame: np.ndarray,
    return_landmarks: bool = False,
    return_module_details: bool = False
) -> Tuple[Optional[str], float, str, any, Optional[Dict[str, Any]]]:
    """
    Full inference pipeline: frame → prediction.
    
    Supports both legacy LSTM model and new ISL multi-module system.
    When ISL modules are available and enabled, uses multi-module orchestration.
    Falls back to existing LSTM model when ISL modules unavailable.
    
    Args:
        session_id: Session identifier for buffer management
        frame: Input frame (numpy array)
        return_landmarks: Whether to return MediaPipe landmarks
        return_module_details: Whether to return detailed module information
        
    Returns:
        Tuple of (word, confidence, status_message, results, module_details)
        - word: Predicted word or None
        - confidence: Confidence score (0.0 to 1.0)
        - status_message: Status string (e.g., "ready", "no_face", "collecting_50%")
        - results: MediaPipe results (if return_landmarks=True)
        - module_details: Dictionary with module information (if return_module_details=True)
    """
    module_details = None
    start_time = time.time()
    
    # 1. Face detection gate (optional based on configuration)
    require_face = True
    if _config_manager is not None:
        require_face = getattr(_config_manager.config, 'require_face_detection', True)
    
    if require_face and not detect_face(frame):
        return None, 0.0, "no_face", None, module_details

    # 2. Check if ISL modules are initialized and enabled
    if _isl_modules_initialized and _config_manager is not None:
        # Get enabled modules
        enabled_modules = [
            name for name in ["detection", "recognition", "translation"]
            if _config_manager.is_module_enabled(name)
        ]
        
        if enabled_modules:
            # Use ISL multi-module system
            try:
                # Execute all enabled modules
                predictions = execute_modules_parallel(frame, session_id, enabled_modules)
                
                # Track timing
                total_time = time.time() - start_time
                if total_time > 0.2:  # 200ms threshold
                    logger.warning(
                        f"⚠️ Frame processing exceeded 200ms: {total_time:.3f}s "
                        f"(modules: {enabled_modules})"
                    )
                
                # Prepare module details if requested
                if return_module_details:
                    module_details = {
                        "active_modules": enabled_modules,
                        "predictions": [
                            {
                                "module": pred.module_name,
                                "word": pred.word,
                                "display_name": pred.display_name,
                                "confidence": pred.confidence,
                                "class_index": pred.class_index
                            }
                            for pred in predictions
                        ],
                        "preprocessing_times": {
                            pred.module_name: pred.preprocessing_time
                            for pred in predictions
                        },
                        "inference_times": {
                            pred.module_name: pred.inference_time
                            for pred in predictions
                        },
                        "total_time": total_time
                    }
                
                # Select final prediction
                if predictions:
                    strategy = _config_manager.get_prediction_strategy()
                    selected = select_final_prediction(predictions, strategy)
                    
                    if selected:
                        if return_module_details and module_details:
                            module_details["selected"] = {
                                "module": selected.module_name,
                                "reason": f"strategy_{strategy}"
                            }
                        
                        return (
                            selected.word,
                            selected.confidence,
                            "ready",
                            None,
                            module_details
                        )
                else:
                    # No predictions above threshold
                    if return_module_details and module_details:
                        module_details["selected"] = None
                    
                    return None, 0.0, "low_confidence", None, module_details
                    
            except Exception as e:
                logger.error(f"ISL multi-module prediction failed: {e}", exc_info=True)
                # Fall through to legacy LSTM fallback
    
    # 3. Fallback to existing LSTM model
    if _config_manager and _config_manager.config.fallback_to_existing_lstm:
        logger.debug("Using fallback LSTM model")
        
        # Keypoint extraction
        keypoints, results = extract_keypoints(frame, return_results=return_landmarks)

        # Buffering
        buffer = get_buffer(session_id)
        buffer.append(keypoints)

        if not buffer.is_ready:
            progress = int(buffer.fill_ratio * 100)
            return None, 0.0, f"collecting_{progress}%", results, module_details

        # Prediction
        if not _model_loaded:
            # Fallback to mock for testing
            return "hello", 0.95, "mock_ready", results, module_details

        sequence = buffer.get_sequence()  # shape (1, 45, 258)
        res = _model.predict(sequence, verbose=0)[0]
        
        # Get highest probability
        prediction_idx = np.argmax(res)
        confidence = float(res[prediction_idx])
        word = get_word_by_index(prediction_idx)

        # Threshold & Reset
        if confidence < settings.CONFIDENCE_THRESHOLD:
            return None, confidence, "low_confidence", results, module_details

        # Success! Clear buffer to avoid rapid re-triggering of the same word
        buffer.clear()
        return word, confidence, "ready", results, module_details
    
    # No models available
    return None, 0.0, "no_model", None, module_details
