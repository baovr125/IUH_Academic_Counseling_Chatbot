from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    source_lang: str = Field("en", pattern="^(en|de|zh|ja|ko|fr|es|ru|th|vi|auto)$")
    target_lang: str = Field("vi", pattern="^(en|de|zh|ja|ko|fr|es|ru|th|vi)$")
    domain: Optional[str] = ""
    # Gợi ý ngôn ngữ từ lần nhận diện trước (chỉ dùng khi source_lang="auto").
    source_lang_hint: Optional[str] = Field(None, pattern="^(en|de|zh|ja|ko|fr|es|ru|th|vi)$")

class StreamTranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    source_lang: str = Field("en", pattern="^(en|de|zh|ja|ko|fr|es|ru|th|vi|auto)$")
    target_lang: str = Field("vi", pattern="^(en|de|zh|ja|ko|fr|es|ru|th|vi)$")
    domain: Optional[str] = ""
    source_lang_hint: Optional[str] = Field(None, pattern="^(en|de|zh|ja|ko|fr|es|ru|th|vi)$")

class FlashcardExtractRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)
    context: str = Field(..., min_length=1, max_length=1000)
    domain: Optional[str] = ""

class LookupRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)

class DetectionCandidate(BaseModel):
    language: str
    confidence: float

class LanguageDetectionDetails(BaseModel):
    # Chỉ có giá trị khi status="detected" (hoặc ngôn ngữ do người dùng chọn thủ công).
    resolved_source_lang: Optional[str] = None
    status: str = "detected"  # detected | uncertain | unknown | unsupported | invalid_input | system_error
    confidence: float = 0.0
    margin: float = 0.0
    engine: str = "none"  # fusion | fasttext | lingua | script | hint | manual | none
    # Tối đa 3 ngôn ngữ ĐƯỢC HỖ TRỢ có khả năng cao nhất (dùng cho UI chọn ngôn ngữ).
    candidates: List[DetectionCandidate] = []
    is_multilingual: bool = False
    message: Optional[str] = None
    # short_input | low_confidence | engines_disagree | out_of_scope | script_mismatch | mixed_language
    reason: Optional[str] = None
    # Với status="unsupported": mã/tên ngôn ngữ thực tế được nhận ra (vd "it", "ar").
    detected_language: Optional[str] = None

class LanguageDetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    source_lang_hint: Optional[str] = Field(None, pattern="^(en|de|zh|ja|ko|fr|es|ru|th|vi)$")

class DomainCandidate(BaseModel):
    domain: str
    term: Optional[str] = None
    translation: Optional[str] = None


class DomainDetails(BaseModel):
    # selected: người dùng chọn thủ công | detected | ambiguous | unknown | error
    status: str = "unknown"
    domain: Optional[str] = None
    confidence: float = 0.0
    # manual | exact | llm | lexical_llm | none
    method: str = "none"
    # Thuật ngữ từ điển tìm thấy trong văn bản (đã bóc HTML) thuộc domain được chọn/nhận diện.
    matched_terms: List[str] = []
    # Trong số đó, thuật ngữ mà bản dịch thực sự chứa bản dịch từ điển (kiểm tra sau khi dịch xong).
    applied_terms: List[str] = []
    # Với status="ambiguous": các domain cùng chứa thuật ngữ đó (UI cho người dùng chọn).
    candidates: List[DomainCandidate] = []
    # Lý do khi unknown/error: llm_unknown | low_confidence | llm_lexical_conflict | llm_unavailable | format_error ...
    reason: Optional[str] = None
    # Nguồn bản dịch: dictionary | llm | nllb
    translator: Optional[str] = None


class TranslationWarning(BaseModel):
    code: str
    # info | warning | error
    severity: str = "info"
    message: str
    domain: Optional[str] = None
    candidates: List[DomainCandidate] = []


class TranslateResponse(BaseModel):
    translated_text: str
    source_lang: str
    target_lang: str
    cached: bool
    latency_ms: float
    warning: Optional[str] = None
    resolved_source_lang: Optional[str] = None
    detection: Optional[LanguageDetectionDetails] = None
    # Chế độ chuyên ngành: kết quả nhận diện/chọn domain và danh sách cảnh báo có cấu trúc.
    domain: Optional[DomainDetails] = None
    warnings: List[TranslationWarning] = []

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
