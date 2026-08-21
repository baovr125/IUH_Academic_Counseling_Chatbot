import re
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator

# Regex kiểm tra tên hợp lệ (chữ cái tiếng Việt/Anh có dấu, khoảng trắng, dấu chấm, dấu gạch nối, dấu nháy đơn)
NAME_REGEX = re.compile(
    r"^[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂưăạảấầẩẫậắằẳẵặẹẻẽềềểỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴÝỶỸửữựỳỵýỷỹ\s\.\'\-]+$"
)
# Regex kiểm tra email tiêu chuẩn RFC 5322
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")
# Regex kiểm tra MSSV IUH: đúng 8 chữ số
STUDENT_CODE_REGEX = re.compile(r"^\d{8}$")
# Regex kiểm tra mật khẩu: tối thiểu 8 ký tự, có ít nhất 1 chữ cái và 1 chữ số
PASSWORD_LETTER_REGEX = re.compile(r"[A-Za-z]")
PASSWORD_DIGIT_REGEX = re.compile(r"\d")

IUH_EMAIL_DOMAINS = ("@student.iuh.edu.vn", "@iuh.edu.vn")


class RegisterRequest(BaseModel):
    full_name: str = Field(..., description="Họ và tên người dùng")
    email: str = Field(..., description="Địa chỉ email")
    password: str = Field(..., description="Mật khẩu (tối thiểu 8 ký tự, gồm chữ và số)")
    confirm_password: Optional[str] = Field(None, description="Xác nhận mật khẩu")
    role: str = Field("student", description="Vai trò: 'student' (Sinh viên/GV IUH) hoặc 'public' (Công cộng)")
    student_code: Optional[str] = Field(None, description="Mã số sinh viên (bắt buộc với role=student, 8 chữ số)")
    department: Optional[str] = Field(None, description="Khoa / Viện (bắt buộc với role=student)")
    major: Optional[str] = Field(None, description="Ngành học (bắt buộc với role=student)")

    @model_validator(mode="before")
    @classmethod
    def normalize_and_alias_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 1. Alias Họ tên
            full_name = data.get("full_name") or data.get("fullName") or data.get("name") or ""
            data["full_name"] = str(full_name).strip()

            # 2. Alias Email
            email = data.get("email") or data.get("identifier") or ""
            data["email"] = str(email).strip().lower()

            # 3. Alias Password & Confirm
            data["password"] = str(data.get("password") or "")
            if "confirmPassword" in data and "confirm_password" not in data:
                data["confirm_password"] = data.get("confirmPassword")

            # 4. Alias Role / UserType
            raw_role = data.get("role") or data.get("userType") or data.get("user_type")
            if raw_role:
                raw_role = str(raw_role).strip().lower()
                data["role"] = "public" if raw_role in ["public", "guest", "parent", "highschool"] else "student"
            else:
                data["role"] = "student"

            # 5. Alias Student Code / MSSV
            sc = data.get("student_code") or data.get("studentCode") or data.get("student_id") or data.get("studentId")
            data["student_code"] = str(sc).strip() if sc and str(sc).strip() else None

            # 6. Alias Department & Major
            dept = data.get("department") or data.get("faculty")
            maj = data.get("major")
            data["department"] = str(dept).strip() if dept and str(dept).strip() else None
            data["major"] = str(maj).strip() if maj and str(maj).strip() else None

        return data

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        clean = v.strip()
        if not (2 <= len(clean) <= 100):
            raise ValueError("Họ và tên bắt buộc từ 2 đến 100 ký tự.")
        if not NAME_REGEX.match(clean):
            raise ValueError("Họ và tên không được chứa ký tự đặc biệt bất hợp pháp.")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean or not EMAIL_REGEX.match(clean):
            raise ValueError("Email không đúng định dạng tiêu chuẩn.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Mật khẩu phải có tối thiểu 8 ký tự.")
        if not PASSWORD_LETTER_REGEX.search(v):
            raise ValueError("Mật khẩu phải bao gồm ít nhất một chữ cái.")
        if not PASSWORD_DIGIT_REGEX.search(v):
            raise ValueError("Mật khẩu phải bao gồm ít nhất một chữ số.")
        return v

    @model_validator(mode="after")
    def validate_audience_rules(self) -> "RegisterRequest":
        # 1. Kiểm tra xác nhận mật khẩu (nếu có truyền)
        if self.confirm_password is not None and self.password != self.confirm_password:
            raise ValueError("Mật khẩu xác nhận không khớp.")

        # 2. Quy tắc đối tượng "Sinh viên / GV IUH"
        if self.role == "student":
            email_lower = str(self.email).lower()
            if not any(email_lower.endswith(domain) for domain in IUH_EMAIL_DOMAINS):
                raise ValueError(
                    "Email sinh viên / giảng viên IUH phải có đuôi @student.iuh.edu.vn hoặc @iuh.edu.vn."
                )

            if not self.student_code:
                raise ValueError("Mã số sinh viên (MSSV) là bắt buộc đối với Sinh viên IUH.")
            if not STUDENT_CODE_REGEX.match(self.student_code):
                raise ValueError("Mã số sinh viên (MSSV) phải chứa đúng 8 chữ số.")

            if not self.department or len(self.department.strip()) < 2:
                raise ValueError("Vui lòng nhập Khoa / Viện của bạn.")

            if not self.major or len(self.major.strip()) < 2:
                raise ValueError("Vui lòng nhập Ngành học của bạn.")

        # 3. Quy tắc đối tượng "Người dùng công cộng"
        elif self.role == "public":
            self.student_code = None
            self.department = None
            self.major = None

        return self


