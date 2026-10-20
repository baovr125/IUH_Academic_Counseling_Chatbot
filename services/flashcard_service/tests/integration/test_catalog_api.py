import pytest

from app.services import catalog_service
from conftest import USER_A, USER_B, make_headers

BASE = "/api/v1/flashcards"
LIST = f"{BASE}/catalog/decks"


def system_deck(db, slug="family", title="Gia đình", category="communication", level="A1", status="published", cards=4):
    deck = db.seed("flashcard_decks", user_id=None, is_system=True, status=status, slug=slug, title=title, lang_code="en",
                   category=category, level=level, description=f"{title}. Nội dung do AI tạo.")
    for n in range(cards):
        db.seed("flashcards", deck_id=deck["id"], user_id=None, term=f"{slug}-{n}", definition=f"nghĩa {n}", part_of_speech="noun",
                lang_code="en", example=f"A {slug}-{n} here.", example_translation=f"Dịch {n}", state=2, reps=5, lapses=1,
                stability=40.0, difficulty=3.0, last_review="2026-01-01T00:00:00+00:00", due="2026-02-01T00:00:00+00:00",
                phonetic="/ˈtɛst/", audio_url="/audio.mp3")
    return deck


class TestList:
    def test_only_published_system_decks_with_counts(self, api, fake_db, headers_a):
        a = system_deck(fake_db, "a", "A", cards=3)
        system_deck(fake_db, "draft", "Draft", status="draft")
        system_deck(fake_db, "old", "Old", status="archived")
        fake_db.seed("flashcard_decks", user_id=USER_B, title="Personal deck", lang_code="en")
        data = api.get(LIST, headers=headers_a).json()["data"]
        assert [d["id"] for d in data] == [a["id"]]
        assert data[0]["cards_count"] == 3 and data[0]["added_deck_id"] is None
        assert "user_id" not in data[0] and "is_system" not in data[0]

    def test_filters(self, api, fake_db, headers_a):
        system_deck(fake_db, "f", "Family", "communication", "A1")
        system_deck(fake_db, "r", "Restaurant", "food", "A2")
        system_deck(fake_db, "t", "Travel", "going_out", "B1")

        def titles(qs):
            return sorted(d["title"] for d in api.get(f"{LIST}{qs}", headers=headers_a).json()["data"])

        assert titles("?category=food") == ["Restaurant"]
        assert titles("?level=B1") == ["Travel"]
        assert titles("?q=fam") == ["Family"]
        assert titles("?category=food&level=A1") == []
        assert len(titles("")) == 3

    @pytest.mark.parametrize("qs", ["?level=Z9", "?level=a1", "?category=" + "x" * 41, "?q=" + "x" * 61])
    def test_invalid_filters_are_422(self, api, fake_db, headers_a, qs):
        assert api.get(f"{LIST}{qs}", headers=headers_a).status_code == 422

    def test_search_wildcards_are_neutralised(self, api, fake_db, headers_a):
        system_deck(fake_db, "f", "Family")
        assert api.get(f"{LIST}?q=%25", headers=headers_a).status_code == 200  # '%' không thành ký tự đại diện

    def test_requires_auth(self, api, fake_db):
        assert api.get(LIST).status_code == 401

    def test_empty_catalog(self, api, fake_db, headers_a):
        assert api.get(LIST, headers=headers_a).json() == {"ok": True, "data": [], "error": None}


class TestPreview:
    def test_returns_first_cards_without_internal_fields(self, api, fake_db, headers_a):
        deck = system_deck(fake_db, cards=15)
        data = api.get(f"{LIST}/{deck['id']}/preview?limit=5", headers=headers_a).json()["data"]
        assert len(data["cards"]) == 5 and data["deck"]["cards_count"] == 15
        assert [c["term"] for c in data["cards"]] == [f"family-{n}" for n in range(5)]
        assert not ({"stability", "due", "user_id", "state"} & data["cards"][0].keys())

    @pytest.mark.parametrize("limit", [0, 51])
    def test_limit_bounds(self, api, fake_db, headers_a, limit):
        deck = system_deck(fake_db)
        assert api.get(f"{LIST}/{deck['id']}/preview?limit={limit}", headers=headers_a).status_code == 422

    def test_drafts_archived_personal_and_unknown_are_404(self, api, fake_db, headers_a):
        draft = system_deck(fake_db, "d", status="draft")
        archived = system_deck(fake_db, "z", status="archived")
        personal = fake_db.seed("flashcard_decks", user_id=USER_B, title="Private", lang_code="en")
        for deck_id in (draft["id"], archived["id"], personal["id"], "00000000-0000-4000-8000-000000000000", "not-a-uuid"):
            assert api.get(f"{LIST}/{deck_id}/preview", headers=headers_a).status_code == 404

    def test_preview_does_not_touch_user_data(self, api, fake_db, headers_a):
        deck = system_deck(fake_db)
        before = len(fake_db.rows("flashcard_decks"))
        api.get(f"{LIST}/{deck['id']}/preview", headers=headers_a)
        assert len(fake_db.rows("flashcard_decks")) == before


