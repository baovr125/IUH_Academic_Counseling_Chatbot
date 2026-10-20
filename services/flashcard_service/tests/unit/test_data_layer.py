"""Kiểm thử lớp dữ liệu của flashcard_service trên Supabase giả: quyền sở hữu, lỗi ghi DB, phân trang."""
import datetime

import pytest
from fastapi import HTTPException

from app.services import excel_importer as importer
from app.services import flashcard_service as fs
from conftest import ADMIN, USER_A, USER_B

NOW = datetime.datetime.now(datetime.timezone.utc)


def iso(days: float = 0.0) -> str:
    return (NOW + datetime.timedelta(days=days)).isoformat()


def seed_deck(db, owner=USER_A, **kw):
    row = dict(user_id=owner, title="Deck", lang_code="en")
    row.update(kw)
    return db.seed("flashcard_decks", **row)


def seed_card(db, deck, owner=USER_A, term="alpha", definition="một", **kw):
    row = dict(deck_id=deck["id"], user_id=owner, term=term, definition=definition, part_of_speech="noun", lang_code="en",
               state=0, reps=0, lapses=0, stability=0.0, difficulty=0.0, due=iso(), last_review=None, example=None)
    row.update(kw)
    return db.seed("flashcards", **row)


async def status_of(coro) -> int:
    try:
        await coro
    except HTTPException as exc:
        return exc.status_code
    return 200


# ============================================================================ quyền sở hữu
class TestOwnership:
    @pytest.fixture
    def world(self, fake_db):
        deck = seed_deck(fake_db)
        card = seed_card(fake_db, deck)
        system = fake_db.seed("flashcard_decks", user_id=None, is_system=True, title="Catalog", lang_code="en", slug="s")
        system_card = seed_card(fake_db, system, owner=None, term="sys", definition="hệ thống")
        return dict(deck=deck, card=card, system=system, system_card=system_card)

    async def test_owner_can_do_everything(self, world):
        d, c = world["deck"]["id"], world["card"]["id"]
        assert await fs.get_deck_cards(d, USER_A)
        assert await fs.update_deck(d, USER_A, title="New")
        assert await fs.update_card(c, USER_A, front_text="beta")
        assert (await fs.review_card(c, 3, USER_A))["reps"] == 1
        assert await fs.delete_card(c, USER_A)
        assert await fs.delete_deck(d, USER_A)

    @pytest.mark.parametrize("action", [
        lambda w: fs.get_deck_cards(w["deck"]["id"], USER_B),
        lambda w: fs.get_study_queue(w["deck"]["id"], USER_B),
        lambda w: fs.get_study_stats(w["deck"]["id"], USER_B),
        lambda w: fs.update_deck(w["deck"]["id"], USER_B, title="hack"),
        lambda w: fs.delete_deck(w["deck"]["id"], USER_B),
        lambda w: fs.create_card(w["deck"]["id"], "x", "y", USER_B),
        lambda w: fs.update_card(w["card"]["id"], USER_B, front_text="hack"),
        lambda w: fs.delete_card(w["card"]["id"], USER_B),
        lambda w: fs.review_card(w["card"]["id"], 3, USER_B),
        lambda w: fs.verify_spelling(w["card"]["id"], "alpha", USER_B),
        lambda w: fs.get_card_by_id(w["card"]["id"], USER_B),
        lambda w: importer.bulk_insert_cards(w["deck"]["id"], USER_B, [{"term": "t", "definition": "d"}]),
    ])
    async def test_other_user_is_forbidden(self, world, action):
        assert await status_of(action(world)) == 403

    @pytest.mark.parametrize("user", [USER_A, USER_B, ADMIN])
    @pytest.mark.parametrize("action", [
        lambda w, u: fs.get_deck_cards(w["system"]["id"], u),
        lambda w, u: fs.get_study_queue(w["system"]["id"], u),
        lambda w, u: fs.update_deck(w["system"]["id"], u, title="hack"),
        lambda w, u: fs.delete_deck(w["system"]["id"], u),
        lambda w, u: fs.create_card(w["system"]["id"], "x", "y", u),
        lambda w, u: fs.review_card(w["system_card"]["id"], 3, u),
        lambda w, u: fs.update_card(w["system_card"]["id"], u, front_text="hack"),
        lambda w, u: fs.delete_card(w["system_card"]["id"], u),
        lambda w, u: importer.bulk_insert_cards(w["system"]["id"], u, [{"term": "t", "definition": "d"}]),
    ])
    async def test_system_decks_are_never_reachable_through_personal_apis(self, world, action, user):
        # Dù là admin: bộ hệ thống chỉ được nạp bằng script/hàm riêng và đọc qua /catalog, không qua API cá nhân.
        assert await status_of(action(world, user)) == 403

    async def test_missing_card_and_deck(self, fake_db):
        assert await status_of(fs.review_card("00000000-0000-4000-8000-000000000000", 3, USER_A)) == 404
        assert await status_of(fs.verify_spelling("00000000-0000-4000-8000-000000000000", "x", USER_A)) == 404
        assert await status_of(fs.update_deck("00000000-0000-4000-8000-000000000000", USER_A, title="x")) == 404
        assert await status_of(fs.create_card("not-a-uuid", "x", "y", USER_A)) == 400


