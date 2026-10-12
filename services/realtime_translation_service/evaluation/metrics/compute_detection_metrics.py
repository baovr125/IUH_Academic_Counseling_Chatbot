"""
evaluation/metrics/compute_detection_metrics.py
================================================
Tính toán đầy đủ các classification metric từ raw result JSONL:

  - Per-language: Precision, Recall, F1
  - Tổng thể: Macro avg, Weighted avg, Accuracy
  - Abstention metrics: reject_rate, coverage, selective_accuracy
  - Open-set metrics: false_detection_rate trên is_valid=False samples
  - Confidence: mean confidence by correct/incorrect
  - Latency: avg, P50, P95, P99

Usage:
    python evaluation/metrics/compute_detection_metrics.py \
        --input evaluation/raw_results/detection_hybrid_20260101_000000.jsonl \
        --output evaluation/results/reports/report_20260101.json
"""

import json
import os
import sys
import argparse
import statistics
from collections import defaultdict
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def load_jsonl(path: str) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def percentile(data: list[float], pct: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * pct / 100
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def compute_per_language_metrics(valid_rows: list[dict]) -> dict:
    """
    Compute Precision, Recall, F1 per language.
    Rejected rows (``predicted is None``) remain in the denominator as false
    negatives. This prevents coverage gaps from being hidden by filtering.
    """
    languages = set()
    for r in valid_rows:
        if r.get("expected_primary_language"):
            languages.add(r["expected_primary_language"])
        if r.get("predicted"):
            languages.add(r["predicted"])

    metrics = {}
    for lang in sorted(languages):
        tp = sum(1 for r in valid_rows
                 if r.get("expected_primary_language") == lang and r.get("predicted") == lang)
        fp = sum(1 for r in valid_rows
                 if r.get("predicted") == lang and r.get("expected_primary_language") != lang)
        fn = sum(1 for r in valid_rows
                 if r.get("expected_primary_language") == lang and r.get("predicted") != lang)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)
                     if (precision + recall) > 0 else 0.0)
        support   = tp + fn

        metrics[lang] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4),
            "recall":    round(recall, 4),
            "f1":        round(f1, 4),
            "support":   support,
        }
    return metrics


def compute_confusion_matrix(valid_rows: list[dict]) -> dict:
    """Return a JSON-safe confusion matrix, including rejected predictions."""
    labels = sorted({
        label
        for row in valid_rows
        for label in (row.get("expected_primary_language"), row.get("predicted"))
        if label
    })
    rejected = "<REJECTED>"
    matrix = {expected: {predicted: 0 for predicted in labels + [rejected]} for expected in labels}
    for row in valid_rows:
        expected = row.get("expected_primary_language")
        if not expected:
            continue
        predicted = row.get("predicted") or rejected
        if predicted not in matrix[expected]:
            for values in matrix.values():
                values[predicted] = 0
        matrix[expected][predicted] += 1
    return {"labels": labels + [rejected], "matrix": matrix}


def compute_macro_weighted(per_lang: dict) -> dict:
    langs = [v for v in per_lang.values() if v["support"] > 0]
    if not langs:
        return {}

    total_support = sum(v["support"] for v in langs)

    macro_p  = statistics.mean(v["precision"] for v in langs)
    macro_r  = statistics.mean(v["recall"]    for v in langs)
    macro_f1 = statistics.mean(v["f1"]        for v in langs)

    w_p  = sum(v["precision"] * v["support"] for v in langs) / total_support
    w_r  = sum(v["recall"]    * v["support"] for v in langs) / total_support
    w_f1 = sum(v["f1"]        * v["support"] for v in langs) / total_support

    return {
        "macro": {
            "precision": round(macro_p,  4),
            "recall":    round(macro_r,  4),
            "f1":        round(macro_f1, 4),
        },
        "weighted": {
            "precision": round(w_p,  4),
            "recall":    round(w_r,  4),
            "f1":        round(w_f1, 4),
        },
    }


