"""
SignVista Backend Configuration

Loads settings from environment variables with sensible defaults.
All relative paths are resolved against the backend / repository directories,
so the server behaves the same no matter which directory it is started from.
"""

import logging
import os
import secrets
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# backend/app/config.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _resolve(path: str, base: Path) -> str:
    """Resolve a possibly-relative path against a base directory."""
    p = Path(path)
    return str(p if p.is_absolute() else (base / p).resolve())


def _load_secret_key(env: str) -> str:
    """
    Return the JWT signing key.

    - SECRET_KEY env var always wins.
    - Outside development it is mandatory.
    - In development a random key is generated once and stored in a
      git-ignored file, so no shared/public fallback key ever exists.
    """
    key = os.getenv("SECRET_KEY", "").strip()
    if key and key != "your-secret-key-here":
        return key

    if env != "development":
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. "
            "This is required when ENV is not 'development'. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    key_file = BACKEND_DIR / ".dev_secret_key"
    try:
        if key_file.exists():
            stored = key_file.read_text().strip()
            if stored:
                return stored
        stored = secrets.token_hex(32)
        key_file.write_text(stored)
        return stored
    except OSError:
        # Read-only filesystem: fall back to a per-process random key
        return secrets.token_hex(32)


class Settings:
    """Application settings loaded from environment variables."""

    # Environment
    ENV: str = os.getenv("ENV", "development").strip().lower()
    DEBUG: bool = ENV == "development"
    # Debug-only routes must be opted into explicitly, even in development
    ENABLE_DEBUG_ROUTES: bool = _env_bool("ENABLE_DEBUG_ROUTES", False)

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS — frontend origins allowed to call the API with credentials
    CORS_ORIGINS: List[str] = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
        ).split(",")
        if o.strip()
    ]

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{(BACKEND_DIR / 'signvista.db').as_posix()}"
    )

    # Paths
    ISL_CONFIG_PATH: str = _resolve(
        os.getenv("ISL_CONFIG_PATH", "config/isl_modules.json"), BACKEND_DIR
    )
    ISL_MODELS_DIR: str = _resolve(
        os.getenv("ISL_MODELS_DIR", "ISL-Unified-Project/models"), REPO_ROOT
    )
    MEDIAPIPE_MODELS_DIR: str = _resolve(
        os.getenv("MEDIAPIPE_MODELS_DIR", "ml/models"), BACKEND_DIR
    )

    # Legacy standalone LSTM (optional). A full Keras model file (.h5/.hdf5/.keras).
    MODEL_PATH: str = _resolve(
        os.getenv("MODEL_PATH", "ml/models/weights/model.keras"), BACKEND_DIR
    )

    # Inference
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
    BUFFER_SIZE: int = int(os.getenv("BUFFER_SIZE", "45"))
    # Maximum frames per second processed per session (excess frames are dropped)
    FRAME_PROCESS_FPS: int = int(os.getenv("FRAME_PROCESS_FPS", "20"))
    # Return a fixed mock prediction when no model is loaded (tests/demos only)
    ALLOW_MOCK_PREDICTIONS: bool = _env_bool("ALLOW_MOCK_PREDICTIONS", False)

    # Frame validation
    MAX_FRAME_SIZE_BYTES: int = int(os.getenv("MAX_FRAME_SIZE_BYTES", str(1 * 1024 * 1024)))  # 1MB

    # Game
    GAME_DURATION_SECONDS: int = int(os.getenv("GAME_DURATION_SECONDS", "30"))
    GAME_POINTS_PER_CORRECT: int = int(os.getenv("GAME_POINTS_PER_CORRECT", "100"))

    # Session store
    SESSION_IDLE_TTL_SECONDS: int = int(os.getenv("SESSION_IDLE_TTL_SECONDS", str(2 * 60 * 60)))

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = _env_bool("RATE_LIMIT_ENABLED", True)
    # Reverse proxies (e.g. the Next.js server) whose X-Forwarded-For header is trusted
    TRUSTED_PROXIES: List[str] = [
        p.strip() for p in os.getenv("TRUSTED_PROXIES", "127.0.0.1,::1").split(",") if p.strip()
    ]

    # ─── JWT Authentication ───────────────────────────────────────────────
    SECRET_KEY: str = _load_secret_key(ENV)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))
    WS_TICKET_EXPIRE_SECONDS: int = 60

    # Cookie security — True outside development (requires HTTPS)
    COOKIE_SECURE: bool = _env_bool("COOKIE_SECURE", ENV != "development")


settings = Settings()
