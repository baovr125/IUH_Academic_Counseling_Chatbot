import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import flashcards
from app.rabbitmq_consumer import start_rabbitmq_consumer
from app.utils.logger import logger, request_id_var

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Flashcard Service is starting up...")
    rabbitmq_conn = await start_rabbitmq_consumer()
    yield
    # Shutdown
    logger.info("Flashcard Service is shutting down...")
    if rabbitmq_conn:
        await rabbitmq_conn.close()

app = FastAPI(
    title="IUH Flashcard & Spaced Repetition Service",
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

app.include_router(flashcards.router, prefix="/api/v1/flashcards")
app.include_router(flashcards.router, prefix="/api/flashcards")
app.include_router(flashcards.router, prefix="/api/v1")
app.include_router(flashcards.router, prefix="/api")

@app.get("/health", tags=["Health Check"])
@app.get("/api/v1/flashcards/health", tags=["Health Check"])
@app.get("/api/flashcards/health", tags=["Health Check"])
def health_check():
    return {"ok": True, "service": "flashcard_service", "status": "running"}
