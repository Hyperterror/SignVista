import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import jwt

from app.config import settings

ACCESS_TOKEN_TYPE = "access"
WS_TICKET_TYPE = "ws"


def _encode(payload: Dict, expires_in: timedelta) -> str:
    now = datetime.now(timezone.utc)
    to_encode = {
        **payload,
        "iat": now,
        "exp": now + expires_in,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: str, token_version: int = 0, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token. `sub` is the immutable user_id."""
    return _encode(
        {"sub": user_id, "ver": token_version, "typ": ACCESS_TOKEN_TYPE},
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_ws_ticket(user_id: str, token_version: int = 0) -> str:
    """Short-lived token used only to open a WebSocket (passed as a query parameter)."""
    return _encode(
        {"sub": user_id, "ver": token_version, "typ": WS_TICKET_TYPE},
        timedelta(seconds=settings.WS_TICKET_EXPIRE_SECONDS),
    )


def decode_token(token: str, expected_type: str = ACCESS_TOKEN_TYPE) -> Optional[Dict]:
    """Decode and verify a JWT. Returns None if invalid, expired, or of the wrong type."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        return None
    if payload.get("typ") != expected_type:
        return None
    return payload


def decode_access_token(token: str) -> Optional[Dict]:
    """Backward-compatible alias."""
    return decode_token(token, ACCESS_TOKEN_TYPE)
