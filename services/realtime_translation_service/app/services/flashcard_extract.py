"""Trích xuất thông tin thẻ từ vựng: prompt theo ngôn ngữ nguồn và chuẩn hóa kết quả LLM (hàm thuần, dễ kiểm thử)."""
from typing import Any, Dict, Optional

# Ngôn ngữ nguồn có thể học (tiếng Việt là ngôn ngữ giải nghĩa nên không nằm trong danh sách này).
LEARNABLE = ("en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th")

LANGUAGE_NAMES = {
    "en": "English", "de": "German", "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
    "fr": "French", "es": "Spanish", "ru": "Russian", "th": "Thai", "vi": "Vietnamese",
}

# Quy ước phiên âm theo từng ngôn ngữ (IPA không phù hợp để người học tiếng Trung/Nhật/Hàn/Thái đọc nhanh).
PHONETIC_RULES = {
    "en": "standard IPA with stress marks, between slashes (e.g. /əˈsɪŋkrənəs/)",
    "de": "standard IPA with stress marks, between slashes (e.g. /ˈkʁaŋkn̩ˌhaʊ̯s/)",
    "fr": "standard IPA between slashes (e.g. /bɔ̃.ʒuʁ/)",
    "es": "standard IPA between slashes (e.g. /ˈbwe.nos ˈdi.as/)",
    "ru": "IPA between slashes, marking the stressed syllable (e.g. /ˈdobrəjə ˈutrə/)",
    "zh": "Hanyu Pinyin with tone marks (e.g. zǎo shang hǎo)",
    "ja": "Hepburn romaji (e.g. ohayō gozaimasu)",
    "ko": "Revised Romanization of Korean (e.g. joeun achim)",
    "th": "RTGS Thai romanization (e.g. sawatdi tonchao)",
}


def clean_lang(code: Optional[str]) -> Optional[str]:
    """Mã ngôn ngữ hợp lệ để học, hoặc None (không đoán, không nhận 'auto')."""
    value = (code or "").strip().lower()[:2]
    return value if value in LEARNABLE else None


def build_prompt(word: str, context: str, domain: str = "", source_lang: Optional[str] = None) -> tuple[str, str]:
    """(system_prompt, user_prompt). Không có source_lang -> giữ hành vi cũ (tương thích ngược)."""
    lang = clean_lang(source_lang)
    if not lang:
        system = (
            "You are an expert lexicographer and linguist. Extract vocabulary info. "
            "For English and German words, provide an exact standard IPA phonetic transcription including primary/secondary stress marks "
            "(e.g. /əˈsɪŋkrənəs/ or /ˈkʁaŋkn̩ˌhaʊ̯s/). "
            "Return EXACT JSON with keys: word, phonetic, part_of_speech, meaning. No extra text."
        )
        return system, f"Word: '{word}'. Context: '{context}'. Domain: '{domain}'."

    name = LANGUAGE_NAMES[lang]
    system = (
        f"You are an expert lexicographer of {name} writing flashcards for Vietnamese learners. "
        f"The headword is in {name}. "
        f"'meaning' MUST be a concise Vietnamese definition/translation of the headword as used in the given context. "
        f"'phonetic' MUST be {PHONETIC_RULES[lang]}. "
        f"'part_of_speech' is a short lowercase English label (noun, verb, adjective, adverb, phrase, ...). "
        f"'example' is ONE short natural {name} sentence using the headword, and 'example_translation' is its Vietnamese translation. "
        "Never invent facts: use an empty string for any field you are not sure about. "
        "Return EXACT JSON with keys: word, phonetic, part_of_speech, meaning, example, example_translation. No extra text."
    )
    return system, f"Word: '{word}'. Context: '{context}'. Domain: '{domain}'."


def normalize_result(raw: Any, word: str) -> Dict[str, str]:
    """Đảm bảo luôn đủ khóa, kiểu chuỗi; bỏ qua khóa lạ."""
    data = raw if isinstance(raw, dict) else {}
    out: Dict[str, str] = {}
    for key in ("word", "phonetic", "part_of_speech", "meaning", "example", "example_translation"):
        value = data.get(key)
        out[key] = value.strip() if isinstance(value, str) else ""
    out["word"] = out["word"] or word
    return out
