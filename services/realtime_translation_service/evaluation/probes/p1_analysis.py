import os, sys, json, logging
from collections import defaultdict
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
SP = os.environ.get("TATOEBA_DIR", os.path.join(ROOT, "evaluation", "dataset", "external", "tatoeba"))
sys.path.insert(0, ROOT)
os.environ["TESTING"] = "1"
logging.disable(logging.CRITICAL)
from app.services import language_detection as ld
ld.warm_up()

def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]

def analyse(name, rows):
    out = defaultdict(list)  # (bucket) -> list of (p1, correct)
    for r in rows:
        d = ld.detect_language_detailed(r["text"])
        if d.status != "detected":
            continue
        an = ld._analyze(r["text"], None)
        if an.early is not None:
            continue
        correct = r["expected_status"] == "detected" and d.resolved_source_lang == r["expected_primary_language"]
        out[an.bucket].append((an.p1, correct))
    print(f"== {name}")
    for bucket in ("short", "medium", "long"):
        items = out[bucket]
        for floor in (0.0, 0.45, 0.5, 0.55, 0.6):
            kept = [c for p, c in items if p >= floor]
            lost_ok = sum(1 for p, c in items if p < floor and c)
            wrong_kept = sum(1 for c in kept if not c)
            print(f"  {bucket:6} floor={floor:.2f}: detected={len(kept):4d} wrong={wrong_kept:2d}  correct_lost={lost_ok:3d}")

analyse("sanity (đã dùng để sửa luật)", load(os.path.join(SP, "external_sanity.jsonl")))
analyse("holdout", load(os.path.join(SP, "external_holdout.jsonl")))
