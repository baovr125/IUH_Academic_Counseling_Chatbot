#!/usr/bin/env python3
"""
Retrieval Evaluation CLI Script with 2-Stage Reranking for IUH Academic Counseling Chatbot.
Stage 1: Hybrid Search (Vector + Full-Text Keyword + RRF) via Supabase RPC.
Stage 2: Cross-Encoder Reranking via sentence_transformers.CrossEncoder.
"""

import os
import sys
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Find root directory containing .env
project_root = Path(__file__).resolve().parent.parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY environment variables not set.")
    sys.exit(1)

print("⚡ Initializing Supabase client & SentenceTransformer embedder ('bkai-foundation-models/vietnamese-bi-encoder')...")
from supabase import create_client
from sentence_transformers import SentenceTransformer, CrossEncoder

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
embedder = SentenceTransformer("bkai-foundation-models/vietnamese-bi-encoder")
print("✅ First-Stage Embedder loaded (768d).")

# Lazy-loaded reranker
_reranker_instance = None
DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"

def get_reranker(model_name: str = DEFAULT_RERANKER_MODEL):
    global _reranker_instance
    if _reranker_instance is None:
        print(f"⚡ Loading Cross-Encoder Reranker model ('{model_name}')...")
        t0 = time.time()
        _reranker_instance = CrossEncoder(model_name)
        print(f"✅ Reranker loaded in {time.time() - t0:.2f}s.\n")
    return _reranker_instance

def evaluate_query(query_text: str, top_k: int = 5, candidate_count: int = 15, use_reranker: bool = True):
    start_time = time.time()
    
    # -------------------------------------------------------------------------
    # STAGE 1: Hybrid Retrieval (Supabase RPC)
    # -------------------------------------------------------------------------
    query_vector = embedder.encode(query_text).tolist()
    
    try:
        response = supabase.rpc(
            "match_chunks_hybrid_rrf",
            {
                "query_text": query_text,
                "query_embedding": query_vector,
                "match_count": candidate_count
            }
        ).execute()
        chunks = response.data or []
    except Exception as e:
        print(f"❌ RPC Execution Error: {e}")
        return

    stage1_time = (time.time() - start_time) * 1000

    if not chunks:
        print("⚠️  No relevant chunks found in database.")
        return

    # -------------------------------------------------------------------------
    # STAGE 2: Cross-Encoder Reranking
    # -------------------------------------------------------------------------
    stage2_time = 0.0
    if use_reranker:
        t_rerank = time.time()
        reranker = get_reranker()
        
        # Build (query, document) pairs for reranker scoring
        pairs = []
        for c in chunks:
            # Combine title + content for optimal reranker context
            meta = c.get("metadata", {}) or {}
            title = meta.get("title", meta.get("sourceTitle", ""))
            text = f"{title}\n{c.get('content', '')}".strip()
            pairs.append((query_text, text))

        # Predict relevance scores
        scores = reranker.predict(pairs)
        
        # Attach rerank score to chunks
        for idx, chunk in enumerate(chunks):
            chunk["rerank_score"] = float(scores[idx])

        # Sort candidate chunks by rerank score descending
        chunks = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
        stage2_time = (time.time() - t_rerank) * 1000

    total_time = (time.time() - start_time) * 1000
    final_chunks = chunks[:top_k]

    print("=" * 80)
    print(f"🔍 QUERY: \"{query_text}\"")
    print(f"⚙️  Reranking Active: {use_reranker} (Candidate Pool: {len(chunks)} -> Top K: {len(final_chunks)})")
    print(f"⏱️  Stage 1 (Hybrid RRF): {stage1_time:.2f} ms | Stage 2 (Reranker): {stage2_time:.2f} ms | Total: {total_time:.2f} ms")
    print("=" * 80)

    for rank, chunk in enumerate(final_chunks, 1):
        chunk_id = chunk.get("id", "N/A")
        rrf_score = chunk.get("rrf_score", 0.0)
        rerank_score = chunk.get("rerank_score", None)
        content = chunk.get("content", "")
        source_url = chunk.get("source_url", "N/A")
        meta = chunk.get("metadata", {}) or {}

        title = meta.get("title", meta.get("sourceTitle", "N/A"))
        page = meta.get("page", "N/A")
        breadcrumbs = meta.get("breadcrumbs", "")

        score_str = f"RRF Score: {rrf_score:.6f}"
        if rerank_score is not None:
            score_str += f" | 🎯 Rerank Score: {rerank_score:.4f}"

        print(f"\n--- [ RANK {rank} ] --- ({score_str})")
        print(f"📌 Chunk ID   : {chunk_id}")
        print(f"📄 Source Title: {title}")
        if breadcrumbs:
            print(f"🗺️  Breadcrumbs : {breadcrumbs}")
        print(f"🌐 Source URL  : {source_url}")
        print(f"📑 Page/Section: Page {page}")
        print(f"📝 Content:\n{content.strip()}\n")
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Evaluate 2-Stage Hybrid + Reranking RAG Retrieval Results.")
    parser.add_argument("query", nargs="?", type=str, help="Query string to evaluate")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of top chunks to output (default: 5)")
    parser.add_argument("--candidates", "-c", type=int, default=15, help="Candidate pool size for first-stage RRF (default: 15)")
    parser.add_argument("--no-rerank", action="store_true", help="Disable second-stage Cross-Encoder reranking")
    args = parser.parse_args()

    use_reranker = not args.no_rerank

    if args.query:
        evaluate_query(args.query, top_k=args.top_k, candidate_count=args.candidates, use_reranker=use_reranker)
    else:
        print("💡 Interactive Evaluation Mode activated.")
        print("Type a query and press Enter. Type 'exit' or 'q' to quit.\n")
        while True:
            try:
                user_input = input("Enter Query > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "q", "quit"):
                    print("Exiting evaluation CLI.")
                    break
                evaluate_query(user_input, top_k=args.top_k, candidate_count=args.candidates, use_reranker=use_reranker)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting evaluation CLI.")
                break

if __name__ == "__main__":
    main()
