"""Nhận diện ngôn ngữ nguồn cho Realtime Translation Service.

Một đường xử lý duy nhất cho /text, /stream và /detect:

    text ──► bóc HTML / làm sạch ──► script profile ──► (luật script chắc chắn)
                                                      └─► fastText top-k + Lingua
                                                          └─► fusion + bằng chứng tiếng Việt/marker
                                                              └─► meta-confidence đã hiệu chỉnh
                                                                  └─► detected | uncertain | unsupported | ...

Chính sách: chỉ `detected` mới được dịch. Các trạng thái còn lại yêu cầu người dùng
chọn ngôn ngữ nguồn (kèm danh sách ứng viên cho UI).
"""
import asyncio
import hashlib
import json
import math
import os
import re
import threading
import unicodedata
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, NavigableString
from lingua import Language, LanguageDetectorBuilder

from app.schemas.translation import DetectionCandidate, LanguageDetectionDetails
from app.services.fasttext_detector import _get_fasttext_model, fasttext_topk
from app.utils.logger import logger

SUPPORTED_CODES = ("en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th", "vi")

# Ngôn ngữ ngoài phạm vi nhưng dễ bị nhầm với ngôn ngữ hỗ trợ: đưa vào Lingua để
# nhận ra chúng thay vì ép vào 10 lớp (xem DETECT_LINGUA_OOS).
DEFAULT_LINGUA_OOS = (
    "it,pt,ro,ca,nl,da,sv,nb,id,ms,tl,pl,tr,uk,bg,cs,hu,el,ar,he,hi,fa,sr,hr,fi"
)

LANGUAGE_NAMES_VI = {
    "en": "tiếng Anh", "de": "tiếng Đức", "zh": "tiếng Trung", "ja": "tiếng Nhật",
    "ko": "tiếng Hàn", "fr": "tiếng Pháp", "es": "tiếng Tây Ban Nha", "ru": "tiếng Nga",
    "th": "tiếng Thái", "vi": "tiếng Việt", "it": "tiếng Ý", "pt": "tiếng Bồ Đào Nha",
    "ro": "tiếng Romania", "ca": "tiếng Catalan", "nl": "tiếng Hà Lan", "da": "tiếng Đan Mạch",
    "sv": "tiếng Thụy Điển", "nb": "tiếng Na Uy", "no": "tiếng Na Uy", "id": "tiếng Indonesia",
    "ms": "tiếng Mã Lai", "tl": "tiếng Tagalog", "pl": "tiếng Ba Lan", "tr": "tiếng Thổ Nhĩ Kỳ",
    "uk": "tiếng Ukraina", "bg": "tiếng Bulgaria", "cs": "tiếng Séc", "hu": "tiếng Hungary",
    "el": "tiếng Hy Lạp", "ar": "tiếng Ả Rập", "he": "tiếng Do Thái", "hi": "tiếng Hindi",
    "fa": "tiếng Ba Tư", "sr": "tiếng Serbia", "hr": "tiếng Croatia", "fi": "tiếng Phần Lan",
}

MESSAGE_UNCERTAIN = "Chưa đủ thông tin để xác định chắc chắn ngôn ngữ. Hãy chọn ngôn ngữ nguồn thủ công."
MESSAGE_EMPTY = "Vui lòng nhập văn bản để nhận diện ngôn ngữ."
MESSAGE_NO_LETTERS = "Vui lòng nhập văn bản chứa ký tự chữ để nhận diện ngôn ngữ."
MESSAGE_URL = "Văn bản liên kết (URL) không phải ngôn ngữ tự nhiên hợp lệ."
MESSAGE_SYSTEM = "Không thể nhận diện ngôn ngữ lúc này. Vui lòng thử lại hoặc chọn ngôn ngữ nguồn thủ công."

STATUS_ERROR_CODES = {
    "uncertain": ("LANG_UNCERTAIN", 400),
    "unsupported": ("LANG_UNSUPPORTED", 400),
    "unknown": ("LANG_UNKNOWN", 400),
    "invalid_input": ("INVALID_INPUT", 400),
    "system_error": ("LANG_SYSTEM_ERROR", 503),
}