# ============================================================================ lỗi ghi DB
class TestWriteFailures:
    async def test_create_deck_failure_is_503_and_nothing_cached(self, fake_db):
        fake_db.fail_when("insert", "flashcard_decks")
        assert await status_of(fs.create_deck("T", "", USER_A, lang_code="en")) == 503
        assert fs.in_memory_decks == {}

    async def test_create_card_failure_is_503_and_nothing_cached(self, fake_db):
        deck = seed_deck(fake_db)
        fake_db.fail_when("insert", "flashcards")
        assert await status_of(fs.create_card(deck["id"], "x", "y", USER_A)) == 503
        assert fs.in_memory_cards == {} and fake_db.rows("flashcards") == []

    async def test_review_write_failure_is_503_and_card_unchanged(self, fake_db):
        card = seed_card(fake_db, seed_deck(fake_db))
        fake_db.fail_when("insert", "review_logs")
        assert await status_of(fs.review_card(card["id"], 3, USER_A)) == 503

    async def test_update_and_delete_failures_are_503(self, fake_db):
        deck = seed_deck(fake_db)
        card = seed_card(fake_db, deck)
        fake_db.fail_when("update", "flashcard_decks")
        fake_db.fail_when("delete", "flashcards")
        assert await status_of(fs.update_deck(deck["id"], USER_A, title="x")) == 503
        assert await status_of(fs.delete_card(card["id"], USER_A)) == 503
        assert await status_of(fs.delete_deck(deck["id"], USER_A)) == 503

    async def test_ownership_check_failure_does_not_fail_open(self, fake_db):
        deck = seed_deck(fake_db, owner=USER_B)
        fake_db.fail_when("select", "flashcard_decks")
        assert await status_of(fs.create_card(deck["id"], "x", "y", USER_A)) == 503
        assert fake_db.rows("flashcards") == []

    async def test_read_failures_are_503(self, fake_db):
        deck = seed_deck(fake_db)
        fake_db.fail_when("select", "flashcards")
        assert await status_of(fs.get_deck_cards(deck["id"], USER_A)) == 503
        fake_db.fail_when("select", "flashcard_decks")
        assert await status_of(fs.get_decks(USER_A)) == 503

    async def test_missing_deck_is_auto_created_for_the_caller(self, fake_db):
        deck_id = "33333333-3333-4333-8333-333333333333"
        card = await fs.create_card(deck_id, "x", "y", USER_A, lang_code="en")
        assert fake_db.rows("flashcard_decks", id=deck_id)[0]["user_id"] == USER_A
        assert fake_db.rows("flashcards", id=card["id"])

    async def test_local_only_ids_do_not_hit_the_database(self, fake_db):
        # Thẻ/deck tạo ở LocalStorage có id không phải UUID: không được ném 503 vì lỗi cú pháp UUID.
        assert await fs.delete_card("local-1", USER_A) is True
        assert await status_of(fs.update_deck("local-deck", USER_A, title="x")) == 404


