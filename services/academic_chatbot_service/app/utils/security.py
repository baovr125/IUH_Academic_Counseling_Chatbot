import os
from typing import Optional
from fastapi import Header, HTTPException, status
from jose import jwt, JWTError
from app.utils.logger import logger

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-iuh-chatbot-2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def extract_user_info_from_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
        user_id = payload.get("sub") or payload.get("user_id")
        role = payload.get("role")
        if user_id:
            return {"user_id": str(user_id), "role": role}
        return None
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
        user_info = extract_user_info_from_token(token)
        if user_info and user_info.get("user_id"):
            return user_info["user_id"]

    # 2. Check X-User-ID header (for direct inter-service communication)
    if x_user_id and x_user_id.strip() and x_user_id != "anonymous":
        return x_user_id.strip()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực danh tính người dùng. Vui lòng đăng nhập lại.",
        headers={"WWW-Authenticate": "Bearer"}
    )

def get_optional_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> str:
    try:
        return get_current_user_id(authorization, x_user_id)
    except HTTPException:
        return "anonymous"

get_optional_current_user_id = get_optional_user_id


def get_current_admin_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    token: Optional[str] = None
) -> str:
    # 1. Check token from query param (for EventSource/SSE)
    if token:
        user_info = extract_user_info_from_token(token)
        if user_info and user_info.get("user_id") and user_info.get("role") == "admin":
            return user_info["user_id"]

    # 2. Check Authorization header
    if authorization and authorization.startswith("Bearer "):
        bearer_token = authorization.split(" ")[1]
        user_info = extract_user_info_from_token(bearer_token)
        if user_info and user_info.get("user_id"):
            if user_info.get("role") == "admin":
                return user_info["user_id"]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Truy cập bị từ chối. Chỉ Admin mới có quyền thực hiện thao tác này."
            )

    # 3. Check X headers (for direct inter-service communication via Kong Gateway)
    if x_user_id and x_user_id.strip() and x_user_id != "anonymous":
        if x_user_role == "admin":
            return x_user_id.strip()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Truy cập bị từ chối. Chỉ Admin mới có quyền thực hiện thao tác này."
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực danh tính người dùng. Vui lòng đăng nhập lại.",
        headers={"WWW-Authenticate": "Bearer"}
    )
