"""Gọi LLM trả JSON cho tính năng sinh từ vựng: Groq -> Gemini -> OpenAI-compatible (vLLM), chỉ dùng `httpx`.

- Mỗi provider có "thời gian nghỉ" (cooldown) khi gặp quota/timeout/lỗi xác thực để không gọi lại liên tục
  (cùng ý tưởng với realtime_translation_service/app/services/domain_llm.py; service này độc lập nên không import chéo).
- Đầu ra bắt buộc là một đối tượng JSON; nếu provider trả văn bản kèm rào markdown thì được bóc ra.
- Biến môi trường:
    VOCAB_LLM_PROVIDERS      thứ tự provider, mặc định "groq,gemini,openai"
    GROQ_API_KEY / VOCAB_GROQ_MODEL      (mặc định openai/gpt-oss-120b; xem ghi chú ở DEFAULT_GROQ_MODEL)
    GEMINI_API_KEY / VOCAB_GEMINI_MODEL  (mặc định gemini-2.5-flash; hỗ trợ ảnh)
    OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL_NAME   endpoint OpenAI-compatible (vLLM)
    VOCAB_LLM_TIMEOUT_SECONDS            thời gian chờ mỗi lần gọi, mặc định 40
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx

from app.utils.logger import logger

# Mặc định gpt-oss-120b vì khóa Groq hiện tại (tier on_demand) giới hạn qwen/qwen3.8-27b ở 1.000 token ĐẦU RA/phút:
# mọi yêu cầu max_tokens lớn hơn bị 429 ngay nên bước ENRICH không chạy được (xem evaluation/README.md). Đổi bằng VOCAB_GROQ_MODEL.
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_COOLDOWN_SECONDS = {"quota": 60.0, "timeout": 10.0, "unavailable": 15.0, "not_found": 600.0, "auth": 600.0, "too_large": 300.0}
_cooldown_until: Dict[str, float] = {}


class LLMError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


class LLMUnavailable(LLMError):
    """Mọi provider đều lỗi hoặc chưa được cấu hình."""


class LLMBadOutput(LLMError):
    """Provider trả lời nhưng không phải JSON hợp lệ."""


@dataclass
class LLMResult:
    data: Dict[str, Any]
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class _Provider:
    name: str
    label: str
    supports_images: bool
    call: Any = field(repr=False, default=None)


def llm_timeout() -> float:
    try:
        return max(5.0, float(os.getenv("VOCAB_LLM_TIMEOUT_SECONDS", "40")))
    except ValueError:
        return 40.0


def reset_cooldowns() -> None:
    _cooldown_until.clear()


def _is_cooling(name: str) -> bool:
    return _cooldown_until.get(name, 0.0) > time.monotonic()


def classify_error(exc: BaseException) -> Tuple[str, float]:
    """Trả (mã lỗi, số giây nghỉ)."""
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, httpx.TimeoutException)):
        return "timeout", _COOLDOWN_SECONDS["timeout"]
    status = None
    response = getattr(exc, "response", None)
    if response is not None:
        status = getattr(response, "status_code", None)
    text = str(exc).lower()
    body = ""
    if response is not None:
        try:
            body = response.text.lower()
        except Exception:  # noqa: BLE001
            body = ""
    # Giới hạn CỨNG của mô hình (ví dụ Groq free: 1.000 token đầu ra/phút cho qwen3.8-27b): thử lại ngay vô ích,
    # nên nghỉ lâu và chuyển provider khác thay vì lặp lại mỗi phút.
    if "request too large" in body or "reduce max_tokens" in body:
        return "too_large", _COOLDOWN_SECONDS["too_large"]
    if status == 429 or any(k in text for k in ("rate limit", "rate_limit", "quota", "resource_exhausted")):
        retry = None
        try:
            header = response.headers.get("retry-after") if response is not None else None
            retry = float(header) if header else None
        except (TypeError, ValueError, AttributeError):
            retry = None
        return "quota", min(300.0, retry) if retry else _COOLDOWN_SECONDS["quota"]
    if status == 404 or "model_not_found" in text or "does not exist" in text:
        return "not_found", _COOLDOWN_SECONDS["not_found"]
    if status in (401, 403):
        return "auth", _COOLDOWN_SECONDS["auth"]
    return "unavailable", _COOLDOWN_SECONDS["unavailable"]


def extract_json_object(text: str) -> Dict[str, Any]:
    """Bóc một đối tượng JSON từ văn bản (chịu được rào ```json và lời dẫn thừa)."""
    if not text or not text.strip():
        raise LLMBadOutput("empty", "Mô hình trả về nội dung rỗng")
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    for candidate in (cleaned, cleaned[cleaned.find("{"): cleaned.rfind("}") + 1] if "{" in cleaned else ""):
        if not candidate:
            continue
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise LLMBadOutput("invalid_json", cleaned[:200])


_client: Optional[httpx.AsyncClient] = None


def _http() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(llm_timeout(), connect=10.0))
    return _client


# --------------------------------------------------------------------------- các provider
async def _call_openai_compatible(
    url: str, api_key: str, model: str, system: str, user: str,
    temperature: float, max_tokens: int, extra: Dict[str, Any], images: Sequence[Tuple[str, bytes]],
) -> Tuple[str, int, int]:
    if images:
        content: Any = [{"type": "text", "text": user}] + [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(raw).decode()}"}}
            for mime, raw in images
        ]
    else:
        content = user
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        **extra,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = await _http().post(url, json=payload, headers=headers, timeout=llm_timeout())
    if response.status_code == 400 and "response_format" in response.text:
        payload.pop("response_format", None)  # một số endpoint không hỗ trợ chế độ JSON
        response = await _http().post(url, json=payload, headers=headers, timeout=llm_timeout())
    response.raise_for_status()
    body = response.json()
    message = (body.get("choices") or [{}])[0].get("message", {})
    usage = body.get("usage") or {}
    return message.get("content") or "", int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0)


async def _groq(system, user, temperature, max_tokens, images):
    model = os.getenv("VOCAB_GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
    extra: Dict[str, Any] = {}
    if "qwen" in model:
        extra["reasoning_effort"] = os.getenv("GROQ_DOMAIN_REASONING_EFFORT", "none")  # tắt suy luận để nhanh
    elif "gpt-oss" in model:
        extra["reasoning_effort"] = "low"
    return await _call_openai_compatible(
        GROQ_URL, os.environ["GROQ_API_KEY"], model, system, user, temperature, max_tokens, extra, images
    )


async def _openai(system, user, temperature, max_tokens, images):
    base = os.environ["OPENAI_BASE_URL"].rstrip("/")
    model = os.getenv("OPENAI_MODEL_NAME", "").strip() or "default"
    extra = {"chat_template_kwargs": {"enable_thinking": False}}  # vLLM: tắt chế độ suy nghĩ của Qwen3
    return await _call_openai_compatible(
        f"{base}/chat/completions", os.getenv("OPENAI_API_KEY", "EMPTY"), model, system, user,
        temperature, max_tokens, extra, images,
    )


async def _gemini(system, user, temperature, max_tokens, images):
    model = os.getenv("VOCAB_GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    parts: List[Dict[str, Any]] = [{"text": user}] + [
        {"inlineData": {"mimeType": mime, "data": base64.b64encode(raw).decode()}} for mime, raw in images
    ]
    generation_config: Dict[str, Any] = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens,
        "responseMimeType": "application/json",
    }
    if "2.5" in model and "pro" not in model:
        generation_config["thinkingConfig"] = {"thinkingBudget": 0}
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": generation_config,
    }
    headers = {"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"}
    response = await _http().post(GEMINI_URL.format(model=model), json=payload, headers=headers, timeout=llm_timeout())
    response.raise_for_status()
    body = response.json()
    candidates = body.get("candidates") or []
    text = "".join(p.get("text", "") for p in ((candidates[0].get("content") or {}).get("parts") or [])) if candidates else ""
    usage = body.get("usageMetadata") or {}
    return text, int(usage.get("promptTokenCount") or 0), int(usage.get("candidatesTokenCount") or 0)


def _configured_providers() -> List[_Provider]:
    order = [p.strip().lower() for p in os.getenv("VOCAB_LLM_PROVIDERS", "groq,gemini,openai").split(",") if p.strip()]
    providers: List[_Provider] = []
    for name in order:
        if name == "groq" and os.getenv("GROQ_API_KEY"):
            providers.append(_Provider("groq", f"groq:{os.getenv('VOCAB_GROQ_MODEL', DEFAULT_GROQ_MODEL)}", False, _groq))
        elif name == "gemini" and os.getenv("GEMINI_API_KEY"):
            providers.append(_Provider("gemini", f"gemini:{os.getenv('VOCAB_GEMINI_MODEL', DEFAULT_GEMINI_MODEL)}", True, _gemini))
        elif name == "openai" and os.getenv("OPENAI_BASE_URL"):
            vision = os.getenv("VOCAB_OPENAI_VISION", "0") == "1"
            providers.append(_Provider("openai", f"openai:{os.getenv('OPENAI_MODEL_NAME', 'default')}", vision, _openai))
    return providers


async def generate_json(
    system: str,
    user: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    images: Sequence[Tuple[str, bytes]] = (),
    timeout: Optional[float] = None,
) -> LLMResult:
    """
    Gọi LLM và trả về đối tượng JSON. Thử lần lượt các provider (bỏ qua provider đang nghỉ/chưa cấu hình).
    `timeout` (giây) giới hạn mỗi lần gọi, không vượt quá VOCAB_LLM_TIMEOUT_SECONDS.
    Raise LLMUnavailable nếu không provider nào thành công.
    """
    call_timeout = min(timeout, llm_timeout()) if timeout else llm_timeout()
    failures: List[Tuple[str, str]] = []
    providers = _configured_providers()
    if images:
        providers = [p for p in providers if p.supports_images]
    if not providers:
        raise LLMUnavailable("no_provider", "Chưa cấu hình provider LLM phù hợp (GROQ_API_KEY / GEMINI_API_KEY / OPENAI_BASE_URL).")

    for provider in providers:
        if _is_cooling(provider.name):
            failures.append((provider.name, "cooldown"))
            continue
        for attempt in range(2):
            try:
                text, p_tok, c_tok = await asyncio.wait_for(
                    provider.call(system, user, temperature if attempt == 0 else 0.0, max_tokens, images),
                    timeout=call_timeout,
                )
                return LLMResult(extract_json_object(text), provider.label, p_tok, c_tok)
            except LLMBadOutput as exc:
                failures.append((provider.name, exc.code))
                logger.warning(f"Vocab LLM {provider.name} trả JSON không hợp lệ (lần {attempt + 1}): {exc.detail[:120]}")
                continue  # thử lại một lần với temperature 0
            except Exception as exc:  # noqa: BLE001
                code, seconds = classify_error(exc)
                _cooldown_until[provider.name] = time.monotonic() + seconds
                logger.warning(f"Vocab LLM provider '{provider.name}' lỗi ({code}); nghỉ {seconds:.0f}s: {str(exc)[:160]}")
                failures.append((provider.name, code))
                break
    summary = ", ".join(f"{n}={c}" for n, c in failures)
    codes = [c for _, c in failures if c not in ("cooldown",)]
    raise LLMUnavailable(codes[0] if codes else "cooldown", summary)
