import os
from typing import Optional
import redis
from app.utils.logger import logger

_redis_client: Optional[redis.Redis] = None
_redis_bytes_client: Optional[redis.Redis] = None

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

def get_redis_bytes() -> Optional[redis.Redis]:
    global _redis_bytes_client
    if _redis_bytes_client is not None:
        return _redis_bytes_client
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    try:
        # For binary data, decode_responses must be False
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=False, socket_timeout=1.0)
        r.ping()
        _redis_bytes_client = r
        return _redis_bytes_client
    except Exception as e:
        logger.warning(f"Could not connect to Redis bytes client at {redis_host}:{redis_port}: {e}")
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

def get_cached_audio(key: str) -> Optional[bytes]:
    r = get_redis_bytes()
    if r:
        try:
            return r.get(f"tts:{key}")
        except Exception as e:
            logger.warning(f"Redis get audio error: {e}")
    return None

def set_cached_audio(key: str, audio_bytes: bytes, ttl: int = 604800): # Cache for 7 days
    r = get_redis_bytes()
    if r:
        try:
            r.setex(f"tts:{key}", ttl, audio_bytes)
        except Exception as e:
            logger.warning(f"Redis set audio error: {e}")
