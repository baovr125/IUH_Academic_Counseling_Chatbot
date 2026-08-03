import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import Base, engine
from routes.auth import router as auth_router
from routes.settings import router as settings_router

try:
    from app.routers.chat import router as chat_router
except ImportError:
    chat_router = None

# Khởi tạo bảng CSDL nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IUH Portal AI - Backend API",
    description="Hệ thống Authentication, Settings & AI Chatbot cho IUH Portal AI",
    version="1.0.0",
)

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
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Chuẩn hóa dữ liệu trả về khi có HTTPException theo API Contract-First:
    { "ok": false, "error": { "message": "...", "code": "..." } }
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": {
                "message": str(exc.detail),
                "code": str(exc.status_code),
            },
        },
    )


# Mount routes
app.include_router(auth_router)
app.include_router(settings_router)
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
