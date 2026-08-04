import os
import uuid
import json
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Any

# Suppress HuggingFace hub warnings & load HF_TOKEN if provided
# os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, CrossEncoder
from supabase import Client, create_client
from google import genai
from google.genai import types

from utils.security import get_optional_current_user_id

router = APIRouter(prefix="/api/chat", tags=["chat"])

# --- 1. Clients & Models Lazy Initialization ---
_supabase_client = None
_gemini_client = None
_embedder_model = None
_reranker_model = None

def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if url and key:
            try:
                _supabase_client = create_client(url, key)
            except Exception:
                pass
    return _supabase_client

def get_gemini():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            try:
                _gemini_client = genai.Client(api_key=api_key)
            except Exception:
                pass
    return _gemini_client

def get_embedder():
    global _embedder_model
    if _embedder_model is None:
        _embedder_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _embedder_model

def get_reranker():
    global _reranker_model
    if _reranker_model is None:
        _reranker_model = CrossEncoder("BAAI/bge-reranker-v2-m3")
    return _reranker_model


def preload_models():
    """Preloads HuggingFace ML models (Embedder & Reranker) during application startup."""
    print("🚀 [PRELOAD] Đang tải ML Models (SentenceTransformer & CrossEncoder) vào RAM...")
    get_embedder()
    get_reranker()
    get_gemini()
    print("✅ [PRELOAD] Sẵn sàng! Tất cả ML Models đã được nạp trước vào bộ nhớ RAM.")


# In-memory session memory fallback (session_id -> list of message dicts)
session_memory: dict = {}

# Priority Gemini models
GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.5-flash"
]

# --- 2. Schemas ---
class Citation(BaseModel):
    id: str
    sourceTitle: str
    pageOrSection: str
    snippet: Optional[str] = None
    url: Optional[str] = None

class ChatMessage(BaseModel):
    id: str
    role: str
    original_answer: Optional[str] = None
    content: str
    citations: Optional[List[Citation]] = None
    createdAt: str
    status: str

class SendMessagePayload(BaseModel):
    sessionId: Optional[str] = None
    content: str

class SendMessageResponseData(BaseModel):
    sessionId: str
    message: ChatMessage

class ApiResult(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[dict] = None


# --- 3. Step 1 & 2: Database Retrieval + Reranking ---
async def retrieve_relevant_chunks(query_text: str, top_k: int = 5, candidate_count: int = 35):
    """
    Stage 1: Retrieve candidate_count (35) chunks via Supabase Hybrid RRF RPC.
    Stage 2: Cross-Encoder Reranking using BAAI/bge-reranker-v2-m3 -> Top k (5).
    Offloads CPU-bound ML inference to background thread pool.
    """
    embedder = get_embedder()
    query_vector = await asyncio.to_thread(lambda: embedder.encode(query_text).tolist())

    supabase = get_supabase()
    if not supabase:
        return []

    try:
        def _call_rpc():
            return supabase.rpc(
                "match_chunks_hybrid_rrf",
                {
                    "query_text": query_text,
                    "query_embedding": query_vector,
                    "match_count": candidate_count
                }
            ).execute()

        response = await asyncio.to_thread(_call_rpc)
        chunks = response.data or []
    except Exception:
        chunks = []

    if not chunks:
        return []

    # Stage 2 Reranking
    pairs = []
    for c in chunks:
        meta = c.get("metadata", {}) or {}
        title = meta.get("title") or meta.get("sourceTitle", "")
        text = f"{title}\n{c.get('content', '')}".strip()
        pairs.append((query_text, text))

    reranker = get_reranker()
    scores = await asyncio.to_thread(lambda: reranker.predict(pairs, batch_size=16))
    for idx, chunk in enumerate(chunks):
        chunk["rerank_score"] = float(scores[idx])

    chunks = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    return chunks[:top_k]


async def generate_standalone_query(history: list, current_query: str) -> str:
    """
    Upgrade 2: LLM Standalone Query Rewriter.
    Converts follow-up questions into a self-contained search query in Vietnamese.
    """
    if not history:
        return current_query

    last_user_msg = None
    for msg in reversed(history):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break

    if not last_user_msg or last_user_msg == current_query:
        return current_query

    rewrite_prompt = (
        "You are a search query rewriter for an academic counselor chatbot at IUH University (Đại học Công nghiệp TP.HCM). "
        "Given the conversation context and a follow-up question, rewrite the follow-up question into "
        "a single, self-contained standalone search query in Vietnamese. "
        "Do NOT answer the question. Only output the rewritten search query.\n\n"
        f"Previous User Question: {last_user_msg}\n"
        f"Follow-up Question: {current_query}\n"
        "Standalone Search Query:"
    )

    gemini_client = get_gemini()
    if gemini_client:
        for m in GEMINI_MODELS:
            try:
                def _gen_rewrite():
                    return gemini_client.models.generate_content(
                        model=m,
                        contents=rewrite_prompt,
                        config=types.GenerateContentConfig(temperature=0.0)
                    )
                res = await asyncio.to_thread(_gen_rewrite)
                if res and res.text:
                    return res.text.strip()
            except Exception:
                continue

    return f"{last_user_msg} {current_query}"


def ensure_uuid(session_id: Optional[str]) -> str:
    """Converts any custom string session_id (e.g. 's_abc123') deterministically to a valid PostgreSQL UUID."""
    if not session_id:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(session_id))
    except (ValueError, TypeError, AttributeError):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(session_id)))


