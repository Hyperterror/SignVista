"""
Shared test fixtures and helpers for SignVista backend tests.

Tests run against an isolated temporary SQLite database — never the
developer's signvista.db.
"""

import base64
import itertools
import os
import sys
import tempfile

# ── Environment must be configured before the app is imported ──
_TEST_DB_DIR = tempfile.mkdtemp(prefix="signvista-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TEST_DB_DIR, "test.db").replace("\\", "/")
os.environ.setdefault("ENV", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["SKIP_ML_WARMUP"] = "1"
os.environ["FRAME_PROCESS_FPS"] = "0"  # no throttling in tests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.session_store import clear_all_sessions  # noqa: E402

_phone_counter = itertools.count(9000000000)


@pytest.fixture
def client():
    """FastAPI test client (unauthenticated)."""
    clear_all_sessions()
    with TestClient(app) as c:
        yield c
    clear_all_sessions()


def register(client: TestClient, name: str = "Test User", password: str = "password123", **extra) -> dict:
    """Register a fresh user on `client` (sets the auth cookie). Returns the response JSON."""
    phone = extra.pop("phone", str(next(_phone_counter)))
    payload = {
        "name": name,
        "email": extra.pop("email", f"user{phone}@example.com"),
        "phone": phone,
        "password": password,
        **extra,
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    data["phone"] = phone
    data["password"] = password
    return data


@pytest.fixture
def auth_client(client):
    """Client logged in as a freshly registered user; `auth_client.user_id` is set."""
    data = register(client)
    client.user_id = data["sessionId"]
    client.user = data
    return client


def make_fake_frame(size: int = 200) -> str:
    """A valid base64-encoded JPEG for testing."""
    import cv2

    img = np.zeros((size, size, 3), dtype=np.uint8)
    img[:, :] = [100, 150, 200]
    _, buffer = cv2.imencode(".jpg", img)
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")


@pytest.fixture
def fake_frame() -> str:
    return make_fake_frame()


def make_invalid_base64() -> str:
    return "data:image/jpeg;base64,notvalidbase64!!!"
