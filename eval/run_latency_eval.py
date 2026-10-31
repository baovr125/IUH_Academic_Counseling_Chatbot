"""Thí nghiệm E5: tóm tắt độ trễ từng giai đoạn từ eval/results/answers_V2.jsonl (Bảng 5.8, Hình 5.3). Không gọi dịch vụ ngoài.

Số đo do run_answer_eval.py ghi ngay trong tiến trình (không qua Kong, nginx hay mạng của client), gồm:
  router_ms     lời gọi bộ định tuyến
  retrieval_ms  truy xuất nhiều truy vấn và xếp hạng lại (rag_data['retrieval_latency_ms'])
  build_ms      sinh vector truy vấn, truy xuất, ký ức phiên và dựng prompt
  gen_ms        sinh câu trả lời (từ lúc gửi tới khi hết luồng)
  ttft_ms       từ lúc nhận câu hỏi đến chữ đầu tiên HIỂN THỊ (sau khi bỏ khối <thinking>)
  total_ms      từ lúc nhận câu hỏi đến hết luồng
Chỉ tính các lượt đi hết đường RAG (path = rag); lượt đầu tiên bị bỏ nếu dùng --skip-first.
"""
import argparse
import statistics

from common import RES, percentile, read_jsonl, write_json

ap = argparse.ArgumentParser()
ap.add_argument("--skip-first", action="store_true", help="bỏ lượt đầu tiên (làm nóng)")
args = ap.parse_args()

rows = [r for r in read_jsonl(RES / "answers_V2.jsonl") if "error" not in r]
if args.skip_first:
    rows = rows[1:]
paths = {}
for r in rows:
    paths[r["path"]] = paths.get(r["path"], 0) + 1
rag_rows = [r for r in rows if r["path"] == "rag" and r.get("ttft_ms") is not None]
fields = ["router_ms", "retrieval_ms", "build_ms", "gen_ms", "ttft_ms", "total_ms"]
summary = {"n_tong": len(rows), "so_luot_theo_duong": paths, "n_rag": len(rag_rows), "giai_doan": {}}
for f in fields:
    vals = [r[f] for r in rag_rows if r.get(f) is not None]
    summary["giai_doan"][f] = {"p50": round(percentile(vals, .5)), "p95": round(percentile(vals, .95)),
                                "mean": round(statistics.mean(vals)), "max": round(max(vals)), "n": len(vals)}
summary["prompt_tokens_p50"] = round(percentile([r["prompt_tokens"] for r in rag_rows if r.get("prompt_tokens")], .5))
summary["raw"] = {f: [r.get(f) for r in rag_rows] for f in fields}
write_json(RES / "latency_summary.json", summary)
print(summary["so_luot_theo_duong"], "n_rag =", len(rag_rows))
for f in fields:
    s = summary["giai_doan"][f]
    print(f"{f:13s} p50={s['p50']:6d}  p95={s['p95']:6d}  mean={s['mean']:6d}  max={s['max']:6d}")