# ---------------------------------------------------------------------------
# Cấu hình & hiệu chỉnh
# ---------------------------------------------------------------------------
def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class DetectionConfig:
    min_confidence: float = 0.30       # p1 tối thiểu của phân phối hợp nhất để được `detected`
    min_margin: float = 0.12           # p1 - p2 tối thiểu
    oos_min_margin: float = 0.50       # khối OOS phải vượt ngôn ngữ hỗ trợ tốt nhất ít nhất ngần này
    # Nếu ≥ outside_mass_block xác suất nằm NGOÀI tập ngôn ngữ hỗ trợ mà nhãn top-1 chưa tới
    # outside_p1_cap thì không kết luận `detected` (thường là ngôn ngữ họ hàng như sv/da/nl, bg/uk).
    outside_mass_block: float = 0.40
    outside_p1_cap: float = 0.60
    ft_skip_threshold: float = 0.90    # fastText đủ chắc → bỏ qua Lingua (nếu text đủ dài)
    always_crosscheck: bool = False    # luôn chạy Lingua để kiểm chứng chéo
    short_units_spaced: int = 3        # < N từ (script có dấu cách) = ngắn
    short_units_cjk: int = 4           # < N ký tự (CJK/Thai) = ngắn
    max_chars: int = 2000              # giới hạn độ dài đưa vào engine
    use_markers: bool = True
    hint_min_prob: float = 0.15        # xác suất tối thiểu để chấp nhận gợi ý (và gợi ý phải nằm trong top-2)
    cache_size: int = 2048
    lingua_oos: tuple = ()
    lingua_low_accuracy: bool = True
    calibration_file: str = ""

    @classmethod
    def from_env(cls) -> "DetectionConfig":
        oos = os.getenv("DETECT_LINGUA_OOS", DEFAULT_LINGUA_OOS)
        service_root = Path(__file__).resolve().parents[2]
        return cls(
            min_confidence=_env_float("DETECT_MIN_CONFIDENCE", 0.30),
            min_margin=_env_float("DETECT_MIN_MARGIN", 0.12),
            oos_min_margin=_env_float("DETECT_OOS_MIN_MARGIN", 0.50),
            outside_mass_block=_env_float("DETECT_OUTSIDE_MASS_BLOCK", 0.40),
            outside_p1_cap=_env_float("DETECT_OUTSIDE_P1_CAP", 0.60),
            ft_skip_threshold=_env_float("DETECT_FAST_THRESHOLD", 0.90),
            always_crosscheck=os.getenv("DETECT_ALWAYS_CROSSCHECK", "0") == "1",
            short_units_spaced=_env_int("DETECT_SHORT_UNITS", 3),
            short_units_cjk=_env_int("DETECT_SHORT_UNITS_CJK", 4),
            max_chars=_env_int("DETECT_MAX_CHARS", 2000),
            use_markers=os.getenv("DETECT_USE_MARKERS", "1") == "1",
            hint_min_prob=_env_float("DETECT_HINT_MIN_PROB", 0.15),
            cache_size=_env_int("DETECT_CACHE_SIZE", 2048),
            lingua_oos=tuple(c.strip().lower() for c in oos.split(",") if c.strip()),
            lingua_low_accuracy=os.getenv("DETECT_LINGUA_LOW_ACCURACY", "1") == "1",
            calibration_file=os.getenv(
                "DETECT_CALIBRATION_FILE", str(service_root / "models" / "detect_calibration.json")
            ),
        )


FEATURE_NAMES = ("p1", "margin", "agree", "short", "purity", "length", "support")


@dataclass
class Calibration:
    """Meta-confidence: sigmoid(bias + Σ coef·feature) ≈ P(nhãn top-1 đúng).

    Đặc trưng (đều trong [0, 1]):
      p1       xác suất hợp nhất của nhãn top-1 (với ngôn ngữ ngoài phạm vi: tổng khối xác suất OOS)
      margin   p1 trừ xác suất của đối thủ gần nhất
      agree    fastText và Lingua cùng nhãn (1), khác nhãn (0), chỉ có một engine (0.5)
      short    văn bản ngắn
      purity   tỉ lệ hệ chữ viết chủ đạo
      length   độ dài hiệu dụng đã chuẩn hóa
      support  bằng chứng độc lập ủng hộ top-1 (tiếng Việt không dấu/có dấu, marker)
    """
    bias: float = -4.0
    coef: dict = field(default_factory=lambda: {
        "p1": 3.5, "margin": 2.0, "agree": 1.5, "short": -0.8, "purity": 1.0, "length": 0.8, "support": 1.5,
    })
    # Ngưỡng meta-confidence để trả `detected` theo độ dài.
    thresholds: dict = field(default_factory=lambda: {"short": 0.93, "medium": 0.90, "long": 0.85})
    # Ngưỡng để kết luận `unsupported` (chặt hơn cho văn bản ngắn vì dễ trùng giữa các ngôn ngữ gần nhau).
    unsupported_thresholds: dict = field(default_factory=lambda: {"short": 0.97, "medium": 0.92, "long": 0.88})
    version: str = "default"

    def unsupported_threshold_for(self, bucket: str) -> float:
        return self.unsupported_thresholds.get(bucket, 0.92)

    @classmethod
    def load(cls, path: str) -> "Calibration":
        cal = cls()
        if not path or not os.path.exists(path):
            return cal
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if tuple(data.get("features", FEATURE_NAMES)) != FEATURE_NAMES:
                logger.warning("Detection calibration feature mismatch; using defaults.")
                return cal
            cal.bias = float(data["bias"])
            cal.coef = {k: float(v) for k, v in data["coef"].items()}
            cal.thresholds = {k: float(v) for k, v in data["thresholds"].items()}
            if "unsupported_thresholds" in data:
                cal.unsupported_thresholds = {k: float(v) for k, v in data["unsupported_thresholds"].items()}
            cal.version = str(data.get("version", "file"))
        except Exception as exc:  # noqa: BLE001 - cấu hình hỏng không được làm sập service
            logger.warning(f"Failed to load detection calibration ({exc}); using defaults.")
            return cls()
        return cal

    def meta(self, features: dict) -> float:
        z = self.bias + sum(self.coef.get(name, 0.0) * features.get(name, 0.0) for name in FEATURE_NAMES)
        return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


_config: Optional[DetectionConfig] = None
_calibration: Optional[Calibration] = None
_state_lock = threading.Lock()


def get_config() -> DetectionConfig:
    global _config
    if _config is None:
        with _state_lock:
            if _config is None:
                _config = DetectionConfig.from_env()
    return _config


def get_calibration() -> Calibration:
    global _calibration
    if _calibration is None:
        with _state_lock:
            if _calibration is None:
                _calibration = Calibration.load(get_config().calibration_file)
    return _calibration


def reload_config(reset_engines: bool = False) -> None:
    """Đọc lại env/calibration và xóa cache kết quả (dùng trong test và công cụ hiệu chỉnh).

    Engine Lingua (nạp model mất ~0,5 s) chỉ được dựng lại khi `reset_engines=True`,
    ví dụ khi đổi `DETECT_LINGUA_OOS`.
    """
    global _config, _calibration, _lingua
    with _state_lock:
        _config = None
        _calibration = None
        if reset_engines:
            _lingua = None
    with _cache_lock:
        _result_cache.clear()


