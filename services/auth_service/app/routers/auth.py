from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    VerifyStudentRequest,
    ApiResult,
)
from app.services.auth_service import (
    register_user,
    login_user,
    get_user_by_token,
    DuplicateEmailException,
    DuplicateStudentCodeException,
    InvalidCredentialsException,
    DatabaseConnectionException,
)
from app.utils.logger import logger

router = APIRouter(tags=["Authentication Service"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=ApiResult)
async def register(payload: RegisterRequest):
    try:
        data = register_user(
            email=str(payload.email),
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            student_code=payload.student_code,
            department=payload.department,
            major=payload.major,
        )
        return ApiResult(ok=True, data=data)
    except DuplicateEmailException as de:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(de), "field": "email"},
        )
    except DuplicateStudentCodeException as dsc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(dsc), "field": "student_code"},
        )
    except DatabaseConnectionException as dce:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": str(dce)},
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(ve)},
        )
    except RuntimeError as re:
        logger.error(f"Registration runtime error: {re}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(re)},
        )
    except Exception as e:
        logger.exception(f"Unexpected registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Đăng ký không thành công. Vui lòng thử lại sau."},
        )


@router.post("/login", status_code=status.HTTP_200_OK, response_model=ApiResult)
async def login(payload: LoginRequest):
    try:
        data = login_user(account=payload.account, password=payload.password)
        return ApiResult(ok=True, data=data)
    except InvalidCredentialsException as ice:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": str(ice)},
        )
    except DatabaseConnectionException as dce:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": str(dce)},
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(ve)},
        )
    except Exception as e:
        logger.exception(f"Unexpected login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Đăng nhập không thành công do lỗi máy chủ."},
        )


@router.post("/verify-student", status_code=status.HTTP_200_OK, response_model=ApiResult)
async def verify_student(payload: VerifyStudentRequest):
    return ApiResult(
        ok=True,
        data={
            "verified": True,
            "studentId": payload.student_id,
            "studentCode": payload.student_id,
            "fullName": f"Sinh viên IUH ({payload.student_id})",
            "faculty": "Công nghệ Thông tin",
        },
    )


@router.get("/me", status_code=status.HTTP_200_OK, response_model=ApiResult)
async def get_me(authorization: Optional[str] = Header(None, alias="Authorization")):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Thiếu Authorization header trong yêu cầu."},
        )

    token = authorization
    if token.startswith("Bearer "):
        token = token[7:].strip()

    user = get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token không hợp lệ hoặc đã hết hạn."},
        )

    return ApiResult(ok=True, data=user)

