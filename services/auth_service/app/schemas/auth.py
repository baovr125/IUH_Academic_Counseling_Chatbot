import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Họ tên: chữ cái (có dấu tiếng Việt), khoảng trắng, dấu chấm, gạch nối, nháy đơn.
NAME_REGEX = re.compile(
    r"^[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂưăạảấầẩẫậắằẳẵặẹẻẽềềểỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴÝỶỸửữựỳỵýỷỹ\s\.\'\-]+$"
)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$")
STUDENT_CODE_REGEX = re.compile(r"^\d{8}$")
PHONE_REGEX = re.compile(r"^\+?[0-9][0-9 .\-]{7,18}$")
PASSWORD_LETTER_REGEX = re.compile(r"[A-Za-z]")
PASSWORD_DIGIT_REGEX = re.compile(r"\d")

STUDENT_EMAIL_DOMAIN = "student.iuh.edu.vn"
IUH_EMAIL_DOMAINS = ("@student.iuh.edu.vn", "@iuh.edu.vn")
PASSWORD_MIN_LENGTH = 8
# bcrypt chỉ dùng 72 byte đầu; từ chối mật khẩu dài hơn thay vì cắt âm thầm.
PASSWORD_MAX_BYTES = 72

COMMON_PASSWORDS = frozenset({
    "12345678", "123456789", "1234567890", "password", "password1", "password123",
    "qwerty123", "qwertyuiop", "abc12345", "abcd1234", "11111111", "iloveyou1",
    "admin123", "admin1234", "welcome1", "welcome123", "letmein123", "iuh12345",
    "matkhau123", "matkhau1", "123456abc", "1q2w3e4r", "1qaz2wsx", "pass1234",
})

AVATAR_MAX_LENGTH = 200_000  # ký tự; ảnh data-URL đã thu nhỏ ở client thường < 50 KB
AVATAR_DATA_URL_REGEX = re.compile(r"^data:image/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$")
AVATAR_HTTPS_REGEX = re.compile(r"^https://[^\s<>\"']{3,2000}$")


class FieldValueError(ValueError):
    """ValueError gắn với một trường cụ thể để handler lỗi trả về đúng ``field`` cho frontend."""

    def __init__(self, message: str, field: str):
        super().__init__(message)
        self.field = field


def check_password_policy(password: str, email: Optional[str] = None) -> None:
    """Ném ValueError nếu mật khẩu vi phạm chính sách. Dùng chung cho đăng ký và đổi mật khẩu."""
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Mật khẩu phải có tối thiểu {PASSWORD_MIN_LENGTH} ký tự.")
    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValueError("Mật khẩu quá dài (tối đa 72 byte, khoảng 72 ký tự không dấu).")
    if not PASSWORD_LETTER_REGEX.search(password):
        raise ValueError("Mật khẩu phải bao gồm ít nhất một chữ cái.")
    if not PASSWORD_DIGIT_REGEX.search(password):
        raise ValueError("Mật khẩu phải bao gồm ít nhất một chữ số.")
    lowered = password.lower()
    if lowered in COMMON_PASSWORDS:
        raise ValueError("Mật khẩu quá phổ biến, vui lòng chọn mật khẩu khác.")
    if email:
        local = email.split("@", 1)[0].lower()
        if local and (lowered == local or lowered == email.lower()):
            raise ValueError("Mật khẩu không được trùng với email hoặc mã số sinh viên.")


def _clean(value: Any) -> Optional[str]:
    text = str(value).strip() if value is not None else ""
    return text or None


class RegisterRequest(BaseModel):
    full_name: str = Field(..., description="Họ và tên người dùng")
    email: str = Field(..., description="Địa chỉ email")
    password: str = Field(..., description="Mật khẩu (8-72 byte, gồm chữ và số)")
    confirm_password: Optional[str] = Field(None, description="Xác nhận mật khẩu")
    role: str = Field("student", description="'student' (Sinh viên/GV IUH) hoặc 'public' (Công cộng)")
    student_code: Optional[str] = Field(
        None, description="MSSV — KHÔNG nhận từ client, được suy ra từ email dạng <8 chữ số>@student.iuh.edu.vn"
    )
    department: Optional[str] = Field(None, description="Khoa / Viện (bắt buộc với role=student)")
    major: Optional[str] = Field(None, description="Ngành học (bắt buộc với role=student)")

    @model_validator(mode="before")
    @classmethod
    def normalize_and_alias_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)  # không sửa trực tiếp dict của request
        data["full_name"] = str(data.get("full_name") or data.get("fullName") or data.get("name") or "").strip()
        data["email"] = str(data.get("email") or data.get("identifier") or "").strip().lower()
        data["password"] = str(data.get("password") or "")
        if "confirmPassword" in data and "confirm_password" not in data:
            data["confirm_password"] = data.get("confirmPassword")

        # Vai trò do client gửi chỉ được phân biệt student/public; KHÔNG BAO GIỜ nhận admin từ đăng ký.
        raw_role = data.get("role") or data.get("userType") or data.get("user_type")
        if raw_role:
            raw_role = str(raw_role).strip().lower()
            data["role"] = "public" if raw_role in ("public", "guest", "parent", "highschool") else "student"
        else:
            data["role"] = "student"

        # MSSV không do client khai báo (tránh chiếm MSSV của người khác bằng email khác);
        # nó được suy ra từ email trong validate_audience_rules.
        data["student_code"] = None
        data["department"] = _clean(data.get("department") or data.get("faculty"))
        data["major"] = _clean(data.get("major"))
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
        if not clean or len(clean) > 254 or not EMAIL_REGEX.match(clean):
            raise ValueError("Email không đúng định dạng tiêu chuẩn.")
        return clean

    @model_validator(mode="after")
    def validate_audience_rules(self) -> "RegisterRequest":
        try:
            check_password_policy(self.password, self.email)
        except ValueError as e:
            raise FieldValueError(str(e), "password")

        if self.confirm_password is not None and self.password != self.confirm_password:
            raise FieldValueError("Mật khẩu xác nhận không khớp.", "confirm_password")

        if self.role == "student":
            if not any(self.email.endswith(domain) for domain in IUH_EMAIL_DOMAINS):
                raise FieldValueError(
                    "Email sinh viên / giảng viên IUH phải có đuôi @student.iuh.edu.vn hoặc @iuh.edu.vn.",
                    "email",
                )
            local, _, domain = self.email.partition("@")
            self.student_code = local if domain == STUDENT_EMAIL_DOMAIN and STUDENT_CODE_REGEX.match(local) else None
            if not self.department or len(self.department) < 2:
                raise FieldValueError("Vui lòng nhập Khoa / Viện của bạn.", "department")
            if not self.major or len(self.major) < 2:
                raise FieldValueError("Vui lòng nhập Ngành học của bạn.", "major")
            if len(self.department) > 150:
                raise FieldValueError("Khoa / Viện tối đa 150 ký tự.", "department")
            if len(self.major) > 150:
                raise FieldValueError("Ngành học tối đa 150 ký tự.", "major")
        else:
            self.student_code = None
            self.department = None
            self.major = None
        return self


