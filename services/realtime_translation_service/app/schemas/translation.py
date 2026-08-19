from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    source_lang: str = "en"
    target_lang: str = "vi"

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

class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
