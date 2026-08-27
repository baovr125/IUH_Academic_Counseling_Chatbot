import pytest
from unittest.mock import patch, MagicMock
from app.services.cache_service import (
    get_cached_translation,
    set_cached_translation,
    get_cached_audio_url,
    set_cached_audio_url,
)


class TestRedisCacheService:
    def test_get_cached_translation_hit(self):
        with patch("app.services.cache_service.get_redis") as mock_get_r:
            mock_redis = MagicMock()
            mock_redis.get.return_value = "xin chào"
            mock_get_r.return_value = mock_redis

            result = get_cached_translation("hello_en_vi")
            assert result == "xin chào"
            mock_redis.get.assert_called_once_with("trans:hello_en_vi")

    def test_get_cached_translation_miss(self):
        with patch("app.services.cache_service.get_redis") as mock_get_r:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_r.return_value = mock_redis

            result = get_cached_translation("unknown_word")
            assert result is None

    def test_set_cached_translation_with_ttl(self):
        with patch("app.services.cache_service.get_redis") as mock_get_r:
            mock_redis = MagicMock()
            mock_get_r.return_value = mock_redis

            set_cached_translation("academic_en_vi", "học thuật", ttl=3600)
            mock_redis.setex.assert_called_once_with("trans:academic_en_vi", 3600, "học thuật")

    def test_get_and_set_cached_audio_url(self):
        with patch("app.services.cache_service.get_redis") as mock_get_r:
            mock_redis = MagicMock()
            mock_redis.get.return_value = "http://minio:9000/audio.mp3"
            mock_get_r.return_value = mock_redis

            set_cached_audio_url("md5_hash_123", "http://minio:9000/audio.mp3", ttl=604800)
            mock_redis.setex.assert_called_once_with("tts_url:md5_hash_123", 604800, "http://minio:9000/audio.mp3")

            url = get_cached_audio_url("md5_hash_123")
            assert url == "http://minio:9000/audio.mp3"

    def test_redis_unavailable_handles_gracefully(self):
        with patch("app.services.cache_service.get_redis") as mock_get_r:
            mock_get_r.return_value = None

            assert get_cached_translation("any_key") is None
            assert get_cached_audio_url("any_key") is None
            # Should not raise exception
            set_cached_translation("any_key", "val")
            set_cached_audio_url("any_key", "url")
