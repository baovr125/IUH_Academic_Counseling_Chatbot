from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

CefrLevel = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
# 9 ngôn ngữ có thể học (không gồm tiếng Việt - ngôn ngữ giải nghĩa). Khớp app.utils.languages.LEARNABLE_LANGS.
VocabLang = Literal["en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th"]
Purpose = Literal["general", "ielts", "toeic", "academic", "it", "business"]

MAX_TOPIC_CHARS = 100
MAX_TEXT_CHARS = 2000
MAX_INSTRUCTION_CHARS = 300
MAX_WORDS = 50
MIN_WORDS = 5


class GenerateVocabRequest(BaseModel):
    """
    Yêu cầu sinh từ vựng. `mode=topic`: theo chủ đề; `mode=text`: trích từ quan trọng từ đoạn văn (viết bằng `lang_code`).
    `lang_code` là ngôn ngữ của TỪ VỰNG được sinh; nghĩa/dịch câu ví dụ luôn bằng tiếng Việt.
    """
    mode: Literal["topic", "text"] = "topic"
    topic: Optional[str] = Field(None, max_length=MAX_TOPIC_CHARS)
    text: Optional[str] = Field(None, max_length=MAX_TEXT_CHARS)
    lang_code: VocabLang = "en"
    level: CefrLevel = "B1"
    count: int = Field(20, ge=MIN_WORDS, le=MAX_WORDS)
    purpose: Optional[Purpose] = None
    instruction: Optional[str] = Field(None, max_length=MAX_INSTRUCTION_CHARS)
    exclude_terms: List[str] = Field(default_factory=list, max_length=200)
    deck_id: Optional[str] = None

    @model_validator(mode="after")
    def _check_input_for_mode(self):
        if self.mode == "topic":
            if not self.topic or len(self.topic.strip()) < 2:
                raise ValueError("Vui lòng nhập chủ đề (ít nhất 2 ký tự).")
        else:
            if not self.text or len(self.text.strip()) < 20:
                raise ValueError("Vui lòng nhập đoạn văn (ít nhất 20 ký tự).")
        self.exclude_terms = [t.strip()[:80] for t in self.exclude_terms if t and t.strip()]
        return self


class GeneratedItem(BaseModel):
    temp_id: str
    term: str
    part_of_speech: str
    ipa: str = ""
    definition: str
    example: str = ""
    example_translation: str = ""
    level: str = ""
    warnings: List[str] = Field(default_factory=list)
    verified: bool = False


class DroppedItem(BaseModel):
    term: str
    reason: str


class GenerateVocabData(BaseModel):
    generation_id: str
    mode: str
    lang_code: str = "en"
    topic: Optional[str] = None
    level: str
    requested: int
    returned: int
    items: List[GeneratedItem]
    dropped: List[DroppedItem] = Field(default_factory=list)
    providers: List[str] = Field(default_factory=list)
    stages: dict = Field(default_factory=dict)
    latency_ms: int = 0
    usage: dict = Field(default_factory=dict)
    quota: Optional[dict] = None


class CommitCard(BaseModel):
    term: str = Field(..., min_length=1, max_length=500)
    definition: str = Field(..., min_length=1, max_length=1000)
    part_of_speech: Optional[str] = Field(None, max_length=50)
    phonetic: Optional[str] = Field(None, max_length=255)
    example: Optional[str] = Field(None, max_length=1000)
    example_translation: Optional[str] = Field(None, max_length=1000)
    level: Optional[str] = Field(None, max_length=8)


class CommitDeck(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    # Bỏ trống = theo `source.lang_code`; cả hai bỏ trống thì là tiếng Anh (hành vi cũ). Giá trị lạ bị từ chối ở router.
    lang_code: Optional[str] = None


class CommitSource(BaseModel):
    mode: Literal["topic", "text", "image"] = "topic"
    # Ngôn ngữ của các từ được lưu. Thêm vào sổ có sẵn: bỏ trống = theo sổ, khác sổ -> 409 LANG_MISMATCH.
    lang_code: Optional[VocabLang] = None
    topic: Optional[str] = Field(None, max_length=MAX_TOPIC_CHARS)
    level: Optional[CefrLevel] = None


class CommitGeneratedRequest(BaseModel):
    """Lưu danh sách từ đã xem trước/chỉnh sửa thành deck mới hoặc thêm vào deck có sẵn."""
    client_request_id: str = Field(..., min_length=8, max_length=64)
    deck: Optional[CommitDeck] = None
    deck_id: Optional[str] = None
    cards: List[CommitCard] = Field(..., min_length=1, max_length=200)
    source: CommitSource = Field(default_factory=CommitSource)

    @model_validator(mode="after")
    def _need_deck(self):
        if not self.deck and not self.deck_id:
            raise ValueError("Cần `deck` (tạo bộ thẻ mới) hoặc `deck_id` (thêm vào bộ thẻ có sẵn).")
        return self
