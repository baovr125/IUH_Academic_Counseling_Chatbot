from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class GlossaryTerm(BaseModel):
    term: str = Field(..., description="Từ gốc tiếng Anh/ngôn ngữ nguồn")
    vi: Optional[str] = Field(None, description="Nghĩa dịch tiếng Việt theo học vụ IUH")
    translation: Optional[str] = Field(None, description="Nghĩa dịch chuẩn")
    context: Optional[str] = Field(None, description="Ngữ cảnh/Giải thích thêm")
    phonetic: Optional[str] = Field(None, description="Phiên âm quốc tế")
    audio_url: Optional[str] = Field(None, description="URL âm thanh phát âm")
    lang_code: Optional[str] = Field(None, description="Mã ngôn ngữ nguồn")


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    file_type: str
    status: str = Field("processing", description="Trạng thái khởi tạo: processing")
    message: str


class DocumentStatusResponse(BaseModel):
    doc_id: str
    status: str = Field(..., description="pending, processing, completed, failed")
    progress: int = Field(0, ge=0, le=100, description="Tiến độ xử lý 0-100%")
    message: str
    pages_processed: Optional[int] = 0
    total_pages: Optional[int] = 0
    translated_file_url: Optional[str] = None
    translated_text: Optional[str] = None
    summary_json: Optional[Dict[str, Any]] = None
    glossary: Optional[List[GlossaryTerm]] = []
    model_used: Optional[str] = None
    error: Optional[str] = None


class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
