import os, sys, json, logging
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
SP = os.environ.get("TATOEBA_DIR", os.path.join(ROOT, "evaluation", "dataset", "external", "tatoeba"))
sys.path.insert(0, ROOT)
os.environ["TESTING"] = "1"
logging.disable(logging.CRITICAL)
from app.services import language_detection as ld
ld.warm_up()
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]

def collect(rows):
    items = []
    for r in rows:
        d = ld.detect_language_detailed(r["text"])
        if d.status != "detected":
            continue
        an = ld._analyze(r["text"], None)
        if an.early is not None:
            continue
        outside = sum(p for c, p in an.dist.items() if c not in ld.SUPPORTED_CODES)
        correct = r["expected_status"] == "detected" and d.resolved_source_lang == r["expected_primary_language"]
        items.append((an.p1, outside, correct))
    return items

sets = {"sanity": collect(load(os.path.join(SP, "external_sanity.jsonl"))),
        "holdout": collect(load(os.path.join(SP, "external_holdout.jsonl")))}
for name, items in sets.items():
    print("==", name, "detected:", len(items), "wrong:", sum(1 for _, _, c in items if not c))
    for outside_floor in (0.15, 0.2, 0.25, 0.3, 0.4):
        for p1_cap in (0.6, 0.7):
            blocked = [(p, o, c) for p, o, c in items if o >= outside_floor and p < p1_cap]
            wrong_blocked = sum(1 for _, _, c in blocked if not c)
            print(f"  outside>={outside_floor:.2f} & p1<{p1_cap}: blocked={len(blocked):3d} (wrong avoided={wrong_blocked}, correct lost={len(blocked)-wrong_blocked})")
