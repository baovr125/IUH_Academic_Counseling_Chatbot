import os
import uuid
import json
import asyncio
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status, Request, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
from app.schemas.documents import (
    DocumentStatusResponse,
    DocumentUploadResponse,
    ApiResult
)
from app.tasks.pdf_worker import dispatch_pdf_translation_job, redis_client
from app.utils.logger import logger
from app.utils.minio_client import upload_file_stream, object_exists, get_object_stream, get_presigned_url
from app.utils.security import get_current_user_id, get_optional_user_id

router = APIRouter(tags=["Document Translation & RAG Service"])

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    source_lang: Optional[str] = Form("en"),
    target_lang: Optional[str] = Form("vi"),
    is_scanned: Optional[bool] = Form(False),
    user_id: str = Depends(get_current_user_id)
):
    """
    1. Tiếp nhận file PDF từ người dùng
    2. Stream trực tiếp vào MinIO (không tốn đĩa cứng máy chủ)
    3. Gửi tác vụ dịch ngầm qua background worker
    4. Trả về HTTP 202 Accepted kèm doc_id
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Định dạng file không được hỗ trợ. Hệ thống chuyên biệt dịch tài liệu học thuật định dạng PDF (.pdf)."
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
    object_name = f"source/{doc_id}.pdf"
    
    try:
        # Stream directly from memory to MinIO
        upload_file_stream(
            object_name=object_name,
            data_stream=file.file,
            length=file_size,
            content_type=file.content_type or "application/pdf"
        )
    except Exception as e:
        logger.exception(f"Lỗi khi lưu stream file upload ({file.filename}) lên MinIO: {e}")
        raise HTTPException(status_code=500, detail="Không thể lưu trữ file tài liệu.")

    # Dispatch background worker
    await dispatch_pdf_translation_job(
        doc_id=doc_id,
        file_path=object_name,
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
            file_type="pdf",
            status="processing",
            message="File PDF đã được tải lên thành công và đang được xử lý dịch thuật ngầm."
        ).model_dump()
    )

@router.get("/{doc_id}/status")
async def get_document_status(
    doc_id: str,
    user_id: str = Depends(get_optional_user_id)
):
    """
    API Lấy trạng thái & kết quả dịch thuật của doc_id từ Redis cache.
    Hỗ trợ khôi phục dữ liệu khi người dùng reload trang (F5).
    """
    latest_state = redis_client.get(f"job_latest_{doc_id}")
    if not latest_state:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy thông tin tài liệu hoặc phiên dịch đã hết hạn."
        )
    return ApiResult(
        ok=True,
        data=json.loads(latest_state)
    )

@router.get("/{doc_id}/stream")
async def stream_document_status(
    request: Request,
    doc_id: str,
    user_id: str = Depends(get_optional_user_id)
):
    """
    API Server-Sent Events (SSE) để stream tiến độ xử lý dịch & trích xuất glossary.
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

@router.get("/{doc_id}/download")
async def download_translated_document(
    doc_id: str,
    user_id: str = Depends(get_optional_user_id)
):
    """
    API Tải về/Xem file kết quả tài liệu đã dịch (.pdf, .docx, .pptx).
    Stream trực tiếp từ MinIO qua Gateway về Client (In-memory Chunk Streaming),
    giải quyết triệt để lỗi DNS hostname nội bộ của Docker (minio:9000).
    """
    found_object = None
    found_ext = None
    for ext in [".pdf", ".docx", ".pptx"]:
        object_name = f"translated/{doc_id}{ext}"
        if object_exists(object_name):
            found_object = object_name
            found_ext = ext
            break
            
    if not found_object:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy file kết quả dịch thuật. Có thể đang trong quá trình xử lý hoặc đã hết hạn."
        )

    media_type = "application/pdf"
    if found_ext == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif found_ext == ".pptx":
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    minio_resp = get_object_stream(found_object)
    if not minio_resp:
        raise HTTPException(status_code=500, detail="Không thể đọc luồng dữ liệu file từ MinIO.")

    def iterfile():
        try:
            for chunk in minio_resp.stream(32 * 1024):
                yield chunk
        finally:
            minio_resp.close()
            minio_resp.release_conn()

    return StreamingResponse(
        iterfile(),
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="Translated_{doc_id[:8]}{found_ext}"',
            "Content-Type": media_type
        }
    )


