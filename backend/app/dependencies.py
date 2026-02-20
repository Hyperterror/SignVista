from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.jwt_utils import decode_access_token
from app.session_store import USERS
from typing import Dict

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Dependency to get current authenticated user from JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    phone: str = payload.get("sub")
    if phone is None:
        raise credentials_exception
        
    user = USERS.get(phone)
    if user is None:
        raise credentials_exception
        
    return user
