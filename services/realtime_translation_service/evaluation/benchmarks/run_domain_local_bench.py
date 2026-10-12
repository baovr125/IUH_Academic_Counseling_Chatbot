"""Benchmark cục bộ (không gọi LLM) cho phần từ điển của chế độ chuyên ngành.

  python evaluation/benchmarks/run_domain_local_bench.py --out <json>

DD-05: `DomainIndex.exact()` trên toàn bộ từ điển thật (Supabase) với 4 dạng mỗi thuật ngữ
       (nguyên dạng, VIẾT HOA, có mạo từ "the", số nhiều) + 50 cụm không có trong từ điển.
LT-02: thời gian dựng chỉ mục và quét (`scan`) văn bản 888 ký tự với từ điển 246 / 1.000 / 10.000 mục,
       bộ nhớ Python của chỉ mục (tracemalloc).
"""
import argparse
import asyncio
import json
import os
import statistics
import sys
import time
import tracemalloc

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)


def _load_env():
    for path in (os.path.join(ROOT, "..", "..", ".env"),):
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    os.environ["REDIS_HOST"] = "localhost"


_load_env()

from app.services.domain_index import DomainIndex, _compiled, get_index  # noqa: E402
from app.services.domain_service import get_all_dictionaries  # noqa: E402

NON_TERMS = [
    "apple pie", "good morning", "thank you", "see you later", "blue sky", "happy birthday", "coffee shop",
    "train station", "summer holiday", "football match", "birthday party", "red car", "my friend", "the weather",
    "a cup of tea", "new york", "walk the dog", "chocolate cake", "beach house", "music festival", "green tea",
    "old town", "rainy day", "school bus", "ice cream", "phone call", "living room", "movie night", "city park",
    "fresh bread", "night market", "mountain trail", "family dinner", "book club", "art museum", "flower garden",
    "sunny afternoon", "river bank", "wooden table", "kitchen knife", "winter coat", "snow day", "lunch break",
    "evening news", "dance class", "pizza night", "garden party", "road trip", "picnic basket", "city lights",
]
TEXT = ("Because of stress concentration at the fillet, the shaft showed fatigue failure well below its yield "
        "strength. ") * 8


def plural(word: str) -> str:
    head, _, last = word.rpartition(" ")
    prefix = f"{head} " if head else ""
    if last.endswith("y") and len(last) > 2 and last[-2] not in "aeiou":
        return prefix + last[:-1] + "ies"
    if last.endswith(("s", "x", "z", "ch", "sh")):
        return prefix + last + "es"
    return prefix + last + "s"


def timed(fn, n):
    times = []
    for _ in range(n):
        s = time.perf_counter()
        fn()
        times.append((time.perf_counter() - s) * 1000)
    return {"p50_ms": statistics.median(times), "max_ms": max(times), "mean_ms": statistics.mean(times), "n": n}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = await get_all_dictionaries()
    index = await get_index(force=True)

    # DD-05
    forms = {"original": lambda w: w, "upper": lambda w: w.upper(), "article_the": lambda w: f"the {w}",
             "plural": plural}
    exact = {}
    misses = []
    for name, fn in forms.items():
        hit = 0
        for e in index.entries:
            got = index.exact(fn(e.word))
            if any(g.word == e.word and g.domain == e.domain for g in got):
                hit += 1
            else:
                misses.append({"form": name, "word": e.word, "query": fn(e.word), "got": [g.word for g in got]})
        exact[name] = {"hit": hit, "total": len(index.entries)}
    false_hits = [p for p in NON_TERMS if index.exact(p)]

    # LT-02
    scale = {}
    for size in (len(rows), 1000, 10000):
        synthetic = []
        i = 0
        while len(synthetic) < size:
            for r in rows:
                if len(synthetic) >= size:
                    break
                suffix = "" if i == 0 else f" variant{i}"
                synthetic.append({"domain": r["domain"], "word": r["word"] + suffix, "translation": r["translation"]})
            i += 1
        _compiled.cache_clear()
        tracemalloc.start()
        s = time.perf_counter()
        idx = DomainIndex.build(synthetic)
        build_ms = (time.perf_counter() - s) * 1000
        s = time.perf_counter()
        idx.scan(TEXT)  # lần đầu: biên dịch regex
        first_scan_ms = (time.perf_counter() - s) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        scale[str(size)] = {"entries": len(idx.entries), "build_ms": build_ms, "first_scan_ms": first_scan_ms,
                            "warm_scan": timed(lambda: idx.scan(TEXT), 20 if size >= 10000 else 100),
                            "python_mem_kib": current / 1024, "python_peak_kib": peak / 1024,
                            "matches": len(idx.scan(TEXT))}
    result = {"dictionary_rows": len(rows), "domains": index.domains, "max_words": index.max_words,
              "exact": exact, "exact_misses": misses, "non_terms": len(NON_TERMS), "non_term_false_hits": false_hits,
              "text_chars": len(TEXT), "scan_scale": scale}
    json.dump(result, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "exact_misses"}, ensure_ascii=False, indent=1))
    print("misses:", len(misses))


if __name__ == "__main__":
    asyncio.run(main())