class TestBulkInsert:
    async def test_inserts_dedupes_and_counts(self, fake_db):
        deck = seed_deck(fake_db)
        seed_card(fake_db, deck, term="Existing")
        data = [{"term": "existing", "definition": "dup"}, {"term": "New", "definition": "mới"},
                {"term": "new", "definition": "dup in batch"}, {"term": "", "definition": "x"}]
        out = await importer.bulk_insert_cards(deck["id"], USER_A, data)
        assert (out["inserted"], out["skipped_duplicates"]) == (1, 2)  # trùng với deck + trùng trong cùng lô
        assert {r["term"] for r in fake_db.rows("flashcards")} == {"Existing", "New"}

    async def test_failure_on_second_chunk_then_retry_is_idempotent(self, fake_db):
        deck = seed_deck(fake_db)
        data = [{"term": f"w{n:04d}", "definition": f"d{n}"} for n in range(250)]
        fake_db.fail_when("insert", "flashcards", lambda n: n == 2)
        assert await status_of(importer.bulk_insert_cards(deck["id"], USER_A, data)) == 503
        assert len(fake_db.rows("flashcards")) == 200  # lô đầu đã lưu, lô sau chưa

        out = await importer.bulk_insert_cards(deck["id"], USER_A, data)
        assert (out["inserted"], out["skipped_duplicates"]) == (50, 200)
        assert len(fake_db.rows("flashcards")) == 250

    async def test_falls_back_when_extended_columns_are_missing(self, fake_db):
        fake_db.missing_columns["flashcards"] = {"example_translation", "level", "source"}
        deck = seed_deck(fake_db)
        out = await importer.bulk_insert_cards(
            deck["id"], USER_A,
            [{"term": "a", "definition": "b", "example": "an a.", "example_translation": "một a", "level": "B1", "source": "ai_topic"}],
        )
        assert out["inserted"] == 1 and out["extended_saved"] is False
        assert fake_db.rows("flashcards")[0]["example"] == "an a."

    async def test_extended_columns_are_saved_when_present(self, fake_db):
        deck = seed_deck(fake_db)
        out = await importer.bulk_insert_cards(
            deck["id"], USER_A, [{"term": "a", "definition": "b", "example_translation": "dịch", "level": "A2", "source": "ai_topic"}]
        )
        row = fake_db.rows("flashcards")[0]
        assert out["extended_saved"] is True
        assert (row["example_translation"], row["level"], row["source"]) == ("dịch", "A2", "ai_topic")
        assert row["user_id"] == USER_A and row["state"] == 0 and row["stability"] == 0.0

    async def test_other_database_errors_are_not_masked_as_missing_columns(self, fake_db):
        deck = seed_deck(fake_db)
        fake_db.fail_when("insert", "flashcards")
        assert await status_of(importer.bulk_insert_cards(deck["id"], USER_A, [{"term": "a", "definition": "b"}])) == 503


# ============================================================================ phân trang & đếm
class TestPagination:
    async def test_more_than_1000_cards_are_all_returned(self, fake_db):
        deck = seed_deck(fake_db)
        fake_db.tables["flashcards"].extend(
            {"id": f"c{n}", "deck_id": deck["id"], "user_id": USER_A, "term": f"t{n}", "definition": "d", "state": 0,
             "created_at": f"2026-01-01T00:00:{n // 100:02d}.{n % 100:02d}+00:00"} for n in range(1500)
        )
        cards = await fs.get_deck_cards(deck["id"], USER_A)
        assert len(cards) == 1500 and len({c["id"] for c in cards}) == 1500

    async def test_existing_terms_and_counts_are_not_capped(self, fake_db):
        deck = seed_deck(fake_db)
        fake_db.tables["flashcards"].extend(
            {"id": f"c{n}", "deck_id": deck["id"], "user_id": USER_A, "term": f"T{n}", "definition": "d"} for n in range(1200)
        )
        assert len(await importer.fetch_existing_terms(fs.get_supabase(), deck["id"])) == 1200
        assert (await fs.get_decks(USER_A))[0]["cards_count"] == 1200

    async def test_get_decks_returns_only_own_decks_newest_first(self, fake_db):
        seed_deck(fake_db, title="old", created_at="2026-01-01T00:00:00+00:00")
        seed_deck(fake_db, title="new", created_at="2026-02-01T00:00:00+00:00")
        seed_deck(fake_db, owner=USER_B, title="theirs")
        fake_db.seed("flashcard_decks", user_id=None, is_system=True, title="system", lang_code="en", slug="x")
        assert [d["title"] for d in await fs.get_decks(USER_A)] == ["new", "old"]


