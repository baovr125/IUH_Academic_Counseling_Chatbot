import os
import fasttext
from functools import lru_cache
from app.utils.logger import logger

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../../../models")
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

def _resolve_model_path() -> str:
    """Env FASTTEXT_LID_MODEL > models/ của service > services/models/ dùng chung (chạy local)."""
    explicit = os.getenv("FASTTEXT_LID_MODEL")
    if explicit:
        return explicit
    candidates = [
        os.path.join(MODEL_DIR, "lid.176.bin"),
        os.path.join(MODEL_DIR, "lid.176.ftz"),
        os.path.join(MODEL_DIR, "..", "..", "models", "lid.176.ftz"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return os.path.normpath(candidate)
    return os.path.normpath(candidates[1])


MODEL_PATH = _resolve_model_path()

# Mapping fastText labels (__label__xx) → service language codes
FASTTEXT_LANG_MAP = {
    "__label__en": "en", "__label__de": "de", "__label__zh": "zh",
    "__label__ja": "ja", "__label__ko": "ko", "__label__fr": "fr",
    "__label__es": "es", "__label__ru": "ru", "__label__th": "th",
    "__label__vi": "vi",
}

# Biến thể của cùng một ngôn ngữ được gộp về mã dịch vụ (vd: Quảng Đông → zh).
FASTTEXT_LABEL_ALIASES = {"yue": "zh", "wuu": "zh"}

@lru_cache(maxsize=1)
def _get_fasttext_model():
    if not os.path.exists(MODEL_PATH):
        logger.error(f"fastText model not found at {MODEL_PATH}. Run download_model.py first.")
        return None
    try:
        # fasttext suppress warnings
        fasttext.FastText.eprint = lambda x: None
        return fasttext.load_model(MODEL_PATH)
    except Exception as e:
        logger.error(f"Failed to load fastText model: {e}")
        return None

def fasttext_topk(text: str, k: int = 5) -> list[tuple[str, float]]:
    """Trả về top-k (mã_ngôn_ngữ, xác_suất) với nhãn gốc của fastText.

    Giữ cả nhãn ngoài phạm vi dịch vụ (it, pt, id, ar...) để tầng quyết định có thể
    nhận biết ngôn ngữ chưa được hỗ trợ thay vì ép vào một trong các ngôn ngữ hỗ trợ.
    Trả về danh sách rỗng nếu model không khả dụng hoặc input rỗng.
    """
    model = _get_fasttext_model()
    if not model:
        return []

    clean_text = text.replace("\n", " ").strip()
    if not clean_text:
        return []

    try:
        labels, scores = model.predict(clean_text, k=k)
    except Exception as e:
        logger.warning(f"FastText prediction error: {e}")
        return []

    merged: dict[str, float] = {}
    for label, score in zip(labels, scores):
        code = label.replace("__label__", "")
        code = FASTTEXT_LABEL_ALIASES.get(code, code)
        merged[code] = merged.get(code, 0.0) + float(score)
    return sorted(merged.items(), key=lambda item: item[1], reverse=True)

def fasttext_detect(text: str) -> tuple[str | None, float, float]:
    """Trả về (language_code, confidence, margin) hoặc (None, 0.0, 0.0).

    Giữ lại cho tương thích ngược (benchmark/test cũ). Nhãn ngoài phạm vi trả về None.
    """
    model = _get_fasttext_model()
    if not model:
        return None, 0.0, 0.0

    # FastText expects single line
    clean_text = text.replace("\n", " ").strip()
    if not clean_text:
        return None, 0.0, 0.0

    try:
        labels, scores = model.predict(clean_text, k=2)
        label = labels[0]
        score = float(scores[0])
        margin = score - float(scores[1]) if len(scores) > 1 else score
        lang_code = FASTTEXT_LANG_MAP.get(label)
        return lang_code, score, margin
    except Exception as e:
        logger.warning(f"FastText prediction error: {e}")
        return None, 0.0, 0.0
