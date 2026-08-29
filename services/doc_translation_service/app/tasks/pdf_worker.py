import os
import json
import redis
import asyncio
import tempfile
import fitz  # PyMuPDF - để đếm số trang
import nest_asyncio
from typing import Dict, Any, Optional
from app.utils.logger import logger
from app.celery_app import celery_app, REDIS_URL
from app.utils.minio_client import download_file, upload_file
from app.utils.rabbitmq_publisher import publish_doc_translated_event

# Cho phép asyncio.run() hoạt động an toàn trong Celery worker (kể cả eventlet/gevent pool)
nest_asyncio.apply()

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

@celery_app.task(
    bind=True, 
    name="app.tasks.pdf_worker.process_document_translation_job_sync",
    acks_late=True,
    reject_on_worker_lost=True
)
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

    # Đếm số trang thực tế để báo cáo tiến độ chính xác
    total_pages = 1
    try:
        doc_meta = fitz.open(local_input_file)
        total_pages = len(doc_meta)
        doc_meta.close()
    except Exception:
        pass

    translated_local_path = os.path.join(tempfile.gettempdir(), f"translated_{doc_id}.pdf")

    try:
        from app.services.markdown_pdf_service import extract_pdf_to_markdown, render_markdown_to_pdf
        from app.services.ollama_translator import translate_markdown_document_ollama
        from app.services.glossary_extractor import extract_glossary

        translated_text = ""
        model_used = "Gemini 2.5 Flash"
        glossary_items = []

        def status_cb(progress: int, message: str, model_name: str = ""):
            nonlocal model_used
            if model_name:
                model_used = model_name
            update_job_status(
                doc_id, 
                "processing", 
                progress, 
                message, 
                model_used=model_used,
                glossary=glossary_items
            )

        update_job_status(doc_id, "processing", 20, "Đang bóc tách PDF bài báo khoa học thành cấu trúc Markdown...")
        md_text, image_dir = extract_pdf_to_markdown(local_input_file, doc_id)
        
        # 1. Xử lý trích xuất Glossary TRƯỚC khi dịch
        glossary_context_str = ""
        update_job_status(doc_id, "processing", 30, "Đang trích xuất thuật ngữ chuyên ngành (Glossary)...")
        if md_text:
            try:
                # nest_asyncio.apply() ở đầu file đảm bảo asyncio.run() hoạt động an toàn
                glossary_items = asyncio.run(extract_glossary(md_text, target_lang=target_lang, source_lang=source_lang))
                if glossary_items:
                    # Format valid glossary pairs into string for translation prompt
                    valid_pairs = []
                    for item in glossary_items:
                        term = str(item.get('term', '')).strip()
                        meaning = str(item.get('translation') or item.get('vi') or '').strip()
                        if term and meaning and not meaning.lower().startswith("thuật ngữ:"):
                            valid_pairs.append(f"- {term}: {meaning}")
                    glossary_context_str = "\n".join(valid_pairs)
                    
                    # Publish event to RabbitMQ for flashcard_service
                    publish_doc_translated_event(
                        doc_id=doc_id,
                        user_id=user_id,
                        file_name=object_name.replace('source/', ''),
                        glossary=glossary_items,
                        source_lang=source_lang
                    )
                    # Hiển thị Glossary lên giao diện ngay lập tức
                    update_job_status(
                        doc_id, 
                        "processing", 
                        35, 
                        f"Đã trích xuất xong {len(glossary_items)} thuật ngữ. Đang bắt đầu dịch thuật...",
                        glossary=glossary_items
                    )
            except Exception as e:
                logger.warning(f"Lỗi khi trích xuất glossary: {e}")
        
        # 2. Dịch thuật song song với Glossary Context
        translated_text, model_used = translate_markdown_document_ollama(
            md_text=md_text,
            source_lang=source_lang,
            target_lang=target_lang,
            status_callback=status_cb,
            glossary_context=glossary_context_str
        )

        update_job_status(
            doc_id, "processing", 85, 
            f"Đang render lại bản dịch ({model_used}) thành PDF chất lượng cao...", 
            model_used=model_used,
            glossary=glossary_items
        )
        out_ext = ".pdf"
        render_markdown_to_pdf(translated_text, translated_local_path)

        # Upload translated file to MinIO
        translated_object_name = f"translated/{doc_id}{out_ext}"
        upload_file(translated_object_name, translated_local_path)
        
        translated_file_url = f"/api/v1/documents/{doc_id}/download"

        # 3. Hoàn tất toàn bộ 100%
        update_job_status(
            doc_id, "completed", 100,
            f"Đã hoàn thành dịch thuật thành công bằng {model_used}!",
            pages_processed=total_pages,
            total_pages=total_pages,
            translated_file_url=translated_file_url,
            translated_text=translated_text,
            summary_json={},
            glossary=glossary_items,
            model_used=model_used
        )
        logger.info(f"✅ [Job Completed] doc_id={doc_id}, extracted {len(glossary_items)} glossary items.")

        return {"doc_id": doc_id, "status": "completed"}

    except Exception as e:
        logger.exception(f"❌ [Job Failed] Lỗi xử lý dịch thuật doc_id={doc_id}: {e}")
        update_job_status(doc_id, "failed", 0, f"Thất bại: {str(e)}", error=str(e))
        return {"doc_id": doc_id, "status": "failed", "error": str(e)}

    finally:
        # Luôn dọn dẹp temp files dù pipeline thành công hay fail
        for temp_file in [local_input_file, translated_local_path]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError as cleanup_err:
                    logger.warning(f"Không thể xóa temp file {temp_file}: {cleanup_err}")


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
