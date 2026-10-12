"""
tests/integration/test_domain_endpoints.py
==========================================
Hợp đồng /text và /stream ở chế độ chuyên ngành (manual và auto), mock LLM/NLLB/Redis/từ điển.

- /stream: detection -> resolved_source_lang -> domain -> text... -> warnings.
- /text: trả `domain` (DomainDetails) và `warnings` (có cấu trúc) cùng trường `warning` chuỗi cũ.
- Hai endpoint đưa ra cùng domain/cảnh báo cho cùng đầu vào.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.domain_index import DomainIndex
from app.services import domain_llm

IT = "Công nghệ Thông tin (IT)"
ROWS = [
    {"domain": IT, "word": "memory leak", "translation": "rò rỉ bộ nhớ"},
    {"domain": "Y khoa / Sức khỏe", "word": "stock", "translation": "kho thuốc"},
    {"domain": "Kinh tế / Tài chính", "word": "stock", "translation": "cổ phiếu"},
]
TEXT = "A memory leak causes crashes in production"
AUTO_STREAM = ["DOMAIN: Công nghệ Thông tin (IT) | CONF: 0.97\n---\n", "Rò rỉ bộ nhớ ", "gây sập hệ thống."]


def parse_sse(response_text):
    events = []
    for line in response_text.splitlines():
        line = line.strip()
        if line.startswith("data: ") and line[6:].strip():
            events.append(json.loads(line[6:]))
    return events


def stream(client, **payload):
    body = {"target_lang": "vi", "source_lang": "en", **payload}
    with client.stream("POST", "/api/v1/translate/stream", json=body) as response:
        text = "".join(response.iter_text())
    return response.status_code, parse_sse(text)


def fake_llm(chunks):
    async def stream_llm(system, user, temperature=0.2):
        yield ("provider", "groq:test")
        for c in chunks:
            yield ("chunk", c)

    return stream_llm


@pytest.fixture
def domain_backend():
    index = DomainIndex.build(ROWS)
    domain_llm.reset_cooldowns()
    with patch("app.services.domain_translation.get_index", AsyncMock(return_value=index)), \
         patch("app.services.domain_translation.get_cached_domain_result", return_value=None), \
         patch("app.services.domain_translation.set_cached_domain_result"), \
         patch("app.services.domain_translation.get_domain_version", return_value=1), \
         patch("app.services.domain_translation._nllb", AsyncMock(return_value="Bản dịch NLLB")):
        yield
    domain_llm.reset_cooldowns()


class TestStreamDomain:
    def test_auto_event_order_and_payload(self, client, domain_backend):
        with patch("app.services.domain_translation.domain_llm.stream_llm", fake_llm(AUTO_STREAM)):
            status, events = stream(client, text=TEXT, domain="auto")
        assert status == 200
        assert events[0]["event"] == "detection"
        assert events[1] == {"resolved_source_lang": "en"}
        kinds = [("domain" if e.get("event") == "domain" else "text" if "text" in e else "warnings" if "warnings" in e else "other") for e in events[2:]]
        assert kinds[0] == "domain" and "text" in kinds
        domain_event = next(e for e in events if e.get("event") == "domain")
        assert domain_event["domain"]["status"] == "detected" and domain_event["domain"]["domain"] == IT
        assert "".join(e["text"] for e in events if "text" in e) == "Rò rỉ bộ nhớ gây sập hệ thống."
        # Event cuối của domain có applied_terms.
        last = [e for e in events if e.get("event") == "domain"][-1]
        assert last["domain"]["applied_terms"] == ["memory leak"]

    def test_manual_domain_streams_llm_text(self, client, domain_backend):
        with patch("app.services.domain_translation.domain_llm.stream_llm", fake_llm(["Rò rỉ bộ nhớ ", "gây sập."])):
            status, events = stream(client, text=TEXT, domain=IT)
        assert status == 200
        domain_event = next(e for e in events if e.get("event") == "domain")
        assert domain_event["domain"]["status"] == "selected"
        assert "".join(e["text"] for e in events if "text" in e) == "Rò rỉ bộ nhớ gây sập."

    def test_ambiguous_short_term_has_candidates_and_no_text(self, client, domain_backend):
        status, events = stream(client, text="stock", domain="auto")
        domain_event = next(e for e in events if e.get("event") == "domain")["domain"]
        assert domain_event["status"] == "ambiguous"
        assert {c["domain"] for c in domain_event["candidates"]} == {"Y khoa / Sức khỏe", "Kinh tế / Tài chính"}
        assert not any("text" in e for e in events)
        assert any(w["code"] == "DOMAIN_AMBIGUOUS" for e in events for w in e.get("warnings", []))

    def test_llm_down_streams_nllb_with_structured_warnings(self, client, domain_backend):
        async def broken(system, user, temperature=0.2):
            raise domain_llm.LLMUnavailable("quota")
            yield  # pragma: no cover

        with patch("app.services.domain_translation.domain_llm.stream_llm", broken):
            status, events = stream(client, text=TEXT, domain="auto")
        assert "".join(e["text"] for e in events if "text" in e) == "Bản dịch NLLB"
        codes = [w["code"] for e in events for w in e.get("warnings", [])]
        assert codes == ["FALLBACK_NLLB"]

    def test_language_stop_still_precedes_domain_logic(self, client, domain_backend):
        status, events = stream(client, text="ok", source_lang="auto", domain="auto")
        assert events[0]["event"] == "detection"
        if events[0]["detection"]["status"] != "detected":
            assert not any(e.get("event") == "domain" for e in events)
            assert any("code" in e for e in events)


class TestTextDomain:
    def post(self, client, **payload):
        body = {"source_lang": "en", "target_lang": "vi", **payload}
        return client.post("/api/v1/translate/text", json=body)

    def test_auto_unknown_returns_domain_without_warnings(self, client, domain_backend):
        with patch("app.services.domain_translation.domain_llm.stream_llm", fake_llm(["DOMAIN: unknown | CONF: 0.9\n---\n", "Chúng tôi đi dạo trên bãi biển bên bờ sông."])):
            res = self.post(client, text="We walked along the beach near the river", domain="auto")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["translated_text"] == "Chúng tôi đi dạo trên bãi biển bên bờ sông."
        assert data["domain"]["status"] == "unknown"
        # Giống nhận diện ngôn ngữ: kết quả lĩnh vực chỉ nằm ở `domain`, không thành cảnh báo.
        assert data["warnings"] == []
        assert data["warning"] is None

    def test_fallback_sets_legacy_warning_string(self, client, domain_backend):
        async def broken(system, user, temperature=0.2):
            raise domain_llm.LLMUnavailable("quota")
            yield  # pragma: no cover

        with patch("app.services.domain_translation.domain_llm.stream_llm", broken):
            data = self.post(client, text=TEXT, domain="auto").json()["data"]
        assert [w["code"] for w in data["warnings"]] == ["FALLBACK_NLLB"]
        # Trường chuỗi cũ vẫn có để tương thích ngược.
        assert data["warning"] == data["warnings"][0]["message"]

    def test_manual_exact_hit_uses_dictionary(self, client, domain_backend):
        res = self.post(client, text="memory leak", domain=IT)
        data = res.json()["data"]
        assert data["translated_text"] == "rò rỉ bộ nhớ"
        assert data["domain"]["translator"] == "dictionary" and data["warnings"] == []

    def test_text_and_stream_agree_on_domain_and_warnings(self, client, domain_backend):
        with patch("app.services.domain_translation.domain_llm.stream_llm", fake_llm(AUTO_STREAM)):
            text_data = self.post(client, text=TEXT, domain="auto").json()["data"]
            _, events = stream(client, text=TEXT, domain="auto")
        stream_domain = [e for e in events if e.get("event") == "domain"][-1]["domain"]
        stream_warnings = [w["code"] for e in events for w in e.get("warnings", [])]
        assert text_data["domain"]["domain"] == stream_domain["domain"]
        assert text_data["domain"]["status"] == stream_domain["status"]
        assert [w["code"] for w in text_data["warnings"]] == stream_warnings

    def test_all_providers_down_and_nllb_down_is_503(self, client, domain_backend):
        async def broken(system, user, temperature=0.2):
            raise domain_llm.LLMUnavailable("quota")
            yield  # pragma: no cover

        with patch("app.services.domain_translation.domain_llm.stream_llm", broken), \
             patch("app.services.domain_translation._nllb", AsyncMock(return_value=None)):
            res = self.post(client, text=TEXT, domain=IT)
        assert res.status_code == 503

    def test_default_translation_mode_is_unchanged(self, client):
        res = self.post(client, text="Hello world", domain="")
        # Không có provider ở môi trường test: chỉ cần chứng minh KHÔNG đi vào luồng chuyên ngành.
        assert res.status_code in (200, 500, 503)
        if res.status_code == 200:
            assert res.json()["data"].get("domain") is None
