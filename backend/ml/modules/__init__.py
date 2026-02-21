"""
ISL Unified Models Integration - Module Package

This package contains the detection, recognition, and translation modules
for the ISL (Indian Sign Language) Unified Project integration.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ModulePrediction:
    """Standardized prediction output from any module."""
    module_name: str  # "detection", "recognition", "translation"
    class_index: int  # Module-specific class index
    word: str  # Mapped word string
    display_name: str  # Human-readable display name
    confidence: float  # 0.0 to 1.0
    preprocessing_time: float  # Seconds
    inference_time: float  # Seconds
    metadata: Dict[str, Any]  # Module-specific additional data
    timestamp: float  # Unix timestamp


__all__ = ["ModulePrediction"]
