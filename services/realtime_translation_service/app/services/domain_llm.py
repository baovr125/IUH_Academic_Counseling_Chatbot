"""Gọi LLM streaming cho chế độ dịch theo chuyên ngành: Groq -> Gemini, có circuit breaker.

- Mỗi provider có "thời gian nghỉ" (cooldown) khi gặp quota/timeout/lỗi để không gọi lại từng request
  trong lúc đang hết hạn mức (Groq free: ~8.000 token/phút).
- Phân biệt lỗi trước token đầu (thử provider kế tiếp / báo LLMUnavailable) với lỗi giữa chừng (LLMInterrupted).
- Tên model đọc từ biến môi trường, chỉ áp dụng cho phạm vi chuyên ngành (GROQ_DOMAIN_MODEL, GEMINI_DOMAIN_MODEL).
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import AsyncGenerator, Dict, List, Tuple

from app.utils.logger import logger

DEFAULT_GROQ_DOMAIN_MODEL = "qwen/qwen3.8-27b"
DEFAULT_GEMINI_DOMAIN_MODEL = "gemini-2.5-flash"

_cooldown_until: Dict[str, float] = {}
_COOLDOWN_SECONDS = {"quota": 60.0, "timeout": 10.0, "unavailable": 15.0, "not_found": 600.0, "auth": 600.0}


class LLMError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


class LLMUnavailable(LLMError):
    """Mọi provider đều lỗi trước khi có token đầu tiên."""


class LLMInterrupted(LLMError):
    """Lỗi sau khi đã phát token: bản dịch có thể chưa đầy đủ."""


def groq_domain_model() -> str:
    return os.getenv("GROQ_DOMAIN_MODEL", DEFAULT_GROQ_DOMAIN_MODEL).strip() or DEFAULT_GROQ_DOMAIN_MODEL


def gemini_domain_model() -> str:
    return os.getenv("GEMINI_DOMAIN_MODEL", DEFAULT_GEMINI_DOMAIN_MODEL).strip() or DEFAULT_GEMINI_DOMAIN_MODEL


def _env_seconds(name: str, default: float) -> float:
    try:
        return max(0.1, float(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


def first_token_timeout() -> float:
    return _env_seconds("DOMAIN_LLM_FIRST_TOKEN_TIMEOUT_SECONDS", 10.0)


def total_timeout() -> float:
    return _env_seconds("DOMAIN_LLM_TOTAL_TIMEOUT_SECONDS", 40.0)


def provider_order() -> List[str]:
    raw = os.getenv("DOMAIN_LLM_PROVIDERS", "groq,gemini")
    order = [p.strip().lower() for p in raw.split(",") if p.strip().lower() in ("groq", "gemini")]
    return order or ["groq", "gemini"]


# --------------------------------------------------------------------------- circuit breaker
def reset_cooldowns() -> None:
    _cooldown_until.clear()


def _is_cooling(provider: str) -> bool:
    return _cooldown_until.get(provider, 0.0) > time.monotonic()


def classify_error(exc: BaseException) -> Tuple[str, float]:
    """Trả (mã lỗi, số giây nghỉ)."""
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return "timeout", _COOLDOWN_SECONDS["timeout"]
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    text = str(exc).lower()
    if status == 429 or any(k in text for k in ("rate limit", "rate_limit", "quota", "resource_exhausted", "too many requests")):
        retry = None
        headers = getattr(getattr(exc, "response", None), "headers", None)
        try:
            retry = float(headers.get("retry-after")) if headers and headers.get("retry-after") else None
        except (TypeError, ValueError):
            retry = None
        return "quota", min(300.0, retry) if retry else _COOLDOWN_SECONDS["quota"]
    if status == 404 or "does not exist" in text or "model_not_found" in text:
        return "not_found", _COOLDOWN_SECONDS["not_found"]
    if status in (401, 403) or "api key" in text or "permission" in text:
        return "auth", _COOLDOWN_SECONDS["auth"]
    return "unavailable", _COOLDOWN_SECONDS["unavailable"]


def _trip(provider: str, code: str, seconds: float, exc: BaseException) -> None:
    _cooldown_until[provider] = time.monotonic() + seconds
    logger.warning(f"Domain LLM provider '{provider}' failed ({code}); pausing {seconds:.0f}s: {str(exc)[:160]}")


# --------------------------------------------------------------------------- providers
def _groq_extra(model: str) -> dict:
    # Model suy luận trên Groq cần tắt/giảm suy luận để token đầu đến nhanh (đã đo: 0,2-0,6 s).
    if "gpt-oss" in model:
        return {"reasoning_effort": os.getenv("GROQ_DOMAIN_REASONING_EFFORT", "low")}
    if "qwen" in model:
        return {"reasoning_effort": os.getenv("GROQ_DOMAIN_REASONING_EFFORT", "none")}
    return {}


async def _stream_groq(client, model: str, system: str, user: str, temperature: float) -> AsyncGenerator[str, None]:
    stream = await client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        stream=True,
        temperature=temperature,
        **_groq_extra(model),
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def _stream_gemini(client, model: str, system: str, user: str, temperature: float) -> AsyncGenerator[str, None]:
    kwargs = {}
    try:
        from google.genai import types

        kwargs["config"] = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        contents = user
    except Exception:  # noqa: BLE001 - SDK khác phiên bản: gộp system vào nội dung
        contents = f"{system}\n\nText:\n{user}"
    stream = await client.aio.models.generate_content_stream(model=model, contents=contents, **kwargs)
    async for chunk in stream:
        if chunk.text:
            yield chunk.text


def _providers():
    from app.services import llm_service

    for name in provider_order():
        if name == "groq":
            yield name, f"groq:{groq_domain_model()}", llm_service.get_groq_client, _stream_groq, groq_domain_model()
        else:
            yield name, f"gemini:{gemini_domain_model()}", llm_service.get_gemini_client, _stream_gemini, gemini_domain_model()


async def stream_llm(
    system: str, user: str, temperature: float = 0.2
) -> AsyncGenerator[Tuple[str, str], None]:
    """Phát ("provider", nhãn) một lần rồi các ("chunk", văn bản).

    Raise LLMUnavailable nếu không provider nào cho ra token; LLMInterrupted nếu lỗi sau khi đã phát token.
    """
    failures: List[Tuple[str, str]] = []
    for name, label, get_client, runner, model in _providers():
        if _is_cooling(name):
            failures.append((name, "cooldown"))
            continue
        client = get_client()
        if not client:
            failures.append((name, "no_client"))
            continue
        agen = runner(client, model, system, user, temperature)
        started = False
        try:
            first = await asyncio.wait_for(agen.__anext__(), first_token_timeout())
            started = True
            yield ("provider", label)
            yield ("chunk", first)
            deadline = time.monotonic() + total_timeout()
            while True:
                nxt = await asyncio.wait_for(agen.__anext__(), max(0.1, deadline - time.monotonic()))
                yield ("chunk", nxt)
        except StopAsyncIteration:
            if started:
                return
            failures.append((name, "empty"))
        except Exception as exc:  # noqa: BLE001
            code, seconds = classify_error(exc)
            _trip(name, code, seconds, exc)
            if started:
                raise LLMInterrupted(code, str(exc)[:200]) from exc
            failures.append((name, code))
        finally:
            try:
                await agen.aclose()
            except Exception:  # noqa: BLE001
                pass
    codes = [c for _, c in failures if c not in ("cooldown", "no_client")]
    summary = codes[0] if codes else ("cooldown" if any(c == "cooldown" for _, c in failures) else "no_provider")
    raise LLMUnavailable(summary, ", ".join(f"{n}={c}" for n, c in failures))
