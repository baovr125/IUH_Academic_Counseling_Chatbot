from typing import Optional, Any, Dict, Generic, TypeVar
from pydantic import BaseModel, EmailStr, Field

T = TypeVar("T")


class RegisterRequest(BaseModel):
    fullName: str = Field(..., min_length=2, max_length=255, description="Họ và tên người dùng")
    identifier: str = Field(..., min_length=3, max_length=255, description="Email hoặc mã sinh viên")
    password: str = Field(..., min_length=6, description="Mật khẩu ít nhất 6 ký tự")
    confirmPassword: str = Field(..., min_length=6, description="Xác nhận mật khẩu")


class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email hoặc mã sinh viên")
    password: str = Field(..., description="Mật khẩu đăng nhập")
    rememberMe: Optional[bool] = False


class LinkGoogleRequest(BaseModel):
    idToken: str = Field(..., description="ID Token nhận từ Google OAuth / Sign-in")


class SetPasswordRequest(BaseModel):
    newPassword: str = Field(..., min_length=6, description="Mật khẩu mới ít nhất 6 ký tự")
    confirmPassword: str = Field(..., min_length=6, description="Xác nhận mật khẩu mới")


class UserResponse(BaseModel):
    id: str
    fullName: str
    email: str
    studentCode: Optional[str] = None
    role: str = "student"
    avatarUrl: Optional[str] = None
    google_id: Optional[str] = None
    googleId: Optional[str] = None
    password_hash: Optional[str] = None
    passwordHash: Optional[str] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: UserResponse
    token: str


class ErrorDetail(BaseModel):
    message: str
    code: Optional[str] = None


class ApiResult(BaseModel, Generic[T]):
    ok: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None

    @classmethod
    def success(cls, data: T) -> "ApiResult[T]":
        return cls(ok=True, data=data)

    @classmethod
    def fail(cls, message: str, code: Optional[str] = None) -> "ApiResult[Any]":
        return cls(ok=False, error=ErrorDetail(message=message, code=code))
