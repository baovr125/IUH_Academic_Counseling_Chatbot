from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LinkGoogleRequest,
    SetPasswordRequest,
    UpdateProfileRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.utils.security import get_current_user_id
from app.services.auth_service import (
    register_user_logic,
    login_user_logic,
    get_user_profile_logic,
    update_user_profile_logic,
    forgot_password_logic,
    reset_password_logic,
    link_google_account_logic,
    set_account_password_logic,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication & Account Linking"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    """POST /api/auth/register: Đăng ký tài khoản Sinh viên / Công cộng."""
    return register_user_logic(payload, db)


@router.post("/login", status_code=status.HTTP_200_OK)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    """POST /api/auth/login: Đăng nhập bằng Email/MSSV và mật khẩu."""
    return login_user_logic(payload, db)


@router.get("/me", status_code=status.HTTP_200_OK)
def get_current_user_profile(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """GET /api/auth/me: Lấy thông tin tài khoản hiện tại từ JWT Token."""
    return get_user_profile_logic(current_user_id, db)


@router.put("/profile", status_code=status.HTTP_200_OK)
def update_user_profile(
    payload: UpdateProfileRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """PUT /api/auth/profile: Cập nhật thông tin cá nhân."""
    return update_user_profile_logic(payload, current_user_id, db)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """POST /api/auth/forgot-password: Yêu cầu mã OTP khôi phục mật khẩu."""
    return forgot_password_logic(payload, db)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """POST /api/auth/reset-password: Đặt lại mật khẩu mới bằng mã OTP."""
    return reset_password_logic(payload, db)


@router.post("/link-google", status_code=status.HTTP_200_OK)
def link_google_account(
    payload: LinkGoogleRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """POST /api/auth/link-google: Liên kết tài khoản Google Sign-In."""
    return link_google_account_logic(payload, current_user_id, db)


@router.post("/set-password", status_code=status.HTTP_200_OK)
def set_account_password(
    payload: SetPasswordRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """POST /api/auth/set-password: Thiết lập mật khẩu mới cho tài khoản."""
    return set_account_password_logic(payload, current_user_id, db)
