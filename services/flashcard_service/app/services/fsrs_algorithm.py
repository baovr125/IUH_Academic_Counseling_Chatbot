import datetime
from typing import Dict, Any, Optional

try:
    from fsrs import FSRS, Card, Rating, State
    HAS_FSRS = True
except ImportError:
    HAS_FSRS = False

def calculate_fsrs(
    grade: int,
    card_dict: Optional[Dict[str, Any]] = None,
    repetition: int = 0,
    stability: float = 0.0,
    difficulty: float = 0.0,
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    grade: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
    Returns updated FSRS fields matching standard Card representation.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    
    if not HAS_FSRS:
        # Fallback to deterministic interval logic
        new_reps = 0 if grade <= 1 else repetition + 1
        new_interval = 1 if grade <= 1 else (3 if repetition == 0 else int(2.5 * (repetition + 1)))
        next_due = now + datetime.timedelta(days=new_interval)
        return {
            "state": 1 if grade <= 1 else 2,
            "reps": new_reps,
            "lapses": 1 if grade <= 1 else 0,
            "stability": round(stability or 2.5, 4),
            "difficulty": round(difficulty or 1.0, 4),
            "elapsed_days": 1,
            "scheduled_days": new_interval,
            "last_review": now.isoformat(),
            "due": next_due.isoformat()
        }

    f = FSRS()
    card = Card()
    
    if card_dict:
        card.reps = card_dict.get("reps", repetition)
        card.lapses = card_dict.get("lapses", 0)
        card.elapsed_days = card_dict.get("elapsed_days", 0)
        card.scheduled_days = card_dict.get("scheduled_days", 0)
        
        state_val = card_dict.get("state", 0)
        if isinstance(state_val, int) and 0 <= state_val <= 3:
            card.state = State(state_val)
            
        st = card_dict.get("stability", stability)
        if st and float(st) > 0:
            card.stability = float(st)
            
        df = card_dict.get("difficulty", difficulty)
        if df and float(df) > 0:
            card.difficulty = float(df)
            
        last_rev = card_dict.get("last_review")
        if last_rev:
            try:
                card.last_review = datetime.datetime.fromisoformat(last_rev)
            except Exception:
                pass
                
        due_val = card_dict.get("due", due_date)
        if due_val:
            try:
                card.due = datetime.datetime.fromisoformat(due_val)
            except Exception:
                card.due = now
    else:
        card.reps = repetition
        if stability > 0:
            card.stability = stability
        if difficulty > 0:
            card.difficulty = difficulty
        if due_date:
            try:
                card.due = datetime.datetime.fromisoformat(due_date)
            except Exception:
                card.due = now

    rating_map = {
        1: Rating.Again,
        2: Rating.Hard,
        3: Rating.Good,
        4: Rating.Easy
    }
    rating = rating_map.get(grade, Rating.Good)
    
    scheduling_cards = f.repeat(card, now)
    new_card = scheduling_cards[rating].card
    
    state_int = int(new_card.state.value) if hasattr(new_card.state, 'value') else int(new_card.state)
    
    return {
        "state": state_int,
        "reps": new_card.reps,
        "lapses": new_card.lapses,
        "stability": round(float(new_card.stability), 4),
        "difficulty": round(float(new_card.difficulty), 4),
        "elapsed_days": new_card.elapsed_days,
        "scheduled_days": new_card.scheduled_days,
        "last_review": new_card.last_review.isoformat() if new_card.last_review else now.isoformat(),
        "due": new_card.due.isoformat()
    }
