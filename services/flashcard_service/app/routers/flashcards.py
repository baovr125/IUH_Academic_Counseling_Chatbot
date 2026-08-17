from typing import Optional, List
from fastapi import APIRouter, Header, Depends, HTTPException
from fastapi.responses import Response
import edge_tts
from app.schemas.flashcards import (
    CreateDeckRequest,
    UpdateDeckRequest,
    CreateCardRequest,
    UpdateCardRequest,
    ReviewCardRequest,
    VerifySpellingRequest,
    VerifySpellingResponse,
    StudyCardItem,
    ApiResult
)
from app.services.flashcard_service import (
    create_deck,
    get_decks,
    update_deck,
    delete_deck,
    create_card,
    update_card,
    review_card,
    get_deck_cards,
    get_study_queue,
    verify_spelling,
    delete_card
)
from app.rabbitmq_consumer import publish_flashcard_created_event
from app.utils.security import get_current_user_id
from app.utils.logger import logger

router = APIRouter(tags=["Flashcard Spaced Repetition Service"])

TTS_VOICE_MAP = {
    # Short 2-letter codes
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-JennyNeural",
    "de": "de-DE-KatjaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "fr": "fr-FR-DeniseNeural",
    "es": "es-ES-ElviraNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "th": "th-TH-PremwadeeNeural",
    # Full Locale codes
    "vi-vn": "vi-VN-HoaiMyNeural",
    "en-us": "en-US-JennyNeural",
    "en-gb": "en-GB-SoniaNeural",
    "de-de": "de-DE-KatjaNeural",
    "zh-cn": "zh-CN-XiaoxiaoNeural",
    "ja-jp": "ja-JP-NanamiNeural",
    "ko-kr": "ko-KR-SunHiNeural",
    "fr-fr": "fr-FR-DeniseNeural",
    "es-es": "es-ES-ElviraNeural",
    "ru-ru": "ru-RU-SvetlanaNeural",
    "th-th": "th-TH-PremwadeeNeural"
}

def resolve_voice(lang: str) -> str:
    cleaned = (lang or "en").strip().lower().replace("_", "-")
    if cleaned in TTS_VOICE_MAP:
        return TTS_VOICE_MAP[cleaned]
    prefix = cleaned[:2]
    return TTS_VOICE_MAP.get(prefix, "en-US-JennyNeural")

@router.get("/tts")
async def tts_endpoint(text: str, lang: str = "en"):
    """
    Sinh file âm thanh phát âm chuẩn phòng thu (Microsoft Neural TTS) cho Flashcard:
    - Tự động chuẩn hóa giọng bản xứ theo ngôn ngữ (en, de, zh, ja, ko, fr, es, ru, th, vi...)
    - Tốc độ phát âm chuẩn ngữ điệu người học (-4%)
    """
    if not text or not text.strip():
        return Response(status_code=400, content="Text cannot be empty")

    voice = resolve_voice(lang)
    try:
        communicate = edge_tts.Communicate(text.strip(), voice, rate="-4%")
        audio_data = bytearray()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
                
        complete_audio = bytes(audio_data)
        
        return Response(
            content=complete_audio,
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "public, max-age=604800",
                "X-TTS-Voice": voice
            }
        )
    except Exception as e:
        logger.error(f"Flashcard TTS generation failed: {e}")
        return Response(status_code=500, content=f"TTS generation failed: {e}")


