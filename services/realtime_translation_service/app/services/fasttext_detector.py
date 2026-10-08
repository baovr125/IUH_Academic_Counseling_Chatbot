import os
import fasttext
from functools import lru_cache
from app.utils.logger import logger

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../../../models")
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

MODEL_PATH = os.getenv("FASTTEXT_LID_MODEL", os.path.join(MODEL_DIR, "lid.176.ftz"))

# Mapping fastText labels (__label__xx) → service language codes
FASTTEXT_LANG_MAP = {
    "__label__en": "en", "__label__de": "de", "__label__zh": "zh",
    "__label__ja": "ja", "__label__ko": "ko", "__label__fr": "fr",
    "__label__es": "es", "__label__ru": "ru", "__label__th": "th",
    "__label__vi": "vi",
}

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

def fasttext_detect(text: str) -> tuple[str | None, float, float]:
    """Trả về (language_code, confidence, margin) hoặc (None, 0.0, 0.0)."""
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