class LoginRequest(BaseModel):
    account: str = Field(..., description="Email hoặc Mã số sinh viên (MSSV)")
    password: str = Field(..., description="Mật khẩu đăng nhập")
    remember_me: Optional[bool] = Field(False, description="Ghi nhớ đăng nhập")

    @model_validator(mode="before")
    @classmethod
    def normalize_login_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            acc = data.get("account") or data.get("identifier") or data.get("email") or data.get("studentCode") or data.get("student_code") or ""
            data["account"] = str(acc).strip()
            data["password"] = str(data.get("password") or "")
            if "rememberMe" in data and "remember_me" not in data:
                data["remember_me"] = bool(data.get("rememberMe"))
        return data

    @field_validator("account")
    @classmethod
    def validate_account(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Vui lòng nhập Email hoặc Mã số sinh viên.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Vui lòng nhập mật khẩu.")
        return v


class VerifyStudentRequest(BaseModel):
    student_id: str = Field(..., description="Mã số sinh viên")
    portal_password: str = Field(..., description="Mật khẩu cổng thông tin")

    @model_validator(mode="before")
    @classmethod
    def normalize_verify_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            sid = data.get("student_id") or data.get("studentCode") or data.get("studentId") or ""
            pwd = data.get("portal_password") or data.get("portalPassword") or data.get("password") or ""
            data["student_id"] = str(sid).strip()
            data["portal_password"] = str(pwd)
        return data


class UpdateSettingsRequest(BaseModel):
    theme: Optional[str] = Field(None, description="Giao diện (light/dark/system)")
    language: Optional[str] = Field(None, description="Ngôn ngữ (vi/en)")
    notifications_enabled: Optional[bool] = Field(None, description="Bật thông báo")



class UserResponse(BaseModel):
    id: str
    email: str
    fullName: str
    full_name: Optional[str] = None
    studentCode: Optional[str] = None
    student_code: Optional[str] = None
    studentId: Optional[str] = None
    department: Optional[str] = None
    major: Optional[str] = None
    role: str = "student"
    avatarUrl: Optional[str] = None
    avatar_url: Optional[str] = None


class AuthResponseData(BaseModel):
    token: str
    user: Dict[str, Any]
    message: Optional[str] = None


class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
