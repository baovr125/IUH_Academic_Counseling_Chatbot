import pytest

from app.services.normalization import (
    build_cloze,
    clean_text,
    dedupe_key,
    find_term_in_sentence,
    normalize_ipa,
    normalize_pos,
)


class TestNormalizePos:
    @pytest.mark.parametrize("raw,expected", [
        ("noun", "noun"), ("Noun", "noun"), ("n.", "noun"), ("N", "noun"), ("danh từ", "noun"),
        ("adv", "adverb"), ("Adv.", "adverb"), ("trạng từ", "adverb"),
        ("prep", "preposition"), ("giới từ", "preposition"),
        ("conj", "conjunction"), ("pron", "pronoun"), ("det", "determiner"), ("interj", "interjection"),
        ("phrasal verb", "phrasal verb"), ("  Phrasal   Verb ", "phrasal verb"),
        ("idiom", "idiom"), ("adj", "adjective"), ("tính từ", "adjective"),
    ])
    def test_known_values(self, raw, expected):
        assert normalize_pos(raw) == expected

    @pytest.mark.parametrize("raw", [None, "", "   ", "xyz", "noun phrase of doom"])
    def test_unknown_returns_none(self, raw):
        assert normalize_pos(raw) is None


class TestDedupeKey:
    def test_case_and_whitespace_insensitive(self):
        assert dedupe_key("  Carbon   Footprint ") == dedupe_key("carbon footprint")

    def test_unicode_normalisation(self):
        assert dedupe_key("café") == dedupe_key("café")

    def test_does_not_strip_diacritics(self):
        assert dedupe_key("cafe") != dedupe_key("café")

    def test_none_safe(self):
        assert dedupe_key(None) == ""


class TestCleanText:
    def test_collapses_whitespace_and_control_chars(self):
        assert clean_text("a\n\n  b\t\x00c", 50) == "a b c"

    def test_truncates(self):
        assert clean_text("x" * 100, 10) == "x" * 10

    def test_none(self):
        assert clean_text(None, 10) == ""


class TestCloze:
    @pytest.mark.parametrize("sentence,term,expected", [
        ("We need sustainable energy.", "sustainable", "We need ________ energy."),
        ("The factory polluted the river.", "pollute", "The factory ________ the river."),
        ("Running is fun.", "run", "________ is fun."),
        ("She gave up smoking.", "give up", None),  # biến hình của cụm động từ: chưa hỗ trợ (chỉ từ đầu biến hình)
        ("They decided to give up smoking.", "give up", "They decided to ________ smoking."),
    ])
    def test_inflection_aware(self, sentence, term, expected):
        assert build_cloze(sentence, term) == expected

    def test_whole_word_only(self):
        assert find_term_in_sentence("The cathedral is old.", "cat") is None

    def test_empty_inputs(self):
        assert build_cloze("", "x") is None
        assert build_cloze("text", "") is None
        assert build_cloze(None, "x") is None

    def test_regex_special_chars_are_escaped(self):
        assert build_cloze("Use c++ daily.", "c++") == "Use ________ daily."


class TestIpa:
    @pytest.mark.parametrize("value", ["/səˈsteɪnəbl/", "/ðɪs/", "/ˈθɪŋk/", "[ˈæpl]", "/ˈkɑrbən ˈfʊtˌprɪnt/", "ˈtɛkˌnɑlədʒi"])
    def test_valid_ipa_is_wrapped_in_slashes(self, value):
        out = normalize_ipa(value)
        assert out.startswith("/") and out.endswith("/")

    @pytest.mark.parametrize("value", ["", None, "/bền vững/", "/ɪ" + "x" * 80 + "/", "/<script>/", "/12345/"])
    def test_invalid_ipa_rejected(self, value):
        assert normalize_ipa(value) == ""

    def test_spelling_copy_is_rejected(self):
        assert normalize_ipa("sustain", "sustain") == ""
        assert normalize_ipa("/kæt/", "cat") == "/kæt/"

    def test_ascii_apostrophe_becomes_stress_mark(self):
        assert "ˈ" in normalize_ipa("/sə'steɪn/")
