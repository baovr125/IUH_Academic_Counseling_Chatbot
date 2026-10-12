"""Hành vi Language Detection với engine THẬT (fastText + Lingua), không mock detector.

Các test này kiểm tra tính chất an toàn của đường nhận diện production (`detect_language_detailed`,
`resolve_source_language`), không phải độ chính xác thống kê (xem evaluation/dev_gate.py cho phần đó).
"""
import pytest

from app.services import language_detection as ld
from app.services.fasttext_detector import _get_fasttext_model

pytestmark = pytest.mark.skipif(
    _get_fasttext_model() is None,
    reason="Cần model fastText lid.176 (chạy download_model.py hoặc đặt FASTTEXT_LID_MODEL).",
)


@pytest.fixture(autouse=True)
def fresh_detector():
    ld.reload_config()
    yield
    ld.reload_config()


def detect(text, hint=None):
    return ld.detect_language_detailed(text, hint)


# --- Ngôn ngữ được hỗ trợ -------------------------------------------------------------------------
SUPPORTED_SAMPLES = [
    ("Machine learning is transforming healthcare around the world", "en"),
    ("Trí tuệ nhân tạo đang thay đổi giáo dục trên toàn thế giới", "vi"),
    ("Ich studiere Informatik an der Universität in Berlin", "de"),
    ("L'intelligence artificielle transforme l'éducation moderne", "fr"),
    ("La inteligencia artificial está cambiando la educación moderna", "es"),
    ("Машинное обучение трансформирует здравоохранение по всему миру", "ru"),
    ("人工智能正在改变教育领域，并提供新的可能性。", "zh"),
    ("機械学習はヘルスケアを変革しています。", "ja"),
    ("기계 학습은 의료를 변화시키고 있습니다.", "ko"),
    ("ปัญญาประดิษฐ์กำลังเปลี่ยนแปลงการศึกษาอย่างรวดเร็ว", "th"),
]


@pytest.mark.parametrize("text,expected", SUPPORTED_SAMPLES)
def test_supported_languages_detected(text, expected):
    result = detect(text)
    assert result.status == "detected"
    assert result.resolved_source_lang == expected
    assert result.candidates and result.candidates[0].language == expected
    assert 0.0 < result.confidence <= 1.0


def test_html_markup_is_ignored():
    assert detect("<p>Machine learning is <b>transforming</b> education worldwide</p>").resolved_source_lang == "en"
    assert detect("<div><h1>Chào mừng bạn đến với trường đại học công nghiệp</h1></div>").resolved_source_lang == "vi"


def test_script_and_style_content_is_not_language_evidence():
    result = detect("<script>var greeting = 'bonjour tout le monde';</script><p>Hello everyone and welcome to class</p>")
    assert result.resolved_source_lang == "en"


def test_all_caps_text_is_normalized():
    assert detect("THIS IS A VERY LOUD SENTENCE WRITTEN ENTIRELY IN CAPITAL LETTERS").resolved_source_lang == "en"


def test_vietnamese_without_diacritics():
    for text in (
        "toi dang hoc lap trinh tai truong dai hoc cong nghiep",
        "hom qua thay giao tra bai kiem tra cho chung toi",
        "em khong hieu bai nay thay oi giai thich lai giup em voi",
    ):
        result = detect(text)
        assert result.status == "detected", text
        assert result.resolved_source_lang == "vi", text


def test_english_with_marker_words_is_not_hijacked():
    for text in (
        "the die is cast and there is no turning back now",
        "please put the empty bottles in the recycling bin outside",
        "my son is here to see the doctor this afternoon",
    ):
        assert detect(text).resolved_source_lang == "en", text


def test_traditional_chinese_without_kana_is_chinese():
    assert detect("很少人能講英語講得比幸子好。").resolved_source_lang == "zh"


def test_japanese_with_embedded_latin_words():
    assert detect("YouTubeが落ちてるんだ。").resolved_source_lang == "ja"


def test_code_switching_vietnamese_english():
    assert detect("Hôm nay tôi có meeting với team về deadline quan trọng").resolved_source_lang == "vi"


