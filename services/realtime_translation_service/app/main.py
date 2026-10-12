import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.services.language_detection import LanguageResolutionError
from app.routers import translation
from app.utils.logger import logger, request_id_var
from app.utils.security import validate_security_config
from app.rabbitmq_consumer import start_rabbitmq_tts_consumer
from app.services.llm_service import preload_models
from app.services.domain_dict_service import sync_dictionary_to_redis
from app.services.minio_client import init_minio

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_security_config()
    if os.getenv("TESTING") == "1":
        yield
        return
    logger.info("Starting up Real-time Translation Service...")
    init_minio()
    nllb_ready = preload_models()

    # Nạp fastText + Lingua và chạy warm-up để request đầu tiên không phải trả giá nạp model.
    from app.services.language_detection import warm_up as warm_up_language_detection
    detection_ready = await asyncio.to_thread(warm_up_language_detection)
    logger.info(
        "Model startup status: nllb=%s fasttext=%s lingua=%s",
        "loaded" if nllb_ready else "unavailable",
        "loaded" if detection_ready["fasttext"] else "unavailable (Lingua fallback remains available)",
        "loaded" if detection_ready["lingua"] else "unavailable",
    )
    
    # Preload NLP models for Word Analysis
    from app.services.word_analysis_service import preload_nlp_models
    preload_nlp_models()
    
    sync_dictionary_to_redis()
    rabbitmq_conn = await start_rabbitmq_tts_consumer()
    yield
    logger.info("Shutting down Real-time Translation Service...")
    if rabbitmq_conn:
        await rabbitmq_conn.close()

app = FastAPI(
    title="IUH Real-time Translation Service",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost,http://127.0.0.1,http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(LanguageResolutionError)
async def language_resolution_error_handler(request: Request, exc: LanguageResolutionError):
    """Ngôn ngữ nguồn chưa xác định được → không dịch; trả mã lỗi có cấu trúc để UI cho người dùng chọn."""
    return JSONResponse(status_code=exc.resolution.http_status, content=exc.to_payload())

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = str(uuid.uuid4())
    request_id_var.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response

app.include_router(translation.router, prefix="/api/v1/translate")
app.include_router(translation.router, prefix="/api/translate")

from app.routers import admin_dictionary
app.include_router(admin_dictionary.router, prefix="/api/v1")
app.include_router(admin_dictionary.router, prefix="/api")

from fastapi import Response

@app.get("/health/live", tags=["Health Check"])
def liveness_check():
    """Liveness probe: Trả về 200 nếu process đang chạy."""
    return {"status": "alive"}

@app.get("/health/ready", tags=["Health Check"])
@app.get("/health", tags=["Health Check"])
@app.get("/api/v1/translate/health", tags=["Health Check"])
@app.get("/api/translate/health", tags=["Health Check"])
async def readiness_check(response: Response):
    """Readiness probe: Kiểm tra các dependency thiết yếu."""
    import asyncio
    import os
    
    status = {
        "status": "ready",
        "service": "realtime_translation_service",
        "dependencies": {
            "redis": "unknown",
            "supabase": "unknown",
            "nllb_model": "unknown",
            "fasttext_model": "unknown",
            "lingua_model": "unknown"
        },
        "providers": {
            "gemini": "configured" if os.environ.get("GEMINI_API_KEY") else "missing",
            "groq": "configured" if os.environ.get("GROQ_API_KEY") else "missing"
        }
    }
    
    # Check Redis
    from app.services.cache_service import get_redis
    def check_redis():
        r = get_redis()
        return r.ping() if r else False
        
    try:
        redis_ok = await asyncio.to_thread(check_redis)
        status["dependencies"]["redis"] = "connected" if redis_ok else "disconnected"
    except Exception:
        status["dependencies"]["redis"] = "error"
        
    # Check Supabase
    from app.services.supabase_client import get_supabase
    def check_supabase():
        sb = get_supabase()
        if sb:
            sb.table("domain_dictionaries").select("count", count="exact").limit(1).execute()
            return True
        return False
        
    try:
        sb_ok = await asyncio.to_thread(check_supabase)
        status["dependencies"]["supabase"] = "connected" if sb_ok else "disconnected"
    except Exception:
        status["dependencies"]["supabase"] = "error"
        
    # Check Models
    from app.services.llm_service import get_nllb_translator
    def check_models():
        translator, tokenizer = get_nllb_translator()
        nllb_ok = translator is not None and tokenizer is not None
        
        from app.services.language_detection import engines_ready
        engines = engines_ready()
        return nllb_ok, engines["fasttext"], engines["lingua"]

    try:
        nllb_ok, ft_ok, lingua_ok = await asyncio.to_thread(check_models)
        status["dependencies"]["nllb_model"] = "loaded" if nllb_ok else "missing"
        status["dependencies"]["fasttext_model"] = "loaded" if ft_ok else "missing"
        status["dependencies"]["lingua_model"] = "loaded" if lingua_ok else "missing"
    except Exception:
        status["dependencies"]["nllb_model"] = "error"
        status["dependencies"]["fasttext_model"] = "error"
        status["dependencies"]["lingua_model"] = "error"
    
    provider_ready = any(
        status["providers"][name] == "configured"
        for name in ("gemini", "groq")
    )
    translation_ready = (
        status["dependencies"]["nllb_model"] == "loaded"
        or provider_ready
    )

    if not translation_ready:
        status["status"] = "unavailable"
        response.status_code = 503
    elif (
        status["dependencies"]["nllb_model"] != "loaded"
        or status["dependencies"]["fasttext_model"] != "loaded"
        or status["dependencies"]["lingua_model"] != "loaded"
    ):
        status["status"] = "degraded"
        
    return status
