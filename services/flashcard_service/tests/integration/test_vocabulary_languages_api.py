"""API sinh từ vựng cho 9 ngôn ngữ: sinh theo ngôn ngữ, sổ đích phải cùng ngôn ngữ (409 trước khi trừ lượt), lưu đúng ngôn ngữ."""
import io

import pytest

from conftest import USER_A, USER_B

GEN = "/api/v1/flashcards/vocabulary/generate"
IMG = "/api/v1/flashcards/vocabulary/generate-image"
QUOTA = "/api/v1/flashcards/vocabulary/quota"
COMMIT = "/api/v1/flashcards/decks/from-generated"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64

GERMAN = ["der Hund", "die Katze", "das Haus", "gehen", "schnell", "Straße"]
LANG_WORDS = {
    "de": GERMAN, "fr": ["le chat", "la maison", "manger", "rapide", "l'école", "œuf"],
    "es": ["el libro", "la casa", "comer", "rápido", "niño", "año"], "ru": ["дом", "книга", "читать", "быстрый", "друг", "окно"],
    "zh": ["和平", "学习", "朋友", "图书馆", "快乐", "天气"], "ja": ["食べる", "図書館", "きれい", "コーヒー", "学生", "天気"],
    "ko": ["먹다", "도서관", "친구", "학생", "날씨", "행복"], "th": ["สวัสดี", "หนังสือ", "เพื่อน", "โรงเรียน", "อาหาร", "ขอบคุณ"],
}


def body(**kw):
    base = {"topic": "Daily life", "level": "B1", "count": 5}
    base.update(kw)
    return base


def used(api, headers):
    return api.get(QUOTA, headers=headers).json()["data"]["used"]


class TestGenerateInEachLanguage:
    @pytest.mark.parametrize("lang", sorted(LANG_WORDS))
    def test_returns_words_in_the_requested_language(self, api, fake_db, fake_llm, headers_a, lang):
        fake_llm.words = LANG_WORDS[lang]
        res = api.post(GEN, headers=headers_a, json=body(lang_code=lang))
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["lang_code"] == lang and data["returned"] == 5
        assert [i["term"] for i in data["items"]] == LANG_WORDS[lang][:5]
        assert "vocabulary curriculum designer" in fake_llm.calls[0]["system"]

    def test_default_is_still_english(self, api, fake_db, fake_llm, headers_a):
        data = api.post(GEN, headers=headers_a, json=body()).json()["data"]
        assert data["lang_code"] == "en" and "English" in fake_llm.calls[0]["system"]

    @pytest.mark.parametrize("lang", ["vi", "xx", "", "EN-US", "auto"])
    def test_non_learnable_or_unknown_language_is_422_and_free(self, api, fake_db, fake_llm, headers_a, lang):
        assert api.post(GEN, headers=headers_a, json=body(lang_code=lang)).status_code == 422
        assert fake_llm.calls == [] and used(api, headers_a) == 0

    def test_text_mode_accepts_a_passage_in_the_language(self, api, fake_db, fake_llm, headers_a):
        fake_llm.words = GERMAN
        res = api.post(GEN, headers=headers_a, json={"mode": "text", "text": "Der Hund läuft schnell durch die Straße. " * 2,
                                                       "lang_code": "de", "level": "B1", "count": 5})
        assert res.status_code == 200 and res.json()["data"]["lang_code"] == "de"
        assert "important German words" in fake_llm.calls[0]["user"]


