import os
import json
import asyncio
import unicodedata
import re
from datetime import datetime

def slugify(text: str, max_words: int = 5) -> str:
    if not text:
        return "query"
    # Take first 5 words
    words = text.split()[:max_words]
    text = " ".join(words)
    # Remove accents
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    # Lowercase and replace non-alphanumeric with dash
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def _write_log(session_id: str, query: str, chunks: list, past_memories: list = None, retrieval_latency_ms: int = None) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")
    
    base_log = os.getenv("LOG_DIR", "./logs/academic_chatbot")
    log_dir = os.path.join(base_log, date_str)
    os.makedirs(log_dir, exist_ok=True)
    
    slug = slugify(rewritten_query, max_words=5)
    file_name = f"{time_str}-{slug}.md" if slug else f"{time_str}.md"
    file_path = os.path.join(log_dir, file_name)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Query: {original_query}\n\n")
            f.write(f"**Rewrited Query:** {rewritten_query}\n\n")
            f.write(f"**Session ID:** {session_id}\n\n")
            f.write(f"**Timestamp:** {now.isoformat()}\n")
            if retrieval_latency_ms is not None:
                f.write(f"**Retrieval Latency:** {retrieval_latency_ms} ms\n")
            f.write("\n")
            f.write("---\n\n")
            
            if past_memories:
                f.write(f"## Retrieved Long-Term Memory ({len(past_memories)} messages)\n\n")
                for i, m in enumerate(past_memories, 1):
                    f.write(f"### Memory {i}\n")
                    f.write(f"**Role:** {m['role']}\n")
                    f.write(f"**Content:** {m['content']}\n")
                    f.write(f"**Similarity:** {m['similarity']:.4f}\n\n")
                f.write("---\n\n")

            if not chunks:
                f.write("*No chunks retrieved.*\n")
                return
                
            for i, chunk in enumerate(chunks, 1):
                score = chunk.get("rerank_score", chunk.get("similarity", "N/A"))
                f.write(f"## Chunk {i} (Score: {score})\n")
                
                meta = chunk.get("metadata", {})
                if meta:
                    f.write("### Metadata:\n```json\n")
                    f.write(json.dumps(meta, indent=2, ensure_ascii=False) + "\n```\n")
                    
                f.write("### Content:\n")
                content = chunk.get("content", "").strip()
                f.write(f"> {content.replace(chr(10), chr(10) + '> ')}\n\n")
                f.write("---\n\n")
        return file_path
    except Exception as e:
        print(f"Error writing retrieval log: {e}")
        return ""

async def log_retrieved_chunks_to_md(session_id: str, query: str, chunks: list, past_memories: list = None, retrieval_latency_ms: int = None) -> str:
    return await asyncio.to_thread(_write_log, session_id, query, chunks, past_memories, retrieval_latency_ms)

def _write_cache_hit_log(session_id: str, original_query: str, rewritten_query: str, cache_hit_data: dict, latency_ms: int) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")
    
    base_log = os.getenv("LOG_DIR", "./logs/academic_chatbot")
    log_dir = os.path.join(base_log, date_str)
    os.makedirs(log_dir, exist_ok=True)
    
    slug = slugify(rewritten_query, max_words=5)
    file_name = f"{time_str}-CACHE-HIT-{slug}.md" if slug else f"{time_str}-CACHE-HIT.md"
    file_path = os.path.join(log_dir, file_name)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Query: {original_query}\n\n")
            f.write(f"**Rewrited Query:** {rewritten_query}\n\n")
            f.write(f"**Session ID:** {session_id}\n\n")
            f.write(f"**Timestamp:** {now.isoformat()}\n")
            f.write(f"**Cache Status:** HIT\n")
            f.write(f"**Cache Source:** {cache_hit_data.get('source', 'Unknown')}\n")
            f.write(f"**Similarity:** {cache_hit_data.get('similarity', 1.0):.4f}\n")
            estimated_tokens = (len(rewritten_query) + len(cache_hit_data.get('cached_answer', ''))) // 4
            f.write(f"**Retrieval Latency:** {latency_ms} ms\n")
            f.write(f"**Tokens Saved:** ~{estimated_tokens} tokens\n\n")
            f.write("---\n\n")
            f.write(f"## Cached Answer\n")
            f.write(f"> {cache_hit_data.get('cached_answer', '').replace(chr(10), chr(10) + '> ')}\n\n")
        return file_path
    except Exception as e:
        print(f"Error writing cache hit log: {e}")
        return ""

