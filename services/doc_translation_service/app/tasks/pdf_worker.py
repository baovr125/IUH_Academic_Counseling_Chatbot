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

import sys
# Thêm thư mục app/services vào sys.path để các module trong pdf2zh có thể dùng import tuyệt đối (vd: from pdf2zh.xxx import yyy)
services_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services"))
if services_dir not in sys.path:
    sys.path.insert(0, services_dir)

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
        from app.services.pdf2zh.high_level import translate
        from app.services.pdf2zh.doclayout import ModelInstance, OnnxModel
        from app.services.glossary_extractor import extract_glossary

        from app.services.ollama_translator import check_ollama_health
        if check_ollama_health():
            model_used = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
        else:
            model_used = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile (Groq)")
        glossary_items = []

        def status_cb(progress_obj: Any):
            # PDFMathTranslate passes a tqdm progress object
            # We can pull current/total from it
            if hasattr(progress_obj, 'n') and hasattr(progress_obj, 'total') and progress_obj.total > 0:
                prog = int(50 + (progress_obj.n / progress_obj.total) * 45)
                msg = f"Đang dịch PDF (trang {progress_obj.n}/{progress_obj.total}) với DocLayout-YOLO..."
            else:
                prog = 50
                msg = "Đang dịch PDF với DocLayout-YOLO..."
                
            update_job_status(
                doc_id, 
                "processing", 
                prog, 
                msg, 
                model_used=model_used,
                glossary=glossary_items
            )

        update_job_status(doc_id, "processing", 20, "Đang trích xuất nội dung văn bản để phân tích thuật ngữ...")
        
        # 1. Trích xuất text cơ bản để tìm Glossary
        md_text = ""
        try:
            doc_meta = fitz.open(local_input_file)
            for page in doc_meta:
                md_text += page.get_text("text") + "\n"
            doc_meta.close()
        except Exception as ex:
            logger.warning(f"Không thể trích xuất văn bản thô cho glossary: {ex}")
        
        update_job_status(doc_id, "processing", 30, "Đang trích xuất thuật ngữ chuyên ngành (Glossary)...")
        if md_text:
            try:
                # nest_asyncio.apply() ở đầu file đảm bảo asyncio.run() hoạt động an toàn
                glossary_items = asyncio.run(extract_glossary(md_text, target_lang=target_lang, source_lang=source_lang))
                if glossary_items:
                    # Publish event to RabbitMQ for flashcard_service
                    publish_doc_translated_event(
                        doc_id=doc_id,
                        user_id=user_id,
                        file_name=object_name.replace('source/', ''),
                        glossary=glossary_items,
                        source_lang=source_lang
                    )
                    update_job_status(
                        doc_id, 
                        "processing", 
                        35, 
                        f"Đã trích xuất xong {len(glossary_items)} thuật ngữ. Đang load model Layout...",
                        glossary=glossary_items
                    )
            except Exception as e:
                logger.warning(f"Lỗi khi trích xuất glossary: {e}")
        
        # 2. Load DocLayout-YOLO Model
        update_job_status(doc_id, "processing", 40, "Đang nạp mô hình nhận diện khung PDF (DocLayout-YOLO)...")
        if ModelInstance.value is None:
            ModelInstance.value = OnnxModel.load_available()

        # 3. Dịch thuật bằng PDFMathTranslate pipeline
        update_job_status(doc_id, "processing", 50, "Bắt đầu dịch trực tiếp trên PDF (giữ nguyên định dạng)...")
        
        out_dir = tempfile.gettempdir()
        result_files = translate(
            files=[local_input_file],
            output=out_dir,
            lang_in=source_lang,
            lang_out=target_lang,
            service=f"ollama_pdf:{model_used}",
            thread=4,
            callback=status_cb,
            model=ModelInstance.value,
        )
        
        # translate trả về danh sách các tuple: (mono_pdf_path, dual_pdf_path)
        if not result_files or len(result_files) == 0:
            raise RuntimeError("PDFMathTranslate không trả về file kết quả nào.")
            
        mono_pdf = result_files[0][0]
        
        # Copy kết quả sang tên mong muốn
        import shutil
        shutil.copy2(mono_pdf, translated_local_path)

        # Upload translated file to MinIO
        translated_object_name = f"translated/{doc_id}.pdf"
        upload_file(translated_object_name, translated_local_path)
        
        translated_file_url = f"/api/v1/documents/{doc_id}/download"

        # Chuẩn hóa đường dẫn ảnh trong Markdown sang API endpoint phục vụ trực tuyến (bỏ qua vì không còn markdown gốc)
        client_markdown_text = "Tính năng xem Markdown bị vô hiệu hóa vì hệ thống đã chuyển sang chế độ Layout Analysis (Pixel-perfect)."

        # 3. Hoàn tất toàn bộ 100%
        update_job_status(
            doc_id, "completed", 100,
            f"Đã hoàn thành dịch thuật thành công bằng {model_used}!",
            pages_processed=total_pages,
            total_pages=total_pages,
            translated_file_url=translated_file_url,
            translated_text=client_markdown_text,
            summary_json={},
            glossary=glossary_items,
            model_used=model_used
        )
        logger.info(f"✅ [Job Completed] doc_id={doc_id}, extracted {len(glossary_items)} glossary items.")

        return {"doc_id": doc_id, "status": "completed"}

    except Exception as e:
        # Kiểm tra nếu là SoftTimeLimitExceeded
        if "SoftTimeLimitExceeded" in type(e).__name__:
            logger.error(f"⏰ [Timeout Warning] Celery SoftTimeLimitExceeded cho doc_id={doc_id}.")
            update_job_status(doc_id, "failed", 0, "Tác vụ quá thời gian giới hạn (Timeout).", error="SoftTimeLimitExceeded")
            return {"doc_id": doc_id, "status": "failed", "error": "SoftTimeLimitExceeded"}

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
