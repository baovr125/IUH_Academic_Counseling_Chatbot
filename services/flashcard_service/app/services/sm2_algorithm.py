import datetime
from typing import Tuple, Dict, Any

def calculate_sm2(
    grade: int,
    repetition: int = 0,
    ease_factor: float = 2.5,
    interval_days: int = 1
) -> Dict[str, Any]:
    """
    Computes the SuperMemo 2 (SM-2) algorithm metrics.
    grade: integer 0 (complete blackout) to 5 (perfect response)
    """
    if grade < 3:
        new_repetition = 0
        new_interval = 1
    else:
        if repetition == 0:
            new_interval = 1
        elif repetition == 1:
            new_interval = 6
        else:
            new_interval = int(round(interval_days * ease_factor))
        new_repetition = repetition + 1

    # Update ease factor formula
    new_ef = ease_factor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    if new_ef < 1.3:
        new_ef = 1.3

    next_review = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=new_interval)

    return {
        "repetition": new_repetition,
        "ease_factor": round(new_ef, 2),
        "interval_days": new_interval,
        "next_review_date": next_review.isoformat()
    }
