"""Chạy một cấu hình Lingua (qua env) và in RSS + chỉ số trên val và mẫu Tatoeba. Dùng: python mem_variants.py"""
import os, sys, json, logging, subprocess
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
EXT = os.path.join(os.environ.get("TATOEBA_DIR", os.path.join(ROOT, "evaluation", "dataset", "external", "tatoeba")), "external_sanity.jsonl")
variants = {
    "full 35 ngôn ngữ, high accuracy": {},
    "full 35 ngôn ngữ, LOW accuracy": {"DETECT_LINGUA_LOW_ACCURACY": "1"},
    "17 ngôn ngữ (10 + 7 láng giềng), high": {"DETECT_LINGUA_OOS": "it,pt,id,nl,pl,tr,uk"},
    "17 ngôn ngữ, LOW": {"DETECT_LINGUA_OOS": "it,pt,id,nl,pl,tr,uk", "DETECT_LINGUA_LOW_ACCURACY": "1"},
}
code = r'''
import os, sys, json, logging, psutil, time
sys.path.insert(0, r"%s")
os.environ["TESTING"] = "1"
logging.disable(logging.CRITICAL)
from app.services import language_detection as ld
ld.reload_config(reset_engines=True)
t = time.perf_counter(); ld.warm_up(); warm = time.perf_counter() - t
rss = psutil.Process().memory_info().rss / 1e6
sys.argv = ["dev_gate", "--file", r"%s"]
sys.path.insert(0, r"%s\evaluation")
import dev_gate
out = dev_gate.evaluate(dev_gate.load_rows("val", r"%s"))
m = out["metrics"]
print(json.dumps({"rss_mb": round(rss), "warmup_s": round(warm, 2), "acc_all_strict": round(m["accuracy_all_strict"], 4),
                  "wrong_confident": round(m["wrong_confident_rate"], 4), "oos_false_accept": round(m["oos_false_accept"], 4),
                  "oos_recall": round(m["oos_recall"], 4)}))
''' % (ROOT, EXT, ROOT, EXT)
for name, env in variants.items():
    e = {**os.environ, "PYTHONIOENCODING": "utf-8", **env}
    r = subprocess.run([sys.executable, "-W", "ignore", "-c", code], capture_output=True, text=True, env=e, encoding="utf-8")
    print(f"{name:42} -> {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]}")
