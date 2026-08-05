import uuid
import json
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from google.genai import types

from app.utils.security import get_optional_current_user_id
from app.schemas.chat import (
    Citation,
    ChatMessage,
    SendMessagePayload,
    RenameSessionPayload,
    FeedbackPayload,
    ApiResult,
)
from app.guardrails.query_filter import (
    check_safety_and_jailbreak,
    normalize_academic_query,
    evaluate_domain_relevance,
)
from app.services.chat_service import (
    get_supabase_client,
    ensure_uuid,
    save_user_msg_to_db,
    save_assistant_msg_to_db,
    save_turn_to_db,
)
from app.services.rag_service import (
    get_gemini,
    preload_models,
    build_rag_payload,
    GEMINI_MODELS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# --- Chat Router Endpoints ---

@router.get("/sessions")
async def get_sessions(current_user_id: Optional[str] = Depends(get_optional_current_user_id)):
    """Fetches all persistent sessions for the authenticated user from PostgreSQL."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return ApiResult(ok=True, data=[])

        query = supabase.table("conversations").select("*")
        if current_user_id:
            query = query.or_(f"user_id.eq.{current_user_id},user_id.is.null")
        else:
            query = query.filter("user_id", "is", "null")

        conv_res = query.order("updated_at", desc=True).execute()
        conversations = conv_res.data or []

        result_sessions = []
        for conv in conversations:
            msg_res = supabase.table("messages").select("*").eq("conversation_id", conv["id"]).order("created_at").execute()
            msg_list = msg_res.data or []

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

            result_sessions.append({
                "id": conv["id"],
                "title": conv.get("title", "Cuộc trò chuyện mới"),
                "updatedAt": conv.get("updated_at", datetime.now(timezone.utc).isoformat()),
                "messages": messages
            })

        return ApiResult(ok=True, data=result_sessions)
    except Exception as e:
        return ApiResult(ok=False, error={"message": str(e)})


@router.patch("/sessions/{session_id}")
async def rename_session(
    session_id: str,
    payload: RenameSessionPayload,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """Renames a chat conversation session in PostgreSQL."""
    clean_id = ensure_uuid(session_id)
    supabase = get_supabase_client()
    if supabase:
        try:
            new_title = payload.title.strip()[:100]
            if not new_title:
                return ApiResult(ok=False, error={"message": "Tiêu đề không được để trống."})
            supabase.table("conversations").update({
                "title": new_title,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", clean_id).execute()
        except Exception as e:
            return ApiResult(ok=False, error={"message": f"Không thể đổi tên cuộc trò chuyện: {str(e)}"})
    return ApiResult(ok=True, data={"sessionId": clean_id, "title": new_title})


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """Deletes a chat conversation from PostgreSQL."""
    clean_id = ensure_uuid(session_id)
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.table("conversations").delete().eq("id", clean_id).execute()
        except Exception as e:
            return ApiResult(ok=False, error={"message": f"Không thể xóa cuộc trò chuyện: {str(e)}"})
    return ApiResult(ok=True, data={"sessionId": clean_id, "deleted": True})


@router.patch("/messages/{message_id}/feedback")
async def submit_feedback(
    message_id: str,
    payload: FeedbackPayload,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """Submits user feedback (like/dislike and comment) for a specific assistant message."""
    try:
        # Strip the "m_" prefix if it exists
        clean_msg_id = message_id[2:] if message_id.startswith("m_") else message_id
        clean_msg_id = ensure_uuid(clean_msg_id)
        
        supabase = get_supabase_client()
        if not supabase:
            return ApiResult(ok=False, error={"message": "Lỗi kết nối CSDL."})
        
        # Verify the message belongs to the user if authentication is implemented here
        
        supabase.table("messages").update({
            "feedback": payload.feedback,
            "feedback_comment": payload.comment
        }).eq("id", clean_msg_id).execute()
        
        return ApiResult(ok=True, data={"messageId": message_id, "feedback": payload.feedback})
    except Exception as e:
        return ApiResult(ok=False, error={"message": f"Không thể gửi phản hồi: {str(e)}"})


@router.post("/messages")
async def send_message(
    payload: SendMessagePayload,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """
    Standard Non-Streaming Endpoint (Fallback).
    Applies Stage 0 Guardrails (Jailbreak Detection, Normalization, Domain Filter).
    """
    session_id = payload.sessionId or f"s_{uuid.uuid4().hex[:8]}"

    try:
        # Stage 0 Guardrails Check
        safety_violation = check_safety_and_jailbreak(payload.content)
        if safety_violation:
            clean_id = save_user_msg_to_db(session_id, payload.content, payload.content, user_id=current_user_id)
            save_assistant_msg_to_db(clean_id, safety_violation)
            assistant_msg = ChatMessage(
                id=f"m_{uuid.uuid4().hex[:8]}",
                role="assistant",
                original_answer=safety_violation,
                content=safety_violation,
                citations=[],
                createdAt=datetime.now(timezone.utc).isoformat(),
                status="complete"
            )
            return ApiResult(ok=True, data={"sessionId": clean_id, "message": assistant_msg.dict()})

        normalized_query = normalize_academic_query(payload.content)

        is_relevant, off_topic_msg = evaluate_domain_relevance(normalized_query)
        if not is_relevant and off_topic_msg:
            clean_id = save_user_msg_to_db(session_id, payload.content, payload.content, user_id=current_user_id)
            save_assistant_msg_to_db(clean_id, off_topic_msg)
            assistant_msg = ChatMessage(
                id=f"m_{uuid.uuid4().hex[:8]}",
                role="assistant",
                original_answer=off_topic_msg,
                content=off_topic_msg,
                citations=[],
                createdAt=datetime.now(timezone.utc).isoformat(),
                status="complete"
            )
            return ApiResult(ok=True, data={"sessionId": clean_id, "message": assistant_msg.dict()})

        start_time = time.perf_counter()
        history, retrieval_query, citations, chunk_ids, system_instruction, contents = await build_rag_payload(session_id, normalized_query)

        gemini_response = None
        last_exception = None
        gemini_client = get_gemini()

        if gemini_client:
            for model_name in GEMINI_MODELS:
                try:
                    cfg_kwargs = {
                        "system_instruction": system_instruction,
                        "temperature": 0.2,
                    }
                    if "2.5" in model_name:
                        cfg_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)

                    def _gen_sync(m_name=model_name, c_kwargs=cfg_kwargs):
                        return gemini_client.models.generate_content(
                            model=m_name,
                            contents=contents,
                            config=types.GenerateContentConfig(**c_kwargs)
                        )
                    gemini_response = await asyncio.to_thread(_gen_sync)
                    if gemini_response and gemini_response.text:
                        break
                except Exception as e:
                    last_exception = e
                    continue

        if gemini_response and gemini_response.text:
            generated_text = gemini_response.text
        else:
            err_msg = str(last_exception) if last_exception else "Gemini client không thể khởi tạo"
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                generated_text = (
                    "⚠️ **Thông báo giới hạn API**: Khóa API Gemini hiện tại đã đạt giới hạn truy cập. "
                    "Vui lòng đợi ít phút hoặc cập nhật `GEMINI_API_KEY` trong file `.env`!"
                )
            else:
                generated_text = f"⚠️ Lỗi kết nối AI: {err_msg}"

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        prompt_tokens = None
        completion_tokens = None
        if gemini_response and hasattr(gemini_response, "usage_metadata") and gemini_response.usage_metadata:
            usage = gemini_response.usage_metadata
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            completion_tokens = getattr(usage, "candidates_token_count", None)

        # Persist user question and assistant answer
        save_turn_to_db(
            session_id, payload.content, generated_text, payload.content, 
            retrieved_chunk_ids=chunk_ids, user_id=current_user_id,
            latency_ms=latency_ms, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        )

        assistant_message = ChatMessage(
            id=f"m_{uuid.uuid4().hex[:8]}",
            role="assistant",
            original_answer=generated_text,
            content=generated_text,
            citations=citations,
            createdAt=datetime.now(timezone.utc).isoformat(),
            status="complete"
        )

        return ApiResult(
            ok=True,
            data={
                "sessionId": ensure_uuid(session_id),
                "message": assistant_message.dict()
            }
        )

    except Exception as e:
        return ApiResult(ok=False, error={"message": str(e)})


@router.post("/messages/stream")
async def send_message_stream(
    payload: SendMessagePayload,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """
    Streaming Endpoint (Server-Sent Events SSE).
    Saves user message immediately and assistant message on completion/abort.
    Applies Stage 0 Guardrails (Jailbreak Detection, Normalization, Domain Filter).
    """
    session_id = payload.sessionId or f"s_{uuid.uuid4().hex[:8]}"
    clean_session_id = save_user_msg_to_db(session_id, payload.content, payload.content, user_id=current_user_id)

    async def event_generator():
        accumulated_text = ""
        chunk_ids = []
        try:
            # Stage 0: Guardrails Check (Jailbreak & Domain Relevance)
            safety_violation = check_safety_and_jailbreak(payload.content)
            if safety_violation:
                yield f"data: {json.dumps({'type': 'metadata', 'sessionId': clean_session_id, 'citations': []})}\n\n"
                yield f"data: {json.dumps({'type': 'delta', 'text': safety_violation})}\n\n"
                accumulated_text = safety_violation
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            normalized_query = normalize_academic_query(payload.content)

            is_relevant, off_topic_msg = evaluate_domain_relevance(normalized_query)
            if not is_relevant and off_topic_msg:
                yield f"data: {json.dumps({'type': 'metadata', 'sessionId': clean_session_id, 'citations': []})}\n\n"
                yield f"data: {json.dumps({'type': 'delta', 'text': off_topic_msg})}\n\n"
                accumulated_text = off_topic_msg
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            start_time = time.perf_counter()
            history, retrieval_query, citations, chunk_ids, system_instruction, contents = await build_rag_payload(clean_session_id, normalized_query)

            # Send metadata event with citations first
            citations_data = [c.dict() for c in citations]
            yield f"data: {json.dumps({'type': 'metadata', 'sessionId': clean_session_id, 'citations': citations_data})}\n\n"

            stream_iter = None
            first_chunk = None
            last_err = None
            gemini_client = get_gemini()

            if gemini_client:
                for model_name in GEMINI_MODELS:
                    try:
                        cfg_kwargs = {
                            "system_instruction": system_instruction,
                            "temperature": 0.2,
                        }
                        if "2.5" in model_name:
                            cfg_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)

                        def _start_stream_with_first_chunk(m_name=model_name, c_kwargs=cfg_kwargs):
                            st = gemini_client.models.generate_content_stream(
                                model=m_name,
                                contents=contents,
                                config=types.GenerateContentConfig(**c_kwargs)
                            )
                            it = iter(st)
                            fc = next(it, None)
                            return it, fc

                        stream_iter, first_chunk = await asyncio.to_thread(_start_stream_with_first_chunk)
                        break
                    except Exception as e:
                        last_err = e
                        continue

            if stream_iter:
                if first_chunk and first_chunk.text:
                    accumulated_text += first_chunk.text
                    last_chunk = first_chunk
                    yield f"data: {json.dumps({'type': 'delta', 'text': first_chunk.text})}\n\n"
                    await asyncio.sleep(0.01)

                # Read synchronous stream chunks in a background thread to avoid blocking asyncio event loop
                while True:
                    chunk = await asyncio.to_thread(lambda: next(stream_iter, None))
                    if chunk is None:
                        break
                    last_chunk = chunk
                    if chunk.text:
                        accumulated_text += chunk.text
                        yield f"data: {json.dumps({'type': 'delta', 'text': chunk.text})}\n\n"
                        await asyncio.sleep(0.01)
            else:
                err_str = str(last_err) if last_err else "Gemini client không thể khởi tạo"
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    fallback_txt = "⚠️ Giới hạn lượt truy cập API Gemini. Vui lòng đợi ít phút!"
                else:
                    fallback_txt = f"⚠️ Lỗi AI: {err_str}"
                accumulated_text = fallback_txt
                yield f"data: {json.dumps({'type': 'delta', 'text': fallback_txt})}\n\n"

            # Done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # Guarantee assistant response is persisted even if client tab disconnected!
            if accumulated_text.strip():
                latency_ms = int((time.perf_counter() - start_time) * 1000) if 'start_time' in locals() else None
                prompt_tokens = None
                completion_tokens = None
                if 'last_chunk' in locals() and last_chunk and hasattr(last_chunk, "usage_metadata") and last_chunk.usage_metadata:
                    usage = last_chunk.usage_metadata
                    prompt_tokens = getattr(usage, "prompt_token_count", None)
                    completion_tokens = getattr(usage, "candidates_token_count", None)

                save_assistant_msg_to_db(
                    clean_session_id, accumulated_text, 
                    retrieved_chunk_ids=chunk_ids,
                    latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens
                )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )