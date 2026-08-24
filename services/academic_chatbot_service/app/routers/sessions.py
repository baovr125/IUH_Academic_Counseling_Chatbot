import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from app.utils.security import get_optional_current_user_id
from app.schemas.chat import RenameSessionPayload, ApiResult
from app.services.chat_service import ensure_uuid
from app.services.supabase_client import get_supabase_client
from app.utils.logger import logger

router = APIRouter(tags=["Academic Chatbot Service - Sessions"])

@router.get("")
@router.get("/") # To handle both /sessions and /sessions/
async def get_sessions(
    limit: int = 20,
    offset: int = 0,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """
    Fetch all sessions for the current user. If the user is unauthenticated, 
    it fetches sessions where user_id is null.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return ApiResult(ok=True, data=[])

        query = supabase.table("conversations").select("*")
        if current_user_id:
            # Match conversations owned by this user or legacy anonymous ones
            query = query.or_(f"user_id.eq.{current_user_id},user_id.is.null")
        else:
            # Anonymous user gets only anonymous conversations
            query = query.filter("user_id", "is", "null")

        conv_res = query.order("updated_at", desc=True).range(offset, offset + limit - 1).execute()
        conversations = conv_res.data or []

        result_sessions = []
        for conv in conversations:
            result_sessions.append({
                "id": conv["id"],
                "title": conv.get("title", "Cuộc trò chuyện mới"),
                "updatedAt": conv.get("updated_at", datetime.now(timezone.utc).isoformat()),
                "messages": []
            })

        return ApiResult(ok=True, data=result_sessions)
    except Exception as e:
        logger.exception(f"Error fetching sessions for user {current_user_id}: {e}")
        return ApiResult(ok=False, error={"message": "Lỗi khi lấy danh sách phiên làm việc"})

@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """
    Fetch all messages for a specific session.
    """
    clean_id = ensure_uuid(session_id)
    try:
        supabase = get_supabase_client()
        if not supabase:
            return ApiResult(ok=True, data=[])

        # Fetch messages ordered by creation time descending for pagination, then reverse for chronological order
        msg_res = supabase.table("messages").select("*").eq("conversation_id", clean_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        msg_list = msg_res.data or []
        msg_list.reverse() 

        messages = [
            {
                "id": f"m_{m['id']}",
                "role": m["role"],
                "content": m["content"],
                "createdAt": m.get("created_at", datetime.now(timezone.utc).isoformat()),
                "status": "complete"
            }
            for m in msg_list
        ]

        return ApiResult(ok=True, data=messages)
    except Exception as e:
        logger.exception(f"Error fetching messages for session {clean_id}: {e}")
        return ApiResult(ok=False, error={"message": "Lỗi khi lấy tin nhắn của phiên làm việc"})

@router.patch("/{session_id}")
async def rename_session(
    session_id: str,
    payload: RenameSessionPayload,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """
    Rename an existing chat session.
    """
    clean_id = ensure_uuid(session_id)
    supabase = get_supabase_client()
    new_title = payload.title.strip()[:100]
    
    if supabase:
        try:
            if not new_title:
                return ApiResult(ok=False, error={"message": "Tiêu đề không được để trống."})
                
            supabase.table("conversations").update({
                "title": new_title,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", clean_id).execute()
        except Exception as e:
            logger.exception(f"Error renaming session {clean_id}: {e}")
            return ApiResult(ok=False, error={"message": "Không thể đổi tên cuộc trò chuyện."})
            
    return ApiResult(ok=True, data={"sessionId": clean_id, "title": new_title})

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """
    Delete a specific session and cascade delete all its messages.
    """
    clean_id = ensure_uuid(session_id)
    supabase = get_supabase_client()
    
    if supabase:
        try:
            supabase.table("conversations").delete().eq("id", clean_id).execute()
        except Exception as e:
            logger.exception(f"Error deleting session {clean_id}: {e}")
            return ApiResult(ok=False, error={"message": "Không thể xóa cuộc trò chuyện."})
            
    return ApiResult(ok=True, data={"sessionId": clean_id, "deleted": True})
