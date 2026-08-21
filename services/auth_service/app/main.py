import uuid
from typing import Any, Dict, List
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from app.utils.logger import logger, request_id_var

app = FastAPI(
    title="IUH Auth Microservice",
    description="Microservice Quản lý Xác thực, Đăng ký & Đăng nhập Hệ thống IUH Academic Chatbot",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = str(uuid.uuid4())
    request_id_var.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors: List[Dict[str, Any]] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field_parts = [str(x) for x in loc if x not in ("body",)]
        field_name = " -> ".join(field_parts) if field_parts else "body"

        msg = err.get("msg", "Dữ liệu không hợp lệ")
        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "")

        errors.append({
            "field": field_name,
            "message": msg,
            "type": err.get("type"),
        })

    first_message = errors[0]["message"] if errors else "Dữ liệu đầu vào không hợp lệ."

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "ok": False,
            "error": {
                "message": first_message,
                "details": errors,
            },
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        msg = detail.get("message", "Yêu cầu không thành công.")
        extra_fields = {k: v for k, v in detail.items() if k != "message"}
    elif isinstance(detail, str):
        msg = detail
        extra_fields = {}
    else:
        msg = str(detail)
        extra_fields = {}

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": {
                "message": msg,
                **extra_fields,
            },
        },
    )


app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(auth.router, prefix="/api/auth")


@app.get("/health", tags=["Health Check"])
@app.get("/api/v1/auth/health", tags=["Health Check"])
@app.get("/api/auth/health", tags=["Health Check"])
def health_check():
    return {"ok": True, "service": "auth_service", "status": "running"}

