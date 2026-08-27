import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestTranslationApiIntegration:
    def test_health_check_returns_200(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["service"] == "realtime_translation_service"

    def test_translate_text_endpoint(self, client):
        with patch("app.routers.translation.translate_text", new_callable=AsyncMock) as mock_trans:
            mock_trans.return_value = ("Xin chào thế giới", False, 120)

            res = client.post("/api/v1/translate/text", json={
                "text": "Hello world",
                "source_lang": "en",
                "target_lang": "vi"
            })
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert data["data"]["translated_text"] == "Xin chào thế giới"
            assert data["data"]["cached"] is False

    def test_lookup_endpoint(self, client):
        with patch("app.routers.translation.translate_text", new_callable=AsyncMock) as mock_trans, \
             patch("app.routers.translation.get_word_audio", new_callable=AsyncMock) as mock_dict:
            mock_trans.return_value = ("thông minh", True, 2)
            mock_dict.return_value = {"phonetic": "/ɪnˈtelɪdʒənt/", "audio_url": "http://audio.mp3"}

            res = client.post("/api/v1/translate/lookup", json={
                "word": "intelligent"
            })
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert data["data"]["word"] == "intelligent"
            assert data["data"]["definition"] == "thông minh"
            assert data["data"]["phonetic"] == "/ɪnˈtelɪdʒənt/"

    def test_tts_endpoint_empty_text_returns_204(self, client):
        res = client.get("/api/v1/translate/tts?text=   &lang=en")
        assert res.status_code == 204

    def test_tts_endpoint_cache_hit_returns_audio(self, client):
        with patch("app.routers.translation.audio_exists") as mock_exists, \
             patch("app.routers.translation.get_audio_bytes") as mock_get_bytes:
            mock_exists.return_value = True
            mock_get_bytes.return_value = b"\xff\xfb\x90\x44"

            res = client.get("/api/v1/translate/tts?text=hello&lang=en")
            assert res.status_code == 200
            assert res.headers["content-type"] == "audio/mpeg"
            assert res.headers["x-cache"] == "HIT"
            assert res.content == b"\xff\xfb\x90\x44"
