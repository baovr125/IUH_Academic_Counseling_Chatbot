"""Thí nghiệm E1: chất lượng truy xuất theo 5 cấu hình (Bảng 5.3). CHỈ ĐỌC Supabase, không gọi LLM.

C1  chỉ vector            hàm match_chunks_hybrid_rrf với query_text rỗng (nhánh toàn văn không có kết quả)
C2  chỉ toàn văn          PostgREST websearch_to_tsquery trên cột fts_tokens (giống nhánh toàn văn của hàm RPC), xếp hạng lại
                          bằng BM25 tính trong Python vì REST không trả ts_rank_cd
C3  lai (RRF)             hàm match_chunks_hybrid_rrf đầy đủ, 50 ứng viên
C4  lai + xếp hạng lại    C3 rồi Cross-Encoder bge-reranker-v2-m3 chấm lại 50 ứng viên (không ngưỡng, không hạn mức)
C5  cấu hình đầy đủ       rag_service.retrieve_relevant_chunks_multi([câu hỏi]): ngưỡng 0,20, hạn mức, gộp về đoạn cha

Câu hỏi được dùng nguyên văn làm truy vấn (không qua bộ định tuyến) để chỉ đo phần truy xuất.
Đơn vị chấm là tài liệu (source_url): danh sách kết quả được rút về các tài liệu duy nhất theo thứ tự xếp hạng.
Cách chạy:  python -B -X utf8 eval/run_retrieval_ablation.py [--limit N]
Kết quả: eval/results/retrieval_ablation.json
"""
import argparse
import asyncio
import json
import math
import re
import statistics
import time
from collections import Counter, defaultdict

from common import (DATA, RES, dedupe, fetch_all, fmt_ci, hit_at_k, import_service, read_jsonl, recall_at_k,
                    reciprocal_rank, unaccent, write_json, percentile)

CONFIGS = ["C1", "C2", "C3", "C4", "C5"]
KS = (1, 3, 5)
ANSWERABLE = {"quy_che", "thu_tuc", "nhieu_y"}

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=0, help="chỉ chạy N câu đầu (thử nhanh)")
ap.add_argument("--questions", default=str(DATA / "questions.jsonl"))
ap.add_argument("--out", default=str(RES / "retrieval_ablation.json"))
args = ap.parse_args()

rag = import_service()
embedder, reranker, sb = rag.get_embedder(), rag.get_reranker(), rag.get_supabase_client()
batch = 32 if rag.get_device() == "cuda" else 8

# ------------------------------------------------------------ chỉ mục BM25 cho C2
docs = {d["id"]: d for d in fetch_all(sb, "documents", "id,source_url,title")}
chunks = fetch_all(sb, "document_chunks", "id,document_id,content")
tok = lambda s: re.findall(r"[a-z0-9]+", unaccent(s).lower())  # noqa: E731
chunk_tokens = {c["id"]: Counter(tok(c["content"])) for c in chunks}
chunk_len = {cid: sum(c.values()) for cid, c in chunk_tokens.items()}
avg_len = statistics.mean(chunk_len.values())
df = Counter(t for c in chunk_tokens.values() for t in c)
N = len(chunks)


