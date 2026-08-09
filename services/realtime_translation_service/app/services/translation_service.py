import os
import time
from typing import Tuple
from google import genai
from app.services.cache_service import get_cached_translation, set_cached_translation
from app.utils.logger import logger

_gemini_client = None

def get_gemini():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            try:
                _gemini_client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Gemini client creation failed: {e}")
    return _gemini_client

async def translate_text(text: str, source_lang: str = "en", target_lang: str = "vi") -> Tuple[str, bool, float]:
    start_time = time.perf_counter()
    cache_key = f"{source_lang}_{target_lang}_{text.strip().lower()}"
    
    cached = get_cached_translation(cache_key)
    if cached:
        latency = (time.perf_counter() - start_time) * 1000
        return cached, True, round(latency, 2)
        
    # Dictionary fallback for common academic terminology
    ACADEMIC_DICT = {
        "prerequisite": "môn học tiên quyết",
        "credits": "tín chỉ",
        "gpa": "điểm trung bình tích lũy",
        "curriculum": "chương trình đào tạo",
        "syllabus": "đề cương môn học",
        "tuition": "học phí",
        "scholarship": "học bổng",
        "graduation": "tốt nghiệp",
        "transcript": "bảng điểm"
    }
    
    clean_lower = text.strip().lower()
    if clean_lower in ACADEMIC_DICT:
        translated = ACADEMIC_DICT[clean_lower]
        set_cached_translation(cache_key, translated)
        latency = (time.perf_counter() - start_time) * 1000
        return translated, False, round(latency, 2)
        
    client = get_gemini()
    if client:
        try:
            prompt = f"Translate the following text accurately from {source_lang} to {target_lang}. Only output the direct translation without quotes or extra text:\n\n{text}"
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if res and res.text:
                translated = res.text.strip()
                set_cached_translation(cache_key, translated)
                latency = (time.perf_counter() - start_time) * 1000
                return translated, False, round(latency, 2)
        except Exception as e:
            logger.exception(f"Translation LLM error: {e}")
            
    # Mock fallback
    translated = f"[Bản dịch: {text}]"
    latency = (time.perf_counter() - start_time) * 1000
    return translated, False, round(latency, 2)
