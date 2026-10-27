import json
from typing import List
from app.utils.logger import logger
from app.services.supabase_client import get_supabase

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
        if not supabase:
            return []
        # Supabase mặc định trả tối đa 1.000 hàng mỗi truy vấn: phân trang để không cắt cụt từ điển.
        rows: List[dict] = []
        page_size, offset = 1000, 0
        while True:
            res = (
                supabase.table("domain_dictionaries")
                .select("domain, word, translation")
                .order("domain")
                .order("word")
                .range(offset, offset + page_size - 1)
                .execute()
            )
            batch = res.data or []
            rows.extend(batch)
            if len(batch) < page_size:
                return rows
            offset += page_size

    try:
        all_dicts = await asyncio.to_thread(_fetch_supabase)
        if r and all_dicts:
            await asyncio.to_thread(r.setex, cache_key, 300, json.dumps(all_dicts))
        return all_dicts
    except Exception as e:
        logger.error(f"Supabase fetch all dicts error: {e}")
        return []
