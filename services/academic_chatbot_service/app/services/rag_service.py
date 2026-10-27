import os
import uuid
import asyncio
import re
import math
import threading
from typing import List, Optional, Tuple, Union
import json
import redis.asyncio as redis
from cachetools import TTLCache
import warnings

# Suppress ONNX Runtime TensorRT provider warnings (TensorRT not installed)
os.environ.setdefault("ORT_LOGGING_LEVEL_SEVERITY", "3")  # ERROR only
warnings.filterwarnings("ignore", message=".*TensorRT.*")
warnings.filterwarnings("ignore", message=".*libnvinfer.*")

_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = os.getenv("REDIS_PORT", "6379")
        _redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    return _redis_client

from sentence_transformers import SentenceTransformer, CrossEncoder
from google import genai

from app.schemas.chat import Citation
from app.guardrails.query_filter import wrap_context_sandbox
from app.services.chat_service import get_session_history_from_db
from app.services.supabase_client import get_supabase_client
from app.utils.logger import logger

_gemini_client = None
_embedder_model = None
_reranker_model = None
_embedder_lock = threading.Lock()
_reranker_lock = threading.Lock()

DEFAULT_GEMINI_MODELS = "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.5-flash"
# Thứ tự thử lần lượt khi gọi Gemini (model đầu lỗi/hết quota thì sang model sau). Ghi đè: GEMINI_MODELS="a,b,c".
GEMINI_MODELS = [m.strip() for m in os.getenv("GEMINI_MODELS", DEFAULT_GEMINI_MODELS).split(",") if m.strip()]

def get_gemini():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            try:
                _gemini_client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.exception(f"Failed to create Gemini client: {e}")
    return _gemini_client

_embedding_cache = TTLCache(maxsize=500, ttl=1800)

def get_device() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"

def get_embedder():
    global _embedder_model
    with _embedder_lock:
        if _embedder_model is None:
            dev = get_device()
            
            onnx_path = "/app/hf_models/vietnamese-bi-encoder-onnx"
            import os
            loaded_onnx = False
            if os.path.exists(os.path.join(onnx_path, "onnx", "model.onnx")):
                try:
                    logger.info(f"Loading Bi-Encoder model (ONNX Optimized) from {onnx_path} on {dev}")
                    # Explicitly set providers to avoid TensorRT lookup
                    if dev == "cuda":
                        model_kwargs = {"provider": "CUDAExecutionProvider"}
                    else:
                        model_kwargs = {"provider": "CPUExecutionProvider"}
                    _embedder_model = SentenceTransformer(onnx_path, backend="onnx", model_kwargs=model_kwargs)
                    loaded_onnx = True
                except Exception as e:
                    logger.warning(f"Failed to load Bi-Encoder ONNX model: {e}. Falling back to PyTorch model.")
            
            if not loaded_onnx:
                logger.info(f"Loading Bi-Encoder model (PyTorch) on device: {dev}")
                kwargs = {}
                if dev == "cuda":
                    import torch
                    kwargs["model_kwargs"] = {"torch_dtype": torch.float16}
                else:
                    kwargs["model_kwargs"] = {"low_cpu_mem_usage": True}
                _embedder_model = SentenceTransformer("bkai-foundation-models/vietnamese-bi-encoder", device=dev, **kwargs)
    return _embedder_model

def get_reranker():
    global _reranker_model
    with _reranker_lock:
        if _reranker_model is None:
            dev = get_device()
            
            onnx_path = "/app/hf_models/bge-reranker-v2-m3-onnx"
            import os
            loaded_onnx = False
            if os.path.exists(os.path.join(onnx_path, "onnx", "model.onnx")):
                try:
                    logger.info(f"Loading Cross-Encoder model (ONNX Optimized) from {onnx_path} on {dev}")
                    # Explicitly set providers to avoid TensorRT lookup
                    if dev == "cuda":
                        model_kwargs = {"provider": "CUDAExecutionProvider"}
                    else:
                        model_kwargs = {"provider": "CPUExecutionProvider"}
                    _reranker_model = CrossEncoder(onnx_path, backend="onnx", model_kwargs=model_kwargs)
                    loaded_onnx = True
                except Exception as e:
                    logger.warning(f"Failed to load Cross-Encoder ONNX model: {e}. Falling back to PyTorch model.")
            
            if not loaded_onnx:
                logger.info(f"Loading Cross-Encoder model (PyTorch) on device: {dev}")
                kwargs = {}
                if dev == "cuda":
                    import torch
                    kwargs["model_kwargs"] = {"torch_dtype": torch.float16}
                else:
                    kwargs["model_kwargs"] = {"low_cpu_mem_usage": True}
                _reranker_model = CrossEncoder("BAAI/bge-reranker-v2-m3", device=dev, **kwargs)
    return _reranker_model

