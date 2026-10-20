"""API trò chơi: bộ thẻ cho ván, ghi kết quả (máy chủ tự tính), cập nhật lịch ôn FSRS có kiểm soát, kỷ lục và thống kê."""
import datetime

import pytest

from conftest import USER_A, USER_B

BASE = "/api/v1/flashcards"
NOW = datetime.datetime.now(datetime.timezone.utc)


def deck(db, lang="en", owner=USER_A, confirmed=True, title="Sổ chơi"):
    return db.seed("flashcard_decks", user_id=owner, title=title, lang_code=lang, lang_confirmed=confirmed)


def card(db, d, term, definition, due_days=-1, state=2, **kw):
    return db.seed(
        "flashcards", deck_id=d["id"], user_id=d["user_id"], term=term, definition=definition, lang_code=d["lang_code"],
        state=state, reps=1, lapses=0, stability=2.0, difficulty=3.0,
        due=(NOW + datetime.timedelta(days=due_days)).isoformat(), last_review=(NOW - datetime.timedelta(days=3)).isoformat() if state else None, **kw,
    )


def filled(db, lang="en", n=6, words=None, **kw):
    d = deck(db, lang)
    words = words or [f"word{chr(97 + i) * 3}" for i in range(n)]
    return d, [card(db, d, w, f"nghĩa của {w}", **kw) for w in words]


def play(api, headers, d, game, items, rid="game-request-0001", **extra):
    body = {"client_request_id": rid, "game": game, "mode": "relax", "deck_id": d["id"], "duration_ms": 30000, "items": items, **extra}
    return api.post(f"{BASE}/games/sessions", headers=headers, json=body)


def it(c, correct=True, attempts=0, hints=0):
    return {"card_id": c["id"], "correct": correct, "attempts": attempts, "hints": hints}


# ============================================================ GET /games/{game}/cards
class TestGameCards:
    def get(self, api, headers, game, d, **qs):
        return api.get(f"{BASE}/games/{game}/cards", headers=headers, params={"deck_id": d["id"], **qs})

    @pytest.mark.parametrize("game", ["match", "speed", "builder"])
    def test_playable_deck(self, api, fake_db, headers_a, game):
        d, _ = filled(fake_db)
        data = self.get(api, headers_a, game, d).json()["data"]
        assert data["playable"] is True and data["game"] == game and data["lang_code"] == "en"
        assert len(data["cards"]) >= 4 and data["due_count"] == len(data["cards"])  # tất cả đều đã đến hạn

    def test_speed_cards_have_four_shuffled_choices_including_the_answer(self, api, fake_db, headers_a):
        d, _ = filled(fake_db, n=8)
        for c in self.get(api, headers_a, "speed", d).json()["data"]["cards"]:
            assert len(c["choices"]) == 4 and c["definition"] in c["choices"] and len(set(c["choices"])) == 4

    def test_match_respects_count_and_defaults_to_six(self, api, fake_db, headers_a):
        d, _ = filled(fake_db, n=12)
        assert len(self.get(api, headers_a, "match", d).json()["data"]["cards"]) == 6
        assert len(self.get(api, headers_a, "match", d, count=100).json()["data"]["cards"]) == 8  # trần của trò

    def test_due_cards_come_first(self, api, fake_db, headers_a):
        d = deck(fake_db)
        later = [card(fake_db, d, f"later{n}", f"sau {n}", due_days=5) for n in range(4)]
        due = [card(fake_db, d, f"due{n}", f"đến hạn {n}", due_days=-1) for n in range(2)]
        data = self.get(api, headers_a, "match", d, count=4).json()["data"]
        ids = [c["id"] for c in data["cards"]]
        assert set(ids[:2]) == {c["id"] for c in due} and data["due_count"] == 2
        assert all(c["is_due"] for c in data["cards"][:2]) and not any(c["is_due"] for c in data["cards"][2:])

    @pytest.mark.parametrize("game", ["match", "speed", "builder"])
    def test_too_few_cards_is_not_playable_with_reason(self, api, fake_db, headers_a, game):
        d, _ = filled(fake_db, n=3)
        data = self.get(api, headers_a, game, d).json()["data"]
        assert data["playable"] is False and data["cards"] == [] and "ít nhất 4" in data["reason"]

    def test_duplicate_definitions_do_not_count_twice(self, api, fake_db, headers_a):
        d = deck(fake_db)
        for w in ("aaa", "bbb", "ccc", "ddd"):
            card(fake_db, d, w, "cùng một nghĩa")
        assert self.get(api, headers_a, "match", d).json()["data"]["playable"] is False

    @pytest.mark.parametrize("lang", ["zh", "ja", "ko", "th"])
    def test_builder_unsupported_for_non_alphabetic_languages(self, api, fake_db, headers_a, lang):
        d, _ = filled(fake_db, lang=lang, words=["早上好", "你好吗", "谢谢你", "再见啊", "对不起"])
        data = self.get(api, headers_a, "builder", d).json()["data"]
        assert data["playable"] is False and "chữ cái" in data["reason"]
        assert self.get(api, headers_a, "match", d).json()["data"]["playable"] is True  # trò khác vẫn chơi được

    def test_builder_picks_only_simple_words(self, api, fake_db, headers_a):
        d, _ = filled(fake_db, lang="de", words=["Haus", "Tür", "guten Morgen", "Baum", "Hund", "ab"])
        terms = {c["term"] for c in self.get(api, headers_a, "builder", d).json()["data"]["cards"]}
        assert terms == {"Haus", "Tür", "Baum", "Hund"}

    def test_unknown_game_404(self, api, fake_db, headers_a):
        d, _ = filled(fake_db)
        res = self.get(api, headers_a, "poker", d)
        assert res.status_code == 404 and res.json()["error"]["code"] == "GAME_NOT_FOUND"

    def test_other_users_deck_is_forbidden(self, api, fake_db, headers_b):
        d, _ = filled(fake_db)
        assert self.get(api, headers_b, "match", d).status_code == 403

    def test_requires_auth(self, api, fake_db):
        d, _ = filled(fake_db)
        assert api.get(f"{BASE}/games/match/cards", params={"deck_id": d["id"]}).status_code == 401


