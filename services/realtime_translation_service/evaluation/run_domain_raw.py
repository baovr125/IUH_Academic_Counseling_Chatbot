"""Chạy LLM thật trên bộ dev/val/holdout và LƯU KẾT QUẢ THÔ (header domain, confidence, bản dịch, độ trễ).

Tách việc gọi API (tốn quota) khỏi việc chỉnh quy tắc `decide_domain` (làm offline trên file kết quả thô).
KHÔNG in key. Ví dụ:
  python evaluation/run_domain_raw.py --split dev --model openai/gpt-oss-20b --out evaluation/results/domain_raw_dev_gptoss20b.jsonl
  python evaluation/run_domain_raw.py --split dev --mode plain --model openai/gpt-oss-20b ...   # dịch KHÔNG domain (đường cơ sở)
"""
import argparse
import asyncio
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


def _load_env():
    for path in (os.path.join(ROOT, "..", "..", ".env"), os.path.join(ROOT, ".env")):
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    os.environ["REDIS_HOST"] = "localhost"


_load_env()

from app.services import domain_llm  # noqa: E402
from app.services.domain_detection import (  # noqa: E402
    JointStreamParser, LexicalSummary, build_auto_system_prompt, build_manual_system_prompt,
)
from app.services.domain_index import get_index  # noqa: E402
from app.services.language_detection import _extract_visible_text  # noqa: E402

DATASETS = {
    "dev": "dataset/domain_dev.jsonl",
    "val": "dataset/domain_val.jsonl",
    "holdout": "dataset/domain_holdout.jsonl",
}
PLAIN_PROMPT = (
    "You are a professional English to Vietnamese translator. Translate naturally. Do not add explanations or "
    "quotes; preserve HTML tags exactly if present; output ONLY the translation."
)


async def run_one(system: str, text: str, parser, retries: int = 3):
    for attempt in range(retries + 1):
        domain_llm.reset_cooldowns()
        t0 = time.perf_counter()
        first = None
        out, header, fmt_err = [], None, False
        try:
            async for kind, value in domain_llm.stream_llm(system, text, 0.2):
                if kind != "chunk":
                    continue
                if first is None:
                    first = time.perf_counter() - t0
                if parser is None:
                    out.append(value)
                    continue
                for ev, payload in parser.feed(value):
                    if ev == "header":
                        header = payload
                    elif ev == "format_error":
                        fmt_err = True
                    elif ev == "text":
                        out.append(payload)
            if parser is not None:
                for ev, payload in parser.finish():
                    if ev == "header":
                        header = payload
                    elif ev == "format_error":
                        fmt_err = True
                    elif ev == "text":
                        out.append(payload)
            return {
                "ok": True, "output": "".join(out), "first_s": first, "total_s": time.perf_counter() - t0,
                "header_domain": header.domain if header else None,
                "header_conf": header.confidence if header else None,
                "format_error": fmt_err or (parser is not None and header is None),
            }
        except domain_llm.LLMError as exc:
            if attempt < retries and exc.code in ("quota", "cooldown", "timeout", "unavailable"):
                await asyncio.sleep(20 * (attempt + 1))
                continue
            return {"ok": False, "error": exc.code, "detail": exc.detail[:160]}
    return {"ok": False, "error": "retries_exhausted"}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=list(DATASETS), help="bộ dữ liệu có sẵn")
    ap.add_argument("--file", help="file JSONL tùy ý (id, text, domain, kind) thay cho --split")
    ap.add_argument("--kinds", default="", help="chỉ chạy các kind này, phân tách bằng dấu phẩy (vd in_domain)")
    ap.add_argument("--model", required=True)
    ap.add_argument("--provider", default="groq", choices=["groq", "gemini"])
    ap.add_argument("--mode", default="auto", choices=["auto", "plain", "manual"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--gap", type=float, default=4.5, help="giây nghỉ giữa các lời gọi (giữ dưới 8.000 token/phút)")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    os.environ["DOMAIN_LLM_PROVIDERS"] = args.provider
    os.environ["GROQ_DOMAIN_MODEL" if args.provider == "groq" else "GEMINI_DOMAIN_MODEL"] = args.model
    if not args.split and not args.file:
        ap.error("cần --split hoặc --file")
    path = args.file or os.path.join(ROOT, "evaluation", DATASETS[args.split])
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    if args.kinds:
        wanted = {k.strip() for k in args.kinds.split(",") if k.strip()}
        rows = [r for r in rows if r["kind"] in wanted]
    if args.limit:
        rows = rows[: args.limit]
    index = await get_index()
    print(f"index: {len(index.entries)} thuật ngữ, max_words={index.max_words}; {len(rows)} mẫu; model={args.model}", flush=True)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    done = set()
    if os.path.exists(args.out):
        done = {json.loads(l)["id"] for l in open(args.out, encoding="utf-8")}
    with open(args.out, "a", encoding="utf-8", newline="\n") as fh:
        for i, row in enumerate(rows, 1):
            if row["id"] in done:
                continue
            if args.mode == "manual" and row["domain"] == "unknown":
                continue  # không có domain đúng để chọn thủ công
            visible = _extract_visible_text(row["text"]).strip()
            exact = index.exact(visible) if len(visible.split()) <= index.max_words and visible == row["text"].strip() else []
            matches = index.scan(visible)
            lex = LexicalSummary.build(matches)
            rec = {
                "id": row["id"], "kind": row["kind"], "label": row["domain"], "text": row["text"],
                "exact_domains": [e.domain for e in exact],
                "lex": {d: {"score": lex.score(d), "terms": lex.terms(d)} for d in lex.per_domain},
                "mode": args.mode, "model": args.model,
            }
            if exact and args.mode == "auto":
                rec.update(ok=True, skipped="exact_dictionary")
            else:
                if args.mode == "auto":
                    system = build_auto_system_prompt(index.domains, [m.entry for m in matches], "en", "vi")
                    parser = JointStreamParser()
                elif args.mode == "manual":
                    system = build_manual_system_prompt(row["domain"], [m.entry for m in matches if m.entry.domain == row["domain"]], "en", "vi")
                    parser = None
                else:
                    system, parser = PLAIN_PROMPT, None
                rec.update(await run_one(system, row["text"], parser))
                await asyncio.sleep(args.gap)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            status = rec.get("header_domain") or rec.get("skipped") or rec.get("error")
            print(f"[{i}/{len(rows)}] {row['id']} {row['kind']:9s} label={row['domain'][:12]:12s} -> {status} {rec.get('header_conf')}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
