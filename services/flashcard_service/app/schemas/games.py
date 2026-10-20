from typing import List, Literal

from pydantic import BaseModel, Field


class GameItem(BaseModel):
    """Kết quả MỘT câu/cặp/từ, theo thứ tự trả lời. Client không gửi điểm: máy chủ tự tính."""
    card_id: str = Field(..., min_length=1, max_length=64)
    correct: bool
    attempts: int = Field(0, ge=0, le=100, description="Số lần chọn/ghép/xếp sai trước khi xong câu này")
    hints: int = Field(0, ge=0, le=20, description="Số lần xem gợi ý (Xếp chữ)")


class SubmitGameSessionRequest(BaseModel):
    client_request_id: str = Field(..., min_length=8, max_length=64)
    game: Literal["match", "speed", "builder", "shooter"]
    mode: Literal["relax", "challenge"] = "relax"
    deck_id: str = Field(..., min_length=1, max_length=64)
    duration_ms: int = Field(0, ge=0, le=3_600_000)
    items: List[GameItem] = Field(..., min_length=1, max_length=100)
    apply_review: bool = True
