import os
import asyncio
from typing import Dict, Any, Optional
from app.services.markdown_pdf_service import extract_pdf_to_markdown, render_markdown_to_pdf
from app.services.ollama_translator import translate_markdown_document_ollama
from app.services.docx_pptx_service import translate_docx_document, translate_pptx_document
from app.services.scanned_pdf_service import process_scanned_pdf_translation
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

def process_document_translation_job_sync(
    doc_id: str,
    file_path: str,
    user_id: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    is_scanned: bool = False
) -> Dict[str, Any]:
    """
    Dispatcher router xử lý dịch thuật đa định dạng:
    1. .pdf -> Academic Paper Translation (PyMuPDF4LLM -> Markdown Batching -> Ollama -> PDF)
    2. .pdf (Scan) -> PyMuPDF -> PaddleOCR -> Ollama -> DOCX
    3. .docx -> Word In-place Translation
    4. .pptx -> PowerPoint In-place Translation
    """
    logger.info(f"🚀 [Job Started] doc_id={doc_id}, file={file_path}, user={user_id}")
    update_job_status(doc_id, "processing", 10, "Đang phân loại định dạng file và khởi tạo pipeline...")

    ext = os.path.splitext(file_path)[1].lower()
    temp_out_dir = "temp_translated"
    os.makedirs(temp_out_dir, exist_ok=True)

    try:
        translated_file_path = ""
        translated_text = ""
        model_used = "Gemini 2.5 Flash"

        def status_cb(progress: int, message: str, model_name: str = ""):
            nonlocal model_used
            if model_name:
                model_used = model_name
            update_job_status(doc_id, "processing", progress, message, model_used=model_used)

        # Giai đoạn 2.2 Routing
        if ext == ".docx":
            update_job_status(doc_id, "processing", 30, "Đang dịch file Word (.docx)...", model_used=model_used)
            translated_file_path = os.path.join(temp_out_dir, f"translated_{doc_id}.docx")
            translate_docx_document(
                input_path=file_path,
                output_path=translated_file_path,
                source_lang=source_lang,
                target_lang=target_lang
            )

        elif ext in [".pptx", ".ppt"]:
            update_job_status(doc_id, "processing", 30, "Đang dịch file PowerPoint (.pptx)...", model_used=model_used)
            translated_file_path = os.path.join(temp_out_dir, f"translated_{doc_id}.pptx")
            translate_pptx_document(
                input_path=file_path,
                output_path=translated_file_path,
                source_lang=source_lang,
                target_lang=target_lang
            )

        elif ext == ".pdf" and is_scanned:
            update_job_status(doc_id, "processing", 30, "Đang OCR & dịch file PDF Scan...", model_used=model_used)
            translated_file_path = os.path.join(temp_out_dir, f"translated_{doc_id}.docx")
            process_scanned_pdf_translation(
                pdf_path=file_path,
                output_docx_path=translated_file_path,
                source_lang=source_lang,
                target_lang=target_lang
            )

        else: # Default: Academic PDF Paper
            update_job_status(doc_id, "processing", 20, "Đang bóc tách PDF bài báo khoa học thành Markdown...")
            md_text, image_dir = extract_pdf_to_markdown(file_path, doc_id)
            
            translated_text, model_used = translate_markdown_document_ollama(
                md_text=md_text,
                source_lang=source_lang,
                target_lang=target_lang,
                status_callback=status_cb
            )

            update_job_status(doc_id, "processing", 85, f"Đang render lại bản dịch ({model_used}) thành PDF...", model_used=model_used)
            translated_file_path = os.path.join(temp_out_dir, f"translated_{doc_id}.pdf")
            render_markdown_to_pdf(translated_text, translated_file_path)

        translated_file_url = f"/api/v1/documents/{doc_id}/download"

        update_job_status(
            doc_id, "completed", 100,
            f"Đã hoàn thành dịch thuật thành công bằng {model_used}!",
            pages_processed=1,
            total_pages=1,
            translated_file_url=translated_file_url,
            translated_text=translated_text,
            summary_json={},
            glossary=[],
            model_used=model_used
        )
        logger.info(f"✅ [Job Completed] doc_id={doc_id}, saved to {translated_file_path}")
        return JOB_STATUS_STORE[doc_id]

    except Exception as e:
        logger.exception(f"❌ [Job Failed] Lỗi xử lý dịch thuật doc_id={doc_id}: {e}")
        update_job_status(doc_id, "failed", 0, f"Thất bại: {str(e)}", error=str(e))
        return JOB_STATUS_STORE[doc_id]

async def dispatch_pdf_translation_job(
    doc_id: str,
    file_path: str,
    user_id: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    is_scanned: bool = False
):
    """
    Offload heavy job sang background thread để không block event loop.
    """
    update_job_status(doc_id, "processing", 5, "Khởi tạo tác vụ dịch ngầm...")
    asyncio.create_task(
        asyncio.to_thread(
            process_document_translation_job_sync,
            doc_id,
            file_path,
            user_id,
            source_lang,
            target_lang,
            is_scanned
        )
    )