def preload_models():
    logger.info("Preloading ML Models into VRAM/RAM & Running Warmup...")
    embedder = get_embedder()
    reranker = get_reranker()
    get_gemini()
    try:
        embedder.encode("IUH kiểm tra khởi động", normalize_embeddings=True)
        reranker.predict([("IUH kiểm tra", "Đại học Công nghiệp TP.HCM")])
        logger.info("SentenceTransformers Warmup completed successfully.")
        
        # Warmup Ollama Models
        import httpx
        import os
        llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if llm_provider == "openai":
            ollama_url = os.getenv("OPENAI_BASE_URL", "http://host.docker.internal:11434/v1").replace("/v1", "/api/generate")
            rewriter_model = os.getenv("OLLAMA_REWRITER_MODEL", "QuantTrio/Qwen3.6-35B-A3B-AWQ")
            generator_model = os.getenv("OPENAI_MODEL_NAME", "QuantTrio/Qwen3.6-35B-A3B-AWQ")
            
            logger.info(f"Preloading Ollama Models into VRAM: {rewriter_model} and {generator_model}...")
            with httpx.Client(timeout=120.0) as client:
                client.post(ollama_url, json={"model": rewriter_model, "prompt": "warmup", "stream": False, "keep_alive": "1h", "options": {"num_predict": 1}})
                client.post(ollama_url, json={"model": generator_model, "prompt": "warmup", "stream": False, "keep_alive": "1h", "options": {"num_predict": 1}})
            logger.info("Ollama Models Warmup completed.")
    except Exception as e:
        logger.warning(f"Warmup warning: {e}")


# --- 1.5 Semantic Cache (Phase 2) ---
async def get_query_embedding(query_text: str) -> list:
    if query_text in _embedding_cache:
        return _embedding_cache[query_text]
    embedder = get_embedder()
    query_vector = await asyncio.to_thread(lambda: embedder.encode(query_text).tolist())
    _embedding_cache[query_text] = query_vector
    return query_vector

