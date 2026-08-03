from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class RegisterRequest(BaseModel):
    """
    Schema payload cho API đăng ký tài khoản.
    Hỗ trợ 2 chế độ đối tượng: 'student' (Sinh viên IUH) và 'public' (Người dùng công cộng).
    """
    fullName: str = Field(..., min_length=2, max_length=255, description="Họ và tên người dùng")
    identifier: str = Field(..., min_length=3, max_length=255, description="Email hoặc mã sinh viên")
    password: str = Field(..., min_length=6, description="Mật khẩu ít nhất 6 ký tự")
    confirmPassword: str = Field(..., min_length=6, description="Xác nhận mật khẩu")
    userType: str = Field("student", description="'student' (Sinh viên IUH) hoặc 'public' (Người dùng công cộng)")
    studentCode: Optional[str] = Field(None, description="Mã số sinh viên (chỉ bắt buộc với Sinh viên IUH)")
    department: Optional[str] = Field(None, description="Khoa / Viện")
    major: Optional[str] = Field(None, description="Ngành học")


class LoginRequest(BaseModel):
    """Schema payload cho API đăng nhập."""
    identifier: str = Field(..., description="Email hoặc mã sinh viên")
    password: str = Field(..., description="Mật khẩu đăng nhập")
    rememberMe: Optional[bool] = False


class LinkGoogleRequest(BaseModel):
    """Schema payload cho API liên kết tài khoản Google ID."""
    idToken: str = Field(..., description="ID Token nhận từ Google OAuth / Sign-in")


class SetPasswordRequest(BaseModel):
    """Schema payload cho API thiết lập mật khẩu đăng nhập (cho tài khoản Google chưa có mật khẩu)."""
    newPassword: str = Field(..., min_length=6, description="Mật khẩu mới ít nhất 6 ký tự")
    confirmPassword: str = Field(..., min_length=6, description="Xác nhận mật khẩu mới")


class UpdateProfileRequest(BaseModel):
    """
    Schema payload cho API cập nhật thông tin hồ sơ cá nhân.
    Hỗ trợ thay đổi thông tin cá nhân và học vụ theo chế độ đối tượng.
    """
    fullName: Optional[str] = Field(None, min_length=2, max_length=255, description="Họ và tên mới")
    phoneNumber: Optional[str] = Field(None, max_length=20, description="Số điện thoại liên hệ")
    studentCode: Optional[str] = Field(None, max_length=50, description="Mã số sinh viên")
    department: Optional[str] = Field(None, max_length=150, description="Khoa / Viện")
    major: Optional[str] = Field(None, max_length=150, description="Ngành học")
    avatarUrl: Optional[str] = Field(None, description="Đường dẫn ảnh đại diện")


class ForgotPasswordRequest(BaseModel):
    """Schema payload gửi yêu cầu mã OTP khôi phục mật khẩu qua Email."""
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="Email tài khoản cần khôi phục")


class ResetPasswordRequest(BaseModel):
    """Schema payload xác nhận OTP và đặt lại mật khẩu mới."""
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="Email tài khoản khôi phục")
    otp: str = Field(..., min_length=4, max_length=10, description="Mã OTP khôi phục mật khẩu")
    newPassword: str = Field(..., min_length=6, description="Mật khẩu mới ít nhất 6 ký tự")
    confirmPassword: str = Field(..., min_length=6, description="Xác nhận mật khẩu mới")


class UserResponse(BaseModel):
    """Schema chuẩn trả về thông tin User cho Frontend (API Contract-First)."""
    id: str
    fullName: str
    email: str
    studentCode: Optional[str] = None
    department: Optional[str] = None
    major: Optional[str] = None
    phoneNumber: Optional[str] = None
    role: str = "student"
    avatarUrl: Optional[str] = None
    google_id: Optional[str] = None
    googleId: Optional[str] = None
    password_hash: Optional[str] = None
    passwordHash: Optional[str] = None
    createdAt: Optional[str] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Schema chuẩn trả về khi đăng nhập hoặc đăng ký thành công."""
    user: UserResponse
    token: str


class ErrorDetail(BaseModel):
    """Schema chi tiết lỗi trả về."""
    message: str
    code: Optional[str] = None


class ApiResult(BaseModel, Generic[T]):
    """
    Schema bao bọc chuẩn API Contract-First:
    - Thành công: { ok: true, data: T }
    - Thất bại: { ok: false, error: { message, code } }
    """
    ok: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None

    @classmethod
    def success(cls, data: T) -> "ApiResult[T]":
        return cls(ok=True, data=data)

    @classmethod
    def fail(cls, message: str, code: Optional[str] = None) -> "ApiResult[Any]":
        return cls(ok=False, error=ErrorDetail(message=message, code=code))
