import os
import json
import asyncio
import ctranslate2
import transformers
from typing import AsyncGenerator, Optional
from google import genai
from groq import AsyncGroq
from app.utils.logger import logger

# Initialize Clients
_translator = None
_tokenizer = None
_nllb_load_attempted = False

NLLB_MODEL_DIR = os.getenv(
    "NLLB_MODEL_DIR",
    "/app/models/nllb-200-distilled-600M-ct2-int8",
)
NLLB_DEVICE = os.getenv("NLLB_DEVICE", "auto").lower()

# Model LLM dự phòng khi NLLB không dùng được (Groq trước, Gemini sau) và cho trích xuất flashcard.
DEFAULT_GROQ_TRANSLATE_MODEL = "llama-3.1-8b-instant"
DEFAULT_GEMINI_TRANSLATE_MODEL = "gemini-2.5-flash"


def groq_translate_model() -> str:
    """Ghi đè bằng GROQ_TRANSLATE_MODEL."""
    return os.getenv("GROQ_TRANSLATE_MODEL", "").strip() or DEFAULT_GROQ_TRANSLATE_MODEL


def gemini_translate_model() -> str:
    """Ghi đè bằng GEMINI_TRANSLATE_MODEL."""
    return os.getenv("GEMINI_TRANSLATE_MODEL", "").strip() or DEFAULT_GEMINI_TRANSLATE_MODEL
NLLB_REQUIRED_FILES = (
    "config.json",
    "model.bin",
    "sentencepiece.bpe.model",
    "shared_vocabulary.txt",
    "tokenizer.json",
)


def _resolve_nllb_model_dir() -> str | None:
    """Resolve one deterministic model path, with local-dev fallbacks."""
    candidates = [NLLB_MODEL_DIR]
    if NLLB_MODEL_DIR == "/app/models/nllb-200-distilled-600M-ct2-int8":
        candidates.extend([
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models/nllb-200-distilled-600M-ct2-int8")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../models/nllb-200-distilled-600M-ct2-int8")),
        ])

    for candidate in candidates:
        if os.path.isdir(candidate):
            missing = [
                filename for filename in NLLB_REQUIRED_FILES
                if not os.path.isfile(os.path.join(candidate, filename))
            ]
            if not missing:
                return candidate
            logger.error("NLLB model is incomplete at %s; missing files: %s", candidate, missing)

    logger.error("NLLB model directory is unavailable. Checked: %s", candidates)
    return None

def get_nllb_translator():
    global _translator, _tokenizer, _nllb_load_attempted
    if _translator is not None and _tokenizer is not None:
        return _translator, _tokenizer
    if _nllb_load_attempted:
        return None, None
    _nllb_load_attempted = True

    model_dir = _resolve_nllb_model_dir()
    if not model_dir:
        return None, None

    try:
        cuda_available = NLLB_DEVICE == "cuda"
        if NLLB_DEVICE == "auto":
            try:
                cuda_available = ctranslate2.get_cuda_device_count() > 0
            except Exception:
                cuda_available = False

        device = "cuda" if cuda_available else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        logger.info(f"Loading NLLB CTranslate2 model on {device.upper()} ({compute_type})...")
        _translator = ctranslate2.Translator(
            model_dir,
            device=device,
            compute_type=compute_type,
            inter_threads=2,
            intra_threads=2
        )
        logger.info("Loading NLLB Tokenizer...")
        _tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir)
        return _translator, _tokenizer
    except Exception as e:
        logger.error(f"Failed to load NLLB model on {device}: {e}. Retrying on CPU INT8 fallback...")
        _translator = None
        _tokenizer = None
        try:
            _translator = ctranslate2.Translator(
                model_dir,
                device="cpu",
                compute_type="int8",
                inter_threads=2,
                intra_threads=2
            )
            _tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir)
            return _translator, _tokenizer
        except Exception as cpu_err:
            logger.error(f"Failed to load NLLB model on CPU fallback: {cpu_err}")
            _translator = None
            _tokenizer = None
            return None, None

