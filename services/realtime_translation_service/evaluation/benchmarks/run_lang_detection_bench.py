"""Benchmark bổ sung cho Language Detection (gọi đúng `detect_language_detailed`).

  python evaluation/benchmarks/run_lang_detection_bench.py --file <jsonl> --out <json> [--latency-n 500 --rounds 3]

Đo:
  - Theo ngôn ngữ: phân bố status, accuracy chặt, sai-mà-tự-tin, false-accept (mẫu ngoài phạm vi bị `detected`).
  - Tính xác định: chạy lại cùng 200 mẫu 3 lần, so (status, ngôn ngữ, confidence làm tròn 6 chữ số).
  - Độ trễ warm: TẮT cache LRU (DETECT_CACHE_SIZE=0) để mỗi lần đều tính thật; n mẫu × số lượt; p50/p95/p99.
Không gồm thời gian nạp model (đã warm_up trước).
"""
import argparse
import json
import logging
import os
import statistics
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
os.environ.setdefault("TESTING", "1")
os.environ["DETECT_CACHE_SIZE"] = "0"  # đo tính toán thật, không đo cache
logging.disable(logging.CRITICAL)

from app.services import language_detection as ld  # noqa: E402


def pct(values, p):
    s = sorted(values)
    return s[min(len(s) - 1, max(0, int(round(p / 100 * (len(s) - 1)))))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--latency-n", type=int, default=500)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--determinism-n", type=int, default=200)
    args = ap.parse_args()
    rows = [json.loads(l) for l in open(args.file, encoding="utf-8") if l.strip()]

    ld.reload_config()
    t0 = time.perf_counter()
    ld.warm_up()
    warm_up_s = time.perf_counter() - t0

    # 1. theo ngôn ngữ
    per = defaultdict(Counter)
    outcomes = []
    for r in rows:
        d = ld.detect_language_detailed(r["text"])
        lang = r["expected_primary_language"]
        if r["expected_status"] == "detected":
            if d.status == "detected":
                key = "correct" if d.resolved_source_lang == lang else "wrong_confident"
            else:
                key = f"abstain_{d.status}"
        else:  # ngoài phạm vi
            key = "false_accept" if d.status == "detected" else f"rejected_{d.status}"
        per[lang][key] += 1
        outcomes.append({"id": r["id"], "expected": lang, "expected_status": r["expected_status"], "status": d.status,
                         "lang": d.resolved_source_lang, "confidence": d.confidence, "reason": d.reason,
                         "outcome": key, "text": r["text"][:120]})

    # 2. tính xác định
    # Lấy mẫu rải đều toàn file (file được sắp theo ngôn ngữ) để đại diện mọi ngôn ngữ.
    def spread(n):
        step = max(1, len(rows) // n)
        return rows[::step][:n]

    sample = spread(args.determinism_n)
    runs = []
    for _ in range(3):
        runs.append([(d.status, d.resolved_source_lang, round(d.confidence, 6))
                     for d in (ld.detect_language_detailed(r["text"]) for r in sample)])
    identical = sum(1 for i in range(len(sample)) if runs[0][i] == runs[1][i] == runs[2][i])

    # 3. độ trễ (cache tắt)
    lat_rows = spread(args.latency_n)
    rounds = []
    for _ in range(args.rounds):
        times = []
        for r in lat_rows:
            s = time.perf_counter()
            ld.detect_language_detailed(r["text"])
            times.append((time.perf_counter() - s) * 1000)
        rounds.append({"p50_ms": statistics.median(times), "p95_ms": pct(times, 95), "p99_ms": pct(times, 99),
                       "max_ms": max(times), "mean_ms": statistics.mean(times)})

    result = {
        "file": os.path.basename(args.file), "samples": len(rows), "warm_up_s": warm_up_s,
        "cache_disabled": True,
        "per_language": {k: dict(v) for k, v in sorted(per.items())},
        "determinism": {"samples": len(sample), "identical_3_runs": identical,
                        "languages": len({r["expected_primary_language"] for r in sample})},
        "latency_sample": {"samples": len(lat_rows), "languages": len({r["expected_primary_language"] for r in lat_rows})},
        "latency_rounds": rounds,
        "outcomes_not_correct": [o for o in outcomes if o["outcome"] not in ("correct", "rejected_unsupported")],
    }
    json.dump(result, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "outcomes_not_correct"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
