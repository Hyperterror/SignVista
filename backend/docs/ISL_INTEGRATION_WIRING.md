# ISL Unified Models Integration - Component Wiring

This document describes how all components of the ISL Unified Models Integration are wired together at application startup.

## Overview

The ISL Unified Models Integration adds support for three recognition modules:
- **Detection Module**: MediaPipe + FNN for gestures (A-Z, 1-9) - 35 classes
- **Recognition Module**: LSTM for word-level recognition (Hello, How are you, Thank you) - 3 classes
- **Translation Module**: YOLO + SqueezeNet for 10-class signs (G, I, K, O, P, S, U, V, X, Y)

## Component Initialization Flow

### 1. Application Startup (`backend/app/main.py`)

The FastAPI application initializes all components during the lifespan startup event:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML model on startup, cleanup on shutdown."""
    
    # 1. Load legacy LSTM model
    initialize_model()
    
    # 2. Initialize ISL Unified modules
    initialize_isl_modules()
    
    yield
    
    # Cleanup on shutdown
```

### 2. ISL Modules Initialization (`backend/ml/inference.py`)

The `initialize_isl_modules()` function orchestrates the initialization of all ISL components:

```python
def initialize_isl_modules():
    """
    Initialize ISL Unified Project modules.
    
    Steps:
    1. Load configuration from file/environment
    2. Validate configuration
    3. Load models for enabled modules
    4. Initialize module instances
    5. Handle missing models gracefully
    """
    
    # Step 1: Initialize ConfigurationManager
    _config_manager = ConfigurationManager()
    
    # Step 2: Validate configuration
    is_valid, errors = _config_manager.validate()
    
    # Step 3: Initialize ModelLoader
    _model_loader = ModelLoader()
    
    # Step 4: Load models for enabled modules
    enabled_modules = [
        name for name in ["detection", "recognition", "translation"]
        if _config_manager.is_module_enabled(name)
    ]
    load_results = _model_loader.load_all_models(enabled_modules)
    
    # Step 5: Initialize module instances
    if load_results.get("detection"):
        _detection_module = DetectionModule(...)
    
    if load_results.get("recognition"):
        _recognition_module = RecognitionModule(...)
    
    if load_results.get("translation"):
        _translation_module = TranslationModule(...)
```

## Component Details

### ConfigurationManager (`backend/ml/config_manager.py`)

**Initialization**: Created at startup in `initialize_isl_modules()`

**Configuration Source**: 
- Primary: `backend/config/isl_modules.json`
- Override: `ISL_MODULE_CONFIG` environment variable
- Fallback: Embedded defaults

**Responsibilities**:
- Load and validate module configuration
- Provide module enable/disable status
- Provide confidence thresholds
- Provide prediction strategy
- Expose configuration status for health endpoint

**Key Methods**:
- `is_module_enabled(module_name)` - Check if module is enabled
- `get_module_config(module_name)` - Get module-specific configuration
- `get_prediction_strategy()` - Get prediction selection strategy
- `get_confidence_threshold(module_name)` - Get confidence threshold

### ModelLoader (`backend/ml/model_loader.py`)

**Initialization**: Created at startup in `initialize_isl_modules()`

**Model Paths**:
- Detection: `ISL-Unified-Project/models/detection/gesture_classifier.h5`
- Recognition: `ISL-Unified-Project/models/recognition/lstm_word_model.hdf5`
- Translation: `ISL-Unified-Project/models/translation/squeezenet_model`
- YOLO: `ISL-Unified-Project/config/yolo/cross-hands.weights`

**Responsibilities**:
- Load TensorFlow/Keras models from disk
- Validate model output shapes
- Handle missing models gracefully
- Support GPU acceleration when available
- Cache model instances in memory

**Key Methods**:
- `load_all_models(enabled_modules)` - Load models for enabled modules
- `get_model(module_name)` - Get loaded model instance
- `validate_model(model, test_input)` - Validate model output

### VocabularyManager (`backend/ml/vocabulary.py`)

**Initialization**: Automatically initialized when module is imported

**Vocabularies**:
- Detection: 35 classes (1-9, A-Z)
- Recognition: 3 classes (Hello, How are you, Thank you)
- Translation: 10 classes (G, I, K, O, P, S, U, V, X, Y)

**Responsibilities**:
- Register module-specific vocabularies
- Map module indices to words
- Provide display names
- Merge vocabularies from all modules
- Resolve vocabulary conflicts by priority

**Key Functions**:
- `register_module_vocabulary(module_name, vocab)` - Register vocabulary
- `get_word_by_module_index(module_name, index)` - Map index to word
- `get_display_name(word, module_name)` - Get display name
- `get_unified_vocabulary()` - Get merged vocabulary

### Module Instances

#### DetectionModule (`backend/ml/modules/detection.py`)

**Initialization**: Created in `initialize_isl_modules()` if enabled and model loaded

**Dependencies**:
- FNN model from ModelLoader
- MediaPipe Hands for landmark extraction
- Configuration from ConfigurationManager

**Processing**:
- Stateless (no temporal buffering)
- Extracts 42-point hand landmarks
- Classifies into 35 gesture classes

#### RecognitionModule (`backend/ml/modules/recognition.py`)

**Initialization**: Created in `initialize_isl_modules()` if enabled and model loaded

**Dependencies**:
- LSTM model from ModelLoader
- MediaPipe Holistic for keypoint extraction
- BufferManager for 45-frame sliding window
- Configuration from ConfigurationManager

**Processing**:
- Stateful (uses 45-frame buffer)
- Extracts 258 pose keypoints
- Classifies into 3 word classes

#### TranslationModule (`backend/ml/modules/translation.py`)

**Initialization**: Created in `initialize_isl_modules()` if enabled and model loaded

**Dependencies**:
- SqueezeNet model from ModelLoader
- YOLO detector for hand detection
- Configuration from ConfigurationManager

**Processing**:
- Stateless (no temporal buffering)
- Detects hands with YOLO
- Applies skin segmentation
- Classifies into 10 sign classes

### InferenceEngine (`backend/ml/inference.py`)

**Initialization**: Uses global module instances initialized at startup

**Responsibilities**:
- Execute enabled modules based on configuration
- Collect predictions from all modules
- Apply prediction selection strategy
- Handle preprocessing failures gracefully
- Track timing and performance metrics

**Key Functions**:
- `predict_from_raw_frame()` - Main inference pipeline
- `execute_modules_parallel()` - Execute all enabled modules
- `select_final_prediction()` - Apply selection strategy

**Prediction Strategies**:
- **Priority**: Select from highest priority module
- **Highest Confidence**: Select prediction with highest confidence
- **Voting**: Boost confidence for words predicted by multiple modules

### API Routes (`backend/app/routes/translate.py`)

**Endpoint**: `POST /api/recognize-frame`

**Query Parameters**:
- `return_module_details` (optional): Include detailed module information

**Response**:
- `word`: Predicted word
- `confidence`: Confidence score
- `buffer_status`: Buffer status
- `history`: Recent predictions
- `module_details` (optional): Detailed module information

**Module Details Structure**:
```json
{
  "active_modules": ["detection", "recognition"],
  "predictions": [
    {
      "module": "detection",
      "word": "A",
      "display_name": "A",
      "confidence": 0.85,
      "class_index": 9
    }
  ],
  "selected": {
    "module": "detection",
    "reason": "strategy_priority"
  },
  "preprocessing_times": {
    "detection": 0.015
  },
  "inference_times": {
    "detection": 0.008
  },
  "total_time": 0.023
}
```

### Health Endpoint (`backend/app/main.py`)

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "ok",
  "model_loaded": true,
  "active_sessions": 0,
  "vocabulary_size": 10,
  "version": "1.0.0",
  "isl_modules": {
    "initialized": true,
    "enabled_modules": ["detection", "recognition"],
    "configuration": {
      "prediction_strategy": "priority",
      "fallback_to_lstm": true
    },
    "modules": {
      "detection": {
        "enabled": true,
        "loaded": true,
        "confidence_threshold": 0.7,
        "priority": 2
      },
      "recognition": {
        "enabled": true,
        "loaded": false,
        "confidence_threshold": 0.6,
        "priority": 1
      },
      "translation": {
        "enabled": false,
        "loaded": false,
        "confidence_threshold": null,
        "priority": null
      }
    }
  }
}
```

## Initialization Sequence Diagram

```
Application Startup
    │
    ├─> initialize_model()
    │   └─> Load legacy LSTM model
    │
    └─> initialize_isl_modules()
        │
        ├─> ConfigurationManager()
        │   ├─> Load config from file
        │   ├─> Validate configuration
        │   └─> Set defaults for invalid values
        │
        ├─> ModelLoader()
        │   ├─> Load detection model
        │   ├─> Load recognition model
        │   ├─> Load translation model
        │   └─> Validate model outputs
        │
        ├─> DetectionModule()
        │   ├─> Initialize MediaPipe Hands
        │   └─> Store model reference
        │
        ├─> RecognitionModule()
        │   ├─> Initialize MediaPipe Holistic
        │   └─> Store model reference
        │
        └─> TranslationModule()
            ├─> Initialize YOLO detector
            └─> Store model reference
```

## Request Flow Diagram

```
Client Request
    │
    ├─> POST /api/recognize-frame
    │
    ├─> decode_base64_frame()
    │
    ├─> predict_from_raw_frame()
    │   │
    │   ├─> detect_face()
    │   │   └─> Return early if no face
    │   │
    │   ├─> execute_modules_parallel()
    │   │   │
    │   │   ├─> DetectionModule.predict()
    │   │   │   ├─> Extract hand landmarks
    │   │   │   ├─> Preprocess landmarks
    │   │   │   └─> FNN classification
    │   │   │
    │   │   ├─> RecognitionModule.predict()
    │   │   │   ├─> Extract pose keypoints
    │   │   │   ├─> Buffer 45 frames
    │   │   │   └─> LSTM classification
    │   │   │
    │   │   └─> TranslationModule.predict()
    │   │       ├─> YOLO hand detection
    │   │       ├─> Skin segmentation
    │   │       └─> SqueezeNet classification
    │   │
    │   ├─> select_final_prediction()
    │   │   └─> Apply strategy (priority/confidence/voting)
    │   │
    │   └─> Return (word, confidence, status, module_details)
    │
    └─> Return JSON response
```

## Configuration

### Default Configuration (`backend/config/isl_modules.json`)

```json
{
  "modules": {
    "detection": {
      "enabled": true,
      "priority": 2,
      "confidence_threshold": 0.7,
      "model_path": "ISL-Unified-Project/models/detection/gesture_classifier.h5",
      "preprocessing_params": {
        "max_num_hands": 2,
        "model_complexity": 0
      }
    },
    "recognition": {
      "enabled": true,
      "priority": 1,
      "confidence_threshold": 0.6,
      "model_path": "ISL-Unified-Project/models/recognition/lstm_word_model.hdf5",
      "preprocessing_params": {
        "buffer_size": 45
      }
    },
    "translation": {
      "enabled": false,
      "priority": 3,
      "confidence_threshold": 0.7,
      "model_path": "ISL-Unified-Project/models/translation/squeezenet_model",
      "preprocessing_params": {
        "yolo_confidence": 0.5,
        "yolo_threshold": 0.3
      }
    }
  },
  "prediction_strategy": "priority",
  "enable_parallel_execution": false,
  "performance_monitoring": true,
  "fallback_to_existing_lstm": true
}
```

## Testing

### Automated Tests

Run the end-to-end integration tests:

```bash
python -m pytest backend/tests/test_integration_e2e.py -v
```

Tests verify:
- ✅ ConfigurationManager is initialized at startup
- ✅ ModelLoader loads all models at startup
- ✅ VocabularyManager registers all module vocabularies
- ✅ InferenceEngine uses all modules based on configuration
- ✅ API routes properly expose module details
- ✅ Health endpoint is accessible

### Manual Testing

Run the manual test script (requires running server):

```bash
# Terminal 1: Start server
uvicorn app.main:app --reload

# Terminal 2: Run manual tests
python backend/test_e2e_manual.py
```

## Troubleshooting

### Issue: ISL modules not initialized

**Symptoms**: Health endpoint shows `"initialized": false`

**Possible Causes**:
1. Configuration file missing or invalid
2. Model files not found
3. Import errors in module code

**Solution**:
1. Check logs for error messages during startup
2. Verify configuration file exists at `backend/config/isl_modules.json`
3. Verify model files exist in `ISL-Unified-Project/models/`

### Issue: Module loaded but not producing predictions

**Symptoms**: Module shows `"loaded": true` but no predictions in response

**Possible Causes**:
1. Confidence threshold too high
2. Preprocessing failure (no face, no hands)
3. Model output below threshold

**Solution**:
1. Check module_details in API response for preprocessing status
2. Lower confidence threshold in configuration
3. Check logs for preprocessing errors

### Issue: Wrong module selected

**Symptoms**: Unexpected module's prediction is selected

**Possible Causes**:
1. Prediction strategy not configured correctly
2. Module priorities not set correctly

**Solution**:
1. Check `prediction_strategy` in configuration
2. Verify module priorities (lower number = higher priority)
3. Use `return_module_details=true` to see all predictions

## Summary

All components are properly wired together at application startup:

1. ✅ **ConfigurationManager** is initialized in `initialize_isl_modules()`
2. ✅ **ModelLoader** loads all models in `initialize_isl_modules()`
3. ✅ **VocabularyManager** registers all module vocabularies on import
4. ✅ **InferenceEngine** uses all modules via `execute_modules_parallel()`
5. ✅ **API routes** expose module details via `return_module_details` parameter
6. ✅ **Health endpoint** shows module status via `get_isl_modules_status()`

The system is ready to handle requests through the frontend with full multi-module support!
