"""
evaluation/benchmarks/run_latency_benchmark.py
===============================================
Benchmark latency riêng cho Language Detection (tách khỏi translation pipeline).

Đo 3 trạng thái:
  1. cold  – lần gọi đầu tiên (model chưa cache)
  2. warm  – sau warm-up (model đã trong LRU cache)
  3. batch – 100 mẫu sequential

Đo 3 phương thức:
  A. function-level: gọi trực tiếp detect_language_detailed() (đường production)
  B. fasttext-only:  gọi trực tiếp fasttext_topk()
  C. lingua-only:    gọi trực tiếp ld._lingua_distribution()

Output:
  - Console table
  - JSONL raw per-sample: evaluation/raw_results/latency_*.jsonl
  - Summary JSON: evaluation/raw_results/latency_summary_*.json

Không tính NLLB, Redis, authentication, network.
"""

import os
import sys
import json
import time
import statistics
import datetime
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Tắt cache kết quả nhận diện để mọi lần đo là tính toán thật (không phải cache hit).
os.environ["DETECT_CACHE_SIZE"] = "0"

from app.services import language_detection as ld
from app.services.fasttext_detector import fasttext_topk, _get_fasttext_model

import logging
logging.disable(logging.CRITICAL)

_HERE = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(_HERE, "../raw_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Representative texts per workload type
# ---------------------------------------------------------------------------

SAMPLE_TEXTS = {
    "vi_long": "Trí tuệ nhân tạo đang thay đổi ngành giáo dục một cách nhanh chóng và sâu sắc.",
    "en_long": "Machine learning algorithms identify complex patterns in large datasets with high accuracy.",
    "vi_short": "Xin chào bạn",
    "en_short": "Hello world",
    "de_long": "Maschinelles Lernen verändert den Bildungssektor grundlegend und bietet neue Möglichkeiten.",
    "zh_long": "人工智能正在迅速改变教育领域，并提供新的可能性。",
    "ambiguous": "ok",
    "html_vi": "<p>Trí tuệ nhân tạo <strong>thay đổi</strong> giáo dục</p>",
    "vi_noaccent": "toi dang hoc lap trinh tai truong dai hoc cong nghiep",
    "codesw": "Hôm nay tôi có meeting với team về deadline quan trọng",
}


def percentile(data: list[float], pct: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * pct / 100
    f = int(k)
    c = f + 1
    if c >= len(s):
        return s[-1]
    return s[f] + (k - f) * (s[c] - s[f])


def measure_fasttext(text: str) -> dict:
    t0 = time.perf_counter()
    top = fasttext_topk(text, k=2)
    lat = (time.perf_counter() - t0) * 1000
    lang, conf = (top[0] if top else (None, 0.0))
    margin = conf - (top[1][1] if len(top) > 1 else 0.0)
    return {"lang": lang, "confidence": conf, "margin": margin, "latency_ms": lat}


def measure_lingua(text: str) -> dict:
    t0 = time.perf_counter()
    try:
        dist = ld._lingua_distribution(text)
        ranked = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
        lang = ranked[0][0] if ranked else None
        conf = ranked[0][1] if ranked else 0.0
        margin = (ranked[0][1] - ranked[1][1]) if len(ranked) > 1 else 0.0
    except Exception:
        lang, conf, margin = None, 0.0, 0.0
    lat = (time.perf_counter() - t0) * 1000
    return {"lang": lang, "confidence": conf, "margin": margin, "latency_ms": lat}


def measure_hybrid(text: str) -> dict:
    """Đường production `detect_language_detailed` (cache kết quả đã tắt)."""
    t0 = time.perf_counter()
    details = ld.detect_language_detailed(text)
    lat = (time.perf_counter() - t0) * 1000
    return {"lang": details.resolved_source_lang, "status": details.status, "latency_ms": lat}


# ---------------------------------------------------------------------------
# Benchmark scenarios
# ---------------------------------------------------------------------------

def benchmark_cold_warm() -> dict:
    """Single call cold vs single call warm (after warm-up)."""
    print("\n[1] Cold vs Warm benchmark ...")
    results = {}

    for label, text in SAMPLE_TEXTS.items():
        # Warm-up FastText and Lingua
        _get_fasttext_model()
        ld._get_lingua()

        ft_warm = measure_fasttext(text)
        lg_warm = measure_lingua(text)
        hy_warm = measure_hybrid(text)

        results[label] = {
            "fasttext_warm_ms": round(ft_warm["latency_ms"], 3),
            "lingua_warm_ms":   round(lg_warm["latency_ms"], 3),
            "hybrid_warm_ms":   round(hy_warm["latency_ms"], 3),
        }
        print(
            f"  {label:15s}  "
            f"ft={ft_warm['latency_ms']:.2f}ms  "
            f"lingua={lg_warm['latency_ms']:.2f}ms  "
            f"hybrid={hy_warm['latency_ms']:.2f}ms"
        )

    return results


def benchmark_batch(n: int = 100) -> dict:
    """Run n sequential calls for each method and compute percentiles."""
    print(f"\n[2] Batch benchmark ({n} sequential calls per method) ...")

    # Use a rotating set of texts
    texts = list(SAMPLE_TEXTS.values())
    methods = {
        "fasttext": measure_fasttext,
        "lingua":   measure_lingua,
        "hybrid":   measure_hybrid,
    }

    raw_records = []
    latency_per_method = {m: [] for m in methods}

    for i in range(n):
        text = texts[i % len(texts)]
        for method_name, fn in methods.items():
            r = fn(text)
            record = {
                "idx": i,
                "text_key": list(SAMPLE_TEXTS.keys())[i % len(SAMPLE_TEXTS)],
                "method": method_name,
                **r,
            }
            raw_records.append(record)
            latency_per_method[method_name].append(r["latency_ms"])

    summary = {}
    for method_name, lats in latency_per_method.items():
        summary[method_name] = {
            "n":      len(lats),
            "avg_ms": round(statistics.mean(lats), 3),
            "p50_ms": round(percentile(lats, 50), 3),
            "p95_ms": round(percentile(lats, 95), 3),
            "p99_ms": round(percentile(lats, 99), 3),
            "max_ms": round(max(lats), 3),
            "min_ms": round(min(lats), 3),
        }
        s = summary[method_name]
        print(
            f"  {method_name:10s}  "
            f"avg={s['avg_ms']} ms  "
            f"p50={s['p50_ms']} ms  "
            f"p95={s['p95_ms']} ms  "
            f"p99={s['p99_ms']} ms  "
            f"max={s['max_ms']} ms"
        )

    return {"per_method": summary, "raw": raw_records}


def benchmark_text_length() -> dict:
    """Compare latency across different text lengths."""
    print("\n[3] Text-length sensitivity benchmark ...")

    lengths = {
        "1_word":    "hello",
        "5_words":   "hello world this is test",
        "20_words":  "Machine learning is transforming the educational sector by providing new possibilities for students",
        "50_words":  ("Artificial intelligence and machine learning are rapidly transforming many industries including "
                      "education healthcare finance and transportation by automating complex tasks providing insights "
                      "from large datasets and enabling new applications that were not previously possible"),
        "100_words": ("The field of artificial intelligence has seen remarkable progress over the past decade "
                      "driven by advances in machine learning deep learning and natural language processing. "
                      "These technologies are now being applied in virtually every industry from healthcare and finance "
                      "to education and entertainment. In the education sector AI is helping to personalize learning "
                      "experiences identify at-risk students and automate administrative tasks. Language detection "
                      "is a fundamental capability that enables multilingual applications to serve users in their "
                      "preferred language automatically without requiring manual language selection by the user."),
    }

    results = {}
    for label, text in lengths.items():
        ft = measure_fasttext(text)
        lg = measure_lingua(text)
        hy = measure_hybrid(text)
        results[label] = {
            "word_count": len(text.split()),
            "fasttext_ms": round(ft["latency_ms"], 3),
            "lingua_ms":   round(lg["latency_ms"], 3),
            "hybrid_ms":   round(hy["latency_ms"], 3),
        }
        print(
            f"  {label:12s} ({len(text.split()):4d} words)  "
            f"ft={ft['latency_ms']:.2f}ms  "
            f"lingua={lg['latency_ms']:.2f}ms  "
            f"hybrid={hy['latency_ms']:.2f}ms"
        )

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_latency_benchmark(batch_n: int = 100) -> dict:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\nWarming up all detectors ...")
    ld.warm_up()

    cold_warm  = benchmark_cold_warm()
    batch      = benchmark_batch(n=batch_n)
    text_len   = benchmark_text_length()

    summary = {
        "timestamp":     timestamp,
        "batch_n":       batch_n,
        "cold_warm":     cold_warm,
        "batch_summary": batch["per_method"],
        "text_length":   text_len,
    }

    # Save raw batch records
    raw_path = os.path.join(RESULTS_DIR, f"latency_raw_{timestamp}.jsonl")
    with open(raw_path, "w", encoding="utf-8") as f:
        for row in batch["raw"]:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary_path = os.path.join(RESULTS_DIR, f"latency_summary_{timestamp}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nRaw records -> {raw_path}")
    print(f"Summary     -> {summary_path}")

    SEP = "=" * 65
    print(f"\n{SEP}")
    print(f"  LATENCY BENCHMARK COMPLETE  ({timestamp})")
    print(SEP)
    if batch.get("per_method"):
        for method, s in batch["per_method"].items():
            print(
                f"  {method:10s}  "
                f"p50={s['p50_ms']} ms  "
                f"p95={s['p95_ms']} ms  "
                f"p99={s['p99_ms']} ms"
            )
    print(SEP)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=100, help="Number of sequential calls for batch benchmark")
    args = parser.parse_args()
    run_latency_benchmark(batch_n=args.batch)
