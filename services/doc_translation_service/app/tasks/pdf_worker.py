import os
import json
import redis
import asyncio
from typing import Dict, Any, Optional
from app.services.markdown_pdf_service import extract_pdf_to_markdown, render_markdown_to_pdf
from app.services.ollama_translator import translate_markdown_document_ollama
from app.services.docx_pptx_service import translate_docx_document, translate_pptx_document
from app.services.scanned_pdf_service import process_scanned_pdf_translation
from app.services.glossary_extractor import extract_glossary
from app.utils.logger import logger
from app.celery_app import celery_app, REDIS_URL

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def update_job_status(
    doc_id: str,
    status: str,
    progress: int,
    message: str,
    **kwargs
):
    payload = {
        "doc_id": doc_id,
        "status": status,
        "progress": progress,
        "message": message,
        **kwargs
    }
    # Publish to Redis Pub/Sub channel
    redis_client.publish(f"job_status_{doc_id}", json.dumps(payload))
    # Optionally store the latest state in Redis so we can fetch it if needed
    redis_client.set(f"job_latest_{doc_id}", json.dumps(payload), ex=3600*24) # expire in 24h

@celery_app.task(bind=True, name="app.tasks.pdf_worker.process_document_translation_job_sync")
def process_document_translation_job_sync(
    self,
    doc_id: str,
    file_path: str,
    user_id: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    is_scanned: bool = False
) -> Dict[str, Any]:
    """
    Dispatcher router xử lý dịch thuật đa định dạng, chạy bằng Celery:
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

        md_text_for_glossary = ""
        
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
            md_text_for_glossary = md_text
            
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

        update_job_status(doc_id, "processing", 95, "Đang trích xuất thuật ngữ chuyên ngành (Glossary)...", model_used=model_used)
        glossary_items = []
        if md_text_for_glossary:
            glossary_items = asyncio.run(extract_glossary(md_text_for_glossary, target_lang=target_lang))

        update_job_status(
            doc_id, "completed", 100,
            f"Đã hoàn thành dịch thuật thành công bằng {model_used}!",
            pages_processed=1,
            total_pages=1,
            translated_file_url=translated_file_url,
            translated_text=translated_text,
            summary_json={},
            glossary=glossary_items,
            model_used=model_used
        )
        logger.info(f"✅ [Job Completed] doc_id={doc_id}, saved to {translated_file_path}")
        return {"doc_id": doc_id, "status": "completed"}

    except Exception as e:
        logger.exception(f"❌ [Job Failed] Lỗi xử lý dịch thuật doc_id={doc_id}: {e}")
        update_job_status(doc_id, "failed", 0, f"Thất bại: {str(e)}", error=str(e))
        return {"doc_id": doc_id, "status": "failed", "error": str(e)}

async def dispatch_pdf_translation_job(
    doc_id: str,
    file_path: str,
    user_id: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    is_scanned: bool = False
):
    """
    Offload heavy job sang Celery background worker.
    """
    update_job_status(doc_id, "processing", 5, "Khởi tạo tác vụ dịch ngầm qua Celery...")
    process_document_translation_job_sync.delay(
        doc_id,
        file_path,
        user_id,
        source_lang,
        target_lang,
        is_scanned
    )
