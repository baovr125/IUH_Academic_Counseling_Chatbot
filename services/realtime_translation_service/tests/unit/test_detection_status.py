"""Logic quyết định của Language Detection (script, fusion, trạng thái) với engine được mock có kiểm soát.

Khác với test_language_detection.py (engine thật), file này cô lập từng nhánh quyết định để chắc chắn
chính sách đúng ngay cả khi điểm số của model thay đổi.
"""
import pytest
from fastapi import HTTPException

from app.services import language_detection as ld
from app.services.translation_service import detect_source_language


@pytest.fixture(autouse=True)
def isolated_detector(monkeypatch):
    ld.reload_config()
    monkeypatch.setattr(ld, "_calibration", ld.Calibration())  # hệ số mặc định, độc lập file hiệu chỉnh
    yield
    ld.reload_config()


def engines(monkeypatch, ft=None, lingua=None, lingua_error=False):
    """Mock hai engine; ft: list[(code, p)] hoặc None, lingua: dict[code, p]."""
    calls = {"ft": 0, "lingua": 0}

    def fake_ft(text, k=5):
        calls["ft"] += 1
        return list(ft or [])

    def fake_lingua(text):
        calls["lingua"] += 1
        if lingua_error:
            raise RuntimeError("lingua down")
        return dict(lingua or {})

    monkeypatch.setattr(ld, "fasttext_topk", fake_ft)
    monkeypatch.setattr(ld, "_lingua_distribution", fake_lingua)
    return calls


LONG_EN = "Students are required to complete all prerequisite courses before registering for the thesis"


# --- Script profile ----------------------------------------------------------------------------------
class TestScriptProfile:
    def test_spaced_text_counts_words(self):
        profile = ld._profile("Hello big wide world")
        assert profile.dominant == ld.LATIN and profile.eff_len == 4 and not profile.cjk_like

    def test_cjk_text_counts_characters_not_words(self):
        profile = ld._profile("人工智能正在改变教育领域")
        assert profile.dominant == ld.HAN and profile.cjk_like and profile.eff_len == 12

    def test_thai_counts_base_letters_only(self):
        # Dấu thanh/nguyên âm kết hợp (Mn) không phải chữ cái nên không tính vào độ dài hiệu dụng.
        assert ld._profile("สวัสดีครับ").eff_len == 7

    def test_vietnamese_marks_are_counted(self):
        assert ld._profile("Trí tuệ nhân tạo").vi_marks >= 2
        assert ld._profile("tri tue nhan tao").vi_marks == 0

    def test_mixed_script_share(self):
        profile = ld._profile("Hello こんにちは")
        assert profile.counts[ld.LATIN] == 5 and profile.counts[ld.KANA] == 5 and profile.share == 0.5


class TestScriptShortcuts:
    cfg = ld.DetectionConfig()

    def shortcut(self, text, ft=()):
        return ld._script_shortcut(ld._profile(text), list(ft), self.cfg)

    def test_arabic_is_unsupported_by_script(self):
        result = self.shortcut("الذكاء الاصطناعي يغير التعليم")
        assert result.status == "unsupported" and result.reason == "script_mismatch"

    def test_unsupported_script_uses_fasttext_label_when_available(self):
        result = self.shortcut("هوش مصنوعی آموزش را تغییر می دهد", ft=[("fa", 0.95)])
        assert result.detected_language == "fa"

    def test_hangul_kana_thai_are_decided_by_script(self):
        assert self.shortcut("기계 학습은 의료를 변화시키고 있다").resolved_source_lang == "ko"
        assert self.shortcut("機械学習はヘルスケアを変革している").resolved_source_lang == "ja"
        assert self.shortcut("ปัญญาประดิษฐ์กำลังเปลี่ยนแปลงการศึกษา").resolved_source_lang == "th"

    def test_single_character_is_too_short(self):
        result = self.shortcut("あ")
        assert result.status == "uncertain" and result.reason == "short_input"

    def test_embedded_latin_words_do_not_cancel_the_script_decision(self):
        assert self.shortcut("YouTubeが落ちてるんだ。").resolved_source_lang == "ja"

    def test_mostly_latin_text_is_not_decided_by_script(self):
        assert self.shortcut("Hello world and こ") is None

    def test_han_only_is_left_to_the_engines(self):
        assert self.shortcut("人工智能正在改变教育") is None


