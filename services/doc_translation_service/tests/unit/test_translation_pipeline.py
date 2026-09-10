import pytest
from unittest.mock import patch, MagicMock
from app.services.ollama_translator import OllamaPDFTranslator

class TestOllamaPDFTranslator:
    def test_translate_calls_ollama_generate_and_returns_sanitized_output(self):
        translator = OllamaPDFTranslator()
        
        with patch("app.services.ollama_translator.call_ollama_generate") as mock_generate, \
             patch("app.services.ollama_translator.sanitize_translation_output") as mock_sanitize, \
             patch("app.services.ollama_translator.contains_untranslated_foreign_scripts", return_value=False):
             
            mock_generate.return_value = "raw translated text"
            mock_sanitize.return_value = "clean translated text"
            
            result = translator.translate("Hello World")
            
            assert result == "clean translated text"
            mock_generate.assert_called_once()
            args, kwargs = mock_generate.call_args
            assert "Hello World" in args[0]
            assert "qwen2.5:14b" == kwargs.get("model", "qwen2.5:14b")
            
    def test_translate_retries_with_strict_prompt_when_chinese_characters_detected(self):
        translator = OllamaPDFTranslator()
        
        with patch("app.services.ollama_translator.call_ollama_generate") as mock_generate, \
             patch("app.services.ollama_translator.sanitize_translation_output", side_effect=lambda x: x):
             
            # Lần 1 trả về text có tiếng Trung, lần 2 trả về text sạch
            mock_generate.side_effect = ["Bản dịch có 中文", "Bản dịch sạch không có Hán tự"]
            
            result = translator.translate("Translate this")
            
            assert result == "Bản dịch sạch không có Hán tự"
            assert mock_generate.call_count == 2
            
            # Lần gọi thứ 2 phải có system instruction strict hơn
            second_call_kwargs = mock_generate.call_args_list[1][0]
            assert "KHÔNG xuất ký tự Hán/Trung Quốc" in second_call_kwargs[1]
            
    def test_translate_falls_back_to_groq_when_ollama_fails(self):
        translator = OllamaPDFTranslator()
        
        with patch("app.services.ollama_translator.call_ollama_generate", side_effect=Exception("Ollama down")), \
             patch("app.services.ollama_translator._execute_groq_fallback") as mock_groq, \
             patch("app.services.ollama_translator.sanitize_translation_output", return_value="Groq fallback text"):
             
            mock_groq.return_value = "Groq fallback text raw"
            
            result = translator.translate("Translate this via fallback")
            
            assert result == "Groq fallback text"
            mock_groq.assert_called_once()
            
    def test_translate_returns_original_text_when_all_fallbacks_fail(self):
        translator = OllamaPDFTranslator()
        
        with patch("app.services.ollama_translator.call_ollama_generate", side_effect=Exception("Ollama down")), \
             patch("app.services.ollama_translator._execute_groq_fallback", side_effect=Exception("Groq down")):
             
            result = translator.translate("Translate this but everything fails")
            
            assert result == "Translate this but everything fails"
