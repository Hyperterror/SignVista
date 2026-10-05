import logging
from typing import Dict, Optional

from fastapi import HTTPException, Request, WebSocket, status

from app.config import settings
from app.database import SessionLocal
from app.jwt_utils import ACCESS_TOKEN_TYPE, WS_TICKET_TYPE, decode_token
from app.models import User

logger = logging.getLogger(__name__)

ACCESS_COOKIE_NAME = "access_token"


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _token_from_request(request: Request) -> Optional[str]:
    """HttpOnly cookie first, then `Authorization: Bearer <token>`."""
    cookie_token = request.cookies.get(ACCESS_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    auth = request.headers.get("Authorization", "")
    scheme, _, value = auth.partition(" ")
    if scheme.lower() == "bearer" and value:
        return value.strip()
    return None


def _user_dict(user: User) -> Dict:
    # Intentionally excludes password_hash
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "preferred_language": user.preferred_language,
        "created_at": user.created_at,
        "token_version": user.token_version or 0,
    }


def resolve_user(token: Optional[str], expected_type: str = ACCESS_TOKEN_TYPE) -> Optional[Dict]:
    """Validate a token and return the matching user dict, or None."""
    if not token:
        return None
    payload = decode_token(token, expected_type)
    if payload is None:
        return None
    user_id = payload.get("sub")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            return None
        # Tokens issued before the last logout / password change are revoked
        if payload.get("ver", 0) != (user.token_version or 0):
            return None
        return _user_dict(user)
    finally:
        db.close()


def get_current_user(request: Request) -> Dict:
    """
    Dependency returning the authenticated user.

    Declared sync on purpose: FastAPI runs it in the threadpool so the
    blocking DB lookup never stalls the event loop.
    """
    token = _token_from_request(request)
    if not token:
        raise _unauthorized("Not authenticated")
    user = resolve_user(token)
    if user is None:
        raise _unauthorized("Invalid or expired session - please login again")
    return user


def require_own_session(current_user: Dict, session_id: str) -> None:
    """403 unless the path/body session id belongs to the authenticated user."""
    if not session_id or current_user["user_id"] != session_id:
        raise HTTPException(status_code=403, detail="Unauthorized")


def origin_allowed(origin: Optional[str]) -> bool:
    # Browsers always send Origin on WebSocket handshakes; non-browser clients may omit it.
    return origin is None or origin in settings.CORS_ORIGINS


def authenticate_websocket(websocket: WebSocket) -> Optional[Dict]:
    """
    Authenticate a WebSocket handshake (blocking — call via run_in_threadpool).

    Accepts a short-lived `ticket` query parameter (from POST /api/auth/ws-ticket)
    or the access-token cookie. Rejects cross-site origins (CSWSH protection).
    """
    if not origin_allowed(websocket.headers.get("origin")):
        logger.warning(f"WebSocket rejected: origin {websocket.headers.get('origin')!r} not allowed")
        return None

    ticket = websocket.query_params.get("ticket")
    if ticket:
        return resolve_user(ticket, WS_TICKET_TYPE)
    return resolve_user(websocket.cookies.get(ACCESS_COOKIE_NAME), ACCESS_TOKEN_TYPE)