async def check_semantic_cache(query_text: str, query_embedding: list = None, threshold: float = 0.92) -> Optional[dict]:
    """
    Phase 2: Semantic Cache Lookup (Redis First, then Supabase)
    """
    try:
        # Check Redis exact match first for zero-latency responses
        redis_client = get_redis()
        cache_key = f"semantic_cache:{query_text.strip().lower()}"
        cached_val = await redis_client.get(cache_key)
        if cached_val:
            data = json.loads(cached_val)
            logger.info(f"Redis Cache HIT for query: '{query_text}'")
            return {"cached_answer": data["answer"], "similarity": 1.0, "source": "Redis Exact Match"}
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")

    query_vector = query_embedding if query_embedding else await get_query_embedding(query_text)
    supabase = get_supabase_client()
    if not supabase:
        return None

    # TWO-STAGE CACHE: LOWER THRESHOLD TO 0.6 FOR BI-ENCODER (High Recall)
    # The Supabase RPC currently has LIMIT 1, so we get the top 1 candidate.
    bi_encoder_threshold = min(threshold, 0.60)
    
    try:
        def _call_rpc():
            return supabase.rpc(
                "match_semantic_cache",
                {
                    "query_vec": query_vector,
                    "match_threshold": bi_encoder_threshold
                }
            ).execute()

        response = await asyncio.to_thread(_call_rpc)
        data = response.data or []
        if data and len(data) > 0:
            hit = data[0]
            hit['source'] = 'Supabase pgvector + Cross-Encoder'
            
            canonical_query = hit.get("canonical_query", "")
            bi_score = hit.get('similarity')
            
            # STAGE 2: CROSS-ENCODER RERANKER (High Precision)
            reranker = get_reranker()
            try:
                # reranker.predict expects a list of tuples: [(query, doc)]
                rerank_scores = reranker.predict([(query_text, canonical_query)])
                rerank_score = float(rerank_scores[0])
            except Exception as e:
                logger.error(f"Reranker failed during cache check: {e}")
                return None
                
            logger.info(f"Two-Stage Cache Check -> Bi-Encoder: {bi_score:.4f} | Cross-Encoder: {rerank_score:.4f}")
            
            # We set a strict threshold of 0.80 for the Cross-Encoder
            if rerank_score < 0.80:
                logger.info(f"Semantic Cache MISS: Reranker rejected ({rerank_score:.4f} < 0.80). Pairs: '{query_text}' vs '{canonical_query}'")
                return None
            
            # Double check entities (numbers) just to be absolutely safe
            nums_q = sorted(re.findall(r'\d+', query_text))
            nums_c = sorted(re.findall(r'\d+', canonical_query))
            if nums_q != nums_c:
                logger.info(f"Semantic Cache MISS: Entity mismatch {nums_q} vs {nums_c} despite high rerank score.")
                return None
                
            logger.info(f"Semantic Cache HIT! Validated by Reranker: {rerank_score:.4f}")
            
            # Asynchronously increment hit count
            cache_id = hit.get("id")
            if cache_id:
                async def _increment():
                    try:
                        res = supabase.table("semantic_cache").select("hit_count").eq("id", cache_id).execute()
                        if res.data:
                            curr = res.data[0].get("hit_count", 0)
                            supabase.table("semantic_cache").update({"hit_count": curr + 1}).eq("id", cache_id).execute()
                    except Exception as e:
                        logger.error(f"Failed to increment cache hit: {e}")
                asyncio.create_task(_increment())
                
            return hit
            
    except Exception as e:
        logger.exception(f"Semantic cache lookup failed: {e}")

    return None


async def async_cache_writeback(query_text: str, answer: str, top_doc_score: float, query_embedding: list = None):
    """
    Phase 3: Quality Gate & Asynchronous Write-Back
    Validates LLM answer against RAG context and blocks bad responses from entering cache.
    """
    try:
        # Rule 1: Relevance check (blocks empty context or low-relevance retrievals)
        if top_doc_score < 0.25:
            logger.info(f"Cache writeback skipped: low top_doc_score {top_doc_score}")
            return
            
        # Rule 2: Length check (blocks empty/truncated answers)
        if not (10 <= len(answer) <= 3000):
            logger.info(f"Cache writeback skipped: invalid length {len(answer)}")
            return
            
        # Rule 3: Self-RAG Reflection check (NO hardcoding - dynamic model reflection)
        if "<answer_confidence>" in answer:
            import re
            match_conf = re.search(r'<answer_confidence>\s*(\w+)\s*</answer_confidence>', answer, re.IGNORECASE)
            if match_conf and match_conf.group(1).strip().upper() != "HIGH":
                logger.info(f"Cache writeback skipped: Self-RAG confidence is {match_conf.group(1)}")
                return

        if "<doc_relevance>" in answer:
            import re
            match_doc = re.search(r'<doc_relevance>\s*(\w+)\s*</doc_relevance>', answer, re.IGNORECASE)
            if match_doc and match_doc.group(1).strip().upper() == "NO":
                logger.info("Cache writeback skipped: Self-RAG doc_relevance is NO")
                return
                    
        query_vector = query_embedding if query_embedding else await get_query_embedding(query_text)
        
        # Save to Redis for O(1) exact lookups later
        try:
            redis_client = get_redis()
            cache_key = f"semantic_cache:{query_text.strip().lower()}"
            await redis_client.setex(
                cache_key, 
                86400, # 24 hours TTL
                json.dumps({"answer": answer, "score": top_doc_score})
            )
        except Exception as e:
            logger.warning(f"Redis cache write failed: {e}")

        supabase = get_supabase_client()
        if not supabase:
            return
            
        from datetime import datetime, timedelta, timezone
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        def _insert():
            return supabase.table("semantic_cache").insert({
                "canonical_query": query_text,
                "query_embedding": query_vector,
                "cached_answer": answer,
                "retrieval_score": top_doc_score,
                "expires_at": expires_at.isoformat()
            }).execute()
            
        await asyncio.to_thread(_insert)
        logger.info(f"Cache writeback success for query: '{query_text}'")
    except Exception as e:
        logger.exception(f"Cache writeback failed: {e}")

