import os
import uuid
import datetime
import random
import re
import difflib
import hashlib
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from supabase import create_client, Client
from app.services.fsrs_algorithm import calculate_fsrs
from app.utils.logger import logger
from starlette.concurrency import run_in_threadpool

# In-memory deck & card store fallback
in_memory_decks: Dict[str, Dict[str, Any]] = {}
in_memory_cards: Dict[str, Dict[str, Any]] = {}

def to_valid_uuid(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    try:
        uuid.UUID(str(val))
        return str(val)
    except ValueError:
        return None

def get_supabase() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

async def create_deck(title: str, description: Optional[str], user_id: str, lang_code: str = "en") -> Dict[str, Any]:
    deck_id = str(uuid.uuid4())
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    deck_data = {
        "id": deck_id,
        "user_id": user_id,
        "title": title,
        "description": description or "",
        "lang_code": lang_code,
        "icon_flag": "🌐",
        "cards_count": 0,
        "created_at": now_iso
    }
    in_memory_decks[deck_id] = deck_data

    supabase = get_supabase()
    if supabase:
        try:
            valid_user_id = to_valid_uuid(user_id)
            sb_payload = {
                "id": deck_id,
                "title": title,
                "description": description or "",
                "lang_code": lang_code,
                "icon_flag": "🌐"
            }
            if valid_user_id:
                sb_payload["user_id"] = valid_user_id
            await run_in_threadpool(lambda: supabase.table("flashcard_decks").insert(sb_payload).execute())
        except Exception as e:
            logger.warning(f"Failed to insert deck into Supabase: {e}")
            
    return deck_data

async def get_decks(user_id: str) -> List[Dict[str, Any]]:
    """Lấy danh sách các bộ thẻ của người dùng hiện tại."""
    decks_map: Dict[str, Dict[str, Any]] = {}
    
    # 1. In-memory: Chỉ lấy bộ thẻ thuộc quyền sở hữu của user_id
    for d in in_memory_decks.values():
        if str(d.get("user_id", "")) == str(user_id):
            d_copy = dict(d)
            d_copy["cards_count"] = len([c for c in in_memory_cards.values() if str(c.get("deck_id")) == str(d.get("id"))])
            decks_map[d["id"]] = d_copy

    # 2. Supabase: Lọc chính xác theo user_id
    supabase = get_supabase()
    if supabase:
        try:
            valid_user_id = to_valid_uuid(user_id)
            if valid_user_id:
                res = await run_in_threadpool(
                    lambda: supabase.table("flashcard_decks")
                        .select("*")
                        .eq("user_id", valid_user_id)
                        .order("created_at", desc=True)
                        .execute()
                )
                if res.data:
                    for d in res.data:
                        did = str(d.get("id"))
                        if did not in decks_map:
                            try:
                                cards_res = await run_in_threadpool(
                                    lambda: supabase.table("flashcards").select("id", count="exact").eq("deck_id", did).execute()
                                )
                                d["cards_count"] = cards_res.count if cards_res.count is not None else 0
                            except Exception:
                                d["cards_count"] = 0
                            decks_map[did] = d
                        else:
                            decks_map[did]["title"] = d.get("title", decks_map[did]["title"])
        except Exception as e:
            logger.warning(f"Failed to fetch decks from Supabase: {e}")
            
    return list(decks_map.values())

async def update_deck(
    deck_id: str,
    user_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    lang_code: Optional[str] = None
) -> Dict[str, Any]:
    """Cập nhật thông tin bộ thẻ với IDOR Protection."""
    supabase = get_supabase()
    if supabase:
        try:
            deck_res = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("*").eq("id", deck_id).execute()
            )
            if not deck_res.data or len(deck_res.data) == 0:
                raise HTTPException(status_code=404, detail="Không tìm thấy bộ thẻ.")
            owner = str(deck_res.data[0].get("user_id", ""))
            if owner and owner != "anonymous" and owner != str(user_id):
                raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa bộ thẻ này.")
            
            update_data = {}
            if title is not None:
                update_data["title"] = title
            if description is not None:
                update_data["description"] = description
            if lang_code is not None:
                update_data["lang_code"] = lang_code
                
            if update_data:
                await run_in_threadpool(
                    lambda: supabase.table("flashcard_decks").update(update_data).eq("id", deck_id).execute()
                )
                
            updated = {**deck_res.data[0], **update_data}
            in_memory_decks[deck_id] = updated
            return updated
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error updating deck in Supabase: {e}")
            
    deck = in_memory_decks.get(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ thẻ.")
    if deck.get("user_id") and deck.get("user_id") != "anonymous" and deck.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa bộ thẻ này.")
    if title is not None:
        deck["title"] = title
    if description is not None:
        deck["description"] = description
    if lang_code is not None:
        deck["lang_code"] = lang_code
    return deck

async def delete_deck(deck_id: str, user_id: str) -> bool:
    """Xóa bộ thẻ cùng tất cả các thẻ bên trong với IDOR Protection."""
    supabase = get_supabase()
    if supabase:
        try:
            deck_res = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("user_id").eq("id", deck_id).execute()
            )
            if not deck_res.data or len(deck_res.data) == 0:
                raise HTTPException(status_code=404, detail="Không tìm thấy bộ thẻ.")
            owner = str(deck_res.data[0].get("user_id", ""))
            if owner and owner != "anonymous" and owner != str(user_id):
                raise HTTPException(status_code=403, detail="Bạn không có quyền xóa bộ thẻ này.")
                
            # Xóa tất cả các thẻ trong bộ thẻ trước
            await run_in_threadpool(
                lambda: supabase.table("flashcards").delete().eq("deck_id", deck_id).execute()
            )
            # Xóa bộ thẻ
            await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").delete().eq("id", deck_id).execute()
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error deleting deck in Supabase: {e}")

    # Xóa trong in-memory
    if deck_id in in_memory_decks:
        if in_memory_decks[deck_id].get("user_id") in [user_id, "anonymous"]:
            del in_memory_decks[deck_id]
            
    # Xóa các thẻ thuộc deck trong in-memory
    card_ids_to_del = [cid for cid, c in in_memory_cards.items() if c.get("deck_id") == deck_id]
    for cid in card_ids_to_del:
        del in_memory_cards[cid]
        
    return True

