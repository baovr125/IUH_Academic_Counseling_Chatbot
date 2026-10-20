from typing import Literal, Optional

from pydantic import BaseModel, Field


class DetectionInfo(BaseModel):
    """Kết quả nhận diện ngôn ngữ của Realtime Translation (chỉ để ghi log/đối chiếu, không dùng để suy đoán)."""
    status: Optional[str] = Field(None, max_length=20)
    engine: Optional[str] = Field(None, max_length=20)
    confidence: Optional[float] = Field(None, ge=0, le=1)


class SaveFromTranslationRequest(BaseModel):
    """
    Lưu một cặp (từ/cụm từ ngoại ngữ -> nghĩa tiếng Việt) từ Realtime Translation vào đúng bộ sưu tập ngôn ngữ.
    `source_lang` KHÔNG có mặc định và không chấp nhận 'auto': thiếu/không rõ thì 422 LANG_REQUIRED.
    """
    client_request_id: str = Field(..., min_length=8, max_length=64)
    source_lang: Optional[str] = Field(None, max_length=10)
    target_lang: Literal["vi"] = "vi"
    term: str = Field(..., min_length=1, max_length=500)
    translation: str = Field(..., min_length=1, max_length=1000)
    phonetic: Optional[str] = Field(None, max_length=255)
    example: Optional[str] = Field(None, max_length=1000)
    example_translation: Optional[str] = Field(None, max_length=1000)
    part_of_speech: Optional[str] = Field(None, max_length=50)
    deck_id: Optional[str] = Field(None, max_length=64)
    on_duplicate: Literal["reject", "update"] = "reject"
    detection: Optional[DetectionInfo] = None


class SetDeckLanguageRequest(BaseModel):
    lang_code: str = Field(..., min_length=2, max_length=10)