# ============================================================ POST /games/sessions
class TestSubmitSession:
    def test_server_computes_score_stars_and_xp(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, n=6)
        res = play(api, headers_a, d, "match", [it(c) for c in cards])
        assert res.status_code == 200, res.text
        data = res.json()["data"]
        s = data["session"]
        assert (s["score"], s["stars"], s["correct"], s["total"], s["xp"], s["lang_code"]) == (600, 3, 6, 6, 90, "en")
        assert data["is_record"] is True and data["previous_best"] == 0 and data["level"]["level"] == 1
        (row,) = fake_db.rows("flashcard_game_sessions")
        assert row["user_id"] == USER_A and row["deck_id"] == d["id"] and row["score"] == 600

    def test_client_cannot_inject_score(self, api, fake_db, headers_a):
        d, cards = filled(fake_db)
        res = play(api, headers_a, d, "match", [it(cards[0], correct=False)], score=999999, stars=3, xp=99999)
        assert res.status_code == 200
        s = res.json()["data"]["session"]
        assert (s["score"], s["stars"], s["xp"]) == (0, 0, 0)

    def test_language_comes_from_the_deck_not_the_client(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, lang="de", words=["Haus", "Baum", "Tür", "Hund"])
        res = play(api, headers_a, d, "speed", [it(c) for c in cards], lang_code="ja")
        assert res.json()["data"]["session"]["lang_code"] == "de"

    def test_due_cards_get_fsrs_reviews_with_correct_grades(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, n=4)
        items = [it(cards[0]), it(cards[1], attempts=1), it(cards[2], hints=1), it(cards[3], correct=False)]
        data = play(api, headers_a, d, "builder", items).json()["data"]
        assert data["review_eligible"] == 4 and data["session"]["reviewed_count"] == 4
        grades = {r["card_id"]: r["grade"] for r in fake_db.rows("review_logs")}
        assert grades == {cards[0]["id"]: 3, cards[1]["id"]: 2, cards[2]["id"]: 2, cards[3]["id"]: 1}
        assert 4 not in grades.values()  # không bao giờ Easy
        assert fake_db.rows("flashcard_game_sessions")[0]["reviewed_count"] == 4

    def test_only_due_non_new_cards_change_schedule(self, api, fake_db, headers_a):
        d = deck(fake_db)
        due = card(fake_db, d, "aaa1", "a")
        future = card(fake_db, d, "bbb2", "b", due_days=4)
        fresh = card(fake_db, d, "ccc3", "c", state=0, due_days=-1)
        filler = card(fake_db, d, "ddd4", "d", due_days=9)
        before = {c["id"]: (c["due"], c["state"]) for c in (future, fresh, filler)}
        data = play(api, headers_a, d, "match", [it(c) for c in (due, future, fresh, filler)]).json()["data"]
        assert data["review_eligible"] == 1
        assert [r["card_id"] for r in fake_db.rows("review_logs")] == [due["id"]]
        assert {c["id"]: (c["due"], c["state"]) for c in (future, fresh, filler)} == before

    def test_each_card_counts_once_per_session(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, n=4)
        play(api, headers_a, d, "speed", [it(cards[0], correct=False, attempts=1), it(cards[0]), it(cards[0]), it(cards[1])])
        logs = [(r["card_id"], r["grade"]) for r in fake_db.rows("review_logs")]
        assert logs == [(cards[0]["id"], 1), (cards[1]["id"], 3)]

    def test_apply_review_off_leaves_schedule_untouched(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, n=4)
        data = play(api, headers_a, d, "match", [it(c) for c in cards], apply_review=False).json()["data"]
        assert data["session"]["reviewed_count"] == 0 and fake_db.rows("review_logs") == []
        assert fake_db.rows("flashcard_game_sessions")[0]["applied_review"] is False

    def test_idempotent_replay_does_not_double_count(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, n=4)
        first = play(api, headers_a, d, "match", [it(c) for c in cards], rid="game-same-request").json()["data"]
        again = play(api, headers_a, d, "match", [it(c) for c in cards], rid="game-same-request").json()["data"]
        assert again["idempotent_replay"] is True and again["session"]["id"] == first["session"]["id"]
        assert len(fake_db.rows("flashcard_game_sessions")) == 1 and len(fake_db.rows("review_logs")) == 4

    def test_record_only_when_beating_previous_best_per_game_and_mode(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, n=6)
        good = [it(c) for c in cards]
        worse = [it(c, attempts=4) for c in cards]
        assert play(api, headers_a, d, "match", good, rid="game-run-000001").json()["data"]["is_record"] is True
        again = play(api, headers_a, d, "match", worse, rid="game-run-000002").json()["data"]
        assert again["is_record"] is False and again["previous_best"] == 600
        assert play(api, headers_a, d, "match", good, rid="game-run-000003", mode="challenge", duration_ms=20000).json()["data"]["is_record"] is True
        assert play(api, headers_a, d, "speed", [it(cards[0])], rid="game-run-000004").json()["data"]["is_record"] is True  # trò khác, kỷ lục riêng

    def test_unknown_cards_are_ignored_and_empty_is_422(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, n=4)
        other_d, other_cards = filled(fake_db, n=4)
        data = play(api, headers_a, d, "match", [it(cards[0]), it(other_cards[0])]).json()["data"]
        assert data["ignored_items"] == 1 and data["session"]["total"] == 1
        res = play(api, headers_a, d, "match", [it(other_cards[1])], rid="game-run-empty-1")
        assert res.status_code == 422 and res.json()["error"]["code"] == "GAME_EMPTY"

    def test_builder_rejected_for_non_alphabetic_language(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, lang="ja", words=["おはよう", "こんにちは", "ありがとう", "さようなら"])
        res = play(api, headers_a, d, "builder", [it(cards[0])])
        assert res.status_code == 422 and res.json()["error"]["code"] == "GAME_UNSUPPORTED_LANG"
        assert fake_db.rows("flashcard_game_sessions") == []

    def test_other_users_deck_is_forbidden_and_nothing_is_saved(self, api, fake_db, headers_b):
        d, cards = filled(fake_db)
        assert play(api, headers_b, d, "match", [it(cards[0])]).status_code == 403
        assert fake_db.rows("flashcard_game_sessions") == [] and fake_db.rows("review_logs") == []

    def test_unconfirmed_invalid_language_deck_is_refused(self, api, fake_db, headers_a):
        d = deck(fake_db, lang="xx")
        c = card(fake_db, d, "aaa", "a")
        res = play(api, headers_a, d, "match", [it(c)])
        assert res.status_code == 409 and res.json()["error"]["code"] == "DECK_LANG_UNKNOWN"

    @pytest.mark.parametrize("patch", [
        {"game": "poker"}, {"mode": "hard"}, {"items": []}, {"client_request_id": "short"}, {"duration_ms": -1},
        {"items": [{"card_id": "x", "correct": True, "attempts": -1}]},
    ])
    def test_validation(self, api, fake_db, headers_a, patch):
        d, cards = filled(fake_db)
        body = {"client_request_id": "game-valid-0001", "game": "match", "mode": "relax", "deck_id": d["id"], "duration_ms": 1000, "items": [it(cards[0])], **patch}
        assert api.post(f"{BASE}/games/sessions", headers=headers_a_of(headers_a), json=body).status_code == 422

    def test_requires_auth(self, api, fake_db):
        assert api.post(f"{BASE}/games/sessions", json={}).status_code == 401

    def test_session_is_saved_even_if_a_review_fails(self, api, fake_db, headers_a, monkeypatch):
        from app.services import game_service

        async def boom(*a, **k):
            raise RuntimeError("db down")

        monkeypatch.setattr(game_service, "review_card", boom)
        d, cards = filled(fake_db, n=4)
        res = play(api, headers_a, d, "match", [it(c) for c in cards])
        assert res.status_code == 200 and res.json()["data"]["session"]["reviewed_count"] == 0
        assert len(fake_db.rows("flashcard_game_sessions")) == 1

    def test_missing_migration_is_a_clear_503_and_changes_nothing(self, api, fake_db, headers_a):
        fake_db.missing_tables.add("flashcard_game_sessions")
        d, cards = filled(fake_db, n=4)
        res = play(api, headers_a, d, "match", [it(c) for c in cards])
        assert res.status_code == 503 and res.json()["error"]["code"] == "MIGRATION_REQUIRED" and "006" in res.json()["error"]["message"]
        assert fake_db.rows("review_logs") == []

    def test_insert_failure_means_no_schedule_change(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, n=4)
        fake_db.fail_when("insert", "flashcard_game_sessions")
        assert play(api, headers_a, d, "match", [it(c) for c in cards]).status_code == 503
        assert fake_db.rows("review_logs") == []