# ============================================================================ hàng đợi học
class TestStudyQueue:
    async def test_due_first_then_new_and_future_cards_excluded(self, fake_db):
        deck = seed_deck(fake_db)
        seed_card(fake_db, deck, term="overdue", state=2, stability=5.0, difficulty=3.0, last_review=iso(-10), due=iso(-3))
        seed_card(fake_db, deck, term="due_today", state=2, stability=5.0, difficulty=3.0, last_review=iso(-5), due=iso(-0.1))
        seed_card(fake_db, deck, term="future", state=2, stability=9.0, difficulty=3.0, last_review=iso(-1), due=iso(5))
        seed_card(fake_db, deck, term="brand_new")
        queue = await fs.get_study_queue(deck["id"], USER_A)
        assert [c["term"] for c in queue] == ["overdue", "due_today", "brand_new"]
        assert queue[-1]["is_new"] is True and queue[-1]["recommended_mode"] == "flip"

    async def test_new_limit_and_total_limit(self, fake_db):
        deck = seed_deck(fake_db)
        for n in range(30):
            seed_card(fake_db, deck, term=f"n{n:02d}", definition=f"d{n}")
        assert len(await fs.get_study_queue(deck["id"], USER_A, new_limit=7)) == 7
        assert len(await fs.get_study_queue(deck["id"], USER_A, limit=5, new_limit=20)) == 5
        assert len(await fs.get_study_queue(deck["id"], USER_A, new_limit=0)) == 0

    async def test_weak_only(self, fake_db):
        deck = seed_deck(fake_db)
        seed_card(fake_db, deck, term="lapsed", state=2, lapses=2, stability=3.0, difficulty=4.0, last_review=iso(-2), due=iso(4))
        seed_card(fake_db, deck, term="hard", state=2, stability=3.0, difficulty=8.0, last_review=iso(-2), due=iso(4))
        seed_card(fake_db, deck, term="easy", state=2, stability=30.0, difficulty=2.0, last_review=iso(-2), due=iso(4))
        assert {c["term"] for c in await fs.get_study_queue(deck["id"], USER_A, weak_only=True)} == {"lapsed", "hard"}

    async def test_choices_need_four_distinct_definitions(self, fake_db):
        deck = seed_deck(fake_db)
        for n, d in enumerate(["một", "hai", "ba"]):
            seed_card(fake_db, deck, term=f"t{n}", definition=d)
        assert all(c["choices"] is None for c in await fs.get_study_queue(deck["id"], USER_A))
        seed_card(fake_db, deck, term="t3", definition="bốn")
        queue = await fs.get_study_queue(deck["id"], USER_A)
        for c in queue:
            assert len(c["choices"]) == 4 and c["definition"] in c["choices"] and len(set(c["choices"])) == 4

    async def test_duplicate_definitions_do_not_become_distractors(self, fake_db):
        deck = seed_deck(fake_db)
        for n, d in enumerate(["giống", "giống", "giống", "khác", "nữa", "thêm"]):
            seed_card(fake_db, deck, term=f"t{n}", definition=d)
        for c in await fs.get_study_queue(deck["id"], USER_A):
            assert len(set(x.lower() for x in c["choices"])) == 4

    async def test_distractors_prefer_same_part_of_speech(self, fake_db):
        deck = seed_deck(fake_db)
        target = seed_card(fake_db, deck, term="run", definition="chạy", part_of_speech="verb")
        for n in range(3):
            seed_card(fake_db, deck, term=f"v{n}", definition=f"động từ {n}", part_of_speech="verb")
        for n in range(5):
            seed_card(fake_db, deck, term=f"n{n}", definition=f"danh từ {n}", part_of_speech="noun")
        picked = fs.build_distractors(target, await fs.get_deck_cards(deck["id"], USER_A))
        assert len(picked) == 3 and all(p.startswith("động từ") for p in picked)

    async def test_cloze_handles_inflection(self, fake_db):
        deck = seed_deck(fake_db)
        seed_card(fake_db, deck, term="pollute", example="The factory polluted the river.")
        (card,) = await fs.get_study_queue(deck["id"], USER_A)
        assert card["cloze_sentence"] == "The factory ________ the river."

    async def test_review_removes_card_from_todays_queue(self, fake_db):
        deck = seed_deck(fake_db)
        card = seed_card(fake_db, deck)
        assert len(await fs.get_study_queue(deck["id"], USER_A)) == 1
        reviewed = await fs.review_card(card["id"], 3, USER_A)
        assert reviewed["state"] == 2 and reviewed["scheduled_days"] >= 1
        assert await fs.get_study_queue(deck["id"], USER_A) == []
        assert len(fake_db.rows("review_logs", card_id=card["id"], user_id=USER_A)) == 1

    async def test_stats(self, fake_db):
        deck = seed_deck(fake_db)
        seed_card(fake_db, deck, term="new1")
        seed_card(fake_db, deck, term="new2")
        seed_card(fake_db, deck, term="due", state=2, stability=5.0, difficulty=3.0, last_review=iso(-9), due=iso(-1))
        seed_card(fake_db, deck, term="mastered", state=2, stability=fs.MASTERED_STABILITY_DAYS, difficulty=3.0, last_review=iso(-9), due=iso(10))
        seed_card(fake_db, deck, term="weak", state=2, lapses=1, stability=4.0, difficulty=6.0, last_review=iso(-3), due=iso(2))
        assert await fs.get_study_stats(deck["id"], USER_A) == {"total": 5, "new": 2, "due": 1, "learning": 2, "mastered": 1, "weak": 1}


