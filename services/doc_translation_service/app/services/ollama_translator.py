import os
import re
import httpx
import logging
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

OLLAMA_DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")

SYSTEM_TRANSLATION_PROMPT = (
    "<instructions>\n"
    "You are an expert academic and technical translator specializing in English to Vietnamese translation.\n"
    "TARGET LANGUAGE: VIETNAMESE (TIẾNG VIỆT).\n"
    "STRICT QUALITY CONSTRAINTS:\n"
    "1. Output 100% pure Vietnamese. Absolutely NO Chinese characters (中文 / 汉字), Japanese, or Korean under any circumstances.\n"
    "2. NEVER output conversational preamble, explanations, notes, or meta-comments (e.g., do NOT write 'Dưới đây là...', 'Here is...', '以下是...'). Output ONLY the raw translated text directly.\n"
    "3. Translate ALL headings, section titles, and table contents into Vietnamese.\n"
    "4. VERY IMPORTANT: You must preserve all placeholders like {v0}, {v1}, {v2} exactly as they appear in the original text. Do not translate or modify them.\n"
    "5. Use formal, professional Vietnamese academic terminology.\n"
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
        r'^(Dưới đây là|Phiên bản dịch|Bản dịch|Text:|Nội dung:|Here is the translation:|Below is the translated).*?\n+',
        r'^(Đoạn văn bản sau|Đây là bản dịch|Bản dịch tiếng Việt).*?\n+',
        r'^```(markdown)?\s*\n',
    ]
    for pattern in preamble_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'\n+```\s*$', '', cleaned)
    closing_patterns = [
        r'\n*(Xin lưu ý|Lưu ý rằng|Please note|Note:|注：|请注意).*?$',
        r'\n*(Hy vọng bản dịch này|Mong bản dịch|Chúc bạn).*?$',
    ]
    for pattern in closing_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    return cleaned.strip()

def contains_untranslated_foreign_scripts(text: str) -> bool:
    if not text:
        return False
    consecutive_chinese = re.findall(r'[\u4e00-\u9fff]{2,}', text)
    if consecutive_chinese:
        return True
    foreign_count = len(re.findall(r'[\u4e00-\u9fff\uac00-\ud7af]', text))
    return foreign_count > 3

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
            "max_tokens": 2048
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

class OllamaPDFTranslator:
    name = "ollama_pdf"
    
    def __init__(self, lang_in: str = "en", lang_out: str = "vi", model: str = None, **kwargs):
        self.lang_in = lang_in
        self.lang_out = lang_out
        self.model = model or OLLAMA_DEFAULT_MODEL
        
    def translate(self, text: str) -> str:
        prompt = f"Translate the following text to Vietnamese. Keep the formula notation {{vX}} exactly unchanged. Do not add any notes.\n\nSource Text: {text}\n\nTranslated Text:"
        
        try:
            # 1. Try vLLM / Ollama
            raw_output = call_ollama_generate(prompt, SYSTEM_TRANSLATION_PROMPT, self.model, temperature=0.1)
            cleaned = sanitize_translation_output(raw_output)
            
            # Strict checking for Chinese characters
            if contains_untranslated_foreign_scripts(cleaned):
                logger.warning("vLLM output contained Chinese characters. Retrying with stricter prompt...")
                strict_system = SYSTEM_TRANSLATION_PROMPT + "\nLƯU Ý: Tuyệt đối KHÔNG xuất ký tự Hán/Trung Quốc!"
                raw_output = call_ollama_generate(prompt, strict_system, self.model, temperature=0.0)
                cleaned = sanitize_translation_output(raw_output)
                if contains_untranslated_foreign_scripts(cleaned):
                    raise ValueError("vLLM still returned Chinese characters")
                    
            return cleaned
        except Exception as vllm_err:
            logger.warning(f"vLLM failed ({vllm_err}). Triggering Groq Fallback...")
            try:
                # 2. Try Groq
                raw_output = _execute_groq_fallback(prompt, SYSTEM_TRANSLATION_PROMPT)
                return sanitize_translation_output(raw_output)
            except Exception as groq_err:
                logger.error(f"Groq fallback failed ({groq_err}). Returning original text.")
                return text # Final fallback: return original text to prevent breaking PDF