def preload_models():
    """Preloads the local translation models into memory (VRAM if available) at startup."""
    logger.info("Preloading local NLLB models...")
    translator, tokenizer = get_nllb_translator()
    
    if translator and tokenizer:
        logger.info("Running dummy inference to warm up CUDA memory allocation...")
        try:
            # Dummy inference to trigger memory allocation and kernel compilation
            nllb_src = LANG_MAP.get("en", "eng_Latn")
            nllb_tgt = LANG_MAP.get("vi", "vie_Latn")
            tokenizer.src_lang = nllb_src
            source_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode("Hello"))
            target_prefix = [nllb_tgt]
            
            # Use synchronous translate_batch for warm-up
            translator.translate_batch(
                [source_tokens],
                target_prefix=[target_prefix]
            )
            logger.info("Dummy inference completed. Model is fully warmed up.")
        except Exception as e:
            logger.warning(f"NLLB model loaded but warm-up inference failed: {e}")
            _translator = None
            _tokenizer = None
            return False
        logger.info("NLLB model loaded and warmed successfully.")
        return True

    logger.error("NLLB model preload failed; local translation is unavailable.")
    return False

def get_groq_client() -> Optional[AsyncGroq]:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        return AsyncGroq(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None

LANG_MAP = {
    "en": "eng_Latn",
    "de": "deu_Latn",
    "zh": "zho_Hans",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "fr": "fra_Latn",
    "es": "spa_Latn",
    "ru": "rus_Cyrl",
    "th": "tha_Thai",
    "vi": "vie_Latn",
}

DOMAIN_EMOJIS = {
    "Công nghệ Thông tin (IT)": "💻",
    "Y khoa / Sức khỏe": "💊",
    "Kinh tế / Tài chính": "📊",
    "Kỹ thuật Cơ khí": "⚙️",
    "Luật / Pháp lý": "⚖️",
    "Marketing": "📈"
}

async def handle_flow_2_stream_translation(text: str, source_lang: str, target_lang: str, domain: str) -> AsyncGenerator[str, None]:
    """Dịch theo chuyên ngành bằng LLM (thủ công hoặc auto) và phát các sự kiện SSE dạng JSON.

    Logic nằm ở `app.services.domain_translation` (dùng chung với /text).
    """
    from app.services.domain_translation import translate_with_domain

    async for event in translate_with_domain(text, source_lang, target_lang, domain):
        if "_internal" in event:
            continue
        yield json.dumps(event, ensure_ascii=False)

async def stream_translation(text: str, source_lang: str, target_lang: str, domain: str = "", source_lang_hint: Optional[str] = None) -> AsyncGenerator[str, None]:
    """Translates text using local NLLB model via CTranslate2. Falls back to Groq/Gemini."""

    # Cùng một hàm resolve với /text và /detect: chỉ `detected` mới được dịch.
    from app.services.language_detection import aresolve_source_language
    resolution = await aresolve_source_language(text, source_lang, source_lang_hint)

    # Luôn phát event 'detection' chuẩn hóa chứa toàn bộ metadata cho client
    yield json.dumps({
        'event': 'detection',
        'detection': resolution.details.model_dump()
    })

    if not resolution.should_translate:
        yield json.dumps({'error': resolution.message, 'code': resolution.error_code})
        return

    source_lang = resolution.source_lang
    yield json.dumps({'resolved_source_lang': source_lang})

    is_flow_2 = domain and domain != "Dịch thông thường (Mặc định)"
    if is_flow_2:
        async for chunk in handle_flow_2_stream_translation(text, source_lang, target_lang, domain):
            yield chunk
        return
        
    # --- FLOW 1 BEGIN ---
    translator, tokenizer = get_nllb_translator()
    
    if translator and tokenizer:
        nllb_src = LANG_MAP.get(source_lang, "eng_Latn")
        nllb_tgt = LANG_MAP.get(target_lang, "vie_Latn")

        try:
            from app.utils.html_parser import HTMLTranslator
            html_translator = HTMLTranslator()
            html_with_placeholders, texts_to_translate = html_translator.extract_text(text)
            
            if not texts_to_translate:
                yield json.dumps({'text': html_with_placeholders})
                return
                
            tokenizer.src_lang = nllb_src
            source_tokens_list = [tokenizer.convert_ids_to_tokens(tokenizer.encode(t)) for t in texts_to_translate]
            target_prefix = [nllb_tgt]

            results = await asyncio.to_thread(
                translator.translate_batch,
                source_tokens_list,
                target_prefix=[target_prefix] * len(texts_to_translate)
            )
            
            translated_texts = []
            for res in results:
                target_tokens = res.hypotheses[0][1:] 
                translated = tokenizer.decode(tokenizer.convert_tokens_to_ids(target_tokens))
                translated_texts.append(translated)
                
            final_translated = html_translator.reconstruct_html(html_with_placeholders, translated_texts)
            
            yield json.dumps({'text': final_translated})
            return
        except Exception as e:
            logger.error(f"NLLB translation failed: {e}. Falling back to LLM.")

    # Fallback to LLMs if NLLB fails or is not available
    groq_client = get_groq_client()
    system_prompt = f"You are a professional translator.\n\nTranslate the following text from {source_lang} to {target_lang}. Only output the direct translation, do not explain or converse. Preserve all HTML tags perfectly if present."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]

    use_fallback = False
    if groq_client:
        try:
            stream = await groq_client.chat.completions.create(
                model=groq_translate_model(),
                messages=messages,
                stream=True,
                temperature=0.3
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield json.dumps({'text': content})
            return
        except Exception as e:
            logger.warning(f"Groq API streaming failed: {e}. Falling back to Gemini.")
            use_fallback = True
    else:
        logger.warning("Groq API key not found. Using Gemini fallback.")
        use_fallback = True

    if use_fallback:
        gemini_client = get_gemini_client()
        if not gemini_client:
            yield json.dumps({'error': 'No LLM API keys configured.'})
            return

        try:
            full_prompt = f"{system_prompt}\n\nText:\n{text}"
            response_stream = await gemini_client.aio.models.generate_content_stream(
                model=gemini_translate_model(),
                contents=full_prompt
            )
            async for chunk in response_stream:
                if chunk.text:
                    yield json.dumps({'text': chunk.text})
        except Exception as e:
            logger.error(f"Gemini fallback failed: {e}")
            yield json.dumps({'error': 'Translation service unavailable.'})


async def extract_flashcard(word: str, context: str, domain: str = "", source_lang: Optional[str] = None) -> dict:
    """Extracts flashcard info returning JSON. Có source_lang -> nghĩa tiếng Việt + phiên âm theo ngôn ngữ đó."""
    from app.services.flashcard_extract import build_prompt, normalize_result

    system_prompt, user_prompt = build_prompt(word, context, domain, source_lang)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    # Bài học có ngôn ngữ nguồn cần model mạnh hơn (CJK/Thái); không truyền thì giữ model cũ.
    groq_model = os.getenv("GROQ_FLASHCARD_MODEL", DEFAULT_GROQ_TRANSLATE_MODEL).strip() or DEFAULT_GROQ_TRANSLATE_MODEL
    structured = bool(source_lang)

    groq_client = get_groq_client()
    if groq_client:
        try:
            response = await groq_client.chat.completions.create(
                model=groq_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            data = json.loads(response.choices[0].message.content)
            return normalize_result(data, word) if structured else data
        except Exception as e:
            logger.warning(f"Groq JSON extraction failed: {e}")

    # Fallback to Gemini for JSON
    gemini_client = get_gemini_client()
    if gemini_client:
        try:
            from google.genai import types
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = gemini_client.models.generate_content(
                model=gemini_translate_model(),
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            return normalize_result(data, word) if structured else data
        except Exception as e:
            logger.error(f"Gemini Flashcard fallback failed: {e}")

    return {}
