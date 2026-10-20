import os, sys, time, json, logging, statistics, threading
from concurrent.futures import ThreadPoolExecutor
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path.insert(0, ROOT)
os.environ["TESTING"] = "1"
os.environ["DETECT_CACHE_SIZE"] = "0"   # đo tính toán thật, không phải cache hit
logging.disable(logging.CRITICAL)
import psutil
proc = psutil.Process()
rss = lambda: proc.memory_info().rss / 1e6
print(f"RSS trước khi import engine: {rss():.0f} MB")
from app.services import language_detection as ld
print(f"RSS sau import: {rss():.0f} MB")
t0 = time.perf_counter(); ld._get_fasttext_model if False else None
from app.services.fasttext_detector import _get_fasttext_model
t0 = time.perf_counter(); _get_fasttext_model(); print(f"nạp fastText: {(time.perf_counter()-t0)*1000:.0f} ms, RSS {rss():.0f} MB")
t0 = time.perf_counter(); ld._get_lingua(); print(f"nạp Lingua (preload {len(ld.get_config().lingua_oos)+10} ngôn ngữ): {(time.perf_counter()-t0)*1000:.0f} ms, RSS {rss():.0f} MB")

rows = []
for name in ("lang_dev.jsonl", "lang_val.jsonl"):
    rows += [json.loads(l) for l in open(os.path.join(ROOT, "evaluation", "dataset", name), encoding="utf-8")]
texts = [r["text"] for r in rows if len(r["text"]) < 3000]

def timed(text):
    t = time.perf_counter(); ld.detect_language_detailed(text); return (time.perf_counter() - t) * 1000

def pct(values, p):
    s = sorted(values); return s[min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))]

for workers in (1, 10, 50):
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        lats = list(pool.map(timed, texts * 3))
    wall = time.perf_counter() - started
    print(f"workers={workers:2d} n={len(lats)} p50={pct(lats,50):.2f}ms p95={pct(lats,95):.2f}ms p99={pct(lats,99):.2f}ms max={max(lats):.1f}ms throughput={len(lats)/wall:.0f}/s")
print(f"RSS cuối: {rss():.0f} MB")
