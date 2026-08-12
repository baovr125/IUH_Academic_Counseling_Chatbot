import uuid
import json
import asyncio
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from google.genai import types

from app.utils.limiter import limiter
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
    ensure_uuid,
    save_user_msg_to_db,
    save_assistant_msg_to_db,
    save_turn_to_db,
)
from app.services.supabase_client import get_supabase_client
from app.services.rag_service import (
    get_gemini,
    build_rag_payload,
    GEMINI_MODELS,
    check_semantic_cache,
    async_cache_writeback,
)
from app.utils.logger import logger

router = APIRouter(tags=["Academic Chatbot Service"])

@router.get("/sessions")
async def get_sessions(
    limit: int = 20,
    offset: int = 0,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    try:
        supabase = get_supabase_client()
        if not supabase:
            return ApiResult(ok=True, data=[])

        query = supabase.table("conversations").select("*")
        if current_user_id:
            query = query.or_(f"user_id.eq.{current_user_id},user_id.is.null")
        else:
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

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    clean_id = ensure_uuid(session_id)
    try:
        supabase = get_supabase_client()
        if not supabase:
            return ApiResult(ok=True, data=[])

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

@router.patch("/sessions/{session_id}")
async def rename_session(
    session_id: str,
    payload: RenameSessionPayload,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
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

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    clean_id = ensure_uuid(session_id)
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.table("conversations").delete().eq("id", clean_id).execute()
        except Exception as e:
            logger.exception(f"Error deleting session {clean_id}: {e}")
            return ApiResult(ok=False, error={"message": "Không thể xóa cuộc trò chuyện."})
    return ApiResult(ok=True, data={"sessionId": clean_id, "deleted": True})

@router.post("/messages")
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    payload: SendMessagePayload,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    session_id = payload.sessionId or f"s_{uuid.uuid4().hex[:8]}"

    try:
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

        # Phase 2: Check Semantic Cache
        cache_hit = await check_semantic_cache(normalized_query)
        if cache_hit:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            cached_answer = cache_hit.get("cached_answer", "")
            
            save_turn_to_db(
                session_id, payload.content, cached_answer, payload.content, 
                retrieved_chunk_ids=[], user_id=current_user_id,
                latency_ms=latency_ms, prompt_tokens=0, completion_tokens=0
            )

            assistant_msg = ChatMessage(
                id=f"m_{uuid.uuid4().hex[:8]}",
                role="assistant",
                original_answer=cached_answer,
                content=cached_answer,
                citations=[],
                createdAt=datetime.now(timezone.utc).isoformat(),
                status="complete"
            )
            return ApiResult(
                ok=True, 
                data={
                    "sessionId": ensure_uuid(session_id), 
                    "message": assistant_msg.dict(),
                    "cacheStatus": "HIT"
                }
            )

        history, retrieval_query, citations, chunk_ids, system_instruction, contents, top_doc_score = await build_rag_payload(session_id, normalized_query)

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
                    logger.exception(f"Error generating content with model {model_name}: {e}")
                    last_exception = e
                    continue

        if gemini_response and gemini_response.text:
            generated_text = gemini_response.text
        else:
            err_msg = str(last_exception) if last_exception else "Gemini client không thể khởi tạo"
            generated_text = f"⚠️ Thông báo hệ thống AI: {err_msg}"

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        save_turn_to_db(
            session_id, payload.content, generated_text, payload.content, 
            retrieved_chunk_ids=chunk_ids, user_id=current_user_id,
            latency_ms=latency_ms
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

        # Trigger async cache write-back in background
        if gemini_response and gemini_response.text:
            asyncio.create_task(async_cache_writeback(normalized_query, generated_text, top_doc_score))

        return ApiResult(
            ok=True,
            data={
                "sessionId": ensure_uuid(session_id),
                "message": assistant_message.dict()
            }
        )

    except Exception as e:
        logger.exception(f"Error in send_message: {e}")
        return ApiResult(ok=False, error={"message": "Đã xảy ra lỗi khi gửi tin nhắn."})

@router.post("/messages/stream")
@limiter.limit("20/minute")
async def send_message_stream(
    request: Request,
    payload: SendMessagePayload,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    session_id = payload.sessionId or f"s_{uuid.uuid4().hex[:8]}"
    clean_session_id = save_user_msg_to_db(session_id, payload.content, payload.content, user_id=current_user_id)

    async def event_generator():
        accumulated_text = ""
        chunk_ids = []
        try:
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

            # Phase 2: Check Semantic Cache
            cache_hit = await check_semantic_cache(normalized_query)
            if cache_hit:
                cached_answer = cache_hit.get("cached_answer", "")
                
                # We yield metadata with cacheStatus
                yield f"data: {json.dumps({'type': 'metadata', 'sessionId': clean_session_id, 'citations': [], 'cacheStatus': 'HIT'})}\n\n"
                yield f"data: {json.dumps({'type': 'delta', 'text': cached_answer})}\n\n"
                accumulated_text = cached_answer
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            history, retrieval_query, citations, chunk_ids, system_instruction, contents, top_doc_score = await build_rag_payload(clean_session_id, normalized_query)

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
                        logger.exception(f"Error streaming content with model {model_name}: {e}")
                        last_err = e
                        continue

            if stream_iter:
                if first_chunk and first_chunk.text:
                    accumulated_text += first_chunk.text
                    yield f"data: {json.dumps({'type': 'delta', 'text': first_chunk.text})}\n\n"

                while True:
                    chunk = await asyncio.to_thread(lambda: next(stream_iter, None))
                    if chunk is None:
                        break
                    if chunk.text:
                        accumulated_text += chunk.text
                        yield f"data: {json.dumps({'type': 'delta', 'text': chunk.text})}\n\n"
            else:
                err_str = str(last_err) if last_err else "Gemini client chưa khởi tạo"
                fallback_txt = f"⚠️ Lỗi AI: {err_str}"
                accumulated_text = fallback_txt
                yield f"data: {json.dumps({'type': 'delta', 'text': fallback_txt})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception(f"Error in send_message_stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Đã xảy ra lỗi máy chủ'})}\n\n"
        finally:
            if accumulated_text.strip():
                save_assistant_msg_to_db(
                    clean_session_id, accumulated_text, 
                    retrieved_chunk_ids=chunk_ids
                )
                
                # Trigger async cache write-back in background
                if not accumulated_text.startswith("⚠️"):
                    asyncio.create_task(async_cache_writeback(normalized_query, accumulated_text, top_doc_score))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