async def create_card(
    deck_id: str,
    front_text: str,
    back_text: str,
    user_id: str,
    phonetic: Optional[str] = None,
    audio_url: Optional[str] = None,
    example_sentence: Optional[str] = None,
    part_of_speech: Optional[str] = None,
    lang_code: str = "en"
) -> Dict[str, Any]:
    """Tạo thẻ mới với IDOR Protection (xác thực quyền sở hữu Deck) và tự động gắn Persistent Audio URL."""
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
    
    # Content-Addressable Storage (CAS) Deduplicated Persistent Audio URL
    if not audio_url and front_text:
        clean_lang = (lang_code or "en").strip().lower()[:2]
        clean_term = front_text.strip().lower()
        term_hash = hashlib.md5(f"{clean_lang}_{clean_term}".encode('utf-8')).hexdigest()
        audio_url = f"/api/v1/translate/audio/terms/{clean_lang}_{term_hash}.mp3"
        
    card_data = {
        "id": card_id,
        "deck_id": deck_id,
        "user_id": user_id,
        "term": front_text,
        "definition": back_text,
        "phonetic": phonetic,
        "audio_url": audio_url,
        "example": example_sentence,
        "example_sentence": example_sentence,
        "part_of_speech": part_of_speech or "phrase",
        "lang_code": lang_code,
        # Standard FSRS Fields
        "state": 0, # 0: New
        "reps": 0,
        "lapses": 0,
        "stability": 0.0,
        "difficulty": 0.0,
        "elapsed_days": 0,
        "scheduled_days": 0,
        "last_review": None,
        "due": now_iso
    }
    
    in_memory_cards[card_id] = card_data
    if deck_id in in_memory_decks:
        in_memory_decks[deck_id]["cards_count"] = len([c for c in in_memory_cards.values() if str(c.get("deck_id")) == str(deck_id)])

    if supabase:
        try:
            valid_deck_id = to_valid_uuid(deck_id)
            valid_user_id = to_valid_uuid(user_id)
            sb_card_payload = {
                "id": card_id,
                "term": front_text,
                "definition": back_text,
                "phonetic": phonetic,
                "audio_url": audio_url,
                "example": example_sentence,
                "part_of_speech": part_of_speech or "phrase",
                "lang_code": lang_code,
                "state": 0,
                "reps": 0,
                "lapses": 0,
                "stability": 0.0,
                "difficulty": 0.0,
                "elapsed_days": 0,
                "scheduled_days": 0,
                "due": now_iso
            }
            if valid_deck_id:
                sb_card_payload["deck_id"] = valid_deck_id
            if valid_user_id:
                sb_card_payload["user_id"] = valid_user_id
            await run_in_threadpool(lambda: supabase.table("flashcards").insert(sb_card_payload).execute())
        except Exception as e:
            logger.warning(f"Failed to insert card into Supabase: {e}")
            
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

