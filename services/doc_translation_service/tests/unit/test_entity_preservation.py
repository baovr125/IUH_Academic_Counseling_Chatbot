from app.services.ollama_translator import get_system_prompt
from app.services.docx_pptx_service import translate_single_text
from unittest.mock import patch


def test_system_prompt_contains_translation_rules():
    prompt = get_system_prompt("en", "vi", has_placeholders=True)
    assert "TARGET LANGUAGE: Vietnamese (Tiếng Việt)" in prompt
    assert "Do not output characters of other languages" in prompt
    assert "Translate ALL headings, section titles, and table contents" in prompt
    assert "preserve all placeholders like {v0}, {v1}, {v2}" in prompt


def test_system_prompt_omits_placeholder_rule_by_default():
    assert "{v0}" not in get_system_prompt("en", "vi")


def test_translate_single_text_passes_system_instruction():
    with patch("app.services.docx_pptx_service.call_ollama_generate") as mock_ollama:
        mock_ollama.return_value = "Kiến trúc Transformer"
        res = translate_single_text("Transformer Architecture", source_lang="en", target_lang="vi")
        assert res == "Kiến trúc Transformer"
        mock_ollama.assert_called_once()
        _, kwargs = mock_ollama.call_args
        assert "system_instruction" in kwargs
        assert "TARGET LANGUAGE: Vietnamese" in kwargs["system_instruction"]
