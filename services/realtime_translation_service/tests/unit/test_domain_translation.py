"""Test đơn vị cho lớp gọi LLM (circuit breaker, timeout, lỗi) và bộ điều phối dịch theo chuyên ngành.

Groq/Gemini/NLLB/Redis đều được mock có kiểm soát: lỗi, hết quota, timeout, stream đứt giữa chừng,
định dạng hỏng và confidence bất thường.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import domain_llm
from app.services.domain_index import DomainIndex
from app.services.domain_translation import (
    MSG_AMBIGUOUS,
    MSG_FALLBACK,
    MSG_INTERRUPTED,
    MSG_UNAVAILABLE,
    collect_domain_translation,
    translate_with_domain,
)

IT = "Công nghệ Thông tin (IT)"
MED = "Y khoa / Sức khỏe"
ECO = "Kinh tế / Tài chính"

ROWS = [
    {"domain": IT, "word": "memory leak", "translation": "rò rỉ bộ nhớ"},
    {"domain": IT, "word": "technical debt", "translation": "nợ kỹ thuật"},
    {"domain": MED, "word": "drug interaction", "translation": "tương tác thuốc"},
    {"domain": MED, "word": "side effect", "translation": "tác dụng phụ"},
    {"domain": ECO, "word": "yield curve", "translation": "đường cong lợi suất"},
    {"domain": ECO, "word": "stock", "translation": "cổ phiếu"},
    {"domain": MED, "word": "stock", "translation": "kho thuốc"},
]


# --------------------------------------------------------------------------- client giả
def groq_client(chunks=(), exc=None, first_delay=0.0, fail_after=None, calls=None):
    async def create(**kwargs):
        if calls is not None:
            calls.append(kwargs)
        if exc is not None:
            raise exc
        if first_delay:
            await asyncio.sleep(first_delay)

        async def gen():
            for i, c in enumerate(chunks):
                if fail_after is not None and i == fail_after:
                    raise RuntimeError("stream đứt")
                yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=c))])

        return gen()

    client = MagicMock()
    client.chat.completions.create = create
    return client


def gemini_client(chunks=(), exc=None, calls=None):
    async def generate_content_stream(**kwargs):
        if calls is not None:
            calls.append(kwargs)
        if exc is not None:
            raise exc

        async def gen():
            for c in chunks:
                yield SimpleNamespace(text=c)

        return gen()

    client = MagicMock()
    client.aio.models.generate_content_stream = generate_content_stream
    return client


class HttpError(Exception):
    def __init__(self, status_code, msg="lỗi"):
        super().__init__(msg)
        self.status_code = status_code


async def drain(agen):
    return [x async for x in agen]


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    domain_llm.reset_cooldowns()
    monkeypatch.delenv("GROQ_DOMAIN_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_DOMAIN_MODEL", raising=False)
    monkeypatch.setenv("DOMAIN_LLM_PROVIDERS", "groq,gemini")
    yield
    domain_llm.reset_cooldowns()


# --------------------------------------------------------------------------- domain_llm
class TestStreamLLM:
    @pytest.mark.asyncio
    async def test_groq_success_reports_provider_and_chunks(self):
        calls = []
        with patch("app.services.llm_service.get_groq_client", return_value=groq_client(["a", "b"], calls=calls)), \
             patch("app.services.llm_service.get_gemini_client", return_value=None):
            events = await drain(domain_llm.stream_llm("sys", "user"))
        assert events == [("provider", f"groq:{domain_llm.DEFAULT_GROQ_DOMAIN_MODEL}"), ("chunk", "a"), ("chunk", "b")]
        assert calls[0]["model"] == domain_llm.DEFAULT_GROQ_DOMAIN_MODEL
        assert calls[0]["stream"] is True
        assert calls[0]["messages"][0] == {"role": "system", "content": "sys"}

    @pytest.mark.asyncio
    async def test_model_name_comes_from_environment(self, monkeypatch):
        monkeypatch.setenv("GROQ_DOMAIN_MODEL", "openai/gpt-oss-120b")
        calls = []
        with patch("app.services.llm_service.get_groq_client", return_value=groq_client(["x"], calls=calls)), \
             patch("app.services.llm_service.get_gemini_client", return_value=None):
            await drain(domain_llm.stream_llm("sys", "user"))
        assert calls[0]["model"] == "openai/gpt-oss-120b"
        assert calls[0]["reasoning_effort"] == "low"

    @pytest.mark.asyncio
    async def test_default_model_is_the_one_chosen_on_dev_set(self):
        calls = []
        with patch("app.services.llm_service.get_groq_client", return_value=groq_client(["x"], calls=calls)), \
             patch("app.services.llm_service.get_gemini_client", return_value=None):
            await drain(domain_llm.stream_llm("sys", "user"))
        assert calls[0]["model"] == "qwen/qwen3.8-27b"
        assert calls[0]["reasoning_effort"] == "none"

    @pytest.mark.asyncio
    async def test_falls_back_to_gemini_when_groq_fails(self):
        with patch("app.services.llm_service.get_groq_client", return_value=groq_client(exc=HttpError(500))), \
             patch("app.services.llm_service.get_gemini_client", return_value=gemini_client(["g1", "g2"])):
            events = await drain(domain_llm.stream_llm("sys", "user"))
        assert events[0] == ("provider", f"gemini:{domain_llm.DEFAULT_GEMINI_DOMAIN_MODEL}")
        assert [v for k, v in events if k == "chunk"] == ["g1", "g2"]

    @pytest.mark.asyncio
    async def test_quota_error_trips_circuit_breaker(self):
        calls = []
        groq = groq_client(exc=HttpError(429, "rate limit reached"), calls=calls)
        with patch("app.services.llm_service.get_groq_client", return_value=groq), \
             patch("app.services.llm_service.get_gemini_client", return_value=gemini_client(["ok"])):
            await drain(domain_llm.stream_llm("sys", "user"))
            await drain(domain_llm.stream_llm("sys", "user"))
        # Lần gọi thứ hai không còn chạm Groq nữa (đang nghỉ).
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_unavailable_reports_reason_code(self):
        with patch("app.services.llm_service.get_groq_client", return_value=groq_client(exc=HttpError(404, "model does not exist"))), \
             patch("app.services.llm_service.get_gemini_client", return_value=None):
            with pytest.raises(domain_llm.LLMUnavailable) as err:
                await drain(domain_llm.stream_llm("sys", "user"))
        assert err.value.code == "not_found"

    @pytest.mark.asyncio
    async def test_no_clients_configured(self):
        with patch("app.services.llm_service.get_groq_client", return_value=None), \
             patch("app.services.llm_service.get_gemini_client", return_value=None):
            with pytest.raises(domain_llm.LLMUnavailable) as err:
                await drain(domain_llm.stream_llm("sys", "user"))
        assert err.value.code == "no_provider"

    @pytest.mark.asyncio
    async def test_first_token_timeout_moves_on_to_next_provider(self, monkeypatch):
        monkeypatch.setenv("DOMAIN_LLM_FIRST_TOKEN_TIMEOUT_SECONDS", "0.1")
        with patch("app.services.llm_service.get_groq_client", return_value=groq_client(["slow"], first_delay=1.0)), \
             patch("app.services.llm_service.get_gemini_client", return_value=gemini_client(["fast"])):
            events = await drain(domain_llm.stream_llm("sys", "user"))
        assert events[0][1].startswith("gemini:")
        assert ("chunk", "fast") in events

    @pytest.mark.asyncio
    async def test_timeout_everywhere_is_reported_as_timeout(self, monkeypatch):
        monkeypatch.setenv("DOMAIN_LLM_FIRST_TOKEN_TIMEOUT_SECONDS", "0.1")
        with patch("app.services.llm_service.get_groq_client", return_value=groq_client(["slow"], first_delay=1.0)), \
             patch("app.services.llm_service.get_gemini_client", return_value=None):
            with pytest.raises(domain_llm.LLMUnavailable) as err:
                await drain(domain_llm.stream_llm("sys", "user"))
        assert err.value.code == "timeout"

    @pytest.mark.asyncio
    async def test_mid_stream_failure_is_interrupted_not_unavailable(self):
        got = []
        with patch("app.services.llm_service.get_groq_client", return_value=groq_client(["một ", "hai ", "ba"], fail_after=2)), \
             patch("app.services.llm_service.get_gemini_client", return_value=gemini_client(["không được gọi"])):
            with pytest.raises(domain_llm.LLMInterrupted):
                async for ev in domain_llm.stream_llm("sys", "user"):
                    got.append(ev)
        assert [v for k, v in got if k == "chunk"] == ["một ", "hai "]

    @pytest.mark.asyncio
    async def test_empty_stream_counts_as_failure(self):
        with patch("app.services.llm_service.get_groq_client", return_value=groq_client([])), \
             patch("app.services.llm_service.get_gemini_client", return_value=None):
            with pytest.raises(domain_llm.LLMUnavailable):
                await drain(domain_llm.stream_llm("sys", "user"))

    @pytest.mark.parametrize("exc,code", [
        (HttpError(429), "quota"),
        (HttpError(500, "RESOURCE_EXHAUSTED: quota exceeded"), "quota"),
        (HttpError(404), "not_found"),
        (HttpError(401), "auth"),
        (asyncio.TimeoutError(), "timeout"),
        (RuntimeError("lạ"), "unavailable"),
    ])
    def test_error_classification(self, exc, code):
        assert domain_llm.classify_error(exc)[0] == code


# --------------------------------------------------------------------------- điều phối
def fake_llm(chunks, provider="groq:test", raise_after=None, raise_exc=None):
    """Thay thế domain_llm.stream_llm: ghi lại system prompt và phát chunk."""
    record = {"calls": []}

    async def stream(system, user, temperature=0.2):
        record["calls"].append({"system": system, "user": user})
        if raise_exc is not None and raise_after is None:
            raise raise_exc
        yield ("provider", provider)
        for i, c in enumerate(chunks):
            if raise_after is not None and i == raise_after:
                raise raise_exc
            yield ("chunk", c)

    return stream, record


@pytest.fixture
def orchestrator():
    index = DomainIndex.build(ROWS)
    set_cache = MagicMock()
    with patch("app.services.domain_translation.get_index", AsyncMock(return_value=index)), \
         patch("app.services.domain_translation.get_cached_domain_result", return_value=None), \
         patch("app.services.domain_translation.set_cached_domain_result", set_cache), \
         patch("app.services.domain_translation.get_domain_version", return_value=1), \
         patch("app.services.domain_translation._nllb", AsyncMock(return_value="Bản dịch NLLB")) as nllb:
        yield SimpleNamespace(index=index, set_cache=set_cache, nllb=nllb)


async def run(text, domain, src="en", tgt="vi", chunks=None, **llm_kwargs):
    stream, record = fake_llm(chunks if chunks is not None else [], **llm_kwargs)
    with patch("app.services.domain_translation.domain_llm.stream_llm", stream):
        events = await drain(translate_with_domain(text, src, tgt, domain))
    return events, record


def event_of(events, kind):
    return [e for e in events if e.get("event") == kind]


def all_warnings(events):
    return [w for e in events if "warnings" in e for w in e["warnings"]]


def codes(events):
    return [w["code"] for w in all_warnings(events)]


def joined(events):
    return "".join(e["text"] for e in events if "text" in e)


AUTO_OK = ["DOMAIN: Công nghệ Thông tin (IT) | CONF: 0.97\n", "---\n", "Một ", "rò rỉ bộ nhớ."]


class TestShortTermPath:
    @pytest.mark.asyncio
    async def test_auto_single_domain_uses_dictionary_without_llm(self, orchestrator):
        events, rec = await run("memory leak", "auto")
        assert rec["calls"] == []
        assert joined(events) == "rò rỉ bộ nhớ"
        details = event_of(events, "domain")[0]["domain"]
        assert (details["status"], details["domain"], details["method"], details["translator"]) == ("detected", IT, "exact", "dictionary")

    @pytest.mark.asyncio
    async def test_exact_lookup_does_not_depend_on_character_count(self, orchestrator):
        # 14 ký tự và 25+ ký tự đều đi cùng một đường tra từ điển.
        events, rec = await run("technical debts", "auto")
        assert joined(events) == "nợ kỹ thuật" and rec["calls"] == []

    @pytest.mark.asyncio
    async def test_auto_shared_term_is_ambiguous_with_candidates(self, orchestrator):
        events, rec = await run("stock", "auto")
        assert rec["calls"] == []
        details = event_of(events, "domain")[0]["domain"]
        assert details["status"] == "ambiguous"
        assert {c["domain"]: c["translation"] for c in details["candidates"]} == {ECO: "cổ phiếu", MED: "kho thuốc"}
        assert codes(events) == ["DOMAIN_AMBIGUOUS"]
        assert all_warnings(events)[0]["message"] == MSG_AMBIGUOUS
        assert joined(events) == ""

    @pytest.mark.asyncio
    async def test_manual_exact_hit_in_selected_domain_uses_dictionary(self, orchestrator):
        events, rec = await run("Memory Leak", IT)
        assert rec["calls"] == [] and joined(events) == "rò rỉ bộ nhớ"
        assert event_of(events, "domain")[0]["domain"]["status"] == "selected"

    @pytest.mark.asyncio
    async def test_manual_term_from_other_domain_goes_to_llm_without_warning(self, orchestrator):
        events, rec = await run("yield curve", IT, chunks=["đường cong lợi suất"])
        assert len(rec["calls"]) == 1
        assert codes(events) == []  # TERM_IN_OTHER_DOMAIN đã bỏ: không làm phiền người dùng

    @pytest.mark.asyncio
    async def test_manual_short_miss_translates_with_llm_silently(self, orchestrator):
        events, rec = await run("random words", IT, chunks=["từ ngẫu nhiên"])
        assert joined(events) == "từ ngẫu nhiên"
        assert codes(events) == []  # TERM_NOT_IN_DICT đã bỏ

    @pytest.mark.asyncio
    async def test_non_english_pair_has_no_dictionary_shortcut(self, orchestrator):
        events, rec = await run("memory leak", "auto", src="de", tgt="vi", chunks=AUTO_OK)
        assert len(rec["calls"]) == 1
        assert codes(events) == []  # GLOSSARY_UNAVAILABLE đã bỏ


class TestManualDomain:
    @pytest.mark.asyncio
    async def test_prompt_contains_glossary_only_for_selected_domain(self, orchestrator):
        text = "A memory leak and a drug interaction occurred"
        events, rec = await run(text, IT, chunks=["bản dịch"])
        system = rec["calls"][0]["system"]
        assert "- memory leak -> rò rỉ bộ nhớ" in system
        assert "drug interaction" not in system
        assert rec["calls"][0]["user"] == text

    @pytest.mark.asyncio
    async def test_morphological_variants_reach_glossary(self, orchestrator):
        events, rec = await run("Memory leaks keep happening in production", IT, chunks=["x"])
        assert "- memory leak -> rò rỉ bộ nhớ" in rec["calls"][0]["system"]

    @pytest.mark.asyncio
    async def test_streams_chunks_and_domain_details_with_applied_terms(self, orchestrator):
        events, _ = await run("A memory leak causes crashes", IT, chunks=["Một ", "rò rỉ bộ nhớ ", "gây sập"], provider="groq:m")
        assert [e["text"] for e in events if "text" in e] == ["Một ", "rò rỉ bộ nhớ ", "gây sập"]
        domain_events = event_of(events, "domain")
        assert domain_events[0]["domain"]["translator"] == "llm:groq:m"
        assert domain_events[-1]["domain"]["applied_terms"] == ["memory leak"]
        assert codes(events) == []
        orchestrator.set_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_glossary_match_is_silent(self, orchestrator):
        events, _ = await run("The server restarted after midnight", IT, chunks=["Máy chủ khởi động lại"])
        assert codes(events) == []  # GLOSSARY_NO_MATCH đã bỏ
        assert event_of(events, "domain")[-1]["domain"]["matched_terms"] == []

    @pytest.mark.asyncio
    async def test_custom_domain_name_is_allowed_without_glossary(self, orchestrator):
        events, rec = await run("The server restarted after midnight", "Thiên văn học", chunks=["x"])
        assert "Thiên văn học" in rec["calls"][0]["system"]
        assert event_of(events, "domain")[0]["domain"]["domain"] == "Thiên văn học"


class TestAutoDomain:
    @pytest.mark.asyncio
    async def test_detected_domain_streams_before_translation_finishes(self, orchestrator):
        events, rec = await run("A memory leak causes crashes", "auto", chunks=AUTO_OK)
        first_domain = next(i for i, e in enumerate(events) if e.get("event") == "domain")
        first_text = next(i for i, e in enumerate(events) if "text" in e)
        assert first_domain < first_text
        assert joined(events) == "Một rò rỉ bộ nhớ."
        final = event_of(events, "domain")[-1]["domain"]
        assert (final["status"], final["domain"]) == ("detected", IT)
        assert final["applied_terms"] == ["memory leak"]
        assert codes(events) == []
        # Prompt auto chứa danh sách domain thật và glossary kèm nhãn domain.
        assert IT in rec["calls"][0]["system"] and "[domain: " in rec["calls"][0]["system"]

    @pytest.mark.asyncio
    async def test_unknown_domain_still_translates_without_banner(self, orchestrator):
        events, _ = await run("We walked along the beach", "auto", chunks=["DOMAIN: unknown | CONF: 0.9\n---\n", "Chúng tôi đi dạo"])
        assert joined(events) == "Chúng tôi đi dạo"
        assert event_of(events, "domain")[-1]["domain"]["status"] == "unknown"
        # Giống nhận diện ngôn ngữ: chỉ có nhãn (event domain), không có cảnh báo.
        assert codes(events) == []
        assert event_of(events, "domain")[-1]["domain"]["reason"] == "llm_unknown"

    @pytest.mark.asyncio
    async def test_low_confidence_abstains(self, orchestrator):
        events, _ = await run("A memory leak causes crashes", "auto",
                              chunks=[f"DOMAIN: {IT} | CONF: 0.30\n---\n", "Bản dịch"])
        assert event_of(events, "domain")[-1]["domain"]["reason"] == "low_confidence"
        assert codes(events) == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("raw", ["nan", "7", "-1", "cao"])
    async def test_abnormal_confidence_is_not_trusted(self, orchestrator, raw):
        events, _ = await run("A memory leak causes crashes", "auto",
                              chunks=[f"DOMAIN: {IT} | CONF: {raw}\n---\n", "Bản dịch"])
        details = event_of(events, "domain")[-1]["domain"]
        assert details["status"] == "unknown" and details["reason"] == "invalid_confidence"

    @pytest.mark.asyncio
    async def test_format_violation_keeps_translation_and_is_not_cached(self, orchestrator):
        events, _ = await run("A memory leak causes crashes", "auto", chunks=["Rò rỉ bộ nhớ gây sập, không có header gì cả."])
        assert joined(events) == "Rò rỉ bộ nhớ gây sập, không có header gì cả."
        assert codes(events) == []  # DOMAIN_FORMAT_ERROR đã bỏ; lý do nằm ở domain.reason
        assert event_of(events, "domain")[-1]["domain"]["reason"] == "format_error"
        assert event_of(events, "domain")[-1]["domain"]["status"] == "unknown"
        orchestrator.set_cache.assert_not_called()

    @pytest.mark.asyncio
    async def test_domain_outside_list_is_rejected(self, orchestrator):
        events, _ = await run("Some text about football", "auto", chunks=["DOMAIN: Thể thao | CONF: 0.99\n---\n", "Bóng đá"])
        assert event_of(events, "domain")[-1]["domain"]["reason"] == "llm_out_of_list"

    @pytest.mark.asyncio
    async def test_html_is_stripped_for_glossary_but_sent_intact_to_llm(self, orchestrator):
        html = "<p>A <b>memory leak</b> causes crashes</p>"
        events, rec = await run(html, "auto", chunks=AUTO_OK)
        assert "- memory leak -> rò rỉ bộ nhớ" in rec["calls"][0]["system"]
        assert rec["calls"][0]["user"] == html

    @pytest.mark.asyncio
    async def test_markup_only_input_is_not_sent_to_llm(self, orchestrator):
        events, rec = await run("<img src='a.png'><br>", "auto")
        assert rec["calls"] == []
        assert joined(events) == "<img src='a.png'><br>"


class TestFailures:
    @pytest.mark.asyncio
    async def test_llm_unavailable_falls_back_to_nllb_with_warnings(self, orchestrator):
        events, _ = await run("A memory leak causes crashes", "auto",
                              raise_exc=domain_llm.LLMUnavailable("quota", "groq=quota"))
        assert joined(events) == "Bản dịch NLLB"
        # DOMAIN_SERVICE_ERROR đã hợp nhất vào FALLBACK_NLLB: đúng một banner, không lộ lý do kỹ thuật.
        assert codes(events) == ["FALLBACK_NLLB"]
        assert all_warnings(events)[0]["message"] == MSG_FALLBACK
        severities = {w["code"]: w["severity"] for w in all_warnings(events)}
        assert severities["FALLBACK_NLLB"] == "warning"
        details = event_of(events, "domain")[-1]["domain"]
        assert details["translator"] == "nllb" and details["status"] == "unknown"
        orchestrator.set_cache.assert_not_called()

    @pytest.mark.asyncio
    async def test_manual_domain_llm_unavailable_keeps_selected_domain(self, orchestrator):
        events, _ = await run("A memory leak causes crashes", IT, raise_exc=domain_llm.LLMUnavailable("timeout"))
        details = event_of(events, "domain")[-1]["domain"]
        assert (details["status"], details["domain"], details["translator"]) == ("selected", IT, "nllb")
        assert "FALLBACK_NLLB" in codes(events)

    @pytest.mark.asyncio
    async def test_nllb_failure_too_gives_error_event(self, orchestrator):
        orchestrator.nllb.return_value = None
        events, _ = await run("A memory leak causes crashes", IT, raise_exc=domain_llm.LLMUnavailable("quota"))
        assert events[-1]["code"] == "TRANSLATION_UNAVAILABLE"
        assert events[-1]["error"] == MSG_UNAVAILABLE
        assert joined(events) == ""

    @pytest.mark.asyncio
    async def test_interrupted_stream_keeps_partial_text_and_warns(self, orchestrator):
        events, _ = await run("A memory leak causes crashes", IT, chunks=["Một ", "hai"],
                              raise_after=1, raise_exc=domain_llm.LLMInterrupted("unavailable"))
        assert joined(events) == "Một "
        assert codes(events) == ["TRANSLATION_INTERRUPTED"]
        assert all_warnings(events)[0]["message"] == MSG_INTERRUPTED
        orchestrator.set_cache.assert_not_called()

    @pytest.mark.asyncio
    async def test_interrupted_before_any_text_falls_back_to_nllb(self, orchestrator):
        # Mới nhận header rồi đứt: chưa có chữ nào của bản dịch.
        events, _ = await run("A memory leak causes crashes", "auto", chunks=["DOMAIN: Công nghệ Thông tin (IT) | CONF: 0.9\n---\n", "x"],
                              raise_after=1, raise_exc=domain_llm.LLMInterrupted("timeout"))
        assert joined(events) == "Bản dịch NLLB"
        assert "FALLBACK_NLLB" in codes(events)

    @pytest.mark.asyncio
    async def test_empty_llm_output_falls_back_to_nllb(self, orchestrator):
        events, _ = await run("A memory leak causes crashes", IT, chunks=["   "])
        assert joined(events).strip().endswith("Bản dịch NLLB")
        assert "FALLBACK_NLLB" in codes(events)


class TestCache:
    @pytest.mark.asyncio
    async def test_cache_hit_replays_without_calling_llm(self, orchestrator):
        stored = {
            "text": "Đã lưu",
            "domain": {"status": "detected", "domain": IT, "confidence": 0.97, "method": "llm", "matched_terms": [],
                       "applied_terms": [], "candidates": [], "translator": "llm:groq:m"},
            "warnings": [],
        }
        stream, rec = fake_llm(["không được gọi"])
        with patch("app.services.domain_translation.get_cached_domain_result", return_value=stored), \
             patch("app.services.domain_translation.domain_llm.stream_llm", stream):
            result = await collect_domain_translation("A memory leak causes crashes", "en", "vi", "auto")
        assert result["cached"] is True and result["text"] == "Đã lưu"
        assert result["domain"]["domain"] == IT
        assert result["warnings"] == []
        assert rec["calls"] == []

    @pytest.mark.asyncio
    async def test_cache_key_separates_auto_and_manual_modes(self):
        from app.services.domain_translation import _cache_key

        assert _cache_key("en", "vi", "auto", 1, "t") != _cache_key("en", "vi", IT, 1, "t")
        # v4: cache cũ (v3) còn chứa các cảnh báo đã bỏ nên không được dùng lại.
        assert _cache_key("en", "vi", "auto", 1, "t").startswith("domain_v4_")
        assert _cache_key("en", "vi", IT, 1, "t") != _cache_key("en", "vi", IT, 2, "t")


class TestCollect:
    @pytest.mark.asyncio
    async def test_collect_gathers_text_domain_and_warnings(self, orchestrator):
        stream, _ = fake_llm(AUTO_OK)
        with patch("app.services.domain_translation.domain_llm.stream_llm", stream):
            result = await collect_domain_translation("A memory leak causes crashes", "en", "vi", "auto")
        assert result["text"] == "Một rò rỉ bộ nhớ."
        assert result["domain"]["domain"] == IT
        assert result["error"] is None and result["cached"] is False


class TestBadTranslationGuard:
    SRC = "The tenant must give written notice to the landlord before terminating the lease agreement."

    @pytest.mark.asyncio
    async def test_copied_source_is_reset_and_replaced_by_nllb(self, orchestrator):
        events, _ = await run(self.SRC, "auto", chunks=["DOMAIN: unknown | CONF: 0.5\n---\n", self.SRC])
        assert any(e.get("event") == "reset" for e in events)
        # Sau reset chỉ còn bản dịch NLLB.
        after_reset = events[next(i for i, e in enumerate(events) if e.get("event") == "reset"):]
        assert "".join(e["text"] for e in after_reset if "text" in e) == "Bản dịch NLLB"
        assert codes(events) == ["FALLBACK_NLLB"]
        orchestrator.set_cache.assert_not_called()

    @pytest.mark.asyncio
    async def test_dashes_only_output_is_rejected(self, orchestrator):
        events, _ = await run(self.SRC, "auto", chunks=["DOMAIN: unknown | CONF: 0.5\n---\n---"])
        assert joined(events) == "Bản dịch NLLB"
        assert "FALLBACK_NLLB" in codes(events)

    @pytest.mark.asyncio
    async def test_collect_applies_reset(self, orchestrator):
        stream, _ = fake_llm(["DOMAIN: unknown | CONF: 0.5\n---\n", self.SRC])
        with patch("app.services.domain_translation.domain_llm.stream_llm", stream):
            result = await collect_domain_translation(self.SRC, "en", "vi", "auto")
        assert result["text"] == "Bản dịch NLLB"

    def test_short_or_name_like_input_is_not_flagged(self):
        from app.services.domain_translation import is_untranslated

        assert not is_untranslated("iPhone 15", "iPhone 15", "en", "vi")
        assert not is_untranslated("Python 3.11 release", "Python 3.11 release", "en", "vi")
        assert is_untranslated("a b c d e", "a b c d e", "en", "vi")
        assert not is_untranslated("a b c d e", "a b c d e", "en", "en")
        assert is_untranslated("hello", "", "en", "vi")
        assert not is_untranslated(self.SRC, "Người thuê nhà phải báo trước bằng văn bản cho chủ nhà.", "en", "vi")
