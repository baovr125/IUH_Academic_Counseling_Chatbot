"""Chạy sinh từ vựng trên bộ dữ liệu đánh giá và ghi kết quả từng lần chạy (JSONL) + tổng hợp chỉ số (JSON).

Hai biến thể để so sánh (ablation):
  three_stage  pipeline production: SELECT -> ENRICH -> VERIFY (phương án B)
  single_call  đối chứng: MỘT lần gọi LLM sinh đủ trường, chỉ có kiểm tra bằng mã (phương án A, chỉ dùng để đánh giá)

Ví dụ (tốn lượt gọi LLM thật; cần GROQ_API_KEY/GEMINI_API_KEY trong .env hoặc môi trường):
  python -m evaluation.run_vocab_eval --variant three_stage --dataset topics --limit 10 --out results/topics_B
  python -m evaluation.run_vocab_eval --variant single_call --dataset topics --limit 10 --out results/topics_A
  python -m evaluation.run_vocab_eval --variant three_stage --dataset passages --out results/passages_B
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from evaluation.common import (  # noqa: E402
    EVAL_DIR, append_jsonl, load_env, read_jsonl, summarise_runs, with_outage_retry,
)

load_env("GROQ_API_KEY", "GEMINI_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_KEY", "OPENAI_MODEL_NAME")

from app.schemas.vocabulary import GenerateVocabRequest  # noqa: E402
from app.services import llm_client, vocab_pipeline as vp  # noqa: E402
from app.services.normalization import dedupe_key  # noqa: E402


def single_call_prompt(req: GenerateVocabRequest, n: int) -> str:
    topic = vp._fence_safe(req.topic) if req.mode == "topic" else "(passage)"
    source = (f"topic: {topic}" if req.mode == "topic" else f"passage: {vp._fence_safe(req.text)}")
    purpose = vp.PURPOSE_HINTS.get(req.purpose or "general", vp.PURPOSE_HINTS["general"])
    return (
        f"Create {n} English vocabulary flashcards for Vietnamese learners.\n"
        f"<user_input>\n{source}\ncefr_level: {req.level}\npurpose: {purpose}\n</user_input>\n"
        f"Each item: term (dictionary headword, base form), pos ({vp.POS_LIST}), ipa (General American IPA between slashes), "
        f"definition_vi (concise Vietnamese meaning, max 12 words, ONE sense), example (one natural English sentence, "
        f"8-18 words, CEFR {req.level}, containing the term exactly as written), example_vi (Vietnamese translation).\n"
        f"Output: {{\"items\":[{{\"term\":\"\",\"pos\":\"\",\"ipa\":\"\",\"definition_vi\":\"\",\"example\":\"\",\"example_vi\":\"\"}}]}}"
    )


async def generate_single_call(req: GenerateVocabRequest) -> Dict[str, Any]:
    """Đối chứng: một lời gọi LLM + kiểm tra/chuẩn hóa bằng mã giống production (không có bước VERIFY)."""
    started = time.monotonic()
    n = req.count + max(1, round(req.count * 0.1))
    try:
        result = await llm_client.generate_json(
            vp.SYSTEM_ENRICH, single_call_prompt(req, n), temperature=0.4, max_tokens=min(8192, 300 + 190 * n), timeout=50.0
        )
    except llm_client.LLMError as exc:
        raise vp._map_llm_error(exc) from exc

    seen, items, dropped, raw_count = set(), [], [], 0
    for raw in [x for x in result.data.get("items", []) if isinstance(x, dict)]:
        raw_count += 1
        cand = vp.sanitize_candidate(raw)
        if not cand:
            dropped.append({"term": str(raw.get("term")), "reason": "invalid_term"})
            continue
        key = dedupe_key(cand["term"])
        if key in seen:
            dropped.append({"term": cand["term"], "reason": "duplicate_or_known"})
            continue
        seen.add(key)
        item, reason = vp.validate_enriched(raw, cand, req.level)
        if item is None:
            dropped.append({"term": cand["term"], "reason": reason or "invalid"})
        else:
            items.append(item)
    if not items:
        raise vp.VocabError(502, "LLM_BAD_OUTPUT", "no valid items")
    final = items[: req.count]
    for i, it in enumerate(final, 1):
        it["temp_id"] = f"g{i}"
    return {
        "generation_id": uuid.uuid4().hex[:16], "mode": req.mode, "topic": req.topic, "level": req.level,
        "requested": req.count, "returned": len(final), "items": final, "dropped": dropped, "providers": [result.provider],
        "stages": {"llm_calls": 1, "rounds": 1, "candidates": raw_count, "enriched_valid": len(items), "rejected": 0, "fixed": 0,
                   "unverified": len(final)},
        "latency_ms": int((time.monotonic() - started) * 1000),
        "usage": {"prompt_tokens": result.prompt_tokens, "completion_tokens": result.completion_tokens},
    }


def build_request(row: Dict[str, Any], dataset: str) -> GenerateVocabRequest:
    if dataset == "passages":
        return GenerateVocabRequest(mode="text", text=row["text"], level=row["level"], count=row.get("count", 10))
    return GenerateVocabRequest(mode="topic", topic=row["topic"], level=row["level"], count=row["count"], purpose=row.get("purpose"))


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["three_stage", "single_call"], default="three_stage")
    ap.add_argument("--dataset", choices=["topics", "passages"], default="topics")
    ap.add_argument("--limit", type=int, default=0, help="chỉ chạy N mẫu đầu (0 = tất cả)")
    ap.add_argument("--only", help="id cách nhau bằng dấu phẩy (vd T01,T05)")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--count", type=int, default=0, help="ghi đè số từ yêu cầu (vd 10 để vừa hạn mức 8.000 token/phút của Groq free)")
    ap.add_argument("--sleep", type=float, default=2.0, help="nghỉ giữa các lần chạy (giây) để tránh chạm giới hạn")
    ap.add_argument("--out", required=True, help="tiền tố tệp kết quả (thêm .jsonl và .summary.json)")
    ap.add_argument("--resume", action="store_true", help="bỏ qua các (id, lần lặp) đã có trong tệp kết quả")
    args = ap.parse_args()

    data = read_jsonl(EVAL_DIR / "dataset" / f"{args.dataset}.jsonl")
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        data = [r for r in data if r["id"] in wanted]
    if args.limit:
        data = data[: args.limit]

    out = Path(args.out) if Path(args.out).is_absolute() else EVAL_DIR / args.out
    rows_path = out.with_suffix(".jsonl")
    done = set()
    if args.resume and rows_path.exists():
        done = {(r["id"], r["repeat"]) for r in read_jsonl(rows_path) if not r.get("error") or r["error"]["code"] not in {"LLM_UNAVAILABLE", "LLM_TIMEOUT"}}
    elif rows_path.exists():
        rows_path.unlink()

    run = vp.generate_vocabulary if args.variant == "three_stage" else generate_single_call
    for row in data:
        for rep in range(1, args.repeat + 1):
            if (row["id"], rep) in done:
                continue
            if args.count:
                row = {**row, "count": args.count}
            req = build_request(row, args.dataset)
            print(f"- {row['id']} #{rep} {row.get('topic') or row['domain']} ({row['level']}, {req.count}) [{args.variant}]", flush=True)
            result, error = await with_outage_retry(lambda: run(req))
            record: Dict[str, Any] = {"id": row["id"], "repeat": rep, "variant": args.variant, "dataset": args.dataset,
                                      "level": row["level"], "purpose": row.get("purpose"), "requested": req.count}
            if error:
                record["error"] = {"code": error.code, "status": error.status}
                print(f"    LỖI {error.code}", flush=True)
            else:
                record.update(result)
                print(f"    {result['returned']}/{result['requested']} từ, {result['latency_ms']} ms, calls={result['stages']['llm_calls']}", flush=True)
            append_jsonl(rows_path, record)
            await asyncio.sleep(args.sleep)

    rows = read_jsonl(rows_path)
    summary = {"variant": args.variant, "dataset": args.dataset, **summarise_runs(rows)}
    out.with_suffix(".summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
