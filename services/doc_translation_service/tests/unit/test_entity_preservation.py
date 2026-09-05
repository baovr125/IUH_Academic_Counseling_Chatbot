import pytest
from app.services.ollama_translator import SYSTEM_TRANSLATION_PROMPT
from app.services.docx_pptx_service import translate_single_text
from unittest.mock import patch, MagicMock


def test_system_translation_prompt_contains_proper_noun_rules():
    assert "BẢO TOÀN TÊN TÁC GIẢ & TÊN RIÊNG" in SYSTEM_TRANSLATION_PROMPT
    assert "BẢO TOÀN TÊN TRƯỜNG, VIỆN NGHIÊN CỨU & CƠ QUAN" in SYSTEM_TRANSLATION_PROMPT
    assert "BẢO TOÀN ĐỊA DANH & ĐỊA ĐIỂM" in SYSTEM_TRANSLATION_PROMPT
    assert "BẢO TOÀN TÊN BỘ DỮ LIỆU, MÔ HÌNH" in SYSTEM_TRANSLATION_PROMPT
    assert "BẢO TOÀN TRÍCH DẪN KHOA HỌC" in SYSTEM_TRANSLATION_PROMPT
    assert "(Tác_giả et al., Năm)" in SYSTEM_TRANSLATION_PROMPT


def test_translate_single_text_passes_system_instruction():
    with patch("app.services.docx_pptx_service.call_ollama_generate") as mock_ollama:
        mock_ollama.return_value = "Kiến trúc Transformer"
        res = translate_single_text("Transformer Architecture", source_lang="en", target_lang="vi")
        assert res == "Kiến trúc Transformer"
        mock_ollama.assert_called_once()
        _, kwargs = mock_ollama.call_args
        assert "system_instruction" in kwargs
        assert "BẢO TOÀN TÊN TÁC GIẢ & TÊN RIÊNG" in kwargs["system_instruction"]
