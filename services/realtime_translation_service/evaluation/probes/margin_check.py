import os, sys, json, logging, statistics
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path.insert(0, ROOT)
os.environ["TESTING"] = "1"
logging.disable(logging.CRITICAL)
from app.services import language_detection as ld
ld.reload_config(); ld.warm_up()
cal = ld.get_calibration()
print("calibration:", cal.version, cal.thresholds, cal.unsupported_thresholds)
rows = []
for name in ("lang_dev.jsonl", "lang_val.jsonl"):
    rows += [json.loads(l) for l in open(os.path.join(ROOT, "evaluation", "dataset", name), encoding="utf-8")]
by_cat = {}
for r in rows:
    if r["expected_status"] != "detected":
        continue
    info = ld.extract_features(r["text"])
    if info["early"]:
        continue
    ok = info["top1"] == r["expected_primary_language"]
    by_cat.setdefault((r["category"], info["bucket"]), []).append((info["meta"], ok))
for (cat, bucket), vals in sorted(by_cat.items()):
    good = [m for m, ok in vals if ok]
    bad = [m for m, ok in vals if not ok]
    thr = cal.thresholds[bucket]
    below = sum(1 for m in good if m < thr)
    print(f"{cat:30} {bucket:6} n={len(vals):3} correct_meta min={min(good) if good else float('nan'):.3f} med={statistics.median(good) if good else float('nan'):.3f} "
          f"below_thr={below}/{len(good)} wrong={len(bad)} wrong_meta_max={max(bad) if bad else float('nan'):.3f} thr={thr:.3f}")
