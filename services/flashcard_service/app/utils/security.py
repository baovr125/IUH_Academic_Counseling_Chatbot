"""Xác thực JWT dùng chung cho các service phía sau Kong.

Nguyên tắc:
- Chỉ tin token Bearer do auth-service ký (HS256, issuer ``iuh-auth-service``, bắt buộc ``exp``).
- Không tin bất kỳ header danh tính nào do client tự gửi (``X-User-ID``, ``X-User-Role``...).
- ``JWT_SECRET_KEY`` là bắt buộc, không có giá trị mặc định; ``validate_security_config()``
  được gọi khi service khởi động để service không chạy với cấu hình yếu.

File này được giữ giống hệt nhau ở các service (chatbot, flashcard, doc_translation,
realtime_translation); khi sửa hãy sửa đồng bộ cả bốn bản.
"""
import os
from typing import Optional

from fastapi import Header, HTTPException, Query, status
from jose import JWTError, jwt

from app.utils.logger import logger

ALGORITHM = "HS256"
TOKEN_ISSUER = "iuh-auth-service"
MIN_SECRET_LENGTH = 32
# Các giá trị đã từng xuất hiện trong repo/tài liệu: coi là đã lộ, không bao giờ được dùng.
KNOWN_INSECURE_SECRETS = frozenset({
    "super-secret-key-iuh-chatbot-2026",
    "your-secret-key",
    "changeme",
    "secret",
})


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret) < MIN_SECRET_LENGTH or secret in KNOWN_INSECURE_SECRETS:
        raise RuntimeError(
            "JWT_SECRET_KEY chưa được cấu hình an toàn: cần đặt biến môi trường với chuỗi "
            f"ngẫu nhiên dài ít nhất {MIN_SECRET_LENGTH} ký tự và không phải giá trị mẫu."
        )
    return secret


def validate_security_config() -> None:
    """Gọi khi khởi động service; ném RuntimeError nếu cấu hình bảo mật không hợp lệ."""
    get_jwt_secret()


def _unauthorized(detail: str = "Không thể xác thực danh tính người dùng. Vui lòng đăng nhập lại.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


def decode_token(token: str) -> Optional[dict]:
    """Giải mã và kiểm tra chữ ký, ``exp`` (bắt buộc) và ``iss``. Trả None nếu không hợp lệ."""
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[ALGORITHM],
            issuer=TOKEN_ISSUER,
            options={"verify_aud": False, "require_exp": True, "require_iss": True},
        )
    except JWTError as e:
        logger.warning(f"Invalid JWT Token: {e}")
        return None
    if not (payload.get("sub") or payload.get("user_id")):
        return None
    return payload


def _user_from_request(authorization: Optional[str], token_query: Optional[str]) -> Optional[dict]:
    # Header Authorization được ưu tiên; ?token= chỉ dành cho EventSource/<audio> không gắn được header.
    token = _bearer_token(authorization) or (token_query.strip() if token_query else None)
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return {"user_id": str(payload.get("sub") or payload.get("user_id")), "role": payload.get("role")}


def get_current_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token: Optional[str] = Query(None),
) -> str:
    user = _user_from_request(authorization, token)
    if not user:
        raise _unauthorized()
    return user["user_id"]


def get_optional_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token: Optional[str] = Query(None),
) -> str:
    user = _user_from_request(authorization, token)
    return user["user_id"] if user else "anonymous"


get_optional_current_user_id = get_optional_user_id


def get_current_admin_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token: Optional[str] = Query(None),
) -> str:
    user = _user_from_request(authorization, token)
    if not user:
        raise _unauthorized()
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Truy cập bị từ chối. Chỉ Admin mới có quyền thực hiện thao tác này.",
        )
    return user["user_id"]
