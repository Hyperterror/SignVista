"""
Recognition Module for ISL Unified Models Integration.

This module implements LSTM-based temporal sequence analysis for word-level
recognition (Hello, How are you, Thank you) - 3 classes.

Features:
- MediaPipe Holistic extraction for 258 features (Pose + Left Hand + Right Hand)
- 45-frame sliding window buffering
- LSTM sequence prediction
- Buffer clearing after confident predictions
"""

import time
import logging
from typing import Optional, Dict, Any
import numpy as np

from . import ModulePrediction
from ..vocabulary import get_word_by_module_index, get_display_name
from ..keypoint_extractor import extract_keypoints
from ..buffer_manager import get_buffer, clear_buffer

logger = logging.getLogger(__name__)


class RecognitionModule:
    """
    Recognition module for word-level sign language recognition using LSTM.
    
    Processes sequences of frames to detect word-level signs using temporal
    analysis. Requires 45 frames before making predictions.
    """
    
    def __init__(self, model: Any, config: Dict[str, Any]):
        """
        Initialize recognition module.
        
        Args:
            model: Loaded LSTM word recognition model (Keras model)
            config: Module configuration with preprocessing_params and confidence_threshold
        """
        self.model = model
        self.config = config
        self.confidence_threshold = config.get("confidence_threshold", 0.6)
        
        # Get preprocessing parameters
        preprocessing_params = config.get("preprocessing_params", {})
        self.buffer_size = preprocessing_params.get("buffer_size", 45)
        self.clear_threshold = preprocessing_params.get("clear_threshold", 0.8)
        
        logger.info(
            f"✅ Recognition module initialized "
            f"(buffer_size={self.buffer_size}, threshold={self.confidence_threshold})"
        )
    
    def predict(self, frame: np.ndarray, session_id: str) -> Optional[ModulePrediction]:
        """
        Process frame with temporal buffering and return word prediction.
        
        Args:
            frame: Input frame as numpy array (H, W, 3) in BGR format
            session_id: Session identifier for buffer management
            
        Returns:
            ModulePrediction with word classification, or None if:
            - Buffer not ready (less than 45 frames)
            - Confidence below threshold
            - Processing error
        """
        start_time = time.time()
        
        try:
            # Extract pose keypoints
            preprocessing_start = time.time()
            keypoints = self.extract_pose_keypoints(frame)
            preprocessing_time = time.time() - preprocessing_start
            
            if keypoints is None:
                logger.debug("Failed to extract pose keypoints")
                return None
            
            # Get buffer for this session
            buffer = get_buffer(session_id)
            
            # Add keypoints to buffer
            buffer.append(keypoints)
            
            # Check if buffer is ready
            if not buffer.is_ready:
                logger.debug(
                    f"Buffer not ready: {buffer.length}/{self.buffer_size} frames"
                )
                return None
            
            # Get sequence from buffer
            sequence = buffer.get_sequence()
            
            if sequence is None:
                logger.debug("Failed to get sequence from buffer")
                return None
            
            # Run inference
            inference_start = time.time()
            predictions = self.model.predict(sequence, verbose=0)
            inference_time = time.time() - inference_start
            
            # Get class with highest confidence
            class_index = int(np.argmax(predictions[0]))
            confidence = float(predictions[0][class_index])
            
            # Apply confidence threshold
            if confidence < self.confidence_threshold:
                logger.debug(
                    f"Recognition confidence {confidence:.3f} below threshold "
                    f"{self.confidence_threshold}"
                )
                return None
            
            # Map to word
            word = get_word_by_module_index("recognition", class_index)
            display_name = get_display_name(word, "recognition")
            
            # Clear buffer if confidence is high enough
            if self.should_clear_buffer(confidence):
                clear_buffer(session_id)
                logger.debug(f"Buffer cleared after confident prediction ({confidence:.3f})")
            
            # Create prediction
            prediction = ModulePrediction(
                module_name="recognition",
                class_index=class_index,
                word=word,
                display_name=display_name,
                confidence=confidence,
                preprocessing_time=preprocessing_time,
                inference_time=inference_time,
                metadata={
                    "buffer_size": buffer.length,
                    "buffer_cleared": self.should_clear_buffer(confidence),
                    "sequence_shape": sequence.shape
                },
                timestamp=time.time()
            )
            
            logger.debug(
                f"Recognition prediction: {display_name} "
                f"(confidence={confidence:.3f}, time={time.time()-start_time:.3f}s)"
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Recognition module prediction failed: {e}", exc_info=True)
            return None
    
    def extract_pose_keypoints(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract 258 features using MediaPipe Holistic.
        
        Features breakdown:
        - Pose: 33 landmarks × 4 (x, y, z, visibility) = 132
        - Left Hand: 21 landmarks × 3 (x, y, z) = 63
        - Right Hand: 21 landmarks × 3 (x, y, z) = 63
        - Total: 258 features
        
        Args:
            frame: Input frame as numpy array (H, W, 3) in BGR format
            
        Returns:
            Numpy array of shape (258,) with extracted keypoints,
            or None if extraction fails
        """
        try:
            # Use existing keypoint extractor
            keypoints, _ = extract_keypoints(frame, return_results=False)
            
            # Verify shape
            if keypoints.shape[0] != 258:
                logger.warning(
                    f"Expected 258 keypoints, got {keypoints.shape[0]}"
                )
                return None
            
            return keypoints
            
        except Exception as e:
            logger.error(f"Pose keypoint extraction failed: {e}")
            return None
    
    def should_clear_buffer(self, confidence: float) -> bool:
        """
        Determine if buffer should be cleared after prediction.
        
        Buffer is cleared when confidence exceeds the clear_threshold
        to prevent the same sign from being detected multiple times.
        
        Args:
            confidence: Prediction confidence score (0.0 to 1.0)
            
        Returns:
            True if buffer should be cleared, False otherwise
        """
        return confidence >= self.clear_threshold
