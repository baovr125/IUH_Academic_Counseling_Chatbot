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

def set_cached_translation(key: str, value: str, ttl: int = 86400):
    r = get_redis()
    if r:
        try:
            r.setex(f"trans:{key}", ttl, value)
        except Exception as e:
            logger.warning(f"Redis set error: {e}")

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

