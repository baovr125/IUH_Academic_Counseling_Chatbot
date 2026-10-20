"""Chuẩn hóa dữ liệu từ vựng dùng chung cho import Excel và sinh từ bằng AI."""
import re
import unicodedata
from typing import Optional

# Từ loại chuẩn của hệ thống.
CANONICAL_POS = (
    "noun", "verb", "adjective", "adverb", "preposition", "conjunction",
    "pronoun", "determiner", "interjection", "phrasal verb", "idiom", "phrase",
)

_POS_ALIASES = {
    "noun": "noun", "n": "noun", "danh từ": "noun", "danh tu": "noun", "nomen": "noun",
    "verb": "verb", "v": "verb", "động từ": "verb", "dong tu": "verb",
    "adjective": "adjective", "adj": "adjective", "a": "adjective", "tính từ": "adjective", "tinh tu": "adjective",
    "adverb": "adverb", "adv": "adverb", "trạng từ": "adverb", "trang tu": "adverb", "phó từ": "adverb",
    "preposition": "preposition", "prep": "preposition", "giới từ": "preposition", "gioi tu": "preposition",
    "conjunction": "conjunction", "conj": "conjunction", "liên từ": "conjunction", "lien tu": "conjunction",
    "pronoun": "pronoun", "pron": "pronoun", "đại từ": "pronoun", "dai tu": "pronoun",
    "determiner": "determiner", "det": "determiner", "article": "determiner", "mạo từ": "determiner",
    "interjection": "interjection", "interj": "interjection", "exclamation": "interjection", "thán từ": "interjection",
    "phrasal verb": "phrasal verb", "phrasal-verb": "phrasal verb", "cụm động từ": "phrasal verb",
    "idiom": "idiom", "thành ngữ": "idiom",
    "phrase": "phrase", "phr": "phrase", "cụm từ": "phrase", "cum tu": "phrase", "collocation": "phrase",
}


def normalize_pos(raw: Optional[str]) -> Optional[str]:
    """Đưa từ loại về dạng chuẩn. Trả None nếu không nhận ra (để nơi gọi tự quyết định mặc định)."""
    if not raw:
        return None
    key = re.sub(r"[.\s]+$", "", str(raw).strip().lower())
    key = re.sub(r"\s+", " ", key)
    return _POS_ALIASES.get(key)


def dedupe_key(term: str) -> str:
    """Khóa chống trùng: NFC + casefold + gộp khoảng trắng (không bỏ dấu để không gộp nhầm từ khác nghĩa)."""
    text = unicodedata.normalize("NFC", str(term or "")).strip().casefold()
    return re.sub(r"\s+", " ", text)


def clean_text(value: Optional[str], max_len: int) -> str:
    """NFC, bỏ ký tự điều khiển, gộp khoảng trắng và cắt theo độ dài tối đa."""
    text = unicodedata.normalize("NFC", str(value or ""))
    text = re.sub(r"[\t\r\n ]", " ", text)  # tab/xuống dòng là khoảng trắng, không phải ký tự để xóa
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def term_regex(term: str) -> "re.Pattern[str]":
    """
    Regex tìm `term` trong câu ví dụ, chịu được biến thể hình thái thường gặp
    (pollute -> polluted/pollution, run -> running). Cụm nhiều từ: chỉ từ đầu được phép biến hình.
    """
    tokens = [t for t in re.split(r"\s+", str(term or "").strip()) if t]
    if not tokens:
        return re.compile(r"(?!x)x")  # không khớp gì
    first = tokens[0]
    if len(first) >= 6:
        # Từ dài: cắt 2 ký tự cuối rồi cho phép hậu tố tới 6 ký tự (pollute -> polluted/pollution).
        first_pattern = re.escape(first[:-2]) + r"\w{0,6}"
    else:
        # Từ ngắn: chỉ chấp nhận hậu tố biến hình quen thuộc để "cat" không khớp "cathedral" (run -> running, use -> using).
        suffix = r"(?:[a-z]?(?:s|es|ed|d|ing|er|ers|est|ly|ies|ied|ion|ions))"
        first_pattern = re.escape(first) + suffix + "?"
        if len(first) >= 3 and first[-1] in "ey":
            first_pattern = f"(?:{first_pattern}|{re.escape(first[:-1])}{suffix})"
    parts = [first_pattern] + [re.escape(t) for t in tokens[1:]]
    return re.compile(r"(?<!\w)" + r"\s+".join(parts) + r"(?!\w)", re.IGNORECASE)


def find_term_in_sentence(sentence: Optional[str], term: str) -> Optional["re.Match[str]"]:
    if not sentence or not term:
        return None
    return term_regex(term).search(sentence)


def build_cloze(sentence: Optional[str], term: str, blank: str = "________") -> Optional[str]:
    """Câu đục lỗ: thay từ khóa (kể cả dạng biến hình) bằng chỗ trống. None nếu không tìm thấy từ trong câu."""
    match = find_term_in_sentence(sentence, term)
    if not match:
        return None
    return sentence[:match.start()] + blank + sentence[match.end():]


# Ký tự cho phép trong phiên âm IPA: chữ Latin, æ ð ŋ ç ø œ, Greek θ β χ (tiếng Anh, Đức, Pháp, Tây Ban Nha), khối IPA
# Extensions (U+0250-02AF), modifier letters (U+02B0-02FF), dấu kết hợp (U+0300-036F), dấu trọng âm/độ dài, ngoặc, dấu cách.
_IPA_ALLOWED = re.compile(
    "^[A-Za-zæðŋçøœθβχɐ-ʯʰ-˿̀-ͯᴀ-ᶿᵻ\s.()\[\]/'\-]+$"
)
# Chữ cái có dấu đặc trưng tiếng Việt (IPA không bao giờ chứa các ký tự này).
_VIETNAMESE_LETTERS = re.compile(
    "[àáảãạăằắẳẵặâầấẩẫậ"
    "èéẻẽẹêềếểễệìíỉĩị"
    "òóỏõọôồốổỗộơờớởỡợ"
    "ùúủũụưừứửữựỳýỷỹỵđ]",
    re.IGNORECASE,
)


def normalize_ipa(value: Optional[str], term: Optional[str] = None) -> str:
    """Trả IPA dạng /.../ nếu hợp lệ về cú pháp; trả chuỗi rỗng nếu thiếu, không hợp lệ hoặc chỉ là chính tả của từ."""
    text = unicodedata.normalize("NFC", str(value or "")).strip()
    if not text:
        return ""
    inner = text.strip("/[] ").replace("'", "ˈ")
    if not (1 <= len(inner) <= 60) or not _IPA_ALLOWED.match(inner) or _VIETNAMESE_LETTERS.search(inner):
        return ""
    if term and re.sub(r"[\s\-]", "", inner).casefold() == re.sub(r"[\s\-]", "", str(term)).casefold():
        return ""  # mô hình chép lại chính tả thay vì phiên âm
    return f"/{inner}/"
