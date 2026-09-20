import os
import re
import httpx
import logging
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

OLLAMA_DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

LANGUAGE_MAP = {
    "vi": "Vietnamese (Tiếng Việt)",
    "en": "English",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "ru": "Russian",
    "es": "Spanish",
    "th": "Thai"
}

def get_system_prompt(lang_in: str, lang_out: str, has_placeholders: bool = False) -> str:
    source = LANGUAGE_MAP.get(lang_in.lower(), lang_in)
    target = LANGUAGE_MAP.get(lang_out.lower(), lang_out)
    placeholder_rule = (
        "5. VERY IMPORTANT: You must preserve all placeholders like {v0}, {v1}, {v2} exactly as they appear in the original text. Do not translate or modify them.\n"
        if has_placeholders else ""
    )
    return (
        "<instructions>\n"
        f"You are an expert academic and technical translator. Your task is to translate from {source} to {target}.\n"
        f"TARGET LANGUAGE: {target}.\n"
        "STRICT QUALITY CONSTRAINTS:\n"
        "1. Output 100% natural target language. Do not output characters of other languages unless necessary for technical terms.\n"
        "2. NEVER output conversational preamble, explanations, notes, or meta-comments (e.g., do NOT write 'Here is...', 'Below is...', 'Dưới đây là...'). Output ONLY the raw translated text directly.\n"
        "3. Translate ALL headings, section titles, and table contents.\n"
        "4. DO NOT transliterate English terms into meaningless target language words (e.g. 'Mekhanizm'). If a term is not in the glossary, keep the original English term.\n"
        f"{placeholder_rule}"
        "6. Use formal, professional academic terminology.\n"
        "</instructions>\n"
    )

_TUNNEL_BYPASS_HEADERS = {
    "ngrok-skip-browser-warning": "true",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

def get_ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", OLLAMA_DEFAULT_HOST).rstrip("/")

def check_ollama_health() -> bool:
    try:
        with httpx.Client(timeout=2.0, verify=False) as client:
            url = f"{get_ollama_host()}/api/tags" if os.getenv("USE_VLLM", "false").lower() != "true" else f"{get_ollama_host()}/v1/models"
            resp = client.get(url, headers=_TUNNEL_BYPASS_HEADERS)
            if resp.status_code != 200:
                return False
            # Ensure it's not the ngrok HTML intercept page
            if "text/html" in resp.headers.get("content-type", "").lower():
                return False
            return True
    except Exception:
        return False

def sanitize_translation_output(text: str) -> str:
    if not text:
        return ""
    cleaned = text
    preamble_patterns = [
        # Tiếng Anh
        r'^(Here is|Below is|Here\'s|The following is)[\s\S]{0,80}?\n+',
        r'^(Translation:|Translated text:|Translated version:)\s*\n*',
        r'^```(markdown|text|json)?\s*\n',
        # Tiếng Việt
        r'^(Dưới đây là|Phiên bản dịch|Bản dịch|Nội dung dịch)[^\n]*\n+',
        r'^(Văn bản đã dịch|Bản dịch sau đây|Đây là bản dịch)[^\n]*\n+',
        r'^(Đoạn văn bản sau|Bản dịch tiếng Việt)[^\n]*\n+',
        # Prompt leakage & Errors
        r'userPlease try again\n?',
        r'The previous response was cut off\.? Please continue\.?\n?',
        r'Please continue the translation\n?',
    ]
    for pattern in preamble_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)

    cleaned = re.sub(r'\n+```\s*$', '', cleaned)

    # Xóa các tag rác do mô hình sinh ra
    cleaned = re.sub(r'<=\$', '', cleaned)
    cleaned = re.sub(r'\$>', '', cleaned)
    cleaned = re.sub(r'\$?<=\{v\d+\}\$?>', '', cleaned)
    cleaned = re.sub(r'<\/?b\d+>', '', cleaned)
    
    # Xóa JSON noise lặp lại
    cleaned = re.sub(r'(\{"\}\s*){2,}', '', cleaned)
    cleaned = re.sub(r'(\{\s*\"){2,}', '', cleaned)

    closing_patterns = [
        r'\n*(Note:|Please note|Note that).*$',
        r'\n*(Xin lưu ý|Lưu ý rằng|Lưu ý:|Chú ý:).*$',
        r'\n*(Hy vọng|Mong bản dịch|Chúc bạn).*$',
        r'\n*(Nếu bạn cần|Bạn có thể liên hệ).*$',
    ]
    for pattern in closing_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    return cleaned.strip()