@router.post("/decks", response_model=ApiResult)
async def create_deck_endpoint(
    payload: CreateDeckRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Tạo bộ thẻ mới cho người dùng đã đăng nhập."""
    data = await create_deck(payload.title, payload.description, user_id, lang_code=payload.lang_code or "en")
    return ApiResult(ok=True, data=data)

@router.get("/decks", response_model=ApiResult)
async def get_decks_endpoint(
    user_id: str = Depends(get_current_user_id)
):
    """Lấy danh sách các bộ thẻ của người dùng hiện tại."""
    data = await get_decks(user_id)
    return ApiResult(ok=True, data=data)

@router.put("/decks/{deck_id}", response_model=ApiResult)
async def update_deck_endpoint(
    deck_id: str,
    payload: UpdateDeckRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Cập nhật thông tin bộ thẻ (tiêu đề, mô tả, ngôn ngữ)."""
    data = await update_deck(
        deck_id=deck_id,
        user_id=user_id,
        title=payload.title,
        description=payload.description,
        lang_code=payload.lang_code
    )
    return ApiResult(ok=True, data=data)

@router.delete("/decks/{deck_id}", response_model=ApiResult)
async def delete_deck_endpoint(
    deck_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Xóa bộ thẻ cùng toàn bộ thẻ bên trong."""
    success = await delete_deck(deck_id=deck_id, user_id=user_id)
    return ApiResult(ok=True, data={"deleted": success})

@router.get("/decks/{deck_id}/cards", response_model=ApiResult)
async def get_deck_cards_endpoint(
    deck_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Lấy danh sách thẻ trong bộ thẻ với kiểm tra quyền sở hữu."""
    data = await get_deck_cards(deck_id, user_id)
    return ApiResult(ok=True, data=data)

@router.get("/decks/{deck_id}/study-queue", response_model=ApiResult)
async def get_study_queue_endpoint(
    deck_id: str,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id)
):
    """
    Lấy hàng đợi thẻ ôn tập thông minh (Smart Study Queue):
    - Tự động quyết định chế độ ôn tập (Lật thẻ hoặc Gõ chính tả)
    - Tự sinh câu đục lỗ Cloze từ câu ví dụ nếu có.
    """
    data = await get_study_queue(deck_id=deck_id, user_id=user_id, limit=limit)
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
        example_sentence=payload.example_sentence,
        part_of_speech=payload.part_of_speech,
        lang_code=payload.lang_code or "en"
    )
    
    # Luôn kích hoạt sự kiện để worker đảm bảo file âm thanh đã được tạo và lưu trữ trên MinIO
    card_id = data.get("id")
    if card_id:
        try:
            await publish_flashcard_created_event(
                card_id=card_id,
                term=payload.front_text,
                lang_code=payload.lang_code or "en",
                user_id=user_id
            )
        except Exception as e:
            logger.warning(f"Could not publish flashcard.created event: {e}")
            
    return ApiResult(ok=True, data=data)

@router.post("/cards/{card_id}/verify-spelling", response_model=ApiResult)
async def verify_spelling_endpoint(
    card_id: str,
    payload: VerifySpellingRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Xác minh gõ chính tả (Spelling Challenge) và tự động tính độ tương đồng Levenshtein:
    - Trả về độ chính xác, từ gốc, gợi ý và Suggested FSRS Grade.
    - Có thể tự động cập nhật nhật ký ôn tập nếu auto_apply_review = True.
    """
    result = await verify_spelling(
        card_id=card_id,
        user_input=payload.user_input,
        user_id=user_id,
        auto_apply_review=payload.auto_apply_review or False
    )
    return ApiResult(ok=True, data=result)

@router.post("/review", response_model=ApiResult)
async def review_card_endpoint(
    payload: ReviewCardRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Ôn tập thẻ với thuật toán FSRS và bảo vệ IDOR (chỉ chủ sở hữu mới được cập nhật thẻ)."""
    updated_card = await review_card(card_id=payload.card_id, grade=payload.grade, user_id=user_id)
    return ApiResult(ok=True, data=updated_card)

@router.put("/cards/{card_id}", response_model=ApiResult)
async def update_card_endpoint(
    card_id: str,
    payload: UpdateCardRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Cập nhật thông tin thẻ từ vựng."""
    data = await update_card(
        card_id=card_id,
        user_id=user_id,
        front_text=payload.front_text,
        back_text=payload.back_text,
        phonetic=payload.phonetic,
        example_sentence=payload.example_sentence,
        part_of_speech=payload.part_of_speech,
        lang_code=payload.lang_code
    )
    return ApiResult(ok=True, data=data)

@router.delete("/cards/{card_id}", response_model=ApiResult)
async def delete_card_endpoint(
    card_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Xóa thẻ với kiểm tra quyền sở hữu."""
    success = await delete_card(card_id, user_id)
    return ApiResult(ok=True, data={"deleted": success})
