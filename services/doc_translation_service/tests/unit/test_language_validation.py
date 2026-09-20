import pytest
from app.services.ollama_translator import contains_untranslated_foreign_scripts

def test_valid_vietnamese():
    assert contains_untranslated_foreign_scripts("Đây là bản dịch tiếng Việt hợp lệ.", "vi") == False

def test_spanish_hallucination():
    text = "Vacunas son necesarios para prevenir la enfermedad por coronavirus 2019."
    # Since langdetect should catch this, it should return True (contains foreign scripts)
    assert contains_untranslated_foreign_scripts(text, "vi") == True

def test_portuguese_hallucination():
    text = "A capacidade de comunicar na linguagem natural (ou seja, abstração)."
    assert contains_untranslated_foreign_scripts(text, "vi") == True

def test_english_technical_terms():
    text = "Mô hình sử dụng Scaled Dot-Product Attention và Residual Dropout."
    # English terms inside Vietnamese sentence should be valid
    assert contains_untranslated_foreign_scripts(text, "vi") == False

def test_short_text():
    text = "Residual Dropout"
    # Too short to detect language accurately, should pass
    assert contains_untranslated_foreign_scripts(text, "vi") == False
