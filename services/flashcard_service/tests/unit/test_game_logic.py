"""Luật chơi thuần: chấm điểm/sao/XP, chọn thẻ, quy tắc cập nhật lịch ôn (không bao giờ Easy)."""
import datetime
import random

import pytest

from app.services import game_logic as g

NOW = datetime.datetime(2026, 10, 18, 12, 0, tzinfo=datetime.timezone.utc)


def item(cid="c", correct=True, attempts=0, hints=0):
    return {"card_id": cid, "correct": correct, "attempts": attempts, "hints": hints}


def card(cid, term=None, definition=None, state=2, due_days=-1, last_review=True, **kw):
    return {
        "id": cid, "term": f"term{cid}" if term is None else term, "definition": f"nghia{cid}" if definition is None else definition, "state": state,
        "due": (NOW + datetime.timedelta(days=due_days)).isoformat(), "last_review": "x" if last_review else None, **kw,
    }


class TestBuilderWords:
    @pytest.mark.parametrize("term,lang,ok", [
        ("Haus", "de", True), ("été", "fr", True), ("niño", "es", True), ("привет", "ru", True), ("apple", "en", True),
        ("ab", "en", False), ("a" * 15, "en", False), ("good morning", "en", False), ("e-mail", "en", False), ("abc1", "en", False),
        ("早上好", "zh", False), ("こんにちは", "ja", False), ("สวัสดี", "th", False), ("Haus", None, False),
    ])
    def test_eligibility(self, term, lang, ok):
        assert g.is_builder_word(term, lang) is ok

    def test_unsupported_reason(self):
        assert g.unsupported_reason("builder", "ja") and g.unsupported_reason("builder", "en") is None
        assert g.unsupported_reason("match", "ja") is None and g.unsupported_reason("speed", "th") is None


class TestSelectCards:
    def test_priority_due_then_weak_then_new_then_rest(self):
        due_old = card("1", due_days=-9)
        due_new = card("2", due_days=-1)
        weak = card("3", due_days=5, lapses=2)
        new = card("4", state=0, last_review=False, due_days=0)
        rest = card("5", due_days=7)
        out = g.select_cards([rest, new, weak, due_new, due_old], "match", "en", 5, NOW, random.Random(1))
        assert [c["id"] for c in out] == ["1", "2", "3", "4", "5"]

    def test_respects_count(self):
        cards = [card(str(i)) for i in range(10)]
        assert len(g.select_cards(cards, "speed", "en", 4, NOW)) == 4

    def test_skips_duplicate_terms_and_definitions_and_empty(self):
        cards = [card("1", "Haus", "nhà"), card("2", "haus", "căn nhà"), card("3", "Tür", "NHÀ"), card("4", "", "x"), card("5", "Baum", "")]
        out = g.select_cards(cards, "match", "de", 10, NOW)
        assert [c["id"] for c in out] == ["1"]

    def test_builder_only_picks_simple_words(self):
        cards = [card("1", "Haus", "nhà"), card("2", "guten Morgen", "chào"), card("3", "Tür", "cửa"), card("4", "ok", "ổn")]
        assert sorted(c["id"] for c in g.select_cards(cards, "builder", "de", 10, NOW)) == ["1", "3"]

    def test_reviewable_means_due_and_not_new(self):
        assert g.is_reviewable(card("1", due_days=-1), NOW)
        assert not g.is_reviewable(card("1", due_days=2), NOW)
        assert not g.is_reviewable(card("1", state=0, last_review=False, due_days=-1), NOW)


