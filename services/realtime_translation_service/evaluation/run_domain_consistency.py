"""Độ nhất quán: gọi lại cùng một đầu vào N lần và đo tỷ lệ cùng một quyết định domain (tiêu chí "lặp 5 lần giống nhau").

Dùng mẫu từ bộ dev (không phải bộ test đóng băng). Tốn N x số mẫu lời gọi LLM thật; không in key.
  python evaluation/run_domain_consistency.py --model qwen/qwen3.8-27b --out evaluation/results/domain_consistency_qwen27b.json
"""
import argparse
import asyncio
import collections
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))

import run_domain_raw as raw  # noqa: E402  (nạp .env, dựng prompt/parser giống production)
from app.services.domain_detection import JointStreamParser, LexicalSummary, build_auto_system_prompt, decide_domain  # noqa: E402
from app.services.domain_index import get_index  # noqa: E402


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--per-domain", type=int, default=3)
    ap.add_argument("--ood", type=int, default=6)
    ap.add_argument("--gap", type=float, default=5.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--split", default="dev", choices=["dev", "val", "holdout"])
    args = ap.parse_args()
    os.environ["DOMAIN_LLM_PROVIDERS"] = "groq"
    os.environ["GROQ_DOMAIN_MODEL"] = args.model

    rows = [json.loads(l) for l in open(os.path.join(ROOT, "evaluation", "dataset", f"domain_{args.split}.jsonl"), encoding="utf-8")]
    chosen, per = [], collections.Counter()
    for r in rows:
        if r["kind"] == "in_domain" and per[r["domain"]] < args.per_domain:
            per[r["domain"]] += 1
            chosen.append(r)
    chosen += [r for r in rows if r["kind"] == "ood"][: args.ood]

    index = await get_index()
    result = []
    for r in chosen:
        matches = index.scan(r["text"])
        lex = LexicalSummary.build(matches)
        system = build_auto_system_prompt(index.domains, [m.entry for m in matches], "en", "vi")
        decisions, outputs = [], []
        for _ in range(args.repeats):
            res = await raw.run_one(system, r["text"], JointStreamParser())
            if res.get("ok"):
                header = None
                if res["header_domain"] is not None:
                    from app.services.domain_detection import JointHeader
                    header = JointHeader(res["header_domain"], res["header_conf"])
                dec = decide_domain(header, lex, index.domains)
                decisions.append(dec.domain if dec.status == "detected" else "unknown")
                outputs.append(res["output"].strip())
            else:
                decisions.append(f"error:{res.get('error')}")
            await asyncio.sleep(args.gap)
        top, n = collections.Counter(decisions).most_common(1)[0]
        result.append({"id": r["id"], "label": r["domain"], "decisions": decisions, "majority": top,
                       "agree": n / len(decisions), "identical_translation": len(set(outputs)) == 1 if outputs else False})
        print(r["id"], f"{n}/{len(decisions)}", top, flush=True)

    per_call = sum(x["agree"] * args.repeats for x in result) / (len(result) * args.repeats)
    unanimous = sum(1 for x in result if x["agree"] == 1.0) / len(result)
    summary = {"model": args.model, "items": len(result), "repeats": args.repeats,
               "per_call_agreement_with_majority": per_call, "items_unanimous": unanimous,
               "items_identical_translation": sum(1 for x in result if x["identical_translation"]) / len(result),
               "majority_correct": sum(1 for x in result if x["majority"] == x["label"]) / len(result)}
    json.dump({"summary": summary, "items": result}, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
