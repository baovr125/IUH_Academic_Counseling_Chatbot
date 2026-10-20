"""Lập lịch ôn tập FSRS (gói ``fsrs`` >= 6, API ``Scheduler``).

Ánh xạ giữa bảng ``flashcards`` và ``fsrs.Card``:

- ``state`` trong DB: 0 = New, 1 = Learning, 2 = Review, 3 = Relearning. Gói ``fsrs`` 6.x không có
  trạng thái New (thẻ mới là ``Learning`` với ``stability=None``), nên New được dựng bằng ``Card()`` mới.
- DB không lưu ``step`` (bước học trong ngày) nên Scheduler được cấu hình ``learning_steps=()`` và
  ``relearning_steps=()``: thẻ ra khỏi trạng thái mới sau lần ôn đầu và luôn có khoảng cách tính bằng ngày.
  Vì thế sau khi ôn thẻ chỉ ở trạng thái Review (2).
- ``reps``, ``lapses``, ``elapsed_days``, ``scheduled_days`` do module này tự tính vì ``Card`` mới không giữ chúng.

Nếu không nạp được ``fsrs`` (thiếu gói hoặc sai phiên bản) module chuyển sang bộ lập lịch dự phòng
đơn giản và ghi log CẢNH BÁO; ``HAS_FSRS`` cho biết nhánh nào đang chạy để test/health-check phát hiện.
"""
import datetime
from typing import Any, Dict, Optional

from app.utils.logger import logger

try:
    from fsrs import Card, Rating, Scheduler, State

    HAS_FSRS = True
except ImportError:  # pragma: no cover - phụ thuộc môi trường
    HAS_FSRS = False
    logger.warning(
        "Không nạp được `fsrs` >= 6 (Scheduler): đang dùng bộ lập lịch DỰ PHÒNG, stability/difficulty "
        "KHÔNG phải kết quả FSRS. Cài `fsrs>=6,<7` theo requirements.txt."
    )

_scheduler: Optional["Scheduler"] = None


def _get_scheduler() -> "Scheduler":
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler(learning_steps=(), relearning_steps=(), enable_fuzzing=True)
    return _scheduler


def _parse_dt(value: Any) -> Optional[datetime.datetime]:
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        dt = value
    else:
        try:
            dt = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)


def _positive(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _build_card(card_dict: Dict[str, Any], now: datetime.datetime) -> "Card":
    """Dựng ``fsrs.Card`` từ hàng DB. Thẻ chưa có stability/difficulty hợp lệ được coi là thẻ mới."""
    stability = _positive(card_dict.get("stability"))
    difficulty = _positive(card_dict.get("difficulty"))
    last_review = _parse_dt(card_dict.get("last_review"))
    if stability is None or difficulty is None or last_review is None:
        return Card()
    return Card(
        state=State.Review,
        step=None,
        stability=stability,
        difficulty=min(10.0, max(1.0, difficulty)),
        due=_parse_dt(card_dict.get("due")) or now,
        last_review=last_review,
    )


def _fallback(grade: int, repetition: int, now: datetime.datetime, card_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Bộ lập lịch dự phòng cố định (KHÔNG phải FSRS)."""
    failed = grade <= 1
    new_reps = 0 if failed else repetition + 1
    interval = 1 if failed else (3 if repetition == 0 else int(2.5 * (repetition + 1)))
    return {
        "state": 2,
        "reps": new_reps,
        "lapses": int(card_dict.get("lapses") or 0) + (1 if failed and repetition > 0 else 0),
        "stability": round(float(card_dict.get("stability") or 2.5), 4),
        "difficulty": round(float(card_dict.get("difficulty") or 1.0), 4),
        "elapsed_days": 0,
        "scheduled_days": interval,
        "last_review": now.isoformat(),
        "due": (now + datetime.timedelta(days=interval)).isoformat(),
    }


def calculate_fsrs(
    grade: int,
    card_dict: Optional[Dict[str, Any]] = None,
    repetition: int = 0,
    stability: float = 0.0,
    difficulty: float = 0.0,
    due_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    grade: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy).
    Trả về các cột FSRS cần ghi lại vào ``flashcards``.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    if card_dict is None:
        card_dict = {"reps": repetition, "stability": stability, "difficulty": difficulty, "due": due_date}
    reps = int(card_dict.get("reps") or repetition or 0)

    if not HAS_FSRS:
        return _fallback(grade, reps, now, card_dict)

    card = _build_card(card_dict, now)
    was_review = card.state == State.Review and card.stability is not None
    last_review = card.last_review

    rating = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}.get(grade, Rating.Good)
    new_card, _log = _get_scheduler().review_card(card, rating, now)

    lapses = int(card_dict.get("lapses") or 0) + (1 if was_review and rating == Rating.Again else 0)
    elapsed_days = max(0, (now - last_review).days) if last_review else 0
    scheduled_days = max(0, round((new_card.due - now).total_seconds() / 86400))

    return {
        "state": int(new_card.state.value),
        "reps": reps + 1,
        "lapses": lapses,
        "stability": round(float(new_card.stability), 4),
        "difficulty": round(float(new_card.difficulty), 4),
        "elapsed_days": elapsed_days,
        "scheduled_days": scheduled_days,
        "last_review": (new_card.last_review or now).isoformat(),
        "due": new_card.due.isoformat(),
    }
