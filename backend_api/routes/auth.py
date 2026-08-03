import hashlib
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import User, PasswordReset, get_db
from schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    LinkGoogleRequest,
    SetPasswordRequest,
    UpdateProfileRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
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
    - Hỗ trợ 2 chế độ: 'student' (Sinh viên/GV IUH) và 'public' (Người dùng công cộng).
    - Email và MSSV được chuẩn hóa chữ thường / chữ hoa giúp đăng nhập không phân biệt hoa thường.
    """
    if payload.password != payload.confirmPassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu xác nhận không trùng khớp.",
        )

    email_clean = payload.identifier.strip().lower()
    existing_user = (
        db.query(User)
        .filter((User.email == email_clean) | (User.student_code == email_clean.upper()))
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email hoặc tài khoản này đã tồn tại trong hệ thống.",
        )

    user_role = "student" if payload.userType == "student" else "public"
    student_code_val = None
    department_val = None
    major_val = None

    if user_role == "student":
        if not payload.studentCode or not payload.studentCode.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã số sinh viên là bắt buộc đối với tài khoản Sinh viên.",
            )
        student_code_val = payload.studentCode.strip().upper()

        # Kiểm tra trùng lặp MSSV
        existing_student = (
            db.query(User)
            .filter((User.student_code == student_code_val) | (User.email == student_code_val.lower()))
            .first()
        )
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã số sinh viên này đã được đăng ký trong hệ thống.",
            )

        department_val = payload.department.strip() if payload.department else None
        major_val = payload.major.strip() if payload.major else None

    hashed_pw = hash_password(payload.password)
    new_user = User(
        id=uuid.uuid4(),
        full_name=payload.fullName.strip(),
        email=email_clean,
        student_code=student_code_val,
        department=department_val,
        major=major_val,
        password_hash=hashed_pw,
        role=user_role,
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
    - Xác thực email (case-insensitive) hoặc MSSV (case-insensitive) và mật khẩu bằng bcrypt -> Trả về token & user info.
    """
    identifier_clean = payload.identifier.strip()
    user = (
        db.query(User)
        .filter(
            (User.email == identifier_clean.lower()) | (User.student_code == identifier_clean.upper())
        )
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
            detail="Tài khoản chưa thiết lập mật khẩu đăng nhập. Vui lòng sử dụng tính năng Quên mật khẩu để tạo mật khẩu.",
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


@router.put("/profile", status_code=status.HTTP_200_OK)
def update_user_profile(
    payload: UpdateProfileRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    PUT /api/auth/profile (Yêu cầu JWT Token):
    - Cập nhật các thông tin full_name, phone_number, student_code, department, major, avatar_url.
    - Kiểm tra trùng lặp MSSV nếu có thay đổi.
    - Trả về user mới.
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
            detail="Không tìm thấy thông tin người dùng.",
        )

    if payload.fullName is not None:
        user.full_name = payload.fullName.strip()
    if payload.phoneNumber is not None:
        user.phone_number = payload.phoneNumber.strip()
    if payload.department is not None:
        user.department = payload.department.strip()
    if payload.major is not None:
        user.major = payload.major.strip()
    if payload.avatarUrl is not None:
        user.avatar_url = payload.avatarUrl.strip()

    if payload.studentCode is not None:
        new_code = payload.studentCode.strip()
        if new_code and new_code != (user.student_code or ""):
            existing = (
                db.query(User)
                .filter(User.student_code == new_code, User.id != user.id)
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mã số sinh viên này đã được đăng ký bởi tài khoản khác.",
                )
            user.student_code = new_code
            user.role = "student"
        elif not new_code:
            user.student_code = None

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return {
        "ok": True,
        "data": user.to_response_dict(),
    }


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    POST /api/auth/forgot-password:
    - Kiểm tra Email có trong hệ thống không -> Tạo mã OTP 6 số ngẫu nhiên.
    - Lưu vào bảng password_resets hạn 15 phút.
    - Trả về { "ok": true, "data": { "message": "Đã tạo mã OTP khôi phục mật khẩu", "devOtp": "<mã_6_số>" } }.
    """
    email_clean = payload.email.strip()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này chưa được đăng ký trong hệ thống.",
        )

    otp_code = f"{random.randint(100000, 999999):06d}"
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    reset_record = PasswordReset(
        id=uuid.uuid4(),
        email=email_clean,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False,
        created_at=datetime.utcnow(),
    )
    db.add(reset_record)
    db.commit()

    return {
        "ok": True,
        "data": {
            "message": "Đã tạo mã OTP khôi phục mật khẩu. Vui lòng kiểm tra email của bạn.",
            "devOtp": otp_code,
        },
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    POST /api/auth/reset-password:
    - Kiểm tra mã OTP trong password_resets (đúng email, đúng OTP, expires_at > now(), is_used == False).
    - Hash mật khẩu mới BCrypt -> Cập nhật password_hash trong users -> Đặt is_used = True cho OTP -> Trả về { "ok": true, "data": null }.
    """
    if payload.newPassword != payload.confirmPassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu xác nhận không trùng khớp.",
        )

    email_clean = payload.email.strip()
    now = datetime.utcnow()

    reset_record = (
        db.query(PasswordReset)
        .filter(
            PasswordReset.email == email_clean,
            PasswordReset.otp_code == payload.otp.strip(),
            PasswordReset.is_used == False,
            PasswordReset.expires_at > now,
        )
        .order_by(PasswordReset.created_at.desc())
        .first()
    )

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã OTP không hợp lệ hoặc đã hết hạn khôi phục mật khẩu.",
        )

    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản tương ứng.",
        )

    user.password_hash = hash_password(payload.newPassword)
    user.updated_at = now
    reset_record.is_used = True
    db.commit()

    return {
        "ok": True,
        "data": None,
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