class TestScoreMatch:
    def test_perfect_game(self):
        r = g.score_session("match", "relax", [item(str(i)) for i in range(6)])
        assert (r["score"], r["stars"], r["correct"], r["mistakes"], r["xp"]) == (600, 3, 6, 0, 90)

    @pytest.mark.parametrize("mistakes,stars", [(0, 3), (2, 3), (3, 2), (5, 2), (6, 1), (30, 1)])
    def test_stars_by_mistakes(self, mistakes, stars):
        items = [item("1", attempts=mistakes)] + [item(str(i)) for i in range(2, 7)]
        assert g.score_session("match", "relax", items)["stars"] == stars

    def test_each_wrong_try_costs_points_with_floor(self):
        assert g.score_session("match", "relax", [item("1", attempts=2)])["score"] == 70
        assert g.score_session("match", "relax", [item("1", attempts=9)])["score"] == 25

    def test_unfinished_game_has_no_stars(self):
        r = g.score_session("match", "relax", [item("1"), item("2", correct=False)])
        assert r["stars"] == 0 and r["score"] == 100

    def test_challenge_time_bonus_and_cheating_clamp(self):
        items = [item(str(i)) for i in range(6)]
        fast = g.score_session("match", "challenge", items, duration_ms=30_000)["score"]
        slow = g.score_session("match", "challenge", items, duration_ms=200_000)["score"]
        zero = g.score_session("match", "challenge", items, duration_ms=0)["score"]
        assert fast == 600 + 60 * 2 and slow == 600
        assert zero == 600 + int(90 - 4.8) * 2  # thời gian giả bị nâng lên tối thiểu 0,8 s/cặp
        assert g.score_session("match", "relax", items, duration_ms=1)["score"] == 600  # relax không có thưởng giờ


class TestScoreSpeed:
    def test_combo_multiplier_progression(self):
        assert [g.speed_multiplier(c) for c in (0, 2, 3, 5, 6, 12, 40)] == [1, 1, 2, 2, 3, 5, 5]

    def test_score_follows_combo_and_resets_on_miss(self):
        seq = [item("a")] * 4 + [item("b", correct=False, attempts=1)] + [item("c")] * 2
        r = g.score_session("speed", "challenge", seq)
        # 3 câu ×1 + câu thứ 4 ×2 + sai (reset) + 2 câu ×1
        assert r["score"] == 10 * 3 + 20 + 10 * 2 and r["best_combo"] == 4 and r["mistakes"] == 1

    @pytest.mark.parametrize("correct,wrong,stars", [(0, 5, 0), (1, 4, 1), (5, 2, 2), (4, 0, 1), (10, 1, 3), (10, 4, 2), (10, 5, 1), (9, 0, 2), (20, 2, 3)])
    def test_stars(self, correct, wrong, stars):
        seq = [item("a")] * correct + [item("b", correct=False, attempts=1)] * wrong
        assert g.score_session("speed", "relax", seq)["stars"] == stars


class TestScoreBuilder:
    def test_solved_clean_vs_hints_vs_mistakes(self):
        assert g.score_session("builder", "relax", [item("1")])["score"] == 100
        assert g.score_session("builder", "relax", [item("1", hints=2)])["score"] == 50
        assert g.score_session("builder", "relax", [item("1", attempts=3)])["score"] == 70
        assert g.score_session("builder", "relax", [item("1", hints=5, attempts=9)])["score"] == 20  # sàn
        assert g.score_session("builder", "relax", [item("1", correct=False)])["score"] == 0

    @pytest.mark.parametrize("solved,total,hints,stars", [(10, 10, 0, 3), (10, 10, 1, 2), (8, 10, 0, 2), (7, 10, 0, 1), (0, 10, 0, 0)])
    def test_stars(self, solved, total, hints, stars):
        items = [item(str(i)) for i in range(solved)] + [item("x", correct=False)] * (total - solved)
        if hints and items:
            items[0]["hints"] = hints
        assert g.score_session("builder", "relax", items)["stars"] == stars


