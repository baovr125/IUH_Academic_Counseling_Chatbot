import uuid
import json
import time
import asyncio
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator

from google.genai import types

from app.schemas.chat import ChatMessage, SendMessagePayload, ApiResult
from app.guardrails.query_filter import (
    check_safety_and_jailbreak,

    evaluate_domain_relevance,
)
from app.services.chat_service import (
    ensure_uuid,
    save_user_msg_to_db,
    save_assistant_msg_to_db,
    save_turn_to_db,
)
from app.services.rag_service import (
    get_gemini,
    build_rag_payload,
    GEMINI_MODELS,
    check_semantic_cache,
    async_cache_writeback,
    get_query_embedding,
    generate_standalone_query,
)
from app.utils.logger import logger
from app.services.chat_service import get_session_history_from_db

async def process_chat_message(
    payload: SendMessagePayload, 
    current_user_id: Optional[str]
) -> ApiResult:
    """
    Process a non-streaming chat message, running safety checks, cache lookups, 
    RAG retrieval, and LLM generation.
    """
    session_id = payload.sessionId or f"s_{uuid.uuid4().hex[:8]}"

    try:
        # Step 1: Safety Check
        safety_violation = check_safety_and_jailbreak(payload.content)
        if safety_violation:
            clean_id = save_user_msg_to_db(session_id, payload.content, payload.content, user_id=current_user_id)
            save_assistant_msg_to_db(clean_id, safety_violation)
            assistant_msg = _build_assistant_message(safety_violation)
            return ApiResult(ok=True, data={"sessionId": clean_id, "message": assistant_msg.dict()})

        # Pre-process the query string
        normalized_query = payload.content

        # Generate Standalone Query first so follow-ups have full context for domain checks
        history = await asyncio.to_thread(get_session_history_from_db, session_id)
        filtered_history = [msg for msg in history if not (msg["role"] == "user" and msg["content"] == normalized_query)]
        retrieval_query = await generate_standalone_query(filtered_history, normalized_query)

        # Generate the single query embedding using the rewritten context-rich query
        query_embedding = await get_query_embedding(retrieval_query)

        # Step 2: Domain Relevance Check
        is_relevant, off_topic_msg = evaluate_domain_relevance(retrieval_query, query_embedding)
        if not is_relevant and off_topic_msg:
            clean_id = save_user_msg_to_db(session_id, payload.content, retrieval_query, user_id=current_user_id)
            save_assistant_msg_to_db(clean_id, off_topic_msg)
            assistant_msg = _build_assistant_message(off_topic_msg)
            return ApiResult(ok=True, data={"sessionId": clean_id, "message": assistant_msg.dict()})

        start_time = time.perf_counter()

        # Step 3: Semantic Cache Lookup (using the context-rich query)
        cache_hit = await check_semantic_cache(retrieval_query, query_embedding)
        if cache_hit:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            cached_answer = cache_hit.get("cached_answer", "")
            
            # Save the turn to DB to keep the conversation history continuous
            save_turn_to_db(
                session_id, payload.content, cached_answer, payload.content, 
                retrieved_chunk_ids=[], user_id=current_user_id,
                latency_ms=latency_ms, prompt_tokens=0, completion_tokens=0
            )

            assistant_msg = _build_assistant_message(cached_answer)
            return ApiResult(
                ok=True, 
                data={
                    "sessionId": ensure_uuid(session_id), 
                    "message": assistant_msg.dict(),
                    "cacheStatus": "HIT"
                }
            )

        # Step 4: RAG Retrieval and Prompt Building
        history, retrieval_query, citations, chunk_ids, system_instruction, contents, top_doc_score = await build_rag_payload(session_id, normalized_query, retrieval_query, query_embedding)

        gemini_response = None
        last_exception = None
        gemini_client = get_gemini()

        # Step 5: LLM Generation (Fallback across models if one fails)
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
                        chat_history = contents[:-1] if len(contents) > 1 else []
                        last_msg = contents[-1].parts[0].text if len(contents) > 0 else ""
                        
                        chat_session = gemini_client.chats.create(
                            model=m_name,
                            config=types.GenerateContentConfig(**c_kwargs),
                            history=chat_history
                        )
                        return chat_session.send_message(last_msg)
                        
                    # Run the synchronous SDK call in a separate thread to avoid blocking the event loop
                    gemini_response = await asyncio.to_thread(_gen_sync)
                    if gemini_response and gemini_response.text:
                        break
                except Exception as e:
                    logger.exception(f"Error generating content with model {model_name}: {e}")
                    last_exception = e
                    continue

        # Extract generated text or fallback error message
        if gemini_response and gemini_response.text:
            generated_text = gemini_response.text
        else:
            err_msg = str(last_exception) if last_exception else "Gemini client không thể khởi tạo"
            generated_text = f"⚠️ Thông báo hệ thống AI: {err_msg}"

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Step 6: Post-processing and DB Saving
        save_turn_to_db(
            session_id, payload.content, generated_text, payload.content, 
            retrieved_chunk_ids=chunk_ids, user_id=current_user_id,
            latency_ms=latency_ms
        )

        assistant_message = _build_assistant_message(generated_text, citations)

        # Trigger async cache write-back in background so the user doesn't wait for it
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

