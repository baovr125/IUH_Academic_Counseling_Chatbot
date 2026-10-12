"""
tests/integration/test_detection_stream_endpoint.py
====================================================
SSE /api/v1/translate/stream với chính sách nhận diện mới:

  - Luôn phát event `detection` đầu tiên (đủ status/confidence/margin/engine/candidates).
  - Chỉ khi status="detected" mới phát `resolved_source_lang` và đi tiếp vào tầng dịch.
  - Các trạng thái còn lại phát event `error` kèm `code` rồi kết thúc, không có event `text`.
  - Cùng một đầu vào phải cho cùng status/mã lỗi ở /text và /stream.
"""
import json
from unittest.mock import patch

import pytest

from app.schemas.translation import DetectionCandidate, LanguageDetectionDetails
from app.services.fasttext_detector import _get_fasttext_model

needs_models = pytest.mark.skipif(_get_fasttext_model() is None, reason="Cần model fastText lid.176")

ITALIAN = "La intelligenza artificiale sta cambiando il modo in cui studiamo ogni giorno"


def parse_sse_events(response_text: str):
    events = []
    for line in response_text.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            payload = line[len("data: "):].strip()
            if payload:
                try:
                    events.append(json.loads(payload))
                except json.JSONDecodeError:
                    pass
    return events


def stream(client, **payload):
    body = {"target_lang": "vi", **payload}
    with client.stream("POST", "/api/v1/translate/stream", json=body) as response:
        text = "".join(response.iter_text())
    return response.status_code, parse_sse_events(text)


@pytest.fixture
def no_providers():
    """Không có NLLB/Groq/Gemini: sau khi nhận diện thành công stream kết thúc bằng event error của tầng dịch."""
    with patch("app.services.llm_service.get_nllb_translator", return_value=(None, None)), \
         patch("app.services.llm_service.get_groq_client", return_value=None), \
         patch("app.services.llm_service.get_gemini_client", return_value=None):
        yield


class TestStreamDetectionPolicy:

    @needs_models
    def test_detected_language_emits_detection_then_resolved_language(self, client, no_providers):
        status, events = stream(client, text="Trí tuệ nhân tạo đang thay đổi giáo dục trên toàn thế giới",
                                source_lang="auto", target_lang="en")
        assert status == 200
        assert events[0]["event"] == "detection"
        detection = events[0]["detection"]
        assert detection["status"] == "detected" and detection["resolved_source_lang"] == "vi"
        for key in ("confidence", "margin", "engine", "candidates"):
            assert key in detection
        assert events[1] == {"resolved_source_lang": "vi"}

    def test_manual_language_emits_manual_detection(self, client, no_providers):
        _, events = stream(client, text="Hello world", source_lang="en")
        assert events[0]["detection"]["engine"] == "manual"
        assert events[1] == {"resolved_source_lang": "en"}

    @needs_models
    def test_unsupported_language_emits_error_with_code_and_no_text(self, client, no_providers):
        status, events = stream(client, text=ITALIAN, source_lang="auto")
        assert status == 200
        assert events[0]["detection"]["status"] == "unsupported"
        assert events[0]["detection"]["detected_language"] == "it"
        error = [e for e in events if "error" in e]
        assert len(error) == 1 and error[0]["code"] == "LANG_UNSUPPORTED"
        assert not [e for e in events if "text" in e or "resolved_source_lang" in e]
        assert events.index(error[0]) == len(events) - 1

    def test_uncertain_language_emits_error_and_candidates(self, client, no_providers):
        uncertain = LanguageDetectionDetails(
            status="uncertain", confidence=0.4, margin=0.05, engine="fusion", reason="short_input",
            message="Chưa đủ thông tin để xác định chắc chắn ngôn ngữ. Hãy chọn ngôn ngữ nguồn thủ công.",
            candidates=[DetectionCandidate(language="en", confidence=0.4)],
        )
        with patch("app.services.language_detection.detect_language_detailed", return_value=uncertain):
            _, events = stream(client, text="ambiguous", source_lang="auto")
        assert events[0]["detection"]["status"] == "uncertain"
        assert events[0]["detection"]["candidates"][0]["language"] == "en"
        assert events[-1]["code"] == "LANG_UNCERTAIN"
        assert not [e for e in events if "text" in e]

    def test_invalid_input_emits_error(self, client, no_providers):
        _, events = stream(client, text="12345 67890", source_lang="auto")
        assert events[0]["detection"]["status"] == "invalid_input"
        assert events[-1]["code"] == "INVALID_INPUT"

    def test_hint_is_forwarded_to_the_resolver(self, client, no_providers):
        hinted = LanguageDetectionDetails(
            resolved_source_lang="en", status="detected", confidence=0.6, margin=0.2, engine="hint",
            candidates=[DetectionCandidate(language="en", confidence=0.2)],
        )
        with patch("app.services.language_detection.detect_language_detailed", return_value=hinted) as mocked:
            _, events = stream(client, text="Hello", source_lang="auto", source_lang_hint="en")
        assert mocked.call_args.args == ("Hello", "en")
        assert events[1] == {"resolved_source_lang": "en"}


class TestTextAndStreamAgree:

    @needs_models
    @pytest.mark.parametrize(
        "text,expected_status,expected_code",
        [
            (ITALIAN, "unsupported", "LANG_UNSUPPORTED"),
            ("12345 67890", "invalid_input", "INVALID_INPUT"),
            ("https://openai.com/research/gpt4", "unknown", "LANG_UNKNOWN"),
        ],
    )
    def test_same_input_same_decision(self, client, no_providers, text, expected_status, expected_code):
        text_response = client.post("/api/v1/translate/text", json={"text": text, "source_lang": "auto", "target_lang": "vi"})
        _, events = stream(client, text=text, source_lang="auto")

        text_error = text_response.json()["error"]
        assert text_error["code"] == expected_code == events[-1]["code"]
        assert text_error["detection"]["status"] == expected_status == events[0]["detection"]["status"]
        assert text_error["detection"] == events[0]["detection"]
        assert text_response.json()["detail"] == events[-1]["error"]