class TestPackagedResources:
    def test_vietnamese_syllable_lexicon_is_packaged_and_loaded(self):
        from pathlib import Path
        path = Path(ld.__file__).resolve().parents[1] / "resources" / "vi_toneless_syllables.txt"
        assert path.exists(), "Thiếu app/resources/vi_toneless_syllables.txt (chạy scripts/build_vi_lexicon.py)"
        lexicon = ld._vi_lexicon()
        assert len(lexicon) > 800
        assert {"khong", "duoc", "nguoi", "truong"} <= lexicon

    def test_lexicon_avoids_common_foreign_function_words(self):
        lexicon = ld._vi_lexicon()
        assert not ({"the", "and", "for", "are", "der", "die", "las", "los", "per", "con"} & lexicon)

    def test_calibration_file_matches_the_feature_contract(self):
        import json
        from pathlib import Path
        path = Path(ld.__file__).resolve().parents[2] / "models" / "detect_calibration.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert tuple(data["features"]) == ld.FEATURE_NAMES
        assert set(data["thresholds"]) == {"short", "medium", "long"}
        assert all(0.5 <= value <= 1.0 for value in data["thresholds"].values())
        assert ld.Calibration.load(str(path)).version == data["version"]


# --- Làm sạch ------------------------------------------------------------------------------------------
class TestCleaning:
    def test_removes_urls_emails_mentions(self):
        cleaned = ld._clean_for_detection("Mail a.b@x.com or see https://x.org/p and @user #tag now", 2000)
        assert "x.com" not in cleaned and "https" not in cleaned and "@user" not in cleaned
        assert "tag" in cleaned  # chỉ bỏ dấu '#'

    def test_html_extraction_skips_protected_tags_and_comments(self):
        visible = ld._extract_visible_text("<style>.a{}</style><!-- note --><p>Hello</p><code>x = 1</code>")
        assert visible.strip() == "Hello"

    def test_plain_text_skips_html_parser(self):
        assert ld._extract_visible_text("a < b and b > c") == "a < b and b > c"

    def test_nfd_text_is_normalized(self):
        import unicodedata
        decomposed = unicodedata.normalize("NFD", "Trí tuệ")
        assert ld._clean_for_detection(decomposed, 2000) == "Trí tuệ"

    def test_cap_keeps_head_and_tail(self):
        cleaned = ld._clean_for_detection("start " + "x " * 5000 + "end", 100)
        assert cleaned.startswith("start") and cleaned.endswith("end") and len(cleaned) <= 101


