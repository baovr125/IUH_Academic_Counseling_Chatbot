import os
import uuid
import json
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, CrossEncoder
from supabase import Client, create_client
from google import genai
from google.genai import types

router = APIRouter(prefix="/api/chat", tags=["chat"])

# --- 1. Clients & Models Initialization ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gemini Client (uses GEMINI_API_KEY environment variable)
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Local models
embedder = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

# In-memory session memory fallback (session_id -> list of message dicts)
session_memory: dict = {}

# Priority Gemini models
GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
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
    data: Optional[dict] = None
    error: Optional[dict] = None


# --- 3. Step 1 & 2: Database Retrieval + Reranking ---
def retrieve_relevant_chunks(query_text: str, top_k: int = 5, candidate_count: int = 35):
    """
    Stage 1: Retrieve candidate_count (35) chunks via Supabase Hybrid RRF RPC.
    Stage 2: Cross-Encoder Reranking using BAAI/bge-reranker-v2-m3 -> Top k (5).
    """
    query_vector = embedder.encode(query_text).tolist()

    response = supabase.rpc(
        "match_chunks_hybrid_rrf",
        {
            "query_text": query_text,
            "query_embedding": query_vector,
            "match_count": candidate_count
        }
    ).execute()

    chunks = response.data or []
    if not chunks:
        return []

    # Stage 2 Reranking
    pairs = []
    for c in chunks:
        meta = c.get("metadata", {}) or {}
        title = meta.get("title") or meta.get("sourceTitle", "")
        text = f"{title}\n{c.get('content', '')}".strip()
        pairs.append((query_text, text))

    scores = reranker.predict(pairs)
    for idx, chunk in enumerate(chunks):
        chunk["rerank_score"] = float(scores[idx])

    chunks = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    return chunks[:top_k]


