"""Chấm chất lượng thẻ: phiếu chấm tay (1 người), LLM-judge đối chiếu, và tính điểm.

  python -m evaluation.rating make  --results results/topics_B.jsonl --n 100 --seed 7 --out results/rating_sheet.csv
      -> tạo phiếu CSV (mở bằng Excel) để người chấm điền các cột *_ok / topic_relevant / level_fit
  python -m evaluation.rating judge --results results/topics_B.jsonl --n 100 --seed 7 --out results/judge.jsonl
      -> LLM-judge chấm đúng các thẻ đó (nên khác mô hình sinh: mặc định ép dùng Gemini để giảm thiên lệch tự ưu ái)
  python -m evaluation.rating judge-summary --judge results/judge.jsonl
      -> tỷ lệ chấp nhận theo LLM-judge (khi chưa có người chấm)
  python -m evaluation.rating score --sheet results/rating_sheet.csv [--judge results/judge.jsonl]
      -> tỷ lệ chấp nhận + khoảng tin cậy Wilson 95%; nếu có --judge thì thêm Cohen's kappa giữa người và LLM-judge

Thang điểm (cột điền trên phiếu):
  definition_ok / example_ok / translation_ok : 0 = sai, 1 = chấp nhận được, 2 = tốt
  topic_relevant                              : 0 = lạc đề, 1 = đúng chủ đề
  level_fit                                   : 0 = sai trình độ (quá dễ/khó), 1 = phù hợp
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

from evaluation.common import EVAL_DIR, cohen_kappa, fmt_pct, load_env, read_jsonl, with_outage_retry, write_jsonl

DIMENSIONS = ["definition_ok", "example_ok", "translation_ok", "topic_relevant", "level_fit"]
THREE_POINT = {"definition_ok", "example_ok", "translation_ok"}


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else EVAL_DIR / p


def sample_items(results_path: Path, n: int, seed: int) -> List[Dict[str, Any]]:
    """Mẫu phân tầng theo trình độ, cố định theo seed để phiếu và LLM-judge chấm cùng một tập thẻ."""
    pool: List[Dict[str, Any]] = []
    for row in read_jsonl(results_path):
        if row.get("error"):
            continue
        for item in row["items"]:
            pool.append({"item_id": f"{row['id']}#{row['repeat']}:{item['temp_id']}", "level": row["level"], "run": row["id"],
                         "topic": row.get("topic") or "(passage)", "mode": row["mode"], **{k: item[k] for k in
                         ("term", "part_of_speech", "ipa", "definition", "example", "example_translation")}})
    rng = random.Random(seed)
    by_level: Dict[str, List[Dict[str, Any]]] = {}
    for it in pool:
        by_level.setdefault(it["level"], []).append(it)
    for items in by_level.values():
        rng.shuffle(items)
    chosen: List[Dict[str, Any]] = []
    while len(chosen) < min(n, len(pool)):
        for level in sorted(by_level):
            if by_level[level] and len(chosen) < n:
                chosen.append(by_level[level].pop())
    return chosen


def cmd_make(args) -> None:
    items = sample_items(resolve(args.results), args.n, args.seed)
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["item_id", "level", "topic", "term", "part_of_speech", "ipa", "definition_vi", "example", "example_vi"]
                        + DIMENSIONS + ["note"])
        for it in items:
            writer.writerow([it["item_id"], it["level"], it["topic"], it["term"], it["part_of_speech"], it["ipa"], it["definition"],
                             it["example"], it["example_translation"]] + [""] * (len(DIMENSIONS) + 1))
    print(f"Đã tạo phiếu {len(items)} thẻ: {out}\nĐiền các cột {', '.join(DIMENSIONS)} theo thang trong docstring của rating.py.")


JUDGE_SYSTEM = (
    "You are an independent, strict evaluator of English-Vietnamese vocabulary flashcards. "
    "Respond with ONE JSON object and nothing else."
)


def judge_prompt(batch: List[Dict[str, Any]]) -> str:
    cards = [{"item_id": b["item_id"], "level": b["level"], "topic": b["topic"], "term": b["term"], "pos": b["part_of_speech"],
              "ipa": b["ipa"], "definition_vi": b["definition"], "example": b["example"], "example_vi": b["example_translation"]} for b in batch]
    return (
        "Rate each flashcard.\n"
        "definition_ok / example_ok / translation_ok: 0 = wrong, 1 = acceptable, 2 = good. "
        "(definition_ok: Vietnamese meaning correct for the pos; example_ok: grammatical, natural, uses the term, suits the level; "
        "translation_ok: Vietnamese translation of the example is accurate.)\n"
        "topic_relevant: 1 if the term suits the topic (for topic '(passage)' use 1), else 0. "
        "level_fit: 1 if the term suits the CEFR level, else 0.\n"
        f"Cards (JSON): {json.dumps(cards, ensure_ascii=False)}\n"
        'Output: {"ratings":[{"item_id":"","definition_ok":0,"example_ok":0,"translation_ok":0,"topic_relevant":0,"level_fit":0}]}'
    )


async def cmd_judge(args) -> None:
    load_env("GROQ_API_KEY", "GEMINI_API_KEY")
    os.environ["VOCAB_LLM_PROVIDERS"] = args.providers
    from app.services import llm_client
    from app.services.vocab_pipeline import VocabError

    items = sample_items(resolve(args.results), args.n, args.seed)
    out_rows: List[Dict[str, Any]] = []
    for i in range(0, len(items), args.batch):
        batch = items[i:i + args.batch]

        async def call():
            try:
                return await llm_client.generate_json(JUDGE_SYSTEM, judge_prompt(batch), temperature=0.0, max_tokens=900, timeout=50.0)
            except llm_client.LLMError as exc:
                raise VocabError(503, "LLM_UNAVAILABLE" if exc.code != "timeout" else "LLM_TIMEOUT", exc.detail) from exc

        result, error = await with_outage_retry(call)
        print(f"- lô {i // args.batch + 1}: " + (f"LỖI {error.code}" if error else f"{len(result.data.get('ratings', []))} đánh giá [{result.provider}]"), flush=True)
        if error:
            continue
        by_id = {r.get("item_id"): r for r in result.data.get("ratings", []) if isinstance(r, dict)}
        for it in batch:
            r = by_id.get(it["item_id"])
            if r:
                out_rows.append({"item_id": it["item_id"], "judge": result.provider, **{d: r.get(d) for d in DIMENSIONS}})
        await asyncio.sleep(args.sleep)
    write_jsonl(resolve(args.out), out_rows)
    print(f"Đã ghi {len(out_rows)}/{len(items)} đánh giá -> {resolve(args.out)}")


def _to_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def acceptable(dim: str, value: int) -> int:
    """Quy về nhị phân để tính tỷ lệ chấp nhận và kappa: điểm >= 1 là đạt."""
    return 1 if value >= 1 else 0


def cmd_score(args) -> None:
    with open(resolve(args.sheet), encoding="utf-8-sig", newline="") as f:
        sheet = list(csv.DictReader(f))
    filled = [r for r in sheet if all(_to_int(r.get(d)) is not None for d in DIMENSIONS)]
    print(f"Phiếu: {len(sheet)} thẻ, đã chấm đủ {len(filled)} thẻ.")
    if not filled:
        print("Chưa có thẻ nào được chấm đủ các cột; điền phiếu rồi chạy lại.")
        return
    print("\nTỷ lệ chấp nhận (người chấm), Wilson 95%:")
    for d in DIMENSIONS:
        vals = [_to_int(r[d]) for r in filled]
        print(f"  {d:<16} đạt >=1: {fmt_pct(sum(acceptable(d, v) for v in vals), len(vals))}" +
              (f"   điểm 2 (tốt): {fmt_pct(sum(v == 2 for v in vals), len(vals))}" if d in THREE_POINT else ""))
    by_level: Dict[str, List[Dict[str, str]]] = {}
    for r in filled:
        by_level.setdefault(r["level"], []).append(r)
    print("\nTheo trình độ (definition_ok >= 1):")
    for level in sorted(by_level):
        rows = by_level[level]
        print(f"  {level}: {fmt_pct(sum(acceptable('d', _to_int(r['definition_ok'])) for r in rows), len(rows))}")

    if args.judge:
        judge = {r["item_id"]: r for r in read_jsonl(resolve(args.judge))}
        print("\nĐối chiếu với LLM-judge (nhị phân: đạt/không đạt):")
        for d in DIMENSIONS:
            pairs = [(acceptable(d, _to_int(r[d])), acceptable(d, _to_int(judge[r["item_id"]][d]))) for r in filled
                     if r["item_id"] in judge and _to_int(judge[r["item_id"]].get(d)) is not None]
            if not pairs:
                continue
            a, b = [p[0] for p in pairs], [p[1] for p in pairs]
            agree = sum(x == y for x, y in pairs)
            print(f"  {d:<16} đồng thuận {fmt_pct(agree, len(pairs))}  Cohen's kappa = {cohen_kappa(a, b):.2f}  "
                  f"(LLM-judge đạt {sum(b)}/{len(b)}, người chấm đạt {sum(a)}/{len(a)})")
    print("\nLưu ý: chỉ có MỘT người chấm nên không tính được kappa giữa người với người; kappa ở trên là người ↔ LLM-judge.")


def cmd_judge_summary(args) -> None:
    """Tỷ lệ chấp nhận theo LLM-judge (chưa có người chấm). Chỉ là ý kiến tham khảo của một mô hình khác."""
    rows = read_jsonl(resolve(args.judge))
    print(f"LLM-judge: {len(rows)} thẻ ({rows[0]['judge'] if rows else '?'})")
    for d in DIMENSIONS:
        vals = [_to_int(r.get(d)) for r in rows if _to_int(r.get(d)) is not None]
        print(f"  {d:<16} đạt >=1: {fmt_pct(sum(v >= 1 for v in vals), len(vals))}" +
              (f"   điểm 2 (tốt): {fmt_pct(sum(v == 2 for v in vals), len(vals))}" if d in THREE_POINT else ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("make", "judge"):
        p = sub.add_parser(name)
        p.add_argument("--results", required=True)
        p.add_argument("--n", type=int, default=100)
        p.add_argument("--seed", type=int, default=7)
        p.add_argument("--out", required=True)
        if name == "judge":
            p.add_argument("--providers", default="gemini", help="provider cho LLM-judge (khác mô hình sinh)")
            p.add_argument("--batch", type=int, default=8)
            p.add_argument("--sleep", type=float, default=45.0, help="Groq qwen: 1.000 token đầu ra/phút -> ~1 lô/phút")
    js = sub.add_parser("judge-summary")
    js.add_argument("--judge", required=True)
    sc = sub.add_parser("score")
    sc.add_argument("--sheet", required=True)
    sc.add_argument("--judge")
    args = ap.parse_args()
    if args.cmd == "make":
        cmd_make(args)
    elif args.cmd == "judge":
        asyncio.run(cmd_judge(args))
    elif args.cmd == "judge-summary":
        cmd_judge_summary(args)
    else:
        cmd_score(args)


if __name__ == "__main__":
    main()
