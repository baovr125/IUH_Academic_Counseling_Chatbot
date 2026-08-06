import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.utils.limiter import limiter
from app.utils.logger import get_logger, request_id_var
import uuid
import traceback

logger = get_logger("main")

from database import Base, engine
from app.routers.auth import router as auth_router
from app.routers.settings import router as settings_router
from app.routers.analytics import router as analytics_router

import asyncio
from contextlib import asynccontextmanager

try:
    from app.routers.chat import router as chat_router, preload_models
except ImportError as e:
    import traceback
    traceback.print_exc()
    chat_router = None
    preload_models = None

# Khởi tạo bảng CSDL nếu kết nối thành công (không làm sập server nếu CSDL tạm thời ngắt kết nối)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Khởi tạo bảng CSDL thành công hoặc bảng đã tồn tại.")
except Exception as err:
    logger.exception("Chưa thể khởi tạo CSDL lúc bắt đầu server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if preload_models:
        try:
            logger.info("Đang nạp trước các ML models...")
            await asyncio.to_thread(preload_models)
            logger.info("Nạp ML models thành công")
        except Exception as err:
            logger.exception("Lỗi preload ML models lúc khởi động")
    yield


app = FastAPI(
    title="IUH Portal AI - Backend API",
    description="Hệ thống Authentication, Settings & AI Chatbot cho IUH Portal AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Cấu hình CORS cho phép React frontend (Vite) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = str(uuid.uuid4())
    request_id_var.set(req_id)
    
    # Optionally attach it to request state
    request.state.request_id = req_id
    
    logger.info(f"Đang xử lý request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
    except Exception as e:
        logger.exception("Lỗi server không mong muốn (Unhandled Exception)")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": {
                    "message": "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.",
                    "code": "500_INTERNAL_SERVER_ERROR",
                    "request_id": req_id
                }
            }
        )



@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Chuẩn hóa dữ liệu trả về khi có HTTPException theo API Contract-First:
    { "ok": false, "error": { "message": "...", "code": "..." } }
    """
    logger.warning(f"HTTPException: {exc.detail} (Code: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": {
                "message": str(exc.detail),
                "code": str(exc.status_code),
                "request_id": request_id_var.get()
            },
        },
    )


from sqlalchemy.exc import OperationalError

@app.exception_handler(OperationalError)
async def db_operational_exception_handler(request: Request, exc: OperationalError):
    logger.error("Lỗi kết nối CSDL (OperationalError)", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": {
                "message": "Không thể kết nối đến cơ sở dữ liệu PostgreSQL/Supabase. Vui lòng kiểm tra mật khẩu & cấu hình DATABASE_URL trong file .env.",
                "code": "500",
                "request_id": request_id_var.get()
            },
        },
    )


# Mount routes
app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(analytics_router) 
if chat_router:
    app.include_router(chat_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "ok": True,
        "data": {
            "name": "IUH Portal AI API",
            "status": "running",
        },
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
