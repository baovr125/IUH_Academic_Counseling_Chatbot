from typing import List, Optional, Any
from pydantic import BaseModel


class Citation(BaseModel):
    id: str
    sourceTitle: str
    pageOrSection: str
    snippet: Optional[str] = None
    url: Optional[str] = None


class ChatMessage(BaseModel):
    id: str
    role: str
    original_answer: Optional[str] = None
    content: str
    citations: Optional[List[Citation]] = None
    createdAt: str
    status: str


class SendMessagePayload(BaseModel):
    sessionId: Optional[str] = None
    content: str


class SendMessageResponseData(BaseModel):
    sessionId: str
    message: ChatMessage


class RenameSessionPayload(BaseModel):
    title: str


class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[dict] = None
