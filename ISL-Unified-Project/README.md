# ISL Unified Project

## Overview

Comprehensive Indian Sign Language (ISL) recognition and translation system combining three powerful approaches:

- **Real-time Gesture Detection** - MediaPipe-based hand landmark detection with FNN classifier
- **Word-level Recognition** - LSTM-based temporal sequence analysis for video-based word recognition
- **Translation with Preprocessing** - YOLO + SqueezeNet pipeline for robust real-time translation

This project consolidates and organizes code from three existing ISL projects into a unified, maintainable structure.

## Project Structure

```
ISL-Unified-Project/
├── detection/              # MediaPipe-based gesture detection
│   ├── isl_detection.py
│   ├── dataset_keypoint_generation.py
│   ├── data/
│   └── notebooks/
├── recognition/            # LSTM-based word recognition
│   ├── deploy_code.py
│   ├── helper_functions.py
│   ├── app.py
│   ├── run_cmd.py
│   └── notebooks/
├── translation/            # Real-time translation with preprocessing
│   ├── main.py
│   ├── preprocessing.py
│   ├── yolo.py
│   └── select_final.py
├── models/                 # All trained models
│   ├── detection/
│   ├── recognition/
│   └── translation/
├── config/                 # Configuration files
│   ├── detection_config.json
│   ├── recognition_config.json
│   ├── translation_config.json
│   ├── translation_classes.json
│   └── yolo/
├── docs/                   # Documentation
│   ├── DETECTION.md
│   ├── RECOGNITION.md
│   └── TRANSLATION.md
├── tests/                  # Test files
├── requirements.txt        # Consolidated dependencies
└── README.md              # This file
```

## Quick Start

### Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

#### Detection Module
Real-time hand gesture detection using webcam:
```bash
cd detection
python isl_detection.py
```

#### Recognition Module
Word-level recognition from video:
```bash
cd recognition
python deploy_code.py
```

Or run the web API:
```bash
cd recognition
python app.py
```

#### Translation Module
Real-time translation with preprocessing:
```bash
cd translation
python main.py
```

## Modules

### Detection Module
- **Technology**: MediaPipe, OpenCV, TensorFlow/Keras
- **Features**: 
  - Real-time hand tracking
  - 42-point landmark extraction
  - Gesture classification (A-Z, 1-9)
- **Documentation**: [DETECTION.md](docs/DETECTION.md)

### Recognition Module
- **Technology**: LSTM, MediaPipe PoseNet, FastAPI
- **Features**:
  - Video frame processing (45 frames)
  - Pose estimation
  - Word recognition (Hello, How are you, Thank you)
  - Web API for video upload
- **Documentation**: [RECOGNITION.md](docs/RECOGNITION.md)

### Translation Module
- **Technology**: YOLO-v3, SqueezeNet, OpenCV
- **Features**:
  - Face detection activation
  - YOLO-based hand detection
  - Skin segmentation (HSV/YCbCr)
  - 10-class sign classification
- **Documentation**: [TRANSLATION.md](docs/TRANSLATION.md)

## Configuration

Each module has its own configuration file in the `config/` directory:
- `detection_config.json` - Detection module settings
- `recognition_config.json` - Recognition module settings
- `translation_config.json` - Translation module settings

## Models

Pre-trained models are located in the `models/` directory:
- `models/detection/gesture_classifier.h5` - FNN classifier for gestures
- `models/recognition/lstm_word_model.hdf5` - LSTM model for word recognition
- `models/translation/squeezenet_model` - SqueezeNet classifier

**Note**: YOLO weights file (`cross-hands.weights`) needs to be downloaded separately and placed in `config/yolo/`.

## Credits

This project consolidates work from three original repositories:

1. **Indian Sign Language Detection**
   - Original focus: MediaPipe-based hand landmark detection
   - Gesture classification using FNN

2. **Indian Sign Language Recognition**
   - Original focus: LSTM-based word-level recognition
   - Video processing with MediaPipe PoseNet

3. **Indian Sign Language Translator**
   - Original focus: Real-time translation with preprocessing
   - YOLO hand detection + SqueezeNet classification

All original project credits and licenses are preserved in their respective documentation files.

## Requirements

- Python 3.8+
- TensorFlow 2.13+
- OpenCV 4.7+
- MediaPipe 0.10+
- See `requirements.txt` for complete list

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing structure
- Tests are added for new features
- Documentation is updated

## License

See individual module documentation for license information from original projects.

## Support

For issues or questions:
- Check module-specific documentation in `docs/`
- Review configuration files in `config/`
- Ensure all dependencies are installed correctly

---

**Note**: This is a consolidated project for educational and research purposes. Please refer to original project repositories for their specific implementations and credits.
