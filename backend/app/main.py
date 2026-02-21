"""
SignVista Backend — FastAPI Application

Main entry point. Initializes the ML model on startup,
configures CORS, and mounts all route routers.

Run with: uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import HealthResponse
from app.session_store import get_active_session_count
from ml.inference import initialize_model, is_model_loaded
from ml.vocabulary import NUM_CLASSES

# ─── Logging Setup ────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("signbridge")


# ─── Lifespan (startup/shutdown) ──────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML model on startup, cleanup on shutdown."""
    logger.info("=" * 60)
    logger.info("🚀 SignBridge Backend starting...")
    logger.info(f"   Environment: {settings.ENV}")
    logger.info(f"   CORS origins: {settings.CORS_ORIGINS}")
    logger.info(f"   Model path: {settings.MODEL_PATH}")
    logger.info(f"   Confidence threshold: {settings.CONFIDENCE_THRESHOLD}")
    logger.info(f"   Buffer size: {settings.BUFFER_SIZE} frames")
    logger.info("=" * 60)

    # Load ML model
    initialize_model()

    if is_model_loaded():
        logger.info("✅ ML model loaded — real predictions active")
    else:
        logger.warning("⚠️ ML model NOT loaded — mock predictions active")
        logger.warning("   Ishit: place model.pth in ml/models/weights/")

    yield

    # Cleanup
    logger.info("🛑 SignVista Backend shutting down...")


# ─── FastAPI App ──────────────────────────────────────────────────

app = FastAPI(
    title="SignBridge API",
    description=(
        "Indian Sign Language Recognition System — "
        "Real-time translation, interactive learning with proficiency tracking, "
        "and gamified challenges."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
)


# ─── CORS Middleware ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ─────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    Returns server status, model state, and active sessions.
    """
    return HealthResponse(
        status="ok",
        model_loaded=is_model_loaded(),
        active_sessions=get_active_session_count(),
        vocabulary_size=NUM_CLASSES,
        version="1.0.0",
    )


# ─── Mount Route Routers ─────────────────────────────────────────

from app.routes import translate, learn, game, stats, vocabulary
from app.routes import profile, text_to_sign, ar, community, auth
from app.routes import dictionary, progress, history, achievements, dashboard, chat

# Auth
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])

# Phase 1
app.include_router(translate.router)
app.include_router(learn.router)
app.include_router(game.router)
app.include_router(stats.router)
app.include_router(vocabulary.router)

# Phase 2 — Dashboard features
app.include_router(profile.router)
app.include_router(text_to_sign.router)
app.include_router(ar.router)

# Phase 3 — Learning & Gamification
app.include_router(dictionary.router)
app.include_router(progress.router)
app.include_router(history.router)
app.include_router(achievements.router)
app.include_router(dashboard.router)
app.include_router(community.router, prefix="/api/community", tags=["Community"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


# ─── Root Redirect ────────────────────────────────────────────────

@app.get("/", tags=["System"])
async def root():
    """Root endpoint — redirects to docs."""
    return {
        "message": "🖐️ SignBridge API — Indian Sign Language Recognition",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
    }
