from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.flashcards import ApiResult
from app.schemas.games import SubmitGameSessionRequest
from app.services.game_service import get_game_cards, get_game_stats, submit_session
from app.utils.security import get_current_user_id

router = APIRouter(tags=["Trò chơi ôn từ vựng"])


@router.get("/games/stats", response_model=ApiResult)
async def game_stats_endpoint(lang_code: Optional[str] = Query(None, max_length=10), user_id: str = Depends(get_current_user_id)):
    """Cấp độ/XP và kỷ lục cá nhân theo từng trò và chế độ (lọc theo ngôn ngữ nếu có)."""
    return ApiResult(ok=True, data=await get_game_stats(user_id, lang_code))


@router.get("/games/{game}/cards", response_model=ApiResult)
async def game_cards_endpoint(
    game: str,
    deck_id: str = Query(..., max_length=64),
    count: Optional[int] = Query(None, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
):
    """Bộ thẻ cho một ván (ưu tiên thẻ đến hạn). `playable=false` kèm lý do khi sổ chưa đủ điều kiện."""
    return ApiResult(ok=True, data=await get_game_cards(user_id, game, deck_id, count))


@router.post("/games/sessions", response_model=ApiResult)
async def submit_game_session_endpoint(payload: SubmitGameSessionRequest, user_id: str = Depends(get_current_user_id)):
    """
    Ghi một ván đã chơi. Điểm/sao/XP do máy chủ tự tính; thẻ đã đến hạn được cập nhật lịch ôn FSRS
    (đúng ngay = Good, cần thử lại/gợi ý = Hard, sai = Again, không bao giờ Easy) khi `apply_review` bật.
    """
    return ApiResult(ok=True, data=await submit_session(user_id, payload))
