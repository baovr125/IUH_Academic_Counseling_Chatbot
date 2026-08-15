import os
import uuid
import datetime
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from supabase import create_client, Client
from app.services.fsrs_algorithm import calculate_fsrs
from app.utils.logger import logger
from starlette.concurrency import run_in_threadpool

# In-memory deck & card store fallback
in_memory_decks: Dict[str, Dict[str, Any]] = {}
in_memory_cards: Dict[str, Dict[str, Any]] = {}

def get_supabase() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

async def create_deck(title: str, description: Optional[str], user_id: str) -> Dict[str, Any]:
    deck_id = str(uuid.uuid4())
    deck_data = {
        "id": deck_id,
        "user_id": user_id,
        "title": title,
        "description": description,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    supabase = get_supabase()
    if supabase:
        try:
            await run_in_threadpool(lambda: supabase.table("flashcard_decks").insert(deck_data).execute())
        except Exception as e:
            logger.warning(f"Failed to insert deck into Supabase: {e}")
            
    in_memory_decks[deck_id] = deck_data
    return deck_data

async def get_decks(user_id: str) -> List[Dict[str, Any]]:
    """Lấy danh sách các bộ thẻ của người dùng hiện tại (IDOR Protection)."""
    supabase = get_supabase()
    if supabase:
        try:
            res = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("*").eq("user_id", user_id).execute()
            )
            if res.data is not None:
                return res.data
        except Exception as e:
            logger.warning(f"Failed to fetch decks from Supabase: {e}")
            
    return [d for d in in_memory_decks.values() if d.get("user_id") == user_id]

async def create_card(
    deck_id: str,
    front_text: str,
    back_text: str,
    user_id: str,
    phonetic: Optional[str] = None,
    audio_url: Optional[str] = None,
    example_sentence: Optional[str] = None
) -> Dict[str, Any]:
    """Tạo thẻ mới với IDOR Protection (xác thực quyền sở hữu Deck)."""
    supabase = get_supabase()
    if supabase:
        try:
            # Kiểm tra xem deck có tồn tại và thuộc quyền sở hữu của user_id không
            deck_res = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("id, user_id").eq("id", deck_id).execute()
            )
            if deck_res.data and len(deck_res.data) > 0:
                owner_id = str(deck_res.data[0].get("user_id", ""))
                if owner_id and owner_id != "anonymous" and owner_id != str(user_id):
                    logger.warning(f"IDOR Alert: User {user_id} attempted to add card to deck {deck_id} owned by {owner_id}")
                    raise HTTPException(
                        status_code=403,
                        detail="Bạn không có quyền thêm thẻ vào bộ thẻ của người khác (IDOR Protection)."
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error checking deck ownership in Supabase: {e}")
    else:
        deck = in_memory_decks.get(deck_id)
        if deck and deck.get("user_id") and deck.get("user_id") != "anonymous" and deck.get("user_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền thêm thẻ vào bộ thẻ của người khác."
            )

    card_id = str(uuid.uuid4())
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    card_data = {
        "id": card_id,
        "deck_id": deck_id,
        "user_id": user_id,
        "term": front_text,
        "definition": back_text,
        "phonetic": phonetic,
        "audio_url": audio_url,
        "example": example_sentence,
        # Standard FSRS Fields
        "state": 0, # 0: New
        "reps": 0,
        "repetition": 0,
        "lapses": 0,
        "stability": 0.0,
        "difficulty": 0.0,
        "elapsed_days": 0,
        "scheduled_days": 0,
        "last_review": None,
        "due": now_iso,
        "next_review_date": now_iso # Legacy alias
    }
    
    if supabase:
        try:
            await run_in_threadpool(lambda: supabase.table("flashcards").insert(card_data).execute())
        except Exception as e:
            logger.warning(f"Failed to insert card into Supabase: {e}")
            
    in_memory_cards[card_id] = card_data
    return card_data

async def update_card_audio_url(card_id: str, audio_url: str) -> bool:
    """Cập nhật đường dẫn âm thanh phát âm (MinIO) vào thẻ Flashcard."""
    if card_id in in_memory_cards:
        in_memory_cards[card_id]["audio_url"] = audio_url
        
    supabase = get_supabase()
    if supabase:
        try:
            await run_in_threadpool(
                lambda: supabase.table("flashcards").update({"audio_url": audio_url}).eq("id", card_id).execute()
            )
            logger.info(f"Updated audio_url for card {card_id} in Supabase.")
            return True
        except Exception as e:
            logger.warning(f"Failed to update audio_url for card {card_id} in Supabase: {e}")
            return False
    return True

async def review_card(card_id: str, grade: int, user_id: str) -> Dict[str, Any]:
    """
    Ôn tập thẻ với thuật toán FSRS và kiểm tra bảo mật quyền sở hữu (IDOR Protection).
    """
    supabase = get_supabase()
    card = None
    
    if supabase:
        try:
            res = await run_in_threadpool(
                lambda: supabase.table("flashcards").select("*").eq("id", card_id).execute()
            )
            if res.data and len(res.data) > 0:
                card = res.data[0]
                card_user_id = str(card.get("user_id", ""))
                
                # Kiểm tra quyền sở hữu trực tiếp của thẻ
                if card_user_id and card_user_id != "anonymous" and card_user_id != str(user_id):
                    # Kiểm tra thêm qua deck_id
                    deck_res = await run_in_threadpool(
                        lambda: supabase.table("flashcard_decks").select("user_id").eq("id", card.get("deck_id")).execute()
                    )
                    deck_owner = str(deck_res.data[0].get("user_id", "")) if deck_res.data else ""
                    if deck_owner and deck_owner != "anonymous" and deck_owner != str(user_id):
                        logger.warning(f"IDOR Violation: User {user_id} attempted to review card {card_id} owned by {card_user_id}")
                        raise HTTPException(
                            status_code=403,
                            detail="Bạn không có quyền ôn tập hoặc thao tác trên thẻ Flashcard này (IDOR Protection)."
                        )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error checking card ownership in Supabase: {e}")
            
    if not card:
        card = in_memory_cards.get(card_id)
        if card:
            card_user = card.get("user_id")
            if card_user and card_user != "anonymous" and card_user != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Bạn không có quyền ôn tập thẻ này."
                )
        else:
            card = {
                "id": card_id,
                "deck_id": "deck-default",
                "user_id": user_id,
                "term": "Sample",
                "definition": "Mẫu",
                "state": 0,
                "reps": 0,
                "repetition": 0,
                "lapses": 0,
                "stability": 0.0,
                "difficulty": 0.0,
                "elapsed_days": 0,
                "scheduled_days": 0,
                "due": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        
    fsrs_results = calculate_fsrs(
        grade=grade,
        card_dict=card
    )
    
    card.update(fsrs_results)
    in_memory_cards[card_id] = card
    
    if supabase:
        try:
            review_log_data = {
                "card_id": card_id,
                "user_id": user_id,
                "grade": grade,
                "rating": grade,
                "state": fsrs_results.get("state", 0),
                "stability": fsrs_results.get("stability", 0.0),
                "difficulty": fsrs_results.get("difficulty", 0.0),
                "elapsed_days": fsrs_results.get("elapsed_days", 0),
                "scheduled_days": fsrs_results.get("scheduled_days", 0),
                "reviewed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            await run_in_threadpool(lambda: [
                supabase.table("flashcards").update(fsrs_results).eq("id", card_id).execute(),
                supabase.table("review_logs").insert(review_log_data).execute()
            ])
        except Exception as e:
            logger.warning(f"Failed to update card review log in Supabase: {e}")
            
    return card

