from typing import Optional, List
from fastapi import APIRouter, Header, Depends, HTTPException
from app.schemas.flashcards import CreateDeckRequest, CreateCardRequest, ReviewCardRequest, ApiResult
from app.services.flashcard_service import (
    create_deck,
    get_decks,
    create_card,
    review_card,
    get_deck_cards,
    delete_card
)
from app.utils.security import get_current_user_id

router = APIRouter(tags=["Flashcard Spaced Repetition Service"])

@router.post("/decks", response_model=ApiResult)
async def create_deck_endpoint(
    payload: CreateDeckRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Tạo bộ thẻ mới cho người dùng đã đăng nhập."""
    data = await create_deck(payload.title, payload.description, user_id)
    return ApiResult(ok=True, data=data)

@router.get("/decks", response_model=ApiResult)
async def get_decks_endpoint(
    user_id: str = Depends(get_current_user_id)
):
    """Lấy danh sách các bộ thẻ của người dùng hiện tại."""
    data = await get_decks(user_id)
    return ApiResult(ok=True, data=data)

@router.get("/decks/{deck_id}/cards", response_model=ApiResult)
async def get_deck_cards_endpoint(
    deck_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Lấy danh sách thẻ trong bộ thẻ với kiểm tra quyền sở hữu."""
    data = await get_deck_cards(deck_id, user_id)
    return ApiResult(ok=True, data=data)

@router.post("/cards", response_model=ApiResult)
async def create_card_endpoint(
    payload: CreateCardRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Tạo thẻ mới gắn liền với user_id và kiểm tra quyền sở hữu deck."""
    data = await create_card(
        deck_id=payload.deck_id,
        front_text=payload.front_text,
        back_text=payload.back_text,
        user_id=user_id,
        phonetic=payload.phonetic,
        audio_url=payload.audio_url,
        example_sentence=payload.example_sentence
    )
    return ApiResult(ok=True, data=data)

@router.post("/review", response_model=ApiResult)
async def review_card_endpoint(
    payload: ReviewCardRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Ôn tập thẻ với thuật toán FSRS và bảo vệ IDOR (chỉ chủ sở hữu mới được cập nhật thẻ)."""
    updated_card = await review_card(card_id=payload.card_id, grade=payload.grade, user_id=user_id)
    return ApiResult(ok=True, data=updated_card)

@router.delete("/cards/{card_id}", response_model=ApiResult)
async def delete_card_endpoint(
    card_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Xóa thẻ với kiểm tra quyền sở hữu."""
    success = await delete_card(card_id, user_id)
    return ApiResult(ok=True, data={"deleted": success})
