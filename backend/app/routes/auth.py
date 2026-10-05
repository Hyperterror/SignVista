"""
SignVista — Authentication Routes

POST /api/auth/register   — create account, sets HttpOnly session cookie
POST /api/auth/login      — authenticate, sets HttpOnly session cookie
POST /api/auth/logout     — revoke all tokens for the user and clear the cookie
GET  /api/auth/me         — current user profile
POST /api/auth/ws-ticket  — short-lived ticket for opening authenticated WebSockets
"""

import logging
import time
import uuid
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import ACCESS_COOKIE_NAME, get_current_user, resolve_user, _token_from_request
from app.jwt_utils import create_access_token, create_ws_ticket
from app.models import User, UserSettings, UserStats
from app.rate_limit import client_ip, enforce, limiter
from app.schemas import AuthLoginRequest, AuthRegisterRequest, AuthResponse, MeResponse, WsTicketResponse
from app.security import burn_password_check, hash_password, needs_rehash, verify_password
from app.session_store import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

INVALID_CREDENTIALS = "Invalid phone number or password"
LOGIN_FAILURE_WINDOW = 15 * 60
LOGIN_FAILURE_LIMIT = 5


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def _auth_response(user: User, message: str) -> AuthResponse:
    return AuthResponse(
        status="ok",
        sessionId=user.user_id,
        user_name=user.name,
        email=user.email,
        token_type="cookie",
        message=message,
    )


@router.post("/register", response_model=AuthResponse)
def auth_register(payload: AuthRegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    """Register a new user."""
    enforce(f"register:{client_ip(request)}", limit=10, window_seconds=3600,
            detail="Too many registration attempts. Please try again later.")

    if db.query(User.id).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")
    if db.query(User.id).filter(func.lower(User.email) == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        user_id=uuid.uuid4().hex[:12],
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        preferred_language=payload.preferred_language,
        created_at=time.time(),
        token_version=0,
    )
    db.add(user)
    db.add(UserStats(user_id=user.user_id))
    db.add(UserSettings(user_id=user.user_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Phone number already registered")
    except Exception:
        db.rollback()
        logger.exception("Registration failed")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")

    db.refresh(user)
    get_session(user.user_id)
    _set_auth_cookie(response, create_access_token(user.user_id, user.token_version))
    return _auth_response(user, "Account created successfully")


@router.post("/login", response_model=AuthResponse)
def auth_login(payload: AuthLoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    """Authenticate an existing user."""
    ip = client_ip(request)
    enforce(f"login:{ip}", limit=20, window_seconds=60, detail="Too many login attempts. Please wait a minute.")

    failure_key = f"login-fail:{payload.phone}"
    if limiter.count(failure_key, LOGIN_FAILURE_WINDOW) >= LOGIN_FAILURE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many failed attempts for this account. Please try again in 15 minutes.",
            headers={"Retry-After": str(LOGIN_FAILURE_WINDOW)},
        )

    user = db.query(User).filter(User.phone == payload.phone).first()
    if user is None:
        burn_password_check(payload.password)
        limiter.hit(failure_key, LOGIN_FAILURE_LIMIT + 1, LOGIN_FAILURE_WINDOW)
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS)

    if not verify_password(payload.password, user.password_hash):
        limiter.hit(failure_key, LOGIN_FAILURE_LIMIT + 1, LOGIN_FAILURE_WINDOW)
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS)

    limiter.reset(failure_key)

    # Transparently upgrade legacy sha256_crypt hashes to bcrypt
    if needs_rehash(user.password_hash) and len(payload.password.encode("utf-8")) <= 72:
        user.password_hash = hash_password(payload.password)
        db.commit()
        db.refresh(user)

    get_session(user.user_id)
    _set_auth_cookie(response, create_access_token(user.user_id, user.token_version or 0))
    return _auth_response(user, "Logged in successfully")


@router.post("/logout")
def auth_logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Revoke every token issued to this user and clear the auth cookie."""
    current = resolve_user(_token_from_request(request))
    if current is not None:
        user = db.query(User).filter(User.user_id == current["user_id"]).first()
        if user is not None:
            user.token_version = (user.token_version or 0) + 1
            db.commit()
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/", samesite="lax",
                           secure=settings.COOKIE_SECURE, httponly=True)
    return {"status": "ok", "message": "Logged out"}


@router.get("/me", response_model=MeResponse)
def auth_me(current_user: Dict = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return MeResponse(
        sessionId=current_user["user_id"],
        name=current_user["name"],
        email=current_user["email"],
        phone=current_user["phone"],
        preferred_language=current_user["preferred_language"] or "en",
        created_at=current_user["created_at"],
    )


@router.post("/ws-ticket", response_model=WsTicketResponse)
def auth_ws_ticket(current_user: Dict = Depends(get_current_user)):
    """
    Issue a short-lived ticket for WebSocket authentication.

    Browsers can't set headers on WebSocket handshakes and cookies may not
    reach a backend on a different host, so the frontend fetches a ticket
    (via the authenticated cookie) and passes it as `?ticket=`.
    """
    return WsTicketResponse(
        ticket=create_ws_ticket(current_user["user_id"], current_user["token_version"]),
        expires_in=settings.WS_TICKET_EXPIRE_SECONDS,
    )