def compute_confidence_metrics(rows: list[dict]) -> dict:
    correct_conf   = [r["confidence"] for r in rows
                      if r.get("confidence") is not None and r.get("correct") is True]
    incorrect_conf = [r["confidence"] for r in rows
                      if r.get("confidence") is not None and r.get("correct") is False]

    def safe_mean(lst):
        return round(statistics.mean(lst), 4) if lst else None

    # Bucket analysis: [0,0.5), [0.5,0.7), [0.7,0.85), [0.85,1.0]
    buckets = {
        "[0.00-0.50)": {"correct": 0, "total": 0},
        "[0.50-0.70)": {"correct": 0, "total": 0},
        "[0.70-0.85)": {"correct": 0, "total": 0},
        "[0.85-1.00]": {"correct": 0, "total": 0},
    }
    for r in rows:
        if r.get("confidence") is None or r.get("correct") is None:
            continue
        c = r["confidence"]
        key = ("[0.85-1.00]" if c >= 0.85 else
               "[0.70-0.85)" if c >= 0.70 else
               "[0.50-0.70)" if c >= 0.50 else "[0.00-0.50)")
        buckets[key]["total"] += 1
        if r["correct"]:
            buckets[key]["correct"] += 1

    bucket_acc = {}
    for k, v in buckets.items():
        bucket_acc[k] = {
            "accuracy": round(v["correct"] / v["total"], 4) if v["total"] else None,
            "count": v["total"],
        }

    calibration_rows = [
        r for r in rows
        if r.get("confidence") is not None and r.get("correct") is not None
    ]
    calibration_bins = []
    if calibration_rows:
        for low, high, include_high in ((0.0, 0.1, False), (0.1, 0.2, False),
                                        (0.2, 0.3, False), (0.3, 0.4, False),
                                        (0.4, 0.5, False), (0.5, 0.6, False),
                                        (0.6, 0.7, False), (0.7, 0.8, False),
                                        (0.8, 0.9, False), (0.9, 1.0, True)):
            selected = [
                r for r in calibration_rows
                if low <= r["confidence"] < high or (include_high and r["confidence"] == high)
            ]
            if not selected:
                continue
            mean_conf = statistics.mean(r["confidence"] for r in selected)
            accuracy = statistics.mean(1.0 if r["correct"] else 0.0 for r in selected)
            calibration_bins.append({
                "lower": low,
                "upper": high,
                "count": len(selected),
                "mean_confidence": round(mean_conf, 4),
                "accuracy": round(accuracy, 4),
                "gap": round(abs(mean_conf - accuracy), 4),
            })
        total = len(calibration_rows)
        ece = sum(b["count"] / total * b["gap"] for b in calibration_bins)
        brier = statistics.mean(
            (r["confidence"] - (1.0 if r["correct"] else 0.0)) ** 2
            for r in calibration_rows
        )
    else:
        ece = 0.0
        brier = 0.0

    return {
        "mean_confidence_correct":   safe_mean(correct_conf),
        "mean_confidence_incorrect": safe_mean(incorrect_conf),
        "confidence_buckets":        bucket_acc,
        "ece": round(ece, 4),
        "brier_score": round(brier, 4),
        "reliability_bins": calibration_bins,
    }


def compute_category_metrics(all_rows: list[dict]) -> dict:
    """Accuracy per category group."""
    by_category = defaultdict(list)
    for r in all_rows:
        cat = r.get("category", "unknown")
        by_category[cat].append(r)

    result = {}
    for cat, rows in by_category.items():
        valid = [r for r in rows if r.get("is_valid", True)]
        accepted = [r for r in valid if r.get("predicted") is not None]
        correct  = [r for r in accepted if r.get("correct")]
        total_v  = len(valid)
        result[cat] = {
            "total":    len(rows),
            "valid":    total_v,
            "accepted": len(accepted),
            "correct":  len(correct),
            "accuracy": round(len(correct) / total_v, 4) if total_v else None,
            "coverage": round(len(accepted) / total_v, 4) if total_v else None,
        }
    return result


def compute_open_set_metrics(all_rows: list[dict]) -> dict:
    """
    Metrics for non-natural-language inputs (is_valid=False).
    Measures false detection rate: system assigns a language when it shouldn't.
    """
    invalid_rows = [r for r in all_rows if not r.get("is_valid", True)]
    if not invalid_rows:
        return {"false_detection_rate": None, "count": 0}

    false_detected = [r for r in invalid_rows if r.get("predicted") is not None]
    return {
        "total_non_natural": len(invalid_rows),
        "false_detected":    len(false_detected),
        "false_detection_rate": round(len(false_detected) / len(invalid_rows), 4),
    }


def compute_latency_metrics(rows: list[dict]) -> dict:
    lats = [r["latency_ms"] for r in rows if r.get("latency_ms") is not None]
    if not lats:
        return {}
    return {
        "avg_ms": round(statistics.mean(lats), 3),
        "p50_ms": round(percentile(lats, 50), 3),
        "p95_ms": round(percentile(lats, 95), 3),
        "p99_ms": round(percentile(lats, 99), 3),
        "max_ms": round(max(lats), 3),
        "min_ms": round(min(lats), 3),
    }


