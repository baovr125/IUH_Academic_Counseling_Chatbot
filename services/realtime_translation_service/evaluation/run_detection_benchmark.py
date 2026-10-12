import json
import time
import os
import sys
import statistics
import datetime
import argparse

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services import language_detection as ld
from app.services.fasttext_detector import fasttext_topk
from app.utils.logger import logger

import logging
logger.setLevel(logging.ERROR)

# ---------------------------------------------------------------------------
# Dataset paths
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(__file__)
DATASET_JSON = os.path.join(_HERE, "dataset/lang_detection_dataset.json")
DATASET_DEV  = os.path.join(_HERE, "dataset/lang_detection_dev.jsonl")
RESULTS_DIR  = os.path.join(_HERE, "raw_results")
os.makedirs(RESULTS_DIR, exist_ok=True)
VALID_STATUSES = {"detected", "uncertain", "unknown", "unsupported", "invalid_input", "system_error"}


def load_dataset(path=None):
    """Load JSON or JSONL automatically. Supports legacy and new schema."""
    chosen = path or (DATASET_DEV if os.path.exists(DATASET_DEV) else DATASET_JSON)
    items = []
    with open(chosen, "r", encoding="utf-8") as f:
        if chosen.endswith(".jsonl"):
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        else:
            data = json.load(f)
            # Normalize legacy schema: expected_lang -> expected_primary_language
            for d in data:
                if "expected_lang" in d and "expected_primary_language" not in d:
                    d["expected_primary_language"] = d["expected_lang"]
                if "expected_languages" not in d:
                    primary = d.get("expected_primary_language")
                    d["expected_languages"] = [primary] if primary else []
                if "category" not in d:
                    d["category"] = "legacy"
                if "expected_status" not in d:
                    d["expected_status"] = "detected" if d.get("expected_primary_language") else "unknown"
                if "is_valid_detection_target" not in d:
                    d["is_valid_detection_target"] = True
            items = data
    validate_dataset(items, chosen)
    print(f"Loaded {len(items)} samples from: {chosen}")
    return items


def validate_dataset(items, source="dataset"):
    """Validate the Phase 1 ground-truth contract before running a benchmark."""
    required = {"id", "text", "category", "expected_primary_language", "expected_status"}
    seen = set()
    errors = []
    for index, item in enumerate(items, start=1):
        missing = required - item.keys()
        if missing:
            errors.append(f"row {index}: missing {sorted(missing)}")
        item_id = item.get("id")
        if item_id in seen:
            errors.append(f"row {index}: duplicate id {item_id}")
        seen.add(item_id)
        if item.get("expected_status") not in VALID_STATUSES:
            errors.append(f"row {index}: invalid expected_status={item.get('expected_status')}")
        if not isinstance(item.get("expected_languages", []), list):
            errors.append(f"row {index}: expected_languages must be a list")
    if errors:
        raise ValueError(f"Invalid detection dataset {source}: " + "; ".join(errors[:10]))


def expected_result(item, predicted, actual_status):
    """Return language correctness and status correctness separately."""
    expected_status = item.get("expected_status", "detected")
    language_correct = (
        expected_status == "detected"
        and predicted == item.get("expected_primary_language")
        and actual_status == "detected"
    )
    status_correct = actual_status == expected_status
    return language_correct, status_correct


# ---------------------------------------------------------------------------
# Engine wrappers
# ---------------------------------------------------------------------------

def evaluate_lingua_only(text):
    """Lingua thuần (tập ngôn ngữ mở rộng của service). Trả (mã hỗ trợ | None, top, margin)."""
    clean_text = text.replace("\n", " ").strip()
    try:
        dist = ld._lingua_distribution(clean_text)
        if not dist:
            return None, 0.0, 0.0
        ranked = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
        top_code, top_value = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else 0.0
        lang_code = top_code if top_code in ld.SUPPORTED_CODES else None
        return lang_code, float(top_value), float(top_value - second)
    except Exception:
        return None, 0.0, 0.0


def evaluate_fasttext_only(text):
    """fastText thuần (top-2 để tính margin). Nhãn ngoài phạm vi dịch vụ → None."""
    top = fasttext_topk(text, k=2)
    if not top:
        return None, 0.0, 0.0
    code, score = top[0]
    second = top[1][1] if len(top) > 1 else 0.0
    return (code if code in ld.SUPPORTED_CODES else None), float(score), float(score - second)


