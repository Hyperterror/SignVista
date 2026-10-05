"""Security regression tests: legacy hashes, lockout, proxy-aware client IP, chat auth."""

import time
import uuid

import pytest
from passlib.hash import sha256_crypt
from starlette.requests import Request

from app.config import settings
from app.database import SessionLocal
from app.models import User, UserSettings, UserStats
from app.rate_limit import client_ip, limiter
from app.security import hash_password, needs_rehash, verify_password


def _legacy_user(password: str) -> str:
    """Insert a user whose password uses the pre-bcrypt sha256_crypt scheme."""
    phone = "7" + str(uuid.uuid4().int)[:9]
    with SessionLocal() as db:
        uid = uuid.uuid4().hex[:12]
        db.add(User(user_id=uid, name="Legacy", email=f"{uid}@example.com", phone=phone,
                    password_hash=sha256_crypt.hash(password), created_at=time.time()))
        db.add(UserStats(user_id=uid))
        db.add(UserSettings(user_id=uid))
        db.commit()
    return phone


def test_bcrypt_roundtrip():
    h = hash_password("correct horse")
    assert verify_password("correct horse", h)
    assert not verify_password("wrong", h)
    assert not needs_rehash(h)


def test_legacy_hash_login_upgrades_to_bcrypt(client):
    phone = _legacy_user("oldpassword1")
    r = client.post("/api/auth/login", json={"phone": phone, "password": "oldpassword1"})
    assert r.status_code == 200, r.text
    with SessionLocal() as db:
        stored = db.query(User).filter(User.phone == phone).first().password_hash
    assert stored.startswith("$2")  # upgraded to bcrypt
    # And the upgraded hash keeps working
    assert client.post("/api/auth/login", json={"phone": phone, "password": "oldpassword1"}).status_code == 200


def test_unknown_user_and_wrong_password_look_identical(client):
    phone = _legacy_user("secret-pass1")
    a = client.post("/api/auth/login", json={"phone": phone, "password": "nope"})
    b = client.post("/api/auth/login", json={"phone": "7000000001", "password": "nope"})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_account_lockout_after_repeated_failures(client, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    limiter.clear()
    phone = _legacy_user("right-pass1")
    for _ in range(5):
        assert client.post("/api/auth/login", json={"phone": phone, "password": "bad"}).status_code == 401
    r = client.post("/api/auth/login", json={"phone": phone, "password": "right-pass1"})
    assert r.status_code == 429
    limiter.clear()


def test_password_too_long_is_rejected(client):
    r = client.post("/api/auth/register", json={
        "name": "X", "email": "long@example.com", "phone": "9123400000", "password": "é" * 40,
    })
    assert r.status_code == 422


def _request(peer: str, xff: str = None) -> Request:
    headers = [(b"x-forwarded-for", xff.encode())] if xff else []
    return Request({"type": "http", "client": (peer, 1234), "headers": headers})


@pytest.mark.parametrize("peer,xff,expected", [
    ("8.8.8.8", "1.1.1.1", "8.8.8.8"),                 # untrusted peer: header ignored
    ("127.0.0.1", "9.9.9.9, 1.2.3.4", "1.2.3.4"),      # right-most untrusted hop
    ("127.0.0.1", None, "127.0.0.1"),
])
def test_client_ip(peer, xff, expected):
    assert client_ip(_request(peer, xff)) == expected


def test_chat_http_send_requires_existing_receiver(auth_client):
    r = auth_client.post("/api/chat/send", json={"receiver_id": "nobody", "content": "hi"})
    assert r.status_code == 400


def test_chat_message_between_users(client):
    from tests.conftest import register
    alice = register(client, name="Alice")
    bob = register(client, name="Bob")  # client is now Bob
    r = client.post("/api/chat/send", json={"receiver_id": alice["sessionId"], "content": "hello alice"})
    assert r.status_code == 200
    assert r.json()["sender_id"] == bob["sessionId"]
    msgs = client.get(f"/api/chat/messages/{alice['sessionId']}").json()
    assert [m["content"] for m in msgs] == ["hello alice"]


def test_like_is_once_per_user(auth_client):
    post = auth_client.post("/api/community/post", json={"content": "Hi #ISL"}).json()
    assert post["tags"] == []  # tags are explicit, not parsed server-side
    first = auth_client.post("/api/community/like", json={"postId": post["id"]}).json()
    second = auth_client.post("/api/community/like", json={"postId": post["id"]}).json()
    assert (first["likes"], first["liked"]) == (1, True)
    assert (second["likes"], second["liked"]) == (0, False)  # toggled off, never 2
