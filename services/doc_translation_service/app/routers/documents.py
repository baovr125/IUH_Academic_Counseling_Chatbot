import os
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status
from fastapi.responses import FileResponse
from app.schemas.documents import (
    DocumentQueryRequest,
    DocumentQueryResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    ApiResult
)
from app.services.rag_engine import query_document_rag
from app.tasks.pdf_worker import dispatch_pdf_translation_job, get_job_status
from app.utils.logger import logger

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

    doc_id = str(uuid.uuid4())
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{doc_id}_{file.filename}")

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        logger.exception(f"Lỗi khi lưu file upload ({file.filename}): {e}")
        raise HTTPException(status_code=500, detail="Không thể lưu trữ file tạm.")

    user_id = x_user_id or "anonymous"

    # Dispatch background worker
    await dispatch_pdf_translation_job(
        doc_id=doc_id,
        file_path=file_path,
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

@router.get("/{doc_id}/status")
async def get_document_status(
    doc_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    API Polling tiến độ xử lý dịch & indexed vector RAG (0% - 100%).
    """
    status_info = get_job_status(doc_id)
    return ApiResult(
        ok=True,
        data=DocumentStatusResponse(
            doc_id=doc_id,
            status=status_info.get("status", "processing"),
            progress=status_info.get("progress", 0),
            message=status_info.get("message", "Đang xử lý..."),
            pages_processed=status_info.get("pages_processed", 0),
            total_pages=status_info.get("total_pages", 0),
            translated_file_url=status_info.get("translated_file_url"),
            translated_text=status_info.get("translated_text"),
            summary_json=status_info.get("summary_json"),
            glossary=status_info.get("glossary", []),
            model_used=status_info.get("model_used"),
            error=status_info.get("error")
        ).model_dump()
    )

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
    temp_dir = "temp_translated"
    target_file = None
    media_type = "application/octet-stream"

    for ext in [".pdf", ".docx", ".pptx"]:
        possible_path = os.path.join(temp_dir, f"translated_{doc_id}{ext}")
        if os.path.exists(possible_path):
            target_file = possible_path
            if ext == ".pdf":
                media_type = "application/pdf"
            elif ext == ".docx":
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif ext == ".pptx":
                media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            break

    if not target_file:
        raise HTTPException(status_code=404, detail="Không tìm thấy file kết quả dịch thuật. Có thể đang trong quá trình xử lý.")

    ext = os.path.splitext(target_file)[1]
    return FileResponse(
        path=target_file,
        media_type=media_type,
        content_disposition_type="inline",
        filename=f"Translated_Document_{doc_id[:8]}{ext}"
    )
