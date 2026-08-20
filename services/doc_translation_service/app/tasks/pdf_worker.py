import os
import json
import redis
import asyncio
import tempfile
from typing import Dict, Any, Optional
from app.utils.logger import logger
from app.celery_app import celery_app, REDIS_URL
from app.utils.minio_client import download_file, upload_file
from app.utils.rabbitmq_publisher import publish_doc_translated_event

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
    update_job_status(doc_id, "processing", 10, "Đang khởi tạo pipeline dịch thuật PDF học thuật...")

    object_name = file_path
    local_input_file = os.path.join(tempfile.gettempdir(), f"input_{doc_id}.pdf")
    try:
        download_file(object_name, local_input_file)
    except Exception as e:
        logger.exception(f"Lỗi khi tải file từ MinIO: {e}")
        update_job_status(doc_id, "failed", 0, f"Thất bại tải file: {str(e)}", error=str(e))
        return {"doc_id": doc_id, "status": "failed", "error": str(e)}

    try:
        from app.services.markdown_pdf_service import extract_pdf_to_markdown, render_markdown_to_pdf
        from app.services.ollama_translator import translate_markdown_document_ollama
        from app.services.glossary_extractor import extract_glossary

        translated_local_path = ""
        translated_text = ""
        model_used = "Gemini 2.5 Flash"

        def status_cb(progress: int, message: str, model_name: str = ""):
            nonlocal model_used
            if model_name:
                model_used = model_name
            update_job_status(doc_id, "processing", progress, message, model_used=model_used)

        update_job_status(doc_id, "processing", 20, "Đang bóc tách PDF bài báo khoa học thành cấu trúc Markdown...")
        md_text, image_dir = extract_pdf_to_markdown(local_input_file, doc_id)
        md_text_for_glossary = md_text
        
        translated_text, model_used = translate_markdown_document_ollama(
            md_text=md_text,
            source_lang=source_lang,
            target_lang=target_lang,
            status_callback=status_cb
        )

        update_job_status(doc_id, "processing", 85, f"Đang render lại bản dịch ({model_used}) thành PDF chất lượng cao...", model_used=model_used)
        translated_local_path = os.path.join(tempfile.gettempdir(), f"translated_{doc_id}.pdf")
        out_ext = ".pdf"
        render_markdown_to_pdf(translated_text, translated_local_path)

        # Upload translated file to MinIO
        translated_object_name = f"translated/{doc_id}{out_ext}"
        upload_file(translated_object_name, translated_local_path)
        
        translated_file_url = f"/api/v1/documents/{doc_id}/download"

        # 1. Thông báo PDF đã sẵn sàng (90%), đang trích xuất thuật ngữ
        update_job_status(
            doc_id, "processing", 90,
            f"Đã render xong PDF! Đang trích xuất thuật ngữ chuyên ngành (Glossary)...",
            pages_processed=1,
            total_pages=1,
            translated_file_url=translated_file_url,
            translated_text=translated_text,
            summary_json={},
            glossary=[],
            model_used=model_used
        )
        logger.info(f"✅ [Document Rendered] doc_id={doc_id}, PDF ready. Extracting glossary...")

        # 2. Xử lý trích xuất Glossary
        glossary_items = []
        if md_text_for_glossary:
            try:
                glossary_items = asyncio.run(extract_glossary(md_text_for_glossary, target_lang=target_lang, source_lang=source_lang))
                if glossary_items:
                    # Publish event to RabbitMQ for flashcard_service
                    publish_doc_translated_event(
                        doc_id=doc_id,
                        user_id=user_id,
                        file_name=object_name.replace('source/', ''),
                        glossary=glossary_items,
                        source_lang=source_lang
                    )
            except Exception as e:
                logger.warning(f"Lỗi khi trích xuất glossary: {e}")

        # 3. Hoàn tất toàn bộ 100% với danh sách Glossary đầy đủ
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
        logger.info(f"✅ [Job Completed] doc_id={doc_id}, extracted {len(glossary_items)} glossary items.")

        # Cleanup local files
        if os.path.exists(local_input_file):
            os.remove(local_input_file)
        if os.path.exists(translated_local_path):
            os.remove(translated_local_path)
            
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
