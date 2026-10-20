"""Đọc-chỉ: tổng hợp số liệu từ test_artifacts để đối chiếu với các báo cáo."""
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET

art = sys.argv[1]
os.chdir(art)

print("== JUnit")
tot = 0
for f in sorted(glob.glob("unit_4_*_junit.xml")):
    r = ET.parse(f).getroot()
    s = r if r.tag == "testsuite" else r.find("testsuite")
    print(f, {k: s.get(k) for k in ("tests", "failures", "errors", "skipped", "time", "timestamp")})
    tot += int(s.get("tests"))
print("TOTAL", tot)

print("== Coverage")
for f in sorted(glob.glob("unit_4_*_coverage.json")) + ["coverage_baseline.json"]:
    d = json.load(open(f, encoding="utf-8"))
    t = d["totals"]
    print(f, "total %.1f%% (%d/%d stmts)" % (t["percent_covered"], t["covered_lines"], t["num_statements"]))
    if f == "coverage_baseline.json":
        for k, v in sorted(d["files"].items()):
            kk = k.replace(os.sep, "/")
            if kk.startswith("app/") and v["summary"]["num_statements"] > 15:
                print("    %-46s %5.1f%% of %d" % (kk, v["summary"]["percent_covered"], v["summary"]["num_statements"]))

print("== TA-01 jsonl (cấu trúc + trạng thái)")
for f in ("ta01_dev_plain_qwen.jsonl", "ta01_dev_manual_qwen.jsonl", "ta01_dev_auto_qwen.jsonl"):
    if not os.path.exists(f):
        print(f, "(thiếu file artifact, bỏ qua)")
        continue
    rows = [json.loads(line) for line in open(f, encoding="utf-8") if line.strip()]
    keys = sorted(rows[0].keys())
    errs = [r.get("error") for r in rows if r.get("error")]
    print(f, "n=%d" % len(rows), "keys=%s" % keys)
    print("   errors:", len(errs), sorted(set(str(e)[:60] for e in errs)))

print("== tq01 json keys")
d = json.load(open("tq01_lt01_nllb.json", encoding="utf-8"))
print({k: (v if not isinstance(v, (list, dict)) else type(v).__name__ + str(len(v))) for k, v in d.items()})

print("== fb03 json")
print(open("fb03_no_provider.json", encoding="utf-8").read()[:900])

print("== dd03 summary keys")
d = json.load(open("dd03_consistency_val_qwen.json", encoding="utf-8"))
print({k: (v if not isinstance(v, (list, dict)) else type(v).__name__ + str(len(v))) for k, v in d.items()})

print("== ld02 devgate json")
print(open("ld02_tatoeba_devgate.json", encoding="utf-8").read()[:1700])
print("== ld01 devgate json")
print(open("ld01_val_devgate.json", encoding="utf-8").read()[:1200])
