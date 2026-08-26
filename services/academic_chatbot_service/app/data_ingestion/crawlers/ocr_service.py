import os
import re
import time
import logging

try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)
gemini_client = None
if os.getenv("GEMINI_API_KEY") and genai:
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def execute_ocr(prompt: str, img) -> str:
    """
    Gửi ảnh lên Gemini API để OCR. Tự động đổi model nếu lỗi 429 quota.
    Nếu 503 (Server sập), chờ 10s. Nếu tất cả model chết, raise Exception.
    """
    if not gemini_client:
        return "[LỖI: Chưa cấu hình GEMINI_API_KEY]"
        
    models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemma-4-31b-it", "gemini-1.5-flash"]
    
    for model_name in models:
        retries = 3
        while retries > 0:
            try:
                response = gemini_client.models.generate_content(
                    model=model_name,
                    contents=[prompt, img]
                )
                if response.text and len(response.text.strip()) > 5:
                    return response.text.strip()
                return ""
            except Exception as api_err:
                err_msg = str(api_err).lower()
                logger.warning(f"Model {model_name} thất bại: {api_err}")
                
                if "429" in err_msg or "quota" in err_msg or "resource_exhausted" in err_msg:
                    if "perday" in err_msg or "per_day" in err_msg:
                        logger.error(f"Model {model_name} đã hết Quota trong ngày. Chuyển model khác!")
                        break
                        
                    match = re.search(r'retry in ([\d\.]+)s', err_msg)
                    wait_time = float(match.group(1)) + 1.0 if match else 60.0
                    logger.warning(f"Bị giới hạn API (429). Đợi {wait_time}s trước khi thử lại...")
                    time.sleep(wait_time)
                    retries -= 1
                    continue
                elif "503" in err_msg or "unavailable" in err_msg or "500" in err_msg:
                    logger.warning(f"Google API đang quá tải ({err_msg[:30]}). Đợi 10s trước khi thử lại...")
                    time.sleep(10)
                    retries -= 1
                    continue
                else:
                    break
    
    logger.error(f"Tất cả các model đều thất bại OCR.")
    raise Exception("API_OCR_FAILED")
