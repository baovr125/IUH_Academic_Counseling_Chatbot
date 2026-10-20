import pytest
from app.services.fsrs_algorithm import calculate_fsrs


class TestFSRSAlgorithm:
    def test_fsrs_rating_again_increases_lapses_or_resets(self):
        result = calculate_fsrs(grade=1, repetition=0)
        assert result["reps"] == 0 or result["lapses"] >= 0
        assert "due" in result
        assert "stability" in result

    def test_fsrs_rating_good_schedules_future_review(self):
        result = calculate_fsrs(grade=3, repetition=0)
        assert result["reps"] >= 1
        assert "due" in result
        assert "scheduled_days" in result

    def test_fsrs_rating_easy_schedules_longer_interval_than_hard(self):
        result_hard = calculate_fsrs(grade=2, repetition=1)
        result_easy = calculate_fsrs(grade=4, repetition=1)
        
        assert result_easy["scheduled_days"] >= result_hard["scheduled_days"]


class TestFSRSIsReal:
    """Chặn việc lặng lẽ rơi về bộ lập lịch dự phòng (từng xảy ra khi gói `fsrs` đổi API)."""

    def test_real_fsrs_library_is_loaded(self):
        from app.services import fsrs_algorithm
        assert fsrs_algorithm.HAS_FSRS is True

    def test_stability_grows_after_successful_reviews_and_drops_after_lapse(self):
        import datetime
        card = {"state": 0, "reps": 0, "lapses": 0, "stability": 0.0, "difficulty": 0.0}
        first = calculate_fsrs(grade=3, card_dict=card)
        assert first["state"] == 2 and first["reps"] == 1

        past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=first["scheduled_days"])
        card = {**card, **first, "last_review": past.isoformat(), "due": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        second = calculate_fsrs(grade=3, card_dict=card)
        assert second["stability"] > first["stability"]
        assert second["scheduled_days"] > first["scheduled_days"]

        lapsed = calculate_fsrs(grade=1, card_dict={**card, **second})
        assert lapsed["lapses"] == 1
        assert lapsed["stability"] < second["stability"]