def headers_a_of(h):  # tiện cho parametrize ở trên (giữ test ngắn gọn)
    return h


# ============================================================ GET /games/stats
class TestStats:
    def stats(self, api, headers, **qs):
        res = api.get(f"{BASE}/games/stats", headers=headers, params=qs)
        assert res.status_code == 200, res.text
        return res.json()["data"]

    def test_empty(self, api, fake_db, headers_a):
        s = self.stats(api, headers_a)
        assert s["plays_total"] == 0 and s["level"]["level"] == 1 and s["games"]["match"]["best"] == {"relax": None, "challenge": None}

    def test_bests_xp_level_and_plays(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, n=6)
        play(api, headers_a, d, "match", [it(c) for c in cards], rid="game-stat-0001")  # 600 điểm, 3 sao, 90 xp
        play(api, headers_a, d, "match", [it(c, attempts=2) for c in cards], rid="game-stat-0002")  # thấp hơn
        play(api, headers_a, d, "speed", [it(cards[i % 6]) for i in range(12)], mode="challenge", rid="game-stat-0003")
        # Đồng hồ của DB giả chạy từ 2026-01-01; đặt thời điểm thật để kiểm tra "hôm nay" (giờ Việt Nam).
        rows = fake_db.rows("flashcard_game_sessions")
        rows[0]["created_at"] = rows[1]["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rows[2]["created_at"] = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)).isoformat()
        s = self.stats(api, headers_a)
        assert s["plays_total"] == 3 and s["plays_today"] == 2
        assert s["games"]["match"]["best"]["relax"] == {"score": 600, "stars": 3, "best_combo": 0}
        assert s["games"]["match"]["best"]["challenge"] is None and s["games"]["match"]["plays"] == 2
        assert s["games"]["speed"]["best"]["challenge"]["best_combo"] == 12
        assert s["level"]["xp"] >= 90 + 80 and s["level"]["level"] >= 2

    def test_filter_by_language_scopes_bests_but_not_xp(self, api, fake_db, headers_a):
        en, en_cards = filled(fake_db, lang="en", n=4)
        de, de_cards = filled(fake_db, lang="de", words=["Haus", "Baum", "Tür", "Hund"])
        play(api, headers_a, en, "match", [it(c) for c in en_cards], rid="game-lang-0001")
        play(api, headers_a, de, "match", [it(c) for c in de_cards], rid="game-lang-0002")
        scoped = self.stats(api, headers_a, lang_code="de")
        assert scoped["plays_total"] == 1 and scoped["lang_code"] == "de"
        assert scoped["level"]["xp"] == self.stats(api, headers_a)["level"]["xp"]

    def test_users_are_isolated(self, api, fake_db, headers_a, headers_b):
        d, cards = filled(fake_db, n=4)
        play(api, headers_a, d, "match", [it(c) for c in cards])
        assert self.stats(api, headers_b)["plays_total"] == 0

    def test_bad_language_422_and_auth(self, api, fake_db, headers_a):
        assert api.get(f"{BASE}/games/stats", headers=headers_a, params={"lang_code": "xx"}).status_code == 422
        assert api.get(f"{BASE}/games/stats").status_code == 401

    def test_missing_migration_503(self, api, fake_db, headers_a):
        fake_db.missing_tables.add("flashcard_game_sessions")
        assert api.get(f"{BASE}/games/stats", headers=headers_a).json()["error"]["code"] == "MIGRATION_REQUIRED"


# ============================================================ Bắn bóng nghĩa (shooter)
class TestShooter:
    def test_cards_need_five_and_come_with_four_choices(self, api, fake_db, headers_a):
        d, _ = filled(fake_db, n=4)
        data = api.get(f"{BASE}/games/shooter/cards", headers=headers_a, params={"deck_id": d["id"]}).json()["data"]
        assert data["playable"] is False and data["min_required"] == 5 and "ít nhất 5" in data["reason"]

        d, _ = filled(fake_db, n=8)
        data = api.get(f"{BASE}/games/shooter/cards", headers=headers_a, params={"deck_id": d["id"]}).json()["data"]
        assert data["playable"] is True and len(data["cards"]) == 8
        for c in data["cards"]:
            assert len(c["choices"]) == 4 and c["definition"] in c["choices"] and len(set(c["choices"])) == 4

    @pytest.mark.parametrize("lang,words", [("ja", ["水", "火", "木", "金", "土", "日"]), ("th", ["น้ำ", "ไฟ", "ไม้", "ทอง", "ดิน", "วัน"])])
    def test_works_for_every_language(self, api, fake_db, headers_a, lang, words):
        d, _ = filled(fake_db, lang=lang, words=words)
        assert api.get(f"{BASE}/games/shooter/cards", headers=headers_a, params={"deck_id": d["id"]}).json()["data"]["playable"] is True

    def test_session_is_scored_by_server_and_updates_due_cards_only(self, api, fake_db, headers_a):
        d, cards = filled(fake_db, n=6)
        items = [it(cards[0]), it(cards[1]), it(cards[2], attempts=1), it(cards[3], correct=False), it(cards[4]), it(cards[5])]
        res = play(api, headers_a, d, "shooter", items, mode="challenge", score=99999)
        assert res.status_code == 200, res.text
        s = res.json()["data"]["session"]
        # 10 + 10 + (10-3=7) + 0 + 10 + 10 ; combo bị ngắt bởi lượt bắn sai và bóng trôi mất
        assert (s["game"], s["score"], s["correct"], s["total"]) == ("shooter", 47, 5, 6)
        grades = {r["card_id"]: r["grade"] for r in fake_db.rows("review_logs")}
        assert grades[cards[0]["id"]] == 3 and grades[cards[2]["id"]] == 2 and grades[cards[3]["id"]] == 1 and 4 not in grades.values()

    def test_game_check_constraint_before_migration_007_is_a_clear_503(self, api, fake_db, headers_a):
        fake_db.fail_with = None
        d, cards = filled(fake_db, n=5)
        from app.services import game_service

        err = game_service._db_error(Exception('new row violates check constraint "flashcard_game_sessions_game_check"'))
        assert err.status == 503 and err.code == "MIGRATION_REQUIRED" and "007" in err.message

    def test_stats_lists_the_new_game(self, api, fake_db, headers_a):
        s = api.get(f"{BASE}/games/stats", headers=headers_a).json()["data"]
        assert set(s["games"]) == {"match", "speed", "builder", "shooter"}
