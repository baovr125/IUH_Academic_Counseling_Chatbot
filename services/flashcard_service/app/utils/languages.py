"""Danh sách ngôn ngữ được hỗ trợ - MỘT nguồn sự thật cho flashcard_service.

Phải khớp với frontend (`LANG_CONFIG` trong frontend/src/services/deckStorage.ts) và realtime_translation_service
(`SUPPORTED_CODES` trong app/services/language_detection.py); test hợp đồng ở tests/unit/test_languages.py kiểm tra điều này.
Hệ thống dùng mã ngôn ngữ ISO (en, zh, ja, ko, vi...), KHÔNG dùng mã quốc gia của lá cờ (GB, CN, JP, KR, VN).
"""
from typing import Optional

SUPPORTED_LANGS = ("en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th", "vi")

# Tiếng Việt là ngôn ngữ giải nghĩa (đích) nên không phải ngôn ngữ để "học" trong luồng chính.
EXPLANATION_LANG = "vi"
LEARNABLE_LANGS = tuple(code for code in SUPPORTED_LANGS if code != EXPLANATION_LANG)

# Tên tiếng Việt, dùng để đặt tên "Sổ mặc định" của từng ngôn ngữ.
LANG_NAMES_VI = {
    "en": "Tiếng Anh", "de": "Tiếng Đức", "zh": "Tiếng Trung", "ja": "Tiếng Nhật", "ko": "Tiếng Hàn",
    "fr": "Tiếng Pháp", "es": "Tiếng Tây Ban Nha", "ru": "Tiếng Nga", "th": "Tiếng Thái", "vi": "Tiếng Việt",
}


def normalize_lang(value: Optional[str]) -> Optional[str]:
    """Chuẩn hóa về mã ISO đã hỗ trợ ('en-US' -> 'en', 'zh_CN' -> 'zh'). Trả None nếu rỗng, 'auto' hoặc không hỗ trợ."""
    if not value:
        return None
    code = str(value).strip().lower().replace("_", "-").split("-")[0]
    return code if code in SUPPORTED_LANGS else None


def default_deck_title(lang_code: str) -> str:
    return f"Từ vựng {LANG_NAMES_VI.get(lang_code, lang_code.upper())}"
