import json
import os
import math
from typing import Optional, List
from app.utils.logger import logger
from app.services.supabase_client import get_supabase

from app.services.cache_service import get_redis
import asyncio

# Cố định danh sách các chuyên ngành và emoji
_PREDEFINED_DOMAINS = [
    "Công nghệ Thông tin (IT)",
    "Y khoa / Sức khỏe",
    "Kinh tế / Tài chính",
    "Kỹ thuật Cơ khí",
    "Luật / Pháp lý",
    "Marketing"
]

DOMAIN_EMOJIS = {
    "Công nghệ Thông tin (IT)": "💻",
    "Y khoa / Sức khỏe": "💊",
    "Kinh tế / Tài chính": "📊",
    "Kỹ thuật Cơ khí": "⚙️",
    "Luật / Pháp lý": "⚖️",
    "Marketing": "📈"
}

async def get_all_domains() -> List[str]:
    """Trả về danh sách tất cả các chuyên ngành thực tế có trong hệ thống."""
    dicts = await get_all_dictionaries()
    if dicts:
        found_domains = list(set(d.get("domain") for d in dicts if d.get("domain")))
        return found_domains if found_domains else _PREDEFINED_DOMAINS
    return _PREDEFINED_DOMAINS

async def get_all_dictionaries() -> List[dict]:
    """Fetch toàn bộ từ điển với Redis Cache và asyncio.to_thread để không block event loop."""
    from app.services.cache_service import get_redis, get_global_dict_version
    r = get_redis()
    v = get_global_dict_version()
    cache_key = f"all_domain_dictionaries_v{v}"
    
    if r:
        try:
            cached_data = await asyncio.to_thread(r.get, cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis get all_dicts error: {e}")
            
    def _fetch_supabase():
        supabase = get_supabase()
        if supabase:
            res = supabase.table("domain_dictionaries").select("domain, word, translation").execute()
            return res.data if res.data else []
        return []

    try:
        all_dicts = await asyncio.to_thread(_fetch_supabase)
        if r and all_dicts:
            await asyncio.to_thread(r.setex, cache_key, 300, json.dumps(all_dicts))
        return all_dicts
    except Exception as e:
        logger.error(f"Supabase fetch all dicts error: {e}")
        return []

async def auto_detect_domain_long(text: str) -> str:
    """Sử dụng LLM Zero-shot Classification để phân loại chuyên ngành văn bản (trả về JSON)."""
    from app.services.llm_service import get_groq_client
    
    valid_domains = await get_all_domains()
    groq_client = get_groq_client()
    
    if not groq_client:
        return ""

    try:
        minimum_confidence = min(1.0, max(0.0, float(os.getenv("AUTO_DOMAIN_MIN_CONFIDENCE", "0.75"))))
    except (TypeError, ValueError):
        minimum_confidence = 0.75

    system_prompt = (
        f"Phân loại đoạn văn vào tối đa một lĩnh vực trong danh sách: {valid_domains}. "
        "Chỉ chọn lĩnh vực nếu nội dung có bằng chứng rõ ràng; nếu ngắn, mơ hồ, ngoài danh sách "
        "hoặc có nhiều lĩnh vực ngang nhau, hãy chọn unknown. Trả về đúng một JSON object với "
        "domain là tên lĩnh vực chính xác trong danh sách hoặc unknown, và confidence là số từ 0 đến 1. "
        "Confidence biểu thị mức chắc chắn của lựa chọn; unknown phải có confidence thấp."
    )

    try:
        res = await asyncio.wait_for(
            groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Đoạn văn:\n{text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            ),
            timeout=max(0.1, float(os.getenv("DOMAIN_CLASSIFIER_TIMEOUT_SECONDS", "20"))),
        )
        content = res.choices[0].message.content.strip()
        parsed = json.loads(content)
        detected = parsed.get("domain", "")
        confidence = parsed.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            return ""
        confidence = float(confidence)
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            return ""
        if confidence < minimum_confidence or str(detected).strip().casefold() == "unknown":
            logger.info(
                "Auto-domain abstained",
                extra={"confidence": confidence, "threshold": minimum_confidence},
            )
            return ""
        
        # Exact match (case-insensitive) validation
        for d in valid_domains:
            if d.lower() == detected.lower():
                logger.info(
                    "Auto-domain selected",
                    extra={"domain": d, "confidence": confidence, "threshold": minimum_confidence},
                )
                return d
                
    except Exception as e:
        logger.warning(f"Auto domain JSON detection failed: {e}")
        
    return ""

async def get_combined_short_translation(text: str) -> str:
    """Quét toàn bộ từ điển và tạo chuỗi tổng hợp nghĩa đa chuyên ngành."""
    # Xử lý input (có thể dùng tokenizer chuẩn nếu cần, ở đây dùng lower)
    clean_text = text.strip().lower()
    
    # Loại bỏ các mạo từ tiếng Anh phổ biến để tăng tỉ lệ hit
    prefixes_to_remove = ["a ", "an ", "the ", "to "]
    for p in prefixes_to_remove:
        if clean_text.startswith(p):
            clean_text = clean_text[len(p):].strip()
            break
            
    all_dicts = await get_all_dictionaries()
    
    found_meanings = []
    # Quét khớp (không phân biệt hoa thường)
    for entry in all_dicts:
        if entry.get("word", "").lower() == clean_text:
            d = entry.get("domain", "")
            t = entry.get("translation", "")
            emoji = DOMAIN_EMOJIS.get(d, "🔹")
            found_meanings.append(f"- {emoji} {d}: {t}")
            
    if found_meanings:
        lines = [f"Từ '{clean_text}' có nghĩa chuyên ngành như sau:"] + found_meanings
        return "\n".join(lines)
    
    return ""
