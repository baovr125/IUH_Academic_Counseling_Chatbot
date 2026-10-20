"""10 bộ sưu tập ngôn ngữ: tổng hợp, danh sách theo ngôn ngữ, lưu từ Realtime Translation, tương thích dữ liệu cũ."""
import datetime

import pytest

from app import rabbitmq_consumer
from app.services import language_service
from app.utils.languages import LEARNABLE_LANGS, SUPPORTED_LANGS
from conftest import USER_A, USER_B, make_headers

BASE = "/api/v1/flashcards"
NOW = datetime.datetime.now(datetime.timezone.utc)

# Cặp (từ ngoại ngữ, nghĩa tiếng Việt) cho từng ngôn ngữ học
SAMPLES = {
    "en": ("Good morning", "Chào buổi sáng"), "de": ("Guten Morgen", "Chào buổi sáng"), "zh": ("早上好", "Chào buổi sáng"),
    "ja": ("おはようございます", "Chào buổi sáng"), "ko": ("좋은 아침", "Chào buổi sáng"), "fr": ("Bonjour", "Xin chào"),
    "es": ("Buenos días", "Chào buổi sáng"), "ru": ("Доброе утро", "Chào buổi sáng"), "th": ("สวัสดีตอนเช้า", "Chào buổi sáng"),
}


@pytest.fixture(autouse=True)
def _clean(fake_db):
    language_service.reset_caches()
    yield
    language_service.reset_caches()


def deck(db, lang="en", owner=USER_A, confirmed=True, title=None, **kw):
    return db.seed("flashcard_decks", user_id=owner, title=title or f"Sổ {lang}", lang_code=lang, lang_confirmed=confirmed, **kw)


def card(db, d, term="word", definition="nghĩa", **kw):
    row = dict(deck_id=d["id"], user_id=d["user_id"], term=term, definition=definition, lang_code=d["lang_code"], state=0, reps=0,
               lapses=0, stability=0.0, difficulty=0.0, due=NOW.isoformat(), last_review=None)
    row.update(kw)
    return db.seed("flashcards", **row)


def save(api, headers, lang, term, meaning, rid=None, **extra):
    body = {"client_request_id": rid or f"req-{lang}-{abs(hash((term, meaning, str(extra)))) % 10**8:08d}", "source_lang": lang,
            "term": term, "translation": meaning, **extra}
    return api.post(f"{BASE}/cards/from-translation", headers=headers, json=body)


def summary(api, headers):
    return api.get(f"{BASE}/languages", headers=headers).json()["data"]