@pytest.mark.parametrize("text,expected", [
    ("Bạn đã review pull request chưa, tôi cần merge trước deadline", "vi"),
    ("Mình đang học machine learning và deep learning ở trường", "vi"),
    ("Tôi vừa deploy xong application lên server và fix bug trong database", "vi"),
    ("toi dang hoc machine learning o truong dai hoc", "vi"),
    ("I really love phở and bánh mì when I travel to Vietnam", "en"),
    # Việt có dấu, thuật ngữ Anh chiếm tỉ lệ cao (~40%)
    ("Cần optimize query và cache để giảm latency của API", "vi"),
    ("Em cần submit assignment trước 11pm được không ạ", "vi"),
    ("Anh gửi giúp em file báo cáo qua email nhé", "vi"),
    # Việt không dấu + từ Anh
    ("ban co the review code giup toi khong", "vi"),
    # Anh chủ đạo + từ Việt
    ("My friend said xin chào to everyone at the meeting", "en"),
    # Việt chủ đạo + chuỗi ngôn ngữ khác trong câu
    ("Tôi đang học tiếng Nhật, câu こんにちは nghĩa là xin chào", "vi"),
    ('Từ "bonjour" trong tiếng Pháp có nghĩa là xin chào', "vi"),
])
def test_mixed_language_text_resolves_to_the_dominant_language(text, expected):
    result = detect(text)
    assert result.status == "detected" and result.resolved_source_lang == expected


@pytest.mark.parametrize("text", ["Hôm nay meeting", "Tôi thích coffee", "OK bạn ơi", "deadline là thứ Sáu"])
def test_short_vietnamese_english_mixes_are_never_confidently_wrong(text):
    # Cụm ngắn gần 50-50: được phép abstain, nhưng nếu đã kết luận thì phải là ngôn ngữ chủ đạo hợp lý.
    result = detect(text)
    if result.status == "detected":
        assert result.resolved_source_lang in ("vi", "en")
    else:
        assert result.status == "uncertain" and result.resolved_source_lang is None


def test_default_lingua_mode_is_low_accuracy(monkeypatch):
    monkeypatch.delenv("DETECT_LINGUA_LOW_ACCURACY", raising=False)
    assert ld.DetectionConfig.from_env().lingua_low_accuracy is True
    monkeypatch.setenv("DETECT_LINGUA_LOW_ACCURACY", "0")
    assert ld.DetectionConfig.from_env().lingua_low_accuracy is False


# --- Ngôn ngữ ngoài phạm vi: không được ép vào 10 ngôn ngữ -----------------------------------------
OUT_OF_SCOPE_SAMPLES = [
    ("La intelligenza artificiale sta cambiando il modo in cui studiamo ogni giorno", "it"),
    ("A inteligência artificial está mudando a forma como estudamos todos os dias", "pt"),
    ("Kecerdasan buatan sedang mengubah cara kita belajar dan bekerja setiap hari", ("id", "ms")),  # gần như một ngôn ngữ
    ("Штучний інтелект змінює спосіб, у який ми вчимося та працюємо щодня", "uk"),
    ("الذكاء الاصطناعي يغير الطريقة التي ندرس بها ونعمل كل يوم", "ar"),
    ("Yapay zeka, her gün nasıl öğrendiğimizi ve çalıştığımızı değiştiriyor", "tr"),
]


@pytest.mark.parametrize("text,language", OUT_OF_SCOPE_SAMPLES)
def test_out_of_scope_language_is_reported_unsupported(text, language):
    result = detect(text)
    assert result.status == "unsupported"
    assert result.resolved_source_lang is None
    assert result.detected_language in (language if isinstance(language, tuple) else (language,))
    assert "chưa được hỗ trợ" in result.message


@pytest.mark.parametrize("word", ["ok", "OK", "no", "hi", "ban", "me"])
def test_tiny_words_are_never_decided_on_their_own(word):
    assert detect(word).status != "detected"
    assert detect(word, hint="en").resolved_source_lang in (None, "en")


