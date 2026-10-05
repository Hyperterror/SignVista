from fastapi import APIRouter, HTTPException, Depends, Response
from app.schemas import AuthRegisterRequest, AuthLoginRequest, AuthResponse
from app.session_store import register_user, login_user
from app.database import SessionLocal
from app.models import User
from app.config import settings
from app.jwt_utils import create_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse)
async def auth_register(request: AuthRegisterRequest, response: Response):
    """Register a new user."""
    success, message, session = register_user(request.model_dump())

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Get user details for response — always close the connection
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == request.phone).first()
        if not user:
            raise HTTPException(status_code=500, detail="User registered but could not be retrieved")
    finally:
        db.close()

    access_token = create_access_token(data={"sub": user.phone, "sessionId": session.session_id})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return AuthResponse(
        status="ok",
        sessionId=session.session_id,
        user_name=user.name,
        email=user.email,
        access_token=access_token,
        token_type="bearer",
        message="Account created successfully",
    )


@router.post("/login", response_model=AuthResponse)
async def auth_login(request: AuthLoginRequest, response: Response):
    """Authenticate existing user."""
    success, message, session = login_user(request.phone, request.password)

    if not success:
        raise HTTPException(status_code=401, detail=message)

    # Get user details — always close the connection
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == request.phone).first()
        if not user:
            raise HTTPException(status_code=500, detail="Login succeeded but user not found")
    finally:
        db.close()

    access_token = create_access_token(data={"sub": user.phone, "sessionId": session.session_id})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return AuthResponse(
        status="ok",
        sessionId=session.session_id,
        user_name=user.name,
        email=user.email,
        access_token=access_token,
        token_type="bearer",
        message="Logged in successfully",
    )


@router.post("/logout")
async def auth_logout(response: Response):
    """Logout endpoint — clears the auth cookie."""
    response.delete_cookie("access_token")
    return {"status": "ok", "message": "Logged out"}
