from typing import List, Optional, Any, Literal
from pydantic import BaseModel, Field, validator


class Citation(BaseModel):
    id: str
    sourceTitle: str
    pageOrSection: str
    snippet: Optional[str] = None
    url: Optional[str] = None


class ChatMessage(BaseModel):
    id: str
    role: Literal['user', 'assistant']
    original_answer: Optional[str] = None
    content: str
    citations: Optional[List[Citation]] = None
    createdAt: str
    status: str


class SendMessagePayload(BaseModel):
    sessionId: Optional[str] = None
    content: str = Field(..., min_length=1, max_length=2000)

    @validator('content')
    def strip_whitespace(cls, v):
        return v.strip()


class SendMessageResponseData(BaseModel):
    sessionId: str
    message: ChatMessage


class RenameSessionPayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)


class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[dict] = None

class FeedbackPayload(BaseModel):
    feedback: Literal['like', 'dislike']
    comment: Optional[str] = Field(None, max_length=500)
