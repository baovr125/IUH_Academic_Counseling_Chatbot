import asyncio
import os
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import catalog, flashcards, games, languages, vocabulary
from app.utils.errors import ApiError
from app import rabbitmq_consumer
from app.rabbitmq_consumer import connect_rabbitmq_with_retry
from app.utils.logger import logger, request_id_var
from app.utils.security import validate_security_config
from app.utils.cors import CORS_ALLOW_ORIGINS

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    validate_security_config()
    logger.info("Flashcard Service is starting up...")
    # Kết nối RabbitMQ ở nền (có thử lại) để API sẵn sàng ngay cả khi RabbitMQ khởi động chậm hơn.
    # RABBITMQ_DISABLED=1: chạy không cần broker (test, demo cục bộ); khi đó không có event TTS/doc.translated.
    if os.getenv("RABBITMQ_DISABLED") == "1":
        logger.info("RABBITMQ_DISABLED=1: bỏ qua kết nối RabbitMQ.")
        rabbitmq_task = asyncio.create_task(asyncio.sleep(0))
    else:
        rabbitmq_task = asyncio.create_task(connect_rabbitmq_with_retry())
    yield
    # Shutdown
    logger.info("Flashcard Service is shutting down...")
    if not rabbitmq_task.done():
        rabbitmq_task.cancel()
        await asyncio.wait({rabbitmq_task}, timeout=3)  # không để một lần kết nối treo chặn việc tắt service
    else:
        try:
            conn = rabbitmq_task.result()
            if conn:
                await conn.close()
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass

app = FastAPI(
    title="IUH Flashcard & Spaced Repetition Service",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=False,
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

@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    """Lỗi nghiệp vụ: {"ok": false, "error": {"code", "message", "data"?}} (frontend đọc error.message / error.code)."""
    error = {"code": exc.code, "message": exc.message}
    if exc.data is not None:
        error["data"] = exc.data
    return JSONResponse(status_code=exc.status, content={"ok": False, "error": error})

for _router in (flashcards.router, vocabulary.router, catalog.router, languages.router, games.router):
    app.include_router(_router, prefix="/api/v1/flashcards")
    app.include_router(_router, prefix="/api/flashcards")
    app.include_router(_router, prefix="/api/v1")
    app.include_router(_router, prefix="/api")

@app.get("/health", tags=["Health Check"])
@app.get("/api/v1/flashcards/health", tags=["Health Check"])
@app.get("/api/flashcards/health", tags=["Health Check"])
def health_check():
    """
    `ok` luôn true khi tiến trình sống. Các cờ bên dưới giúp phát hiện cấu hình thiếu mà không cần đọc log:
    - fsrs: False nghĩa là đang chạy bộ lập lịch DỰ PHÒNG (không phải FSRS thật).
    - llm_providers: các provider LLM đã có khóa/URL; rỗng nghĩa là tính năng sinh từ sẽ trả 503.
    - supabase / rabbitmq: đã cấu hình cơ sở dữ liệu / đã kết nối broker (event TTS, doc.translated).
    """
    from app.services import fsrs_algorithm, llm_client
    from app.services.flashcard_service import get_supabase

    return {
        "ok": True,
        "service": "flashcard_service",
        "status": "running",
        "fsrs": fsrs_algorithm.HAS_FSRS,
        "llm_providers": [p.name for p in llm_client._configured_providers()],
        "supabase": get_supabase() is not None,
        "rabbitmq": rabbitmq_consumer._exchange is not None,
    }
