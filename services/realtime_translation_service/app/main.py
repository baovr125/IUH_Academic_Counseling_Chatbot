import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import translation
from app.utils.logger import logger, request_id_var
from app.rabbitmq_consumer import start_rabbitmq_tts_consumer
from app.services.llm_service import preload_models
from app.services.domain_dict_service import sync_dictionary_to_redis
from app.services.minio_client import init_minio

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Real-time Translation Service...")
    init_minio()
    preload_models()
    
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
            "fasttext_model": "unknown"
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
        
        from app.services.fasttext_detector import _get_fasttext_model
        ft_ok = _get_fasttext_model() is not None
        return nllb_ok, ft_ok
        
    try:
        nllb_ok, ft_ok = await asyncio.to_thread(check_models)
        status["dependencies"]["nllb_model"] = "loaded" if nllb_ok else "missing"
        status["dependencies"]["fasttext_model"] = "loaded" if ft_ok else "missing"
    except Exception:
        status["dependencies"]["nllb_model"] = "error"
        status["dependencies"]["fasttext_model"] = "error"
    
    # Determine overall status
    if (status["dependencies"]["nllb_model"] != "loaded" or 
        status["dependencies"]["fasttext_model"] != "loaded" or
        status["dependencies"]["redis"] != "connected"):
        status["status"] = "degraded"
        response.status_code = 503
        
    return status