async def invalidate_semantic_cache():
    """
    Gọi khi pipeline re-index document_chunks để xóa cache cũ.
    """
    try:
        redis_client = get_redis()
        keys = await redis_client.keys("semantic_cache:*")
        if keys:
            await redis_client.delete(*keys)
            
        supabase = get_supabase_client()
        if supabase:
            def _delete():
                return supabase.table("semantic_cache").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            await asyncio.to_thread(_delete)
        logger.info("Đã xóa hoàn toàn Semantic Cache (Redis + Supabase).")
    except Exception as e:
        logger.exception(f"Lỗi khi xóa Semantic Cache: {e}")


# --- 2. Hybrid Retrieval & Multi-Query Reranking ---
RERANKER_THRESHOLD: float = 0.20
GOOD_SCORE_THRESHOLD: float = 0.65

def get_adaptive_candidate_count(estimated_score: float = 0.5) -> int:
    """
    Self-RAG Dynamic Candidate Count:
    Adjusts candidate retrieval count dynamically based on relevance quality:
    - High quality (score >= 0.80): 30 candidates (accelerates reranker)
    - Moderate quality (0.50 <= score < 0.80): 50 candidates (default balanced)
    - Low/uncertain quality (score < 0.50): 70 candidates (high recall)
    """
    if estimated_score >= 0.80:
        return 30
    if estimated_score >= 0.50:
        return 50
    return 70

