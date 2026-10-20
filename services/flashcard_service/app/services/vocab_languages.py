"""Cấu hình sinh từ vựng cho từng ngôn ngữ học (9 ngôn ngữ; tiếng Việt là ngôn ngữ giải nghĩa nên không nằm trong đây).

Mỗi ngôn ngữ có: tên (để đưa vào lời nhắc cho LLM), quy tắc dạng từ gốc, kiểu phiên âm, hệ chữ viết (để loại các "từ"
sai ngôn ngữ, ví dụ LLM trả chữ Hán cho bộ thẻ tiếng Đức) và cách tìm từ khóa trong câu ví dụ.
Danh sách mã phải khớp `app.utils.languages.LEARNABLE_LANGS` (test hợp đồng ở tests/unit/test_vocab_languages.py).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Hệ chữ -> tiền tố tên Unicode của ký tự (unicodedata.name).
_SCRIPT_PREFIXES = {
    "latin": ("LATIN",),
    "cyrillic": ("CYRILLIC",),
    "han": ("CJK UNIFIED", "CJK COMPATIBILITY IDEOGRAPH", "IDEOGRAPHIC ITERATION"),
    "kana": ("HIRAGANA", "KATAKANA"),
    "hangul": ("HANGUL",),
    "thai": ("THAI",),
}


@dataclass(frozen=True)
class VocabLang:
    code: str
    name: str  # tên tiếng Anh, dùng trong lời nhắc
    vi_name: str
    scripts: Tuple[str, ...]  # hệ chữ được phép cho chữ cái của từ vựng
    spaced: bool  # từ ngăn cách bằng khoảng trắng (zh/ja/th thì không)
    headword_rules: str  # quy tắc dạng từ gốc (đưa vào lời nhắc SELECT)
    reading_kind: str  # ipa | pinyin | kana_romaji | romanization
    reading_instruction: str  # yêu cầu cho trường phiên âm (lời nhắc ENRICH)
    example_length: str
    articles: Tuple[str, ...] = ()  # mạo từ đứng đầu của danh từ (de/fr/es): dạng từ vựng có mạo từ, so khớp/chống trùng thì bỏ mạo từ
    token_factor: float = 1.0  # chữ không phải Latin tốn nhiều token hơn: nhân với ngân sách max_tokens

    @property
    def article_pattern(self) -> Optional["re.Pattern[str]"]:
        if not self.articles:
            return None
        # "l'" (tiếng Pháp) dính liền từ sau; các mạo từ còn lại cách một khoảng trắng.
        alternatives = "|".join(re.escape(a) for a in sorted(self.articles, key=len, reverse=True))
        return re.compile(rf"^(?:(?:{alternatives})(?:\s+|(?<=['’])))", re.IGNORECASE)


LANGS: Dict[str, VocabLang] = {
    "en": VocabLang(
        code="en", name="English", vi_name="Tiếng Anh", scripts=("latin",), spaced=True,
        headword_rules=(
            "Each item is a dictionary headword in base form (noun singular, bare verb WITHOUT \"to\", adjective base; "
            "no leading articles) or a common phrasal verb/collocation of 2-3 words. No inflected forms, no proper nouns, no duplicates."
        ),
        reading_kind="ipa",
        reading_instruction="General American IPA between slashes with stress marks, e.g. /səˈsteɪnəbl/. If unsure return \"\".",
        example_length="8-18 words",
    ),
    "de": VocabLang(
        code="de", name="German", vi_name="Tiếng Đức", scripts=("latin",), spaced=True,
        headword_rules=(
            "Each item is a German dictionary headword: NOUNS in nominative singular WITH their definite article and capitalised "
            "(e.g. \"der Hund\", \"die Entscheidung\", \"das Ergebnis\" - the article shows the gender); verbs in the infinitive "
            "(separable verbs as one word, e.g. \"aufstehen\"); adjectives in base form; or a common 2-3 word expression. "
            "No inflected forms, no proper nouns, no duplicates."
        ),
        reading_kind="ipa",
        reading_instruction="Standard German IPA between slashes with stress marks, e.g. /hʊnt/. If unsure return \"\".",
        example_length="6-16 words",
        articles=("der", "die", "das", "ein", "eine"),
    ),
    "fr": VocabLang(
        code="fr", name="French", vi_name="Tiếng Pháp", scripts=("latin",), spaced=True,
        headword_rules=(
            "Each item is a French dictionary headword: NOUNS in singular WITH their definite article "
            "(e.g. \"le chat\", \"la maison\", \"l'école\" - the article shows the gender); verbs in the infinitive; adjectives in the "
            "masculine singular; or a common 2-3 word expression. No inflected forms, no proper nouns, no duplicates."
        ),
        reading_kind="ipa",
        reading_instruction="Standard French IPA between slashes, e.g. /ʃa/ (use ɛ̃ ɑ̃ ɔ̃ for nasal vowels). If unsure return \"\".",
        example_length="6-16 words",
        articles=("le", "la", "les", "l'", "l’", "un", "une"),
    ),
    "es": VocabLang(
        code="es", name="Spanish", vi_name="Tiếng Tây Ban Nha", scripts=("latin",), spaced=True,
        headword_rules=(
            "Each item is a Spanish dictionary headword: NOUNS in singular WITH their definite article "
            "(e.g. \"el libro\", \"la casa\" - the article shows the gender); verbs in the infinitive; adjectives in the masculine "
            "singular; or a common 2-3 word expression. No inflected forms, no proper nouns, no duplicates."
        ),
        reading_kind="ipa",
        reading_instruction="Spanish IPA between slashes with stress marks, e.g. /ˈkasa/. If unsure return \"\".",
        example_length="6-16 words",
        articles=("el", "la", "los", "las", "un", "una"),
    ),
    "ru": VocabLang(
        code="ru", name="Russian", vi_name="Tiếng Nga", scripts=("cyrillic",), spaced=True,
        headword_rules=(
            "Each item is a Russian dictionary headword written in Cyrillic: nouns in nominative singular, verbs in the infinitive "
            "(prefer the imperfective form), adjectives in masculine nominative singular, or a common 2-3 word expression. "
            "No inflected forms, no proper nouns, no duplicates."
        ),
        reading_kind="ipa",
        reading_instruction="IPA between slashes with stress marks, e.g. /ˈdom/. Latin-script IPA only (no Cyrillic). If unsure return \"\".",
        example_length="5-14 words",
        token_factor=1.5,
    ),
    "zh": VocabLang(
        code="zh", name="Chinese (Mandarin)", vi_name="Tiếng Trung", scripts=("han",), spaced=False,
        headword_rules=(
            "Each item is a common Mandarin word or short expression of 1-4 characters in SIMPLIFIED Chinese characters "
            "(not pinyin, not traditional characters). No proper nouns, no duplicates, no single characters that are not words by themselves."
        ),
        reading_kind="pinyin",
        reading_instruction=(
            "Pinyin WITH tone marks, syllables separated by a space, lowercase, e.g. \"hé píng\" or \"xué xí\" "
            "(no IPA, no characters). If unsure return \"\"."
        ),
        example_length="8-24 characters",
        token_factor=1.6,
    ),
    "ja": VocabLang(
        code="ja", name="Japanese", vi_name="Tiếng Nhật", scripts=("han", "kana"), spaced=False,
        headword_rules=(
            "Each item is a Japanese dictionary form written the usual way (kanji and kana as in a dictionary, e.g. \"食べる\", "
            "\"図書館\", \"きれい\"); verbs and i-adjectives in dictionary form; no romaji, no inflected forms, no proper nouns, no duplicates."
        ),
        reading_kind="kana_romaji",
        reading_instruction=(
            "The hiragana reading, then \" · \", then Hepburn romaji, e.g. \"たべる · taberu\" or \"としょかん · toshokan\". "
            "If unsure return \"\"."
        ),
        example_length="10-30 characters",
        token_factor=1.6,
    ),
    "ko": VocabLang(
        code="ko", name="Korean", vi_name="Tiếng Hàn", scripts=("hangul",), spaced=True,
        headword_rules=(
            "Each item is a Korean dictionary headword written in Hangul: nouns in base form, verbs and adjectives in dictionary form "
            "ending in 다 (e.g. \"먹다\"), or a common 2-3 word expression. No romanisation, no inflected forms, no proper nouns, no duplicates."
        ),
        reading_kind="romanization",
        reading_instruction="Revised Romanization of Korean in lowercase Latin letters, e.g. \"meokda\". If unsure return \"\".",
        example_length="5-14 words",
        token_factor=1.6,
    ),
    "th": VocabLang(
        code="th", name="Thai", vi_name="Tiếng Thái", scripts=("thai",), spaced=False,
        headword_rules=(
            "Each item is a common Thai word or short expression written in Thai script (no romanisation, no spaces inside a word, "
            "no proper nouns, no duplicates)."
        ),
        reading_kind="romanization",
        reading_instruction="RTGS romanization of the Thai word in lowercase Latin letters, e.g. \"sawatdi\". If unsure return \"\".",
        example_length="8-24 characters (Thai is written without spaces between words)",
        token_factor=1.7,
    ),
}

LEARNABLE_CODES = tuple(LANGS.keys())

# Mục đích học gắn với kỳ thi tiếng Anh: không áp dụng cho ngôn ngữ khác.
ENGLISH_ONLY_PURPOSES = ("ielts", "toeic")


def get_lang(code: Optional[str]) -> VocabLang:
    """Cấu hình của ngôn ngữ; mã lạ/rỗng rơi về tiếng Anh (hành vi cũ của tính năng)."""
    return LANGS.get((code or "en").strip().lower()[:2], LANGS["en"])


def strip_article(lang: VocabLang, term: str) -> str:
    """Bỏ mạo từ đứng đầu (der/die/das, le/la/l', el/la...): 'der Hund' -> 'Hund'. Ngôn ngữ không có mạo từ: giữ nguyên."""
    text = unicodedata.normalize("NFC", str(term or "")).strip()
    pattern = lang.article_pattern
    if not pattern:
        return text
    stripped = pattern.sub("", text, count=1).strip()
    return stripped or text


def _script_of(ch: str) -> Optional[str]:
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return None
    if name.startswith("KATAKANA-HIRAGANA"):  # dấu kéo dài ー
        return "kana"
    for script, prefixes in _SCRIPT_PREFIXES.items():
        if name.startswith(prefixes):
            return script
    return None


_ALLOWED_PUNCT = set(" -'’/.·")


def is_valid_term(lang: VocabLang, term: str) -> bool:
    """
    Từ/cụm từ hợp lệ cho `lang`: 1-60 ký tự, chỉ gồm chữ cái, dấu kết hợp, khoảng trắng và - ' ’ / . ·;
    có ít nhất một chữ cái và MỌI chữ cái thuộc hệ chữ của ngôn ngữ (từ Đức không được chứa chữ Hán/Cyrillic...).
    Lưu ý: không phát hiện được từ Latin sai ngôn ngữ (từ tiếng Anh trong bộ thẻ tiếng Đức) - việc đó thuộc bước kiểm duyệt bằng LLM.
    """
    text = unicodedata.normalize("NFC", str(term or "")).strip()
    if not 1 <= len(text) <= 60:
        return False
    letters = 0
    for ch in text:
        category = unicodedata.category(ch)
        if category[0] == "M":  # dấu kết hợp (dấu thanh Thái, dấu Latin)
            continue
        if category[0] == "L":
            letters += 1
            if _script_of(ch) not in lang.scripts:
                return False
            continue
        if ch in _ALLOWED_PUNCT:
            continue
        return False
    if letters == 0:
        return False
    # Từ phải bắt đầu bằng chữ cái và kết thúc bằng chữ cái (hoặc dấu chấm của từ viết tắt).
    last = text[-1]
    return unicodedata.category(text[0])[0] == "L" and (last == "." or unicodedata.category(last)[0] in ("L", "M"))


# =============================================================================== phiên âm
_PINYIN = re.compile(r"^[A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜüÜ\s'’\-]+$")
_ROMAN = re.compile(r"^[A-Za-zāīūēō\s'’\-]+$")
_KANA_ROMAJI = re.compile(r"^[ぁ-ゟ゠-ヿー・\s·A-Za-zāīūēōĀĪŪĒŌ'’\-()]+$")


def normalize_reading(lang: VocabLang, value: Optional[str], term: Optional[str] = None) -> str:
    """
    Chuẩn hóa phiên âm theo ngôn ngữ; trả chuỗi rỗng nếu thiếu/không hợp lệ.
    - ipa: do `normalization.normalize_ipa` kiểm tra (dạng /.../).
    - pinyin / romanization / kana_romaji: kiểm tra bảng chữ cho phép, độ dài, và không chép lại chính từ gốc.
    """
    from app.services.normalization import normalize_ipa  # tránh vòng import

    text = unicodedata.normalize("NFC", str(value or "")).strip()
    if not text:
        return ""
    if lang.reading_kind == "ipa":
        return normalize_ipa(text, strip_article(lang, term or "") or term)
    text = re.sub(r"\s+", " ", text)
    if len(text) > 60:
        return ""
    pattern = {"pinyin": _PINYIN, "romanization": _ROMAN, "kana_romaji": _KANA_ROMAJI}[lang.reading_kind]
    if not pattern.match(text):
        return ""
    if term and text.casefold() == str(term).strip().casefold():
        return ""  # chép lại chính từ gốc thay vì phiên âm
    return text


# =============================================================================== tìm từ khóa trong câu ví dụ
def term_pattern(lang: VocabLang, term: str) -> "re.Pattern[str]":
    """
    Regex tìm từ khóa (đã bỏ mạo từ) trong câu ví dụ, chịu biến hình thông thường.
    Ngôn ngữ có khoảng trắng: khớp phần gốc (bỏ tối đa 2 ký tự cuối) + hậu tố biến hình ngắn.
    Ngôn ngữ không có khoảng trắng (zh/ja/th) và tiếng Hàn: khớp chuỗi con; động từ ja/ko bỏ đuôi để bắt dạng chia (食べる -> 食べます, 먹다 -> 먹어요).
    """
    headword = strip_article(lang, term)
    if not headword:
        return re.compile(r"(?!x)x")
    if not lang.spaced or lang.code == "ko":
        stem = headword
        if lang.code == "ko" and len(stem) >= 2 and stem.endswith("다"):
            stem = stem[:-1]
        elif lang.code == "ja" and len(stem) >= 2 and stem[-1] in "るいうくぐすつぬぶむ":
            stem = stem[:-1]
        return re.compile(re.escape(stem))
    tokens = [t for t in re.split(r"\s+", headword) if t]
    first = tokens[0]
    cut = 2 if len(first) >= 6 else (1 if len(first) >= 4 else 0)
    stem = first[: len(first) - cut] if cut else first
    first_pattern = re.escape(stem) + (r"\w{0,8}" if cut else r"\w{0,3}")
    parts = [first_pattern] + [re.escape(t) for t in tokens[1:]]
    return re.compile(r"(?<!\w)" + r"\s+".join(parts) + r"(?!\w)", re.IGNORECASE)


def find_term(lang: VocabLang, sentence: Optional[str], term: str) -> Optional["re.Match[str]"]:
    if not sentence or not term:
        return None
    return term_pattern(lang, term).search(sentence)
