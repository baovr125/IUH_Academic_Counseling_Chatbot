from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CreateDeckRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    lang_code: Optional[str] = "en"

class UpdateDeckRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    lang_code: Optional[str] = None

class CreateCardRequest(BaseModel):
    deck_id: str
    front_text: str = Field(..., min_length=1, max_length=500)
    back_text: str = Field(..., min_length=1, max_length=1000)
    phonetic: Optional[str] = None
    audio_url: Optional[str] = None
    example_sentence: Optional[str] = None
    part_of_speech: Optional[str] = None
    lang_code: Optional[str] = "en"

class UpdateCardRequest(BaseModel):
    front_text: Optional[str] = Field(None, min_length=1, max_length=500)
    back_text: Optional[str] = Field(None, min_length=1, max_length=1000)
    phonetic: Optional[str] = None
    example_sentence: Optional[str] = None
    part_of_speech: Optional[str] = None
    lang_code: Optional[str] = None

class ReviewCardRequest(BaseModel):
    card_id: str
    grade: int = Field(..., ge=0, le=5)  # Quality 0 to 5 (1: Again, 2: Hard, 3: Good, 4: Easy)

class VerifySpellingRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=500)
    auto_apply_review: Optional[bool] = False  # Tự động cập nhật FSRS grade nếu muốn

class VerifySpellingResponse(BaseModel):
    is_correct: bool
    is_close: bool = False
    similarity_score: float
    correct_term: str
    user_input: str
    feedback: str
    suggested_grade: int
    audio_url: Optional[str] = None
    phonetic: Optional[str] = None
    example_sentence: Optional[str] = None
    lang_code: Optional[str] = "en"

class StudyCardItem(BaseModel):
    id: str
    deck_id: str
    term: str
    definition: str
    phonetic: Optional[str] = None
    audio_url: Optional[str] = None
    example_sentence: Optional[str] = None
    part_of_speech: Optional[str] = None
    lang_code: Optional[str] = "en"
    state: int
    stability: float
    difficulty: float
    due: str
    recommended_mode: str = "flip"  # "flip" | "spelling"
    cloze_sentence: Optional[str] = None

class CardResponse(BaseModel):
    id: str
    deck_id: str
    front_text: str
    back_text: str
    phonetic: Optional[str] = None
    audio_url: Optional[str] = None
    example_sentence: Optional[str] = None
    part_of_speech: Optional[str] = None
    lang_code: Optional[str] = "en"
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
