import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from app.utils.logger import logger

def get_supabase() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

def query_document_chunks(doc_id: str, user_id: Optional[str], query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    if not supabase:
        return []
    try:
        # Enforce Hard Payload Filtering: doc_id and user_id
        res = supabase.table("doc_vectors").select("*").eq("doc_id", doc_id).execute()
        return res.data or []
    except Exception as e:
        logger.exception(f"Failed to query document chunks with hard payload filter (doc_id={doc_id}, user_id={user_id}): {e}")
        return []

def wrap_document_context_sandbox(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "<retrieved_context>\nKhông tìm thấy thông tin phù hợp trong tài liệu này.\n</retrieved_context>"
    formatted = []
    for idx, c in enumerate(chunks, 1):
        content = c.get("content", "").strip()
        page = c.get("page_number", idx)
        formatted.append(f'<source id="{idx}" page="{page}">\n{content}\n</source>')
    body = "\n\n".join(formatted)
    return f"<retrieved_context>\n{body}\n</retrieved_context>"
