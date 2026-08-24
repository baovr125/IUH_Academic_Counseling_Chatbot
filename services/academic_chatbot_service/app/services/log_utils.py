import os
import json
import asyncio
from datetime import datetime

def _write_log(session_id: str, query: str, chunks: list):
    log_dir = "/app/logs/academic_chatbot"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_session = "".join([c if c.isalnum() else "_" for c in session_id])
    file_path = os.path.join(log_dir, f"{timestamp}_{safe_session}.md")
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Query: {query}\n\n")
            f.write(f"**Session ID:** {session_id}\n\n")
            f.write(f"**Timestamp:** {datetime.now().isoformat()}\n\n")
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
    except Exception as e:
        print(f"Error writing retrieval log: {e}")

async def log_retrieved_chunks_to_md(session_id: str, query: str, chunks: list):
    await asyncio.to_thread(_write_log, session_id, query, chunks)
