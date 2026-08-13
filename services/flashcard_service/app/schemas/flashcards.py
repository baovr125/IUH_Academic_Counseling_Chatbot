from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CreateDeckRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class CreateCardRequest(BaseModel):
    deck_id: str
    front_text: str = Field(..., min_length=1, max_length=500)
    back_text: str = Field(..., min_length=1, max_length=1000)
    phonetic: Optional[str] = None
    audio_url: Optional[str] = None
    example_sentence: Optional[str] = None

class ReviewCardRequest(BaseModel):
    card_id: str
    grade: int = Field(..., ge=0, le=5)  # Quality 0 to 5

class CardResponse(BaseModel):
    id: str
    deck_id: str
    front_text: str
    back_text: str
    phonetic: Optional[str] = None
    audio_url: Optional[str] = None
    example_sentence: Optional[str] = None
    # SM-2 / FSRS combined fields
    repetition: int
    ease_factor: Optional[float] = 2.5
    interval_days: int
    stability: Optional[float] = None
    difficulty: Optional[float] = None
    lapses: Optional[int] = 0
    next_review_date: str

class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
