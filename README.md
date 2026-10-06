# SignVista

Indian Sign Language (ISL) recognition and learning platform: real-time sign
translation from the webcam, text/voice → sign lookup, camera-based practice
with proficiency tracking, a timed sign game, and a small community with chat.

```text
frontend/              Next.js 16 app (App Router, React 19, Tailwind)
backend/               FastAPI API, SQLite, ML inference
ISL-Unified-Project/   Pretrained models + original training code
```

## How it fits together

```text
Browser ──HTTP /api/*──▶ Next.js (proxy) ──▶ FastAPI ──▶ SQLite
   │                                           │
   └──WebSocket (ticket auth)──────────────────┘──▶ ML pipeline
                                                    MediaPipe Pose + Hands
                                                    ├─ Recognition: 45-frame LSTM (hello / how are you / thank you)
                                                    ├─ Detection: per-frame classifier (A–Z, 1–9)
                                                    └─ Translation: YOLO + SqueezeNet (disabled, weights not in repo)
```

- **Auth**: phone + password. The session is an HttpOnly cookie. Because the
  browser calls `/api` on the frontend origin (Next.js proxies it), the cookie
  is first-party. WebSockets authenticate with a 60-second ticket from
  `POST /api/auth/ws-ticket`. Logging out revokes every token issued to that user.
- **Data**: SQLite at `backend/signvista.db`. Schema changes that only add
  tables or columns are applied automatically at startup (`app/migrations.py`).
- **ML details**: [backend/docs/ML_PIPELINE.md](backend/docs/ML_PIPELINE.md).

## Run locally

Requirements: Python 3.12–3.13, Node 20+.

```bash
# Backend (terminal 1)
cd backend
python -m venv venv
venv\Scripts\activate            # Windows  (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env             # optional in development
uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend
npm install
cp .env.example .env.local       # optional; defaults work locally
npm run dev                      # http://localhost:3000
```

In development, if `SECRET_KEY` is unset, a random key is generated once into
`backend/.dev_secret_key`; this file is git-ignored. API docs are served at
<http://localhost:8000/docs> in development only.

## Run with Docker

```bash
cp .env.example .env             # set SECRET_KEY
docker compose up --build        # frontend :3000, backend :8000
```

The database is stored in the `backend-data` volume. Sign media is mounted
from `backend/static/assets`.

## Tests and checks

```bash
cd backend && pip install -r requirements-dev.txt && ruff check . && pytest   # isolated temp database
cd frontend && npm run lint && npm run typecheck && npm run build
```

CI (`.github/workflows/ci.yml`) runs the same checks on every pull request
and builds the Docker images on pushes to `main`.

## Database migrations

Schema changes use Alembic (`backend/alembic/`). Migrations run automatically
at startup; databases created by older versions are adopted in place. After
changing `app/models.py`:

```bash
cd backend && alembic revision --autogenerate -m "describe the change"
```

`tests/test_migrations.py` fails if the models and migrations drift apart.

## Known gaps (need content or models, not code)

- **Sign demonstration GIFs** are not included. Add them under
  `backend/static/assets/signs/` (see the README there). Until then the UI
  shows a labelled placeholder.
- **Recognizable vocabulary is small.** The word model only knows *hello*,
  *how are you* and *thank you*, plus static letters and digits. Other
  dictionary words can be studied but not practiced with the camera until
  models are trained for them.
- **Translation module** needs `ISL-Unified-Project/config/yolo/cross-hands.weights`
  (not in the repo) before it can be enabled in `backend/config/isl_modules.json`.

## License

MIT. See [LICENSE](LICENSE). Frontend third-party notices are in
[frontend/ATTRIBUTIONS.md](frontend/ATTRIBUTIONS.md).
