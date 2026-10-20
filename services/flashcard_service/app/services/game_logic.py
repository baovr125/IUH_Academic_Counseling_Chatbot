"""Luật chơi thuần (không I/O) của 4 trò: Ghép cặp, Đua 60 giây, Xếp chữ, Bắn bóng nghĩa.

Máy chủ TỰ TÍNH điểm/sao/XP từ kết quả từng câu do client gửi (client không gửi điểm), và quyết định thẻ nào được cập nhật
lịch ôn FSRS. Quy tắc lịch ôn (thận trọng — đoán trúng trong trò chơi không chứng minh đã nhớ lâu):
  * chỉ thẻ ĐÃ ĐẾN HẠN và không phải thẻ mới;
  * đúng ngay, không gợi ý -> Good (3); đúng nhưng phải thử lại/xem gợi ý -> Hard (2); sai/bỏ qua -> Again (1);
  * KHÔNG BAO GIỜ Easy (4);
  * mỗi thẻ chỉ tính một lần trong một ván (lần xuất hiện đầu tiên).
"""
from __future__ import annotations

import datetime
import math
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

GAMES = ("match", "speed", "builder", "shooter")
MODES = ("relax", "challenge")

MIN_CARDS = {"match": 4, "speed": 4, "builder": 4, "shooter": 5}
DEFAULT_COUNT = {"match": 6, "speed": 30, "builder": 10, "shooter": 12}
MAX_COUNT = {"match": 8, "speed": 40, "builder": 12, "shooter": 20}
MAX_ITEMS = 100

# Xếp chữ chỉ có nghĩa với ngôn ngữ chữ cái (không dùng cho zh/ja/ko/th).
BUILDER_LANGS = ("en", "de", "fr", "es", "ru")
BUILDER_MIN_LEN, BUILDER_MAX_LEN = 3, 14

MAX_ATTEMPTS, MAX_HINTS = 20, 5


def is_builder_word(term: Any, lang: Optional[str]) -> bool:
    """Từ đơn gồm toàn chữ cái (có dấu được), 3–14 ký tự, thuộc ngôn ngữ chữ cái."""
    if lang not in BUILDER_LANGS:
        return False
    word = str(term or "").strip()
    return BUILDER_MIN_LEN <= len(word) <= BUILDER_MAX_LEN and word.isalpha()


def unsupported_reason(game: str, lang: Optional[str]) -> Optional[str]:
    if game == "builder" and lang not in BUILDER_LANGS:
        return "Trò Xếp chữ chỉ dùng cho ngôn ngữ chữ cái (Anh, Đức, Pháp, Tây Ban Nha, Nga). Hãy thử Ghép cặp hoặc Đua 60 giây."
    return None


# ---- chọn thẻ cho ván chơi -----------------------------------------------------------------------

def _is_new(card: Dict[str, Any]) -> bool:
    return int(card.get("state") or 0) == 0 and not card.get("last_review")


def _due_at(card: Dict[str, Any]) -> datetime.datetime:
    value = card.get("due")
    try:
        dt = value if isinstance(value, datetime.datetime) else datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return datetime.datetime.now(datetime.timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)