# --- Fusion & trạng thái ---------------------------------------------------------------------------------
class TestFusionDecisions:
    def test_confident_fasttext_skips_lingua(self, monkeypatch):
        calls = engines(monkeypatch, ft=[("en", 0.99), ("de", 0.003)])
        result = ld.detect_language_detailed(LONG_EN)
        assert result.status == "detected" and result.resolved_source_lang == "en"
        assert result.engine == "fasttext" and calls["lingua"] == 0

    def test_crosscheck_flag_always_runs_lingua(self, monkeypatch):
        monkeypatch.setenv("DETECT_ALWAYS_CROSSCHECK", "1")
        ld.reload_config()
        monkeypatch.setattr(ld, "_calibration", ld.Calibration())
        calls = engines(monkeypatch, ft=[("en", 0.99)], lingua={"en": 0.97, "de": 0.01})
        result = ld.detect_language_detailed(LONG_EN)
        assert calls["lingua"] == 1 and result.engine == "fusion"

    def test_engines_disagreeing_on_short_text_is_uncertain(self, monkeypatch):
        engines(monkeypatch, ft=[("en", 0.55), ("fr", 0.3)], lingua={"es": 0.5, "fr": 0.3, "en": 0.1})
        result = ld.detect_language_detailed("Je pense")
        assert result.status == "uncertain" and result.resolved_source_lang is None
        assert result.reason in ("short_input", "engines_disagree", "low_confidence")
        assert {c.language for c in result.candidates} & {"en", "es", "fr"}

    def test_candidates_only_contain_supported_languages(self, monkeypatch):
        engines(monkeypatch, ft=[("it", 0.5), ("es", 0.3)], lingua={"it": 0.5, "es": 0.3, "pt": 0.1})
        result = ld.detect_language_detailed("Come stai oggi amico mio")
        assert all(c.language in ld.SUPPORTED_CODES for c in result.candidates)

    def test_out_of_scope_language_is_unsupported(self, monkeypatch):
        engines(monkeypatch, ft=[("it", 0.97), ("es", 0.01)], lingua={"it": 0.96, "es": 0.02})
        result = ld.detect_language_detailed("La intelligenza artificiale sta cambiando il modo in cui studiamo")
        assert result.status == "unsupported" and result.detected_language == "it"
        assert result.resolved_source_lang is None

    def test_out_of_scope_with_strong_supported_competitor_is_only_uncertain(self, monkeypatch):
        engines(monkeypatch, ft=[("pt", 0.5), ("es", 0.45)], lingua={"pt": 0.5, "es": 0.4})
        result = ld.detect_language_detailed("Por favor ayuda")
        assert result.status == "uncertain"

    def test_much_probability_outside_supported_set_blocks_detection(self, monkeypatch):
        # fr dẫn đầu nhưng ≥40% xác suất thuộc hr/it (ngôn ngữ ngoài phạm vi) → không kết luận detected.
        engines(monkeypatch, ft=[("fr", 0.55), ("hr", 0.35)], lingua={"fr": 0.45, "hr": 0.3, "it": 0.15})
        result = ld.detect_language_detailed("Je li Boston daleko danas")
        assert result.status == "uncertain" and result.reason == "out_of_scope"
        assert result.resolved_source_lang is None

    def test_independent_vietnamese_evidence_is_exempt_from_the_outside_rule(self, monkeypatch):
        engines(monkeypatch, ft=[("tl", 0.4), ("id", 0.2), ("vi", 0.2)], lingua={"vi": 0.55, "id": 0.2, "ms": 0.1})
        result = ld.detect_language_detailed("toi dang hoc lap trinh tai truong dai hoc cong nghiep")
        assert result.status == "detected" and result.resolved_source_lang == "vi"

    def test_rare_fasttext_label_never_means_unsupported(self, monkeypatch):
        engines(monkeypatch, ft=[("ilo", 0.9)], lingua={})
        result = ld.detect_language_detailed("ko bik lm sao luon")
        assert result.status != "unsupported" and result.resolved_source_lang is None

    def test_lingua_only_when_fasttext_is_unavailable(self, monkeypatch):
        engines(monkeypatch, ft=[], lingua={"vi": 0.97, "fr": 0.01})
        result = ld.detect_language_detailed("Trí tuệ nhân tạo đang thay đổi giáo dục trên toàn thế giới")
        assert result.status == "detected" and result.resolved_source_lang == "vi"
        assert result.engine == "lingua"

    def test_all_engines_failing_is_system_error(self, monkeypatch):
        engines(monkeypatch, ft=[], lingua_error=True)
        result = ld.detect_language_detailed("Some perfectly normal english sentence here")
        assert result.status == "system_error" and result.message

    def test_unexpected_exception_is_system_error_and_not_cached(self, monkeypatch):
        def boom(text, k=5):
            raise ValueError("model exploded")

        monkeypatch.setattr(ld, "fasttext_topk", boom)
        first = ld.detect_language_detailed("Some perfectly normal english sentence here")
        assert first.status == "system_error"
        engines(monkeypatch, ft=[("en", 0.99)])
        assert ld.detect_language_detailed("Some perfectly normal english sentence here").status == "detected"

    def test_han_only_japanese_label_is_merged_into_chinese(self, monkeypatch):
        engines(monkeypatch, ft=[("ja", 0.77), ("zh", 0.2)])
        result = ld.detect_language_detailed("很少人能講英語講得比幸子好。")
        assert result.status == "detected" and result.resolved_source_lang == "zh"

    def test_very_short_han_only_stays_ambiguous(self, monkeypatch):
        engines(monkeypatch, ft=[("ja", 0.75), ("zh", 0.2)])
        result = ld.detect_language_detailed("大学")
        assert result.status == "uncertain"

    def test_vietnamese_toneless_evidence_breaks_a_tie(self, monkeypatch):
        engines(monkeypatch, ft=[("en", 0.3), ("vi", 0.25)], lingua={"vi": 0.65, "fr": 0.14, "en": 0.1})
        result = ld.detect_language_detailed("toi dang hoc lap trinh tai truong dai hoc cong nghiep")
        assert result.resolved_source_lang == "vi"

    def test_result_cache_avoids_recomputation(self, monkeypatch):
        calls = engines(monkeypatch, ft=[("en", 0.99)])
        ld.detect_language_detailed(LONG_EN)
        ld.detect_language_detailed(LONG_EN)
        assert calls["ft"] == 1
        ld.detect_language_detailed(LONG_EN, hint="en")  # khoá cache có hint
        assert calls["ft"] == 2


