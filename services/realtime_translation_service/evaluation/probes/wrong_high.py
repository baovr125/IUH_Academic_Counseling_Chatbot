import os, sys, json, logging
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path.insert(0, ROOT)
os.environ["TESTING"] = "1"
logging.disable(logging.CRITICAL)
from app.services import language_detection as ld
ld.reload_config(); ld.warm_up()
rows = []
for name in ("lang_dev.jsonl", "lang_val.jsonl"):
    rows += [json.loads(l) for l in open(os.path.join(ROOT, "evaluation", "dataset", name), encoding="utf-8")]
out = []
for r in rows:
    if r["expected_status"] not in ("detected", "unsupported"):
        continue
    info = ld.extract_features(r["text"])
    if info["early"]:
        continue
    top1 = info["top1"]
    if r["expected_status"] == "detected":
        ok = top1 == r["expected_primary_language"]
    else:
        ok = top1 not in ld.SUPPORTED_CODES and top1 != ld.OTHER_LABEL
    if not ok and top1 in ld.SUPPORTED_CODES:
        out.append((info["meta"], info["bucket"], r["expected_primary_language"], top1, r["category"], r["text"][:60]))
for item in sorted(out, reverse=True)[:25]:
    print(f"meta={item[0]:.3f} {item[1]:6} exp={item[2]} got={item[3]} cat={item[4]} :: {item[5]!r}")
