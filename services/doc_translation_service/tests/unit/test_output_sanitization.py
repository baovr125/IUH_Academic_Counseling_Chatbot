import pytest
from app.services.ollama_translator import sanitize_translation_output

def test_sanitize_translation_output_normal():
    text = "Đây là văn bản bình thường."
    assert sanitize_translation_output(text) == text

def test_sanitize_translation_output_preamble():
    text = "Dưới đây là bản dịch:\n\nNội dung chính."
    assert sanitize_translation_output(text) == "Nội dung chính."

def test_sanitize_translation_output_prompt_leakage():
    text = "userPlease try again\nNội dung chính."
    assert sanitize_translation_output(text) == "Nội dung chính."

    text = "The previous response was cut off. Please continue.\nNội dung chính."
    assert sanitize_translation_output(text) == "Nội dung chính."
    
    text = "Please continue the translation\nNội dung chính."
    assert sanitize_translation_output(text) == "Nội dung chính."

def test_sanitize_translation_output_json_noise():
    text = "Nội dung chính.\n{\"}{\"}{\"}{\"}"
    assert sanitize_translation_output(text) == "Nội dung chính."
