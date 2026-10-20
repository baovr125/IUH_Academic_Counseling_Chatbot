from fastapi import APIRouter, Depends, Query

from app.rabbitmq_consumer import publish_flashcard_created_event
from app.schemas.flashcards import ApiResult
from app.schemas.languages import SaveFromTranslationRequest, SetDeckLanguageRequest
from app.services.flashcard_service import set_deck_language
from app.services.language_service import (
    SORTS,
    STATUSES,
    language_summary,
    list_language_cards,
    save_from_translation,
)
from app.utils.logger import logger
from app.utils.security import get_current_user_id

router = APIRouter(tags=["Flashcard theo ngôn ngữ"])


@router.get("/languages", response_model=ApiResult)
async def get_languages_endpoint(user_id: str = Depends(get_current_user_id)):
    """
    Tổng hợp 10 bộ sưu tập ngôn ngữ của bạn (số sổ, số từ, đến hạn, mới, hay quên) và các bộ thẻ còn
    "cần xác nhận ngôn ngữ" (dữ liệu cũ chưa rõ ngôn ngữ: không bị gán bừa vào ngôn ngữ nào).
    """
    return ApiResult(ok=True, data=await language_summary(user_id))


@router.get("/languages/{lang_code}/cards", response_model=ApiResult)
async def get_language_cards_endpoint(
    lang_code: str,
    q: str | None = Query(None, max_length=60),
    sort: str = Query("recent", description=f"một trong {SORTS}"),
    status: str = Query("all", description=f"một trong {STATUSES}"),
    deck_id: str | None = Query(None, max_length=64),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    """Tất cả từ vựng của một ngôn ngữ: tìm kiếm, lọc (đến hạn/mới/hay quên), sắp xếp và phân trang ở máy chủ."""
    data = await list_language_cards(user_id, lang_code, q=q, sort=sort, status=status, deck_id=deck_id, limit=limit, offset=offset)
    return ApiResult(ok=True, data=data)


@router.post("/cards/from-translation", response_model=ApiResult)
async def save_from_translation_endpoint(payload: SaveFromTranslationRequest, user_id: str = Depends(get_current_user_id)):
    """
    Lưu từ từ Realtime Translation vào đúng bộ sưu tập ngôn ngữ nguồn (nghĩa tiếng Việt).
    Lỗi: 422 LANG_REQUIRED/LANG_UNSUPPORTED, 409 LANG_MISMATCH/DUPLICATE_CARD, 403 (sổ của người khác).
    """
    data = await save_from_translation(user_id, payload)
    if data.get("created"):
        card = data["card"]
        try:
            await publish_flashcard_created_event(
                card_id=card["id"], term=card["term"], lang_code=card["lang_code"], user_id=user_id, phonetic=card.get("phonetic")
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Could not publish flashcard.created event: {exc}")
    return ApiResult(ok=True, data=data)


@router.post("/decks/{deck_id}/language", response_model=ApiResult)
async def set_deck_language_endpoint(deck_id: str, payload: SetDeckLanguageRequest, user_id: str = Depends(get_current_user_id)):
    """Xác nhận/đổi ngôn ngữ của cả bộ thẻ (mọi thẻ đổi theo). Dùng cho mục "Cần xác nhận ngôn ngữ"."""
    return ApiResult(ok=True, data=await set_deck_language(deck_id, user_id, payload.lang_code))
