"""Thí nghiệm E3: quy tắc của bộ nhớ đệm ngữ nghĩa trên các cặp câu hỏi (Bảng 5.6). KHÔNG ghi Redis hay Supabase.

Mô phỏng trong bộ nhớ đúng quy tắc của rag_service.check_semantic_cache (tầng ngữ nghĩa):
  1. lấy ứng viên gần nhất theo cosine trong chỉ mục (ở đây là tập các câu q1 của mọi cặp, vì hệ thống thật cũng chỉ lấy 1 ứng viên);
  2. cosine >= 0,60 (bi-encoder vietnamese-bi-encoder);
  3. điểm Cross-Encoder bge-reranker-v2-m3 của (câu hỏi, câu đã lưu) >= 0,80;
  4. hai câu có cùng tập chữ số.
Không mô phỏng tầng Redis khớp chính xác, thời hạn hết hạn và bước ghi qua cổng chất lượng. Hai ngưỡng 0,60 và 0,80 chép từ mã nguồn;
nếu mã đổi, sửa hằng số dưới đây.

Loại cặp: dien_dat_lai (q2 diễn đạt lại q1, kỳ vọng trúng q1) và khac_con_so (q2 khác q1 ở một con số, kỳ vọng KHÔNG trúng q1).
Kết quả: eval/results/cache_eval.json
"""
import re
import statistics
import time

import numpy as np

from common import DATA, RES, fmt_ci, import_service, percentile, read_jsonl, write_json

COS_MIN, CE_MIN = 0.60, 0.80

rag = import_service()
embedder, reranker = rag.get_embedder(), rag.get_reranker()
pairs = read_jsonl(DATA / "cache_pairs.jsonl")
index_q = [p["q1"] for p in pairs]
vecs = embedder.encode(index_q, normalize_embeddings=True)
reranker.predict([("khởi động", "khởi động")])


def digits(s):
    return sorted(re.findall(r"\d+", s))


def sigmoid_if_needed(x):
    x = float(x)
    return 1 / (1 + np.exp(-x)) if (x < 0 or x > 1) else x


rows = []
for p in pairs:
    t0 = time.perf_counter()
    v = embedder.encode(p["q2"], normalize_embeddings=True)
    sims = vecs @ v
    j = int(np.argmax(sims))
    cos = float(sims[j])
    cand = index_q[j]
    ce = sigmoid_if_needed(reranker.predict([(p["q2"], cand)])[0]) if cos >= COS_MIN else None
    num_ok = digits(p["q2"]) == digits(cand)
    hit = cos >= COS_MIN and ce is not None and ce >= CE_MIN and num_ok
    hit_no_num = cos >= COS_MIN and ce is not None and ce >= CE_MIN
    rows.append({
        "id": p["id"], "type": p["type"], "q2": p["q2"], "candidate": cand, "candidate_is_partner": cand == p["q1"],
        "cos": round(cos, 4), "ce": None if ce is None else round(ce, 4), "numbers_match": num_ok,
        "hit": hit, "hit_without_number_rule": hit_no_num, "check_ms": round((time.perf_counter() - t0) * 1000, 1)})

para = [r for r in rows if r["type"] == "dien_dat_lai"]
numd = [r for r in rows if r["type"] == "khac_con_so"]
summary = {
    "dien_dat_lai": {
        "n": len(para),
        "hit_dung_cap": fmt_ci(sum(r["hit"] and r["candidate_is_partner"] for r in para), len(para)),
        "hit_nham_cap_khac": sum(r["hit"] and not r["candidate_is_partner"] for r in para),
        "khong_hit": sum(not r["hit"] for r in para)},
    "khac_con_so": {
        "n": len(numd),
        "hit_nham_cap_dung_cung_cau_goc": fmt_ci(sum(r["hit"] and r["candidate_is_partner"] for r in numd), len(numd)),
        "hit_nham_neu_bo_luat_so": fmt_ci(sum(r["hit_without_number_rule"] and r["candidate_is_partner"] for r in numd), len(numd)),
        "hit_bat_ky": sum(r["hit"] for r in numd)},
    "check_ms_p50": round(percentile([r["check_ms"] for r in rows], .5), 1),
    "check_ms_p95": round(percentile([r["check_ms"] for r in rows], .95), 1),
    "nguong": {"cosine": COS_MIN, "cross_encoder": CE_MIN},
}
# quét ngưỡng Cross-Encoder để xem độ nhạy (chỉ các ứng viên đã qua ngưỡng cosine)
sweep = []
for th in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
    pr = sum(r["ce"] is not None and r["ce"] >= th and r["candidate_is_partner"] for r in para)
    fh = sum(r["ce"] is not None and r["ce"] >= th and r["candidate_is_partner"] for r in numd)
    sweep.append({"ce_min": th, "hit_dien_dat_lai": f"{pr}/{len(para)}", "hit_nham_khac_con_so_neu_bo_luat_so": f"{fh}/{len(numd)}"})
summary["quet_nguong_cross_encoder"] = sweep
write_json(RES / "cache_eval.json", {"rows": rows, "summary": summary})
for r in rows:
    print(f"{r['id']} cos={r['cos']:.3f} ce={r['ce']} so={r['numbers_match']} hit={r['hit']}")
print(summary)