# ---------------------------------------------------------------------------
# Script (hệ chữ viết)
# ---------------------------------------------------------------------------
LATIN, CYRILLIC, HAN, KANA, HANGUL, THAI = "latin", "cyrillic", "han", "kana", "hangul", "thai"
UNSUPPORTED_SCRIPTS = {"greek", "hebrew", "arabic", "indic", "other"}


def _script_of(cp: int) -> str:
    if cp < 0x250 or 0x1E00 <= cp <= 0x1EFF or 0x2C60 <= cp <= 0x2C7F or 0xA720 <= cp <= 0xA7FF \
            or 0xFF21 <= cp <= 0xFF5A:
        return LATIN
    if 0x370 <= cp <= 0x3FF or 0x1F00 <= cp <= 0x1FFF:
        return "greek"
    if 0x400 <= cp <= 0x52F or 0x2DE0 <= cp <= 0x2DFF or 0xA640 <= cp <= 0xA69F:
        return CYRILLIC
    if 0x590 <= cp <= 0x5FF:
        return "hebrew"
    if 0x600 <= cp <= 0x6FF or 0x750 <= cp <= 0x77F or 0x8A0 <= cp <= 0x8FF or 0xFB50 <= cp <= 0xFDFF \
            or 0xFE70 <= cp <= 0xFEFF:
        return "arabic"
    if 0x900 <= cp <= 0xDFF:
        return "indic"
    if 0xE00 <= cp <= 0xE7F:
        return THAI
    if 0x1100 <= cp <= 0x11FF or 0x3130 <= cp <= 0x318F or 0xAC00 <= cp <= 0xD7AF or 0xA960 <= cp <= 0xA97F \
            or 0xFFA0 <= cp <= 0xFFDC:
        return HANGUL
    if 0x3040 <= cp <= 0x30FF or 0x31F0 <= cp <= 0x31FF or 0xFF66 <= cp <= 0xFF9F:
        return KANA
    if 0x3400 <= cp <= 0x4DBF or 0x4E00 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF or 0x20000 <= cp <= 0x2FA1F:
        return HAN
    return "other"


def _is_vi_mark(ch: str, cp: int) -> bool:
    """Ký tự đặc trưng tiếng Việt (ă đ ơ ư và các nguyên âm mang dấu thanh ở khối Latin Extended Additional)."""
    return 0x1EA0 <= cp <= 0x1EF9 or ch in "ăĂđĐơƠưƯ"


@dataclass
class ScriptProfile:
    counts: dict
    letters: int
    dominant: str
    share: float
    eff_len: int
    vi_marks: int

    @property
    def cjk_like(self) -> bool:
        return self.dominant in (HAN, KANA, HANGUL, THAI)


def _profile(text: str) -> ScriptProfile:
    counts: dict = defaultdict(int)
    vi_marks = 0
    letters = 0
    for ch in text:
        if not ch.isalpha():
            continue
        cp = ord(ch)
        letters += 1
        counts[_script_of(cp)] += 1
        if _is_vi_mark(ch, cp):
            vi_marks += 1
    if letters == 0:
        return ScriptProfile({}, 0, "none", 0.0, 0, 0)
    dominant, top = max(counts.items(), key=lambda kv: kv[1])
    # Han + Kana được xem là cùng "hệ chữ Nhật/Trung" khi tính độ dài hiệu dụng.
    if dominant in (HAN, KANA, HANGUL, THAI):
        eff_len = counts[HAN] + counts[KANA] + counts[HANGUL] + counts[THAI]
    else:
        eff_len = sum(1 for tok in re.findall(r"\w+", text) if any(c.isalpha() for c in tok))
    return ScriptProfile(dict(counts), letters, dominant, top / letters, eff_len, vi_marks)


# ---------------------------------------------------------------------------
# Bóc HTML & làm sạch
# ---------------------------------------------------------------------------
# Mọi regex dưới đây dùng lượng từ có giới hạn để thời gian chạy tuyến tính theo độ dài đầu vào
# (tránh ReDoS bậc hai trên chuỗi dài không có khoảng trắng hoặc có nhiều ký tự '<').
_HTML_HINT = re.compile(r"<[a-zA-Z!/][^>]{0,500}>|&[a-zA-Z#0-9]{1,10};")
_HTML_STRIP = re.compile(r"<[^>]{0,500}>")
_PROTECTED_TAGS = {"script", "style", "code", "pre"}
_URL_RE = re.compile(r"(?:https?://|www\.)\S{1,2000}", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,5}")
_MENTION_RE = re.compile(r"(?<![\w])@\w{1,64}")
_HASH_RE = re.compile(r"#(?=\w)")
MAX_RAW_CHARS = 60_000  # lớp phòng thủ thứ hai trước khi bóc HTML; schema API đã giới hạn 1.000–3.000 ký tự


def _cap_raw(text: str) -> str:
    if len(text) <= MAX_RAW_CHARS:
        return text
    head = int(MAX_RAW_CHARS * 0.6)
    return text[:head] + " " + text[-(MAX_RAW_CHARS - head):]


def _extract_visible_text(text: str) -> str:
    if not _HTML_HINT.search(text):
        return text
    try:
        soup = BeautifulSoup(text, "html.parser")
        parts = []
        for node in soup.find_all(string=True):
            if type(node) is not NavigableString:  # bỏ comment, doctype, CDATA...
                continue
            parent = node.parent
            if parent is not None and parent.name in _PROTECTED_TAGS:
                continue
            piece = str(node).strip()
            if piece:
                parts.append(piece)
        return " ".join(parts)
    except Exception:  # noqa: BLE001 - gồm RecursionError với HTML lồng quá sâu
        return _HTML_STRIP.sub(" ", text)