# ------------------------------------------------------------ nguồn tương đương (đánh giá nới lỏng)
# Nhiều quy định xuất hiện ở nhiều tài liệu (trang cẩm nang, Quy chế đầy đủ, Sổ tay sinh viên). Ngoài nhãn gold chặt, một
# tài liệu cũng được coi là đúng nếu chứa TẤT CẢ cụm khóa của câu hỏi (data/key_phrases.json).
norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[*#_`]", " ", s.lower())).strip()  # noqa: E731
parents = fetch_all(sb, "document_parents", "id,document_id,content")
doc_text = defaultdict(str)
for pr in parents:
    doc_text[pr["document_id"]] += " " + pr["content"]
doc_text = {did: norm(tx) for did, tx in doc_text.items()}
KEY = {k: v for k, v in json.loads((DATA / "key_phrases.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}


def relaxed_gold(qid, gold):
    phrases = [norm(x) for x in KEY.get(qid, [])]
    if not phrases:
        return sorted(gold)
    by_phrase = {d["source_url"] for did, d in docs.items() if all(ph in doc_text.get(did, "") for ph in phrases)}
    missing = [g for g in gold if g not in by_phrase]
    if missing and len(gold) == 1:
        print(f"[CẢNH BÁO] {qid}: tài liệu gold không chứa đủ cụm khóa: {missing}")
    return sorted(by_phrase | set(gold))


def bm25(query_tokens, cid, k1=1.5, b=0.75):
    tf, score = chunk_tokens[cid], 0.0
    for t in set(query_tokens):
        if t in tf:
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            score += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * chunk_len[cid] / avg_len))
    return score


def rpc(query_text, vec, n=50):
    return sb.rpc("match_chunks_hybrid_rrf", {"query_text": query_text, "query_embedding": vec, "match_count": n}).execute().data or []


def fts_candidates(question):
    q = unaccent(question)
    rows = (sb.table("document_chunks").select("id,document_id").limit(500).text_search(
        "fts_tokens", q, options={"config": "simple", "type": "web_search"}).execute().data) or []
    qt = tok(question)
    ranked = sorted(rows, key=lambda r: bm25(qt, r["id"]), reverse=True)[:50]
    return [docs[r["document_id"]]["source_url"] for r in ranked if r["document_id"] in docs], len(rows)


def rerank(question, cands):
    pairs = [(question, f"{(c.get('metadata') or {}).get('title') or ''}\n{c.get('content') or ''}".strip()) for c in cands]
    scores = reranker.predict(pairs, batch_size=batch)
    out = []
    for c, s in zip(cands, scores):
        s = float(s)
        out.append((c, 1 / (1 + math.exp(-s)) if (s < 0 or s > 1) else s))
    return sorted(out, key=lambda x: x[1], reverse=True)


async def c5(question):
    chunks_, top = await rag.retrieve_relevant_chunks_multi([question])
    return [c.get("source_url") or (c.get("metadata") or {}).get("source_url") for c in chunks_], top


def timed(fn, *a):
    t = time.perf_counter()
    r = fn(*a)
    return r, (time.perf_counter() - t) * 1000


questions = read_jsonl(args.questions)
if args.limit:
    questions = questions[:args.limit]
loop = asyncio.new_event_loop()
loop.run_until_complete(rag.get_query_embedding("khởi động mô hình"))   # làm nóng mô hình, không tính vào kết quả
reranker.predict([("khởi động", "khởi động")])

records = []
for i, q in enumerate(questions, 1):
    text = q["question"]
    vec, embed_ms = timed(lambda: embedder.encode(text).tolist())
    loop.run_until_complete(rag.get_query_embedding(text))                # bỏ thời gian sinh vector khỏi C5
    rec = {"id": q["id"], "group": q["group"], "gold": q["gold_sources"],
           "relaxed_gold": relaxed_gold(q["id"], q["gold_sources"]) if q["gold_sources"] else [], "embed_ms": round(embed_ms, 1), "ranked": {}, "ms": {}}

    c1, rec["ms"]["C1"] = timed(rpc, "", vec)
    rec["ranked"]["C1"] = dedupe([c.get("source_url") for c in c1])
    (c2, n_fts), rec["ms"]["C2"] = timed(fts_candidates, text)
    rec["ranked"]["C2"], rec["fts_matches"] = dedupe(c2), n_fts
    c3, rec["ms"]["C3"] = timed(rpc, text, vec)
    rec["ranked"]["C3"] = dedupe([c.get("source_url") for c in c3])
    t0 = time.perf_counter()
    rr = rerank(text, c3)
    rec["ms"]["C4"] = rec["ms"]["C3"] + (time.perf_counter() - t0) * 1000
    rec["ranked"]["C4"] = dedupe([c.get("source_url") for c, _ in rr])
    rec["top_rerank_score"] = round(rr[0][1], 4) if rr else None
    t0 = time.perf_counter()
    (c5r, top5) = loop.run_until_complete(c5(text))
    rec["ms"]["C5"] = (time.perf_counter() - t0) * 1000
    rec["ranked"]["C5"], rec["c5_returned"], rec["c5_top_score"] = dedupe(c5r), len(c5r), round(top5, 4)
    for k in rec["ms"]:
        rec["ms"][k] = round(rec["ms"][k], 1)
    records.append(rec)
    print(f"[{i}/{len(questions)}] {q['id']} {q['group']:13s} C3→{(rec['ranked']['C3'][:1] or ['-'])[0][-40:]}  fts={n_fts}", flush=True)

# ------------------------------------------------------------ tổng hợp
summary = {}
for scope, pred in [("tat_ca_co_dap_an", lambda r: r["group"] in ANSWERABLE)] + [(g, (lambda g: lambda r: r["group"] == g)(g)) for g in sorted(ANSWERABLE)]:
    rows = [r for r in records if pred(r)]
    if not rows:
        continue
    summary[scope] = {"n": len(rows)}
    for cfg in CONFIGS:
        m = {}
        for k in KS:
            hits = sum(hit_at_k(r["ranked"][cfg], set(r["gold"]), k) for r in rows)
            m[f"hit@{k}"] = {"k": hits, "n": len(rows), "text": fmt_ci(hits, len(rows))}
        for k in KS:
            hits = sum(hit_at_k(r["ranked"][cfg], set(r["relaxed_gold"]), k) for r in rows)
            m[f"hit@{k}_nl"] = {"k": hits, "n": len(rows), "text": fmt_ci(hits, len(rows))}
        m["mrr@5_nl"] = round(statistics.mean(reciprocal_rank(r["ranked"][cfg], set(r["relaxed_gold"]), 5) for r in rows), 4)
        m["mrr@5"] = round(statistics.mean(reciprocal_rank(r["ranked"][cfg], set(r["gold"]), 5) for r in rows), 4)
        m["recall@5"] = round(statistics.mean(recall_at_k(r["ranked"][cfg], set(r["gold"]), 5) for r in rows), 4)
        ms = [r["ms"][cfg] for r in rows]
        m["ms_p50"], m["ms_p95"] = round(percentile(ms, .5), 1), round(percentile(ms, .95), 1)
        summary[scope][cfg] = m
oos = [r for r in records if r["group"] not in ANSWERABLE]
summary["ngoai_pham_vi_va_ngoai_kho"] = {
    "n": len(oos), "c5_tra_ve_rong": sum(r["c5_returned"] == 0 for r in oos),
    "top_rerank_score": {r["id"]: r["top_rerank_score"] for r in oos}}
ans = [r for r in records if r["group"] in ANSWERABLE]
if ans:
    summary["tong_ket_nhanh_toan_van"] = {
        "ti_le_cau_hoi_co_ket_qua_toan_van": f"{sum(r['fts_matches'] > 0 for r in ans)}/{len(ans)}",
        "so_chunk_khop_trung_vi": statistics.median(r["fts_matches"] for r in ans)}
    summary["c5_cau_hoi_co_dap_an_tra_ve_rong"] = sum(r["c5_returned"] == 0 for r in ans)
    summary["top_rerank_score_co_dap_an"] = {"min": min(r["top_rerank_score"] for r in ans), "median": statistics.median(r["top_rerank_score"] for r in ans)}
write_json(args.out, {"records": records, "summary": summary, "n_chunks": N, "n_documents": len(docs)})

print("\n| Cấu hình | Hit@1 | Hit@3 | Hit@5 | MRR@5 | p50 (ms) |")
for cfg in CONFIGS:
    m = summary["tat_ca_co_dap_an"][cfg]
    print(f"| {cfg} | {m['hit@1']['text']} | {m['hit@3']['text']} | {m['hit@5']['text']} | {m['mrr@5']} | "
          f"{m['hit@1_nl']['text']} | {m['hit@3_nl']['text']} | {m['mrr@5_nl']} | {m['ms_p50']} |")
print(json_ := {k: v for k, v in summary.items() if k not in CONFIGS and not k.startswith(("tat_ca", "quy", "thu", "nhieu"))})
