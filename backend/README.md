# SignVista Backend

FastAPI service for authentication, learning progress, games, community and
real-time ISL recognition. See the [root README](../README.md) for setup.

## Layout

```text
app/
  main.py            app factory: middleware, routers, startup (migrations, models, warm-up)
  config.py          settings from environment / .env (paths resolved absolutely)
  database.py        SQLAlchemy engine (SQLite, WAL, foreign keys)
  migrations.py      additive schema migration (new tables/columns)
  models.py          ORM models
  schemas.py         request/response models + validation
  security.py        password hashing (bcrypt; legacy sha256_crypt upgraded on login)
  jwt_utils.py       access tokens and WebSocket tickets
  dependencies.py    auth dependencies (cookie or bearer), WebSocket auth + Origin check
  rate_limit.py      in-process sliding-window limiter, proxy-aware client IP
  session_store.py   per-user state: XP, levels, streaks, achievements, games, activity
  routes/            API endpoints
  utils/             frame decoding, throttling, AR payloads
ml/
  inference.py       pipeline orchestration and module selection
  keypoint_extractor.py  MediaPipe Pose + Hand landmarkers (pooled, thread-safe)
  modules/           detection / recognition / translation modules
  model_loader.py    model loading and validation
  vocabulary.py      label maps per module
config/isl_modules.json   enabled modules, thresholds, selection strategy
static/assets/signs/      sign demonstration media (served at /assets/signs)
scripts/live_camera.py    webcam tool for checking the ML pipeline
tests/                    pytest suite (uses a temporary database)
```

## API overview

All endpoints except `/health`, `/api/vocabulary`, `/api/dictionary*`,
`/api/text-to-sign` and `/api/signs/*` require authentication. Paths that
contain a `{sessionId}` must match the signed-in user (otherwise 403).

| Area | Endpoints |
| ---- | --------- |
| Auth | `POST /api/auth/register`, `/login`, `/logout`, `GET /api/auth/me`, `POST /api/auth/ws-ticket` |
| Recognition | `POST /api/recognize-frame`, `WS /api/ws/recognize?ticket=`, `POST /api/ar/landmarks` |
| Learning | `POST /api/learn/attempt`, `GET /api/progress/{id}`, `/api/progress/{id}/next`, `/api/stats/{id}` |
| Game | `POST /api/game/start`, `/api/game/attempt`, `GET /api/game/result/{id}/{gameId}` |
| Profile | `GET/POST /api/profile`, `GET /api/dashboard/{id}`, `/api/history/{id}`, `/api/achievements/{id}` |
| Settings | `GET /api/settings/{id}`, `PUT /api/settings`, `GET /api/notifications/{id}`, `POST /api/notifications/read*` |
| Community | `GET /api/community/feed`, `POST /post`, `/like`, `GET/POST /posts/{id}/comments`, `GET /active-users` |
| Chat | `WS /api/chat/ws?ticket=`, `GET /api/chat/contacts`, `/messages/{contactId}`, `POST /api/chat/send` |
| Content | `GET /api/vocabulary`, `/api/dictionary`, `/api/dictionary/{word}`, `POST /api/text-to-sign`, `GET /api/signs/{word}` |

`recognize-frame` returns `buffer_status`, one of `collecting_NN%`, `ready`,
`low_confidence`, `no_hands`, `no_face`, `no_model`, `landmarks_unavailable` or
`throttled`.

## Configuration

Every setting is documented in [.env.example](.env.example). Production
(`ENV` other than `development`) requires `SECRET_KEY`, sends `Secure`
cookies and HSTS, and hides `/docs`. Debug routes are only mounted when
`ENABLE_DEBUG_ROUTES=true`.
