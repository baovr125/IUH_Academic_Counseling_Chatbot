import os
import uuid
import json
import asyncio
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status, Request
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from app.schemas.documents import (
    DocumentQueryRequest,
    DocumentQueryResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    ApiResult
)
from app.services.rag_engine import query_document_rag
from app.tasks.pdf_worker import dispatch_pdf_translation_job, redis_client
from app.utils.logger import logger
from app.utils.minio_client import upload_file, download_file, get_presigned_url
import tempfile

router = APIRouter(tags=["Document Translation & RAG Service"])

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    source_lang: Optional[str] = Form("en"),
    target_lang: Optional[str] = Form("vi"),
    is_scanned: Optional[bool] = Form(False),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    1. Tiếp nhận file PDF/DOCX/PPTX từ người dùng
    2. Khởi tạo doc_id (UUIDv4)
    3. Gửi tác vụ dịch ngầm qua background worker
    4. Trả về HTTP 202 Accepted kèm doc_id
    """
    if not file.filename.endswith((".pdf", ".docx", ".doc", ".pptx", ".ppt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Định dạng file không được hỗ trợ. Vui lòng tải file PDF, Word hoặc PowerPoint."
        )

    # Validate file size (Max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Kích thước file vượt quá giới hạn 10MB."
        )

    doc_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    object_name = f"source/{doc_id}{ext}"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        file_path = temp_file.name
        try:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            # Upload to MinIO
            upload_file(object_name, file_path)
        except Exception as e:
            logger.exception(f"Lỗi khi lưu file upload ({file.filename}): {e}")
            raise HTTPException(status_code=500, detail="Không thể lưu trữ file tạm.")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    user_id = x_user_id or "anonymous"

    # Dispatch background worker
    await dispatch_pdf_translation_job(
        doc_id=doc_id,
        file_path=object_name, # Pass object_name instead of local file_path
        user_id=user_id,
        source_lang=source_lang,
        target_lang=target_lang,
        is_scanned=is_scanned
    )

    return ApiResult(
        ok=True,
        data=DocumentUploadResponse(
            doc_id=doc_id,
            filename=file.filename,
            file_type=file.filename.split(".")[-1],
            status="processing",
            message="File đã được tải lên thành công và đang được xử lý dịch thuật ngầm."
        ).model_dump()
    )

@router.get("/{doc_id}/stream")
async def stream_document_status(
    request: Request,
    doc_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    API Server-Sent Events (SSE) để stream tiến độ xử lý dịch & RAG.
    """
    async def event_generator():
        # Lấy trạng thái hiện tại (nếu có) để gửi ngay
        latest_state = redis_client.get(f"job_latest_{doc_id}")
        if latest_state:
            yield {
                "event": "update",
                "data": latest_state
            }
            
        pubsub = redis_client.pubsub()
        pubsub.subscribe(f"job_status_{doc_id}")
        
        try:
            while True:
                if await request.is_disconnected():
                    break

                # timeout=1.0 để không block hoàn toàn
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = message["data"]
                    yield {
                        "event": "update",
                        "data": data
                    }
                    
                    data_dict = json.loads(data)
                    if data_dict.get("status") in ["completed", "failed"]:
                        break
                else:
                    await asyncio.sleep(0.5)
        finally:
            pubsub.unsubscribe(f"job_status_{doc_id}")
            pubsub.close()

    return EventSourceResponse(event_generator())

@router.post("/{doc_id}/query")
async def query_document(
    doc_id: str,
    payload: DocumentQueryRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    API Hỏi đáp Document RAG cô lập theo doc_id và user_id (Hard Payload Filtering).
    """
    user_id = x_user_id or "anonymous"
    res = query_document_rag(
        doc_id=doc_id,
        user_id=user_id,
        query_text=payload.query
    )
    return ApiResult(
        ok=True,
        data=res.model_dump()
    )

@router.get("/{doc_id}/download")
async def download_translated_document(
    doc_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    API Tải về file kết quả tài liệu đã dịch (.pdf, .docx, .pptx).
    """
    # Assuming the worker uploads translated file to translated/<doc_id>.pdf/docx/pptx
    # First we check the DB to get the actual translated file name or try all extensions
    media_type = "application/octet-stream"
    found_ext = None
    
    # Simple check for extension (could be optimized by checking DB status)
    for ext in [".pdf", ".docx", ".pptx"]:
        object_name = f"translated/{doc_id}{ext}"
        try:
            # We don't have a direct "exists" method in minio python without stat_object, 
            # let's try getting presigned URL or download to temp
            url = get_presigned_url(object_name)
            if url:
                # Redirect to MinIO or download it
                pass
        except Exception:
            continue
            
    # To keep it simple and secure, download from MinIO to temp file and serve
    import tempfile
    from starlette.background import BackgroundTask
    
    target_file = None
    for ext in [".pdf", ".docx", ".pptx"]:
        object_name = f"translated/{doc_id}{ext}"
        temp_path = os.path.join(tempfile.gettempdir(), f"translated_{doc_id}{ext}")
        try:
            download_file(object_name, temp_path)
            target_file = temp_path
            found_ext = ext
            break
        except Exception:
            continue
            
    if not target_file:
        raise HTTPException(status_code=404, detail="Không tìm thấy file kết quả dịch thuật. Có thể đang trong quá trình xử lý.")

    if found_ext == ".pdf":
        media_type = "application/pdf"
    elif found_ext == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif found_ext == ".pptx":
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    return FileResponse(
        path=target_file,
        media_type=media_type,
        content_disposition_type="inline",
        filename=f"Translated_Document_{doc_id[:8]}{found_ext}",
        background=BackgroundTask(lambda: os.remove(target_file) if os.path.exists(target_file) else None)
    )