async def retrieve_relevant_chunks_multi(
    queries: List[str], 
    top_k: int = 8, 
    candidate_count: int = 50
) -> Tuple[List[dict], float]:
    """
    Multi-Query Hybrid Retrieval & Query-Specific Cross-Encoder Reranking:
    1. Runs parallel Supabase Hybrid RRF RPC for each subquery via asyncio.gather.
    2. Reranks candidate chunks with their specific matching subquery using bge-reranker-v2-m3.
    3. Enforces dynamic quota per subquery (floor 2 per query, ceiling max 6 or 10, threshold >= 0.65).
    4. De-duplicates and expands neighbor window context.
    Returns: (expanded_chunks, top_doc_score)
    """
    if not queries:
        return [], 0.0

    # Clean and limit max 4 sub-queries
    valid_queries = [q.strip() for q in queries if q and q.strip()][:4]
    if not valid_queries:
        return [], 0.0

    supabase = get_supabase_client()
    if not supabase:
        return [], 0.0

    num_q = len(valid_queries)
    # Dynamic Quota Allocation based on agreed rules:
    # 1 query: default 3, max 5 (tối ưu Lost-in-the-Middle cho tiếng Việt)
    # 2 queries: default 4 (2/query), max 5
    # 3 queries: default 6 (2/query), max 8
    # 4 queries: default 8 (2/query), max 8
    floor_per_query = 2 if num_q > 1 else 3
    if num_q == 1:
        max_ceiling = 5
        max_per_query = 5
    elif num_q == 2:
        max_ceiling = 5
        max_per_query = 3
    elif num_q == 3:
        max_ceiling = 8
        max_per_query = 3
    else:  # num_q == 4
        max_ceiling = 8
        max_per_query = 3

    # Step 1: Concurrently generate query embeddings for all subqueries
    query_embeddings = await asyncio.gather(*(get_query_embedding(q) for q in valid_queries))

    # Step 2: Retrieve candidate chunks concurrently for each query
    async def _fetch_candidates(q_text: str, q_vec: list):
        try:
            def _call_rpc():
                return supabase.rpc(
                    "match_chunks_hybrid_rrf",
                    {
                        "query_text": q_text,
                        "query_embedding": q_vec,
                        "match_count": candidate_count
                    }
                ).execute()
            response = await asyncio.to_thread(_call_rpc)
            return response.data or []
        except Exception as e:
            logger.exception(f"Hybrid RRF retrieval failed for subquery '{q_text[:30]}...': {e}")
            return []

    candidates_per_query = await asyncio.gather(
        *(_fetch_candidates(q, vec) for q, vec in zip(valid_queries, query_embeddings))
    )

    reranker = get_reranker()
    batch_size = 32 if get_device() == "cuda" else 8

    # Step 3: Query-specific Reranking for each subquery
    selected_chunks_by_query = []
    all_top_scores = []
    raw_max_score = 0.0

    for q_idx, (q_text, chunks) in enumerate(zip(valid_queries, candidates_per_query)):
        if not chunks:
            continue

        pairs = []
        for c in chunks:
            meta = c.get("metadata", {}) or {}
            title = meta.get("title") or meta.get("sourceTitle", "")
            text = f"{title}\n{c.get('content', '')}".strip()
            pairs.append((q_text, text))

        try:
            scores = await asyncio.to_thread(lambda: reranker.predict(pairs, batch_size=batch_size))
            scored_chunks = []
            for idx, chunk in enumerate(chunks):
                c_copy = dict(chunk)
                score = float(scores[idx])
                # CrossEncoder (BAAI/bge-reranker-v2-m3) already outputs probabilities in [0.0, 1.0].
                # If a model or mock returns raw logits outside [0.0, 1.0], apply Sigmoid once.
                if score < 0.0 or score > 1.0:
                    score = 1.0 / (1.0 + math.exp(-score))
                c_copy["rerank_score"] = score
                c_copy["matched_subquery"] = q_text
                scored_chunks.append(c_copy)

            # Sort descending by rerank_score
            scored_chunks = sorted(scored_chunks, key=lambda x: x["rerank_score"], reverse=True)
            if scored_chunks:
                raw_max_score = max(raw_max_score, scored_chunks[0]["rerank_score"])
            
            # Giữ các chunk có điểm rerank >= RERANKER_THRESHOLD
            valid_chunks = [c for c in scored_chunks if c["rerank_score"] >= RERANKER_THRESHOLD]
            if not valid_chunks:
                continue

            all_top_scores.append(valid_chunks[0]["rerank_score"])

            # SOTA Parent-Aware Quota Selection:
            # Group candidate chunks by parent section, preserving the highest-scoring child chunk
            # for each distinct parent so that sibling child chunks do not crowd out vital sections.
            seen_parents = set()
            distinct_parent_chunks = []
            for chunk in valid_chunks:
                p_id = chunk.get("parent_id") or chunk.get("id")
                if p_id not in seen_parents:
                    seen_parents.add(p_id)
                    distinct_parent_chunks.append(chunk)

            # Filter distinct parent chunks with good score (>= 0.65)
            good_parent_chunks = [c for c in distinct_parent_chunks if c["rerank_score"] >= GOOD_SCORE_THRESHOLD]

            # Quota selection based on distinct parent sections:
            # If good parent sections >= floor_per_query, take up to max_per_query distinct parents.
            # Otherwise, fallback to take at least floor_per_query distinct parents (if available).
            if len(good_parent_chunks) >= floor_per_query:
                picked = good_parent_chunks[:max_per_query]
            else:
                picked = distinct_parent_chunks[:floor_per_query]

            selected_chunks_by_query.append(picked)
        except Exception as e:
            logger.exception(f"Reranking failed for subquery '{q_text}': {e}")
            continue

    # Step 4: Merge & Deduplicate across subqueries in round-robin fashion
    merged_map = {}
    max_group_len = max((len(group) for group in selected_chunks_by_query), default=0)
    for i in range(max_group_len):
        for group in selected_chunks_by_query:
            if i < len(group):
                chunk = group[i]
                c_id = chunk.get("id")
                if c_id not in merged_map:
                    merged_map[c_id] = chunk
                else:
                    # Keep higher rerank_score if duplicate
                    if chunk["rerank_score"] > merged_map[c_id]["rerank_score"]:
                        merged_map[c_id] = chunk

    # Step 5: SOTA Parent Document Retrieval (Small-to-Big Collapse)
    # Collapse multiple child chunks from the same parent section into a single cohesive Parent record
    parent_map = {}
    for chunk in merged_map.values():
        p_id = chunk.get("parent_id") or chunk.get("id")
        if p_id not in parent_map:
            p_item = dict(chunk)
            if chunk.get("parent_content"):
                p_item["child_content"] = chunk.get("content", "")
                p_item["content"] = chunk["parent_content"]
            parent_map[p_id] = p_item
        else:
            # Update with highest rerank_score and matching subquery among sibling chunks
            if chunk.get("rerank_score", 0) > parent_map[p_id].get("rerank_score", 0):
                parent_map[p_id]["rerank_score"] = chunk["rerank_score"]
                parent_map[p_id]["matched_subquery"] = chunk.get("matched_subquery")
                if chunk.get("content"):
                    parent_map[p_id]["child_content"] = chunk.get("content", "")

    final_chunks = list(parent_map.values())
    final_chunks = sorted(final_chunks, key=lambda x: x["rerank_score"], reverse=True)[:max_ceiling]

    top_doc_score = max(all_top_scores) if all_top_scores else raw_max_score

    if final_chunks:
        logger.info(f"Multi-Query ({num_q} queries): Selected {len(final_chunks)} parent sections, Top Score: {top_doc_score:.4f}")

    if not final_chunks or top_doc_score < RERANKER_THRESHOLD:
        logger.warning(f"All chunks rejected. Top score {top_doc_score:.4f} is below threshold {RERANKER_THRESHOLD}.")
        return [], 0.0

    return final_chunks, top_doc_score