# --- 4. Database Session History Helpers ---
def get_session_history_from_db(session_id: str) -> list:
    """Loads chat messages from Supabase PostgreSQL tables."""
    clean_id = ensure_uuid(session_id)
    try:
        supabase = get_supabase()
        if supabase:
            res = supabase.table("messages").select("*").eq("conversation_id", clean_id).order("created_at").execute()
            if res.data:
                return [{"role": m["role"], "content": m["content"]} for m in res.data]
    except Exception:
        pass
    return session_memory.get(clean_id, [])

def save_user_msg_to_db(session_id: str, user_content: str, title: str, user_id: Optional[str] = None) -> str:
    """Ensures conversation exists (setting initial title once) and saves user message immediately to PostgreSQL."""
    clean_id = ensure_uuid(session_id)
    supabase = get_supabase()
    if supabase:
        try:
            # Check if conversation already exists in DB
            existing_res = supabase.table("conversations").select("id, title").eq("id", clean_id).execute()
            if existing_res.data and len(existing_res.data) > 0:
                # Existing conversation: only update timestamp, preserve original title
                update_payload = {"updated_at": datetime.now(timezone.utc).isoformat()}
                if user_id:
                    update_payload["user_id"] = user_id
                supabase.table("conversations").update(update_payload).eq("id", clean_id).execute()
            else:
                # New conversation: set initial title from first user query
                conv_payload = {
                    "id": clean_id,
                    "title": title[:50] or "Cuộc trò chuyện mới",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                if user_id:
                    conv_payload["user_id"] = user_id
                supabase.table("conversations").insert(conv_payload).execute()
        except Exception:
            pass

        try:
            supabase.table("messages").insert({
                "conversation_id": clean_id,
                "role": "user",
                "content": user_content
            }).execute()
        except Exception:
            pass

    if clean_id not in session_memory:
        session_memory[clean_id] = []
    session_memory[clean_id].append({"role": "user", "content": user_content})
    return clean_id


def save_assistant_msg_to_db(session_id: str, assistant_content: str, retrieved_chunk_ids: list = None):
    """Saves assistant message to PostgreSQL and updates conversation timestamp."""
    clean_id = ensure_uuid(session_id)
    supabase = get_supabase()
    if supabase:
        try:
            supabase.table("conversations").update({
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", clean_id).execute()
        except Exception:
            pass

        try:
            supabase.table("messages").insert({
                "conversation_id": clean_id,
                "role": "assistant",
                "content": assistant_content,
                "retrieved_chunk_ids": retrieved_chunk_ids or []
            }).execute()
        except Exception:
            pass

    if clean_id not in session_memory:
        session_memory[clean_id] = []
    session_memory[clean_id].append({"role": "assistant", "content": assistant_content})


def save_turn_to_db(session_id: str, user_content: str, assistant_content: str, title: str, retrieved_chunk_ids: list = None, user_id: Optional[str] = None):
    """Persists conversation and message turns into PostgreSQL tables."""
    clean_id = save_user_msg_to_db(session_id, user_content, title, user_id=user_id)
    save_assistant_msg_to_db(clean_id, assistant_content, retrieved_chunk_ids)


class RenameSessionPayload(BaseModel):
    title: str

# --- 5. Chat Router Endpoints ---
@router.get("/sessions")
async def get_sessions(current_user_id: Optional[str] = Depends(get_optional_current_user_id)):
    """Fetches all persistent sessions for the authenticated user from PostgreSQL."""
    try:
        supabase = get_supabase()
        if not supabase:
            return ApiResult(ok=True, data=[])

        query = supabase.table("conversations").select("*").or_("is_deleted.eq.false,is_deleted.is.null")
        if current_user_id:
            query = query.or_(f"user_id.eq.{current_user_id},user_id.is.null")

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
    supabase = get_supabase()
    if supabase:
        try:
            new_title = payload.title.strip()[:100] or "Cuộc trò chuyện mới"
            supabase.table("conversations").update({"title": new_title, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", clean_id).execute()
        except Exception as e:
            return ApiResult(ok=False, error={"message": f"Không thể đổi tên cuộc trò chuyện: {str(e)}"})
    return ApiResult(ok=True, data={"sessionId": clean_id, "title": payload.title})


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """Soft deletes a chat conversation from user view while preserving database records for RAG analytics."""
    clean_id = ensure_uuid(session_id)
    supabase = get_supabase()
    if supabase:
        try:
            supabase.table("conversations").update({"is_deleted": True, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", clean_id).execute()
        except Exception as e:
            return ApiResult(ok=False, error={"message": f"Không thể xóa cuộc trò chuyện: {str(e)}"})
    return ApiResult(ok=True, data={"sessionId": clean_id, "deleted": True})


async def build_rag_payload(session_id: str, content: str):
    """Helper to process history, query expansion, retrieval, citations, and prompt."""
    history = get_session_history_from_db(session_id)
    retrieval_query = await generate_standalone_query(history, content)

    # 1. Retrieve & Rerank (Top 35 candidates -> Top 5)
    chunks = await retrieve_relevant_chunks(retrieval_query, top_k=5, candidate_count=35)

    # 2. Citations & Context
    context_parts = []
    citations = []
    chunk_ids = []
    for index, c in enumerate(chunks, 1):
        context_parts.append(f"[Source {index}]: {c['content']}")
        chunk_ids.append(c.get("id"))
        meta = c.get("metadata", {}) or {}

        source_title = meta.get("title") or meta.get("sourceTitle") or "Cẩm nang Sinh viên IUH"
        page = meta.get("page")
        breadcrumbs = meta.get("breadcrumbs")
        chapter = meta.get("chapter_parent")

        if page and str(page) != "None":
            page_or_section = f"Trang {page}"
        elif breadcrumbs and len(breadcrumbs) > 0:
            page_or_section = " > ".join(breadcrumbs[:2])
        elif chapter:
            page_or_section = str(chapter)
        else:
            page_or_section = "Quy định IUH"

        snippet = c['content'][:140] + "..." if len(c['content']) > 140 else c['content']

        citations.append(Citation(
            id=f"c_{uuid.uuid4().hex[:8]}",
            sourceTitle=source_title,
            pageOrSection=page_or_section,
            snippet=snippet,
            url=c.get("source_url")
        ))

    context_str = "\n\n".join(context_parts) if context_parts else "Không tìm thấy tài liệu phù hợp trong CSDL."

    # 3. Build System Instruction with strict grounding rules
    system_instruction = (
        "Bạn là Trợ lý Tư vấn Học tập thông minh của Trường Đại học Công nghiệp TP.HCM (IUH).\n"
        "Nhiệm vụ của bạn là giải đáp thắc mắc của sinh viên về quy chế học tập, quy trình thủ tục, học phí, và các quy định nhà trường.\n\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. Trả lời CHÍNH XÁC, DỰA TRÊN NGỮ CẢNH ĐƯỢC CỦNG CỐ bên dưới.\n"
        "2. Nếu ngữ cảnh không có thông tin, hãy thành thật trả lời không biết và hướng dẫn sinh viên liên hệ Phòng Đào tạo (pdt@iuh.edu.vn).\n"
        "3. Trích dẫn rõ nguồn, trang hoặc điều khoản nếu có trong ngữ cảnh.\n"
        "4. Trả lời thân thiện, lịch sự, chuẩn mực sư phạm.\n\n"
        f"--- NGỮ CẢNH TÀI LIỆU TRÍCH XUẤT ---\n{context_str}\n-----------------------------------"
    )

    # Convert past turns to Gemini content objects
    contents = []
    for turn in history[-6:]:
        role = "user" if turn["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=turn["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=content)]))

    return history, retrieval_query, citations, chunk_ids, system_instruction, contents


@router.post("/messages")
async def send_message(payload: SendMessagePayload):
    """
    Standard Non-Streaming Endpoint (Fallback).
    """
    session_id = payload.sessionId or f"s_{uuid.uuid4().hex[:8]}"

    try:
        history, retrieval_query, citations, chunk_ids, system_instruction, contents = await build_rag_payload(session_id, payload.content)

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

        # Persist user question and assistant answer
        save_turn_to_db(session_id, payload.content, generated_text, payload.content, retrieved_chunk_ids=chunk_ids)

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
    """
    session_id = payload.sessionId or f"s_{uuid.uuid4().hex[:8]}"
    clean_session_id = save_user_msg_to_db(session_id, payload.content, payload.content, user_id=current_user_id)

    async def event_generator():
        accumulated_text = ""
        chunk_ids = []
        try:
            history, retrieval_query, citations, chunk_ids, system_instruction, contents = await build_rag_payload(clean_session_id, payload.content)

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
                    yield f"data: {json.dumps({'type': 'delta', 'text': first_chunk.text})}\n\n"
                    await asyncio.sleep(0.01)

                for chunk in stream_iter:
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
            # Guarantee assistant response is persisted even if client tab disconnected/switched!
            if accumulated_text.strip():
                save_assistant_msg_to_db(clean_session_id, accumulated_text, retrieved_chunk_ids=chunk_ids)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )