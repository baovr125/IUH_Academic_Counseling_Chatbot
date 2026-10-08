import pytest
from fastapi import HTTPException
from app.services.translation_service import detect_source_language

# Bỏ qua khởi tạo model thật bằng cách mock ngay khi import (cho fasttext)
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def mock_fasttext():
    with patch("app.services.fasttext_detector.fasttext_detect") as mock_ft:
        # Giả lập fasttext luôn trả về (None, 0.0) để test luồng Lingua (fallback)
        mock_ft.return_value = (None, 0.0)
        yield mock_ft

# Nhóm 1: Happy path
def test_detect_english():
    assert detect_source_language("Machine learning is transforming healthcare") == "en"

def test_detect_vietnamese():
    assert detect_source_language("Trí tuệ nhân tạo đang thay đổi giáo dục") == "vi"

def test_detect_german():
    assert detect_source_language("Ich studiere Informatik an der Universität") == "de"

def test_detect_chinese():
    assert detect_source_language("人工智能正在改变教育") == "zh"

def test_detect_japanese():
    assert detect_source_language("機械学習はヘルスケアを変革している") == "ja"

def test_detect_korean():
    assert detect_source_language("기계 학습은 의료를 변화시키고 있다") == "ko"

def test_detect_french():
    assert detect_source_language("L'intelligence artificielle transforme l'éducation") == "fr"

def test_detect_spanish():
    assert detect_source_language("La inteligencia artificial está cambiando la educación") == "es"

def test_detect_russian():
    assert detect_source_language("Машинное обучение трансформирует здравоохранение") == "ru"

def test_detect_thai():
    assert detect_source_language("ปัญญาประดิษฐ์กำลังเปลี่ยนแปลงการศึกษา") == "th"

# Nhóm 2: Edge cases
def test_detect_html_stripped():
    assert detect_source_language("<b>Machine learning is great</b>") == "en"

def test_detect_short_ambiguous_raises():
    with pytest.raises(HTTPException) as excinfo:
        detect_source_language("ok")
    assert excinfo.value.status_code == 400

def test_detect_empty_string_raises():
    with pytest.raises(HTTPException) as excinfo:
        detect_source_language("   ")
    assert excinfo.value.status_code == 400

def test_detect_emoji_only_raises():
    with pytest.raises(HTTPException) as excinfo:
        detect_source_language("😊👍🎉")
    assert excinfo.value.status_code == 400

def test_detect_german_markers():
    assert detect_source_language("Ich bin da") == "de"

def test_detect_french_markers():
    assert detect_source_language("je suis ici") == "fr"

def test_detect_spanish_markers():
    assert detect_source_language("yo estoy aquí") == "es"

def test_detect_mixed_script():
    lang = detect_source_language("Hello こんにちは")
    assert lang in ["en", "ja"]

# Nhóm 3: Uncertainty handling
def test_low_confidence_rejects():
    with patch("app.services.translation_service._get_language_detector") as mock_detector_builder:
        mock_detector = MagicMock()
        mock_value = MagicMock()
        mock_value.language = "en"
        mock_value.value = 0.40 # Below 0.45
        mock_detector.compute_language_confidence_values.return_value = [mock_value]
        mock_detector_builder.return_value = mock_detector
        
        with pytest.raises(HTTPException) as excinfo:
            detect_source_language("some text")
        assert excinfo.value.status_code == 400

def test_fasttext_fast_path():
    with patch("app.services.fasttext_detector.fasttext_detect") as mock_ft:
        # Giả lập fasttext trả về high confidence
        mock_ft.return_value = ("fr", 0.95)
        # Sẽ không cần qua Lingua
        assert detect_source_language("bonjour") == "fr"
