from app.guardrails.query_filter import OFF_TOPIC_MESSAGE
import uuid
import json
import time
import asyncio
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator

from app.services.llm_providers import get_llm_provider

from app.schemas.chat import ChatMessage, SendMessagePayload, ApiResult
from app.guardrails.query_filter import (
    check_safety_and_jailbreak,

)
from app.services.chat_service import (
    ensure_uuid,
    save_user_msg_to_db,
    save_assistant_msg_to_db,
    save_turn_to_db,
    update_message_embedding_in_db,
)
from app.services.log_utils import log_cache_hit_to_md, write_full_rag_log_to_md
from app.services.rag_service import (
    build_rag_payload,
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
        start_rewrite = time.perf_counter()
        retrieval_query_raw, router_model = await generate_standalone_query(filtered_history, normalized_query)
        rewrite_latency_ms = int((time.perf_counter() - start_rewrite) * 1000)
        
        # Step 2: Extract Intent Router Flag
        print(f"HEY! retrieval_query_raw IS: {repr(retrieval_query_raw)}", flush=True)
        if retrieval_query_raw.strip() == "<FALSE>":
            clean_id = save_user_msg_to_db(session_id, payload.content, retrieval_query_raw, user_id=current_user_id)
            save_assistant_msg_to_db(clean_id, OFF_TOPIC_MESSAGE)
            assistant_msg = _build_assistant_message(OFF_TOPIC_MESSAGE)
            return ApiResult(ok=True, data={"sessionId": clean_id, "message": assistant_msg.dict()})
            
        # Extract the actual rewritten query
        retrieval_query = retrieval_query_raw.replace("<TRUE>", "").replace("</TRUE>", "").strip()

        # Generate the single query embedding using the rewritten context-rich query
        query_embedding = await get_query_embedding(retrieval_query)
        
        # --- HYBRID MEMORY: Save user embedding to DB in background ---
        asyncio.create_task(asyncio.to_thread(update_message_embedding_in_db, user_msg_id, query_embedding))

        start_time = time.perf_counter()

        # Step 3: Semantic Cache Lookup (using the context-rich query)
        cache_hit = await check_semantic_cache(retrieval_query, query_embedding)
        if cache_hit:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            cached_answer = cache_hit.get("cached_answer", "")
            
            # --- CACHE LOGGING ---
            asyncio.create_task(log_cache_hit_to_md(clean_session_id, normalized_query, retrieval_query, cache_hit, latency_ms))
            
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
        history, retrieval_query, citations, chunk_ids, system_instruction, contents, top_doc_score, rag_data = await build_rag_payload(session_id, normalized_query, retrieval_query, query_embedding)

        provider = get_llm_provider()
        stream_generator = provider.generate_stream(system_instruction, contents)
        
        prompt_tokens = 0
        completion_tokens = 0
        generated_text = ""
        
        try:
            async for chunk_data in stream_generator:
                if "prompt_tokens" in chunk_data:
                    prompt_tokens = chunk_data["prompt_tokens"]
                if "completion_tokens" in chunk_data:
                    completion_tokens = chunk_data["completion_tokens"]
                    
                text = chunk_data.get("text", "")
                if text:
                    generated_text += text
        except Exception as e:
            logger.exception(f"Error collecting LLM stream: {e}")
            generated_text = f"⚠️ Lỗi AI: {e}"

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Step 6: Post-processing and DB Saving
        save_turn_to_db(
            session_id, payload.content, generated_text, payload.content, 
            retrieved_chunk_ids=chunk_ids, user_id=current_user_id,
            latency_ms=latency_ms
        )
        
        try:
            if 'log_file_path' in locals() and log_file_path:
                with open(log_file_path, "a", encoding="utf-8") as lf:
                    lf.write("## AI Answer & Thinking Stage\n\n")
                    lf.write(generated_text + "\n\n")
                    lf.write("---\n")
        except Exception as _e:
            logger.error(f"Failed to append to markdown log: {_e}")

        assistant_message = _build_assistant_message(generated_text, citations)

        # Trigger async cache write-back in background so the user doesn't wait for it
        if gemini_response and gemini_response.text:
            asyncio.create_task(async_cache_writeback(retrieval_query, generated_text, top_doc_score, query_embedding))

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
    clean_session_id, user_msg_id = save_user_msg_to_db(session_id, payload.content, payload.content, user_id=current_user_id)

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
        start_rewrite = time.perf_counter()
        retrieval_query_raw, router_model = await generate_standalone_query(filtered_history, normalized_query)
        rewrite_latency_ms = int((time.perf_counter() - start_rewrite) * 1000)

        # Step 2: Extract Intent Router Flag
        print(f"HEY! retrieval_query_raw IS: {repr(retrieval_query_raw)}", flush=True)
        if retrieval_query_raw.strip() == "<FALSE>":
            yield _build_sse_metadata(clean_session_id)
            yield _build_sse_delta(OFF_TOPIC_MESSAGE)
            accumulated_text = OFF_TOPIC_MESSAGE
            yield _build_sse_done()
            return
            
        # Extract the actual rewritten query
        retrieval_query = retrieval_query_raw.replace("<TRUE>", "").replace("</TRUE>", "").strip()

        # Generate the single query embedding using the rewritten context-rich query
        query_embedding = await get_query_embedding(retrieval_query)
        
        # --- HYBRID MEMORY: Save user embedding to DB in background ---
        asyncio.create_task(asyncio.to_thread(update_message_embedding_in_db, user_msg_id, query_embedding))

        start_time = time.perf_counter()
        # Step 3: Semantic Cache Lookup
        cache_hit = await check_semantic_cache(retrieval_query, query_embedding)
        if cache_hit:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            cached_answer = cache_hit.get("cached_answer", "")
            
            # --- CACHE LOGGING ---
            asyncio.create_task(log_cache_hit_to_md(clean_session_id, normalized_query, retrieval_query, cache_hit, latency_ms))
            
            # Yield metadata with cacheStatus as HIT
            yield _build_sse_metadata(clean_session_id, cache_status="HIT")
            yield _build_sse_delta(cached_answer)
            accumulated_text = cached_answer
            yield _build_sse_done()
            return

        # Step 4: RAG Retrieval and Prompt Building
        history, retrieval_query, citations, chunk_ids, system_instruction, contents, top_doc_score, rag_data = await build_rag_payload(clean_session_id, normalized_query, retrieval_query, query_embedding)

        # Immediately send citations (metadata) to the client
        citations_data = [c.dict() for c in citations]
        yield _build_sse_metadata(clean_session_id, citations_data)

        provider = get_llm_provider()
        stream_generator = provider.generate_stream(system_instruction, contents)
        
        start_llm = time.perf_counter()
        prompt_tokens = 0
        completion_tokens = 0
        llm_latency_ms = 0
        
        in_thinking = False
        strip_next_whitespace = False
        buffer = ""
        
        async for chunk_data in stream_generator:
            if "prompt_tokens" in chunk_data:
                prompt_tokens = chunk_data["prompt_tokens"]
            if "completion_tokens" in chunk_data:
                completion_tokens = chunk_data["completion_tokens"]
                
            text = chunk_data.get("text", "")
            if text:
                accumulated_text += text
                buffer += text
                
                while buffer:
                    if strip_next_whitespace:
                        buffer = buffer.lstrip()
                        if not buffer:
                            break
                        strip_next_whitespace = False
                        
                    if not in_thinking:
                        start_idx = buffer.find("<thinking>")
                        if start_idx != -1:
                            if start_idx > 0:
                                yield _build_sse_delta(buffer[:start_idx])
                            in_thinking = True
                            buffer = buffer[start_idx + len("<thinking>"):]
                        else:
                            partial_match = False
                            for i in range(len("<thinking>") - 1, 0, -1):
                                if len(buffer) >= i:
                                    suffix = buffer[-i:]
                                    if "<thinking>".startswith(suffix):
                                        if len(buffer) > i:
                                            yield _build_sse_delta(buffer[:-i])
                                            buffer = suffix
                                        partial_match = True
                                        break
                            
                            if not partial_match:
                                yield _build_sse_delta(buffer)
                                buffer = ""
                            else:
                                break
                    else:
                        end_idx = buffer.find("</thinking>")
                        if end_idx != -1:
                            in_thinking = False
                            buffer = buffer[end_idx + len("</thinking>"):]
                            strip_next_whitespace = True
                        else:
                            partial_match = False
                            for i in range(len("</thinking>") - 1, 0, -1):
                                if len(buffer) >= i:
                                    suffix = buffer[-i:]
                                    if "</thinking>".startswith(suffix):
                                        buffer = suffix
                                        partial_match = True
                                        break
                            
                            if not partial_match:
                                buffer = ""
                            else:
                                break
                                
        if buffer and not in_thinking:
            yield _build_sse_delta(buffer)

        llm_latency_ms = int((time.perf_counter() - start_llm) * 1000)
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
            
            try:
                if 'rag_data' in locals() and rag_data:
                    _rlat = rag_data.get('retrieval_latency_ms', 0)
                    _rl = rewrite_latency_ms if 'rewrite_latency_ms' in locals() else 0
                    _ll = llm_latency_ms if 'llm_latency_ms' in locals() else 0
                    _pt = prompt_tokens if 'prompt_tokens' in locals() else 0
                    _ct = completion_tokens if 'completion_tokens' in locals() else 0
                    
                    _rm = router_model if 'router_model' in locals() else "Unknown"
                    _lm = provider.last_used_model if 'provider' in locals() else "Unknown"
                    
                    asyncio.create_task(write_full_rag_log_to_md(
                        clean_session_id, normalized_query, retrieval_query, rag_data['chunks'], rag_data['past_memories'],
                        _rlat, _rl, _ll, _pt, _ct, accumulated_text, _rm, _lm
                    ))
            except Exception as _e:
                logger.error(f"Failed to write full markdown log: {_e}")
            
            # Trigger async cache write-back in background
            if not accumulated_text.startswith("⚠️"):
                _rq = retrieval_query if 'retrieval_query' in locals() else ""
                _tds = top_doc_score if 'top_doc_score' in locals() else 0.0
                _qe = query_embedding if 'query_embedding' in locals() else None
                if _rq and _qe:
                    asyncio.create_task(async_cache_writeback(_rq, accumulated_text, _tds, _qe))

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