# --- Không có chữ / không phải ngôn ngữ tự nhiên ---------------------------------------------------
@pytest.mark.parametrize("text", ["   ", "\t\n  \r", "12345 67890", "😊👍🎉🔥", "!!! ??? ... ---"])
def test_inputs_without_letters_are_invalid(text):
    assert detect(text).status == "invalid_input"


@pytest.mark.parametrize("text", ["https://openai.com/research/gpt4", "john.doe@example.com", "www.example.com"])
def test_links_and_emails_are_unknown(text):
    result = detect(text)
    assert result.status == "unknown"
    assert "URL" in result.message


def test_urls_inside_a_sentence_do_not_break_detection():
    result = detect("Visit https://www.example.com/docs for the full documentation and many examples")
    assert result.resolved_source_lang == "en"


# --- Văn bản ngắn / mơ hồ: không được sai mà vẫn tự tin ---------------------------------------------
AMBIGUOUS_SHORT = [
    ("Hello", "en"), ("Thanks", "en"), ("merci", "fr"), ("Danke", "de"), ("Gracias", "es"),
    ("xin chao", "vi"), ("cam on", "vi"), ("你好", "zh"), ("ありがとう", "ja"), ("Привет", "ru"),
    ("a", None), ("aaaaaaaaaaaaaaaa", None), ("OK", None),
]


@pytest.mark.parametrize("text,expected", AMBIGUOUS_SHORT)
def test_short_inputs_are_never_confidently_wrong(text, expected):
    result = detect(text)
    if result.status == "detected":
        assert expected is not None and result.resolved_source_lang == expected
    else:
        assert result.resolved_source_lang is None


def test_typing_prefixes_are_never_confidently_wrong():
    sentence = "Die Studenten müssen alle Pflichtkurse abschließen, bevor sie ihre Arbeit anmelden dürfen."
    words = sentence.split()
    for count in range(1, len(words) + 1):
        result = detect(" ".join(words[:count]))
        if result.status == "detected":
            assert result.resolved_source_lang == "de", " ".join(words[:count])


def test_uncertain_has_no_resolved_language_but_offers_candidates():
    result = detect("Hello")
    assert result.status in ("uncertain", "detected")
    if result.status == "uncertain":
        assert result.resolved_source_lang is None
        assert result.reason in ("short_input", "low_confidence", "engines_disagree", "mixed_language")
        assert result.message


# --- Gợi ý ngôn ngữ (chống nhấp nháy khi gõ) -------------------------------------------------------
def test_hint_resolves_a_short_ambiguous_continuation():
    base = detect("Hello")
    if base.status != "uncertain":
        pytest.skip("Engine hiện đủ chắc chắn cho 'Hello'; không cần hint.")
    hinted = detect("Hello", hint="en")
    assert hinted.status == "detected"
    assert hinted.resolved_source_lang == "en"
    assert hinted.engine == "hint"


def test_hint_never_overrides_strong_contrary_evidence():
    result = detect("La intelligenza artificiale sta cambiando il modo in cui studiamo ogni giorno", hint="en")
    assert result.status == "unsupported"
    result = detect("Trí tuệ nhân tạo đang thay đổi giáo dục trên toàn thế giới", hint="en")
    assert result.resolved_source_lang == "vi"


# --- Chính sách dừng & hợp đồng ---------------------------------------------------------------------
def test_manual_language_always_wins_and_skips_detection():
    resolution = ld.resolve_source_language("whatever text", "de")
    assert resolution.should_translate and resolution.source_lang == "de"
    assert resolution.details.engine == "manual" and resolution.details.confidence == 1.0


def test_auto_with_detected_language_translates():
    resolution = ld.resolve_source_language("Machine learning is transforming healthcare around the world", "auto")
    assert resolution.should_translate and resolution.source_lang == "en"
    assert resolution.error_code is None


