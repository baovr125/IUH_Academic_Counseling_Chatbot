import os
from typing import Optional
import redis
from app.utils.logger import logger

_redis_client: Optional[redis.Redis] = None

def get_redis() -> Optional[redis.Redis]:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    try:
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True, socket_timeout=1.0)
        r.ping()
        _redis_client = r
        return _redis_client
    except Exception as e:
        logger.warning(f"Could not connect to Redis at {redis_host}:{redis_port}: {e}")
        return None

def get_cached_translation(key: str) -> Optional[str]:
    r = get_redis()
    if r:
        try:
            return r.get(f"trans:{key}")
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
    return None

def get_cached_warning(key: str) -> Optional[str]:
    r = get_redis()
    if r:
        try:
            return r.get(f"trans_warn:{key}")
        except Exception:
            pass
    return None

def set_cached_translation(key: str, value: str, warning: str = None, ttl: int = 86400):
    r = get_redis()
    if r:
        try:
            r.setex(f"trans:{key}", ttl, value)
            if warning:
                r.setex(f"trans_warn:{key}", ttl, warning)
            else:
                r.delete(f"trans_warn:{key}")
        except Exception as e:
            logger.warning(f"Redis set error: {e}")

def get_cached_domain_result(key: str) -> Optional[dict]:
    """Kết quả dịch theo chuyên ngành (bản dịch + domain + cảnh báo) dạng JSON."""
    import json

    r = get_redis()
    if r:
        try:
            raw = r.get(f"domtrans:{key}")
            return json.loads(raw) if raw else None
        except Exception as e:
            logger.warning(f"Redis get domain result error: {e}")
    return None


def set_cached_domain_result(key: str, value: dict, ttl: int = 86400):
    import json

    r = get_redis()
    if r:
        try:
            r.setex(f"domtrans:{key}", ttl, json.dumps(value, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Redis set domain result error: {e}")


def get_global_dict_version() -> int:
    r = get_redis()
    if r:
        try:
            v = r.get("global_dict_ver")
            return int(v) if v else 1
        except Exception:
            pass
    return 1

def increment_global_dict_version() -> int:
    r = get_redis()
    if r:
        try:
            return r.incr("global_dict_ver")
        except Exception:
            pass
    return 1

def get_translation_text_hash(text: str) -> str:
    """Hash normalized translation input without collapsing meaningful letter case."""
    import hashlib
    import unicodedata

    normalized = unicodedata.normalize("NFC", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def get_cached_audio_url(key: str) -> Optional[str]:
    r = get_redis()
    if r:
        try:
            return r.get(f"tts_url:{key}")
        except Exception as e:
            logger.warning(f"Redis get audio url error: {e}")
    return None

def set_cached_audio_url(key: str, audio_url: str, ttl: int = 604800): # Cache URL string for 7 days
    r = get_redis()
    if r:
        try:
            r.setex(f"tts_url:{key}", ttl, audio_url)
        except Exception as e:
            logger.warning(f"Redis set audio url error: {e}")

def get_domain_version(domain: str) -> int:
    if domain == "auto":
        return get_global_dict_version()
        
    r = get_redis()
    if not r or not domain or domain == "Dịch thông thường (Mặc định)":
        return 0
    try:
        v = r.get(f"domain_ver:{domain}")
        return int(v) if v else 1
    except Exception as e:
        logger.warning(f"Redis get domain_ver error: {e}")
        return 1

def increment_domain_version(domain: str) -> int:
    r = get_redis()
    if r and domain and domain != "Dịch thông thường (Mặc định)":
        try:
            return r.incr(f"domain_ver:{domain}")
        except Exception as e:
            logger.warning(f"Redis incr domain_ver error: {e}")
    return 0

