"""
Translation Module for ISL Unified Models Integration.

This module implements YOLO-v3 hand detection with SqueezeNet classification
for real-time translation of 10 sign classes (G, I, K, O, P, S, U, V, X, Y).

Features:
- YOLO-v3 hand detection using OpenCV DNN backend
- Skin segmentation using HSV and YCbCr color spaces
- SqueezeNet-based classification for 10 classes
- Stateless frame processing (no temporal buffering)
- Handles single and multiple hand detections
"""

import time
import logging
import os
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import cv2

from . import ModulePrediction
from ..vocabulary import get_word_by_module_index, get_display_name

logger = logging.getLogger(__name__)


class TranslationModule:
    """
    Translation module for sign language recognition using YOLO + SqueezeNet.
    
    Processes individual frames to detect hands, segment skin, and classify signs
    into 10 classes (G, I, K, O, P, S, U, V, X, Y).
    """
    
    def __init__(self, model: Any, yolo_config: str, yolo_weights: str, config: Dict[str, Any]):
        """
        Initialize translation module.
        
        Args:
            model: Loaded SqueezeNet classifier model
            yolo_config: Path to YOLO configuration file
            yolo_weights: Path to YOLO weights file
            config: Module configuration with preprocessing_params and confidence_threshold
        """
        self.model = model
        self.config = config
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        
        # Get preprocessing parameters
        preprocessing_params = config.get("preprocessing_params", {})
        self.yolo_confidence = preprocessing_params.get("yolo_confidence", 0.5)
        self.yolo_threshold = preprocessing_params.get("yolo_threshold", 0.3)
        self.yolo_size = preprocessing_params.get("yolo_size", 416)
        self.target_size = tuple(preprocessing_params.get("target_size", [224, 224]))
        
        # Initialize YOLO detector
        self.yolo_net = self._load_yolo(yolo_config, yolo_weights)
        
        logger.info(
            f"✅ Translation module initialized "
            f"(yolo_conf={self.yolo_confidence}, yolo_thresh={self.yolo_threshold}, "
            f"target_size={self.target_size})"
        )
    
    def _load_yolo(self, config_path: str, weights_path: str) -> cv2.dnn.Net:
        """
        Load YOLO detector using OpenCV DNN backend.
        
        Args:
            config_path: Path to YOLO configuration file
            weights_path: Path to YOLO weights file
            
        Returns:
            Loaded YOLO network
            
        Raises:
            ValueError: If model files are not found
        """
        if not os.path.exists(config_path):
            raise ValueError(f"YOLO config file not found: {config_path}")
        
        if not os.path.exists(weights_path):
            raise ValueError(
                f"YOLO weights file not found: {weights_path}\n"
                f"Please download the weights file manually and place it in the correct directory."
            )
        
        try:
            net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
            logger.info(f"✅ YOLO detector loaded from {weights_path}")
            return net
        except Exception as e:
            raise ValueError(f"Failed to load YOLO detector: {e}")
    
    def predict(self, frame: np.ndarray) -> Optional[ModulePrediction]:
        """
        Detect hands, segment skin, and classify sign.
        
        Processing pipeline:
        1. Use YOLO to detect hand bounding boxes
        2. Merge multiple detections into single region
        3. Extract hand region from frame
        4. Apply skin segmentation
        5. Resize to (224, 224) for SqueezeNet
        6. Classify into 10 classes
        
        Args:
            frame: Input frame as numpy array (H, W, 3) in BGR format
            
        Returns:
            ModulePrediction with sign classification, or None if:
            - No hands detected
            - Confidence below threshold
            - Processing error
        """
        start_time = time.time()
        
        try:
            # Detect hands using YOLO
            preprocessing_start = time.time()
            hand_boxes = self.detect_hands(frame)
            
            if not hand_boxes:
                logger.debug("No hands detected in frame")
                return None
            
            # Merge multiple hand detections and extract region
            x, y, x1, y1 = self._merge_hand_boxes(hand_boxes)
            
            # Ensure coordinates are within frame bounds
            h, w = frame.shape[:2]
            x = max(0, x)
            y = max(0, y)
            x1 = min(w, x1)
            y1 = min(h, y1)
            
            # Extract hand region
            hand_region = frame[y:y1, x:x1]
            
            if hand_region.size == 0:
                logger.debug("Empty hand region after extraction")
                return None
            
            # Apply skin segmentation
            segmented = self.segment_skin(hand_region)
            
            # Preprocess for SqueezeNet
            preprocessed = self.preprocess_for_squeezenet(segmented)
            preprocessing_time = time.time() - preprocessing_start
            
            # Run inference
            inference_start = time.time()
            predictions = self.model.predict(preprocessed, verbose=0)
            inference_time = time.time() - inference_start
            
            # Get class with highest confidence
            class_index = int(np.argmax(predictions[0]))
            confidence = float(predictions[0][class_index])
            
            # Apply confidence threshold
            if confidence < self.confidence_threshold:
                logger.debug(
                    f"Translation confidence {confidence:.3f} below threshold "
                    f"{self.confidence_threshold}"
                )
                return None
            
            # Map to word
            word = get_word_by_module_index("translation", class_index)
            display_name = get_display_name(word, "translation")
            
            # Create prediction
            prediction = ModulePrediction(
                module_name="translation",
                class_index=class_index,
                word=word,
                display_name=display_name,
                confidence=confidence,
                preprocessing_time=preprocessing_time,
                inference_time=inference_time,
                metadata={
                    "num_hands_detected": len(hand_boxes),
                    "hand_region": {"x": x, "y": y, "x1": x1, "y1": y1},
                    "hand_boxes": hand_boxes
                },
                timestamp=time.time()
            )
            
            logger.debug(
                f"Translation prediction: {display_name} "
                f"(confidence={confidence:.3f}, time={time.time()-start_time:.3f}s)"
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Translation module prediction failed: {e}", exc_info=True)
            return None
    
    def detect_hands(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Use YOLO to detect hand bounding boxes.
        
        Args:
            frame: Input frame as numpy array (H, W, 3) in BGR format
            
        Returns:
            List of bounding boxes as (x, y, w, h) tuples
        """
        try:
            ih, iw = frame.shape[:2]
            
            # Get output layer names
            ln = self.yolo_net.getLayerNames()
            unconnected = self.yolo_net.getUnconnectedOutLayers()
            
            # Handle both old and new OpenCV API
            if isinstance(unconnected[0], (list, np.ndarray)):
                ln = [ln[i[0] - 1] for i in unconnected]
            else:
                ln = [ln[i - 1] for i in unconnected]
            
            # Create blob from image
            blob = cv2.dnn.blobFromImage(
                frame, 1 / 255.0, (self.yolo_size, self.yolo_size),
                swapRB=True, crop=False
            )
            
            # Run forward pass
            self.yolo_net.setInput(blob)
            layer_outputs = self.yolo_net.forward(ln)
            
            # Process detections
            boxes = []
            confidences = []
            
            for output in layer_outputs:
                for detection in output:
                    scores = detection[5:]
                    confidence = float(np.max(scores))
                    
                    if confidence > self.yolo_confidence:
                        # Scale bounding box coordinates
                        box = detection[0:4] * np.array([iw, ih, iw, ih])
                        (centerX, centerY, width, height) = box.astype("int")
                        
                        # Calculate top-left corner
                        x = int(centerX - (width / 2))
                        y = int(centerY - (height / 2))
                        
                        boxes.append([x, y, int(width), int(height)])
                        confidences.append(confidence)
            
            # Apply non-maximum suppression
            if len(boxes) > 0:
                idxs = cv2.dnn.NMSBoxes(
                    boxes, confidences,
                    self.yolo_confidence, self.yolo_threshold
                )
                
                if len(idxs) > 0:
                    # Handle both old and new OpenCV API
                    if isinstance(idxs, np.ndarray):
                        if idxs.ndim == 2:
                            idxs = idxs.flatten()
                    
                    result_boxes = []
                    for i in idxs:
                        x, y, w, h = boxes[i]
                        result_boxes.append((x, y, w, h))
                    
                    return result_boxes
            
            return []
            
        except Exception as e:
            logger.error(f"YOLO hand detection failed: {e}")
            return []
    
    def _merge_hand_boxes(self, hand_boxes: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
        """
        Merge multiple hand detections into single bounding box.
        
        Args:
            hand_boxes: List of bounding boxes as (x, y, w, h) tuples
            
        Returns:
            Merged bounding box as (x, y, x1, y1) tuple
        """
        if len(hand_boxes) == 1:
            x, y, w, h = hand_boxes[0]
            return x, y, x + w, y + h
        
        # Multiple hands: merge into single region
        x_min = min(box[0] for box in hand_boxes)
        y_min = min(box[1] for box in hand_boxes)
        x_max = max(box[0] + box[2] for box in hand_boxes)
        y_max = max(box[1] + box[3] for box in hand_boxes)
        
        return x_min, y_min, x_max, y_max
    
    def segment_skin(self, hand_region: np.ndarray) -> np.ndarray:
        """
        Apply HSV + YCbCr skin segmentation.
        
        This method uses color space thresholding to segment skin regions:
        1. Convert to HSV and YCbCr color spaces
        2. Apply thresholds for skin color detection
        3. Combine masks from both color spaces
        4. Apply morphological operations (erosion, dilation)
        5. Use watershed algorithm for region-based segmentation
        
        Args:
            hand_region: Hand region as numpy array (H, W, 3) in BGR format
            
        Returns:
            Segmented hand region with background removed
        """
        try:
            # Convert to HSV and YCbCr
            hsv_image = cv2.cvtColor(hand_region, cv2.COLOR_BGR2HSV)
            ycbcr_image = cv2.cvtColor(hand_region, cv2.COLOR_BGR2YCR_CB)
            
            # Define skin color thresholds
            lower_hsv = np.array([0, 40, 0], dtype="uint8")
            upper_hsv = np.array([25, 255, 255], dtype="uint8")
            lower_ycbcr = np.array([0, 138, 67], dtype="uint8")
            upper_ycbcr = np.array([255, 173, 133], dtype="uint8")
            
            # Create masks
            mask_hsv = cv2.inRange(hsv_image, lower_hsv, upper_hsv)
            mask_ycbcr = cv2.inRange(ycbcr_image, lower_ycbcr, upper_ycbcr)
            
            # Combine masks
            binary_mask = cv2.add(mask_hsv, mask_ycbcr)
            
            # Morphological operations
            foreground = cv2.erode(binary_mask, None, iterations=3)
            dilated = cv2.dilate(binary_mask, None, iterations=3)
            
            # Create background marker
            _, background = cv2.threshold(dilated, 1, 128, cv2.THRESH_BINARY)
            
            # Combine foreground and background markers
            markers = cv2.add(foreground, background)
            markers32 = np.int32(markers)
            
            # Apply watershed
            cv2.watershed(hand_region, markers32)
            
            # Convert back to uint8
            m = cv2.convertScaleAbs(markers32)
            
            # Create final mask
            _, mask = cv2.threshold(m, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Apply mask to original image
            output = cv2.bitwise_and(hand_region, hand_region, mask=mask)
            
            return output
            
        except Exception as e:
            logger.error(f"Skin segmentation failed: {e}")
            # Return original image if segmentation fails
            return hand_region
    
    def preprocess_for_squeezenet(self, hand_region: np.ndarray) -> np.ndarray:
        """
        Resize to (224, 224) and normalize for SqueezeNet input.
        
        Args:
            hand_region: Hand region as numpy array (H, W, 3) in BGR format
            
        Returns:
            Preprocessed image of shape (1, 224, 224, 3) ready for model input
        """
        try:
            # Resize to target size
            resized = cv2.resize(hand_region, self.target_size, interpolation=cv2.INTER_AREA)
            
            # Convert to RGB (SqueezeNet expects RGB)
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # Normalize to [0, 1]
            normalized = rgb.astype(np.float32) / 255.0
            
            # Add batch dimension
            preprocessed = np.expand_dims(normalized, axis=0)
            
            return preprocessed
            
        except Exception as e:
            logger.error(f"Preprocessing for SqueezeNet failed: {e}")
            raise
