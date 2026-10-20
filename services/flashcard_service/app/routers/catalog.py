from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.flashcards import ApiResult
from app.services.catalog_service import clone_catalog_deck, get_catalog_preview, list_catalog
from app.utils.security import get_current_user_id

router = APIRouter(tags=["Flashcard Catalog (thư viện bộ từ)"])


@router.get("/catalog/decks", response_model=ApiResult)
async def list_catalog_endpoint(
    category: Optional[str] = Query(None, max_length=40),
    level: Optional[str] = Query(None, pattern="^(A1|A2|B1|B2|C1|C2)$"),
    q: Optional[str] = Query(None, max_length=60),
    user_id: str = Depends(get_current_user_id),
):
    """Các bộ từ vựng hệ thống đã xuất bản; `added_deck_id` có giá trị nếu bạn đã thêm bộ này vào sổ của mình."""
    return ApiResult(ok=True, data=await list_catalog(user_id, category=category, level=level, query=q))


@router.get("/catalog/decks/{deck_id}/preview", response_model=ApiResult)
async def catalog_preview_endpoint(
    deck_id: str,
    limit: int = Query(10, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
):
    """Xem trước một số thẻ đầu của bộ từ (không tạo gì trong sổ của bạn)."""
    return ApiResult(ok=True, data=await get_catalog_preview(deck_id, limit))


@router.post("/catalog/decks/{deck_id}/clone", response_model=ApiResult)
async def clone_catalog_endpoint(deck_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Thêm bộ từ vào sổ của bạn: sao chép thẻ sang một deck riêng với trạng thái học mới.
    Idempotent: đã thêm rồi thì trả lại sổ đó (`created=false`).
    """
    return ApiResult(ok=True, data=await clone_catalog_deck(deck_id, user_id))