# ================================================================== /languages
class TestSummary:
    def test_always_lists_all_ten_languages_in_order(self, api, fake_db, headers_a):
        data = summary(api, headers_a)
        assert [l["code"] for l in data["languages"]] == list(SUPPORTED_LANGS)
        assert {l["code"] for l in data["languages"] if not l["learnable"]} == {"vi"}
        assert all(l["decks"] == 0 and l["cards"] == 0 for l in data["languages"])
        assert data["unconfirmed"] == {"decks": [], "cards": 0}

    def test_counts_are_separated_per_language(self, api, fake_db, headers_a):
        en, de = deck(fake_db, "en"), deck(fake_db, "de")
        for n in range(3):
            card(fake_db, en, f"e{n}")
        for n in range(2):
            card(fake_db, de, f"d{n}")
        langs = {l["code"]: l for l in summary(api, headers_a)["languages"]}
        assert (langs["en"]["decks"], langs["en"]["cards"]) == (1, 3)
        assert (langs["de"]["decks"], langs["de"]["cards"]) == (1, 2)
        assert langs["ja"]["cards"] == 0

    def test_due_new_weak_and_last_activity(self, api, fake_db, headers_a):
        d = deck(fake_db, "fr")
        card(fake_db, d, "nouveau")
        card(fake_db, d, "du", state=2, stability=3.0, last_review=(NOW - datetime.timedelta(days=5)).isoformat(),
             due=(NOW - datetime.timedelta(days=1)).isoformat())
        card(fake_db, d, "futur", state=2, stability=9.0, last_review=(NOW - datetime.timedelta(days=2)).isoformat(),
             due=(NOW + datetime.timedelta(days=7)).isoformat())
        card(fake_db, d, "oublié", state=2, lapses=2, stability=2.0, last_review=(NOW - datetime.timedelta(days=1)).isoformat(),
             due=(NOW + datetime.timedelta(days=1)).isoformat())
        fr = next(l for l in summary(api, headers_a)["languages"] if l["code"] == "fr")
        assert (fr["cards"], fr["new"], fr["due"], fr["weak"]) == (4, 1, 1, 1)
        assert fr["last_activity"] is not None

    def test_mastered_uses_the_21_day_stability_threshold_and_ignores_new_cards(self, api, fake_db, headers_a):
        d = deck(fake_db, "ja")
        reviewed = (NOW - datetime.timedelta(days=3)).isoformat()
        card(fake_db, d, "新", state=0, stability=30.0)  # còn mới (chưa ôn): không tính dù stability lớn
        card(fake_db, d, "二十", state=2, stability=20.9, last_review=reviewed)  # sát ngưỡng: chưa thuộc
        card(fake_db, d, "二十一", state=2, stability=21.0, last_review=reviewed, due=(NOW + datetime.timedelta(days=9)).isoformat())
        card(fake_db, d, "九十", state=2, stability=90.0, last_review=reviewed, due=(NOW - datetime.timedelta(days=1)).isoformat())
        card(fake_db, deck(fake_db, "ko"), "한", state=2, stability=50.0, last_review=reviewed)
        langs = {l["code"]: l for l in summary(api, headers_a)["languages"]}
        assert langs["ja"]["mastered"] == 2 and langs["ja"]["due"] == 2  # "九十" vừa thuộc vừa đến hạn
        assert langs["ko"]["mastered"] == 1
        assert langs["en"]["mastered"] == 0

    def test_other_users_and_system_decks_are_not_counted(self, api, fake_db, headers_a):
        card(fake_db, deck(fake_db, "es", owner=USER_B), "ajeno")
        system = fake_db.seed("flashcard_decks", user_id=None, is_system=True, title="Sistema", lang_code="es", lang_confirmed=True)
        fake_db.seed("flashcards", deck_id=system["id"], user_id=None, term="x", definition="y", lang_code="es")
        assert next(l for l in summary(api, headers_a)["languages"] if l["code"] == "es")["cards"] == 0

    def test_unconfirmed_and_invalid_language_decks_are_not_assigned_to_any_language(self, api, fake_db, headers_a):
        legacy = deck(fake_db, "en", confirmed=False, title="Sổ cũ")
        weird = deck(fake_db, "xx", confirmed=True, title="Mã lạ")
        card(fake_db, legacy, "a")
        card(fake_db, legacy, "b")
        card(fake_db, weird, "c")
        data = summary(api, headers_a)
        assert all(l["cards"] == 0 and l["decks"] == 0 for l in data["languages"])
        assert {d["title"]: d["cards_count"] for d in data["unconfirmed"]["decks"]} == {"Sổ cũ": 2, "Mã lạ": 1}
        assert data["unconfirmed"]["cards"] == 3

    def test_default_deck_id_is_exposed(self, api, fake_db, headers_a):
        d = deck(fake_db, "ko", is_default=True)
        assert next(l for l in summary(api, headers_a)["languages"] if l["code"] == "ko")["default_deck_id"] == d["id"]

    def test_more_than_1000_cards_are_all_counted(self, api, fake_db, headers_a):
        d = deck(fake_db, "ru")
        fake_db.tables["flashcards"].extend(
            {"id": f"c{n}", "deck_id": d["id"], "user_id": USER_A, "term": f"t{n}", "definition": "d", "lang_code": "ru", "state": 0,
             "last_review": None, "lapses": 0} for n in range(1500))
        assert next(l for l in summary(api, headers_a)["languages"] if l["code"] == "ru")["cards"] == 1500

    def test_requires_auth(self, api, fake_db):
        assert api.get(f"{BASE}/languages").status_code == 401

    def test_missing_migration_gives_a_clear_error(self, api, fake_db, headers_a):
        fake_db.missing_columns["flashcard_decks"] = {"lang_confirmed", "is_default"}
        res = api.get(f"{BASE}/languages", headers=headers_a)
        assert res.status_code == 503 and res.json()["error"]["code"] == "MIGRATION_REQUIRED" and "005" in res.json()["error"]["message"]


