import os, sys, time, logging
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path.insert(0, ROOT)
os.environ["TESTING"] = "1"
logging.disable(logging.CRITICAL)
from app.services import language_detection as ld
ld.warm_up()
a = ld.detect_language_detailed("Hello")
print("Hello ->", a.status, a.confidence, a.margin, [(c.language, c.confidence) for c in a.candidates])
an = ld._analyze("Hello", None)
print("top1/top2", an.top1, an.top2, an.p1, sorted(an.dist.items(), key=lambda kv: -kv[1])[:5])
hostile = {
    "a*200000": "a" * 200_000,
    "nested div x5000": "<div>" * 5_000 + "Hello world, this is a test" + "</div>" * 5_000,
    "zwj*1000+Hello": "\u200d" * 1_000 + "Hello",
    "nul": "\x00\x01\x02 hello there my friend",
    "hebrew*500": "עברית" * 500 + " English words mixed in",
    "math-bold": "𝓗𝓮𝓵𝓵𝓸 𝔀𝓸𝓻𝓵𝓭 𝓽𝓱𝓲𝓼 𝓲𝓼 𝓪 𝓽𝓮𝓼𝓽",
    "é*3000": "é" * 3_000,
    "comment": "<!--" + "x" * 10_000,
}
for name, text in hostile.items():
    t0 = time.perf_counter()
    d = ld.detect_language_detailed(text)
    print(f"{name:20} {time.perf_counter()-t0:8.3f}s  {d.status}")
