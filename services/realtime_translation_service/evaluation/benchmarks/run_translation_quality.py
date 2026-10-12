"""TQ-01/LT-01: NLLB (chế độ dịch thông thường) trên các cặp tham chiếu; TQ-02: chấm bản dịch LLM đã chạy sẵn.

  python evaluation/benchmarks/run_translation_quality.py nllb --refs <jsonl> --out <json>
  python evaluation/benchmarks/run_translation_quality.py score --refs <jsonl> --raw <domain_raw.jsonl> --out <json>

- `nllb`: gọi `run_nllb_only` (hàm production), warm-up 3 câu, đo thời gian từng câu, chrF/BLEU bằng sacrebleu.
- `score`: chấm chrF/BLEU cho trường `output` của file thô do `run_domain_raw.py` sinh ra (cùng id).
"""
import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
os.environ.setdefault("TESTING", "1")
logging.disable(logging.CRITICAL)


def pct(values, p):
    s = sorted(values)
    return s[min(len(s) - 1, max(0, int(round(p / 100 * (len(s) - 1)))))]


def corpus_scores(hyps, refs):
    import sacrebleu

    return {"chrF": sacrebleu.corpus_chrf(hyps, [refs]).score, "BLEU": sacrebleu.corpus_bleu(hyps, [refs]).score,
            "sacrebleu": sacrebleu.__version__}


async def run_nllb(rows):
    from app.services.translation_service import run_nllb_only

    for r in rows[:3]:  # warm-up (nạp model + CUDA)
        await run_nllb_only(r["text"], "en", "vi")
    hyps, times = [], []
    for r in rows:
        s = time.perf_counter()
        hyps.append(await run_nllb_only(r["text"], "en", "vi"))
        times.append((time.perf_counter() - s) * 1000)
    return hyps, times


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["nllb", "score"])
    ap.add_argument("--refs", required=True)
    ap.add_argument("--raw")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = [json.loads(l) for l in open(args.refs, encoding="utf-8") if l.strip()]
    refs = [r["reference"] for r in rows]

    if args.mode == "nllb":
        t0 = time.perf_counter()
        hyps, times = asyncio.run(run_nllb(rows))
        result = {"system": "nllb-200-distilled-600M (ctranslate2, run_nllb_only)", "samples": len(rows),
                  "wall_s": time.perf_counter() - t0, **corpus_scores(hyps, refs),
                  "latency_ms": {"p50": statistics.median(times), "p95": pct(times, 95), "max": max(times),
                                 "mean": statistics.mean(times)},
                  "items": [{"id": r["id"], "source": r["text"], "reference": r["reference"], "hypothesis": h, "ms": t}
                            for r, h, t in zip(rows, hyps, times)]}
    else:
        raw = {json.loads(l)["id"]: json.loads(l) for l in open(args.raw, encoding="utf-8") if l.strip()}
        missing = [r["id"] for r in rows if r["id"] not in raw or not raw[r["id"]].get("ok")]
        kept = [r for r in rows if r["id"] not in missing]
        hyps = [raw[r["id"]].get("output") or "" for r in kept]
        result = {"system": f"llm auto ({next(iter(raw.values())).get('model')})", "samples": len(kept),
                  "missing_or_failed": missing, **corpus_scores(hyps, [r["reference"] for r in kept]),
                  "items": [{"id": r["id"], "reference": r["reference"], "hypothesis": h,
                             "domain": raw[r["id"]].get("header_domain")} for r, h in zip(kept, hyps)]}
    json.dump(result, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "items"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
