from typing import Optional
from fastapi import APIRouter, Header
from app.schemas.flashcards import CreateDeckRequest, CreateCardRequest, ReviewCardRequest, ApiResult
from app.services.flashcard_service import create_deck, create_card, review_card

router = APIRouter(tags=["Flashcard Spaced Repetition Service"])

@router.post("/decks")
async def create_deck_endpoint(payload: CreateDeckRequest, x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    data = await create_deck(payload.title, payload.description, x_user_id or "anonymous")
    return ApiResult(ok=True, data=data)

@router.post("/cards")
async def create_card_endpoint(payload: CreateCardRequest):
    data = await create_card(
        deck_id=payload.deck_id,
        front_text=payload.front_text,
        back_text=payload.back_text,
        phonetic=payload.phonetic,
        audio_url=payload.audio_url,
        example_sentence=payload.example_sentence
    )
    return ApiResult(ok=True, data=data)

@router.post("/review")
async def review_card_endpoint(payload: ReviewCardRequest):
    updated_card = await review_card(card_id=payload.card_id, grade=payload.grade)
    return ApiResult(ok=True, data=updated_card)