# ================================================================== /languages/{code}/cards
class TestLanguageCards:
    def terms(self, api, headers, lang, **qs):
        query = "&".join(f"{k}={v}" for k, v in qs.items())
        res = api.get(f"{BASE}/languages/{lang}/cards?{query}", headers=headers)
        assert res.status_code == 200, res.text
        return [c["term"] for c in res.json()["data"]["items"]], res.json()["data"]

    def test_only_cards_of_the_selected_language(self, api, fake_db, headers_a):
        card(fake_db, deck(fake_db, "en"), "apple")
        card(fake_db, deck(fake_db, "de"), "Apfel")
        card(fake_db, deck(fake_db, "ja"), "りんご")
        assert self.terms(api, headers_a, "de")[0] == ["Apfel"]
        assert self.terms(api, headers_a, "en")[0] == ["apple"]
        assert self.terms(api, headers_a, "ja")[0] == ["りんご"]
        assert self.terms(api, headers_a, "ko")[0] == []

    def test_cards_include_deck_title_and_normalised_fields(self, api, fake_db, headers_a):
        card(fake_db, deck(fake_db, "fr", title="Mon sổ"), "bonjour", "xin chào", example="Bonjour!")
        _, data = self.terms(api, headers_a, "fr")
        item = data["items"][0]
        assert item["deck_title"] == "Mon sổ" and item["example_sentence"] == "Bonjour!" and item["lang_code"] == "fr"

    def test_combines_all_decks_of_the_language(self, api, fake_db, headers_a):
        card(fake_db, deck(fake_db, "es", title="A"), "uno")
        card(fake_db, deck(fake_db, "es", title="B"), "dos")
        assert sorted(self.terms(api, headers_a, "es")[0]) == ["dos", "uno"]

    def test_search_matches_term_and_definition_case_insensitively(self, api, fake_db, headers_a):
        d = deck(fake_db, "de")
        card(fake_db, d, "Haus", "ngôi nhà")
        card(fake_db, d, "Auto", "xe hơi")
        card(fake_db, d, "Hausaufgabe", "bài tập về nhà")
        assert sorted(self.terms(api, headers_a, "de", q="haus")[0]) == ["Haus", "Hausaufgabe"]
        assert self.terms(api, headers_a, "de", q="XE")[0] == ["Auto"]
        assert self.terms(api, headers_a, "de", q="zzz")[0] == []

    @pytest.mark.parametrize("q", ["a,b", "(x)", "50%", "a_b", "*", "\\\\", "x.or.y"])
    def test_search_special_characters_do_not_break_the_query(self, api, fake_db, headers_a, q):
        card(fake_db, deck(fake_db, "de"), "Haus")
        assert api.get(f"{BASE}/languages/de/cards", params={"q": q}, headers=headers_a).status_code == 200

    def test_sorting(self, api, fake_db, headers_a):
        d = deck(fake_db, "ru")
        card(fake_db, d, "б", due=(NOW + datetime.timedelta(days=3)).isoformat())
        card(fake_db, d, "а", due=(NOW + datetime.timedelta(days=9)).isoformat())
        card(fake_db, d, "в", due=(NOW + datetime.timedelta(days=1)).isoformat())
        assert self.terms(api, headers_a, "ru", sort="alpha")[0] == ["а", "б", "в"]
        assert self.terms(api, headers_a, "ru", sort="due")[0] == ["в", "б", "а"]
        assert self.terms(api, headers_a, "ru", sort="recent")[0] == ["в", "а", "б"]  # mới thêm trước

    def test_status_filters(self, api, fake_db, headers_a):
        d = deck(fake_db, "th")
        card(fake_db, d, "ใหม่")
        card(fake_db, d, "ถึงเวลา", state=2, last_review=NOW.isoformat(), due=(NOW - datetime.timedelta(days=1)).isoformat())
        card(fake_db, d, "ลืม", state=2, lapses=3, last_review=NOW.isoformat(), due=(NOW + datetime.timedelta(days=4)).isoformat())
        assert self.terms(api, headers_a, "th", status="new")[0] == ["ใหม่"]
        assert self.terms(api, headers_a, "th", status="due")[0] == ["ถึงเวลา"]
        assert self.terms(api, headers_a, "th", status="weak")[0] == ["ลืม"]
        assert len(self.terms(api, headers_a, "th", status="all")[0]) == 3

    def test_pagination_reports_total(self, api, fake_db, headers_a):
        d = deck(fake_db, "ko")
        for n in range(25):
            card(fake_db, d, f"w{n:02d}")
        first, data = self.terms(api, headers_a, "ko", sort="alpha", limit=10, offset=0)
        assert len(first) == 10 and data["total"] == 25
        last, _ = self.terms(api, headers_a, "ko", sort="alpha", limit=10, offset=20)
        assert last == [f"w{n:02d}" for n in range(20, 25)]

    def test_deck_filter_and_foreign_deck_is_404(self, api, fake_db, headers_a):
        a, b = deck(fake_db, "en", title="A"), deck(fake_db, "en", title="B")
        german = deck(fake_db, "de")
        card(fake_db, a, "x")
        card(fake_db, b, "y")
        assert self.terms(api, headers_a, "en", deck_id=a["id"])[0] == ["x"]
        assert api.get(f"{BASE}/languages/en/cards?deck_id={german['id']}", headers=headers_a).status_code == 404

    def test_unconfirmed_decks_are_not_in_any_collection(self, api, fake_db, headers_a):
        card(fake_db, deck(fake_db, "en", confirmed=False), "legacy")
        assert self.terms(api, headers_a, "en")[0] == []

    def test_users_are_isolated(self, api, fake_db, headers_a, headers_b):
        card(fake_db, deck(fake_db, "fr", owner=USER_A), "secret")
        assert self.terms(api, headers_b, "fr")[0] == []

    @pytest.mark.parametrize("path,code", [("xx", "LANG_UNSUPPORTED"), ("auto", "LANG_REQUIRED")])
    def test_invalid_language_is_422(self, api, fake_db, headers_a, path, code):
        res = api.get(f"{BASE}/languages/{path}/cards", headers=headers_a)
        assert res.status_code == 422 and res.json()["error"]["code"] == code

    @pytest.mark.parametrize("qs", ["sort=random", "status=bogus", "limit=0", "limit=500", "offset=-1"])
    def test_invalid_query_parameters(self, api, fake_db, headers_a, qs):
        assert api.get(f"{BASE}/languages/en/cards?{qs}", headers=headers_a).status_code == 422

    def test_empty_collection(self, api, fake_db, headers_a):
        _, data = self.terms(api, headers_a, "ja")
        assert data["items"] == [] and data["total"] == 0


