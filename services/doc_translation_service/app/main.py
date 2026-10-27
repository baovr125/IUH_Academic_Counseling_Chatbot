import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import documents
from app.utils.logger import request_id_var
from app.utils.security import validate_security_config
from app.utils.cors import CORS_ALLOW_ORIGINS

app = FastAPI(
    title="IUH Document Translation Service",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    validate_security_config()


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = str(uuid.uuid4())
    request_id_var.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response

# Chỉ mount 1 prefix chuẩn /api/v1/documents
app.include_router(documents.router, prefix="/api/v1/documents")

@app.get("/health", tags=["Health Check"])
@app.get("/api/v1/documents/health", tags=["Health Check"])
def health_check():
    return {"ok": True, "service": "doc_translation_service", "status": "running"}
