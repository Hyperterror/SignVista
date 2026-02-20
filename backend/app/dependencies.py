from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.jwt_utils import decode_access_token
from app.session_store import USERS
from typing import Dict

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

import logging
logger = logging.getLogger(__name__)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Dependency to get current authenticated user from JWT."""
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
        
    user = USERS.get(phone)
    if user is None:
        logger.warning(f"Auth failed: User with phone {phone} not found in memory (Server restart?)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired - please login again",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user
