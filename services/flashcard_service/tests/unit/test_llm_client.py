import json

import httpx
import pytest

from app.services import llm_client
from app.services.llm_client import LLMBadOutput, LLMUnavailable, classify_error, extract_json_object, generate_json


def _openai_body(content: str, prompt: int = 11, completion: int = 7) -> dict:
    return {"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": prompt, "completion_tokens": completion}}


def _gemini_body(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}], "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 3}}


@pytest.fixture
def transport(monkeypatch):
    """Cài httpx client giả: test gán `transport.handler(request) -> httpx.Response`."""
    for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENAI_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("VOCAB_LLM_PROVIDERS", raising=False)

    class State:
        requests: list = []
        handler = None

    state = State()

    def dispatch(request: httpx.Request) -> httpx.Response:
        state.requests.append(request)
        return state.handler(request)

    llm_client.reset_cooldowns()
    monkeypatch.setattr(llm_client, "_client", httpx.AsyncClient(transport=httpx.MockTransport(dispatch)))
    yield state
    llm_client.reset_cooldowns()


def _hosts(state) -> list:
    return [r.url.host for r in state.requests]


class TestExtractJson:
    def test_plain_json(self):
        assert extract_json_object('{"a": 1}') == {"a": 1}

    def test_markdown_fence(self):
        assert extract_json_object('```json\n{"a": 1}\n```') == {"a": 1}

    def test_prose_around_object(self):
        assert extract_json_object('Sure! Here you go:\n{"words": []}\nHope this helps.') == {"words": []}

    @pytest.mark.parametrize("text", ["", "   ", "not json at all", "[1, 2, 3]", '{"a": '])
    def test_invalid_raises_bad_output(self, text):
        with pytest.raises(LLMBadOutput):
            extract_json_object(text)


class TestClassifyError:
    def _status_error(self, status: int, headers: dict | None = None) -> httpx.HTTPStatusError:
        request = httpx.Request("POST", "https://x.test")
        return httpx.HTTPStatusError("boom", request=request, response=httpx.Response(status, headers=headers or {}, request=request))

    def test_rate_limit_uses_retry_after(self):
        code, seconds = classify_error(self._status_error(429, {"retry-after": "42"}))
        assert (code, seconds) == ("quota", 42.0)

    def test_rate_limit_default_and_cap(self):
        assert classify_error(self._status_error(429))[1] == 60.0
        assert classify_error(self._status_error(429, {"retry-after": "9999"}))[1] == 300.0

    def test_auth_not_found_timeout_other(self):
        assert classify_error(self._status_error(401))[0] == "auth"
        assert classify_error(self._status_error(403))[0] == "auth"
        assert classify_error(self._status_error(404))[0] == "not_found"
        assert classify_error(httpx.ReadTimeout("slow"))[0] == "timeout"
        assert classify_error(self._status_error(500))[0] == "unavailable"
        assert classify_error(RuntimeError("quota exceeded for project"))[0] == "quota"


