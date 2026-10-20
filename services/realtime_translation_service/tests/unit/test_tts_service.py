"""tts_service: bảng giọng đủ 10 ngôn ngữ, thử lại khi lỗi tạm thời, không bao giờ trả âm thanh rỗng, báo sức khỏe."""
from unittest.mock import patch

import pytest

from app.services import tts_service
from app.services.tts_service import TTSUnavailable, resolve_voice, synthesize

LANGS = ["en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th", "vi"]


@pytest.fixture(autouse=True)
def _fast_and_clean():
    tts_service.reset_state()
    with patch.object(tts_service, "RETRY_DELAY_S", 0):
        yield
    tts_service.reset_state()


class FakeCommunicate:
    """edge_tts.Communicate giả: mỗi lần gọi lấy một kịch bản (list chunk hoặc Exception) từ hàng đợi."""
    script: list = []
    calls = 0

    def __init__(self, text, voice, rate=None):
        type(self).calls += 1
        self.item = type(self).script.pop(0)

    async def stream(self):
        if isinstance(self.item, Exception):
            raise self.item
        for chunk in self.item:
            yield chunk


def script(*items):
    FakeCommunicate.script = list(items)
    FakeCommunicate.calls = 0
    return patch.object(tts_service.edge_tts, "Communicate", FakeCommunicate)


AUDIO = [{"type": "WordBoundary"}, {"type": "audio", "data": b"\xff\xfb\x90"}, {"type": "audio", "data": b"\x44"}]


class TestVoices:
    @pytest.mark.parametrize("lang", LANGS)
    def test_every_language_has_a_voice_with_matching_locale(self, lang):
        assert resolve_voice(lang).lower().startswith(lang)

    @pytest.mark.parametrize("raw,expected", [("de-DE", "de-DE-KillianNeural"), ("de_DE", "de-DE-KillianNeural"), ("EN-us", "en-US-AriaNeural"),
                                              ("ja-JP", "ja-JP-NanamiNeural"), ("zh_CN", "zh-CN-XiaoxiaoNeural"), ("fr-CA", "fr-FR-DeniseNeural")])
    def test_locales(self, raw, expected):
        assert resolve_voice(raw) == expected

    @pytest.mark.parametrize("raw", [None, "", "auto", "xx"])
    def test_unknown_falls_back_to_english_voice(self, raw):
        assert resolve_voice(raw) == "en-US-AriaNeural"


class TestSynthesize:
    async def test_returns_audio_chunks_only(self):
        with script(AUDIO):
            assert await synthesize("Hallo", "de-DE-KillianNeural") == b"\xff\xfb\x90\x44"
        assert tts_service.health()["status"] == "ok"

    async def test_retries_transient_failure_then_succeeds(self):
        with script(Exception("403 Invalid response status"), Exception("403"), AUDIO):
            assert await synthesize("Hallo", "v") == b"\xff\xfb\x90\x44"
            assert FakeCommunicate.calls == 3
        assert tts_service.health()["status"] == "ok"

    async def test_gives_up_after_retries_and_reports_degraded(self):
        with script(*[Exception("403")] * (tts_service.RETRIES + 1)):
            with pytest.raises(TTSUnavailable):
                await synthesize("Hallo", "v")
        h = tts_service.health()
        assert h["status"] == "degraded" and "403" in h["last_error"] and h["consecutive_failures"] == 1

    async def test_empty_audio_is_an_error_never_returned(self):
        with script(*[[{"type": "WordBoundary"}]] * (tts_service.RETRIES + 1)):
            with pytest.raises(TTSUnavailable):
                await synthesize("Hallo", "v")

    async def test_recovery_clears_degraded(self):
        with script(*[Exception("x")] * (tts_service.RETRIES + 1)):
            with pytest.raises(TTSUnavailable):
                await synthesize("a", "v")
        with script(AUDIO):
            await synthesize("a", "v")
        assert tts_service.health()["status"] == "ok"

    def test_health_unknown_before_any_call(self):
        assert tts_service.health()["status"] == "unknown"
