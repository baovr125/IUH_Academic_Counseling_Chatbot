import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import translation
from app.utils.logger import logger, request_id_var

app = FastAPI(
    title="IUH Real-time Translation Service",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
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

@app.get("/health", tags=["Health Check"])
@app.get("/api/v1/translate/health", tags=["Health Check"])
@app.get("/api/translate/health", tags=["Health Check"])
def health_check():
    return {"ok": True, "service": "realtime_translation_service", "status": "running"}
