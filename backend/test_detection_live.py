"""
Quick diagnostic script to test ISL detection system.
Run this to see what's happening with the modules.
"""

import sys
import logging
import numpy as np
import cv2

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
)

# Import components
from ml.config_manager import ConfigurationManager
from ml.model_loader import ModelLoader
from ml.inference import initialize_isl_modules, are_isl_modules_initialized, predict_from_raw_frame

print("=" * 60)
print("ISL Detection System Diagnostic")
print("=" * 60)

# 1. Check configuration
print("\n1. Checking configuration...")
config_mgr = ConfigurationManager()
is_valid, errors = config_mgr.validate()
print(f"   Configuration valid: {is_valid}")
if errors:
    print(f"   Errors: {errors}")

enabled_modules = [
    name for name in ["detection", "recognition", "translation"]
    if config_mgr.is_module_enabled(name)
]
print(f"   Enabled modules: {enabled_modules}")

# 2. Check model files
print("\n2. Checking model files...")
model_loader = ModelLoader()
load_results = model_loader.load_all_models(enabled_modules)
print(f"   Load results: {load_results}")

# 3. Initialize ISL modules
print("\n3. Initializing ISL modules...")
initialize_isl_modules()
print(f"   Modules initialized: {are_isl_modules_initialized()}")

# 4. Test with a dummy frame
print("\n4. Testing with dummy frame...")
dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

# Add a simple face-like region (to pass face detection)
cv2.rectangle(dummy_frame, (200, 100), (440, 380), (255, 255, 255), -1)

word, confidence, status, _, module_details = predict_from_raw_frame(
    session_id="test-diagnostic",
    frame=dummy_frame,
    return_module_details=True
)

print(f"   Result: word={word}, confidence={confidence}, status={status}")
if module_details:
    print(f"   Active modules: {module_details.get('active_modules')}")
    print(f"   Predictions: {module_details.get('predictions')}")
    print(f"   Selected: {module_details.get('selected')}")

print("\n" + "=" * 60)
print("Diagnostic complete!")
print("=" * 60)
