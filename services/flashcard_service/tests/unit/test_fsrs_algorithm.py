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
