import datetime

import pytest

from app.services import vocab_quota as q
from app.services.vocab_pipeline import VocabError
from conftest import ADMIN, USER_A, USER_B


class TestTiers:
    def test_defaults(self, monkeypatch):
        monkeypatch.delenv("VOCAB_DAILY_LIMIT_NORMAL", raising=False)
        monkeypatch.delenv("VOCAB_DAILY_LIMIT_STUDENT", raising=False)
        monkeypatch.delenv("VOCAB_DAILY_LIMIT_ADMIN", raising=False)
        assert q.tier_info("admin") == ("admin", "QUẢN TRỊ", 50)
        assert q.tier_info("student") == ("student", "SINH VIÊN IUH", 10)
        assert q.tier_info("public") == ("normal", "THƯỜNG", 3)
        assert q.tier_info(None) == ("normal", "THƯỜNG", 3)
        assert q.tier_info("unknown-role") == ("normal", "THƯỜNG", 3)  # vai trò lạ không được hưởng hạn mức cao hơn

    def test_env_overrides_each_tier_independently_and_garbage_falls_back(self, monkeypatch):
        monkeypatch.setenv("VOCAB_DAILY_LIMIT_NORMAL", "7")
        monkeypatch.setenv("VOCAB_DAILY_LIMIT_STUDENT", "12")
        monkeypatch.setenv("VOCAB_DAILY_LIMIT_ADMIN", "99")
        assert (q.tier_info("public")[2], q.tier_info("student")[2], q.tier_info("admin")[2]) == (7, 12, 99)
        for name, role, default in (("NORMAL", "public", 3), ("STUDENT", "student", 10), ("ADMIN", "admin", 50)):
            monkeypatch.setenv(f"VOCAB_DAILY_LIMIT_{name}", "many")
            assert q.tier_info(role)[2] == default


class TestReserveRefund:
    async def test_reserve_until_exhausted_then_429(self, fake_db):
        for expected_used in (1, 2, 3):
            await q.reserve(USER_A, "public")
            assert (await q.get_quota(USER_A, "public"))["used"] == expected_used
        with pytest.raises(VocabError) as err:
            await q.reserve(USER_A, "public")
        assert (err.value.status, err.value.code) == (429, "QUOTA_EXCEEDED")
        assert (await q.get_quota(USER_A, "public"))["remaining"] == 0

    async def test_student_gets_ten_then_429(self, fake_db):
        for _ in range(10):
            await q.reserve(USER_A, "student")
        with pytest.raises(VocabError) as err:
            await q.reserve(USER_A, "student")
        assert (err.value.status, err.value.code) == (429, "QUOTA_EXCEEDED")
        assert (await q.get_quota(USER_A, "student"))["limit"] == 10

    async def test_refund_gives_the_slot_back_and_never_goes_negative(self, fake_db):
        await q.reserve(USER_A)
        await q.refund(USER_A)
        assert (await q.get_quota(USER_A))["used"] == 0
        await q.refund(USER_A)
        assert (await q.get_quota(USER_A))["used"] == 0

    async def test_users_are_independent(self, fake_db):
        for _ in range(3):
            await q.reserve(USER_A)
        assert (await q.get_quota(USER_B))["remaining"] == 3

    async def test_admin_has_larger_limit(self, fake_db):
        quota = await q.get_quota(ADMIN, "admin")
        assert (quota["tier"], quota["limit"]) == ("admin", 50)

    async def test_resets_on_the_next_vietnam_day(self, fake_db, monkeypatch):
        today = datetime.date(2026, 6, 1)
        monkeypatch.setattr(q, "_today", lambda: today)
        for _ in range(3):
            await q.reserve(USER_A)
        monkeypatch.setattr(q, "_today", lambda: today + datetime.timedelta(days=1))
        assert (await q.get_quota(USER_A))["remaining"] == 3

    async def test_resets_at_is_next_midnight_vietnam(self, fake_db):
        value = (await q.get_quota(USER_A))["resets_at"]
        parsed = datetime.datetime.fromisoformat(value)
        assert parsed.utcoffset() == datetime.timedelta(hours=7) and (parsed.hour, parsed.minute) == (0, 0)


class TestStorage:
    async def test_usage_is_persisted_in_the_table(self, fake_db):
        await q.reserve(USER_A)
        await q.reserve(USER_A)
        (row,) = fake_db.rows("vocab_generation_usage", user_id=USER_A)
        assert row["used"] == 2 and row["usage_date"] == q._today().isoformat()

    async def test_falls_back_to_memory_when_table_is_missing(self, fake_db):
        fake_db.missing_tables.add("vocab_generation_usage")
        await q.reserve(USER_A)
        assert (await q.get_quota(USER_A))["used"] == 1
        assert q._memory[(USER_A, q._today().isoformat())] == 1

    async def test_non_uuid_user_uses_memory(self, fake_db):
        await q.reserve("local-user")
        assert (await q.get_quota("local-user"))["used"] == 1
        assert fake_db.rows("vocab_generation_usage") == []

    async def test_refund_failure_is_swallowed(self, fake_db):
        await q.reserve(USER_A)
        fake_db.fail_when("upsert", "vocab_generation_usage")
        await q.refund(USER_A)  # không ném lỗi
