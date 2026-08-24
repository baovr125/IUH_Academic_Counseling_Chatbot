import uuid
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.routers import chat, sessions
from app.utils.limiter import limiter
from app.utils.logger import logger, request_id_var
from app.services.rag_service import preload_models

app = FastAPI(
    title="IUH Academic Chatbot Service",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(asyncio.to_thread(preload_models))

# Include chat messages endpoints
app.include_router(chat.router, prefix="/api/v1/chat/messages")
app.include_router(chat.router, prefix="/api/chat/messages")

# Include chat sessions endpoints
app.include_router(sessions.router, prefix="/api/v1/chat/sessions")
app.include_router(sessions.router, prefix="/api/chat/sessions")

@app.get("/health", tags=["Health Check"])
@app.get("/api/v1/chat/health", tags=["Health Check"])
@app.get("/api/chat/health", tags=["Health Check"])
def health_check():
    return {"ok": True, "service": "academic_chatbot_service", "status": "running"}
