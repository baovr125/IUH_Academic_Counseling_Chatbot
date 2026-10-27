import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.utils.logger import logger
from app.services.supabase_client import execute_with_retry, get_supabase_client

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
        res = execute_with_retry(
            lambda sp: sp.table("messages").select("*").eq("conversation_id", clean_id).order("created_at").execute()
        )
        if res and res.data:
            return [{"role": m["role"], "content": m["content"]} for m in res.data]
    except Exception as e:
        logger.exception(f"Failed to load session history for {clean_id}: {e}")
    return session_memory.get(clean_id, [])

def save_user_msg_to_db(session_id: str, user_content: str, title: str, user_id: Optional[str] = None) -> tuple[str, str]:
    clean_id = ensure_uuid(session_id)
    msg_id = str(uuid.uuid4())

    try:
        existing_res = execute_with_retry(
            lambda sp: sp.table("conversations").select("id, title").eq("id", clean_id).execute()
        )
        if existing_res and existing_res.data and len(existing_res.data) > 0:
            update_payload = {"updated_at": datetime.now(timezone.utc).isoformat()}
            if user_id and user_id != "anonymous":
                update_payload["user_id"] = user_id
            execute_with_retry(
                lambda sp: sp.table("conversations").update(update_payload).eq("id", clean_id).execute()
            )
        else:
            conv_payload = {
                "id": clean_id,
                "title": title[:50] or "Cuộc trò chuyện mới",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            if user_id and user_id != "anonymous":
                conv_payload["user_id"] = user_id

            try:
                execute_with_retry(
                    lambda sp: sp.table("conversations").insert(conv_payload).execute()
                )
            except Exception as insert_e:
                logger.warning(f"Failed to insert conversation with user_id, trying without user_id: {insert_e}")
                if "user_id" in conv_payload:
                    del conv_payload["user_id"]
                    execute_with_retry(
                        lambda sp: sp.table("conversations").insert(conv_payload).execute()
                    )
    except Exception as e:
        logger.exception(f"Failed to upsert conversation {clean_id}: {e}")

    try:
        execute_with_retry(
            lambda sp: sp.table("messages").insert({
                "id": msg_id,
                "conversation_id": clean_id,
                "role": "user",
                "content": user_content
            }).execute()
        )
    except Exception as e:
        logger.exception(f"Failed to insert user message for {clean_id}: {e}")

    if clean_id not in session_memory:
        session_memory[clean_id] = []
    session_memory[clean_id].append({"role": "user", "content": user_content})
    return clean_id, msg_id

def save_assistant_msg_to_db(session_id: str, assistant_content: str, retrieved_chunk_ids: list = None, latency_ms: int = None, prompt_tokens: int = None, completion_tokens: int = None):
    clean_id = ensure_uuid(session_id)

    try:
        execute_with_retry(
            lambda sp: sp.table("conversations").update({
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", clean_id).execute()
        )
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

        execute_with_retry(
            lambda sp: sp.table("messages").insert(msg_payload).execute()
        )
    except Exception as e:
        logger.exception(f"Failed to insert assistant message for {clean_id}: {e}")

    if clean_id not in session_memory:
        session_memory[clean_id] = []
    session_memory[clean_id].append({"role": "assistant", "content": assistant_content})

def save_turn_to_db(session_id: str, user_content: str, assistant_content: str, title: str, retrieved_chunk_ids: list = None, user_id: Optional[str] = None, latency_ms: int = None, prompt_tokens: int = None, completion_tokens: int = None):
    clean_id, _ = save_user_msg_to_db(session_id, user_content, title, user_id=user_id)
    save_assistant_msg_to_db(clean_id, assistant_content, retrieved_chunk_ids, latency_ms, prompt_tokens, completion_tokens)

def update_message_embedding_in_db(message_id: str, embedding: list):
    if not embedding:
        return
    try:
        execute_with_retry(
            lambda sp: sp.table("messages").update({"embedding": embedding}).eq("id", message_id).execute()
        )
    except Exception as e:
        logger.exception(f"Failed to update embedding for message {message_id}: {e}")

def delete_last_turn_from_db(session_id: str, message_ids: Optional[List[str]] = None) -> None:
    """
    When regenerating with bypassCache, delete the previous HIT-cache turn
    (assistant message and corresponding user question) from DB and in-memory cache
    so user doesn't see duplicate questions or outdated cache information.
    """
    clean_id = ensure_uuid(session_id)
    
    # 1. If explicit UUIDs were provided, attempt to delete by ID
    if message_ids:
        valid_uuids = []
        for mid in message_ids:
            try:
                uuid.UUID(str(mid))
                valid_uuids.append(str(mid))
            except (ValueError, TypeError, AttributeError):
                pass
        if valid_uuids:
            try:
                execute_with_retry(
                    lambda sp: sp.table("messages").delete().in_("id", valid_uuids).execute()
                )
            except Exception as e:
                logger.warning(f"Could not delete specific message IDs {valid_uuids} for {clean_id}: {e}")

    # 2. Always ensure the latest 2 messages in this conversation are cleaned if they correspond to the turn
    try:
        sp_res = execute_with_retry(
            lambda sp: sp.table("messages")
                .select("id, role, created_at")
                .eq("conversation_id", clean_id)
                .order("created_at", desc=True)
                .limit(2)
                .execute()
        )
        if sp_res and sp_res.data:
            to_delete = [m["id"] for m in sp_res.data]
            if to_delete:
                execute_with_retry(
                    lambda sp: sp.table("messages").delete().in_("id", to_delete).execute()
                )
    except Exception as e:
        logger.warning(f"Failed to delete last turn for session {clean_id}: {e}")

    # 3. Clean in-memory session cache
    if clean_id in session_memory and len(session_memory[clean_id]) >= 2:
        session_memory[clean_id] = session_memory[clean_id][:-2]