@pytest.mark.parametrize(
    "text,error_code,http_status",
    [
        ("12345", "INVALID_INPUT", 400),
        ("https://openai.com/research/gpt4", "LANG_UNKNOWN", 400),
        ("La intelligenza artificiale sta cambiando il modo in cui studiamo ogni giorno", "LANG_UNSUPPORTED", 400),
    ],
)
def test_auto_without_a_trustworthy_language_stops(text, error_code, http_status):
    resolution = ld.resolve_source_language(text, "auto")
    assert not resolution.should_translate
    assert resolution.source_lang is None
    assert resolution.error_code == error_code
    assert resolution.http_status == http_status
    assert resolution.message


def test_resolution_error_payload_is_structured():
    resolution = ld.resolve_source_language("12345", "auto")
    payload = ld.LanguageResolutionError(resolution).to_payload()
    assert payload["ok"] is False
    assert payload["detail"] == payload["error"]["message"]
    assert payload["error"]["code"] == "INVALID_INPUT"
    assert payload["error"]["detection"]["status"] == "invalid_input"


# --- Xác định, cache, an toàn đầu vào ---------------------------------------------------------------
def test_detection_is_deterministic_and_cache_returns_copies():
    text = "Trí tuệ nhân tạo đang thay đổi giáo dục trên toàn thế giới"
    first, second = detect(text), detect(text)
    assert first == second
    
    second.candidates.clear()
    assert detect(text).candidates, "Sửa kết quả trả về không được làm hỏng cache"


def test_never_raises_on_hostile_input():
    hostile = [
        "a" * 200_000,
        "<div>" * 5_000 + "Hello world, this is a test" + "</div>" * 5_000,
        "‍" * 1_000 + "Hello",
        "\x00\x01\x02 hello there my friend",
        "עברית" * 500 + " English words mixed in",
        "𝓗𝓮𝓵𝓵𝓸 𝔀𝓸𝓻𝓵𝓭 𝓽𝓱𝓲𝓼 𝓲𝓼 𝓪 𝓽𝓮𝓼𝓽",
        "é" * 3_000,
        "<!--" + "x" * 10_000,
    ]
    for text in hostile:
        result = detect(text)
        assert result.status in ("detected", "uncertain", "unsupported", "unknown", "invalid_input", "system_error")


def test_long_input_is_capped_for_the_engines():
    cleaned = ld._clean_for_detection("word " * 50_000, 2000)
    assert len(cleaned) <= 2001


def test_log_records_do_not_contain_raw_text(monkeypatch):
    captured = []

    class Recorder:
        def info(self, message, *args, **kwargs):
            captured.append((message, kwargs))

        def warning(self, *args, **kwargs):
            captured.append(("warning", kwargs))

        def error(self, *args, **kwargs):
            captured.append(("error", kwargs))

    monkeypatch.setattr(ld, "logger", Recorder())
    secret = "Thông tin riêng tư của người dùng không được ghi vào log hệ thống"
    ld.detect_language_detailed(secret)
    flattened = repr(captured)
    assert "riêng tư" not in flattened
    assert "input_length" in flattened


# --- Hiệu chỉnh -----------------------------------------------------------------------------------------
def test_calibration_falls_back_to_defaults_for_missing_or_broken_file(tmp_path):
    assert ld.Calibration.load(str(tmp_path / "missing.json")).version == "default"
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert ld.Calibration.load(str(broken)).version == "default"
    mismatched = tmp_path / "mismatch.json"
    mismatched.write_text('{"features": ["x"], "bias": 0, "coef": {}, "thresholds": {}}', encoding="utf-8")
    assert ld.Calibration.load(str(mismatched)).version == "default"


def test_meta_confidence_is_monotonic_in_evidence():
    cal = ld.Calibration()
    weak = {"p1": 0.4, "margin": 0.05, "agree": 0.0, "short": 1.0, "purity": 1.0, "length": 0.1, "support": 0.0}
    strong = {"p1": 0.99, "margin": 0.95, "agree": 1.0, "short": 0.0, "purity": 1.0, "length": 1.0, "support": 0.0}
    assert 0.0 <= cal.meta(weak) < cal.meta(strong) <= 1.0