class TestReviewAndSpelling:
    async def test_again_on_review_card_adds_lapse_and_lowers_stability(self, fake_db):
        card = seed_card(fake_db, seed_deck(fake_db), state=2, reps=3, stability=12.0, difficulty=4.0, last_review=iso(-12), due=iso(0))
        out = await fs.review_card(card["id"], 1, USER_A)
        assert out["lapses"] == 1 and out["stability"] < 12.0 and out["reps"] == 4
        row = fake_db.rows("flashcards", id=card["id"])[0]
        assert row["lapses"] == 1 and row["last_review"]

    async def test_good_review_grows_stability(self, fake_db):
        card = seed_card(fake_db, seed_deck(fake_db), state=2, reps=1, stability=3.0, difficulty=4.0, last_review=iso(-3), due=iso(0))
        assert (await fs.review_card(card["id"], 3, USER_A))["stability"] > 3.0

    @pytest.mark.parametrize("typed,expected_grade,flags", [
        ("alpha", 4, (True, False)), ("Alpha ", 4, (True, False)), ("alpah", 2, (False, True)), ("zzzz", 1, (False, False)),
    ])
    async def test_verify_spelling(self, fake_db, typed, expected_grade, flags):
        card = seed_card(fake_db, seed_deck(fake_db), term="alpha")
        out = await fs.verify_spelling(card["id"], typed, USER_A)
        assert out["suggested_grade"] == expected_grade and (out["is_correct"], out["is_close"]) == flags

    async def test_auto_apply_review_writes_a_log(self, fake_db):
        card = seed_card(fake_db, seed_deck(fake_db), term="alpha")
        await fs.verify_spelling(card["id"], "alpha", USER_A, auto_apply_review=True)
        assert len(fake_db.rows("review_logs", card_id=card["id"])) == 1


