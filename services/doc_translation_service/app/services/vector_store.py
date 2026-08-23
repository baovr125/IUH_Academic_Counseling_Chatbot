import os
import re
from typing import List, Dict, Any, Optional
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None
from supabase import create_client, Client
from app.utils.logger import logger

_model_instance = None

# --- CẤU HÌNH MO-HINH EMBEDDING BGE-M3 (1024 DIMENSIONS) ---
MODEL_NAME = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

def get_device() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"

def get_embedding_model() -> Optional[SentenceTransformer]:
    global _model_instance
    if _model_instance is None and SentenceTransformer is not None:
        dev = get_device()
        logger.info(f"🔄 Đang khởi tạo mô hình nhúng BAAI/bge-m3 ({EMBEDDING_DIM}d) trên thiết bị: {dev.upper()}...")
        kwargs = {}
        if dev == "cuda":
            import torch
            kwargs["model_kwargs"] = {"torch_dtype": torch.float16}
        else:
            kwargs["model_kwargs"] = {"low_cpu_mem_usage": True}
        try:
            _model_instance = SentenceTransformer(MODEL_NAME, device=dev, **kwargs)
        except Exception as e:
            logger.warning(f"Could not load BGE-M3 model: {e}")
    return _model_instance

def get_supabase() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

def inject_metadata_prefix(child_text: str, parent_title: str, ancestors: List[str]) -> str:
    """
    Thuật toán inject_meta prefixing: ghép thông tin đường dẫn tiêu đề vào đầu đoạn trước khi nhúng vector.
    """
    ancestor_path = " > ".join(ancestors) if ancestors else ""
    if ancestor_path and parent_title:
        full_path = f"{ancestor_path} > {parent_title}"
    else:
        full_path = parent_title or ancestor_path or "Tổng quan"
        
    prefix = f"[Mục: {full_path}] "
    return prefix + child_text

def compute_embedding(text: str) -> List[float]:
    model = get_embedding_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()

def upsert_doc_vectors(
    doc_id: str,
    user_id: str,
    child_chunks: List[Dict[str, Any]]
) -> int:
    """
    Upsert danh sách Chunks vào Supabase PostgreSQL table 'doc_vectors'.
    """
    supabase = get_supabase()
    if not supabase:
        logger.warning("Supabase Client chưa được khởi tạo, bỏ qua bước upsert vector.")
        return 0

    records = []
    model = get_embedding_model()

    # Calculate embeddings in batch for efficiency
    texts_to_embed = []
    for chunk in child_chunks:
        injected = inject_metadata_prefix(
            child_text=chunk["content"],
            parent_title=chunk.get("parent_title", ""),
            ancestors=chunk.get("ancestors", [])
        )
        chunk["injected_content"] = injected
        texts_to_embed.append(injected)

    logger.info(f"⚡ Đang tính toán Vector BGE-M3 (1024d) cho {len(texts_to_embed)} chunks...")
    embeddings = model.encode(texts_to_embed, normalize_embeddings=True)

    for idx, chunk in enumerate(child_chunks):
        vec = embeddings[idx].tolist()
        records.append({
            "doc_id": doc_id,
            "user_id": user_id,
            "parent_id": chunk.get("parent_id"),
            "page_number": chunk.get("page_number", 1),
            "chunk_index": chunk.get("chunk_index", idx + 1),
            "content": chunk.get("content", ""),
            "translated_content": chunk.get("translated_content", chunk.get("content", "")),
            "injected_content": chunk.get("injected_content", ""),
            "metadata": {
                "parent_title": chunk.get("parent_title"),
                "ancestors": chunk.get("ancestors", [])
            },
            "embedding": vec
        })

    try:
        # Use UPSERT to avoid index bloat
        res = supabase.table("doc_vectors").upsert(
            records, 
            on_conflict="doc_id,user_id,chunk_index"
        ).execute()
        inserted_count = len(res.data) if res.data else 0
        logger.info(f"✅ Đã upsert thành công {inserted_count} vector chunks (1024d) vào Supabase.")
        return inserted_count
    except Exception as e:
        logger.exception(f"Lỗi khi upsert doc_vectors vào Supabase: {e}")
        return 0

def query_document_chunks(
    doc_id: str,
    user_id: Optional[str],
    query_text: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Truy vấn Vector Search trên Supabase doc_vectors áp dụng HARD PAYLOAD FILTERING:
    WHERE doc_id = '...' AND user_id = '...'
    """
    supabase = get_supabase()
    if not supabase:
        return []

    try:
        query_vec = compute_embedding(query_text)
        
        # Hard Payload Filtering query
        # Calling Supabase rpc match_doc_vectors if available, or direct filter query
        rpc_res = supabase.rpc("match_doc_vectors", {
            "query_embedding": query_vec,
            "filter_doc_id": doc_id,
            "filter_user_id": user_id or "anonymous",
            "match_threshold": 0.2,
            "match_count": top_k
        }).execute()

        if rpc_res and rpc_res.data:
            return rpc_res.data
    except Exception:
        # Fallback direct table query with filter
        pass

    try:
        res = supabase.table("doc_vectors") \
            .select("id, doc_id, user_id, page_number, chunk_index, content, translated_content, injected_content, metadata") \
            .eq("doc_id", doc_id) \
            .execute()
        return res.data[:top_k] if res.data else []
    except Exception as e:
        logger.exception(f"Lỗi khi truy vấn vector chunks cho doc_id={doc_id}: {e}")
        return []

def wrap_document_context_sandbox(chunks: List[Dict[str, Any]]) -> str:
    """
    Bọc dữ liệu trích xuất từ Vector DB vào thẻ XML <retrieved_context> chống Prompt Injection.
    """
    if not chunks:
        return "<retrieved_context>\nKhông tìm thấy thông tin phù hợp trong tài liệu này.\n</retrieved_context>"

    formatted = []
    for idx, c in enumerate(chunks, 1):
        content = c.get("translated_content") or c.get("content", "").strip()
        page = c.get("page_number", idx)
        formatted.append(f'<source id="{idx}" page="{page}">\n{content}\n</source>')
        
    body = "\n\n".join(formatted)
    return f"<retrieved_context>\n{body}\n</retrieved_context>"
