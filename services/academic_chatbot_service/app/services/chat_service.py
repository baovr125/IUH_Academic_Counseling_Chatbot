import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.utils.logger import logger
from app.services.supabase_client import get_supabase_client

session_memory: Dict[str, List[dict]] = {}

def ensure_uuid(session_id: Optional[str]) -> str:
    if not session_id:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(session_id))
    except (ValueError, TypeError, AttributeError):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(session_id)))

def get_session_history_from_db(session_id: str) -> list:
    clean_id = ensure_uuid(session_id)
    try:
        supabase = get_supabase_client()
        if supabase:
            res = supabase.table("messages").select("*").eq("conversation_id", clean_id).order("created_at").execute()
            if res.data:
                return [{"role": m["role"], "content": m["content"]} for m in res.data]
    except Exception as e:
        logger.exception(f"Failed to load session history for {clean_id}: {e}")
    return session_memory.get(clean_id, [])

def save_user_msg_to_db(session_id: str, user_content: str, title: str, user_id: Optional[str] = None) -> str:
    clean_id = ensure_uuid(session_id)
    supabase = get_supabase_client()
    if supabase:
        try:
            existing_res = supabase.table("conversations").select("id, title").eq("id", clean_id).execute()
            if existing_res.data and len(existing_res.data) > 0:
                update_payload = {"updated_at": datetime.now(timezone.utc).isoformat()}
                if user_id:
                    update_payload["user_id"] = user_id
                supabase.table("conversations").update(update_payload).eq("id", clean_id).execute()
            else:
                conv_payload = {
                    "id": clean_id,
                    "title": title[:50] or "Cuộc trò chuyện mới",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                if user_id:
                    conv_payload["user_id"] = user_id
                supabase.table("conversations").insert(conv_payload).execute()
        except Exception as e:
            logger.exception(f"Failed to upsert conversation {clean_id}: {e}")

        try:
            supabase.table("messages").insert({
                "conversation_id": clean_id,
                "role": "user",
                "content": user_content
            }).execute()
        except Exception as e:
            logger.exception(f"Failed to insert user message for {clean_id}: {e}")

    if clean_id not in session_memory:
        session_memory[clean_id] = []
    session_memory[clean_id].append({"role": "user", "content": user_content})
    return clean_id

def save_assistant_msg_to_db(session_id: str, assistant_content: str, retrieved_chunk_ids: list = None, latency_ms: int = None, prompt_tokens: int = None, completion_tokens: int = None):
    clean_id = ensure_uuid(session_id)
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.table("conversations").update({
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", clean_id).execute()
        except Exception as e:
            logger.exception(f"Failed to update conversation timestamp for {clean_id}: {e}")

        try:
            msg_payload = {
                "conversation_id": clean_id,
                "role": "assistant",
                "content": assistant_content,
                "retrieved_chunk_ids": retrieved_chunk_ids or []
            }
            if latency_ms is not None: msg_payload["latency_ms"] = latency_ms
            if prompt_tokens is not None: msg_payload["prompt_tokens"] = prompt_tokens
            if completion_tokens is not None: msg_payload["completion_tokens"] = completion_tokens
            
            supabase.table("messages").insert(msg_payload).execute()
        except Exception as e:
            logger.exception(f"Failed to insert assistant message for {clean_id}: {e}")

    if clean_id not in session_memory:
        session_memory[clean_id] = []
    session_memory[clean_id].append({"role": "assistant", "content": assistant_content})

def save_turn_to_db(session_id: str, user_content: str, assistant_content: str, title: str, retrieved_chunk_ids: list = None, user_id: Optional[str] = None, latency_ms: int = None, prompt_tokens: int = None, completion_tokens: int = None):
    clean_id = save_user_msg_to_db(session_id, user_content, title, user_id=user_id)
    save_assistant_msg_to_db(clean_id, assistant_content, retrieved_chunk_ids, latency_ms, prompt_tokens, completion_tokens)