def run(input_path: str, output_path: str | None = None) -> dict:
    rows = load_jsonl(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Split into valid / invalid
    all_valid   = [r for r in rows if r.get("is_valid", True)]
    all_invalid = [r for r in rows if not r.get("is_valid", True)]

    accepted_valid = [r for r in all_valid if r.get("predicted") is not None]
    correct_valid  = [r for r in accepted_valid if r.get("correct")]

    total_valid   = len(all_valid)
    total_accept  = len(accepted_valid)
    total_correct = len(correct_valid)

    accuracy     = total_correct / total_valid if total_valid else 0.0
    coverage     = total_accept  / total_valid if total_valid else 0.0
    sel_acc      = total_correct / total_accept if total_accept else 0.0
    reject_rate  = 1.0 - coverage

    per_lang  = compute_per_language_metrics(all_valid)
    avg_stats = compute_macro_weighted(per_lang)
    conf_met  = compute_confidence_metrics(rows)
    cat_met   = compute_category_metrics(rows)
    open_met  = compute_open_set_metrics(rows)
    lat_met   = compute_latency_metrics(rows)

    report = {
        "timestamp":         timestamp,
        "input_file":        os.path.basename(input_path),
        "total_samples":     len(rows),
        "valid_samples":     total_valid,
        "invalid_samples":   len(all_invalid),
        "accepted":          total_accept,
        "correct":           total_correct,
        "accuracy":          round(accuracy, 4),
        "coverage":          round(coverage, 4),
        "selective_accuracy": round(sel_acc, 4),
        "reject_rate":       round(reject_rate, 4),
        "per_language":      per_lang,
        "confusion_matrix":  compute_confusion_matrix(all_valid),
        "aggregate":         avg_stats,
        "confidence":        conf_met,
        "by_category":       cat_met,
        "open_set":          open_met,
        "latency":           lat_met,
    }

    # Print summary
    SEP = "=" * 65
    print(f"\n{SEP}")
    print(f"  DETECTION METRICS REPORT  ({timestamp})")
    print(SEP)
    print(f"  Input      : {os.path.basename(input_path)}")
    print(f"  Samples    : {len(rows)} total, {total_valid} valid, {len(all_invalid)} non-natural")
    print(f"  Accepted   : {total_accept} / {total_valid} valid")
    print(f"  Accuracy   : {accuracy*100:.2f}%")
    print(f"  Coverage   : {coverage*100:.2f}%")
    print(f"  Sel. Acc.  : {sel_acc*100:.2f}%")
    print(f"  Reject Rate: {reject_rate*100:.2f}%")
    if avg_stats.get("macro"):
        m = avg_stats["macro"]
        print(f"  Macro F1   : {m['f1']:.4f}  (P={m['precision']:.4f} R={m['recall']:.4f})")
    if avg_stats.get("weighted"):
        w = avg_stats["weighted"]
        print(f"  Weighted F1: {w['f1']:.4f}  (P={w['precision']:.4f} R={w['recall']:.4f})")
    if lat_met:
        print(
            f"  Latency    : avg={lat_met['avg_ms']} ms"
            f"  p50={lat_met['p50_ms']} ms"
            f"  p95={lat_met['p95_ms']} ms"
            f"  p99={lat_met['p99_ms']} ms"
        )
    print(f"\n  Per-language F1:")
    for lang, m in per_lang.items():
        print(f"    {lang:4s}  P={m['precision']:.3f}  R={m['recall']:.3f}  "
              f"F1={m['f1']:.3f}  support={m['support']}")
    if open_met.get("false_detection_rate") is not None:
        print(
            f"\n  Open-set: {open_met['false_detected']}/{open_met['total_non_natural']}"
            f" non-natural inputs incorrectly got language assigned"
            f" (rate={open_met['false_detection_rate']:.1%})"
        )
    print(f"\n{SEP}\n")

    # Save report
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Report saved -> {output_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Compute detection metrics from raw JSONL result.")
    parser.add_argument("--input", "-i", required=True, help="Path to raw JSONL result file")
    parser.add_argument("--output", "-o", default=None, help="Path to save JSON report")
    args = parser.parse_args()

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.splitext(os.path.basename(args.input))[0]
        out_dir = os.path.join(os.path.dirname(args.input), "../results/reports")
        args.output = os.path.join(out_dir, f"report_{base}_{ts}.json")

    run(args.input, args.output)


if __name__ == "__main__":
    main()
