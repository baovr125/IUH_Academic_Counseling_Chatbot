import re
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import config
from app.routers import auth
from app.services import auth_service as svc
from app.utils.logger import logger, request_id_var

# /docs và /openapi.json mặc định TẮT; bật bằng ENABLE_API_DOCS=true khi phát triển.
_docs = config.docs_enabled()
app = FastAPI(
    title="IUH Auth Microservice",
    description="Microservice Quản lý Xác thực, Đăng ký & Đăng nhập Hệ thống IUH Academic Chatbot",
    version="1.1.0",
    docs_url="/docs" if _docs else None,
    redoc_url=None,
    openapi_url="/openapi.json" if _docs else None,
)


@app.on_event("startup")
async def validate_configuration() -> None:
    config.validate_config()
    if not config.get_supabase_key():
        logger.warning("Chưa cấu hình khóa Supabase (SUPABASE_SERVICE_ROLE_KEY).")


# Không dùng "*": auth chỉ dùng header Authorization (không cookie) và đi qua Kong, nên chỉ cần whitelist dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._\-]{8,64}$")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    # Nhận X-Request-ID do Kong (plugin correlation-id) đặt để truy vết xuyên service; không hợp lệ thì tự sinh.
    incoming: Optional[str] = request.headers.get("x-request-id")
    req_id = incoming if incoming and _REQUEST_ID_RE.match(incoming) else str(uuid.uuid4())
    request_id_var.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    # Phản hồi chứa token/thông tin cá nhân: không cho trình duyệt hay proxy lưu cache.
    response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response


def _error(status_code: int, message: str, field: Optional[str] = None,
           details: Optional[List[Dict[str, Any]]] = None, headers: Optional[Dict[str, str]] = None) -> JSONResponse:
    error: Dict[str, Any] = {"message": message}
    if field:
        error["field"] = field
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"ok": False, "error": error}, headers=headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors: List[Dict[str, Any]] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field_parts = [str(x) for x in loc if x not in ("body",)]
        field_name = " -> ".join(field_parts) if field_parts else "body"
        msg = err.get("msg", "Dữ liệu không hợp lệ")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        # Lỗi từ model_validator không có vị trí trường; FieldValueError mang theo tên trường đúng.
        original = (err.get("ctx") or {}).get("error")
        if original is not None and getattr(original, "field", None):
            field_name = original.field
        errors.append({"field": field_name, "message": msg, "type": err.get("type")})

    first = errors[0] if errors else None
    return _error(
        status.HTTP_400_BAD_REQUEST,
        first["message"] if first else "Dữ liệu đầu vào không hợp lệ.",
        field=first["field"] if first and first["field"] != "body" else None,
        details=errors,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Mọi lỗi HTTP (kể cả 404/405 do routing) đi qua cùng một định dạng {ok:false, error:{...}}."""
    detail = exc.detail
    field = None
    if isinstance(detail, dict):
        msg = detail.get("message", "Yêu cầu không thành công.")
        field = detail.get("field")
    elif isinstance(detail, str):
        msg = {404: "Không tìm thấy tài nguyên yêu cầu.", 405: "Phương thức không được hỗ trợ."}.get(exc.status_code, detail)
    else:
        msg = "Yêu cầu không thành công."
    return _error(exc.status_code, msg, field=field, headers=getattr(exc, "headers", None))


@app.exception_handler(svc.InvalidCredentialsException)
async def invalid_credentials_handler(request: Request, exc: svc.InvalidCredentialsException):
    return _error(status.HTTP_401_UNAUTHORIZED, str(exc))


@app.exception_handler(svc.CurrentPasswordIncorrectException)
async def current_password_handler(request: Request, exc: svc.CurrentPasswordIncorrectException):
    # 400 (không phải 401) để client không hiểu nhầm là phiên đăng nhập hết hạn.
    return _error(status.HTTP_400_BAD_REQUEST, str(exc), field="current_password")


@app.exception_handler(svc.InvalidTokenException)
async def invalid_token_handler(request: Request, exc: svc.InvalidTokenException):
    return _error(status.HTTP_401_UNAUTHORIZED, str(exc), headers={"WWW-Authenticate": "Bearer"})


@app.exception_handler(svc.TooManyAttemptsException)
async def too_many_attempts_handler(request: Request, exc: svc.TooManyAttemptsException):
    minutes = max(1, (exc.retry_after + 59) // 60)
    return _error(
        status.HTTP_429_TOO_MANY_REQUESTS,
        f"Quá nhiều lần thử không thành công. Vui lòng thử lại sau {minutes} phút.",
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.exception_handler(svc.DatabaseConnectionException)
async def database_exception_handler(request: Request, exc: svc.DatabaseConnectionException):
    # Chi tiết lỗi đã được ghi log ở nơi phát sinh; client chỉ nhận thông điệp chung.
    return _error(status.HTTP_503_SERVICE_UNAVAILABLE, "Hệ thống tạm thời không khả dụng. Vui lòng thử lại sau.")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error", extra={"path": request.url.path})
    return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "Đã xảy ra lỗi máy chủ. Vui lòng thử lại sau.")


app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(auth.router, prefix="/api/auth", include_in_schema=False)


@app.get("/health", tags=["Health Check"])
@app.get("/api/v1/auth/health", tags=["Health Check"], include_in_schema=False)
@app.get("/api/auth/health", tags=["Health Check"], include_in_schema=False)
def health_check():
    return {"ok": True, "service": "auth_service", "status": "running"}