async def log_cache_hit_to_md(session_id: str, original_query: str, rewritten_query: str, cache_hit_data: dict, latency_ms: int) -> str:
    return await asyncio.to_thread(_write_cache_hit_log, session_id, original_query, rewritten_query, cache_hit_data, latency_ms)

def _write_full_log(session_id: str, original_query: str, rewritten_query: str, chunks: list, past_memories: list, retrieval_latency_ms: int, rewrite_latency_ms: int, llm_latency_ms: int, prompt_tokens: int, completion_tokens: int, ai_answer: str, router_model: str = "Unknown", llm_model: str = "Unknown") -> str:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")
    
    base_log = os.getenv("LOG_DIR", "./logs/academic_chatbot")
    log_dir = os.path.join(base_log, date_str)
    os.makedirs(log_dir, exist_ok=True)
    
    slug = slugify(rewritten_query, max_words=5)
    file_name = f"{time_str}-{slug}.md" if slug else f"{time_str}.md"
    file_path = os.path.join(log_dir, file_name)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Query: {original_query}\n\n")
            f.write(f"**Rewrited Query:** {rewritten_query}\n\n")
            f.write(f"**Session ID:** {session_id}\n\n")
            f.write(f"**Timestamp:** {now.isoformat()}\n\n")
            
            f.write("## AI Performance Metrics\n\n")
            if rewrite_latency_ms:
                f.write(f"## {router_model} - **Standalone Router Latency:** {rewrite_latency_ms} ms\n")
            if retrieval_latency_ms:
                f.write(f"## Retrieval - **Latency:** {retrieval_latency_ms} ms\n")
            if llm_latency_ms:
                f.write(f"## {llm_model} - **LLM Generation Latency:** {llm_latency_ms} ms\n")
            if prompt_tokens:
                f.write(f"- **Prompt Tokens:** {prompt_tokens}\n")
                f.write(f"- **Completion Tokens:** {completion_tokens}\n")
                f.write(f"- **Total Tokens:** {prompt_tokens + completion_tokens}\n")
            f.write("\n---\n\n")
            
            f.write("## AI Answer & Thinking Stage\n\n")
            f.write(ai_answer + "\n\n---\n\n")
            
            if past_memories:
                f.write(f"## Retrieved Long-Term Memory ({len(past_memories)} messages)\n\n")
                for idx, m in enumerate(past_memories, 1):
                    role_str = "Sinh viên" if m['role'] == "user" else "Bạn"
                    f.write(f"### Memory {idx}\n")
                    f.write(f"**Role:** {role_str}\n")
                    f.write(f"**Content:** {m['content']}\n")
                    f.write(f"**Similarity:** {m['similarity']:.4f}\n\n")
                f.write("---\n\n")
                
            f.write(f"## Retrieved Context Chunks ({len(chunks)} chunks)\n\n")
            for idx, chunk in enumerate(chunks, 1):
                score = chunk.get("rerank_score", chunk.get("similarity", "N/A"))
                if isinstance(score, float):
                    f.write(f"### Chunk {idx} (Score: {score:.4f})\n")
                else:
                    f.write(f"### Chunk {idx} (Score: {score})\n")
                
                meta = chunk.get("metadata", {})
                if meta:
                    f.write("### Metadata:\n```json\n")
                    import json
                    f.write(json.dumps(meta, indent=2, ensure_ascii=False) + "\n```\n")
                    
                f.write("### Content:\n")
                chunk_content = chunk.get("content", "").strip()
                f.write(f"> {chunk_content.replace(chr(10), chr(10) + '> ')}\n\n")
                f.write("---\n\n")
                
        return file_path
    except Exception as e:
        print(f"Error writing full log: {e}")
        return ""

async def write_full_rag_log_to_md(session_id: str, original_query: str, rewritten_query: str, chunks: list, past_memories: list, retrieval_latency_ms: int, rewrite_latency_ms: int, llm_latency_ms: int, prompt_tokens: int, completion_tokens: int, ai_answer: str, router_model: str = "Unknown", llm_model: str = "Unknown") -> str:
    return await asyncio.to_thread(_write_full_log, session_id, original_query, rewritten_query, chunks, past_memories, retrieval_latency_ms, rewrite_latency_ms, llm_latency_ms, prompt_tokens, completion_tokens, ai_answer, router_model, llm_model)
