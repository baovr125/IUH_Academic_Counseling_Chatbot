"""Kiểm thử OpenAICompatibleProvider.generate_stream khi LLM local lỗi.

Hồi quy cho lỗi tham chiếu biến `e` ngoài khối `except` (NameError khi không có provider dự phòng).
"""
from unittest.mock import patch

from app.services.llm_providers import OpenAICompatibleProvider


class _FailingClient:
    """Thay httpx.AsyncClient: mở stream là lỗi ngay."""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def stream(self, *args, **kwargs):
        raise RuntimeError("máy chủ LLM không phản hồi")


class _FallbackProvider:
    last_used_model = "Fallback-Test"

    async def generate_stream(self, system_instruction, history_dicts):
        yield {"text": "câu trả lời dự phòng"}


async def _collect(provider):
    return [c async for c in provider.generate_stream("system", [{"role": "user", "content": "xin chào"}])]


async def test_stream_error_without_fallback_reports_original_error():
    provider = OpenAICompatibleProvider("http://llm.invalid/v1", "key", "model", fallback_provider=None)
    with patch("app.services.llm_providers.httpx.AsyncClient", _FailingClient):
        chunks = await _collect(provider)

    assert len(chunks) == 1
    assert "không có Fallback" in chunks[0]["text"]
    assert "máy chủ LLM không phản hồi" in chunks[0]["text"]


async def test_stream_error_with_fallback_uses_fallback_provider():
    provider = OpenAICompatibleProvider("http://llm.invalid/v1", "key", "model", fallback_provider=_FallbackProvider())
    with patch("app.services.llm_providers.httpx.AsyncClient", _FailingClient):
        chunks = await _collect(provider)

    assert chunks == [{"text": "câu trả lời dự phòng"}]
    assert provider.last_used_model == "Fallback-Test"
