import os
import asyncio
from typing import Dict, Any, Optional
# Bỏ qua import pdf_parser và vector_store để tránh crash thư viện transformers
# from app.services.pdf_parser import parse_pdf_document, hierarchical_chunk_pages
from app.services.glossary_service import scan_document_for_glossary
from app.services.translator import translate_chunk_with_gemini, generate_document_summary_and_glossary
# from app.services.vector_store import upsert_doc_vectors
from app.utils.logger import logger

# Store in-memory status dictionary for fast polling response
JOB_STATUS_STORE: Dict[str, Dict[str, Any]] = {}

def get_job_status(doc_id: str) -> Dict[str, Any]:
    if doc_id in JOB_STATUS_STORE:
        return JOB_STATUS_STORE[doc_id]
    return {
        "doc_id": doc_id,
        "status": "not_found",
        "progress": 0,
        "message": "Tài liệu chưa được xử lý.",
        "pages_processed": 0,
        "total_pages": 0,
        "translated_file_url": None,
        "translated_text": None,
        "summary_json": {},
        "glossary": []
    }

def update_job_status(
    doc_id: str,
    status: str,
    progress: int,
    message: str,
    **kwargs
):
    current = JOB_STATUS_STORE.get(doc_id, {"doc_id": doc_id})
    current.update({
        "status": status,
        "progress": progress,
        "message": message,
        **kwargs
    })
    JOB_STATUS_STORE[doc_id] = current

def process_pdf_translation_job_sync(
    doc_id: str,
    file_path: str,
    user_id: str,
    source_lang: str = "en",
    target_lang: str = "vi"
) -> Dict[str, Any]:
    """
    Tiến trình xử lý dịch file PDF giữ nguyên cấu trúc sử dụng luồng: PDF -> Markdown -> Translate -> PDF.
    Phần Vector/RAG tạm thời được bỏ qua theo yêu cầu.
    """
    from app.services.markdown_pdf_service import extract_pdf_to_markdown, render_markdown_to_pdf
    from app.services.translator import translate_markdown_document

    logger.info(f"🚀 [Job Started] doc_id={doc_id}, file={file_path}, user={user_id}")
    update_job_status(doc_id, "processing", 10, "Đang đọc và phân tích cấu trúc file PDF...")

    try:
        # Step 1: Parse PDF to Markdown
        update_job_status(doc_id, "processing", 20, "Đang bóc tách PDF thành Markdown và trích xuất hình ảnh...")
        md_text, image_dir = extract_pdf_to_markdown(file_path, doc_id)
        
        # Step 2: Translate Markdown Document
        update_job_status(doc_id, "processing", 50, "Đang dịch toàn văn tài liệu giữ nguyên cấu trúc...")
        translated_md = translate_markdown_document(
            md_text=md_text,
            source_lang=source_lang,
            target_lang=target_lang
        )

        # Step 3: Render translated Markdown to PDF
        update_job_status(doc_id, "processing", 80, "Đang render lại bản dịch thành file PDF...")
        translated_file_dir = "temp_translated"
        os.makedirs(translated_file_dir, exist_ok=True)
        translated_file_path = os.path.join(translated_file_dir, f"translated_{doc_id}.pdf")
        
        render_markdown_to_pdf(translated_md, translated_file_path)

        translated_file_url = f"/api/v1/documents/{doc_id}/download"

        update_job_status(
            doc_id, "completed", 100,
            "Đã hoàn thành dịch thuật và tạo file PDF thành công!",
            pages_processed=1, # Bypass page counting for now
            total_pages=1,
            translated_file_url=translated_file_url,
            translated_text=translated_md,
            summary_json={},
            glossary=[]
        )
        logger.info(f"✅ [Job Completed] doc_id={doc_id}, saved to {translated_file_path}")
        return JOB_STATUS_STORE[doc_id]

    except Exception as e:
        logger.exception(f"❌ [Job Failed] Lỗi xử lý PDF translation cho doc_id={doc_id}: {e}")
        update_job_status(doc_id, "failed", 0, f"Thất bại: {str(e)}", error=str(e))
        return JOB_STATUS_STORE[doc_id]

async def dispatch_pdf_translation_job(
    doc_id: str,
    file_path: str,
    user_id: str,
    source_lang: str = "en",
    target_lang: str = "vi"
):
    """
    Offload CPU heavy job sang background thread qua asyncio.to_thread để không gây block FastAPI event loop.
    """
    update_job_status(doc_id, "processing", 5, "Khởi tạo tác vụ dịch ngầm...")
    asyncio.create_task(
        asyncio.to_thread(
            process_pdf_translation_job_sync,
            doc_id,
            file_path,
            user_id,
            source_lang,
            target_lang
        )
    )
