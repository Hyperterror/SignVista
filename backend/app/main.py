"""
SignVista Backend — FastAPI Application

Run with: uvicorn app.main:app --reload   (from the backend/ directory)
"""

import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings as app_settings
from app.migrations import run_migrations
from app.schemas import HealthResponse
from app.session_store import get_active_session_count
from ml.inference import (
    are_isl_modules_initialized,
    get_isl_modules_status,
    initialize_isl_modules,
    initialize_model,
    is_model_loaded,
    warmup,
)
from ml.sign_demos import STATIC_DIR
from ml.vocabulary import NUM_CLASSES

logging.basicConfig(
    level=logging.DEBUG if app_settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
# Third-party libraries are very chatty at DEBUG
for noisy in ("asyncio", "absl", "h5py", "PIL", "matplotlib", "urllib3", "multipart"):
    logging.getLogger(noisy).setLevel(logging.WARNING)
logger = logging.getLogger("signvista")

MAX_REQUEST_BYTES = 3 * 1024 * 1024


# ─── Lifespan (startup/shutdown) ──────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("🚀 SignVista Backend starting...")
    logger.info(f"   Environment: {app_settings.ENV}")
    logger.info(f"   CORS origins: {app_settings.CORS_ORIGINS}")
    logger.info(f"   Database: {app_settings.DATABASE_URL.split('///')[0]}///…")
    logger.info("=" * 60)

    logger.info("📦 Applying database migrations...")
    run_migrations()

    initialize_model()
    initialize_isl_modules()
    if are_isl_modules_initialized() and is_model_loaded():
        logger.info("✅ Sign recognition models loaded")
    else:
        logger.warning("⚠️ No sign recognition model loaded — recognition endpoints will report 'no_model'")

    # Warm MediaPipe/TensorFlow in the background so startup stays fast
    if os.getenv("SKIP_ML_WARMUP", "").lower() not in ("1", "true"):
        threading.Thread(target=warmup, name="ml-warmup", daemon=True).start()

    yield
    logger.info("🛑 SignVista Backend shutting down...")


# ─── FastAPI App ──────────────────────────────────────────────────

app = FastAPI(
    title="SignVista API",
    description=(
        "Indian Sign Language Recognition System — "
        "Real-time translation, interactive learning with proficiency tracking, "
        "and gamified challenges."
    ),
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs" if app_settings.DEBUG else None,
    redoc_url="/redoc" if app_settings.DEBUG else None,
    openapi_url="/openapi.json" if app_settings.DEBUG else None,
)


# ─── Middleware ───────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def security_headers_and_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_REQUEST_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if not app_settings.DEBUG:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ─── Health Check ─────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    return HealthResponse(
        status="ok",
        model_loaded=is_model_loaded(),
        active_sessions=get_active_session_count(),
        vocabulary_size=NUM_CLASSES,
        version="1.1.0",
        isl_modules=get_isl_modules_status(),
    )


# ─── Routers ──────────────────────────────────────────────────────

from app.routes import (  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402
    achievements,
    ar,
    auth,
    chat,
    community,
    dashboard,
    dictionary,
    game,
    history,
    learn,
    notifications,
    profile,
    progress,
    stats,
    text_to_sign,
    translate,
    vocabulary,
)
from app.routes import settings as settings_router

for router_module in (
    auth, translate, learn, game, stats, vocabulary,
    profile, text_to_sign, ar,
    dictionary, progress, history, achievements, dashboard, community, chat,
    notifications, settings_router,
):
    app.include_router(router_module.router)

if app_settings.ENABLE_DEBUG_ROUTES:
    from app.routes import debug  # noqa: E402
    app.include_router(debug.router)
    logger.warning("⚠️ Debug routes enabled (ENABLE_DEBUG_ROUTES=true)")

# Sign demonstration media (GIFs) — see backend/static/assets/signs/README.md
os.makedirs(os.path.join(STATIC_DIR, "assets"), exist_ok=True)
app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")


@app.get("/", tags=["System"])
def root():
    return {
        "message": "🖐️ SignVista API — Indian Sign Language Recognition",
        "docs": "/docs" if app_settings.DEBUG else None,
        "health": "/health",
        "version": "1.1.0",
    }
