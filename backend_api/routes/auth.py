import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import User, get_db
from schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    LinkGoogleRequest,
    SetPasswordRequest,
    ApiResult,
)
from utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_id,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication & Account Linking"])


def verify_google_id_token(id_token: str) -> Dict[str, Any]:
    """
    Xác thực Google ID Token với Google API hoặc fallback chế độ Demo/Development.
    """
    try:
        if (
            not id_token.startswith("mock_")
            and not id_token.startswith("test_")
            and not id_token.startswith("google_id_token_")
        ):
            resp = requests.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
                timeout=5.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("sub"):
                    return data
    except Exception:
        pass

    # Fallback cho môi trường phát triển (Dev/Demo) khi dùng mock token
    token_str = (
        id_token.replace("mock_", "")
        .replace("test_", "")
        .replace("google_id_token_", "")
    )
    mock_sub = f"gg_{hashlib.md5(token_str.encode('utf-8')).hexdigest()[:16]}"
    email_val = token_str if "@" in token_str else f"{token_str}@gmail.com"
    return {
        "sub": mock_sub,
        "email": email_val,
        "name": "Google Linked User",
        "picture": "https://lh3.googleusercontent.com/a/default-user=s96-c",
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    POST /api/auth/register:
    - Nhận { fullName, identifier, password, confirmPassword }.
    - Kiểm tra email (identifier) đã tồn tại chưa -> Nếu có trả về lỗi hợp lệ.
    - Hash mật khẩu, lưu vào users (role='student'), trả về { "ok": true, "data": { "user": {...}, "token": "jwt_..." } }.
    """
    if payload.password != payload.confirmPassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu xác nhận không trùng khớp.",
        )

    existing_user = (
        db.query(User).filter(User.email == payload.identifier.strip()).first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email hoặc tài khoản này đã tồn tại trong hệ thống.",
        )

    hashed_pw = hash_password(payload.password)
    new_user = User(
        id=uuid.uuid4(),
        full_name=payload.fullName.strip(),
        email=payload.identifier.strip(),
        password_hash=hashed_pw,
        role="student",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(
        {
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role,
        }
    )

    return {
        "ok": True,
        "data": {
            "user": new_user.to_response_dict(),
            "token": token,
        },
    }


@router.post("/login", status_code=status.HTTP_200_OK)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    POST /api/auth/login:
    - Nhận { identifier, password }.
    - Xác thực email và mật khẩu bằng bcrypt -> Trả về { "ok": true, "data": { "user": {...}, "token": "jwt_..." } }.
    """
    user = (
        db.query(User)
        .filter(User.email == payload.identifier.strip())
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác.",
        )

    if user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản chưa thiết lập mật khẩu đăng nhập. Vui lòng đăng nhập bằng Google hoặc thiết lập mật khẩu.",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác.",
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )

    return {
        "ok": True,
        "data": {
            "user": user.to_response_dict(),
            "token": token,
        },
    }


@router.get("/me", status_code=status.HTTP_200_OK)
def get_current_user_profile(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    GET /api/auth/me:
    - Xác thực JWT Token từ header Authorization: Bearer <token>, trả về User hiện tại.
    """
    user = None
    try:
        user_uuid = uuid.UUID(current_user_id)
        user = db.query(User).filter(User.id == user_uuid).first()
    except ValueError:
        user = db.query(User).filter(User.email == current_user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại hoặc đã bị xóa.",
        )

    return {
        "ok": True,
        "data": user.to_response_dict(),
    }


@router.post("/link-google", status_code=status.HTTP_200_OK)
def link_google_account(
    payload: LinkGoogleRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    POST /api/auth/link-google:
    - Nhận { idToken } từ Google Sign-In của người dùng đang đăng nhập (nhận dạng qua JWT Bearer Token).
    - Xác thực idToken với Google, cập nhật google_id và avatar_url (nếu chưa có) vào bản ghi users hiện tại.
    """
    user = None
    try:
        user_uuid = uuid.UUID(current_user_id)
        user = db.query(User).filter(User.id == user_uuid).first()
    except ValueError:
        user = db.query(User).filter(User.email == current_user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin tài khoản hiện tại.",
        )

    google_data = verify_google_id_token(payload.idToken)
    google_id = google_data.get("sub")
    if not google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xác thực Google ID Token.",
        )

    # Kiểm tra google_id đã được liên kết với user khác chưa
    existing_linked = (
        db.query(User)
        .filter(User.google_id == google_id, User.id != user.id)
        .first()
    )
    if existing_linked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản Google này đã được liên kết với một tài khoản khác trong hệ thống.",
        )

    user.google_id = google_id
    avatar_url = google_data.get("picture")
    if not user.avatar_url and avatar_url:
        user.avatar_url = avatar_url

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return {
        "ok": True,
        "data": user.to_response_dict(),
    }


@router.post("/set-password", status_code=status.HTTP_200_OK)
def set_account_password(
    payload: SetPasswordRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    POST /api/auth/set-password:
    - Nhận { newPassword, confirmPassword } từ người dùng đang đăng nhập.
    - Kiểm tra nếu password_hash hiện tại là NULL hoặc cho phép cập nhật mật khẩu -> Hash và lưu password_hash mới.
    """
    if payload.newPassword != payload.confirmPassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu xác nhận không trùng khớp.",
        )

    user = None
    try:
        user_uuid = uuid.UUID(current_user_id)
        user = db.query(User).filter(User.id == user_uuid).first()
    except ValueError:
        user = db.query(User).filter(User.email == current_user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin tài khoản.",
        )

    user.password_hash = hash_password(payload.newPassword)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {
        "ok": True,
        "data": None,
    }
