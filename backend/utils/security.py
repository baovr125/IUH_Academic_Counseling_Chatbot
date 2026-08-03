import os
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# =====================================================================
# CẤU HÌNH JOSE JWT & BCRYPT
# =====================================================================
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "iuh_portal_ai_secret_key_2026_super_secure_default")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")) # 7 ngày

security_scheme = HTTPBearer(auto_error=True)
optional_security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Mã hóa mật khẩu sử dụng Bcrypt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """Xác thực mật khẩu so với hash đã lưu trong DB."""
    if not hashed_password:
        return False
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Tạo JWT Access Token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Dict[str, Any]:
    """Giải mã và xác thực JWT Token."""
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
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
) -> str:
    """Dependency lấy user_id (hoặc email) từ Bearer Token."""
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
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security_scheme)
) -> Optional[str]:
    """Dependency lấy user_id (không bắt buộc, trả về None nếu không có token)."""
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = verify_access_token(credentials.credentials)
        return str(payload.get("sub")) if payload.get("sub") else None
    except HTTPException:
        return None