async def retrieve_relevant_chunks(query_text: str, query_embedding: list = None, top_k: int = 5, candidate_count: int = 30):
    """Backward-compatible wrapper for single query retrieval."""
    chunks, _ = await retrieve_relevant_chunks_multi([query_text], top_k=top_k, candidate_count=candidate_count)
    return chunks

async def generate_standalone_query(history: list, current_query: str) -> Tuple[bool, List[str], str, str, str]:
    """
    Module Adaptive Query Rewriter & Router (Slim):
    1. Đánh giá nhu cầu truy xuất CSDL (need_retrieval: true/false).
    2. Phân loại ý định vào 1 trong 7 intents.
    3. Phân rã câu hỏi kép thành 1 đến tối đa 4 sub-queries độc lập.
    4. Kiểm soát an toàn (Guardrail / Rejected query).
    Returns: (need_retrieval: bool, queries: List[str], router_model: str, intent: str, reason: str)
    """
    last_user_msg = None
    if history:
        for msg in reversed(history):
            if msg['role'] == 'user':
                last_user_msg = msg['content']
                break

    context_str = f"Lịch sử chat gần nhất:\n- Sinh viên: {last_user_msg}\n" if last_user_msg and last_user_msg != current_query else ""

    rewrite_prompt = (
        "Bạn là AI Router & Query Rewriter cho Chatbot Tư vấn Học vụ Đại học IUH.\n"
        "Phân tích câu hỏi của sinh viên và trả về chuỗi JSON gồm: 'need_retrieval', 'intent', 'queries'.\n\n"
        "QUY TẮC:\n"
        "1. GUARDRAIL: Nếu câu hỏi quấy phá, vi phạm an toàn, hoặc ngoài lề không liên quan trường học:\n"
        "   -> 'need_retrieval': false, 'intent': 'GENERAL', 'queries': [\"REJECTED_QUERY\"].\n"
        "2. ĐÁNH GIÁ NHU CẦU: 'need_retrieval': false khi chỉ chào hỏi xã giao, cảm ơn, tán gẫu; 'need_retrieval': true khi hỏi về quy chế, thủ tục, điểm, học phí, v.v.\n"
        "3. PHÂN LOẠI INTENT: Chọn 1 trong 7 nhóm: PROCEDURE, REGULATION, CRISIS, GENERAL, ADVISING, COMPLAINT, TECH_SUPPORT.\n"
        "4. TÌM KIẾM (queries):\n"
        "   - Nếu need_retrieval=false: queries=[].\n"
        "   - Nếu câu hỏi có nhiều ý riêng biệt: Tách thành 2 đến tối đa 3 câu tìm kiếm độc lập.\n"
        "   - Nếu câu hỏi chỉ có 1 ý: Giữ nguyên từ khóa cốt lõi. TUYỆT ĐỐI KHÔNG thêm từ đồng nghĩa suy diễn (như 'tiêu chuẩn', 'hướng dẫn'), KHÔNG gắn thêm chữ 'IUH'.\n\n"
        "VÍ DỤ MẪU:\n"
        "1. Câu kép đa ý:\n"
        "Sinh viên: Em muốn bảo lưu kỳ này và rút học phí thì làm thế nào?\n"
        "JSON: {\"need_retrieval\": true, \"intent\": \"PROCEDURE\", \"queries\": [\"điều kiện hồ sơ xin tạm dừng tiến độ học tập bảo lưu kết quả\", \"quy định rút và hoàn trả học phí khi tạm dừng học tập\"]}\n\n"
        "2. Xã giao / cảm ơn:\n"
        "Sinh viên: Dạ em hiểu rồi, cảm ơn ad nhiều ạ!\n"
        "JSON: {\"need_retrieval\": false, \"intent\": \"GENERAL\", \"queries\": []}\n\n"
        "3. Câu đơn bảo toàn từ khóa gốc:\n"
        "Sinh viên: Điều kiện xét học bổng khuyến khích học tập?\n"
        "JSON: {\"need_retrieval\": true, \"intent\": \"REGULATION\", \"queries\": [\"điều kiện xét học bổng khuyến khích học tập\"]}\n\n"
        "THỰC HÀNH:\n"
        f"{context_str}"
        f"Sinh viên: {current_query}\n"
        "JSON:"
    )

    from app.services.llm_providers import get_rewriter_provider
    provider = get_rewriter_provider()
    
    system_inst = "Chỉ trả về chuỗi JSON hợp lệ chứa các trường 'need_retrieval', 'intent', 'queries', KHÔNG kèm theo bất kỳ văn bản giải thích nào khác."
    res = await provider.generate_text(prompt=rewrite_prompt, system_instruction=system_inst, temperature=0.0)

    if res:
        import json
        start_idx = res.find("{")
        end_idx = res.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_str = res[start_idx:end_idx+1]
            try:
                data = json.loads(json_str)
                reason = data.get("reason", "")
                need_retrieval = bool(data.get("need_retrieval", True))
                raw_queries = data.get("queries", [])
                if isinstance(raw_queries, str):
                    raw_queries = [raw_queries]
                intent = data.get("intent", "GENERAL").upper()

                # Handle Rejected / Off-topic
                if any("REJECTED_QUERY" in str(q).upper() for q in raw_queries):
                    return False, ["REJECTED_QUERY"], provider.last_used_model, intent, reason

                if not need_retrieval:
                    return False, [], provider.last_used_model, intent, reason

                clean_queries = [str(q).strip() for q in raw_queries if str(q).strip()]
                if not clean_queries:
                    clean_queries = [current_query]

                return True, clean_queries[:4], provider.last_used_model, intent, reason
            except Exception as e:
                logger.warning(f"Failed to parse extracted JSON: {e}. String: {json_str}")

    # Fallback in case of parsing or generation failure
    return True, [current_query], provider.last_used_model, "GENERAL", "Fallback parsing error"



 


