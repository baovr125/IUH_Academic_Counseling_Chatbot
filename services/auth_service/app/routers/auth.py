import ipaddress
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.schemas.auth import (
    ApiResult,
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UpdateSettingsRequest,
)
from app.services import auth_service as svc

router = APIRouter(tags=["Authentication Service"])


# Các handler dưới đây là hàm đồng bộ (def): FastAPI chạy chúng trong threadpool, nhờ đó bcrypt và
# lời gọi Supabase đồng bộ không chặn event loop của toàn service.

def _unauthorized(message: str = "Token không hợp lệ hoặc đã hết hạn.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_client_ip(request: Request) -> str:
    """IP thật của client: chỉ tin X-Real-IP do Kong đặt khi kết nối đến từ mạng nội bộ."""
    peer = request.client.host if request.client else "unknown"
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        try:
            if ipaddress.ip_address(peer).is_private:
                return real_ip.strip()[:64]
        except ValueError:
            pass
    return peer


def require_token(authorization: Optional[str] = Header(None, alias="Authorization")) -> str:
    if not authorization:
        raise _unauthorized("Thiếu Authorization header trong yêu cầu.")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        raise _unauthorized("Authorization header phải có dạng 'Bearer <token>'.")
    return value.strip()


def get_current_user(token: str = Depends(require_token)) -> Dict[str, Any]:
    user = svc.get_user_by_token(token)
    if not user:
        raise _unauthorized()
    return user


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=ApiResult)
def register(payload: RegisterRequest):
    try:
        data = svc.register_user(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            student_code=payload.student_code,
            department=payload.department,
            major=payload.major,
        )
    except svc.DuplicateEmailException as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail={"message": str(e), "field": "email"})
    except svc.DuplicateStudentCodeException as e:
        # MSSV nay được suy ra từ email nên lỗi trùng MSSV gắn vào ô email.
        raise HTTPException(status.HTTP_409_CONFLICT, detail={"message": str(e), "field": "email"})
    return ApiResult(ok=True, data=data)


@router.post("/login", status_code=status.HTTP_200_OK, response_model=ApiResult)
def login(payload: LoginRequest, request: Request):
    data = svc.login_user(account=payload.account, password=payload.password, client_ip=get_client_ip(request))
    return ApiResult(ok=True, data=data)


@router.post("/refresh", status_code=status.HTTP_200_OK, response_model=ApiResult)
def refresh(token: str = Depends(require_token)):
    return ApiResult(ok=True, data=svc.refresh_access_token(token))


@router.post("/logout", status_code=status.HTTP_200_OK, response_model=ApiResult)
def logout(user: Dict[str, Any] = Depends(get_current_user)):
    revoked = svc.logout_user(user["id"])
    return ApiResult(ok=True, data={"revoked": revoked})


@router.get("/me", status_code=status.HTTP_200_OK, response_model=ApiResult)
def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    return ApiResult(ok=True, data=user)


@router.put("/profile", status_code=status.HTTP_200_OK, response_model=ApiResult)
def update_profile(payload: UpdateProfileRequest, user: Dict[str, Any] = Depends(get_current_user)):
    try:
        updated = svc.update_profile(user["id"], payload.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail={"message": str(e)})
    return ApiResult(ok=True, data=updated)


@router.post("/change-password", status_code=status.HTTP_200_OK, response_model=ApiResult)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user),
):
    data = svc.change_password(
        user["id"], payload.current_password, payload.new_password, client_ip=get_client_ip(request)
    )
    return ApiResult(ok=True, data=data)


@router.get("/settings", status_code=status.HTTP_200_OK, response_model=ApiResult)
def get_settings(user: Dict[str, Any] = Depends(get_current_user)):
    return ApiResult(ok=True, data=svc.get_user_settings(user["id"]))


@router.put("/settings", status_code=status.HTTP_200_OK, response_model=ApiResult)
def update_settings(payload: UpdateSettingsRequest, user: Dict[str, Any] = Depends(get_current_user)):
    changes = {
        "theme": payload.theme,
        "language": payload.language,
        "soundEnabled": payload.sound_enabled,
        "academicAlerts": payload.academic_alerts,
    }
    return ApiResult(ok=True, data=svc.update_user_settings(user["id"], changes))
