"""
Detection Module for ISL Unified Models Integration.

This module implements MediaPipe Hands-based hand landmark extraction
with FNN classifier for gesture recognition (A-Z, 1-9) - 35 classes.

Features:
- 42-point hand landmark extraction (21 landmarks per hand, x and y coordinates)
- Relative coordinate conversion and normalization
- Stateless frame processing (no temporal buffering)
- Confidence threshold filtering
"""

import time
import logging
from typing import Optional, Dict, Any
import numpy as np

from . import ModulePrediction
from ..vocabulary import get_word_by_module_index, get_display_name

logger = logging.getLogger(__name__)

# Lazy imports to avoid loading heavy dependencies at module level
_mp = None
_hand_landmarker = None
_hand_landmarker_options = None


def _import_mediapipe():
    """Lazy import MediaPipe."""
    global _mp, _hand_landmarker, _hand_landmarker_options
    if _mp is None:
        import mediapipe as mp
        _mp = mp
        _hand_landmarker = mp.tasks.vision.HandLandmarker
        _hand_landmarker_options = mp.tasks.vision.HandLandmarkerOptions
    return _mp, _hand_landmarker, _hand_landmarker_options


class DetectionModule:
    """
    Detection module for gesture recognition using MediaPipe Hands + FNN classifier.
    
    Processes individual frames to detect hand landmarks and classify gestures
    into 35 classes (1-9, A-Z).
    """
    
    def __init__(self, model: Any, config: Dict[str, Any]):
        """
        Initialize detection module.
        
        Args:
            model: Loaded FNN gesture classifier (Keras model)
            config: Module configuration with preprocessing_params and confidence_threshold
        """
        self.model = model
        self.config = config
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        
        # Get preprocessing parameters
        preprocessing_params = config.get("preprocessing_params", {})
        self.max_num_hands = preprocessing_params.get("max_num_hands", 2)
        self.model_complexity = preprocessing_params.get("model_complexity", 0)
        self.min_detection_confidence = preprocessing_params.get("min_detection_confidence", 0.7)
        self.min_tracking_confidence = preprocessing_params.get("min_tracking_confidence", 0.7)
        
        # Temporal smoothing - track last N predictions
        self.prediction_history = []
        self.history_size = 3  # Smooth over last 3 predictions
        
        # Initialize MediaPipe Hands using new tasks API
        mp, hand_landmarker_class, hand_landmarker_options_class = _import_mediapipe()
        
        # Download hand landmarker model if not present
        import os
        import urllib.request
        
        model_dir = "backend/ml/models"
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "hand_landmarker.task")
        
        if not os.path.exists(model_path):
            logger.info("Downloading MediaPipe hand landmarker model...")
            model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            try:
                urllib.request.urlretrieve(model_url, model_path)
                logger.info(f"✅ Downloaded hand landmarker model to {model_path}")
            except Exception as e:
                logger.error(f"Failed to download hand landmarker model: {e}")
                raise
        
        # Create options
        base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
        options = hand_landmarker_options_class(
            base_options=base_options,
            num_hands=self.max_num_hands,
            min_hand_detection_confidence=self.min_detection_confidence,
            min_hand_presence_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        
        # Create hand landmarker
        self.hands = hand_landmarker_class.create_from_options(options)
        
        logger.info(
            f"✅ Detection module initialized "
            f"(max_hands={self.max_num_hands}, complexity={self.model_complexity})"
        )
    
    def predict(self, frame: np.ndarray) -> Optional[ModulePrediction]:
        """
        Process frame and return gesture prediction.
        
        Args:
            frame: Input frame as numpy array (H, W, 3) in BGR format
            
        Returns:
            ModulePrediction with gesture classification, or None if:
            - No hands detected
            - Confidence below threshold
            - Processing error
        """
        start_time = time.time()
        
        try:
            # Extract hand landmarks
            preprocessing_start = time.time()
            landmarks = self.extract_hand_landmarks(frame)
            preprocessing_time = time.time() - preprocessing_start
            
            if landmarks is None:
                logger.debug("No hands detected in frame")
                return None
            
            # Preprocess landmarks
            processed_landmarks = self.preprocess_landmarks(landmarks)
            
            # Run inference
            inference_start = time.time()
            predictions = self.model.predict(processed_landmarks, verbose=0)
            inference_time = time.time() - inference_start
            
            # Get top 3 predictions for analysis
            top_3_indices = np.argsort(predictions[0])[-3:][::-1]
            top_3_confidences = predictions[0][top_3_indices]
            
            # Get class with highest confidence
            class_index = int(top_3_indices[0])
            confidence = float(top_3_confidences[0])
            second_confidence = float(top_3_confidences[1]) if len(top_3_confidences) > 1 else 0.0
            
            # Confidence margin check - reject if top prediction is not significantly better
            confidence_margin = confidence - second_confidence
            if confidence_margin < 0.15:  # Top prediction must be at least 15% better
                logger.debug(
                    f"Detection: Top prediction {get_word_by_module_index('detection', class_index)} "
                    f"({confidence:.3f}) not significantly better than second "
                    f"({second_confidence:.3f}), margin={confidence_margin:.3f}"
                )
                return None
            
            # Apply confidence threshold
            if confidence < self.confidence_threshold:
                logger.info(
                    f"Detection: {display_name} with confidence {confidence:.3f} "
                    f"below threshold {self.confidence_threshold} - not returning"
                )
                return None
            
            # Map to word
            word = get_word_by_module_index("detection", class_index)
            display_name = get_display_name(word, "detection")
            
            # Add to prediction history for temporal smoothing
            self.prediction_history.append({
                "class_index": class_index,
                "confidence": confidence,
                "word": word
            })
            
            # Keep only last N predictions
            if len(self.prediction_history) > self.history_size:
                self.prediction_history.pop(0)
            
            # Temporal smoothing - require consistency
            if len(self.prediction_history) >= 2:
                # Check if recent predictions agree
                recent_words = [p["word"] for p in self.prediction_history[-2:]]
                if len(set(recent_words)) > 1:  # Predictions don't agree
                    logger.debug(
                        f"Detection: Inconsistent predictions {recent_words}, "
                        f"waiting for consistency"
                    )
                    return None
            
            logger.info(
                f"✅ Detection successful: {display_name} "
                f"(class_index={class_index}, confidence={confidence:.3f}, "
                f"margin={confidence_margin:.3f})"
            )
            
            # Create prediction
            prediction = ModulePrediction(
                module_name="detection",
                class_index=class_index,
                word=word,
                display_name=display_name,
                confidence=confidence,
                preprocessing_time=preprocessing_time,
                inference_time=inference_time,
                metadata={
                    "num_hands": len(landmarks) // 42,  # 42 features per hand
                    "raw_landmarks": landmarks.tolist()
                },
                timestamp=time.time()
            )
            
            logger.debug(
                f"Detection prediction: {display_name} "
                f"(confidence={confidence:.3f}, time={time.time()-start_time:.3f}s)"
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Detection module prediction failed: {e}", exc_info=True)
            return None
    
    def extract_hand_landmarks(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract 42-point hand landmarks using MediaPipe Hands.
        
        Args:
            frame: Input frame as numpy array (H, W, 3) in BGR format
            
        Returns:
            Numpy array of shape (42,) with [x1, y1, x2, y2, ..., x21, y21] for one hand,
            or None if no hands detected
        """
        try:
            # Convert BGR to RGB for MediaPipe
            import cv2
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create MediaPipe Image
            mp, _, _ = _import_mediapipe()
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Process frame
            results = self.hands.detect(mp_image)
            
            if not results.hand_landmarks or len(results.hand_landmarks) == 0:
                return None
            
            # Extract landmarks from first detected hand
            # MediaPipe returns 21 landmarks per hand with x, y, z coordinates
            # We only use x and y for 42 features
            hand_landmarks = results.hand_landmarks[0]
            
            landmarks = []
            for landmark in hand_landmarks:
                landmarks.append(landmark.x)
                landmarks.append(landmark.y)
            
            return np.array(landmarks, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Hand landmark extraction failed: {e}")
            return None
    
    def preprocess_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Convert to relative coordinates and normalize.
        
        Preprocessing steps:
        1. Convert to relative coordinates (subtract base point - wrist)
        2. Normalize by max absolute value
        3. Reshape to (1, 42) for model input
        
        Args:
            landmarks: Raw landmarks array of shape (42,)
            
        Returns:
            Preprocessed landmarks array of shape (1, 42)
        """
        # Make a copy to avoid modifying original
        processed = landmarks.copy()
        
        # Extract wrist coordinates (first landmark, indices 0 and 1)
        wrist_x = processed[0]
        wrist_y = processed[1]
        
        # Convert to relative coordinates
        # Subtract wrist position from all x coordinates
        processed[0::2] -= wrist_x  # Every even index is x
        # Subtract wrist position from all y coordinates
        processed[1::2] -= wrist_y  # Every odd index is y
        
        # Normalize by max absolute value
        max_val = np.max(np.abs(processed))
        if max_val > 0:
            processed = processed / max_val
        
        # Reshape to (1, 42) for model input
        processed = processed.reshape(1, -1)
        
        return processed
    
    def __del__(self):
        """Cleanup MediaPipe resources."""
        if hasattr(self, 'hands'):
            self.hands.close()
