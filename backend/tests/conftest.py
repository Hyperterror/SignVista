"""
Shared test fixtures and helpers for SignVista backend tests.
"""

import base64
import os
import sys

import numpy as np
import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.session_store import clear_all_sessions


@pytest.fixture
def client():
    """FastAPI test client."""
    clear_all_sessions()
    with TestClient(app) as c:
        yield c
    clear_all_sessions()


def make_fake_frame() -> str:
    """Create a valid base64-encoded JPEG for testing."""
    # Create a simple 200x200 image
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[:, :] = [100, 150, 200]  # Fill with color

    import cv2
    _, buffer = cv2.imencode(".jpg", img)
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


@pytest.fixture
def fake_frame() -> str:
    """Fixture wrapper for make_fake_frame."""
    return make_fake_frame()


def make_invalid_base64() -> str:
    """Create invalid base64 data."""
    return "data:image/jpeg;base64,notvalidbase64!!!"