def generate_standalone_query(history: list, current_query: str) -> str:
    """
    Upgrade 2: LLM Standalone Query Rewriter.
    Converts follow-up questions into a self-contained search query.
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
        "You are a search query rewriter for an academic counselor chatbot at IUH University. "
        "Given the conversation context and a follow-up question, rewrite the follow-up question into "
        "a single, self-contained standalone search query in Vietnamese. "
        "Do NOT answer the question. Only output the rewritten search query.\n\n"
        f"Previous User Question: {last_user_msg}\n"
        f"Follow-up Question: {current_query}\n"
        "Standalone Search Query:"
    )

    for m in GEMINI_MODELS:
        try:
            res = gemini_client.models.generate_content(
                model=m,
                contents=rewrite_prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            if res and res.text:
                return res.text.strip()
        except Exception:
            continue

    return f"{last_user_msg} {current_query}"


# --- 4. Database Session History Helpers (Upgrade 3) ---
def get_session_history_from_db(session_id: str) -> list:
    """Loads chat messages from Supabase PostgreSQL tables."""
    try:
        res = supabase.table("messages").select("*").eq("conversation_id", session_id).order("created_at").execute()
        if res.data:
            return [{"role": m["role"], "content": m["content"]} for m in res.data]
    except Exception:
        pass
    return session_memory.get(session_id, [])


def save_turn_to_db(session_id: str, user_content: str, assistant_content: str, title: str):
    """Persists conversation and message turns into PostgreSQL tables."""
    # 1. Ensure conversation exists
    try:
        supabase.table("conversations").upsert({
            "id": session_id,
            "title": title[:50]
        }).execute()
    except Exception:
        pass

    # 2. Save messages
    try:
        supabase.table("messages").insert([
            {"conversation_id": session_id, "role": "user", "content": user_content},
            {"conversation_id": session_id, "role": "assistant", "content": assistant_content}
        ]).execute()
    except Exception:
        pass

    # Backup in memory
    if session_id not in session_memory:
        session_memory[session_id] = []
    session_memory[session_id].append({"role": "user", "content": user_content})
    session_memory[session_id].append({"role": "assistant", "content": assistant_content})


# --- 5. Endpoints ---

@router.get("/sessions", response_model=ApiResult)
async def fetch_sessions():
    """Fetches all persistent sessions from PostgreSQL for sidebar history."""
    try:
        conv_res = supabase.table("conversations").select("*").order("updated_at", desc=True).execute()
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


def build_rag_payload(session_id: str, content: str):
    """Helper to process history, query expansion, retrieval, citations, and prompt."""
    history = get_session_history_from_db(session_id)
    retrieval_query = generate_standalone_query(history, content)

    # 1. Retrieve & Rerank (Top 35 candidates -> Top 5)
    chunks = retrieve_relevant_chunks(retrieval_query, top_k=5, candidate_count=35)

    # 2. Citations & Context
    context_parts = []
    citations = []
    for index, c in enumerate(chunks, 1):
        context_parts.append(f"[Source {index}]: {c['content']}")
        meta = c.get("metadata", {}) or {}

        source_title = meta.get("title") or meta.get("sourceTitle") or "Cẩm nang Sinh viên IUH"
        page = meta.get("page")
        breadcrumbs = meta.get("breadcrumbs")
        chapter = meta.get("chapter_parent")

        if page and str(page) != "None":
            page_or_section = f"Trang {page}"
        elif chapter and str(chapter) != "None":
            page_or_section = str(chapter)
        elif breadcrumbs and str(breadcrumbs) != "None":
            page_or_section = str(breadcrumbs)
        else:
            page_or_section = "Quy chế & Cẩm nang"

        source_url = c.get("source_url") or meta.get("source_url") or meta.get("source")

        citations.append(
            Citation(
                id=f"c_{uuid.uuid4().hex[:8]}",
                sourceTitle=source_title,
                pageOrSection=page_or_section,
                snippet=c["content"][:120].strip() + "...",
                url=source_url if source_url and source_url != "N/A" else None
            )
        )

    context_str = "\n\n".join(context_parts)

    # 3. Formulate Gemini Multi-Turn Contents
    system_instruction = (
        "You are an academic counselor assistant for Industrial University of Ho Chi Minh City (IUH). "
        "Answer the student's question accurately using ONLY the provided context below. "
        "Consider previous conversation context when responding to follow-up questions. "
        "If the answer cannot be found in the context, state that you don't have enough information in the university documents."
    )

    contents = []
    for msg in history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )

    current_turn_prompt = f"Retrieved Document Context:\n{context_str}\n\nStudent Question: {content}"
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=current_turn_prompt)]
        )
    )

    return history, retrieval_query, citations, system_instruction, contents


@router.post("/messages", response_model=ApiResult)
async def send_message(payload: SendMessagePayload):
    try:
        session_id = payload.sessionId or f"s_{uuid.uuid4().hex[:8]}"
        history, retrieval_query, citations, system_instruction, contents = build_rag_payload(session_id, payload.content)

        gemini_response = None
        last_exception = None

        for model_name in GEMINI_MODELS:
            try:
                gemini_response = gemini_client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    )
                )
                if gemini_response and gemini_response.text:
                    break
            except Exception as e:
                last_exception = e
                continue

        if gemini_response and gemini_response.text:
            generated_text = gemini_response.text
        else:
            err_msg = str(last_exception)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                generated_text = (
                    "⚠️ **Thông báo giới hạn API**: Khóa API Gemini hiện tại đã đạt giới hạn truy cập. "
                    "Vui lòng đợi ít phút hoặc cập nhật `GEMINI_API_KEY` trong file `.env`!"
                )
            else:
                generated_text = f"⚠️ Lỗi kết nối AI: {err_msg}"

        # Persist to DB
        save_turn_to_db(session_id, payload.content, generated_text, payload.content)

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
                "sessionId": session_id,
                "message": assistant_message.dict()
            }
        )

    except Exception as e:
        return ApiResult(ok=False, error={"message": str(e)})


@router.post("/messages/stream")
async def send_message_stream(payload: SendMessagePayload):
    """
    Upgrade 4: Streaming Endpoint (Server-Sent Events SSE).
    Streams Gemini response tokens in real-time.
    """
    session_id = payload.sessionId or f"s_{uuid.uuid4().hex[:8]}"

    async def event_generator():
        try:
            history, retrieval_query, citations, system_instruction, contents = build_rag_payload(session_id, payload.content)

            # Send metadata event with citations first
            citations_data = [c.dict() for c in citations]
            yield f"data: {json.dumps({'type': 'metadata', 'sessionId': session_id, 'citations': citations_data})}\n\n"

            accumulated_text = ""
            stream = None
            last_err = None

            for model_name in GEMINI_MODELS:
                try:
                    stream = gemini_client.models.generate_content_stream(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.2,
                        )
                    )
                    break
                except Exception as e:
                    last_err = e
                    continue

            if stream:
                for chunk in stream:
                    if chunk.text:
                        accumulated_text += chunk.text
                        yield f"data: {json.dumps({'type': 'delta', 'text': chunk.text})}\n\n"
                        await asyncio.sleep(0.01)
            else:
                err_str = str(last_err)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    fallback_txt = "⚠️ Giới hạn lượt truy cập API Gemini. Vui lòng đợi ít phút!"
                else:
                    fallback_txt = f"⚠️ Lỗi AI: {err_str}"
                accumulated_text = fallback_txt
                yield f"data: {json.dumps({'type': 'delta', 'text': fallback_txt})}\n\n"

            # Save completed turn to PostgreSQL
            save_turn_to_db(session_id, payload.content, accumulated_text, payload.content)

            # Done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")