"""Tiện ích dùng chung cho bộ đánh giá sinh từ vựng bằng AI (không in khóa API)."""
from __future__ import annotations

import asyncio
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

EVAL_DIR = Path(__file__).resolve().parent
SERVICE_DIR = EVAL_DIR.parent
REPO_DIR = SERVICE_DIR.parent.parent
sys.path.insert(0, str(SERVICE_DIR))

RETRY_WAIT_SECONDS = 65
OUTAGE_CODES = {"LLM_UNAVAILABLE", "LLM_TIMEOUT"}  # lỗi do provider, không tính vào tỷ lệ lỗi của hệ thống


def load_env(*names: str) -> None:
    """Nạp biến môi trường từ .env ở thư mục gốc dự án (chỉ các khóa được yêu cầu)."""
    path = REPO_DIR / ".env"
    wanted = set(names)
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            if not wanted or key.strip() in wanted:
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    os.environ.setdefault("JWT_SECRET_KEY", "x" * 40)


def read_jsonl(path: Path | str) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf8").splitlines() if line.strip()]


def write_jsonl(path: Path | str, rows: Iterable[Dict[str, Any]]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_jsonl(path: Path | str, row: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


async def with_outage_retry(fn, attempts: int = 3, wait: float = RETRY_WAIT_SECONDS, log=print):
    """Gọi `fn()` (coroutine factory). Lỗi do provider (429/timeout) thì chờ rồi thử lại, hết lượt mới trả lỗi cuối."""
    from app.services.vocab_pipeline import VocabError

    last: Optional[VocabError] = None
    for attempt in range(1, attempts + 1):
        try:
            return await fn(), None
        except VocabError as exc:
            last = exc
            if exc.code not in OUTAGE_CODES or attempt == attempts:
                break
            log(f"    provider bận ({exc.code}), chờ {wait:.0f}s rồi thử lại ({attempt}/{attempts})")
            await asyncio.sleep(wait)
    return None, last


# ---------------------------------------------------------------------------------------- thống kê
def percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def wilson(successes: int, total: int, z: float = 1.96) -> Tuple[float, float, float]:
    """(tỷ lệ, cận dưới, cận trên) khoảng tin cậy Wilson 95%."""
    if total == 0:
        return float("nan"), float("nan"), float("nan")
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def cohen_kappa(a: Sequence[Any], b: Sequence[Any]) -> float:
    """Hệ số Cohen's kappa cho hai chuỗi nhãn cùng độ dài."""
    n = len(a)
    if n == 0 or n != len(b):
        return float("nan")
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum((ca[k] / n) * (cb[k] / n) for k in set(ca) | set(cb))
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def fmt_pct(successes: int, total: int) -> str:
    p, lo, hi = wilson(successes, total)
    return "n/a" if total == 0 else f"{p * 100:.1f}% [{lo * 100:.0f}-{hi * 100:.0f}] ({successes}/{total})"


# ---------------------------------------------------------------------------------------- chỉ số tự động
def summarise_runs(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tổng hợp chỉ số tự động từ các dòng kết quả của run_vocab_eval."""
    ok_rows = [r for r in rows if not r.get("error")]
    outage = [r for r in rows if r.get("error") and r["error"]["code"] in OUTAGE_CODES]
    failures = [r for r in rows if r.get("error") and r["error"]["code"] not in OUTAGE_CODES]
    items = [it for r in ok_rows for it in r["items"]]

    dup_runs = 0
    for r in ok_rows:
        keys = [" ".join(it["term"].casefold().split()) for it in r["items"]]
        dup_runs += len(keys) != len(set(keys))

    candidates = sum(r["stages"].get("candidates", 0) for r in ok_rows)
    enriched_valid = sum(r["stages"].get("enriched_valid", 0) for r in ok_rows)
    rejected = sum(r["stages"].get("rejected", 0) for r in ok_rows)
    fixed = sum(r["stages"].get("fixed", 0) for r in ok_rows)

    latencies = [r["latency_ms"] / 1000 for r in ok_rows]
    tokens_in = [r["usage"]["prompt_tokens"] for r in ok_rows]
    tokens_out = [r["usage"]["completion_tokens"] for r in ok_rows]
    returned = sum(r["returned"] for r in ok_rows)
    fulfilled = sum(1 for r in ok_rows if r["returned"] >= 0.9 * r["requested"])

    def share(pred) -> Tuple[int, int]:
        return sum(1 for it in items if pred(it)), len(items)

    return {
        "runs": len(rows), "ok": len(ok_rows), "provider_outage": len(outage), "system_failures": len(failures),
        "items": len(items),
        "count_fulfilment_ge90pct": fmt_pct(fulfilled, len(ok_rows)),
        "mean_returned_ratio": round(sum(r["returned"] / r["requested"] for r in ok_rows) / len(ok_rows), 3) if ok_rows else None,
        "runs_with_duplicates": dup_runs,
        "schema_valid_rate_of_candidates": fmt_pct(enriched_valid, candidates) if candidates else "n/a",
        "reviewer_reject_rate": fmt_pct(rejected, enriched_valid) if enriched_valid else "n/a",
        "reviewer_fix_rate": fmt_pct(fixed, returned) if returned else "n/a",
        "example_contains_term": fmt_pct(*share(lambda i: bool(i["example"]) and "example_missing_term" not in i["warnings"])),
        "ipa_present_and_valid": fmt_pct(*share(lambda i: bool(i["ipa"]))),
        "example_translation_present": fmt_pct(*share(lambda i: bool(i["example_translation"]))),
        "verified_share": fmt_pct(*share(lambda i: i["verified"])),
        "latency_s": {"p50": round(percentile(latencies, 0.5), 1), "p95": round(percentile(latencies, 0.95), 1),
                      "mean": round(sum(latencies) / len(latencies), 1)} if latencies else None,
        "tokens_per_run": {"prompt": round(sum(tokens_in) / len(tokens_in)), "completion": round(sum(tokens_out) / len(tokens_out))} if ok_rows else None,
        "tokens_per_returned_item": round((sum(tokens_in) + sum(tokens_out)) / returned, 1) if returned else None,
        "llm_calls_per_run": round(sum(r["stages"].get("llm_calls", 0) for r in ok_rows) / len(ok_rows), 2) if ok_rows else None,
        "error_codes": dict(Counter(r["error"]["code"] for r in rows if r.get("error"))),
        "providers": dict(Counter(p for r in ok_rows for p in r["providers"])),
    }
