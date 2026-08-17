import os
from typing import Optional
from fastapi import Header, HTTPException, status
from jose import jwt, JWTError
from app.utils.logger import logger

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-iuh-chatbot-2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def extract_user_id_from_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
        user_id = payload.get("sub") or payload.get("user_id")
        return str(user_id) if user_id else None
    except JWTError as e:
        logger.warning(f"Invalid JWT Token: {e}")
        return None

def get_current_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> str:
    # 1. Check Authorization header
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        user_id = extract_user_id_from_token(token)
        if user_id:
            return user_id

    # 2. Check X-User-ID header (for direct inter-service communication)
    if x_user_id and x_user_id.strip() and x_user_id != "anonymous":
        return x_user_id.strip()

    # 3. Default demo/guest student user ID to ensure smooth experience
    return "default_student_user"

def get_optional_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> str:
    try:
        return get_current_user_id(authorization, x_user_id)
    except HTTPException:
        return "anonymous"