class TestUpperCaseAndMixedSelection:
    def test_uppercase_text_is_lowercased_for_engines(self, monkeypatch):
        seen = []

        def spy(text, k=5):
            seen.append(text)
            return [("en", 0.99)]

        monkeypatch.setattr(ld, "fasttext_topk", spy)
        ld.detect_language_detailed("THIS IS A VERY LOUD SENTENCE WRITTEN IN CAPITAL LETTERS")
        assert seen and seen[0] == seen[0].lower()

    def test_mixed_case_text_is_untouched(self, monkeypatch):
        seen = []

        def spy(text, k=5):
            seen.append(text)
            return [("en", 0.99)]

        monkeypatch.setattr(ld, "fasttext_topk", spy)
        ld.detect_language_detailed("NASA announced a new mission to Mars")
        assert seen[0] == "NASA announced a new mission to Mars"


# --- Chính sách dừng và wrapper tương thích ----------------------------------------------------------------
class TestPolicyAndCompat:
    def test_wrapper_returns_language_when_detected(self, monkeypatch):
        engines(monkeypatch, ft=[("en", 0.99)])
        assert detect_source_language(LONG_EN) == "en"

    @pytest.mark.parametrize(
        "text,ft,status_code",
        [
            ("12345", [], 400),
            ("La intelligenza artificiale sta cambiando il modo in cui studiamo", [("it", 0.97)], 400),
            ("Hi", [("en", 0.2), ("de", 0.2)], 400),
        ],
    )
    def test_wrapper_raises_for_every_non_detected_status(self, monkeypatch, text, ft, status_code):
        engines(monkeypatch, ft=ft, lingua={"it": 0.95} if "intelligenza" in text else {"en": 0.2, "de": 0.2})
        with pytest.raises(HTTPException) as info:
            detect_source_language(text)
        assert info.value.status_code == status_code

    def test_system_error_maps_to_503(self, monkeypatch):
        engines(monkeypatch, ft=[], lingua_error=True)
        resolution = ld.resolve_source_language("Some perfectly normal english sentence here", "auto")
        assert not resolution.should_translate
        assert resolution.error_code == "LANG_SYSTEM_ERROR" and resolution.http_status == 503

    def test_all_statuses_have_error_codes(self):
        assert set(ld.STATUS_ERROR_CODES) == {"uncertain", "unsupported", "unknown", "invalid_input", "system_error"}
