from fastapi import APIRouter, HTTPException, Depends
from app.schemas import AuthRegisterRequest, AuthLoginRequest, AuthResponse
from app.session_store import register_user, login_user, USERS
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthResponse)
async def auth_register(request: AuthRegisterRequest):
    """Register a new user."""
    success, message, session = register_user(request.dict())
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Get user details for response
    user = USERS[request.phone]
    
    # Generate JWT
    from app.jwt_utils import create_access_token
    access_token = create_access_token(data={"sub": user["phone"], "sessionId": session.session_id})
    
    return AuthResponse(
        status="ok",
        sessionId=session.session_id,
        user_name=user["name"],
        email=user["email"],
        access_token=access_token,
        token_type="bearer",
        message="Account created successfully"
    )

@router.post("/login", response_model=AuthResponse)
async def auth_login(request: AuthLoginRequest):
    """Authenticate existing user."""
    success, message, session = login_user(request.phone, request.password)
    
    if not success:
        # Check if it was user not found or wrong password for security
        # But for UX we might be specific in hackathon
        raise HTTPException(status_code=401, detail=message)
    
    # Get user details
    user = USERS[request.phone]
    
    # Generate JWT
    from app.jwt_utils import create_access_token
    access_token = create_access_token(data={"sub": user["phone"], "sessionId": session.session_id})
    
    return AuthResponse(
        status="ok",
        sessionId=session.session_id,
        user_name=user["name"],
        email=user["email"],
        access_token=access_token,
        token_type="bearer",
        message="Logged in successfully"
    )

@router.post("/logout")
async def auth_logout():
    """Logout endpoint."""
    return {"status": "ok", "message": "Logged out"}