def contains_untranslated_foreign_scripts(text: str, target_lang: str = 'vi') -> bool:
    if not text:
        return False

    # Luôn bị coi là ngoại lai (CJK liên tiếp)
    if re.search(r'[\u4e00-\u9fff]{2,}', text):
        return True
    if re.search(r'[\uac00-\ud7af]{2,}', text):  # Korean
        return True

    # Ngoại lai khi target là ngôn ngữ Latin (vi/en/fr/de...)
    LATIN_TARGETS = {'vi', 'en', 'fr', 'de', 'es', 'it', 'pt'}
    if target_lang.lower()[:2] in LATIN_TARGETS:
        FOREIGN_SCRIPTS = [
            (r'[\u0400-\u04FF]{3,}', "Cyrillic"),   # Tiếng Nga
            (r'[\u0600-\u06FF]{3,}', "Arabic"),
            (r'[\u0900-\u097F]{3,}', "Devanagari"),
            (r'[\u0E00-\u0E7F]{3,}', "Thai"),
            (r'[\u3040-\u309F]{2,}', "Hiragana"),
            (r'[\u30A0-\u30FF]{2,}', "Katakana"),
        ]
        for pattern, name in FOREIGN_SCRIPTS:
            if re.search(pattern, text):
                logger.warning(f"Unexpected {name} script in {target_lang} output!")
                return True
                
        # Dùng langdetect để kiểm tra nếu text dài và target là Tiếng Việt
        if target_lang.lower()[:2] == 'vi' and len(text.split()) > 4:
            try:
                from langdetect import detect
                lang = detect(text)
                if lang in ['es', 'pt', 'en']:
                    # Cho phép English nếu là terms, cần check cẩn thận hơn, nhưng 'es', 'pt' thì chắc chắn sai
                    if lang in ['es', 'pt']:
                        logger.warning(f"Detected hallucinated language: {lang} instead of {target_lang}")
                        return True
            except Exception:
                pass

    return False

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError, RuntimeError)),
    reraise=True
)
def call_ollama_generate(prompt: str, system_instruction: str, model: str, temperature: float = 0.1) -> str:
    target_host = get_ollama_host()
    is_vllm = os.getenv("USE_VLLM", "false").lower() == "true"
    
    if is_vllm:
        url = f"{target_host}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "top_p": 0.9,
            "max_tokens": 2048,
            "repetition_penalty": 1.15
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('VLLM_API_KEY', 'sk-dummy')}",
            **_TUNNEL_BYPASS_HEADERS,
        }
    else:
        url = f"{target_host}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": 2048,
                "repeat_penalty": 1.15
            }
        }
        headers = {
            "Content-Type": "application/json",
            **_TUNNEL_BYPASS_HEADERS,
        }

    try:
        with httpx.Client(timeout=45.0, verify=False, http2=False) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            if is_vllm:
                return data["choices"][0]["message"]["content"].strip()
            else:
                return data.get("response", "").strip()
    except Exception as e:
        logger.error(f"Error calling Ollama/vLLM: {e}")
        raise RuntimeError(f"Ollama/vLLM API error: {e}")

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True
)
def _execute_groq_fallback(prompt: str, system_instruction: str) -> str:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("Missing GROQ_API_KEY")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 2048
    }
    with httpx.Client(timeout=35.0) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()

def _extract_placeholders(text: str) -> set:
    return set(re.findall(r'\{v\d+\}', text))

def _restore_placeholders(translated: str, original_text: str) -> str:
    """Restore missing placeholders theo vị trí tỷ lệ trong bản dịch."""
    originals = re.findall(r'\{v\d+\}', original_text)
    if not originals:
        return translated
    # Xóa placeholder biến dạng còn sót
    cleaned = re.sub(r'\{[^}]{0,20}\}|<=\$[^$]*\$>', '', translated).strip()
    total_len = max(len(cleaned), 1)
    parts = list(cleaned)
    offset = 0
    for i, ph in enumerate(originals):
        pos = int((i + 1) / (len(originals) + 1) * total_len) + offset
        parts.insert(pos, ph)
        offset += len(ph)
    return ''.join(parts)

