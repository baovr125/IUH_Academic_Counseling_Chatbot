"""
tests/integration/test_detection_text_endpoint.py
==================================================
REST /api/v1/translate/text và /api/v1/translate/detect với hợp đồng nhận diện ngôn ngữ mới:

  - Chỉ `detected` mới được dịch; uncertain/unsupported/unknown/invalid_input trả lỗi có cấu trúc
    {ok:false, detail, error:{code, message, detection}} và KHÔNG gọi tầng dịch.
  - /detect luôn trả chi tiết chuẩn hóa (kể cả uncertain/unsupported) với HTTP 200.
  - source_lang_hint được chuyển xuống tầng dịch.
"""
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.translation import DetectionCandidate, LanguageDetectionDetails
from app.services.fasttext_detector import _get_fasttext_model

needs_models = pytest.mark.skipif(_get_fasttext_model() is None, reason="Cần model fastText lid.176")

ITALIAN = "La intelligenza artificiale sta cambiando il modo in cui studiamo ogni giorno"


def uncertain_details():
    return LanguageDetectionDetails(
        status="uncertain", confidence=0.4, margin=0.05, engine="fusion", reason="short_input",
        message="Chưa đủ thông tin để xác định chắc chắn ngôn ngữ. Hãy chọn ngôn ngữ nguồn thủ công.",
        candidates=[DetectionCandidate(language="en", confidence=0.4), DetectionCandidate(language="fr", confidence=0.3)],
    )


class TestTextEndpoint:

    def test_explicit_language_returns_manual_detection(self, client):
        manual = LanguageDetectionDetails(
            resolved_source_lang="en", status="detected", confidence=1.0, margin=1.0, engine="manual",
            candidates=[DetectionCandidate(language="en", confidence=1.0)],
        )
        with patch("app.routers.translation.translate_text", new_callable=AsyncMock) as mock_trans:
            mock_trans.return_value = ("Xin chào", False, 10.0, None, "en", manual)
            res = client.post("/api/v1/translate/text", json={"text": "Hello", "source_lang": "en", "target_lang": "vi"})
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["resolved_source_lang"] == "en"
        assert data["detection"]["engine"] == "manual"

    def test_auto_detected_contract_and_hint_forwarding(self, client):
        detected = LanguageDetectionDetails(
            resolved_source_lang="vi", status="detected", confidence=0.985, margin=0.92, engine="fasttext",
            candidates=[DetectionCandidate(language="vi", confidence=0.985)],
        )
        with patch("app.routers.translation.translate_text", new_callable=AsyncMock) as mock_trans:
            mock_trans.return_value = ("Hello world", False, 25.0, None, "vi", detected)
            res = client.post("/api/v1/translate/text", json={
                "text": "Xin chào thế giới", "source_lang": "auto", "target_lang": "en", "source_lang_hint": "vi",
            })
        assert res.status_code == 200
        payload = res.json()["data"]
        assert payload["resolved_source_lang"] == "vi"
        assert payload["detection"]["status"] == "detected"
        assert payload["detection"]["candidates"][0]["language"] == "vi"
        assert mock_trans.call_args.kwargs["source_lang_hint"] == "vi"

    def test_invalid_hint_is_rejected_by_schema(self, client):
        res = client.post("/api/v1/translate/text", json={
            "text": "Hello", "source_lang": "auto", "target_lang": "vi", "source_lang_hint": "xx",
        })
        assert res.status_code == 422

    @needs_models
    def test_unsupported_language_stops_with_structured_error(self, client):
        with patch("app.services.translation_service.run_nllb_only", new_callable=AsyncMock) as nllb:
            res = client.post("/api/v1/translate/text", json={"text": ITALIAN, "source_lang": "auto", "target_lang": "vi"})
        assert res.status_code == 400
        body = res.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "LANG_UNSUPPORTED"
        assert body["detail"] == body["error"]["message"]
        detection = body["error"]["detection"]
        assert detection["status"] == "unsupported" and detection["detected_language"] == "it"
        assert detection["resolved_source_lang"] is None
        nllb.assert_not_called()

    def test_uncertain_language_stops_and_offers_candidates(self, client):
        with patch("app.services.language_detection.detect_language_detailed", return_value=uncertain_details()):
            res = client.post("/api/v1/translate/text", json={"text": "ambiguous", "source_lang": "auto", "target_lang": "vi"})
        assert res.status_code == 400
        error = res.json()["error"]
        assert error["code"] == "LANG_UNCERTAIN"
        assert [c["language"] for c in error["detection"]["candidates"]] == ["en", "fr"]

    def test_text_without_letters_returns_invalid_input(self, client):
        res = client.post("/api/v1/translate/text", json={"text": "12345 67890", "source_lang": "auto", "target_lang": "vi"})
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "INVALID_INPUT"
        assert "ký tự chữ" in res.json()["detail"]

    def test_url_only_text_returns_unknown(self, client):
        res = client.post("/api/v1/translate/text", json={
            "text": "https://openai.com/research/gpt4", "source_lang": "auto", "target_lang": "vi"})
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "LANG_UNKNOWN"

    def test_system_error_maps_to_503(self, client):
        broken = LanguageDetectionDetails(status="system_error", engine="none", message="Không thể nhận diện ngôn ngữ lúc này.")
        with patch("app.services.language_detection.detect_language_detailed", return_value=broken):
            res = client.post("/api/v1/translate/text", json={"text": "Hello there", "source_lang": "auto", "target_lang": "vi"})
        assert res.status_code == 503
        assert res.json()["error"]["code"] == "LANG_SYSTEM_ERROR"


class TestDetectEndpoint:

    @needs_models
    def test_detected_language(self, client):
        res = client.post("/api/v1/translate/detect", json={"text": "Trí tuệ nhân tạo đang thay đổi giáo dục trên toàn thế giới"})
        assert res.status_code == 200
        det = res.json()["data"]
        assert res.json()["ok"] is True
        assert det["status"] == "detected" and det["resolved_source_lang"] == "vi"
        assert det["candidates"][0]["language"] == "vi"

    @needs_models
    def test_unsupported_language_is_reported_with_http_200(self, client):
        res = client.post("/api/v1/translate/detect", json={"text": ITALIAN})
        assert res.status_code == 200
        det = res.json()["data"]
        assert det["status"] == "unsupported" and det["detected_language"] == "it"

    def test_uncertain_is_reported_with_http_200(self, client):
        with patch("app.routers.translation.adetect_language_detailed", new_callable=AsyncMock) as mocked:
            mocked.return_value = uncertain_details()
            res = client.post("/api/v1/translate/detect", json={"text": "ok", "source_lang_hint": "en"})
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "uncertain"
        assert mocked.call_args.args == ("ok", "en")

    def test_invalid_input_returns_400(self, client):
        res = client.post("/api/v1/translate/detect", json={"text": "987654321"})
        assert res.status_code == 400

    def test_system_error_returns_503(self, client):
        broken = LanguageDetectionDetails(status="system_error", engine="none", message="Lỗi hệ thống.")
        with patch("app.routers.translation.adetect_language_detailed", new_callable=AsyncMock) as mocked:
            mocked.return_value = broken
            res = client.post("/api/v1/translate/detect", json={"text": "Hello there"})
        assert res.status_code == 503
