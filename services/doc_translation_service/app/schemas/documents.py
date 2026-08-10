from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class GlossaryTerm(BaseModel):
    term: str = Field(..., description="Từ gốc tiếng Anh/ngôn ngữ nguồn")
    vi: str = Field(..., description="Nghĩa dịch chuẩn tiếng Việt theo học vụ IUH")
    context: Optional[str] = Field(None, description="Ngữ cảnh/Giải thích thêm")

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
    summary_json: Optional[Dict[str, Any]] = None
    glossary: Optional[List[GlossaryTerm]] = []
    error: Optional[str] = None

class CitationItem(BaseModel):
    page: int
    snippet: str
    score: Optional[float] = None

class DocumentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)

class DocumentQueryResponse(BaseModel):
    doc_id: str
    answer: str
    citations: List[CitationItem] = []

class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