class TestXpAndLevels:
    def test_challenge_gives_more_xp(self):
        items = [item(str(i)) for i in range(6)]
        assert g.score_session("match", "relax", items)["xp"] == 90
        assert g.score_session("match", "challenge", items)["xp"] == 135

    @pytest.mark.parametrize("xp,level", [(0, 1), (99, 1), (100, 2), (399, 2), (400, 3), (900, 4), (-5, 1)])
    def test_levels(self, xp, level):
        assert g.level_for_xp(xp)["level"] == level

    def test_level_bounds(self):
        info = g.level_for_xp(250)
        assert (info["level_floor_xp"], info["next_level_xp"]) == (100, 400)

    def test_unknown_game_raises(self):
        with pytest.raises(ValueError):
            g.score_session("poker", "relax", [item()])

    def test_inputs_are_clamped(self):
        r = g.score_session("builder", "relax", [item("1", attempts=10_000, hints=10_000)])
        assert r["mistakes"] == g.MAX_ATTEMPTS and r["hints"] == g.MAX_HINTS


class TestReviewRules:
    def test_grades_are_again_hard_good_never_easy(self):
        assert g.grade_for(item(correct=False)) == 1
        assert g.grade_for(item(attempts=1)) == 2 and g.grade_for(item(hints=1)) == 2
        assert g.grade_for(item()) == 3

    def test_only_due_non_new_cards_and_once_per_card(self):
        cards = {
            "due": card("due", due_days=-1), "future": card("future", due_days=3),
            "new": card("new", state=0, last_review=False, due_days=-1),
        }
        items = [item("due"), item("future"), item("new"), item("due", correct=False), item("ghost")]
        assert g.review_plan(items, cards, NOW) == [("due", 3)]  # chỉ lần xuất hiện ĐẦU TIÊN của thẻ tính

    def test_wrong_first_appearance_is_again(self):
        cards = {"a": card("a", due_days=-2)}
        assert g.review_plan([item("a", correct=False), item("a")], cards, NOW) == [("a", 1)]

    def test_no_plan_for_empty(self):
        assert g.review_plan([], {}, NOW) == []


class TestScoreShooter:
    def test_clean_shots_build_combo_like_speed(self):
        r = g.score_session("shooter", "challenge", [item(str(i)) for i in range(5)])
        # 3 lượt đầu ×1, lượt 4–5 ×2
        assert r["score"] == 10 * 3 + 20 * 2 and r["best_combo"] == 5 and r["correct"] == 5

    def test_wrong_shots_cost_points_and_break_combo(self):
        r = g.score_session("shooter", "relax", [item("a"), item("b"), item("c", attempts=2), item("d")])
        assert r["score"] == 10 + 10 + max(5, 10 - 6) + 10 and r["best_combo"] == 2 and r["mistakes"] == 2

    def test_missed_bubble_scores_zero_and_breaks_combo(self):
        r = g.score_session("shooter", "relax", [item("a"), item("b"), item("c", correct=False), item("d")])
        assert r["score"] == 30 and r["correct"] == 3

    @pytest.mark.parametrize("correct,total,mistakes,stars", [(10, 10, 0, 3), (10, 10, 2, 3), (10, 10, 3, 2), (8, 10, 0, 2), (7, 10, 0, 1), (0, 5, 0, 0)])
    def test_stars(self, correct, total, mistakes, stars):
        items = [item(str(i)) for i in range(correct)] + [item("x", correct=False)] * (total - correct)
        if mistakes and items:
            items[0]["attempts"] = mistakes
        assert g.score_session("shooter", "relax", items)["stars"] == stars

    def test_limits_and_listing(self):
        assert "shooter" in g.GAMES and g.MIN_CARDS["shooter"] == 5 and g.DEFAULT_COUNT["shooter"] <= g.MAX_COUNT["shooter"]
        assert g.unsupported_reason("shooter", "ja") is None and g.unsupported_reason("shooter", "th") is None  # dùng được mọi ngôn ngữ

    def test_review_grades_follow_the_same_rules(self):
        cards = {"a": card("a", due_days=-1), "b": card("b", due_days=-1), "c": card("c", due_days=-1)}
        items = [item("a"), item("b", attempts=1), item("c", correct=False)]
        assert g.review_plan(items, cards, NOW) == [("a", 3), ("b", 2), ("c", 1)]