def build_dynamic_system_instruction(intent: str, memory_str: str, context_str: str, content: str) -> str:
    from app.prompts.prompt_templates import BASE_PERSONA_AND_SAFETY, INTENT_RULES, INTENT_FEW_SHOTS
    
    intent = intent.upper()
    if intent not in INTENT_RULES:
        intent = "GENERAL"
        
    base_prompt = BASE_PERSONA_AND_SAFETY
    rules = INTENT_RULES.get(intent, "")
    few_shots = INTENT_FEW_SHOTS.get(intent, "")
    
    # Đảm bảo khối context chỉ bọc đúng 1 lần thẻ <retrieved_context>
    if "<retrieved_context>" in context_str:
        retrieved_block = context_str
    else:
        retrieved_block = f"<retrieved_context>\n{context_str}\n</retrieved_context>"

    final_prompt = f"{base_prompt}\n\n{rules}\n\n{few_shots}\n\n"
    final_prompt += f"{memory_str}\n\n{retrieved_block}\n\n"
    final_prompt += f"<user_query>\n{content}\n</user_query>"
    return final_prompt

async def retrieve_past_memory(session_id: str, query_embedding: list, current_query: str, match_threshold: float = 0.8, limit: int = 3) -> list:
    if not query_embedding:
        return []
    try:
        from app.services.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        if not supabase:
            return []
            
        def _rpc():
            return supabase.rpc("match_past_messages", {
                "query_vec": query_embedding,
                "match_threshold": match_threshold,
                "match_count": limit,
                "p_session_id": session_id
            }).execute()
            
        import asyncio
        res = await asyncio.to_thread(_rpc)
        if res.data:
            return [m for m in res.data if m['content'] != current_query]
        return []
    except Exception as e:
        logger.warning(f"Failed to retrieve past memory: {e}")
        return []

