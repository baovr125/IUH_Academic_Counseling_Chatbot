# -*- coding: utf-8 -*-
"""Dev-gate cho Language Detection (chạy trên bộ dev/val, KHÔNG phải bộ test của evaluation.md).

    python evaluation/dev_gate.py --split val --show-errors
    python evaluation/dev_gate.py --split all --json out.json

Gọi trực tiếp `detect_language_detailed` (cùng đường xử lý production của /text, /stream, /detect).
"""
import argparse
import json
import logging
import os
import statistics
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("TESTING", "1")
logging.disable(logging.CRITICAL)

from app.services import language_detection as ld  # noqa: E402

DATASET_DIR = os.path.join(ROOT, "evaluation", "dataset")

GATES = {
    "accuracy_clear_strict": (">=", 0.96),
    "vietnamese_or_abstain": (">=", 0.98),
    "short_or_abstain": (">=", 0.92),
    "wrong_confident_rate": ("<=", 0.01),
    "oos_false_accept": ("<=", 0.07),
    "latency_p95_ms": ("<=", 30.0),
}


def load_rows(split: str, file: str = "") -> list:
    if file:
        with open(file, "r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    names = {"dev": ["lang_dev.jsonl"], "val": ["lang_val.jsonl"], "all": ["lang_dev.jsonl", "lang_val.jsonl"]}[split]
    rows = []
    for name in names:
        with open(os.path.join(DATASET_DIR, name), "r", encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    return rows


def classify(row: dict, details) -> str:
    """Trả về: correct | abstain_ok | wrong_confident | wrong_status | missed_unsupported."""
    expected_status = row["expected_status"]
    expected_lang = row.get("expected_primary_language")
    status = details.status
    lang = details.resolved_source_lang

    if expected_status == "detected":
        if status == "detected":
            return "correct" if lang == expected_lang else "wrong_confident"
        if status == "uncertain" and row.get("abstain_ok"):
            return "abstain_ok"
        return "wrong_status"
    if expected_status == "unsupported":
        if status == "unsupported":
            return "correct"
        if status == "detected":
            return "wrong_confident"
        return "abstain_ok" if status == "uncertain" else "wrong_status"
    if expected_status == "uncertain":
        return "wrong_confident" if status == "detected" else "correct"
    # invalid_input / unknown
    if status == expected_status:
        return "correct"
    return "wrong_confident" if status == "detected" else "wrong_status"


def percentile(values: list, pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round(pct / 100.0 * (len(ordered) - 1)))))
    return ordered[index]


def evaluate(rows: list) -> dict:
    ld.reload_config()
    ld.warm_up()
    results, latencies = [], []
    for row in rows:
        started = time.perf_counter()
        details = ld.detect_language_detailed(row["text"])
        latencies.append((time.perf_counter() - started) * 1000)
        results.append((row, details, classify(row, details)))

    total = len(results)
    wrong_confident = [r for r in results if r[2] == "wrong_confident"]
    detect_expected = [r for r in results if r[0]["expected_status"] == "detected"]
    clear = [r for r in detect_expected if not r[0].get("abstain_ok")]
    vi_rows = [r for r in detect_expected if r[0]["expected_primary_language"] == "vi"]
    short_rows = [r for r in detect_expected
                  if r[0]["category"] in ("short", "vietnamese_no_diacritic_short", "typing_prefix")]
    oos_rows = [r for r in results if r[0]["expected_status"] == "unsupported"]
    predicted_detected = [r for r in results if r[1].status == "detected"]

    def rate(subset, ok_set):
        return sum(1 for r in subset if r[2] in ok_set) / len(subset) if subset else float("nan")

    metrics = {
        "samples": total,
        "accuracy_clear_strict": rate(clear, {"correct"}),
        "accuracy_all_strict": rate(detect_expected, {"correct"}),
        "accuracy_all_or_abstain": rate(detect_expected, {"correct", "abstain_ok"}),
        "vietnamese_strict": rate(vi_rows, {"correct"}),
        "vietnamese_or_abstain": rate(vi_rows, {"correct", "abstain_ok"}),
        "short_or_abstain": rate(short_rows, {"correct", "abstain_ok"}),
        "wrong_confident_rate": len(wrong_confident) / total if total else float("nan"),
        "wrong_confident_among_detected": len(wrong_confident) / len(predicted_detected) if predicted_detected else 0.0,
        "oos_false_accept": (sum(1 for r in oos_rows if r[1].status == "detected") / len(oos_rows)) if oos_rows else float("nan"),
        "oos_recall": rate(oos_rows, {"correct"}),
        "latency_p50_ms": statistics.median(latencies),
        "latency_p95_ms": percentile(latencies, 95),
        "latency_p99_ms": percentile(latencies, 99),
    }

    per_category = defaultdict(Counter)
    for row, _, outcome in results:
        per_category[row["category"]][outcome] += 1
    metrics["per_category"] = {cat: dict(counts) for cat, counts in sorted(per_category.items())}
    return {"metrics": metrics, "results": results}