async def get_card_by_id(card_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Lấy thông tin thẻ kèm kiểm tra IDOR."""
    supabase = get_supabase()
    if supabase:
        try:
            res = await run_in_threadpool(
                lambda: supabase.table("flashcards").select("*").eq("id", card_id).execute()
            )
            if res.data and len(res.data) > 0:
                card = res.data[0]
                card_user_id = str(card.get("user_id", ""))
                if card_user_id and card_user_id != "anonymous" and card_user_id != str(user_id):
                    raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập thẻ này.")
                return card
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Failed to fetch card from Supabase: {e}")
    
    card = in_memory_cards.get(card_id)
    if card and card.get("user_id") and card.get("user_id") != "anonymous" and card.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập thẻ này.")
    return card

async def review_card(card_id: str, grade: int, user_id: str) -> Dict[str, Any]:
    """
    Ôn tập thẻ với thuật toán FSRS và kiểm tra bảo mật quyền sở hữu (IDOR Protection).
    grade: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
    """
    card = await get_card_by_id(card_id, user_id)
    if not card:
        card = {
            "id": card_id,
            "deck_id": "deck-default",
            "user_id": user_id,
            "term": "Sample",
            "definition": "Mẫu",
            "state": 0,
            "reps": 0,
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
    
    supabase = get_supabase()
    if supabase:
        try:
            valid_uid = to_valid_uuid(user_id)
            review_log_data = {
                "card_id": card_id,
                "grade": grade,
                "state": fsrs_results.get("state", 0),
                "stability": fsrs_results.get("stability", 0.0),
                "difficulty": fsrs_results.get("difficulty", 0.0),
                "elapsed_days": fsrs_results.get("elapsed_days", 0),
                "scheduled_days": fsrs_results.get("scheduled_days", 0),
                "reviewed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            if valid_uid:
                review_log_data["user_id"] = valid_uid

            await run_in_threadpool(lambda: [
                supabase.table("flashcards").update(fsrs_results).eq("id", card_id).execute(),
                supabase.table("review_logs").insert(review_log_data).execute()
            ])
        except Exception as e:
            logger.warning(f"Failed to update card review log in Supabase: {e}")
            
    return card

async def verify_spelling(card_id: str, user_input: str, user_id: str, auto_apply_review: bool = False) -> Dict[str, Any]:
    """
    Xác minh gõ chính tả (Active Recall Spelling Challenge):
    - So khớp từ gốc và chuỗi người dùng nhập (chuẩn hóa chữ thường, xóa khoảng trắng thừa).
    - Tính điểm tương đồng bằng Levenshtein/SequenceMatcher.
    - Đưa ra phản hồi gợi ý thông minh và gợi ý Grade FSRS tương ứng.
    """
    card = await get_card_by_id(card_id, user_id)
    if not card:
        card = {"id": card_id, "term": str(user_input).strip(), "definition": ""}

    correct_term = str(card.get("term", "")).strip()
    normalized_target = correct_term.lower()
    normalized_input = str(user_input).strip().lower()

    # Tính độ tương đồng
    matcher = difflib.SequenceMatcher(None, normalized_input, normalized_target)
    similarity = matcher.ratio()

    is_correct = (normalized_input == normalized_target)
    is_close = False
    feedback = ""
    suggested_grade = 1

    if is_correct:
        feedback = "Chính xác tuyệt đối! 🎉 Bạn đã ghi nhớ từ này rất xuất sắc."
        suggested_grade = 4  # 4: Easy
    elif similarity >= 0.75:
        is_close = True
        feedback = f"Gần đúng rồi! Lỗi chính tả nhỏ. Bạn gõ '{user_input}', đáp án đúng là '{correct_term}'."
        suggested_grade = 2  # 2: Hard
    else:
        feedback = f"Chưa chính xác. Đáp án đúng là '{correct_term}'. Hãy luyện tập thêm nhé!"
        suggested_grade = 1  # 1: Again

    if auto_apply_review:
        await review_card(card_id=card_id, grade=suggested_grade, user_id=user_id)

    return {
        "is_correct": is_correct,
        "is_close": is_close,
        "similarity_score": round(similarity, 3),
        "correct_term": correct_term,
        "user_input": user_input,
        "feedback": feedback,
        "suggested_grade": suggested_grade,
        "audio_url": card.get("audio_url"),
        "phonetic": card.get("phonetic"),
        "example_sentence": card.get("example"),
        "lang_code": card.get("lang_code") or "en"
    }

async def get_study_queue(deck_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Lấy danh sách thẻ trong bộ để học, kết hợp phân bổ ngẫu nhiên chế độ học:
    - Mode 1: "flip" (Lật thẻ truyền thống ~70%)
    - Mode 2: "spelling" (Thử thách gõ chính tả ~30%, tăng lên 50% nếu từ khó/hay quên)
    - Tự động sinh Cloze prompt từ câu ví dụ nếu có.
    """
    raw_cards = await get_deck_cards(deck_id, user_id)
    deck_info = in_memory_decks.get(deck_id) or {}
    deck_lang = deck_info.get("lang_code") or deck_info.get("langCode") or "en"
    
    study_items = []
    
    for card in raw_cards[:limit]:
        term = card.get("term", "")
        example = card.get("example", "")
        state = card.get("state", 0)
        lapses = card.get("lapses", 0)
        difficulty = card.get("difficulty", 0.0)
        card_lang = card.get("lang_code") or card.get("langCode") or deck_lang
        
        # Quyết định chế độ học thông minh (Smart Mode Selector)
        # Nếu từ hay quên (lapses > 0 hoặc difficulty > 5.0) -> Tăng tỷ lệ gõ chính tả lên 50%
        spelling_chance = 0.5 if (lapses > 0 or difficulty >= 5.0 or state in (1, 3)) else 0.3
        recommended_mode = "spelling" if (random.random() < spelling_chance and len(term.split()) <= 3) else "flip"
        
        # Sinh câu đục lỗ (Cloze Sentence) nếu có câu ví dụ
        cloze_sentence = None
        if example and term:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            cloze_sentence = pattern.sub("________", example)
            
        study_items.append({
            "id": card.get("id"),
            "deck_id": card.get("deck_id"),
            "term": term,
            "definition": card.get("definition", ""),
            "phonetic": card.get("phonetic"),
            "audio_url": card.get("audio_url"),
            "example_sentence": example,
            "part_of_speech": card.get("part_of_speech"),
            "lang_code": card_lang,
            "state": state,
            "stability": card.get("stability", 0.0),
            "difficulty": difficulty,
            "due": card.get("due", datetime.datetime.now(datetime.timezone.utc).isoformat()),
            "recommended_mode": recommended_mode,
            "cloze_sentence": cloze_sentence
        })
        
    return study_items

async def get_deck_cards(deck_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Lấy danh sách thẻ trong bộ thẻ."""
    cards_map: Dict[str, Dict[str, Any]] = {}
    
    # 1. In-memory cards
    for cid, c in in_memory_cards.items():
        if str(c.get("deck_id")) == str(deck_id):
            cards_map[cid] = dict(c)

    # 2. Supabase cards
    supabase = get_supabase()
    if supabase:
        try:
            valid_deck_id = to_valid_uuid(deck_id)
            if valid_deck_id:
                res = await run_in_threadpool(
                    lambda: supabase.table("flashcards")
                        .select("*")
                        .eq("deck_id", valid_deck_id)
                        .order("created_at", desc=False)
                        .execute()
                )
                if res.data:
                    for c in res.data:
                        cid = str(c.get("id"))
                        if cid not in cards_map:
                            cards_map[cid] = {
                                "id": cid,
                                "deck_id": deck_id,
                                "term": c.get("term", ""),
                                "definition": c.get("definition", ""),
                                "phonetic": c.get("phonetic"),
                                "audio_url": c.get("audio_url"),
                                "example_sentence": c.get("example"),
                                "example": c.get("example"),
                                "part_of_speech": c.get("part_of_speech", "phrase"),
                                "lang_code": c.get("lang_code", "en"),
                                "state": c.get("state", 0),
                                "reps": c.get("reps", 0),
                                "lapses": c.get("lapses", 0),
                                "stability": c.get("stability", 0.0),
                                "difficulty": c.get("difficulty", 0.0),
                                "elapsed_days": c.get("elapsed_days", 0),
                                "scheduled_days": c.get("scheduled_days", 0),
                                "last_review": c.get("last_review"),
                                "due": c.get("due") or datetime.datetime.now(datetime.timezone.utc).isoformat()
                            }
        except Exception as e:
            logger.warning(f"Failed to fetch cards from Supabase: {e}")
            
    return list(cards_map.values())

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

async def update_card(
    card_id: str,
    user_id: str,
    front_text: Optional[str] = None,
    back_text: Optional[str] = None,
    phonetic: Optional[str] = None,
    example_sentence: Optional[str] = None,
    part_of_speech: Optional[str] = None,
    lang_code: Optional[str] = None
) -> Dict[str, Any]:
    """Cập nhật thông tin thẻ với IDOR Protection."""
    supabase = get_supabase()
    if supabase:
        try:
            card_res = await run_in_threadpool(
                lambda: supabase.table("flashcards").select("*").eq("id", card_id).execute()
            )
            if not card_res.data or len(card_res.data) == 0:
                raise HTTPException(status_code=404, detail="Không tìm thấy thẻ từ vựng.")
            owner = str(card_res.data[0].get("user_id", ""))
            if owner and owner != "anonymous" and owner != str(user_id):
                raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa thẻ này.")
                
            update_data = {}
            if front_text is not None:
                update_data["term"] = front_text
            if back_text is not None:
                update_data["definition"] = back_text
            if phonetic is not None:
                update_data["phonetic"] = phonetic
            if example_sentence is not None:
                update_data["example"] = example_sentence
            if part_of_speech is not None:
                update_data["part_of_speech"] = part_of_speech
            if lang_code is not None:
                update_data["lang_code"] = lang_code
                
            # Nếu đổi từ hoặc đổi ngôn ngữ, tính lại persistent audio URL
            term = front_text or card_res.data[0].get("term", "")
            target_lang = lang_code or card_res.data[0].get("lang_code", "en")
            if term and (front_text is not None or lang_code is not None):
                clean_lang = target_lang.strip().lower()[:2]
                clean_term = term.strip().lower()
                term_hash = hashlib.md5(f"{clean_lang}_{clean_term}".encode('utf-8')).hexdigest()
                update_data["audio_url"] = f"/api/v1/translate/audio/terms/{clean_lang}_{term_hash}.mp3"
                
            if update_data:
                await run_in_threadpool(
                    lambda: supabase.table("flashcards").update(update_data).eq("id", card_id).execute()
                )
                
            updated = {**card_res.data[0], **update_data}
            in_memory_cards[card_id] = updated
            return updated
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error updating card in Supabase: {e}")
            
    card = in_memory_cards.get(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Không tìm thấy thẻ từ vựng.")
    if card.get("user_id") and card.get("user_id") != "anonymous" and card.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa thẻ này.")
    if front_text is not None:
        card["term"] = front_text
    if back_text is not None:
        card["definition"] = back_text
    if phonetic is not None:
        card["phonetic"] = phonetic
    if example_sentence is not None:
        card["example"] = example_sentence
    if part_of_speech is not None:
        card["part_of_speech"] = part_of_speech
    if lang_code is not None:
        card["lang_code"] = lang_code
    return card
