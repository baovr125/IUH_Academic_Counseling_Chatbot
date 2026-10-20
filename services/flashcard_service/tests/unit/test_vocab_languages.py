"""Cấu hình sinh từ vựng theo ngôn ngữ: hợp đồng 9 ngôn ngữ, kiểm tra từ theo hệ chữ, mạo từ, phiên âm, tìm từ trong câu."""
import pytest

from app.services.vocab_languages import (
    ENGLISH_ONLY_PURPOSES,
    LANGS,
    LEARNABLE_CODES,
    get_lang,
    is_valid_term,
    normalize_reading,
    strip_article,
    term_pattern,
)
from app.utils.languages import LEARNABLE_LANGS


def L(code):
    return LANGS[code]


class TestContract:
    def test_covers_exactly_the_learnable_languages(self):
        assert set(LEARNABLE_CODES) == set(LEARNABLE_LANGS) and len(LEARNABLE_CODES) == 9
        assert "vi" not in LANGS  # tiếng Việt là ngôn ngữ giải nghĩa

    @pytest.mark.parametrize("code", sorted(LANGS))
    def test_every_language_is_fully_described(self, code):
        lang = L(code)
        assert lang.code == code and lang.name and lang.vi_name.startswith("Tiếng ")
        assert lang.headword_rules and lang.reading_instruction and lang.example_length
        assert lang.reading_kind in ("ipa", "pinyin", "kana_romaji", "romanization")
        assert lang.scripts and lang.token_factor >= 1.0

    def test_unknown_code_falls_back_to_english(self):
        assert get_lang(None).code == "en" and get_lang("xx").code == "en" and get_lang("DE").code == "de"

    def test_exam_purposes_are_english_only(self):
        assert set(ENGLISH_ONLY_PURPOSES) == {"ielts", "toeic"}


class TestTermValidation:
    @pytest.mark.parametrize("code,term", [
        ("de", "der Hund"), ("de", "Straße"), ("de", "schön"), ("fr", "l'école"), ("fr", "l’école"), ("fr", "œuf"),
        ("es", "el niño"), ("es", "año"), ("ru", "дом"), ("ru", "Ёлка"), ("zh", "和平"), ("zh", "图书馆"),
        ("ja", "食べる"), ("ja", "コーヒー"), ("ja", "きれい"), ("ko", "먹다"), ("ko", "도서관"), ("th", "สวัสดี"), ("th", "ขอบคุณ"),
        ("en", "sustainable"),
    ])
    def test_valid(self, code, term):
        assert is_valid_term(L(code), term)

    @pytest.mark.parametrize("code,term", [
        ("de", "狗"), ("de", "дом"), ("de", "Hund1"), ("de", "-Hund"), ("de", ""), ("de", "x" * 61), ("de", "Hund<script>"),
        ("zh", "peace"), ("zh", "和平 abc"), ("ja", "taberu"), ("ko", "meokda"), ("ko", "食"), ("ru", "dom"), ("th", "sawatdi"),
        ("fr", "дом"), ("es", "和平"),
    ])
    def test_wrong_script_or_junk_is_rejected(self, code, term):
        assert not is_valid_term(L(code), term)


class TestArticles:
    @pytest.mark.parametrize("code,term,expected", [
        ("de", "der Hund", "Hund"), ("de", "Die Katze", "Katze"), ("de", "das Haus", "Haus"),
        ("fr", "le chat", "chat"), ("fr", "l'école", "école"), ("fr", "l’école", "école"),
        ("es", "el libro", "libro"), ("es", "la casa", "casa"),
    ])
    def test_leading_article_is_stripped(self, code, term, expected):
        assert strip_article(L(code), term) == expected

    @pytest.mark.parametrize("code,term", [
        ("de", "dermatologie"), ("de", "die"), ("fr", "lecture"), ("es", "elefante"), ("en", "the cat"), ("ja", "食べる"), ("zh", "和平"),
    ])
    def test_words_that_merely_start_like_an_article_are_untouched(self, code, term):
        assert strip_article(L(code), term) == term


class TestReadings:
    @pytest.mark.parametrize("code,value,term,expected", [
        ("de", "/hʊnt/", "der Hund", "/hʊnt/"), ("de", "[ɪç]", "ich", "/ɪç/"), ("de", "/ˈʃøːn/", "schön", "/ˈʃøːn/"),
        ("fr", "/ʃa/", "le chat", "/ʃa/"), ("fr", "/bɔ̃/", "bon", "/bɔ̃/"), ("fr", "/œf/", "œuf", "/œf/"),
        ("es", "/ˈkasa/", "la casa", "/ˈkasa/"), ("es", "/niɲo/", "el niño", "/niɲo/"), ("es", "/aβa/", "haba", "/aβa/"),
        ("ru", "/ˈdom/", "дом", "/ˈdom/"),
        ("zh", "hé píng", "和平", "hé píng"), ("zh", "xué xí", "学习", "xué xí"),
        ("ja", "たべる · taberu", "食べる", "たべる · taberu"), ("ja", "コーヒー · kōhī", "コーヒー", "コーヒー · kōhī"),
        ("ko", "meokda", "먹다", "meokda"), ("th", "sawatdi", "สวัสดี", "sawatdi"),
    ])
    def test_valid_readings_are_accepted(self, code, value, term, expected):
        assert normalize_reading(L(code), value, term) == expected

    @pytest.mark.parametrize("code,value,term", [
        ("de", "hund", "der Hund"),  # chép lại chính tả (không tính mạo từ)
        ("de", "/хунд/", "Hund"), ("ru", "/дом/", "дом"),  # IPA không được chứa chữ Cyrillic
        ("zh", "和平", "和平"), ("zh", "/hé píng/", "和平"), ("zh", "hé píng 1", "和平"),
        ("ja", "食べる", "食べる"), ("ko", "먹다", "먹다"), ("th", "สวัสดี", "สวัสดี"), ("ko", "meokda" * 20, "먹다"),
        ("fr", "", "chat"), ("fr", None, "chat"),
    ])
    def test_invalid_readings_become_empty(self, code, value, term):
        assert normalize_reading(L(code), value, term) == ""


class TestTermInSentence:
    @pytest.mark.parametrize("code,term,sentence", [
        ("de", "der Hund", "Der Hund läuft schnell."), ("de", "der Hund", "Ich mag Hunde."), ("de", "gehen", "Wir gehen nach Hause."),
        ("fr", "l'école", "J'aime l'école."), ("fr", "le chat", "Les chats dorment."), ("es", "el libro", "Leo un libro interesante."),
        ("ru", "дом", "Мы живём в доме."), ("zh", "和平", "我们热爱和平。"), ("ja", "食べる", "毎日りんごを食べます。"),
        ("ja", "図書館", "図書館で本を読む。"), ("ko", "먹다", "저는 밥을 먹어요."), ("th", "สวัสดี", "เขาพูดว่า สวัสดี ครับ"),
    ])
    def test_found_including_inflected_forms(self, code, term, sentence):
        assert term_pattern(L(code), term).search(sentence)

    @pytest.mark.parametrize("code,term,sentence", [
        ("de", "der Hund", "Die Katze schläft."), ("zh", "和平", "我们喜欢苹果。"), ("ja", "図書館", "学校へ行く。"),
        ("ko", "먹다", "저는 물을 마셔요."), ("ru", "дом", "Мы идём в школу."),
    ])
    def test_absent_term_is_not_found(self, code, term, sentence):
        assert not term_pattern(L(code), term).search(sentence)

    def test_empty_term_matches_nothing(self):
        assert not term_pattern(L("de"), "").search("irgendein Satz")
