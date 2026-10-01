import asyncio
import json
import os
import sys
import numpy as np
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import generate_standalone_query, retrieve_relevant_chunks
from app.services.llm_generation_service import get_query_embedding

TEST_DATA_DIR = "tests/test_data"
REPORT_DIR = "tests/reports"
os.makedirs(REPORT_DIR, exist_ok=True)

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

async def run_semantic_cache_test():
    print("Running Semantic Cache Tests...")
    with open(f"{TEST_DATA_DIR}/semantic_cache_test.json", "r", encoding="utf-8") as f:
        cases = json.load(f)
    report = []
    passed = 0
    from app.services.rag_service import get_reranker
    for case in cases:
        emb1 = await get_query_embedding(case["initial"])
        emb2 = await get_query_embedding(case["subsequent"])
        sim = cosine_similarity(emb1, emb2)
        
        actual = "miss"
        rerank_score = 0.0
        
        # TWO-STAGE CACHE SIMULATION
        if sim >= 0.60:
            reranker = get_reranker()
            try:
                rerank_scores = reranker.predict([(case["subsequent"], case["initial"])])
                rerank_score = float(rerank_scores[0])
                if rerank_score >= 0.80:
                    actual = "hit"
            except Exception:
                pass
        
        is_pass = (actual == case["expected"])
        if is_pass: passed += 1
        case_report = {
            "id": case.get("id"),
            "initial": case["initial"],
            "subsequent": case["subsequent"],
            "expected": case["expected"],
            "actual": actual,
            "cosine_similarity": float(sim), "rerank_score": rerank_score,
            "pass": is_pass
        }
        report.append(case_report)
    out_file = f"{REPORT_DIR}/semantic_cache_test_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": {"total": len(cases), "passed": passed, "accuracy": passed/len(cases)}, "results": report}, f, ensure_ascii=False, indent=2)
    print(f"Saved report to {out_file}\n")

async def run_injection_test():
    print("Running Injection & Guardrail Tests...")
    with open(f"{TEST_DATA_DIR}/injection_guardrail_test.json", "r", encoding="utf-8") as f:
        cases = json.load(f)
    report = []
    passed = 0
    for case in cases:
        rewritten = await generate_standalone_query([], case["query"])
        actual_status = "blocked_by_guardrail" if "<FALSE>" in rewritten else "allowed"
        
        expected = case.get("expected", "")
        if not expected:
            expected = "allowed" if "normal" in case.get("type", "") else "blocked_by_guardrail"
            
        is_pass = False
        if "blocked" in expected and actual_status == "blocked_by_guardrail":
            is_pass = True
        elif "allowed" in expected and actual_status == "allowed":
            is_pass = True
            
        if is_pass: passed += 1
        case_report = {
            "id": case.get("id"),
            "query": case["query"],
            "expected": expected,
            "actual": actual_status,
            "pass": is_pass
        }
        report.append(case_report)
    out_file = f"{REPORT_DIR}/injection_guardrail_test_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": {"total": len(cases), "passed": passed, "accuracy": passed/len(cases)}, "results": report}, f, ensure_ascii=False, indent=2)
    print(f"Saved report to {out_file}\n")

async def run_retrieval_test(file_name):
    print(f"Running Retrieval Test: {file_name}...")
    with open(f"{TEST_DATA_DIR}/{file_name}.json", "r", encoding="utf-8") as f:
        cases = json.load(f)
    report = []
    for case in cases:
        query = case["query"]
        rewritten = await generate_standalone_query([], query)
        clean_query = rewritten.replace("<TRUE>", "").replace("</TRUE>", "").replace("<FALSE>", "").strip()
        emb = await get_query_embedding(clean_query)
        chunks = await retrieve_relevant_chunks(clean_query, emb, top_k=3)
        extracted_contexts = []
        for c in chunks:
            extracted_contexts.append({
                "score": c.get("similarity", 0),
                "content_snippet": c.get("content", "")[:100] + "..."
            })
        case_report = {
            "id": case.get("id"),
            "query": query,
            "rewritten": clean_query,
            "retrieved_chunks": extracted_contexts
        }
        report.append(case_report)
    out_file = f"{REPORT_DIR}/{file_name}_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": {"total": len(cases)}, "results": report}, f, ensure_ascii=False, indent=2)
    print(f"Saved report to {out_file}\n")

async def main():
    await run_semantic_cache_test()
    await run_injection_test()
    await run_retrieval_test("cross_document_test")
    await run_retrieval_test("tabular_data_test")
    await run_retrieval_test("temporal_conflict_test")
    print("All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