class TestClone:
    def clone(self, api, deck_id, headers):
        return api.post(f"{LIST}/{deck_id}/clone", headers=headers)

    def test_creates_an_independent_deck_with_fresh_fsrs_state(self, api, fake_db, headers_a):
        deck = system_deck(fake_db, cards=5)
        res = self.clone(api, deck["id"], headers_a)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["created"] is True and data["inserted"] == 5 and data["deck"]["cards_count"] == 5

        (mine,) = fake_db.rows("flashcard_decks", user_id=USER_A)
        assert mine["origin_deck_id"] == deck["id"] and mine["is_system"] is False
        assert (mine["title"], mine["category"], mine["level"]) == ("Gia đình", "communication", "A1")
        copies = fake_db.rows("flashcards", deck_id=mine["id"])
        assert len(copies) == 5
        for c in copies:
            assert c["user_id"] == USER_A and c["source"] == "curated" and c["level"] == "A1"
            assert (c["state"], c["reps"], c["lapses"], c["stability"], c["difficulty"]) == (0, 0, 0, 0.0, 0.0)  # không thừa hưởng tiến độ
            assert c["last_review"] is None and c["example_translation"] and c["phonetic"]
        assert {c["id"] for c in copies}.isdisjoint({c["id"] for c in fake_db.rows("flashcards", deck_id=deck["id"])})

    def test_idempotent_and_marks_added_in_list(self, api, fake_db, headers_a):
        deck = system_deck(fake_db)
        first = self.clone(api, deck["id"], headers_a).json()["data"]
        second = self.clone(api, deck["id"], headers_a).json()["data"]
        assert second["created"] is False and second["inserted"] == 0 and second["deck"]["id"] == first["deck"]["id"]
        assert len(fake_db.rows("flashcard_decks", user_id=USER_A)) == 1
        listed = api.get(LIST, headers=headers_a).json()["data"][0]
        assert listed["added_deck_id"] == first["deck"]["id"]
        assert api.get(LIST, headers=make_headers(USER_B)).json()["data"][0]["added_deck_id"] is None

    def test_two_users_get_separate_copies_and_progress(self, api, fake_db, headers_a, headers_b):
        deck = system_deck(fake_db, cards=4)
        a = self.clone(api, deck["id"], headers_a).json()["data"]["deck"]["id"]
        b = self.clone(api, deck["id"], headers_b).json()["data"]["deck"]["id"]
        assert a != b
        card_a = api.get(f"{BASE}/decks/{a}/study-queue", headers=headers_a).json()["data"][0]
        assert api.post(f"{BASE}/review", headers=headers_a, json={"card_id": card_a["id"], "grade": 4}).status_code == 200
        stats_b = api.get(f"{BASE}/decks/{b}/study-stats", headers=headers_b).json()["data"]
        assert (stats_b["new"], stats_b["learning"]) == (4, 0)  # tiến độ của A không ảnh hưởng B
        # ...và không ảnh hưởng bản gốc của hệ thống
        assert {c["state"] for c in fake_db.rows("flashcards", deck_id=deck["id"])} == {2}
        assert all(c["stability"] == 40.0 for c in fake_db.rows("flashcards", deck_id=deck["id"]))

    def test_editing_or_deleting_the_copy_never_touches_the_original(self, api, fake_db, headers_a):
        deck = system_deck(fake_db, cards=3)
        mine = self.clone(api, deck["id"], headers_a).json()["data"]["deck"]["id"]
        card = api.get(f"{BASE}/decks/{mine}/cards", headers=headers_a).json()["data"][0]
        assert api.put(f"{BASE}/cards/{card['id']}", headers=headers_a, json={"back_text": "đã sửa"}).status_code == 200
        assert api.delete(f"{BASE}/decks/{mine}", headers=headers_a).status_code == 200
        originals = fake_db.rows("flashcards", deck_id=deck["id"])
        assert len(originals) == 3 and all(c["definition"].startswith("nghĩa") for c in originals)
        assert fake_db.rows("flashcard_decks", id=deck["id"])
        assert self.clone(api, deck["id"], headers_a).json()["data"]["created"] is True  # xóa bản sao rồi có thể thêm lại

    def test_clone_appears_in_my_decks_but_the_system_deck_never_does(self, api, fake_db, headers_a):
        deck = system_deck(fake_db)
        assert api.get(f"{BASE}/decks", headers=headers_a).json()["data"] == []
        self.clone(api, deck["id"], headers_a)
        mine = api.get(f"{BASE}/decks", headers=headers_a).json()["data"]
        assert len(mine) == 1 and mine[0]["id"] != deck["id"] and mine[0]["cards_count"] == 4

    @pytest.mark.parametrize("status", ["draft", "archived"])
    def test_unpublished_decks_cannot_be_cloned(self, api, fake_db, headers_a, status):
        deck = system_deck(fake_db, status=status)
        assert self.clone(api, deck["id"], headers_a).status_code == 404
        assert fake_db.rows("flashcard_decks", user_id=USER_A) == []

    def test_personal_and_unknown_decks_cannot_be_cloned(self, api, fake_db, headers_a):
        personal = fake_db.seed("flashcard_decks", user_id=USER_B, title="Private", lang_code="en")
        assert self.clone(api, personal["id"], headers_a).status_code == 404
        assert self.clone(api, "not-a-uuid", headers_a).status_code == 404

    def test_empty_system_deck_is_409_and_creates_nothing(self, api, fake_db, headers_a):
        deck = system_deck(fake_db, cards=0)
        assert self.clone(api, deck["id"], headers_a).status_code == 409
        assert fake_db.rows("flashcard_decks", user_id=USER_A) == []

    def test_failure_while_copying_cards_removes_the_half_made_deck(self, api, fake_db, headers_a):
        deck = system_deck(fake_db)
        fake_db.fail_when("insert", "flashcards")
        assert self.clone(api, deck["id"], headers_a).status_code == 503
        assert fake_db.rows("flashcard_decks", user_id=USER_A) == []
        fake_db.fail.clear()
        assert self.clone(api, deck["id"], headers_a).json()["data"]["created"] is True

    def test_double_click_race_returns_the_existing_copy(self, api, fake_db, headers_a, monkeypatch):
        deck = system_deck(fake_db)
        winner = self.clone(api, deck["id"], headers_a).json()["data"]["deck"]["id"]
        real = catalog_service._existing_clone
        calls = {"n": 0}

        async def blind_first_time(supabase, uid, origin):
            calls["n"] += 1
            return None if calls["n"] == 1 else await real(supabase, uid, origin)

        monkeypatch.setattr(catalog_service, "_existing_clone", blind_first_time)
        res = self.clone(api, deck["id"], headers_a)  # chỉ mục UNIQUE chặn bản sao thứ hai
        assert res.status_code == 200 and res.json()["data"] == {**res.json()["data"], "created": False}
        assert res.json()["data"]["deck"]["id"] == winner and len(fake_db.rows("flashcard_decks", user_id=USER_A)) == 1

    def test_requires_auth(self, api, fake_db):
        deck = system_deck(fake_db)
        assert api.post(f"{LIST}/{deck['id']}/clone").status_code == 401


