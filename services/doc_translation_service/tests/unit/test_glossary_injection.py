import pytest
from app.services.ollama_translator import OllamaPDFTranslator

def test_glossary_exact_match():
    glossary = {
        "Attention": "Cơ chế chú ý",
        "Scaled Dot-Product Attention": "Chú ý tích vô hướng có tỉ lệ",
        "Residual Dropout": "Dropout phần dư"
    }
    translator = OllamaPDFTranslator(lang_in="en", lang_out="vi", glossary=glossary)
    
    text = "The model uses Scaled Dot-Product Attention."
    hint = translator._build_glossary_hint(text)
    
    assert "Scaled Dot-Product Attention" in hint
    assert "Residual Dropout" not in hint

def test_glossary_case_insensitive():
    glossary = {
        "Attention": "Cơ chế chú ý"
    }
    translator = OllamaPDFTranslator(lang_in="en", lang_out="vi", glossary=glossary)
    
    text = "The attention mechanism is crucial."
    hint = translator._build_glossary_hint(text)
    
    assert "Attention" in hint