class TestTargetDeckLanguage:
    def test_english_deck_rejects_german_generation_before_spending_a_credit(self, api, fake_db, fake_llm, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_A, title="English", lang_code="en")
        res = api.post(GEN, headers=headers_a, json=body(lang_code="de", deck_id=deck["id"]))
        assert (res.status_code, res.json()["error"]["code"]) == (409, "LANG_MISMATCH")
        assert "Tiếng Anh" in res.json()["error"]["message"] and "Tiếng Đức" in res.json()["error"]["message"]
        assert fake_llm.calls == [] and used(api, headers_a) == 0

    def test_german_deck_accepts_german_and_excludes_known_words_even_without_article(self, api, fake_db, fake_llm, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_A, title="Deutsch", lang_code="de")
        fake_db.seed("flashcards", deck_id=deck["id"], user_id=USER_A, term="Hund", definition="con chó", lang_code="de")
        fake_llm.words = GERMAN
        res = api.post(GEN, headers=headers_a, json=body(lang_code="de", deck_id=deck["id"], count=5))
        assert res.status_code == 200
        terms = {i["term"] for i in res.json()["data"]["items"]}
        assert "der Hund" not in terms and "die Katze" in terms

    def test_german_deck_rejects_english_default_request(self, api, fake_db, fake_llm, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_A, title="Deutsch", lang_code="de")
        res = api.post(GEN, headers=headers_a, json=body(deck_id=deck["id"]))  # không nói lang_code => en
        assert res.status_code == 409 and fake_llm.calls == [] and used(api, headers_a) == 0

    def test_other_users_deck_is_still_403(self, api, fake_db, fake_llm, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_B, title="Theirs", lang_code="de")
        res = api.post(GEN, headers=headers_a, json=body(lang_code="de", deck_id=deck["id"]))
        assert res.status_code == 403 and fake_llm.calls == []


class TestGenerateFromImage:
    @pytest.mark.parametrize("lang", ["de", "ja", "th"])
    def test_language_form_field_reaches_the_prompt(self, api, fake_db, fake_llm, headers_a, lang):
        fake_llm.words = LANG_WORDS[lang]
        res = api.post(IMG, headers=headers_a, files={"file": ("p.png", io.BytesIO(PNG))},
                       data={"level": "B1", "count": "5", "lang_code": lang})
        assert res.status_code == 200 and res.json()["data"]["lang_code"] == lang
        assert "readable" in fake_llm.calls[0]["user"] and fake_llm.calls[0]["images"]

    def test_unsupported_language_form_value_is_422(self, api, fake_db, fake_llm, headers_a):
        res = api.post(IMG, headers=headers_a, files={"file": ("p.png", io.BytesIO(PNG))}, data={"lang_code": "vi"})
        assert res.status_code == 422 and fake_llm.calls == []