def verdict(metrics: dict) -> dict:
    out = {}
    for name, (op, target) in GATES.items():
        value = metrics[name]
        if value != value:  # NaN: tập đang chấm không có nhóm mẫu này → không áp dụng
            out[name] = {"value": value, "target": f"{op} {target}", "pass": True, "applicable": False}
            continue
        ok = (value >= target) if op == ">=" else (value <= target)
        out[name] = {"value": value, "target": f"{op} {target}", "pass": bool(ok), "applicable": True}
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "val", "all"], default="val")
    parser.add_argument("--file", help="Chấm trên một file JSONL tùy ý (cùng schema) thay cho dev/val")
    parser.add_argument("--show-errors", action="store_true")
    parser.add_argument("--json", help="Ghi kết quả ra file JSON")
    args = parser.parse_args()

    outcome = evaluate(load_rows(args.split, args.file or ""))
    metrics, results = outcome["metrics"], outcome["results"]
    gates = verdict(metrics)

    print(f"== Dev-gate Language Detection  split={args.split}  samples={metrics['samples']} ==")
    for name, info in gates.items():
        flag = "PASS" if info["pass"] else "FAIL"
        value = info["value"]
        shown = f"{value:.4f}" if isinstance(value, float) else str(value)
        if not info.get("applicable", True):
            flag, shown = "n/a ", "n/a"
        print(f"  [{flag}] {name:26} {shown:>9}   (cần {info['target']})")
    print(f"  (tham khảo) accuracy_all_strict={metrics['accuracy_all_strict']:.4f}  "
          f"accuracy_all_or_abstain={metrics['accuracy_all_or_abstain']:.4f}  "
          f"vietnamese_strict={metrics['vietnamese_strict']:.4f}  oos_recall={metrics['oos_recall']:.4f}  "
          f"wrong_confident_among_detected={metrics['wrong_confident_among_detected']:.4f}")
    print(f"  latency p50/p95/p99 = {metrics['latency_p50_ms']:.2f} / {metrics['latency_p95_ms']:.2f} / {metrics['latency_p99_ms']:.2f} ms")
    print("  Theo nhóm:")
    for cat, counts in metrics["per_category"].items():
        print(f"    {cat:30} {dict(counts)}")

    if args.show_errors:
        print("\n-- Lỗi / abstain --")
        for row, details, label in results:
            if label in ("correct",):
                continue
            cands = ",".join(f"{c.language}:{c.confidence:.2f}" for c in details.candidates)
            print(f"  [{label:15}] exp={row['expected_status']}/{row.get('expected_primary_language')} "
                  f"got={details.status}/{details.resolved_source_lang or details.detected_language} "
                  f"conf={details.confidence:.2f} eng={details.engine} reason={details.reason} [{cands}] "
                  f"cat={row['category']} :: {row['text'][:70]!r}")

    if args.json:
        serial = {"metrics": metrics, "gates": gates}
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(serial, handle, ensure_ascii=False, indent=2)
    return 0 if all(info["pass"] for info in gates.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
