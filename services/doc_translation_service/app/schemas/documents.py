from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DocumentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)

class DocumentQueryResponse(BaseModel):
    doc_id: str
    answer: str
    citations: List[Dict[str, Any]]

class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
