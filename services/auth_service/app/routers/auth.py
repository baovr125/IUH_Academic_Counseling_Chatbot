from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional
from app.schemas.auth import RegisterRequest, LoginRequest, VerifyStudentRequest, ApiResult
from app.services.auth_service import register_user, login_user
from app.utils.logger import logger

router = APIRouter(tags=["Authentication Service"])

@router.post("/register")
async def register(payload: RegisterRequest):
    try:
        data = register_user(payload.email, payload.password, payload.full_name, payload.student_id)
        return ApiResult(ok=True, data=data)
    except Exception as e:
        logger.exception(f"Registration error: {e}")
        return ApiResult(ok=False, error={"message": "Đăng ký không thành công"})

@router.post("/login")
async def login(payload: LoginRequest):
    data = login_user(payload.account, payload.password)
    if not data:
        return ApiResult(ok=False, error={"message": "Tài khoản hoặc mật khẩu không chính xác"})
    return ApiResult(ok=True, data=data)

@router.post("/verify-student")
async def verify_student(payload: VerifyStudentRequest):
    return ApiResult(ok=True, data={
        "verified": True,
        "studentId": payload.student_id,
        "fullName": f"Sinh viên IUH ({payload.student_id})",
        "faculty": "Công nghệ Thông tin"
    })

@router.get("/me")
async def get_me(authorization: Optional[str] = Header(None)):
    if not authorization:
        return ApiResult(ok=False, error={"message": "Unauthorized"})
    return ApiResult(ok=True, data={"id": "user-demo", "email": "student@iuh.edu.vn", "fullName": "Sinh viên IUH", "role": "student"})
