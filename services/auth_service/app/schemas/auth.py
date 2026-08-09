from pydantic import BaseModel, model_validator
from typing import Optional, Any, Dict

class RegisterRequest(BaseModel):
    email: str = ""
    password: str
    full_name: str = ""
    student_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_register_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            email = data.get("email") or data.get("identifier") or data.get("studentCode") or ""
            full_name = data.get("full_name") or data.get("fullName") or "Sinh viên IUH"
            student_id = data.get("student_id") or data.get("studentCode")
            data["email"] = email
            data["full_name"] = full_name
            if student_id:
                data["student_id"] = student_id
        return data

class LoginRequest(BaseModel):
    account: str = ""
    password: str

    @model_validator(mode="before")
    @classmethod
    def normalize_login_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            acc = data.get("account") or data.get("identifier") or data.get("email") or ""
            data["account"] = acc
        return data

class VerifyStudentRequest(BaseModel):
    student_id: str = ""
    portal_password: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_verify_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            sid = data.get("student_id") or data.get("studentCode") or data.get("studentId") or ""
            pwd = data.get("portal_password") or data.get("portalPassword") or data.get("password") or ""
            data["student_id"] = sid
            data["portal_password"] = pwd
        return data

class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