# ================================================================== POST /cards/from-translation
class TestSaveFromTranslation:
    @pytest.mark.parametrize("lang", LEARNABLE_LANGS)
    def test_each_language_is_saved_into_its_own_collection(self, api, fake_db, headers_a, lang):
        term, meaning = SAMPLES[lang]
        res = save(api, headers_a, lang, term, meaning, phonetic="/fon/", example=f"{term}!")
        assert res.status_code == 200, res.text
        data = res.json()["data"]
        assert data["created"] is True and data["card"]["lang_code"] == lang and data["card"]["target_lang"] == "vi"

        (row,) = fake_db.rows("flashcards")
        assert (row["term"], row["definition"], row["lang_code"], row["target_lang"], row["source"]) == (term, meaning, lang, "vi", "translation")
        assert row["user_id"] == USER_A and row["state"] == 0 and row["audio_url"].split("/")[-1].startswith(f"{lang}_")
        (d,) = fake_db.rows("flashcard_decks", user_id=USER_A)
        assert d["lang_code"] == lang and d["is_default"] is True and d["lang_confirmed"] is True and d["id"] == row["deck_id"]

        # xuất hiện ở đúng bộ sưu tập và KHÔNG ở bộ sưu tập nào khác
        for other in SUPPORTED_LANGS:
            items = api.get(f"{BASE}/languages/{other}/cards", headers=headers_a).json()["data"]["items"]
            assert [c["term"] for c in items] == ([term] if other == lang else [])

    def test_german_example_from_the_brief(self, api, fake_db, headers_a):
        data = save(api, headers_a, "de", "Guten Morgen", "Chào buổi sáng").json()["data"]
        assert data["deck"]["title"] == "Từ vựng Tiếng Đức"
        langs = {l["code"]: l for l in summary(api, headers_a)["languages"]}
        assert langs["de"]["cards"] == 1 and langs["en"]["cards"] == 0

    def test_second_save_reuses_the_default_deck(self, api, fake_db, headers_a):
        save(api, headers_a, "ja", "水", "nước")
        save(api, headers_a, "ja", "火", "lửa")
        assert len(fake_db.rows("flashcard_decks", user_id=USER_A)) == 1 and len(fake_db.rows("flashcards")) == 2
        save(api, headers_a, "ko", "물", "nước")
        assert len(fake_db.rows("flashcard_decks", user_id=USER_A)) == 2  # mỗi ngôn ngữ một sổ mặc định

    def test_locale_codes_are_normalised(self, api, fake_db, headers_a):
        assert save(api, headers_a, "EN-us", "hello", "xin chào").json()["data"]["card"]["lang_code"] == "en"

    @pytest.mark.parametrize("lang", [None, "", "auto", "AUTO"])
    def test_missing_or_auto_language_is_refused_not_guessed(self, api, fake_db, headers_a, lang):
        body = {"client_request_id": "req-00000001", "term": "Hallo", "translation": "Xin chào"}
        if lang is not None:
            body["source_lang"] = lang
        res = api.post(f"{BASE}/cards/from-translation", headers=headers_a, json=body)
        assert res.status_code == 422 and res.json()["error"]["code"] == "LANG_REQUIRED"
        assert fake_db.rows("flashcards") == [] and fake_db.rows("flashcard_decks") == []

    @pytest.mark.parametrize("lang", ["xx", "gb", "klingon"])
    def test_unsupported_language(self, api, fake_db, headers_a, lang):
        res = save(api, headers_a, lang, "x", "y")
        assert res.status_code == 422 and res.json()["error"]["code"] == "LANG_UNSUPPORTED"

    def test_vietnamese_is_not_a_source_language(self, api, fake_db, headers_a):
        res = save(api, headers_a, "vi", "xin chào", "hello")
        assert res.status_code == 422 and res.json()["error"]["code"] == "LANG_UNSUPPORTED"

    def test_target_language_must_be_vietnamese(self, api, fake_db, headers_a):
        assert save(api, headers_a, "de", "Hallo", "Hello", target_lang="en").status_code == 422

    @pytest.mark.parametrize("term,meaning", [("", "nghĩa"), ("   ", "nghĩa"), ("Hallo", ""), ("Hallo", "  "), ("x" * 501, "y")])
    def test_empty_or_too_long_text_is_422(self, api, fake_db, headers_a, term, meaning):
        assert save(api, headers_a, "de", term, meaning).status_code == 422

    def test_explicit_deck_of_the_same_language(self, api, fake_db, headers_a):
        mine = deck(fake_db, "de", title="Bài học")
        data = save(api, headers_a, "de", "Haus", "ngôi nhà", deck_id=mine["id"]).json()["data"]
        assert data["deck"]["id"] == mine["id"] and fake_db.rows("flashcards")[0]["deck_id"] == mine["id"]
        assert len(fake_db.rows("flashcard_decks", user_id=USER_A)) == 1  # không tạo sổ mặc định thừa

    def test_deck_of_another_language_is_a_conflict(self, api, fake_db, headers_a):
        english = deck(fake_db, "en")
        res = save(api, headers_a, "de", "Haus", "nhà", deck_id=english["id"])
        assert res.status_code == 409 and res.json()["error"]["code"] == "LANG_MISMATCH"
        assert fake_db.rows("flashcards") == []

    def test_other_users_deck_is_forbidden(self, api, fake_db, headers_a):
        theirs = deck(fake_db, "de", owner=USER_B)
        assert save(api, headers_a, "de", "Haus", "nhà", deck_id=theirs["id"]).status_code == 403
        assert fake_db.rows("flashcards") == []

    def test_unconfirmed_deck_is_refused_even_if_the_code_matches(self, api, fake_db, headers_a):
        legacy = deck(fake_db, "de", confirmed=False)
        res = save(api, headers_a, "de", "Haus", "nhà", deck_id=legacy["id"])
        assert res.status_code == 409 and res.json()["error"]["code"] == "DECK_LANG_UNCONFIRMED"

    def test_duplicate_is_reported_with_the_existing_card(self, api, fake_db, headers_a):
        first = save(api, headers_a, "fr", "Bonjour", "Xin chào", rid="req-first-0001").json()["data"]["card"]
        res = save(api, headers_a, "fr", "  bonjour ", "Chào buổi sáng", rid="req-second-002")
        assert res.status_code == 409
        error = res.json()["error"]
        assert error["code"] == "DUPLICATE_CARD" and error["data"]["card"]["id"] == first["id"] and error["data"]["deck"]["title"]
        assert len(fake_db.rows("flashcards")) == 1 and fake_db.rows("flashcards")[0]["definition"] == "Xin chào"

    def test_duplicate_can_update_the_meaning(self, api, fake_db, headers_a):
        save(api, headers_a, "fr", "Bonjour", "Xin chào", rid="req-first-0001")
        res = save(api, headers_a, "fr", "bonjour", "Chào buổi sáng", rid="req-second-002", on_duplicate="update", phonetic="/bɔ̃.ʒuʁ/")
        data = res.json()["data"]
        assert res.status_code == 200 and data["created"] is False and data["updated"] is True
        (row,) = fake_db.rows("flashcards")
        assert row["definition"] == "Chào buổi sáng" and row["phonetic"] == "/bɔ̃.ʒuʁ/" and row["term"] == "Bonjour"

    def test_same_term_in_a_different_language_is_not_a_duplicate(self, api, fake_db, headers_a):
        assert save(api, headers_a, "fr", "Chat", "con mèo").status_code == 200
        assert save(api, headers_a, "de", "Chat", "cuộc trò chuyện").status_code == 200
        assert len(fake_db.rows("flashcards")) == 2

    def test_idempotent_by_client_request_id(self, api, fake_db, headers_a):
        first = save(api, headers_a, "es", "Hola", "Xin chào", rid="req-idem-00001").json()["data"]
        again = save(api, headers_a, "es", "Hola", "Xin chào", rid="req-idem-00001").json()["data"]
        assert again["idempotent_replay"] is True and again["card"]["id"] == first["card"]["id"]
        assert len(fake_db.rows("flashcards")) == 1

    def test_failed_save_is_not_cached(self, api, fake_db, headers_a):
        fake_db.fail_when("insert", "flashcards")
        assert save(api, headers_a, "es", "Hola", "Xin chào", rid="req-retry-0001").status_code == 503
        fake_db.fail.clear()
        assert save(api, headers_a, "es", "Hola", "Xin chào", rid="req-retry-0001").status_code == 200

    def test_default_deck_race_returns_the_existing_deck(self, api, fake_db, headers_a, monkeypatch):
        """Hai lần lưu đầu tiên chạy song song: người thua cuộc (vi phạm UNIQUE) phải dùng sổ do người thắng tạo."""
        from fastapi import HTTPException

        winners = []

        async def losing_create(*args, **kwargs):
            # Trong lúc ta định tạo, yêu cầu song song đã tạo xong sổ mặc định -> insert của ta vi phạm UNIQUE.
            winners.append(deck(fake_db, "ru", is_default=True, title="Sổ thắng cuộc"))
            raise HTTPException(status_code=500, detail="duplicate key value violates unique constraint")

        monkeypatch.setattr(language_service, "create_deck", losing_create)
        res = save(api, headers_a, "ru", "Привет", "Xin chào")
        assert res.status_code == 200, res.text
        assert res.json()["data"]["deck"]["id"] == winners[0]["id"]
        assert len(fake_db.rows("flashcard_decks", user_id=USER_A, lang_code="ru")) == 1

    def test_requires_auth(self, api, fake_db):
        res = api.post(f"{BASE}/cards/from-translation", json={"client_request_id": "req-00000001", "source_lang": "de", "term": "a", "translation": "b"})
        assert res.status_code == 401

    def test_missing_migration_is_a_clear_503(self, api, fake_db, headers_a):
        fake_db.missing_columns["flashcard_decks"] = {"is_default", "lang_confirmed"}
        res = save(api, headers_a, "de", "Hallo", "Xin chào")
        assert res.status_code == 503 and res.json()["error"]["code"] == "MIGRATION_REQUIRED"

    def test_tts_event_is_published_for_new_cards_only(self, api, fake_db, headers_a, monkeypatch):
        sent = []

        async def record(**kw):
            sent.append(kw)

        import app.routers.languages as router
        monkeypatch.setattr(router, "publish_flashcard_created_event", record)
        save(api, headers_a, "ja", "水", "nước", rid="req-event-0001")
        save(api, headers_a, "ja", "水", "nước", rid="req-event-0002")  # trùng -> 409, không phát event
        assert [(e["term"], e["lang_code"]) for e in sent] == [("水", "ja")]


