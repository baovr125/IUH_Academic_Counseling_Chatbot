from typing import Optional
import os
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from fastapi.responses import StreamingResponse

from app.utils.limiter import limiter
from app.utils.security import get_optional_current_user_id
from app.schemas.chat import SendMessagePayload
from app.services.llm_generation_service import process_chat_message, process_chat_message_stream

router = APIRouter(tags=["Academic Chatbot Service - Chat"])

@router.post("")
@router.post("/") # To handle both /messages and /messages/ if included differently
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    payload: SendMessagePayload,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """
    Synchronously generate a response for a chat message. 
    This waits for the full response to be generated before returning.
    """
    return await process_chat_message(payload, current_user_id)


@router.post("/stream")
@limiter.limit("20/minute")
async def send_message_stream(
    request: Request,
    payload: SendMessagePayload,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """
    Stream a response for a chat message using Server-Sent Events (SSE).
    """
    return StreamingResponse(
        process_chat_message_stream(payload, current_user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Disables proxy buffering for Nginx/Kong
        }
    )

@router.delete("/cache")
async def clear_semantic_cache(
    x_dev_token: str = Header(None),
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """
    Manually invalidate all semantic cache entries in Redis and Supabase.
    """
    expected_token = os.getenv("DEV_ADMIN_TOKEN", "iuh-dev-secret-2026")
    if not x_dev_token or x_dev_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Forbidden: Developer access only."
        )

    from app.services.rag_service import invalidate_semantic_cache
    await invalidate_semantic_cache()
    return {"message": "Cache successfully cleared from Redis and Supabase."}

