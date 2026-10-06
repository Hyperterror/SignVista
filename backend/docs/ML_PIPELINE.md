# ML pipeline

How a camera frame becomes a sign prediction, and what to keep consistent
when retraining models.

## Per-frame flow (`ml/inference.py::predict_from_raw_frame`)

1. **Optional face gate.** This runs only if `require_face_detection` is true
   in `config/isl_modules.json` (default false). It uses an OpenCV Haar cascade.
2. **Landmarks, extracted once** (`ml/keypoint_extractor.py`). MediaPipe Tasks
   `PoseLandmarker` (full) + `HandLandmarker` run in IMAGE mode from a small
   thread-safe pool. Model files are in `ml/models/*.task`.
   - Hands are assigned to the signer's left or right by matching each hand's
     wrist to the pose wrists, the same way legacy Holistic did it.
   - Recognition features are 258 values: pose 33×(x,y,z,visibility),
     left hand 21×(x,y,z), right hand 21×(x,y,z). This is the same layout as
     `ISL-Unified-Project/recognition/helper_functions.py::extract_keypoints`.
3. **Modules** (enabled and loaded ones only):
   - **Recognition**, the word level (`modules/recognition.py`). It appends
     features to a per-session 45-frame sliding buffer (`buffer_manager.py`).
     When the buffer is full and hands appear in at least 30% of its frames,
     it runs the LSTM. The buffer is cleared after a prediction with
     confidence ≥ 0.8. Classes: hello, how_are_you, thank_you.
   - **Detection**, static gestures (`modules/detection.py`). It uses the
     hand landmarks of a **horizontally mirrored** frame in **pixel
     coordinates**, made relative to the wrist and normalized by the maximum
     absolute value. This matches `detection/isl_detection.py`, the training
     code. It rejects ambiguous results (top-2 margin < 0.15) and requires the
     same answer on 2 consecutive frames per session. Classes: 1–9, A–Z.
   - **Translation**: YOLO hand detector + SqueezeNet (10 letters). Works, but
     **disabled by default**: it costs ~360 ms per frame on CPU and its letters
     are already covered by Detection. Enable it in `config/isl_modules.json`
     only with a GPU. It needs `cross-hands.weights` (246 MB, too large for
     git); fetch it with `python scripts/download_models.py`.
4. **Selection.** Predictions above each module's threshold are combined with
   `prediction_strategy` (priority, highest_confidence or voting).
   Recognition has priority 1.
5. **Status.** `collecting_NN%` is reported while the word buffer fills;
   `no_hands`, `low_confidence` or `ready` otherwise.

Learn and game routes ignore letter/digit predictions while the target is a
word-level sign, and start a fresh buffer after each recorded attempt.

## Performance

Models run through `ml/predictor.py`, which compiles them with `tf.function`
using a fixed input signature. `model.predict()` costs 50–75 ms per call
because of its batch-oriented overhead; the compiled path takes about 6 ms
for the LSTM and under 1 ms for the classifier, with identical outputs.
A frame costs about 25 ms of MediaPipe landmarking plus a few milliseconds
of inference on a laptop CPU.

## Models

| Module | File | Notes |
| ------ | ---- | ----- |
| Recognition | `ISL-Unified-Project/models/recognition/lstm_word_model.hdf5` | **Weights only.** Architecture is rebuilt in `model_loader.build_recognition_model` (LSTM 64→128→256→64, Dense 64→32→3, relu). |
| Detection | `ISL-Unified-Project/models/detection/gesture_classifier.h5` | Full Keras model, input (1, 42). |
| Translation | `ISL-Unified-Project/models/translation/squeezenet_model` | Keras 2.2.4 HDF5 without extension; rebuilt from its stored config (`model_loader.load_keras_file`). Needs YOLO weights. |

Optional: a standalone full Keras model at `MODEL_PATH` is used only when the
recognition module isn't available.

## Adding signs / retraining

- Keep the feature layout and preprocessing above identical between training
  and inference. A mismatch produces confident but wrong predictions.
- Update the label maps in `ml/vocabulary.py` (`RECOGNITION_VOCAB`,
  `DETECTION_VOCAB`) and the class count in `build_recognition_model`.
- Newly recognizable words automatically show up in the game pool, as camera
  practice targets and as `recognizable: true` in `GET /api/vocabulary`.
- Check the result with `python -m scripts.live_camera` (needs `opencv-python`).
