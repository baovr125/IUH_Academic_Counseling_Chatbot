import os
import uuid
import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from app.services.sm2_algorithm import calculate_sm2
from app.utils.logger import logger

# In-memory deck & card store fallback
in_memory_decks: Dict[str, Dict[str, Any]] = {}
in_memory_cards: Dict[str, Dict[str, Any]] = {}

def get_supabase() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

def create_deck(title: str, description: Optional[str], user_id: str) -> Dict[str, Any]:
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
            supabase.table("decks").insert(deck_data).execute()
        except Exception as e:
            logger.warning(f"Failed to insert deck into Supabase: {e}")
            
    in_memory_decks[deck_id] = deck_data
    return deck_data

def create_card(deck_id: str, front_text: str, back_text: str, phonetic: Optional[str] = None, example_sentence: Optional[str] = None) -> Dict[str, Any]:
    card_id = str(uuid.uuid4())
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    card_data = {
        "id": card_id,
        "deck_id": deck_id,
        "front_text": front_text,
        "back_text": back_text,
        "phonetic": phonetic,
        "example_sentence": example_sentence,
        "repetition": 0,
        "ease_factor": 2.5,
        "interval_days": 1,
        "next_review_date": now_iso
    }
    supabase = get_supabase()
    if supabase:
        try:
            supabase.table("cards").insert(card_data).execute()
        except Exception as e:
            logger.warning(f"Failed to insert card into Supabase: {e}")
            
    in_memory_cards[card_id] = card_data
    return card_data

def review_card(card_id: str, grade: int) -> Dict[str, Any]:
    card = in_memory_cards.get(card_id)
    if not card:
        card = {
            "id": card_id,
            "deck_id": "deck-default",
            "front_text": "Sample",
            "back_text": "Mẫu",
            "repetition": 0,
            "ease_factor": 2.5,
            "interval_days": 1,
            "next_review_date": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
    sm2_results = calculate_sm2(
        grade=grade,
        repetition=card.get("repetition", 0),
        ease_factor=card.get("ease_factor", 2.5),
        interval_days=card.get("interval_days", 1)
    )
    
    card.update(sm2_results)
    in_memory_cards[card_id] = card
    
    supabase = get_supabase()
    if supabase:
        try:
            supabase.table("cards").update(sm2_results).eq("id", card_id).execute()
            supabase.table("review_logs").insert({
                "card_id": card_id,
                "grade": grade,
                "reviewed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to update card review log in Supabase: {e}")
            
    return card
