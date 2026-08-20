import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from jose import JWTError, jwt
from fastapi import HTTPException, status, Security, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.logger import logger

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-iuh-chatbot-2026")
ALGORITHM = "HS256"

security_scheme = HTTPBearer(auto_error=True)
optional_security_scheme = HTTPBearer(auto_error=False)

def verify_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn.",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> str:
    if x_user_id:
        return x_user_id
    token = credentials.credentials
    payload = verify_access_token(token)
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token thiếu định danh người dùng (sub).",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return str(user_id)

def get_optional_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security_scheme),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Optional[str]:
    if x_user_id:
        return x_user_id
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = verify_access_token(credentials.credentials)
        return str(payload.get("sub")) if payload.get("sub") else None
    except Exception:
        return None