class LoginRequest(BaseModel):
    account: str = Field(..., description="Email hoặc Mã số sinh viên (MSSV)")
    password: str = Field(..., description="Mật khẩu đăng nhập")

    @model_validator(mode="before")
    @classmethod
    def normalize_login_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        acc = (data.get("account") or data.get("identifier") or data.get("email")
               or data.get("studentCode") or data.get("student_code") or "")
        data["account"] = str(acc).strip()
        data["password"] = str(data.get("password") or "")
        return data

    @field_validator("account")
    @classmethod
    def validate_account(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Vui lòng nhập Email hoặc Mã số sinh viên.")
        if len(clean) > 254:
            raise ValueError("Email hoặc Mã số sinh viên không hợp lệ.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Vui lòng nhập mật khẩu.")
        if len(v) > 1024:
            raise ValueError("Mật khẩu không hợp lệ.")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        data["current_password"] = str(data.get("current_password") or data.get("currentPassword") or "")
        data["new_password"] = str(data.get("new_password") or data.get("newPassword") or "")
        if "confirmPassword" in data and "confirm_password" not in data:
            data["confirm_password"] = data.get("confirmPassword")
        return data

    @model_validator(mode="after")
    def validate_passwords(self) -> "ChangePasswordRequest":
        if not self.current_password:
            raise FieldValueError("Vui lòng nhập mật khẩu hiện tại.", "current_password")
        try:
            check_password_policy(self.new_password)
        except ValueError as e:
            raise FieldValueError(str(e), "new_password")
        if self.confirm_password is not None and self.new_password != self.confirm_password:
            raise FieldValueError("Mật khẩu xác nhận không khớp.", "confirm_password")
        if self.new_password == self.current_password:
            raise FieldValueError("Mật khẩu mới phải khác mật khẩu hiện tại.", "new_password")
        return self


class UpdateProfileRequest(BaseModel):
    """Chỉ các trường được phép sửa. Email, MSSV và vai trò KHÔNG sửa được qua API này."""

    model_config = ConfigDict(extra="ignore")

    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    major: Optional[str] = None
    avatar_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = {}
        for snake, camel in (("full_name", "fullName"), ("phone_number", "phoneNumber"),
                             ("department", "department"), ("major", "major"), ("avatar_url", "avatarUrl")):
            if snake in data:
                out[snake] = data[snake]
            elif camel in data:
                out[snake] = data[camel]
        return out

    @field_validator("full_name")
    @classmethod
    def v_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip()
        if not (2 <= len(clean) <= 100):
            raise FieldValueError("Họ và tên bắt buộc từ 2 đến 100 ký tự.", "full_name")
        if not NAME_REGEX.match(clean):
            raise FieldValueError("Họ và tên không được chứa ký tự đặc biệt bất hợp pháp.", "full_name")
        return clean

    @field_validator("phone_number")
    @classmethod
    def v_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip()
        if clean == "":
            return ""  # xóa số điện thoại
        if not PHONE_REGEX.match(clean):
            raise FieldValueError("Số điện thoại không hợp lệ.", "phone_number")
        return clean

    @field_validator("department", "major")
    @classmethod
    def v_text(cls, v: Optional[str], info) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip()
        if len(clean) < 2 or len(clean) > 150:
            raise FieldValueError("Giá trị bắt buộc từ 2 đến 150 ký tự.", info.field_name)
        return clean

    @field_validator("avatar_url")
    @classmethod
    def v_avatar(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip()
        if clean == "":
            return ""  # gỡ ảnh đại diện
        if len(clean) > AVATAR_MAX_LENGTH:
            raise FieldValueError("Ảnh đại diện quá lớn.", "avatar_url")
        if not (AVATAR_DATA_URL_REGEX.match(clean) or AVATAR_HTTPS_REGEX.match(clean)):
            raise FieldValueError("Ảnh đại diện phải là URL https hoặc ảnh PNG/JPEG/WEBP.", "avatar_url")
        return clean


class UpdateSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    theme: Optional[Literal["light", "dark", "system"]] = None
    language: Optional[Literal["vi", "en"]] = None
    sound_enabled: Optional[bool] = Field(None, alias="soundEnabled")
    academic_alerts: Optional[bool] = Field(None, alias="academicAlerts")


class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[dict] = None