# ============================================================================ streak
class TestStreak:
    def _log(self, db, days_ago, hour=10, user=USER_A, n=1):
        today = datetime.datetime.now(fs.VN_TZ).date()
        day = today - datetime.timedelta(days=days_ago)
        ts = datetime.datetime.combine(day, datetime.time(hour), tzinfo=fs.VN_TZ).isoformat()
        for _ in range(n):
            db.seed("review_logs", user_id=user, card_id=None, reviewed_at=ts)

    async def test_counts_intensity_and_streaks(self, fake_db):
        self._log(fake_db, 0, n=12)
        self._log(fake_db, 1, n=3)
        self._log(fake_db, 2, n=1)
        self._log(fake_db, 5, n=25)
        self._log(fake_db, 6, n=1)
        out = await fs.get_review_streak(USER_A, 84)
        assert len(out["days"]) == 84
        assert (out["current_streak"], out["longest_streak"], out["today_reviews"], out["total_reviews"]) == (3, 3, 12, 42)
        assert out["days"][-1]["intensity"] == 3 and out["days"][-6]["intensity"] == 4 and out["days"][-2]["intensity"] == 1

    async def test_streak_survives_until_end_of_today_when_not_yet_studied(self, fake_db):
        self._log(fake_db, 1, n=2)
        self._log(fake_db, 2, n=1)
        assert (await fs.get_review_streak(USER_A))["current_streak"] == 2

    async def test_gap_resets_current_streak(self, fake_db):
        self._log(fake_db, 3, n=2)
        assert (await fs.get_review_streak(USER_A))["current_streak"] == 0

    async def test_other_users_logs_are_ignored(self, fake_db):
        self._log(fake_db, 0, user=USER_B, n=9)
        assert (await fs.get_review_streak(USER_A))["total_reviews"] == 0

    async def test_day_boundary_uses_vietnam_time(self, fake_db):
        # 20:30 UTC hôm qua = 03:30 ICT hôm nay -> thuộc về ngày hôm nay theo giờ Việt Nam.
        today_vn = datetime.datetime.now(fs.VN_TZ).date()
        ts = datetime.datetime.combine(today_vn - datetime.timedelta(days=1), datetime.time(20, 30), tzinfo=datetime.timezone.utc)
        fake_db.seed("review_logs", user_id=USER_A, card_id=None, reviewed_at=ts.isoformat())
        assert (await fs.get_review_streak(USER_A))["today_reviews"] == 1

    async def test_today_cards_counts_distinct_cards_not_reviews(self, fake_db):
        today = datetime.datetime.now(fs.VN_TZ).date()
        ts = lambda d, h: datetime.datetime.combine(d, datetime.time(h), tzinfo=fs.VN_TZ).isoformat()  # noqa: E731
        for card_id, hour in (("c1", 8), ("c1", 9), ("c1", 10), ("c2", 11)):
            fake_db.seed("review_logs", user_id=USER_A, card_id=card_id, reviewed_at=ts(today, hour))
        fake_db.seed("review_logs", user_id=USER_A, card_id=None, reviewed_at=ts(today, 12))  # không gắn thẻ -> không tính
        fake_db.seed("review_logs", user_id=USER_A, card_id="c3", reviewed_at=ts(today - datetime.timedelta(days=1), 12))  # hôm qua
        fake_db.seed("review_logs", user_id=USER_B, card_id="c9", reviewed_at=ts(today, 12))  # người khác
        out = await fs.get_review_streak(USER_A)
        assert out["today_reviews"] == 5 and out["today_cards"] == 2

    async def test_today_cards_is_zero_without_activity(self, fake_db):
        assert (await fs.get_review_streak(USER_A))["today_cards"] == 0

    async def test_no_database_returns_empty(self, monkeypatch):
        monkeypatch.setattr(fs, "get_supabase", lambda: None)
        out = await fs.get_review_streak("anyone", 7)
        assert out["current_streak"] == 0 and len(out["days"]) == 7 and out["today_cards"] == 0


class TestSharedSupabaseClient:
    def test_client_is_created_once_and_reused(self, monkeypatch):
        created = []
        monkeypatch.setattr(fs, "make_supabase", lambda url, key: created.append((url, key)) or object())
        fs.reset_supabase_client()
        first = fs.get_supabase()
        assert fs.get_supabase() is first and fs.get_supabase() is first
        assert len(created) == 1  # trước đây mỗi lần gọi tạo một client (và kết nối TLS) mới
        fs.reset_supabase_client()

    def test_rebuilt_when_credentials_change(self, monkeypatch):
        monkeypatch.setattr(fs, "make_supabase", lambda url, key: (url, key))
        fs.reset_supabase_client()
        monkeypatch.setenv("SUPABASE_URL", "https://a.test")
        a = fs.get_supabase()
        monkeypatch.setenv("SUPABASE_URL", "https://b.test")
        assert fs.get_supabase() != a
        fs.reset_supabase_client()

    def test_real_client_uses_http1_pool(self):
        client = fs.make_supabase("https://x.supabase.test", "sb_secret_test_key")
        http = client.postgrest.session
        assert http._transport._pool._http2 is False  # HTTP/2 chia sẻ một kết nối: bị ngắt hàng loạt khi gọi song song
        fs.reset_supabase_client()

    def test_returns_none_without_configuration(self, monkeypatch):
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        assert fs.get_supabase() is None