async def process_chat_message_stream(
    payload: SendMessagePayload, 
    current_user_id: Optional[str]
) -> AsyncGenerator[str, None]:
    """
    Generator function that yields Server-Sent Events (SSE) representing 
    the streaming response of the chatbot.
    """
    session_id = payload.sessionId or f"s_{uuid.uuid4().hex[:8]}"
    
    # Pre-save the user message since the generation is streamed and might be interrupted
    clean_session_id = save_user_msg_to_db(session_id, payload.content, payload.content, user_id=current_user_id)

    accumulated_text = ""
    chunk_ids = []
    top_doc_score = 0.0
    
    try:
        # Step 1: Safety Check
        safety_violation = check_safety_and_jailbreak(payload.content)
        if safety_violation:
            yield _build_sse_metadata(clean_session_id)
            yield _build_sse_delta(safety_violation)
            accumulated_text = safety_violation
            yield _build_sse_done()
            return

        # Pre-process the query string
        normalized_query = payload.content

        # Generate Standalone Query first so follow-ups have full context for domain checks
        history = await asyncio.to_thread(get_session_history_from_db, session_id)
        filtered_history = [msg for msg in history if not (msg["role"] == "user" and msg["content"] == normalized_query)]
        retrieval_query = await generate_standalone_query(filtered_history, normalized_query)

        # Generate the single query embedding using the rewritten context-rich query
        query_embedding = await get_query_embedding(retrieval_query)

        # Step 2: Domain Relevance Check
        is_relevant, off_topic_msg = evaluate_domain_relevance(retrieval_query, query_embedding)
        if not is_relevant and off_topic_msg:
            yield _build_sse_metadata(clean_session_id)
            yield _build_sse_delta(off_topic_msg)
            accumulated_text = off_topic_msg
            yield _build_sse_done()
            return

        # Step 3: Semantic Cache Lookup
        cache_hit = await check_semantic_cache(retrieval_query, query_embedding)
        if cache_hit:
            cached_answer = cache_hit.get("cached_answer", "")
            # Yield metadata with cacheStatus as HIT
            yield _build_sse_metadata(clean_session_id, cache_status="HIT")
            yield _build_sse_delta(cached_answer)
            accumulated_text = cached_answer
            yield _build_sse_done()
            return

        # Step 4: RAG Retrieval and Prompt Building
        history, retrieval_query, citations, chunk_ids, system_instruction, contents, top_doc_score = await build_rag_payload(clean_session_id, normalized_query, retrieval_query, query_embedding)

        # Immediately send citations (metadata) to the client
        citations_data = [c.dict() for c in citations]
        yield _build_sse_metadata(clean_session_id, citations_data)

        stream_iter = None
        first_chunk = None
        last_err = None
        gemini_client = get_gemini()

        # Step 5: LLM Streaming (Fallback across models)
        if gemini_client:
            for model_name in GEMINI_MODELS:
                try:
                    cfg_kwargs = {
                        "system_instruction": system_instruction,
                        "temperature": 0.2,
                    }
                    def _start_stream_with_first_chunk(m_name=model_name, c_kwargs=cfg_kwargs):
                        chat_history = contents[:-1] if len(contents) > 1 else []
                        last_msg = contents[-1].parts[0].text if len(contents) > 0 else ""
                        
                        chat_session = gemini_client.chats.create(
                            model=m_name,
                            config=types.GenerateContentConfig(**c_kwargs),
                            history=chat_history
                        )
                        st = chat_session.send_message_stream(last_msg)
                        
                        # Grab the very first chunk to verify the stream didn't error out immediately
                        it = iter(st)
                        fc = next(it, None)
                        return it, fc

                    # Run in background thread to avoid blocking loop during network initialization
                    stream_iter, first_chunk = await asyncio.to_thread(_start_stream_with_first_chunk)
                    break
                except Exception as e:
                    logger.exception(f"Error streaming content with model {model_name}: {e}")
                    last_err = e
                    continue

        if stream_iter:
            # Yield the first chunk we retrieved earlier
            if first_chunk and first_chunk.text:
                accumulated_text += first_chunk.text
                yield _build_sse_delta(first_chunk.text)

            # Continue yielding the rest of the stream
            while True:
                chunk = await asyncio.to_thread(lambda: next(stream_iter, None))
                if chunk is None:
                    break
                if chunk.text:
                    accumulated_text += chunk.text
                    yield _build_sse_delta(chunk.text)
        else:
            # Fallback error message if all models failed
            err_str = str(last_err) if last_err else "Gemini client chưa khởi tạo"
            fallback_txt = f"⚠️ Lỗi AI: {err_str}"
            accumulated_text = fallback_txt
            yield _build_sse_delta(fallback_txt)

        yield _build_sse_done()

    except Exception as e:
        logger.exception(f"Error in send_message_stream: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': 'Đã xảy ra lỗi máy chủ'})}\n\n"
    finally:
        # Always attempt to save whatever was generated to DB
        if accumulated_text.strip():
            save_assistant_msg_to_db(
                clean_session_id, accumulated_text, 
                retrieved_chunk_ids=chunk_ids
            )
            
            # Trigger async cache write-back in background
            if not accumulated_text.startswith("⚠️"):
                asyncio.create_task(async_cache_writeback(normalized_query, accumulated_text, top_doc_score))

# --- Helper Methods ---

def _build_assistant_message(text: str, citations: list = None) -> ChatMessage:
    return ChatMessage(
        id=f"m_{uuid.uuid4().hex[:8]}",
        role="assistant",
        original_answer=text,
        content=text,
        citations=citations or [],
        createdAt=datetime.now(timezone.utc).isoformat(),
        status="complete"
    )

def _build_sse_metadata(session_id: str, citations: list = None, cache_status: str = None) -> str:
    payload = {'type': 'metadata', 'sessionId': session_id, 'citations': citations or []}
    if cache_status:
        payload['cacheStatus'] = cache_status
    return f"data: {json.dumps(payload)}\n\n"

def _build_sse_delta(text: str) -> str:
    return f"data: {json.dumps({'type': 'delta', 'text': text})}\n\n"

def _build_sse_done() -> str:
    return f"data: {json.dumps({'type': 'done'})}\n\n"