class TestCommitInEachLanguage:
    def payload(self, lang="de", rid="req-lang-0001", cards=None, deck_lang=None, source_lang="same"):
        cards = cards or [{"term": "der Hund", "definition": "con chó", "part_of_speech": "noun", "phonetic": "/hʊnt/",
                           "example": "Der Hund läuft.", "example_translation": "Con chó chạy."},
                          {"term": "gehen", "definition": "đi", "part_of_speech": "verb"}]
        return {"client_request_id": rid, "deck": {"title": f"AI {lang}", "lang_code": deck_lang or lang}, "cards": cards,
                "source": {"mode": "topic", "topic": "Daily life", "level": "B1",
                           **({"lang_code": lang} if source_lang == "same" else ({"lang_code": source_lang} if source_lang else {}))}}

    @pytest.mark.parametrize("lang", sorted(LANG_WORDS))
    def test_new_deck_and_cards_get_the_language(self, api, fake_db, headers_a, lang):
        cards = [{"term": t, "definition": "nghĩa"} for t in LANG_WORDS[lang][:3]]
        res = api.post(COMMIT, headers=headers_a, json=self.payload(lang, rid=f"req-new-{lang}", cards=cards))
        assert res.status_code == 200 and res.json()["data"]["inserted"] == 3
        (deck,) = fake_db.rows("flashcard_decks", user_id=USER_A)
        assert deck["lang_code"] == lang
        assert {r["lang_code"] for r in fake_db.rows("flashcards", deck_id=deck["id"])} == {lang}

    def test_source_language_alone_decides_the_new_deck_language(self, api, fake_db, headers_a):
        p = self.payload("fr", rid="req-src-0001")
        p["deck"].pop("lang_code")
        assert api.post(COMMIT, headers=headers_a, json=p).status_code == 200
        assert fake_db.rows("flashcard_decks", user_id=USER_A)[0]["lang_code"] == "fr"

    def test_no_language_at_all_keeps_the_old_english_default(self, api, fake_db, headers_a):
        p = self.payload("en", rid="req-def-0001", source_lang=None)
        p["deck"].pop("lang_code")
        assert api.post(COMMIT, headers=headers_a, json=p).status_code == 200
        assert fake_db.rows("flashcard_decks", user_id=USER_A)[0]["lang_code"] == "en"

    def test_deck_and_source_languages_must_agree(self, api, fake_db, headers_a):
        res = api.post(COMMIT, headers=headers_a, json=self.payload("de", rid="req-mix-0001", source_lang="fr"))
        assert (res.status_code, res.json()["error"]["code"]) == (409, "LANG_MISMATCH")
        assert fake_db.rows("flashcard_decks") == []

    @pytest.mark.parametrize("bad", ["vi", "xx"])
    def test_non_learnable_deck_language_is_rejected(self, api, fake_db, headers_a, bad):
        res = api.post(COMMIT, headers=headers_a, json=self.payload("de", rid=f"req-bad-{bad}", deck_lang=bad, source_lang=None))
        assert res.status_code == 422 and fake_db.rows("flashcard_decks") == []

    def test_add_to_existing_german_deck_follows_the_deck(self, api, fake_db, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_A, title="Deutsch", lang_code="de")
        for source in ("same", None):  # có hoặc không truyền ngôn ngữ nguồn
            p = self.payload("de", rid=f"req-add-{source}", source_lang=source,
                             cards=[{"term": f"Wort{source}", "definition": "từ"}])
            p.pop("deck")
            p["deck_id"] = deck["id"]
            assert api.post(COMMIT, headers=headers_a, json=p).status_code == 200
        assert {r["lang_code"] for r in fake_db.rows("flashcards", deck_id=deck["id"])} == {"de"}

    def test_german_cards_cannot_be_saved_into_an_english_deck(self, api, fake_db, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_A, title="English", lang_code="en")
        p = self.payload("de", rid="req-mis-0001")
        p.pop("deck")
        p["deck_id"] = deck["id"]
        res = api.post(COMMIT, headers=headers_a, json=p)
        assert (res.status_code, res.json()["error"]["code"]) == (409, "LANG_MISMATCH")
        assert fake_db.rows("flashcards") == []

    def test_article_noun_is_not_mistaken_for_a_phrase_when_pos_is_missing(self, api, fake_db, headers_a):
        cards = [{"term": "der Hund", "definition": "con chó"}, {"term": "auf Wiedersehen", "definition": "tạm biệt"},
                 {"term": "和平", "definition": "hòa bình"}]
        p = self.payload("de", rid="req-pos-0001", cards=cards[:2])
        assert api.post(COMMIT, headers=headers_a, json=p).status_code == 200
        pos = {r["term"]: r["part_of_speech"] for r in fake_db.rows("flashcards")}
        assert pos == {"der Hund": "noun", "auf Wiedersehen": "phrase"}

    def test_generate_commit_study_roundtrip_in_german(self, api, fake_db, fake_llm, headers_a):
        fake_llm.words = GERMAN
        gen = api.post(GEN, headers=headers_a, json=body(lang_code="de", count=6)).json()["data"]
        cards = [{"term": i["term"], "definition": i["definition"], "part_of_speech": i["part_of_speech"], "phonetic": i["ipa"],
                  "example": i["example"], "example_translation": i["example_translation"], "level": "B1"} for i in gen["items"]]
        res = api.post(COMMIT, headers=headers_a, json=self.payload("de", rid="req-rt-0001", cards=cards))
        deck_id = res.json()["data"]["deck"]["id"]
        queue = api.get(f"/api/v1/flashcards/decks/{deck_id}/study-queue", headers=headers_a).json()["data"]
        assert len(queue) == 6 and {c["lang_code"] for c in queue} == {"de"}