async def build_rag_payload(session_id: str, content: str, retrieval_queries: Union[List[str], str], query_embedding: list = None, intent: str = "GENERAL"):
    history = await asyncio.to_thread(get_session_history_from_db, session_id)
    filtered_history = [
        msg for msg in history
        if not (msg["role"] == "user" and msg["content"] == content)
    ]

    queries_list = [retrieval_queries] if isinstance(retrieval_queries, str) else retrieval_queries
    queries_list = [q.strip() for q in queries_list if q and q.strip()]
    if not queries_list:
        queries_list = [content]

    import time
    t0 = time.perf_counter()
    chunks, top_doc_score = await retrieve_relevant_chunks_multi(queries_list)
    retrieval_latency_ms = int((time.perf_counter() - t0) * 1000)

    # --- HYBRID MEMORY: Fetch semantic past messages using primary query embedding ---
    primary_emb = query_embedding
    if not primary_emb:
        primary_emb = await get_query_embedding(queries_list[0])
    past_memories = await retrieve_past_memory(session_id, primary_emb, content)

    memory_str = ""
    if past_memories:
        memory_str = "\n\n[KÝ ỨC DÀI HẠN TỪ LỊCH SỬ CHAT TRƯỚC ĐÂY KHỚP VỚI NGỮ CẢNH]\n"
        for m in past_memories:
            role_vi = "Sinh viên" if m['role'] == "user" else "Bạn"
            memory_str += f"- {role_vi} từng nói: {m['content']}\n"
        memory_str += "Hãy dùng thông tin này nếu nó giúp giải quyết câu hỏi hiện tại của sinh viên.\n"

    rag_data = {
        'chunks': chunks,
        'past_memories': past_memories,
        'retrieval_latency_ms': retrieval_latency_ms,
        'queries': queries_list
    }

    citations = []
    chunk_ids = []
    for index, c in enumerate(chunks, 1):
        chunk_ids.append(c.get("id"))
        meta = c.get("metadata", {}) or {}

        source_title = meta.get("title") or meta.get("sourceTitle") or "Cẩm nang Sinh viên IUH"
        page = meta.get("page")
        breadcrumbs = meta.get("breadcrumbs")
        chapter = meta.get("chapter_parent")

        headers = meta.get("headers", [])
        if page and str(page) != "None":
            page_or_section = f"Trang {page}"
        elif headers and len(headers) > 0:
            clean_header = headers[-1].replace('#', '').replace('*', '').replace('\n', ' ').strip()
            page_or_section = clean_header if clean_header else "Quy định IUH"
        elif breadcrumbs and len(breadcrumbs) > 0:
            if isinstance(breadcrumbs, str):
                parts = [p.strip() for p in breadcrumbs.split(">")]
                page_or_section = " > ".join(parts[-2:]) if len(parts) > 1 else parts[0]
            else:
                page_or_section = str(breadcrumbs)
        elif chapter:
            page_or_section = str(chapter)
        else:
            page_or_section = "Thông tin chung"

        chunk_content = c.get('content', '')
        snippet = chunk_content[:140] + "..." if len(chunk_content) > 140 else chunk_content

        citations.append(Citation(
            id=f"c_{uuid.uuid4().hex[:8]}",
            sourceTitle=source_title,
            pageOrSection=page_or_section,
            snippet=snippet,
            url=meta.get("source_url")
        ))

    context_str = wrap_context_sandbox(chunks, user_query=content) if chunks else "<retrieved_context>\nKhông tìm thấy tài liệu phù hợp trong CSDL.\n</retrieved_context>"

    system_instruction = build_dynamic_system_instruction(intent, memory_str, context_str, content)

    contents = []
    for turn in filtered_history[-6:]:
        role = "user" if turn["role"] == "user" else "model"
        contents.append({"role": role, "content": turn["content"]})
    contents.append({"role": "user", "content": content})

    primary_query_str = queries_list[0] if queries_list else content
    return history, primary_query_str, citations, chunk_ids, system_instruction, contents, top_doc_score, rag_data