def is_reviewable(card: Dict[str, Any], now: Optional[datetime.datetime] = None) -> bool:
    """Thẻ được phép cập nhật lịch ôn từ trò chơi: đã học (không mới) và đã đến hạn."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return not _is_new(card) and _due_at(card) <= now


def _is_weak(card: Dict[str, Any]) -> bool:
    return int(card.get("lapses") or 0) > 0 or float(card.get("difficulty") or 0.0) >= 7.0


def select_cards(
    cards: Sequence[Dict[str, Any]],
    game: str,
    lang: Optional[str],
    count: int,
    now: Optional[datetime.datetime] = None,
    rng: Optional[random.Random] = None,
) -> List[Dict[str, Any]]:
    """
    Ưu tiên thẻ đến hạn (quá hạn lâu nhất trước) -> thẻ hay quên -> thẻ mới -> còn lại (xáo ngẫu nhiên trong từng nhóm).
    Loại thẻ trùng từ hoặc trùng nghĩa (để không có hai đáp án đúng) và thẻ thiếu nội dung.
    """
    rng = rng or random.Random()
    now = now or datetime.datetime.now(datetime.timezone.utc)
    eligible = []
    for card in cards:
        term, definition = str(card.get("term") or "").strip(), str(card.get("definition") or "").strip()
        if not term or not definition:
            continue
        if game == "builder" and not is_builder_word(term, lang):
            continue
        eligible.append(card)

    due = sorted((c for c in eligible if is_reviewable(c, now)), key=_due_at)
    used = {id(c) for c in due}
    weak = [c for c in eligible if id(c) not in used and not _is_new(c) and _is_weak(c)]
    used |= {id(c) for c in weak}
    new = [c for c in eligible if id(c) not in used and _is_new(c)]
    used |= {id(c) for c in new}
    rest = [c for c in eligible if id(c) not in used]
    for group in (weak, new, rest):
        rng.shuffle(group)

    chosen: List[Dict[str, Any]] = []
    seen_terms, seen_defs = set(), set()
    for card in due + weak + new + rest:
        t, d = str(card["term"]).strip().lower(), str(card["definition"]).strip().lower()
        if t in seen_terms or d in seen_defs:
            continue
        seen_terms.add(t)
        seen_defs.add(d)
        chosen.append(card)
        if len(chosen) >= count:
            break
    return chosen


# ---- chấm điểm -----------------------------------------------------------------------------------

def _clamp(value: Any, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return lo


def normalize_items(items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "card_id": str(it.get("card_id")),
            "correct": bool(it.get("correct")),
            "attempts": _clamp(it.get("attempts"), 0, MAX_ATTEMPTS),
            "hints": _clamp(it.get("hints"), 0, MAX_HINTS),
        }
        for it in items
    ]


def speed_multiplier(combo_before: int) -> int:
    """×1 cho 3 câu đúng đầu, rồi ×2, ×3 ... tối đa ×5."""
    return min(1 + combo_before // 3, 5)


def score_session(game: str, mode: str, items: Sequence[Dict[str, Any]], duration_ms: int = 0) -> Dict[str, int]:
    """Trả về điểm, sao, XP và các số liệu tổng hợp. `items` theo THỨ TỰ trả lời."""
    its = normalize_items(items)
    total = len(its)
    correct = sum(1 for i in its if i["correct"])
    mistakes = sum(i["attempts"] for i in its)
    hints = sum(i["hints"] for i in its)
    best_combo = 0
    score = 0
    stars = 0

    if game == "match":
        for i in its:
            if i["correct"]:
                score += max(25, 100 - 15 * min(i["attempts"], 5))
        finished = total > 0 and correct == total
        if finished:
            stars = 3 if mistakes <= 2 else 2 if mistakes <= 5 else 1
            if mode == "challenge":
                # Thưởng tốc độ; tối thiểu 0,8 s/cặp để dữ liệu thời gian giả không nhận thưởng tối đa.
                seconds = max(duration_ms, 800 * total) / 1000
                score += int(max(0.0, 90.0 - seconds)) * 2

    elif game == "speed":
        combo = 0
        for i in its:
            if i["correct"]:
                score += 10 * speed_multiplier(combo)
                combo += 1
                best_combo = max(best_combo, combo)
            else:
                combo = 0
        accuracy = correct / total if total else 0.0
        stars = 3 if correct >= 10 and accuracy >= 0.9 else 2 if correct >= 5 and accuracy >= 0.7 else 1 if correct >= 1 else 0

    elif game == "shooter":
        # Mỗi từ = một lượt ngắm bắn. Bắn đúng ngay: 10 × hệ số combo; bắn sai trước khi trúng thì mất combo và bị trừ điểm.
        # Bóng đúng trôi chạm đáy (correct=False) là 0 điểm và cũng mất combo.
        combo = 0
        for i in its:
            if i["correct"] and i["attempts"] == 0:
                score += 10 * speed_multiplier(combo)
                combo += 1
                best_combo = max(best_combo, combo)
            elif i["correct"]:
                score += max(5, 10 - 3 * i["attempts"])
                combo = 0
            else:
                combo = 0
        ratio = correct / total if total else 0.0
        stars = 3 if ratio == 1 and mistakes <= 2 else 2 if ratio >= 0.8 else 1 if correct >= 1 else 0

    elif game == "builder":
        for i in its:
            if i["correct"]:
                score += max(20, 100 - 25 * i["hints"] - 10 * i["attempts"])
        ratio = correct / total if total else 0.0
        stars = 3 if ratio == 1 and hints == 0 else 2 if ratio >= 0.8 else 1 if correct >= 1 else 0

    else:
        raise ValueError(f"Trò chơi không hợp lệ: {game}")

    xp = correct * 10 + stars * 10
    if mode == "challenge":
        xp = int(xp * 1.5)
    return {
        "total": total, "correct": correct, "mistakes": mistakes, "hints": hints, "best_combo": best_combo,
        "score": score, "stars": stars, "xp": xp,
    }


# ---- lịch ôn ---------------------------------------------------------------------------------------

def grade_for(item: Dict[str, Any]) -> int:
    """Again(1) / Hard(2) / Good(3). Không bao giờ Easy."""
    if not item["correct"]:
        return 1
    return 3 if item["attempts"] == 0 and item["hints"] == 0 else 2


def review_plan(items: Sequence[Dict[str, Any]], cards_by_id: Dict[str, Dict[str, Any]], now: Optional[datetime.datetime] = None) -> List[Tuple[str, int]]:
    """[(card_id, grade)] cho các thẻ đủ điều kiện, mỗi thẻ một lần (lần xuất hiện đầu tiên)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    plan: List[Tuple[str, int]] = []
    seen = set()
    for it in normalize_items(items):
        cid = it["card_id"]
        if cid in seen:
            continue
        seen.add(cid)
        card = cards_by_id.get(cid)
        if card is not None and is_reviewable(card, now):
            plan.append((cid, grade_for(it)))
    return plan


# ---- XP / cấp độ -----------------------------------------------------------------------------------

def level_for_xp(xp: int) -> Dict[str, int]:
    """Cấp n cần 100·(n-1)² XP: 0, 100, 400, 900 ..."""
    xp = max(0, int(xp))
    level = 1 + int(math.sqrt(xp / 100))
    floor_xp, next_xp = 100 * (level - 1) ** 2, 100 * level ** 2
    return {"level": level, "xp": xp, "level_floor_xp": floor_xp, "next_level_xp": next_xp}
