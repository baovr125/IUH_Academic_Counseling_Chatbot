"""Danh sách ngôn ngữ: chuẩn hóa mã và HỢP ĐỒNG giữa flashcard_service, frontend và realtime_translation_service."""
import re
from pathlib import Path

import pytest

from app.utils.languages import (
    EXPLANATION_LANG,
    LEARNABLE_LANGS,
    SUPPORTED_LANGS,
    default_deck_title,
    normalize_lang,
)

REPO = Path(__file__).resolve().parents[4]
FRONTEND_CONFIG = REPO / "frontend" / "src" / "services" / "deckStorage.ts"
REALTIME_DETECTION = REPO / "services" / "realtime_translation_service" / "app" / "services" / "language_detection.py"
TTS_ROUTER = Path(__file__).resolve().parents[2] / "app" / "routers" / "flashcards.py"


class TestRegistry:
    def test_ten_languages_with_iso_codes(self):
        assert SUPPORTED_LANGS == ("en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th", "vi")

    def test_vietnamese_is_the_explanation_language_not_a_learnable_one(self):
        assert EXPLANATION_LANG == "vi" and "vi" not in LEARNABLE_LANGS and len(LEARNABLE_LANGS) == 9

    @pytest.mark.parametrize("raw,expected", [
        ("en", "en"), ("EN", "en"), (" de ", "de"), ("en-US", "en"), ("zh_CN", "zh"), ("ja-JP", "ja"), ("vi", "vi"),
    ])
    def test_normalize_accepts_locales(self, raw, expected):
        assert normalize_lang(raw) == expected

    @pytest.mark.parametrize("raw", [None, "", "  ", "auto", "AUTO", "xx", "gb", "cn", "jp", "kr", "vn", "english"])
    def test_normalize_rejects_unknown_auto_and_flag_country_codes(self, raw):
        # "GB/CN/JP/KR/VN" là mã quốc gia của lá cờ, KHÔNG phải mã ngôn ngữ của hệ thống.
        assert normalize_lang(raw) is None

    def test_default_deck_titles_are_vietnamese(self):
        assert default_deck_title("de") == "Từ vựng Tiếng Đức"
        assert default_deck_title("ja") == "Từ vựng Tiếng Nhật"


class TestCrossServiceContract:
    def test_frontend_lang_config_matches_backend(self):
        if not FRONTEND_CONFIG.exists():
            pytest.skip("không có mã nguồn frontend (chạy trong image)")
        text = FRONTEND_CONFIG.read_text(encoding="utf8")
        block = text[text.index("export const LANG_CONFIG"):text.index("function getStorageKey")]
        codes = re.findall(r"^\s{2}([a-z]{2}):\s*\{", block, flags=re.MULTILINE)
        assert tuple(codes) == SUPPORTED_LANGS

    def test_realtime_translation_supported_codes_match(self):
        if not REALTIME_DETECTION.exists():
            pytest.skip("không có mã nguồn realtime_translation_service")
        match = re.search(r"SUPPORTED_CODES\s*=\s*\(([^)]*)\)", REALTIME_DETECTION.read_text(encoding="utf8"))
        codes = tuple(re.findall(r'"([a-z]{2})"', match.group(1)))
        assert codes == SUPPORTED_LANGS

    def test_every_language_has_a_tts_voice(self):
        text = TTS_ROUTER.read_text(encoding="utf8")
        block = text[text.index("TTS_VOICE_MAP"):text.index("def resolve_voice")]
        for code in SUPPORTED_LANGS:
            assert f'"{code}":' in block, f"thiếu giọng đọc TTS cho {code}"
