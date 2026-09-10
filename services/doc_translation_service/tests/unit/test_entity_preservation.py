import pytest
from app.services.ollama_translator import SYSTEM_TRANSLATION_PROMPT
from app.services.docx_pptx_service import translate_single_text
from unittest.mock import patch


def test_system_translation_prompt_contains_proper_noun_rules():
    assert "TARGET LANGUAGE: VIETNAMESE (TIẾNG VIỆT)" in SYSTEM_TRANSLATION_PROMPT
    assert "Absolutely NO Chinese characters" in SYSTEM_TRANSLATION_PROMPT
    assert "Translate ALL headings, section titles, and table contents" in SYSTEM_TRANSLATION_PROMPT
    assert "preserve all placeholders like {v0}, {v1}, {v2}" in SYSTEM_TRANSLATION_PROMPT


def test_translate_single_text_passes_system_instruction():
    with patch("app.services.docx_pptx_service.call_ollama_generate") as mock_ollama:
        mock_ollama.return_value = "Kiến trúc Transformer"
        res = translate_single_text("Transformer Architecture", source_lang="en", target_lang="vi")
        assert res == "Kiến trúc Transformer"
        mock_ollama.assert_called_once()
        _, kwargs = mock_ollama.call_args
        assert "system_instruction" in kwargs
        assert "TARGET LANGUAGE: VIETNAMESE" in kwargs["system_instruction"]