# ================================================================== tương thích & dữ liệu cũ
class TestLegacyCompatibilityAndStrictness:
    def test_existing_cards_remain_accessible_through_their_deck(self, api, fake_db, headers_a):
        legacy = deck(fake_db, "en", confirmed=False, title="Sổ cũ")
        card(fake_db, legacy, "old")
        assert api.get(f"{BASE}/decks/{legacy['id']}/cards", headers=headers_a).json()["data"][0]["term"] == "old"
        assert api.get(f"{BASE}/decks/{legacy['id']}/study-queue", headers=headers_a).status_code == 200

    def test_confirming_a_legacy_deck_moves_it_and_its_cards(self, api, fake_db, headers_a):
        legacy = deck(fake_db, "en", confirmed=False, title="Sổ cũ")
        card(fake_db, legacy, "Haus", audio_url="/api/v1/translate/audio/terms/en_old.mp3")
        res = api.post(f"{BASE}/decks/{legacy['id']}/language", headers=headers_a, json={"lang_code": "de"})
        assert res.status_code == 200
        (d,) = fake_db.rows("flashcard_decks", id=legacy["id"])
        (c,) = fake_db.rows("flashcards", deck_id=legacy["id"])
        assert (d["lang_code"], d["lang_confirmed"], c["lang_code"]) == ("de", True, "de")
        assert c["audio_url"].split("/")[-1].startswith("de_")  # URL âm thanh chứa mã ngôn ngữ nên được tính lại
        langs = {l["code"]: l for l in summary(api, headers_a)["languages"]}
        assert langs["de"]["cards"] == 1 and langs["en"]["cards"] == 0
        assert summary(api, headers_a)["unconfirmed"]["decks"] == []

    def test_confirming_with_the_same_language_just_confirms(self, api, fake_db, headers_a):
        legacy = deck(fake_db, "en", confirmed=False)
        card(fake_db, legacy, "apple")
        assert api.post(f"{BASE}/decks/{legacy['id']}/language", headers=headers_a, json={"lang_code": "en"}).status_code == 200
        assert next(l for l in summary(api, headers_a)["languages"] if l["code"] == "en")["cards"] == 1

    def test_set_language_is_owner_only_and_validated(self, api, fake_db, headers_a, headers_b):
        mine = deck(fake_db, "en", confirmed=False)
        assert api.post(f"{BASE}/decks/{mine['id']}/language", headers=headers_b, json={"lang_code": "de"}).status_code == 403
        assert api.post(f"{BASE}/decks/{mine['id']}/language", headers=headers_a, json={"lang_code": "xx"}).status_code == 422
        system = fake_db.seed("flashcard_decks", user_id=None, is_system=True, title="S", lang_code="en", lang_confirmed=True)
        assert api.post(f"{BASE}/decks/{system['id']}/language", headers=headers_a, json={"lang_code": "de"}).status_code == 403
        assert fake_db.rows("flashcard_decks", id=mine["id"])[0]["lang_code"] == "en"

    def test_old_clients_without_migration_005_can_still_change_a_deck_language(self, api, fake_db, headers_a):
        fake_db.missing_columns["flashcard_decks"] = {"lang_confirmed", "is_default"}
        d = fake_db.seed("flashcard_decks", user_id=USER_A, title="x", lang_code="en")
        assert api.post(f"{BASE}/decks/{d['id']}/language", headers=headers_a, json={"lang_code": "fr"}).status_code == 200
        assert fake_db.rows("flashcard_decks", id=d["id"])[0]["lang_code"] == "fr"

    # ---- API cũ không còn tự gán 'en'
    def test_create_deck_requires_a_valid_language(self, api, fake_db, headers_a):
        assert api.post(f"{BASE}/decks", headers=headers_a, json={"title": "T"}).status_code == 422
        bad = api.post(f"{BASE}/decks", headers=headers_a, json={"title": "T", "lang_code": "xx"})
        assert bad.status_code == 422 and bad.json()["error"]["code"] == "LANG_UNSUPPORTED"
        ok = api.post(f"{BASE}/decks", headers=headers_a, json={"title": "T", "lang_code": "ja-JP"})
        assert ok.status_code == 200 and ok.json()["data"]["lang_code"] == "ja"
        assert fake_db.rows("flashcard_decks")[0]["lang_confirmed"] is True

    def test_create_card_takes_the_language_of_its_deck(self, api, fake_db, headers_a):
        german = deck(fake_db, "de")
        res = api.post(f"{BASE}/cards", headers=headers_a, json={"deck_id": german["id"], "front_text": "Haus", "back_text": "nhà"})
        assert res.status_code == 200 and fake_db.rows("flashcards")[0]["lang_code"] == "de"  # trước đây mặc định 'en'

    def test_create_card_language_mismatch_is_409(self, api, fake_db, headers_a):
        german = deck(fake_db, "de")
        res = api.post(f"{BASE}/cards", headers=headers_a, json={"deck_id": german["id"], "front_text": "Haus", "back_text": "nhà", "lang_code": "en"})
        assert res.status_code == 409 and res.json()["error"]["code"] == "LANG_MISMATCH" and fake_db.rows("flashcards") == []

    def test_create_card_in_a_deck_with_an_unknown_language_is_refused(self, api, fake_db, headers_a):
        weird = deck(fake_db, "xx")
        res = api.post(f"{BASE}/cards", headers=headers_a, json={"deck_id": weird["id"], "front_text": "a", "back_text": "b"})
        assert res.status_code == 409 and res.json()["error"]["code"] == "DECK_LANG_UNKNOWN"

    def test_update_card_cannot_change_language_but_same_language_is_fine(self, api, fake_db, headers_a):
        c = card(fake_db, deck(fake_db, "de"), "Haus")
        assert api.put(f"{BASE}/cards/{c['id']}", headers=headers_a, json={"back_text": "nhà", "lang_code": "de"}).status_code == 200
        res = api.put(f"{BASE}/cards/{c['id']}", headers=headers_a, json={"lang_code": "en"})
        assert res.status_code == 409 and fake_db.rows("flashcards")[0]["lang_code"] == "de"

    def test_changing_a_deck_language_through_the_edit_endpoint_cascades(self, api, fake_db, headers_a):
        d = deck(fake_db, "en")
        card(fake_db, d, "x")
        assert api.put(f"{BASE}/decks/{d['id']}", headers=headers_a, json={"lang_code": "es"}).status_code == 200
        assert fake_db.rows("flashcards")[0]["lang_code"] == "es" and fake_db.rows("flashcard_decks")[0]["lang_code"] == "es"

    def test_deck_list_can_be_filtered_on_the_server(self, api, fake_db, headers_a):
        deck(fake_db, "en", title="EN")
        deck(fake_db, "de", title="DE")
        titles = lambda qs: sorted(d["title"] for d in api.get(f"{BASE}/decks{qs}", headers=headers_a).json()["data"])
        assert titles("") == ["DE", "EN"] and titles("?lang_code=de") == ["DE"] and titles("?lang_code=de-AT") == ["DE"]
        assert titles("?lang_code=ja") == []
        assert api.get(f"{BASE}/decks?lang_code=xx", headers=headers_a).status_code == 422

    def test_excel_import_language_mismatch_is_409(self, api, fake_db, headers_a):
        import io
        import openpyxl
        wb = openpyxl.Workbook()
        wb.active.append(["Term", "Definition"])
        wb.active.append(["Haus", "nhà"])
        buf = io.BytesIO()
        wb.save(buf)
        german = deck(fake_db, "de")
        res = api.post(f"{BASE}/decks/{german['id']}/import-excel?lang_code=en", headers=headers_a, files={"file": ("w.xlsx", buf.getvalue())})
        assert res.status_code == 409 and fake_db.rows("flashcards") == []


# ================================================================== consumer doc.translated
class TestDocTranslatedLanguage:
    class Msg:
        def __init__(self, payload):
            import json
            self.body = json.dumps(payload).encode()

        def process(self):
            class Ctx:
                async def __aenter__(s):
                    return s

                async def __aexit__(s, *a):
                    return False

            return Ctx()

    payload = {"user_id": USER_A, "file_name": "bai.pdf", "doc_id": "d1", "glossary_json": [{"term": "Haus", "definition": "nhà"}]}

    @pytest.mark.parametrize("source_lang", [None, "", "auto", "xx", "vi"])
    async def test_unknown_language_creates_nothing(self, fake_db, source_lang):
        await rabbitmq_consumer.process_doc_translated_event(self.Msg({**self.payload, "source_lang": source_lang}))
        assert fake_db.rows("flashcard_decks") == [] and fake_db.rows("flashcards") == []

    async def test_known_language_goes_to_its_collection(self, fake_db):
        await rabbitmq_consumer.process_doc_translated_event(self.Msg({**self.payload, "source_lang": "de"}))
        (d,) = fake_db.rows("flashcard_decks")
        assert d["lang_code"] == "de" and fake_db.rows("flashcards")[0]["lang_code"] == "de"
