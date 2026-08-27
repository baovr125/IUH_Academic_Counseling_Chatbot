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

def _write_log(session_id: str, query: str, chunks: list) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")
    
    base_log = os.getenv("LOG_DIR", "./logs/academic_chatbot")
    log_dir = os.path.join(base_log, date_str)
    os.makedirs(log_dir, exist_ok=True)
    
    slug = slugify(query, max_words=5)
    file_name = f"{time_str}-{slug}.md" if slug else f"{time_str}.md"
    file_path = os.path.join(log_dir, file_name)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Query: {query}\n\n")
            f.write(f"**Session ID:** {session_id}\n\n")
            f.write(f"**Timestamp:** {now.isoformat()}\n\n")
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

async def log_retrieved_chunks_to_md(session_id: str, query: str, chunks: list) -> str:
    return await asyncio.to_thread(_write_log, session_id, query, chunks)
