from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    source_lang: str = "en"
    target_lang: str = "vi"
    domain: Optional[str] = ""

class StreamTranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    source_lang: str = "en"
    target_lang: str = "vi"
    domain: Optional[str] = ""

class FlashcardExtractRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)
    context: str = Field(..., min_length=1, max_length=1000)
    domain: Optional[str] = ""

class LookupRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)

class TranslateResponse(BaseModel):
    translated_text: str
    source_lang: str
    target_lang: str
    cached: bool
    latency_ms: float
    warning: Optional[str] = None

class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class WordAnalysisRequest(BaseModel):
    text: str = Field(..., description="Câu context hoàn chỉnh")
    selected_text: str = Field(..., description="Từ được bôi đen")
    source_lang: str = "en"
    target_lang: str = "vi"

class MeaningDef(BaseModel):
    pos: str
    english_definition: str
    target_language_meaning: str
    examples: List[str] = []
    target_language_examples: List[str] = []

class WordAnalysisResponse(BaseModel):
    word: str
    lemma: str
    part_of_speech: str
    context: str
    contextual_meaning: Optional[MeaningDef] = None
    other_meanings: List[MeaningDef] = []
    cached: bool
    latency_ms: float
