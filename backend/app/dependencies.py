from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.jwt_utils import decode_access_token
from typing import Dict, Optional
from app.database import SessionLocal
from app.models import User

import logging
logger = logging.getLogger(__name__)


class CookieBearer(OAuth2PasswordBearer):
    """OAuth2 bearer that reads the token from an HttpOnly cookie first, then falls back to the Authorization header."""
    async def __call__(self, request: Request) -> Optional[str]:
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            return cookie_token
        return await super().__call__(request)


oauth2_scheme = CookieBearer(tokenUrl="api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Dependency to get current authenticated user from JWT.
    
    Returns a dict with user_id, name, email, phone, preferred_language, created_at.
    Does NOT include the password hash.
    """
    payload = decode_access_token(token)
    if payload is None:
        logger.warning("Auth failed: Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    phone: str = payload.get("sub")
    if phone is None:
        logger.warning("Auth failed: Token missing 'sub' claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing identification",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if user is None:
            logger.warning(f"Auth failed: User with phone {phone} not found in DB")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired - please login again",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Return user info — intentionally excludes password_hash
        return {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "preferred_language": user.preferred_language,
            "created_at": user.created_at,
        }
    finally:
        db.close()