class TestMigrationMissing:
    @pytest.mark.parametrize("call", [
        lambda api, h: api.get(LIST, headers=h),
        lambda api, h: api.get(f"{LIST}/00000000-0000-4000-8000-000000000000/preview", headers=h),
        lambda api, h: api.post(f"{LIST}/00000000-0000-4000-8000-000000000000/clone", headers=h),
    ])
    def test_clear_message_when_migration_004_is_not_applied(self, api, fake_db, headers_a, call):
        fake_db.missing_columns["flashcard_decks"] = {"is_system", "status", "category", "level", "slug", "origin_deck_id"}
        res = call(api, headers_a)
        assert res.status_code == 503 and "004" in res.json()["detail"]

    def test_other_features_keep_working_without_migration_004(self, api, fake_db, headers_a):
        fake_db.missing_columns["flashcard_decks"] = {"is_system", "status", "category", "level", "slug", "origin_deck_id"}
        assert api.post(f"{BASE}/decks", headers=headers_a, json={"title": "Mine", "lang_code": "en"}).status_code == 200
        assert api.get(f"{BASE}/decks", headers=headers_a).status_code == 200


class TestSystemDecksAreReadOnlyThroughPersonalApis:
    @pytest.fixture
    def sys(self, fake_db):
        deck = system_deck(fake_db, cards=2)
        card = fake_db.rows("flashcards", deck_id=deck["id"])[0]
        return deck, card

    @pytest.mark.parametrize("user", [USER_A, USER_B])
    def test_every_personal_endpoint_is_forbidden(self, api, fake_db, sys, user):
        deck, card = sys
        h = make_headers(user)
        deck_id, card_id = deck["id"], card["id"]
        calls = [
            api.get(f"{BASE}/decks/{deck_id}/cards", headers=h),
            api.get(f"{BASE}/decks/{deck_id}/study-queue", headers=h),
            api.get(f"{BASE}/decks/{deck_id}/study-stats", headers=h),
            api.put(f"{BASE}/decks/{deck_id}", headers=h, json={"title": "hack"}),
            api.delete(f"{BASE}/decks/{deck_id}", headers=h),
            api.post(f"{BASE}/cards", headers=h, json={"deck_id": deck_id, "front_text": "x", "back_text": "y"}),
            api.put(f"{BASE}/cards/{card_id}", headers=h, json={"front_text": "hack"}),
            api.delete(f"{BASE}/cards/{card_id}", headers=h),
            api.post(f"{BASE}/review", headers=h, json={"card_id": card_id, "grade": 3}),
            api.post(f"{BASE}/cards/{card_id}/verify-spelling", headers=h, json={"user_input": card["term"]}),
        ]
        assert [c.status_code for c in calls] == [403] * len(calls)
        assert len(fake_db.rows("flashcards", deck_id=deck_id)) == 2
        assert fake_db.rows("flashcard_decks", id=deck_id)[0]["title"] == "Gia đình"
        assert fake_db.rows("flashcards", id=card_id)[0]["stability"] == 40.0
