import datetime
from typing import Dict, Any, Optional

try:
    from fsrs import FSRS, Card, Rating
    HAS_FSRS = True
except ImportError:
    HAS_FSRS = False

def calculate_fsrs(
    grade: int,
    repetition: int = 0,
    stability: float = 0.0,
    difficulty: float = 0.0,
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    grade: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
    Returns updated FSRS fields.
    """
    if not HAS_FSRS:
        # Fallback to simple SM-2 like logic if FSRS is not installed correctly
        return _fallback_sm2(grade, repetition, stability, difficulty)
        
    f = FSRS()
    card = Card()
    card.reps = repetition
    if stability > 0:
        card.stability = stability
    if difficulty > 0:
        card.difficulty = difficulty
    if due_date:
        try:
            card.due = datetime.datetime.fromisoformat(due_date)
        except:
            card.due = datetime.datetime.now(datetime.timezone.utc)
            
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Map 1..4 grade to fsrs Rating
    rating_map = {
        1: Rating.Again,
        2: Rating.Hard,
        3: Rating.Good,
        4: Rating.Easy
    }
    rating = rating_map.get(grade, Rating.Good)
    
    scheduling_cards = f.repeat(card, now)
    new_card = scheduling_cards[rating].card
    
    return {
        "repetition": new_card.reps,
        "stability": round(new_card.stability, 4),
        "difficulty": round(new_card.difficulty, 4),
        "next_review_date": new_card.due.isoformat()
    }

def _fallback_sm2(grade: int, repetition: int, ease: float, diff: float):
    # Dummy fallback if library missing
    new_repetition = 0 if grade <= 1 else repetition + 1
    new_interval = 1 if grade <= 1 else (6 if repetition == 1 else int(2.5 * repetition))
    next_review = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=new_interval)
    return {
        "repetition": new_repetition,
        "stability": ease or 2.5,
        "difficulty": diff or 1.0,
        "next_review_date": next_review.isoformat()
    }
