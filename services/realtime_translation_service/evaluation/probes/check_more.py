"""Đọc-chỉ: số liệu phụ từ artifact (không gọi API, không đo lại hệ thống)."""
import collections
import json
import os
import statistics
import sys

art, svc = sys.argv[1], sys.argv[2]


def jl(path):
    if not os.path.exists(path):
        print("(thiếu file artifact, bỏ qua)", path)
        return []
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


print("== TQ-01: khớp chính xác và phân bố theo nhóm")
tq = json.load(open(os.path.join(art, "tq01_lt01_nllb.json"), encoding="utf-8"))
gt = json.load(open(os.path.join(svc, "evaluation/dataset/ground_truth_dataset.json"), encoding="utf-8"))
cats = collections.Counter(r["category"] for r in gt)
print("categories:", dict(cats))
items = tq["items"]
exact = sum(1 for it in items if it["hypothesis"].strip() == it["reference"].strip())
exact_ci = sum(1 for it in items if it["hypothesis"].strip().lower().rstrip(".") == it["reference"].strip().lower().rstrip("."))
print("exact match:", exact, "/", len(items), "| bỏ hoa-thường và dấu chấm cuối:", exact_ci)
print("độ dài nguồn (từ): median", statistics.median(len(it["source"].split()) for it in items),
      "max", max(len(it["source"].split()) for it in items))
html = sum(1 for it in items if "<" in it["source"])
print("câu có thẻ HTML:", html)
for it in items[:60]:
    if any(k in it["source"].lower() for k in ("credit", "transcript", "prerequisite", "semester")):
        print("  ", it["id"], "|", it["source"], "|", it["reference"], "|", it["hypothesis"])

print("== lang_val: phân bố")
val = jl(os.path.join(svc, "evaluation/dataset/lang_val.jsonl"))
print("keys:", sorted(val[0].keys()))
for key in ("category", "expected_status", "lang", "label", "expected"):
    if key in val[0]:
        print(key, dict(collections.Counter(str(r.get(key)) for r in val)))

print("== domain sets: phân bố kind")
for name in ("domain_dev", "domain_val", "domain_holdout"):
    rows = jl(os.path.join(svc, "evaluation/dataset/%s.jsonl" % name))
    print(name, len(rows), dict(collections.Counter(r.get("kind") for r in rows)))

print("== dd03 summary")
d = json.load(open(os.path.join(art, "dd03_consistency_val_qwen.json"), encoding="utf-8"))
print(json.dumps(d["summary"], ensure_ascii=False))

print("== ld02_04 bench: determinism, latency, reasons")
b = json.load(open(os.path.join(art, "ld02_04_tatoeba_bench.json"), encoding="utf-8"))
print("keys:", list(b.keys()))
for k in ("determinism", "latency_rounds", "abstain_reasons", "reasons", "config"):
    if k in b:
        print(k, json.dumps(b[k], ensure_ascii=False)[:700])

print("== TA-01 (2026-10-10): độ trễ theo chế độ")
for f in ("ta01_dev_plain_qwen.jsonl", "ta01_dev_manual_qwen.jsonl", "ta01_dev_auto_qwen.jsonl"):
    rows = jl(os.path.join(art, f))
    ok = [r for r in rows if r.get("ok")]
    fs = sorted(r["first_s"] for r in ok if r.get("first_s") is not None)
    ts = sorted(r["total_s"] for r in ok if r.get("total_s") is not None)

    def pct(a, p):
        return a[min(len(a) - 1, int(round(p * (len(a) - 1))))] if a else float("nan")

    print(f, "n=%d ok=%d" % (len(rows), len(ok)),
          "first p50=%.2f p95=%.2f" % (pct(fs, 0.5), pct(fs, 0.95)),
          "total p50=%.2f p95=%.2f" % (pct(ts, 0.5), pct(ts, 0.95)))