def evaluate_hybrid(text):
    """ĐƯỜNG PRODUCTION: `detect_language_detailed` (cùng hàm /text, /stream, /detect gọi).

    Trả (mã ngôn ngữ | None, status thật của service, chi tiết). Không còn quy mọi lỗi về "unknown".
    """
    details = ld.detect_language_detailed(text)
    return details.resolved_source_lang, details.status, details


# ---------------------------------------------------------------------------
# Percentile helper
# ---------------------------------------------------------------------------

def percentile(data, pct):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * pct / 100
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


# ---------------------------------------------------------------------------
# Main benchmark
# ---------------------------------------------------------------------------

def run_benchmark(dataset_path=None):
    dataset = load_dataset(dataset_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    engines = ["fasttext", "lingua", "hybrid"]
    raw = {e: [] for e in engines}
    latencies = {e: [] for e in engines}

    print("\nWarming up detectors ...")
    ld.warm_up()
    print(f"Running {len(dataset)} samples ...\n")

    for item in dataset:
        text            = item["text"]
        expected_lang   = item.get("expected_primary_language") or item.get("expected_lang")
        expected_status = item.get("expected_status", "detected")
        is_valid        = item.get("is_valid_detection_target", True)
        item_id         = item.get("id", "?")
        category        = item.get("category", "unknown")
        expected_langs  = item.get("expected_languages", [expected_lang] if expected_lang else [])
        notes           = item.get("notes", "")

        # -- FastText ---------------------------------------------------------
        t0 = time.perf_counter()
        ft_lang, ft_conf, ft_margin = evaluate_fasttext_only(text)
        ft_lat = (time.perf_counter() - t0) * 1000
        ft_status = "detected" if ft_lang else "unknown"
        ft_correct, ft_status_correct = expected_result(item, ft_lang, ft_status)
        raw["fasttext"].append({
            "id": item_id,
            "text": text[:80],
            "category": category,
            "expected_languages": expected_langs,
            "expected_primary_language": expected_lang,
            "expected_status": expected_status,
            "notes": notes,
            "is_valid": is_valid,
            "predicted": ft_lang,
            "status": ft_status,
            "engine": "fasttext",
            "confidence": round(ft_conf, 4),
            "margin": round(ft_margin, 4),
            "latency_ms": round(ft_lat, 3),
            "correct": ft_correct if is_valid else None,
            "status_correct": ft_status_correct,
            "error": None,
        })
        latencies["fasttext"].append(ft_lat)

        # -- Lingua -----------------------------------------------------------
        t0 = time.perf_counter()
        lg_lang, lg_conf, lg_margin = evaluate_lingua_only(text)
        lg_lat = (time.perf_counter() - t0) * 1000
        lg_status = "detected" if lg_lang else "unknown"
        lg_correct, lg_status_correct = expected_result(item, lg_lang, lg_status)
        raw["lingua"].append({
            "id": item_id,
            "text": text[:80],
            "category": category,
            "expected_languages": expected_langs,
            "expected_primary_language": expected_lang,
            "expected_status": expected_status,
            "notes": notes,
            "is_valid": is_valid,
            "predicted": lg_lang,
            "status": lg_status,
            "engine": "lingua",
            "confidence": round(lg_conf, 4),
            "margin": round(lg_margin, 4),
            "latency_ms": round(lg_lat, 3),
            "correct": lg_correct if is_valid else None,
            "status_correct": lg_status_correct,
            "error": None,
        })
        latencies["lingua"].append(lg_lat)

        # -- Hybrid (full pipeline) -------------------------------------------
        t0 = time.perf_counter()
        hy_lang, hy_status, hy_details = evaluate_hybrid(text)
        hy_lat = (time.perf_counter() - t0) * 1000
        hy_correct, hy_status_correct = expected_result(item, hy_lang, hy_status)
        raw["hybrid"].append({
            "id": item_id,
            "text": text[:80],
            "category": category,
            "expected_languages": expected_langs,
            "expected_primary_language": expected_lang,
            "expected_status": expected_status,
            "notes": notes,
            "is_valid": is_valid,
            "predicted": hy_lang,
            "status": hy_status,
            "engine": "hybrid",
            "service_engine": hy_details.engine,
            "reason": hy_details.reason,
            "detected_language": hy_details.detected_language,
            "confidence": round(hy_details.confidence, 4),
            "margin": round(hy_details.margin, 4),
            "latency_ms": round(hy_lat, 3),
            "correct": hy_correct if is_valid else None,
            "status_correct": hy_status_correct,
            "error": None,
        })
        latencies["hybrid"].append(hy_lat)

    # -- Aggregate metrics ----------------------------------------------------
    summary = {}
    for engine in engines:
        rows          = raw[engine]
        valid_rows    = [r for r in rows if r["is_valid"]]
        accepted_rows = [r for r in valid_rows if r["predicted"] is not None]
        correct_rows  = [r for r in accepted_rows if r["correct"]]
        status_correct = sum(1 for r in rows if r.get("status_correct"))

        total       = len(rows)
        valid_total = len(valid_rows)
        accepted    = len(accepted_rows)
        correct     = len(correct_rows)

        accuracy    = correct  / valid_total if valid_total else 0.0
        coverage    = accepted / valid_total if valid_total else 0.0
        sel_acc     = correct  / accepted    if accepted    else 0.0

        lats = latencies[engine]
        summary[engine] = {
            "total_samples":      total,
            "valid_samples":      valid_total,
            "accepted":           accepted,
            "correct":            correct,
            "status_correct":     status_correct,
            "status_accuracy":    round(status_correct / total, 4) if total else 0.0,
            "accuracy":           round(accuracy, 4),
            "coverage":           round(coverage, 4),
            "selective_accuracy": round(sel_acc, 4),
            "reject_rate":        round(1.0 - coverage, 4),
            "avg_latency_ms":     round(statistics.mean(lats), 3) if lats else 0,
            "p50_latency_ms":     round(percentile(lats, 50), 3),
            "p95_latency_ms":     round(percentile(lats, 95), 3),
            "p99_latency_ms":     round(percentile(lats, 99), 3),
            "max_latency_ms":     round(max(lats), 3) if lats else 0,
        }

    # -- Save raw results -----------------------------------------------------
    for engine in engines:
        out_path = os.path.join(RESULTS_DIR, f"detection_{engine}_{timestamp}.jsonl")
        with open(out_path, "w", encoding="utf-8") as f:
            for row in raw[engine]:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Raw results saved -> {out_path}")

    summary_path = os.path.join(RESULTS_DIR, f"detection_summary_{timestamp}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"timestamp": timestamp, "engines": summary}, f, ensure_ascii=False, indent=2)
    print(f"Summary saved      -> {summary_path}")

    # -- Print report ---------------------------------------------------------
    SEP = "=" * 60
    print(f"\n{SEP}")
    print(f"  DETECTION BENCHMARK REPORT  ({timestamp})")
    print(SEP)
    for engine, s in summary.items():
        print(f"\n  Engine : {engine.upper()}")
        print(
            f"  Samples: {s['total_samples']}"
            f"  (valid: {s['valid_samples']}, accepted: {s['accepted']})"
        )
        print(f"  Accuracy          : {s['accuracy']*100:.2f}%")
        print(f"  Coverage          : {s['coverage']*100:.2f}%")
        print(f"  Selective Accuracy: {s['selective_accuracy']*100:.2f}%")
        print(f"  Reject Rate       : {s['reject_rate']*100:.2f}%")
        print(
            f"  Latency (ms)  avg={s['avg_latency_ms']}"
            f"  p50={s['p50_latency_ms']}"
            f"  p95={s['p95_latency_ms']}"
            f"  p99={s['p99_latency_ms']}"
            f"  max={s['max_latency_ms']}"
        )
    print(f"\n{SEP}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Language Detection benchmark")
    parser.add_argument("--dataset", default=None, help="JSON/JSONL ground-truth dataset")
    parser.add_argument("--output-dir", default=RESULTS_DIR, help="Directory for raw results")
    args = parser.parse_args()
    RESULTS_DIR = os.path.abspath(args.output_dir)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    run_benchmark(args.dataset)
