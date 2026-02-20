# SignVista Backend 🖐️

Indian Sign Language Recognition System — FastAPI Backend

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload --port 8000

# 4. Open docs
# http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check + model status |
| `GET` | `/api/vocabulary` | List available ISL words |
| `POST` | `/api/recognize-frame` | Real-time sign translation |
| `POST` | `/api/learn/attempt` | Practice a word + proficiency |
| `GET` | `/api/stats/{sessionId}` | Learning statistics |
| `POST` | `/api/game/start` | Start a game round |
| `POST` | `/api/game/attempt` | Submit sign during game |
| `GET` | `/api/game/result/{sid}/{gid}` | Game results + badges |

## For Team Members

### Ishit (ML Engineer)
- Place trained `model.pth` at `ml/models/weights/model.pth`
- Model architecture is in `ml/models/lstm_model.py` — ensure your training matches:
  - Input: `(batch, 45, 99)` → 45 frames × 33 landmarks × 3 coords
  - Output: 15 classes (see `ml/vocabulary.py`)
- Update `ml/vocabulary.py` if your label order is different

### Ayush (Frontend Engineer)
- All request/response models are in `app/schemas.py`
- Backend runs on `http://localhost:8000`
- CORS is configured for `localhost:3000` and `localhost:3001`
- Use Swagger UI at `/docs` to test endpoints interactively

## Architecture

```
backend/
├── app/                     # FastAPI application
│   ├── main.py              # Entry point + CORS + health
│   ├── config.py            # Environment settings
│   ├── schemas.py           # Pydantic request/response models
│   ├── session_store.py     # In-memory session management
│   ├── routes/              # API endpoints
│   │   ├── translate.py     # POST /api/recognize-frame
│   │   ├── learn.py         # POST /api/learn/attempt
│   │   ├── game.py          # POST /api/game/*
│   │   ├── stats.py         # GET /api/stats/{sessionId}
│   │   └── vocabulary.py    # GET /api/vocabulary
│   └── utils/
│       └── frame_utils.py   # Base64 decode + validation
├── ml/                      # ML pipeline (interfaces for Ishit)
│   ├── inference.py         # Main prediction orchestrator
│   ├── buffer_manager.py    # 45-frame keypoint buffer
│   ├── keypoint_extractor.py # Mediapipe Pose
│   ├── face_detector.py     # Haar cascade gate
│   ├── vocabulary.py        # Word list + label mapping
│   └── models/
│       ├── lstm_model.py    # LSTM architecture (PyTorch)
│       └── weights/         # Drop model.pth here
├── tests/                   # pytest test suite
├── Dockerfile               # For Render.com
└── requirements.txt
```

## Docker

```bash
docker-compose up --build
```

## Testing

```bash
pytest tests/ -v
```