async def get_deck_cards(deck_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Lấy danh sách thẻ trong bộ thẻ với kiểm tra quyền sở hữu (IDOR Protection)."""
    supabase = get_supabase()
    if supabase:
        try:
            deck_res = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("user_id").eq("id", deck_id).execute()
            )
            if deck_res.data and len(deck_res.data) > 0:
                owner = str(deck_res.data[0].get("user_id", ""))
                if owner and owner != "anonymous" and owner != str(user_id):
                    raise HTTPException(
                        status_code=403,
                        detail="Bạn không có quyền truy cập bộ thẻ này."
                    )
                    
            res = await run_in_threadpool(
                lambda: supabase.table("flashcards").select("*").eq("deck_id", deck_id).execute()
            )
            if res.data is not None:
                return res.data
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Failed to fetch cards from Supabase: {e}")
            
    return [c for c in in_memory_cards.values() if c.get("deck_id") == deck_id]

async def delete_card(card_id: str, user_id: str) -> bool:
    """Xóa thẻ với IDOR Protection."""
    supabase = get_supabase()
    if supabase:
        try:
            res = await run_in_threadpool(
                lambda: supabase.table("flashcards").select("user_id, deck_id").eq("id", card_id).execute()
            )
            if res.data and len(res.data) > 0:
                owner = str(res.data[0].get("user_id", ""))
                if owner and owner != "anonymous" and owner != str(user_id):
                    raise HTTPException(status_code=403, detail="Bạn không có quyền xóa thẻ này.")
                    
            await run_in_threadpool(
                lambda: supabase.table("flashcards").delete().eq("id", card_id).execute()
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Failed to delete card in Supabase: {e}")
            
    if card_id in in_memory_cards:
        if in_memory_cards[card_id].get("user_id") == user_id:
            del in_memory_cards[card_id]
    return True
