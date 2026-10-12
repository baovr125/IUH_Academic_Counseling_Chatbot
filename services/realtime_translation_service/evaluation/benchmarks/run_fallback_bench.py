"""FB-01..03: tiêm lỗi thật vào chế độ chuyên ngành và đo hành vi fallback của `translate_with_domain` (hàm production).

  python evaluation/benchmarks/run_fallback_bench.py --scenario bad_model|timeout|no_provider --n 10 --out <json>

- bad_model  : GROQ_DOMAIN_MODEL trỏ tới model không tồn tại (Groq trả 404 thật), chỉ dùng Groq.
- timeout    : timeout token đầu 0,1 s với Groq thật (model mặc định), chỉ dùng Groq.
- no_provider: không có client Groq/Gemini (không gọi mạng).
NLLB là model thật (GPU). Bỏ qua đọc cache kết quả (để mọi câu đều đi đường dịch thật); không ghi gì ra Redis
vì kết quả fallback không được cache theo thiết kế.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
import time
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
import run_domain_raw  # noqa: E402,F401  (nạp .env, REDIS_HOST=localhost)

logging.disable(logging.CRITICAL)

from app.services import domain_llm  # noqa: E402
from app.services.domain_translation import translate_with_domain  # noqa: E402


async def run(rows, scenario):
    out = []
    for r in rows:
        events, t0 = [], time.perf_counter()
        async for ev in translate_with_domain(r["text"], "en", "vi", "auto"):
            events.append(ev)
        ms = (time.perf_counter() - t0) * 1000
        domain = [e["domain"] for e in events if e.get("event") == "domain"]
        out.append({
            "id": r["id"], "ms": ms,
            "text": "".join(e["text"] for e in events if "text" in e),
            "warnings": [w["code"] for e in events if "warnings" in e for w in e["warnings"]],
            "translator": domain[-1].get("translator") if domain else None,
            "error": next((e for e in events if "error" in e), None),
            "groq_cooling": domain_llm._is_cooling("groq"),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True, choices=["bad_model", "timeout", "no_provider"])
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "evaluation", "dataset", "domain_val.jsonl"), encoding="utf-8")]
    rows = [r for r in rows if r["kind"] == "in_domain"][: args.n]

    os.environ["DOMAIN_LLM_PROVIDERS"] = "groq"
    domain_llm.reset_cooldowns()
    patches = [patch("app.services.domain_translation.get_cached_domain_result", return_value=None),
               patch("app.services.domain_translation.set_cached_domain_result")]
    if args.scenario == "bad_model":
        os.environ["GROQ_DOMAIN_MODEL"] = "does-not-exist/model-404"
    elif args.scenario == "timeout":
        os.environ.pop("GROQ_DOMAIN_MODEL", None)
        os.environ["DOMAIN_LLM_FIRST_TOKEN_TIMEOUT_SECONDS"] = "0.1"
    else:
        patches += [patch("app.services.llm_service.get_groq_client", return_value=None),
                    patch("app.services.llm_service.get_gemini_client", return_value=None)]
    for p in patches:
        p.start()
    try:
        items = asyncio.run(run(rows, args.scenario))
    finally:
        for p in patches:
            p.stop()
    ok = [i for i in items if i["text"].strip() and not i["error"]]
    summary = {
        "scenario": args.scenario, "samples": len(items),
        "with_translation": len(ok),
        "translator_nllb": sum(1 for i in items if i["translator"] == "nllb"),
        "warnings_exactly_fallback": sum(1 for i in items if i["warnings"] == ["FALLBACK_NLLB"]),
        "errors": sum(1 for i in items if i["error"]),
        "first_ms": items[0]["ms"] if items else None,
        "rest_ms_max": max((i["ms"] for i in items[1:]), default=None),
        "rest_ms_mean": (sum(i["ms"] for i in items[1:]) / (len(items) - 1)) if len(items) > 1 else None,
    }
    json.dump({"summary": summary, "items": items}, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
