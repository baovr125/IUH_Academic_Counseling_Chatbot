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

@app.get("/health", tags=["Health Check"])
@app.get("/api/v1/translate/health", tags=["Health Check"])
@app.get("/api/translate/health", tags=["Health Check"])
def health_check():
    return {"ok": True, "service": "realtime_translation_service", "status": "running"}