class TestGenerateJson:
    async def test_no_providers_configured(self, transport):
        with pytest.raises(LLMUnavailable) as err:
            await generate_json("sys", "user")
        assert err.value.code == "no_provider"
        assert transport.requests == []

    async def test_groq_success_sends_expected_request(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test_secret")
        transport.handler = lambda r: httpx.Response(200, json=_openai_body('{"ok": true}'))
        result = await generate_json("SYS", "USER", temperature=0.4, max_tokens=123)

        assert result.data == {"ok": True}
        assert result.provider.startswith("groq:")
        assert (result.prompt_tokens, result.completion_tokens) == (11, 7)
        req = transport.requests[0]
        body = json.loads(req.content)
        assert req.headers["authorization"] == "Bearer gsk_test_secret"
        assert body["messages"] == [{"role": "system", "content": "SYS"}, {"role": "user", "content": "USER"}]
        assert body["response_format"] == {"type": "json_object"}
        assert body["temperature"] == 0.4 and body["max_tokens"] == 123
        assert body["model"] == "openai/gpt-oss-120b" and body["reasoning_effort"] == "low"  # gpt-oss: giảm suy luận để nhanh

    async def test_qwen_override_disables_reasoning(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "g")
        monkeypatch.setenv("VOCAB_GROQ_MODEL", "qwen/qwen3.8-27b")
        transport.handler = lambda r: httpx.Response(200, json=_openai_body('{"ok": true}'))
        await generate_json("s", "u")
        body = json.loads(transport.requests[0].content)
        assert body["model"] == "qwen/qwen3.8-27b" and body["reasoning_effort"] == "none"

    async def test_api_key_never_appears_in_url_or_body(self, transport, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "AIza_super_secret")
        transport.handler = lambda r: httpx.Response(200, json=_gemini_body('{"ok": 1}'))
        await generate_json("s", "u")
        req = transport.requests[0]
        assert "AIza_super_secret" not in str(req.url)
        assert b"AIza_super_secret" not in req.content
        assert req.headers["x-goog-api-key"] == "AIza_super_secret"

    async def test_groq_429_falls_back_to_gemini_and_enters_cooldown(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "g")
        monkeypatch.setenv("GEMINI_API_KEY", "m")

        def handler(request):
            if request.url.host == "api.groq.com":
                return httpx.Response(429, json={"error": "rate limited"}, headers={"retry-after": "30"})
            return httpx.Response(200, json=_gemini_body('{"from": "gemini"}'))

        transport.handler = handler
        first = await generate_json("s", "u")
        assert first.data == {"from": "gemini"} and first.provider.startswith("gemini:")
        assert _hosts(transport) == ["api.groq.com", "generativelanguage.googleapis.com"]

        transport.requests.clear()
        await generate_json("s", "u")
        assert _hosts(transport) == ["generativelanguage.googleapis.com"]  # Groq đang nghỉ: không gọi lại

    async def test_invalid_json_is_retried_then_next_provider(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "g")
        monkeypatch.setenv("GEMINI_API_KEY", "m")

        def handler(request):
            if request.url.host == "api.groq.com":
                return httpx.Response(200, json=_openai_body("I cannot produce JSON, sorry"))
            return httpx.Response(200, json=_gemini_body('{"ok": 1}'))

        transport.handler = handler
        result = await generate_json("s", "u", temperature=0.7)
        assert result.data == {"ok": 1}
        groq_calls = [r for r in transport.requests if r.url.host == "api.groq.com"]
        assert len(groq_calls) == 2
        assert json.loads(groq_calls[0].content)["temperature"] == 0.7
        assert json.loads(groq_calls[1].content)["temperature"] == 0.0  # lần thử lại dùng temperature 0

    async def test_response_format_rejected_is_retried_without_it(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "g")
        calls = []

        def handler(request):
            body = json.loads(request.content)
            calls.append("response_format" in body)
            if "response_format" in body:
                return httpx.Response(400, text='{"error":"response_format is not supported for this model"}')
            return httpx.Response(200, json=_openai_body('{"ok": 2}'))

        transport.handler = handler
        assert (await generate_json("s", "u")).data == {"ok": 2}
        assert calls == [True, False]

    async def test_all_providers_failing_raises_unavailable_with_first_code(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "g")
        monkeypatch.setenv("GEMINI_API_KEY", "m")
        transport.handler = lambda r: httpx.Response(429 if r.url.host == "api.groq.com" else 500, json={})
        with pytest.raises(LLMUnavailable) as err:
            await generate_json("s", "u")
        assert err.value.code == "quota"
        assert "groq=quota" in err.value.detail and "gemini=unavailable" in err.value.detail

    async def test_timeout_is_classified_and_next_provider_used(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "g")
        monkeypatch.setenv("GEMINI_API_KEY", "m")

        def handler(request):
            if request.url.host == "api.groq.com":
                raise httpx.ReadTimeout("too slow", request=request)
            return httpx.Response(200, json=_gemini_body('{"ok": 3}'))

        transport.handler = handler
        assert (await generate_json("s", "u")).data == {"ok": 3}

    async def test_images_only_go_to_vision_capable_providers(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "g")
        monkeypatch.setenv("GEMINI_API_KEY", "m")
        transport.handler = lambda r: httpx.Response(200, json=_gemini_body('{"words": []}'))
        await generate_json("s", "u", images=[("image/png", b"\x89PNG-bytes")])
        assert _hosts(transport) == ["generativelanguage.googleapis.com"]
        body = json.loads(transport.requests[0].content)
        part = body["contents"][0]["parts"][1]["inlineData"]
        assert part["mimeType"] == "image/png" and part["data"]

    async def test_images_without_vision_provider_is_unavailable(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "g")
        with pytest.raises(LLMUnavailable) as err:
            await generate_json("s", "u", images=[("image/png", b"x")])
        assert err.value.code == "no_provider"
        assert transport.requests == []

    async def test_provider_order_env_is_respected(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "g")
        monkeypatch.setenv("GEMINI_API_KEY", "m")
        monkeypatch.setenv("VOCAB_LLM_PROVIDERS", "gemini,groq")
        transport.handler = lambda r: httpx.Response(200, json=_gemini_body('{"first": "gemini"}'))
        assert (await generate_json("s", "u")).provider.startswith("gemini:")
        assert _hosts(transport) == ["generativelanguage.googleapis.com"]

    async def test_openai_compatible_endpoint(self, transport, monkeypatch):
        monkeypatch.setenv("OPENAI_BASE_URL", "http://vllm.local:8000/v1/")
        monkeypatch.setenv("OPENAI_MODEL_NAME", "qwen-test")
        transport.handler = lambda r: httpx.Response(200, json=_openai_body('{"ok": 4}'))
        result = await generate_json("s", "u")
        assert result.provider == "openai:qwen-test"
        assert str(transport.requests[0].url) == "http://vllm.local:8000/v1/chat/completions"
        assert json.loads(transport.requests[0].content)["chat_template_kwargs"] == {"enable_thinking": False}


class TestHardLimits:
    async def test_request_too_large_is_classified_and_long_cooldown(self, transport, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "g")
        monkeypatch.setenv("GEMINI_API_KEY", "m")
        body = {"error": {"message": "Request too large for model `qwen/qwen3.8-27b` on output tokens per minute (OTPM): Limit 1000, Requested 1025. "
                                     "reduce max_tokens (or the request's expected output) and try again."}}

        def handler(request):
            if request.url.host == "api.groq.com":
                return httpx.Response(429, json=body)
            return httpx.Response(200, json=_gemini_body('{"from": "gemini"}'))

        transport.handler = handler
        assert (await generate_json("s", "u")).provider.startswith("gemini:")
        assert llm_client._cooldown_until["groq"] - llm_client.time.monotonic() > 200  # nghỉ ~5 phút, không phải 60 s
        transport.requests.clear()
        await generate_json("s", "u")
        assert _hosts(transport) == ["generativelanguage.googleapis.com"]

    def test_classification(self):
        request = httpx.Request("POST", "https://x.test")
        response = httpx.Response(429, text="Request too large for model ... reduce max_tokens", request=request)
        error = httpx.HTTPStatusError("429", request=request, response=response)
        assert classify_error(error) == ("too_large", 300.0)
