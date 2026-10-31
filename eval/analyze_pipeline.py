"""Chỉ báo tự động từ answers_V2.jsonl (bổ sung cho chấm tay ở E2; KHÔNG thay thế đánh giá chất lượng câu trả lời).

- Đường xử lý của từng nhóm câu hỏi (guardrail, router từ chối, không tra cứu, RAG).
- Hit@K đầu cuối: tài liệu trong retrieved_sources (sau bộ định tuyến, hạn mức và gộp đoạn cha) có chứa nhãn đúng hay không.
- Phân bố thẻ tự đánh giá (doc_relevance, answer_confidence).
- Với câu ngoài kho/ngoài phạm vi: câu trả lời có chứa cụm từ chối ("chưa tìm thấy", lời nhắc chỉ hỗ trợ học vụ) hay không.
Kết quả: eval/results/pipeline_indicators.json
"""
import json
from collections import Counter, defaultdict

from common import RES, dedupe, fmt_ci, hit_at_k, read_jsonl, write_json

v2 = {r["id"]: r for r in read_jsonl(RES / "answers_V2.jsonl") if "error" not in r}
abl = {r["id"]: r for r in json.loads((RES / "retrieval_ablation.json").read_text(encoding="utf-8"))["records"]}
ANSWERABLE = {"quy_che", "thu_tuc", "nhieu_y"}
REFUSAL = ("chưa tìm thấy", "chỉ hỗ trợ", "không có thông tin", "không tìm thấy")

paths = defaultdict(Counter)
for r in v2.values():
    paths[r["group"]][r["path"]] += 1
out = {"duong_xu_ly_theo_nhom": {g: dict(c) for g, c in paths.items()}}

ans = [r for r in v2.values() if r["group"] in ANSWERABLE]
for k in (1, 3, 5):
    strict = sum(hit_at_k(dedupe(r["retrieved_sources"]), set(abl[r["id"]]["gold"]), k) for r in ans)
    relaxed = sum(hit_at_k(dedupe(r["retrieved_sources"]), set(abl[r["id"]]["relaxed_gold"]), k) for r in ans)
    out[f"hit@{k}_dau_cuoi"] = {"chat": fmt_ci(strict, len(ans)), "noi_long": fmt_ci(relaxed, len(ans))}
out["qua_bo_dinh_tuyen"] = {"so_cau_hoi_co_dap_an": len(ans), "so_cau_bi_chan_hoac_tu_choi": sum(r["path"] != "rag" for r in ans),
                            "so_truy_van_trung_binh": round(sum(len(r["queries"]) for r in ans) / len(ans), 2)}
refl = Counter()
for r in v2.values():
    if r["path"] == "rag" and r.get("reflection"):
        refl[(r["reflection"]["doc_relevance"], r["reflection"]["answer_confidence"])] += 1
out["tu_danh_gia_doc_relevance_x_confidence"] = {f"{a}/{b}": n for (a, b), n in sorted(refl.items())}
oos = [r for r in v2.values() if r["group"] not in ANSWERABLE]
out["ngoai_pham_vi_ngoai_kho"] = {
    r["id"]: {"group": r["group"], "path": r["path"], "co_cum_tu_choi": any(x in r["answer"].lower() for x in REFUSAL),
              "top_doc_score": r.get("top_doc_score")} for r in oos}
out["ngoai_pham_vi_ngoai_kho_tu_choi"] = fmt_ci(sum(any(x in r["answer"].lower() for x in REFUSAL) for r in oos), len(oos)) if oos else None
write_json(RES / "pipeline_indicators.json", out)
print(json.dumps(out, ensure_ascii=False, indent=1))