def _clean_for_detection(text: str, max_chars: int) -> str:
    cleaned = _URL_RE.sub(" ", text)
    cleaned = _EMAIL_RE.sub(" ", cleaned)
    cleaned = _MENTION_RE.sub(" ", cleaned)
    cleaned = _HASH_RE.sub("", cleaned)
    cleaned = unicodedata.normalize("NFC", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_chars:
        head = int(max_chars * 0.6)
        cleaned = cleaned[:head] + " " + cleaned[-(max_chars - head):]
    return cleaned


# ---------------------------------------------------------------------------
# Engine: Lingua (mở rộng ngôn ngữ ngoài phạm vi) & fastText
# ---------------------------------------------------------------------------
_lingua = None
_lingua_codes: dict = {}
_lingua_lock = threading.Lock()


def _get_lingua():
    global _lingua, _lingua_codes
    if _lingua is not None:
        return _lingua, _lingua_codes
    with _lingua_lock:
        if _lingua is None:
            by_code = {lang.iso_code_639_1.name.lower(): lang for lang in Language.all()}
            wanted = list(SUPPORTED_CODES) + [c for c in get_config().lingua_oos if c not in SUPPORTED_CODES]
            languages = [by_code[c] for c in wanted if c in by_code]
            builder = LanguageDetectorBuilder.from_languages(*languages)
            if get_config().lingua_low_accuracy:
                builder = builder.with_low_accuracy_mode()  # ít RAM hơn nhiều, kém chính xác hơn ở văn bản ngắn
            detector = builder.with_preloaded_language_models().build()
            _lingua_codes = {lang: lang.iso_code_639_1.name.lower() for lang in languages}
            _lingua = detector
    return _lingua, _lingua_codes


def _lingua_distribution(text: str) -> dict:
    detector, codes = _get_lingua()
    values = detector.compute_language_confidence_values(text)
    dist = {codes[v.language]: float(v.value) for v in values if v.value > 0}
    return dist


# ---------------------------------------------------------------------------
# Bằng chứng bổ sung: tiếng Việt không dấu & marker
# ---------------------------------------------------------------------------
# Âm tiết/từ tiếng Việt viết không dấu, đặc trưng và ít trùng với tiếng Anh/Pháp/Tây Ban Nha/Đức.
VI_TONELESS_WORDS = frozenset("""
khong duoc nhung nguoi truong hoc giup kiem thay giao viet dang nhu nao cung voi cua cac ngay thang
tinh lap trinh toi minh chung nhieu xin sinh vien bai tap truoc nop thi biet hieu nha nhat thoi gian
phong khoa sach quyen dep tot lam gioi giai thich hoi loi nuoc banh ngon nong lanh troi nang cho trong
tuan phut duoi khi nhe nhi thuc nghiep cong viec tieng
""".split())
VI_TONELESS_PHRASES = ("xin chao", "cam on", "xin loi", "tam biet", "chuc mung", "khong sao", "da vang",
                       "vang a", "chao ban", "chao em", "chao anh")

# Marker chỉ dùng để phân giải giữa các ngôn ngữ Latin đã nằm trong top ứng viên;
# cần >= 2 marker khác nhau và không bao giờ ghi đè top-1 tự tin.
LANGUAGE_MARKERS = {
    "de": frozenset({"und", "nicht", "ich", "ist", "eine", "einen", "mit", "für", "wir", "sind",
                     "aber", "auch", "dem", "zum", "zur", "über", "nach", "oder", "wenn", "noch",
                     "bin", "habe", "sein", "das", "ein"}),
    "fr": frozenset({"est", "sont", "dans", "avec", "pour", "vous", "nous", "les", "des", "une",
                     "qui", "pas", "très", "mais", "comme", "cette", "aussi", "être", "je", "suis",
                     "elle", "ne", "au", "aux", "du", "sur", "par", "plus", "bien"}),
    "es": frozenset({"los", "las", "está", "están", "pero", "para", "por", "también", "más", "una",
                     "este", "esta", "puede", "tiene", "hacer", "yo", "estoy", "nosotros", "muy",
                     "del", "con", "soy", "aquí", "el", "como"}),
}
# Từ trùng với tiếng Anh/ngôn ngữ khác trong các list trên chỉ có giá trị khi đi cùng ≥2 marker.
MARKER_BOOST_PER_HIT = 0.12
MARKER_BOOST_CAP = 0.30


_vi_lexicon_cache: Optional[frozenset] = None


def _vi_lexicon() -> frozenset:
    """Từ vựng âm tiết tiếng Việt không dấu (sinh bởi scripts/build_vi_lexicon.py) + danh sách tay."""
    global _vi_lexicon_cache
    if _vi_lexicon_cache is None:
        words = set(VI_TONELESS_WORDS)
        path = Path(__file__).resolve().parents[1] / "resources" / "vi_toneless_syllables.txt"
        try:
            with open(path, "r", encoding="utf-8") as handle:
                words.update(line.strip() for line in handle if line.strip())
        except OSError:
            logger.warning("Vietnamese toneless lexicon not found; using the built-in short list.")
        _vi_lexicon_cache = frozenset(words)
    return _vi_lexicon_cache


def _vi_evidence(text: str, profile: ScriptProfile) -> tuple[float, str]:
    """Trả về (sức mạnh bằng chứng tiếng Việt trong [0, 0.95], loại: "marks" | "toneless" | "")."""
    if profile.dominant != LATIN or profile.letters == 0:
        return 0.0, ""
    if profile.vi_marks > 0:
        ratio = profile.vi_marks / profile.letters
        return min(0.95, 0.45 + 3.0 * ratio + 0.1 * min(profile.vi_marks, 5)), "marks"
    lowered = text.casefold()
    tokens = re.findall(r"[a-z]+", lowered)
    if not tokens:
        return 0.0, ""
    lexicon = _vi_lexicon()
    hits = sum(1 for tok in tokens if tok in lexicon)
    phrase_hits = sum(1 for phrase in VI_TONELESS_PHRASES if phrase in lowered)
    ratio = min(1.0, (hits + 2 * phrase_hits) / len(tokens))
    enough_hits = hits >= 3 or (hits >= 2 and len(tokens) <= 4) or phrase_hits > 0
    if enough_hits and ratio >= 0.4:
        return min(0.9, 0.25 + 0.9 * ratio), "toneless"
    return 0.0, ""


def _marker_hits(text: str) -> dict:
    words = set(re.findall(r"\w+", text.casefold()))
    return {lang: len(words & markers) for lang, markers in LANGUAGE_MARKERS.items()}


# ---------------------------------------------------------------------------
# Kết quả trung gian & phân tích
# ---------------------------------------------------------------------------
@dataclass
class Analysis:
    early: Optional[LanguageDetectionDetails] = None
    dist: dict = field(default_factory=dict)
    top1: Optional[str] = None
    top2: Optional[str] = None
    p1: float = 0.0
    margin: float = 0.0
    features: dict = field(default_factory=dict)
    meta: float = 0.0
    bucket: str = "medium"
    engine: str = "none"
    ft_top: Optional[str] = None
    lg_top: Optional[str] = None
    profile: Optional[ScriptProfile] = None
    multilingual: bool = False


OTHER_LABEL = "?"


def _collapse_unknown_labels(ft: list, cfg: DetectionConfig) -> list:
    """Nhãn fastText ngoài dịch vụ và ngoài danh sách ngôn ngữ dễ nhầm được gộp thành "?".

    Nhãn hiếm (ilo, war, ceb...) trên văn bản ngắn/nhiễu không đủ tin cậy để kết luận
    `unsupported`; chúng chỉ làm giảm độ chắc chắn của nhãn top-1.
    """
    known = set(SUPPORTED_CODES) | set(cfg.lingua_oos)
    collapsed: dict = {}
    for code, p in ft:
        key = code if code in known else OTHER_LABEL
        collapsed[key] = collapsed.get(key, 0.0) + p
    return sorted(collapsed.items(), key=lambda kv: kv[1], reverse=True)


def _details(status: str, **kwargs) -> LanguageDetectionDetails:
    return LanguageDetectionDetails(status=status, **kwargs)


def _candidates(dist: dict, limit: int = 3) -> list:
    ranked = sorted(
        ((code, p) for code, p in dist.items() if code in SUPPORTED_CODES and p > 0.01),
        key=lambda kv: kv[1], reverse=True,
    )
    return [DetectionCandidate(language=code, confidence=round(p, 4)) for code, p in ranked[:limit]]


def _bucket(profile: ScriptProfile, cfg: DetectionConfig) -> tuple[str, bool]:
    short_limit = cfg.short_units_cjk if profile.cjk_like else cfg.short_units_spaced
    if profile.eff_len < short_limit:
        return "short", True
    medium_limit = 16 if profile.cjk_like else 8
    return ("medium" if profile.eff_len < medium_limit else "long"), False


def _script_shortcut(profile: ScriptProfile, ft: list, cfg: DetectionConfig) -> Optional[LanguageDetectionDetails]:
    """Luật chắc chắn dựa trên hệ chữ viết (Hangul/Kana/Thai) và hệ chữ không được hỗ trợ."""
    counts = profile.counts
    letters = profile.letters
    kana, hangul, thai, han = counts.get(KANA, 0), counts.get(HANGUL, 0), counts.get(THAI, 0), counts.get(HAN, 0)

    latin = counts.get(LATIN, 0)

    def decided(lang: str, share: float, units: int) -> LanguageDetectionDetails:
        """`share`: tỉ lệ chữ của hệ chữ đặc trưng trên tổng chữ cái; từ Latin xen vào (tên riêng,
        thuật ngữ như "YouTube") không làm mất kết luận miễn là hệ chữ đặc trưng chiếm ≥ 40%."""
        if units < 2:
            return _details("uncertain", engine="script", reason="short_input", message=MESSAGE_UNCERTAIN,
                            candidates=[DetectionCandidate(language=lang, confidence=0.5)])
        if share < 0.4:
            return _details("uncertain", engine="script", reason="mixed_language", message=MESSAGE_UNCERTAIN,
                            confidence=round(share * 0.5, 4),
                            candidates=[DetectionCandidate(language=lang, confidence=round(share, 4))],
                            is_multilingual=True)
        conf = round(min(0.99, 0.9 + 0.02 * units) * (0.6 + 0.4 * share), 4)
        return _details("detected", resolved_source_lang=lang, confidence=conf, margin=round(share, 4),
                        engine="script", candidates=[DetectionCandidate(language=lang, confidence=conf)],
                        is_multilingual=latin > 0 and share < 0.95)

    if profile.dominant in UNSUPPORTED_SCRIPTS and profile.share >= 0.5:
        ft_code = next((c for c, p in ft if c not in SUPPORTED_CODES and p >= 0.3), None)
        shown = ft_code or profile.dominant
        name = LANGUAGE_NAMES_VI.get(shown, shown)
        return _details(
            "unsupported", engine="script", confidence=round(profile.share, 4), margin=round(profile.share, 4),
            reason="script_mismatch", detected_language=shown,
            message=f"Ngôn ngữ nhận diện được ({name}) chưa được hỗ trợ. Hãy chọn ngôn ngữ nguồn thủ công.",
        )
    non_latin = letters - latin
    if hangul / letters >= 0.4 and hangul >= non_latin * 0.9:
        return decided("ko", hangul / letters, hangul)
    if kana > 0 and (kana + han) / letters >= 0.4 and (kana + han) >= non_latin * 0.9 \
            and (kana >= 2 or kana / (kana + han) >= 0.2):
        return decided("ja", (kana + han) / letters, kana + han)
    if thai / letters >= 0.4 and thai >= non_latin * 0.9:
        return decided("th", thai / letters, thai)
    return None


def _analyze(text: str, hint: Optional[str]) -> Analysis:
    cfg = get_config()
    cal = get_calibration()

    visible = _extract_visible_text(_cap_raw(text))
    if not visible.strip():
        return Analysis(early=_details("invalid_input", engine="none", message=MESSAGE_EMPTY))
    if not any(c.isalpha() for c in visible):
        return Analysis(early=_details("invalid_input", engine="none", message=MESSAGE_NO_LETTERS))

    cleaned = _clean_for_detection(visible, cfg.max_chars)
    if not any(c.isalpha() for c in cleaned):
        return Analysis(early=_details("unknown", engine="none", message=MESSAGE_URL))

    profile = _profile(cleaned)
    # Văn bản viết HOA toàn bộ làm lệch cả hai engine: đưa về chữ thường (chỉ cho hệ chữ có hoa/thường).
    engine_text = cleaned
    if profile.dominant in (LATIN, CYRILLIC) and cleaned.isupper():
        engine_text = cleaned.lower()
    ft = fasttext_topk(engine_text, k=5)
    ft = _collapse_unknown_labels(ft, cfg)

    shortcut = _script_shortcut(profile, ft, cfg)
    if shortcut is not None:
        return Analysis(early=shortcut, profile=profile)

    bucket, is_short = _bucket(profile, cfg)
    ft_top, ft_p1 = (ft[0] if ft else (None, 0.0))

    # Lingua: chạy khi fastText không đủ chắc, text ngắn, nhãn ngoài phạm vi hoặc fastText không khả dụng.
    run_lingua = (
        cfg.always_crosscheck
        or not ft
        or is_short
        or ft_top not in SUPPORTED_CODES
        or ft_p1 < cfg.ft_skip_threshold
        or profile.eff_len < 4
        or profile.share < 0.9
    )
    lg: dict = {}
    if run_lingua:
        try:
            lg = _lingua_distribution(engine_text)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Lingua detection failed: {type(exc).__name__}")
    if not ft and not lg:
        return Analysis(early=_details("system_error", engine="none", message=MESSAGE_SYSTEM))

    w_ft, w_lg = (0.45, 0.55) if is_short else (0.55, 0.45)
    dist: dict = defaultdict(float)
    if ft and lg:
        for code, p in ft:
            dist[code] += w_ft * p
        for code, p in lg.items():
            dist[code] += w_lg * p
        engine = "fusion"
    elif ft:
        for code, p in ft:
            dist[code] += p
        engine = "fasttext"
    else:
        for code, p in lg.items():
            dist[code] += p
        engine = "lingua"

    # Bằng chứng bổ sung (độc lập với hai engine)
    support_for: dict = {}
    vi_strength, vi_kind = _vi_evidence(cleaned, profile)
    if vi_strength > 0:
        dist["vi"] += (0.9 if vi_kind == "toneless" else 0.5) * vi_strength
        support_for["vi"] = vi_strength
    if profile.dominant == HAN and not profile.counts.get(KANA) and not profile.counts.get(HANGUL):
        # Hán tự thuần (không kana/hangul): văn bản tiếng Nhật gần như luôn có kana, nên ưu tiên zh.
        # Chuỗi đủ dài → gộp toàn bộ khối xác suất `ja` vào `zh` (fastText hay gán `ja` cho chữ phồn thể).
        dist["zh"] += 0.3
        if profile.eff_len >= 5 and "ja" in dist:
            dist["zh"] += dist.pop("ja")
    if cfg.use_markers and profile.dominant == LATIN:
        top_codes = {code for code, _ in sorted(dist.items(), key=lambda kv: kv[1], reverse=True)[:3]}
        for lang, count in _marker_hits(cleaned).items():
            if count >= 2 and lang in top_codes:
                dist[lang] += min(MARKER_BOOST_CAP, MARKER_BOOST_PER_HIT * count)
                support_for[lang] = max(support_for.get(lang, 0.0), min(0.9, 0.3 * count))

    total = sum(dist.values())
    if total <= 0:
        return Analysis(early=_details("unknown", engine=engine, reason="low_confidence",
                                       message=MESSAGE_UNCERTAIN), profile=profile)
    dist = {code: p / total for code, p in dist.items()}

    # Ngôn ngữ ngoài phạm vi được xử lý theo khối xác suất (id/ms, hr/sr... dễ lẫn nhau).
    oos_ranked = sorted(((c, p) for c, p in dist.items() if c not in SUPPORTED_CODES and c != OTHER_LABEL),
                        key=lambda kv: kv[1], reverse=True)
    sup_ranked = sorted(((c, p) for c, p in dist.items() if c in SUPPORTED_CODES),
                        key=lambda kv: kv[1], reverse=True)
    oos_mass = sum(p for _, p in oos_ranked)
    other_mass = dist.get(OTHER_LABEL, 0.0)
    best_sup_p = sup_ranked[0][1] if sup_ranked else 0.0
    if oos_ranked and oos_mass > max(best_sup_p, other_mass):
        top1, p1 = oos_ranked[0][0], oos_mass
        top2 = sup_ranked[0][0] if sup_ranked else None
        margin = oos_mass - max(best_sup_p, other_mass)
        group_oos = True
    elif other_mass > best_sup_p:
        top1, p1 = OTHER_LABEL, other_mass
        top2 = sup_ranked[0][0] if sup_ranked else None
        margin = other_mass - best_sup_p
        group_oos = False
    else:
        ranked = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
        top1, p1 = ranked[0]
        top2, p2 = ranked[1] if len(ranked) > 1 else (None, 0.0)
        margin = p1 - p2
        group_oos = False

    lg_top = max(lg.items(), key=lambda kv: kv[1])[0] if lg else None

    def _same(code: Optional[str]) -> bool:
        return code == top1 or (group_oos and code is not None and code not in SUPPORTED_CODES)

    if ft and lg:
        agree = 1.0 if (_same(ft_top) and _same(lg_top)) else 0.0
    else:
        agree = 0.5
    features = {
        "p1": p1,
        "margin": margin,
        "agree": agree,
        "short": 1.0 if is_short else 0.0,
        "purity": profile.share,
        "length": min(1.0, profile.eff_len / (40.0 if profile.cjk_like else 20.0)),
        "support": support_for.get(top1, 0.0),
    }
    return Analysis(
        dist=dist, top1=top1, top2=top2, p1=p1, margin=margin, features=features,
        meta=cal.meta(features), bucket=bucket, engine=engine, ft_top=ft_top, lg_top=lg_top,
        profile=profile, multilingual=profile.share < 0.85,
    )


def _finalize(analysis: Analysis, hint: Optional[str]) -> LanguageDetectionDetails:
    if analysis.early is not None:
        return analysis.early

    cfg = get_config()
    cal = get_calibration()
    top1, dist = analysis.top1, analysis.dist
    candidates = _candidates(dist)
    base = dict(
        confidence=round(analysis.meta, 4), margin=round(analysis.margin, 4), engine=analysis.engine,
        candidates=candidates, is_multilingual=analysis.multilingual,
    )

    def hinted() -> Optional[LanguageDetectionDetails]:
        """Gợi ý từ lần nhận diện trước: chỉ nhận khi nằm trong top-2 ngôn ngữ hỗ trợ và đủ xác suất.
        Chỉ được gọi khi kết luận chắc chắn đã không xảy ra, nên không bao giờ ghi đè bằng chứng mạnh."""
        if hint not in SUPPORTED_CODES or dist.get(hint, 0.0) < cfg.hint_min_prob:
            return None
        supported_top2 = [code for code, _ in sorted(
            ((c, p) for c, p in dist.items() if c in SUPPORTED_CODES), key=lambda kv: kv[1], reverse=True)[:2]]
        if hint not in supported_top2:
            return None
        return _details("detected", resolved_source_lang=hint, **{**base, "engine": "hint"})

    if top1 == OTHER_LABEL:
        return hinted() or _details("uncertain", reason="low_confidence", message=MESSAGE_UNCERTAIN, **base)

    if top1 not in SUPPORTED_CODES:
        # Ngôn ngữ ngoài phạm vi được nhận ra. Chỉ kết luận `unsupported` khi ngôn ngữ hỗ trợ tốt nhất
        # còn rất ít xác suất; nếu không (vd câu ngắn es/pt/it) thì để người dùng chọn.
        if (
            analysis.meta >= cal.unsupported_threshold_for(analysis.bucket)
            and analysis.p1 >= cfg.min_confidence
            and analysis.margin >= cfg.oos_min_margin
        ):
            name = LANGUAGE_NAMES_VI.get(top1, top1)
            return _details(
                "unsupported", reason="out_of_scope", detected_language=top1,
                message=f"Ngôn ngữ nhận diện được ({name}) chưa được hỗ trợ. Hãy chọn ngôn ngữ nguồn thủ công.",
                **base,
            )
        return hinted() or _details("uncertain", reason="low_confidence", message=MESSAGE_UNCERTAIN, **base)

    threshold = cal.thresholds.get(analysis.bucket, 0.9)
    outside_mass = sum(p for code, p in dist.items() if code not in SUPPORTED_CODES)
    # Bằng chứng độc lập ủng hộ nhãn top-1 (tiếng Việt có/không dấu, marker) thì không coi là "ngoài phạm vi".
    independent_support = analysis.features.get("support", 0.0) >= 0.5
    probably_outside = (
        outside_mass >= cfg.outside_mass_block
        and analysis.p1 < cfg.outside_p1_cap
        and not independent_support
    )
    # Từ đơn 1–3 chữ cái ("ok", "no", "hi", "ban") dùng chung cho nhiều ngôn ngữ: không bao giờ tự kết luận.
    profile = analysis.profile
    tiny_word = bool(profile) and not profile.cjk_like and profile.eff_len <= 1 and profile.letters <= 3
    confident = (
        analysis.meta >= threshold
        and analysis.p1 >= cfg.min_confidence
        and analysis.margin >= cfg.min_margin
        and not probably_outside
        and not tiny_word
    )
    if confident:
        return _details("detected", resolved_source_lang=top1, **base)

    hint_result = hinted()
    if hint_result is not None:
        return hint_result

    if probably_outside:
        return _details(
            "uncertain", reason="out_of_scope",
            message="Văn bản có thể thuộc một ngôn ngữ chưa được hỗ trợ. Hãy chọn ngôn ngữ nguồn thủ công.",
            **base,
        )
    if analysis.features.get("short"):
        reason = "short_input"
    elif analysis.features.get("agree") == 0.0:
        reason = "engines_disagree"
    elif analysis.multilingual:
        reason = "mixed_language"
    else:
        reason = "low_confidence"
    return _details("uncertain", reason=reason, message=MESSAGE_UNCERTAIN, **base)


# ---------------------------------------------------------------------------
# API công khai
# ---------------------------------------------------------------------------
_result_cache: "OrderedDict[str, LanguageDetectionDetails]" = OrderedDict()
_cache_lock = threading.Lock()


def _cache_key(text: str, hint: Optional[str]) -> str:
    return hashlib.sha1(f"{hint or ''}\x00{text}".encode("utf-8", "surrogatepass")).hexdigest()


def detect_language_detailed(text: str, hint: Optional[str] = None) -> LanguageDetectionDetails:
    """Nhận diện ngôn ngữ của `text`. Không bao giờ ném ngoại lệ: lỗi → status="system_error"."""
    cfg = get_config()
    key = _cache_key(text, hint)
    with _cache_lock:
        cached = _result_cache.get(key)
        if cached is not None:
            _result_cache.move_to_end(key)
            return cached.model_copy(deep=True)

    try:
        analysis = _analyze(text, hint)
        details = _finalize(analysis, hint)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Language detection crashed: {type(exc).__name__}: {exc}")
        return LanguageDetectionDetails(status="system_error", engine="none", message=MESSAGE_SYSTEM)

    logger.info(
        "LangDetect",
        extra={
            "status": details.status, "lang": details.resolved_source_lang, "engine": details.engine,
            "confidence": details.confidence, "margin": details.margin, "reason": details.reason,
            "input_length": len(text),
        },
    )
    if details.status != "system_error":
        with _cache_lock:
            _result_cache[key] = details
            while len(_result_cache) > cfg.cache_size:
                _result_cache.popitem(last=False)
    return details.model_copy(deep=True)


def extract_features(text: str) -> dict:
    """Đặc trưng nội bộ cho công cụ hiệu chỉnh offline (không dùng cache)."""
    analysis = _analyze(text, None)
    return {
        "early": analysis.early is not None,
        "features": analysis.features,
        "top1": analysis.top1,
        "bucket": analysis.bucket,
        "meta": analysis.meta,
    }


def manual_details(lang: str) -> LanguageDetectionDetails:
    return LanguageDetectionDetails(
        resolved_source_lang=lang, status="detected", confidence=1.0, margin=1.0, engine="manual",
        candidates=[DetectionCandidate(language=lang, confidence=1.0)], is_multilingual=False,
    )


@dataclass
class LanguageResolution:
    details: LanguageDetectionDetails
    should_translate: bool
    source_lang: Optional[str]
    error_code: Optional[str] = None
    http_status: int = 200
    message: Optional[str] = None


class LanguageResolutionError(Exception):
    """Ném ra khi không thể dịch vì ngôn ngữ nguồn chưa xác định được."""

    def __init__(self, resolution: LanguageResolution):
        super().__init__(resolution.message or resolution.error_code)
        self.resolution = resolution

    def to_payload(self) -> dict:
        res = self.resolution
        return {
            "ok": False,
            "detail": res.message,
            "error": {"code": res.error_code, "message": res.message,
                      "detection": res.details.model_dump()},
        }


def resolve_source_language(text: str, requested: str, hint: Optional[str] = None) -> LanguageResolution:
    """Điểm vào duy nhất cho /text, /stream, /detect (đồng bộ)."""
    if requested != "auto":
        return LanguageResolution(manual_details(requested), True, requested)
    details = detect_language_detailed(text, hint)
    if details.status == "detected" and details.resolved_source_lang:
        return LanguageResolution(details, True, details.resolved_source_lang)
    code, http_status = STATUS_ERROR_CODES.get(details.status, ("LANG_UNKNOWN", 400))
    return LanguageResolution(
        details, False, None, error_code=code, http_status=http_status,
        message=details.message or MESSAGE_UNCERTAIN,
    )


# Executor riêng để detection không tranh chấp thread với NLLB (to_thread mặc định).
_EXECUTOR = ThreadPoolExecutor(max_workers=_env_int("DETECT_WORKERS", 4), thread_name_prefix="langdetect")


async def aresolve_source_language(text: str, requested: str, hint: Optional[str] = None) -> LanguageResolution:
    if requested != "auto":
        return LanguageResolution(manual_details(requested), True, requested)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_EXECUTOR, resolve_source_language, text, requested, hint)


async def adetect_language_detailed(text: str, hint: Optional[str] = None) -> LanguageDetectionDetails:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_EXECUTOR, detect_language_detailed, text, hint)


WARMUP_SAMPLES = (
    "Machine learning is transforming healthcare",
    "Trí tuệ nhân tạo đang thay đổi giáo dục",
    "人工智能正在改变教育",
    "La inteligencia artificial está cambiando la educación",
)


def warm_up() -> dict:
    """Nạp fastText + Lingua và chạy vài lượt nhận diện (gọi lúc khởi động)."""
    status = {"fasttext": _get_fasttext_model() is not None, "lingua": False}
    try:
        _get_lingua()
        status["lingua"] = True
        for sample in WARMUP_SAMPLES:
            detect_language_detailed(sample)
        _result_cache.clear()
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Language detection warm-up failed: {type(exc).__name__}: {exc}")
    return status


def engines_ready() -> dict:
    return {"fasttext": _get_fasttext_model() is not None, "lingua": _lingua is not None}
