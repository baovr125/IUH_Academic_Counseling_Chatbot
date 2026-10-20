import collections
import json
import sys

path = sys.argv[1]
rows = [json.loads(l) for l in open(path, encoding="utf8") if l.strip()]
print("tổng vi phạm:", len(rows))
by = collections.defaultdict(lambda: {"n": 0, "min": 99, "pages": set(), "themes": set(), "text": ""})
for r in rows:
    key = (r["cls"], r["theme"])
    d = by[key]
    d["n"] += 1
    d["min"] = min(d["min"], r["ratio"])
    d["pages"].add(r["page"][:2])
    d["text"] = d["text"] or r["text"]
for (cls, theme), d in sorted(by.items(), key=lambda kv: (kv[0][1], kv[1]["min"])):
    print(f"[{theme:5}] min {d['min']:<5} x{d['n']:<3} pages={','.join(sorted(d['pages']))}  '{d['text'][:28]}'  :: {cls}")
