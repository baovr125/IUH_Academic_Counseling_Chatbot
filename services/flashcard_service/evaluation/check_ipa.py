"""Đối chiếu IPA do AI sinh với từ điển công khai (api.dictionaryapi.dev) trên mẫu các từ đơn.

  python -m evaluation.check_ipa --results results/topics_B.jsonl --n 100 --seed 7 --out results/ipa_check.json

Hạn chế cần nêu khi báo cáo: từ điển trộn giọng Anh/Mỹ và nhiều biến thể nên đây là CẬN DƯỚI của độ chính xác;
không có dữ liệu cho mọi từ (đo riêng độ phủ). So khớp: "exact" = trùng sau khi bỏ dấu nhấn/độ dài; "close" = độ giống >= 0.8.
"""
from __future__ import annotations

import argparse
import difflib
import json
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from evaluation.common import EVAL_DIR, fmt_pct, read_jsonl

API = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
_STRIP = re.compile(r"[ˈˌːˑ.\s/\[\]()'‿͡]")


def normalise(ipa: str) -> str:
    text = _STRIP.sub("", ipa or "").lower()
    return text.replace("ɹ", "r").replace("ɡ", "g").replace("ɚ", "ər").replace("ɝ", "ɜr")


def dictionary_ipas(client: httpx.Client, word: str) -> Optional[List[str]]:
    try:
        res = client.get(API.format(word=word), timeout=15)
    except httpx.HTTPError:
        return None
    if res.status_code != 200:
        return []
    found = set()
    for entry in res.json():
        if entry.get("phonetic"):
            found.add(entry["phonetic"])
        for ph in entry.get("phonetics", []):
            if ph.get("text"):
                found.add(ph["text"])
    return sorted(found)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--delay", type=float, default=0.6, help="nghỉ giữa các lời gọi API (giây)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    results = Path(args.results) if Path(args.results).is_absolute() else EVAL_DIR / args.results
    words: Dict[str, str] = {}
    for row in read_jsonl(results):
        for it in row.get("items", []):
            term = it["term"]
            if it["ipa"] and re.fullmatch(r"[A-Za-z]+", term):  # chỉ từ đơn; cụm từ không có mục từ điển
                words.setdefault(term.lower(), it["ipa"])
    sample = list(words.items())
    random.Random(args.seed).shuffle(sample)
    sample = sample[: args.n]

    records, covered, exact, close = [], 0, 0, 0
    with httpx.Client(headers={"User-Agent": "iuh-flashcard-eval/1.0"}) as client:
        for i, (word, ipa) in enumerate(sample, 1):
            refs = dictionary_ipas(client, word)
            rec: Dict[str, Any] = {"word": word, "ai_ipa": ipa, "dictionary": refs}
            if refs:
                covered += 1
                mine = normalise(ipa)
                targets = [normalise(r) for r in refs]
                rec["exact"] = mine in targets
                rec["best_ratio"] = round(max(difflib.SequenceMatcher(None, mine, t).ratio() for t in targets), 3)
                rec["close"] = rec["exact"] or rec["best_ratio"] >= 0.8
                exact += rec["exact"]
                close += rec["close"]
            records.append(rec)
            print(f"{i:>3}/{len(sample)} {word:<16} {ipa:<24} {refs}", flush=True)
            time.sleep(args.delay)

    summary = {
        "sampled_words": len(sample), "dictionary_coverage": fmt_pct(covered, len(sample)),
        "exact_match_among_covered": fmt_pct(exact, covered), "close_match_among_covered(>=0.8)": fmt_pct(close, covered),
        "note": "Cận dưới: từ điển trộn giọng Anh/Mỹ; chỉ tính các từ đơn có mục từ điển.",
    }
    out = Path(args.out) if Path(args.out).is_absolute() else EVAL_DIR / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