class OllamaPDFTranslator:
    name = "ollama_pdf"
    
    def __init__(self, lang_in: str = "en", lang_out: str = "vi", model: str = None, glossary: dict = None, **kwargs):
        self.lang_in = lang_in
        self.lang_out = lang_out
        self.model = model or OLLAMA_DEFAULT_MODEL
        self.glossary = glossary or {}
        
    def _build_glossary_hint(self, text: str) -> str:
        if not self.glossary:
            return ""
        matched_items = []
        for k, v in self.glossary.items():
            escaped_k = re.escape(k)
            # Use word boundary if possible, otherwise simple substring check
            pattern = r'\b' + escaped_k + r'\b'
            try:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    matched_items.append((k, v))
                elif k.lower() in text.lower():
                    matched_items.append((k, v))
            except Exception:
                if k.lower() in text.lower():
                    matched_items.append((k, v))
                    
        if not matched_items:
            return ""
            
        lines = [f"  - {k} -> {v}" for k, v in matched_items[:30]]
        return "\n[DOMAIN GLOSSARY — Use these translations exactly]:\n" + "\n".join(lines) + "\n"
        
    def translate(self, text: str, context: Optional[str] = None) -> str:
        target_lang_name = LANGUAGE_MAP.get(self.lang_out.lower(), self.lang_out)
        glossary_hint = self._build_glossary_hint(text)
        
        has_placeholders = bool(re.search(r'\{v\d+\}', text))
        placeholder_instruction = " Keep the formula notation {vX} exactly unchanged." if has_placeholders else ""

        if context and context.strip() and not re.match(r"^\{v\d+\}$", context.strip()):
            prompt = f"Translate the following text to {target_lang_name}.{placeholder_instruction} Do not add any notes.{glossary_hint}\n\n[Previous Context (For reference only, DO NOT translate)]:\n{context}\n\n[Text to translate]:\n{text}\n\nTranslated Text:"
        else:
            prompt = f"Translate the following text to {target_lang_name}.{placeholder_instruction} Do not add any notes.{glossary_hint}\n\n[Text to translate]:\n{text}\n\nTranslated Text:"
            
        system_prompt = get_system_prompt(self.lang_in, self.lang_out, has_placeholders)
        
        try:
            # 1. Try vLLM / Ollama
            raw_output = call_ollama_generate(prompt, system_prompt, self.model, temperature=0.1)
            cleaned = sanitize_translation_output(raw_output)
            
            # === THÊM: Placeholder integrity check ===
            original_phs = _extract_placeholders(text)
            result_phs   = _extract_placeholders(cleaned)

            if original_phs and original_phs != result_phs:
                logger.warning(f"Placeholder mismatch! Expected {original_phs}, got {result_phs}.")
                strict_system = system_prompt + (
                    "\nCRITICAL: Input chứa placeholders {v0},{v1}... "
                    "PHẢI giữ nguyên 100%, KHÔNG đổi tên, KHÔNG xóa, KHÔNG sửa format."
                )
                try:
                    raw2 = call_ollama_generate(prompt, strict_system, self.model, temperature=0.0)
                    cleaned2 = sanitize_translation_output(raw2)
                    if _extract_placeholders(cleaned2) == original_phs:
                        cleaned = cleaned2
                    else:
                        cleaned = _restore_placeholders(cleaned, text)
                except Exception:
                    cleaned = _restore_placeholders(cleaned, text)
            
            # Strict checking for Chinese/foreign characters
            if contains_untranslated_foreign_scripts(cleaned, target_lang=self.lang_out):
                logger.warning("vLLM output contained unexpected foreign characters. Retrying with stricter prompt...")
                strict_system = system_prompt + "\nLƯU Ý: Tuyệt đối KHÔNG xuất ký tự ngoại lai không liên quan!"
                raw_output = call_ollama_generate(prompt, strict_system, self.model, temperature=0.0)
                cleaned2 = sanitize_translation_output(raw_output)
                if contains_untranslated_foreign_scripts(cleaned2, target_lang=self.lang_out):
                    raise ValueError("vLLM still returned foreign characters")
                cleaned = cleaned2
                
                # Cần check lại placeholder sau retry này
                if original_phs and _extract_placeholders(cleaned) != original_phs:
                    cleaned = _restore_placeholders(cleaned, text)

            # === THÊM: Terminology Enforcement (Post-processing) ===
            if self.glossary:
                for k in sorted(self.glossary.keys(), key=len, reverse=True):
                    v = self.glossary[k]
                    if k.lower() in text.lower():
                        # Replace English term if LLM left it untranslated
                        pattern = r'\b' + re.escape(k) + r'\b'
                        cleaned = re.sub(pattern, v, cleaned, flags=re.IGNORECASE)

            return cleaned
        except Exception as vllm_err:
            logger.warning(f"vLLM failed ({vllm_err}). Triggering Groq Fallback...")
            try:
                # 2. Try Groq
                raw_output = _execute_groq_fallback(prompt, system_prompt)
                cleaned = sanitize_translation_output(raw_output)
                # Check placeholders for Groq too
                original_phs = _extract_placeholders(text)
                if original_phs and _extract_placeholders(cleaned) != original_phs:
                    cleaned = _restore_placeholders(cleaned, text)
                    
                # === THÊM: Terminology Enforcement (Post-processing) cho Groq ===
                if self.glossary:
                    for k in sorted(self.glossary.keys(), key=len, reverse=True):
                        v = self.glossary[k]
                        if k.lower() in text.lower():
                            pattern = r'\b' + re.escape(k) + r'\b'
                            cleaned = re.sub(pattern, v, cleaned, flags=re.IGNORECASE)
                            
                return cleaned
            except Exception as groq_err:
                logger.error(f"Groq fallback failed ({groq_err}). Returning original text.")
                return text # Final fallback: return original text to prevent breaking PDF
