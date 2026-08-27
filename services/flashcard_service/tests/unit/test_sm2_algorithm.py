import pytest
from app.services.sm2_algorithm import calculate_sm2


class TestSuperMemo2Algorithm:
    def test_grade_below_3_resets_repetition_and_interval(self):
        # Grade 0, 1, 2 indicates memory blackout / failure
        for grade in [0, 1, 2]:
            result = calculate_sm2(grade=grade, repetition=5, ease_factor=2.5, interval_days=30)
            assert result["repetition"] == 0
            assert result["interval_days"] == 1
            assert result["ease_factor"] < 2.5  # EF decreases on failure

    def test_first_successful_review_repetition_1(self):
        # Initial review (repetition=0), grade=4
        result = calculate_sm2(grade=4, repetition=0, ease_factor=2.5, interval_days=1)
        assert result["repetition"] == 1
        assert result["interval_days"] == 1
        assert result["ease_factor"] == 2.5  # Grade 4 keeps EF stable (2.5 + (0.1 - 1*0.1) = 2.5)

    def test_second_successful_review_interval_is_6_days(self):
        # Second review (repetition=1), grade=5
        result = calculate_sm2(grade=5, repetition=1, ease_factor=2.5, interval_days=1)
        assert result["repetition"] == 2
        assert result["interval_days"] == 6
        assert result["ease_factor"] == 2.6  # Grade 5 increases EF by 0.1

    def test_third_successful_review_interval_multiplied_by_ease_factor(self):
        # Third review (repetition=2), interval_days=6, EF=2.6, grade=4
        result = calculate_sm2(grade=4, repetition=2, ease_factor=2.6, interval_days=6)
        assert result["repetition"] == 3
        # new_interval = round(6 * 2.6) = round(15.6) = 16
        assert result["interval_days"] == 16

    def test_ease_factor_cannot_drop_below_minimum_1_point_3(self):
        # Repeated failures with grade 0 should never drop EF below 1.3
        current_ef = 1.4
        result = calculate_sm2(grade=0, repetition=0, ease_factor=current_ef, interval_days=1)
        assert result["ease_factor"] == 1.3

    def test_next_review_date_is_iso_formatted(self):
        result = calculate_sm2(grade=4, repetition=0, ease_factor=2.5, interval_days=1)
        assert "next_review_date" in result
        assert isinstance(result["next_review_date"], str)
        assert "T" in result["next_review_date"]
