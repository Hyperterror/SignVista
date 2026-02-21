"""
SignVista Backend Configuration

Loads settings from environment variables with sensible defaults.
Ishit: No changes needed here unless you add new ML config.
Ayush: CORS_ORIGINS must include your frontend URL.
"""

import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS — add Ayush's frontend URL here
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"
    ).split(",")

    # ML Model paths — Ishit will place weights here
    MODEL_PATH: str = os.getenv("MODEL_PATH", "ml/models/weights/model.pth")
    ANN_MODEL_PATH: str = os.getenv("ANN_MODEL_PATH", "ml/models/weights/model.h5")

    # Inference
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
    BUFFER_SIZE: int = int(os.getenv("BUFFER_SIZE", "45"))
    FRAME_PROCESS_FPS: int = int(os.getenv("FRAME_PROCESS_FPS", "5"))

    # Frame validation
    MAX_FRAME_SIZE_BYTES: int = int(os.getenv("MAX_FRAME_SIZE_BYTES", str(1 * 1024 * 1024)))  # 1MB

    # Game
    GAME_DURATION_SECONDS: int = int(os.getenv("GAME_DURATION_SECONDS", "30"))
    GAME_POINTS_PER_CORRECT: int = int(os.getenv("GAME_POINTS_PER_CORRECT", "100"))

    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"

    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-for-signvista-hackathon-2024")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week 


settings = Settings()
