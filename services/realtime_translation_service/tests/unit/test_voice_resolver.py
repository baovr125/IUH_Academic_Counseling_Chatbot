import pytest
from app.routers.translation import resolve_voice, TTS_VOICE_MAP


class TestVoiceResolver:
    @pytest.mark.parametrize("input_lang, expected_voice", [
        ("vi", "vi-VN-HoaiMyNeural"),
        ("en", "en-US-AriaNeural"),
        ("de", "de-DE-KillianNeural"),
        ("zh", "zh-CN-XiaoxiaoNeural"),
        ("ja", "ja-JP-NanamiNeural"),
        ("ko", "ko-KR-SunHiNeural"),
        ("fr", "fr-FR-DeniseNeural"),
        ("es", "es-ES-ElviraNeural"),
        ("ru", "ru-RU-SvetlanaNeural"),
        ("th", "th-TH-PremwadeeNeural"),
        ("vi-VN", "vi-VN-HoaiMyNeural"),
        ("en-US", "en-US-AriaNeural"),
        ("en-GB", "en-GB-RyanNeural"),
        ("de-DE", "de-DE-KillianNeural"),
        ("de_DE", "de-DE-KillianNeural"),
    ])
    def test_resolve_voice_known_languages_and_locales(self, input_lang, expected_voice):
        assert resolve_voice(input_lang) == expected_voice

    def test_resolve_voice_fallback_for_unknown_language(self):
        # Unknown language should fallback to default AriaNeural
        assert resolve_voice("unknown_xyz") == "en-US-AriaNeural"
        assert resolve_voice("") == "en-US-AriaNeural"
        assert resolve_voice(None) == "en-US-AriaNeural"
