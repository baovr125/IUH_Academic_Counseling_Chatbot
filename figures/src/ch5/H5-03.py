"""H5-03 Tỉ lệ trúng của bộ nhớ đệm ngữ nghĩa với cặp diễn đạt lại và cặp khác con số (E3).

Dữ liệu: eval/results/cache_eval.json do eval/run_cache_eval.py sinh ra. Với cặp khác con số, so sánh quy tắc đầy đủ
(có bước so khớp chữ số) với quy tắc bỏ bước đó, để thấy tác dụng của bước này.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402

rows = json.loads((Path(__file__).resolve().parents[3] / "eval" / "results" / "cache_eval.json").read_text(encoding="utf-8"))["rows"]
para = [r for r in rows if r["type"] == "dien_dat_lai"]
numd = [r for r in rows if r["type"] == "khac_con_so"]
pct = lambda k, n: 100 * k / n  # noqa: E731
bars = [
    ("Cặp diễn đạt lại\n(nên trúng)", pct(sum(r["hit"] and r["candidate_is_partner"] for r in para), len(para)), figstyle.SERIES[2]),
    ("Cặp khác con số, quy tắc đầy đủ\n(không nên trúng)", pct(sum(r["hit"] and r["candidate_is_partner"] for r in numd), len(numd)), figstyle.SERIES[0]),
    ("Cặp khác con số, bỏ bước\nso khớp số (không nên trúng)", pct(sum(r["hit_without_number_rule"] and r["candidate_is_partner"] for r in numd), len(numd)), figstyle.SERIES[1]),
]
fig, ax = figstyle.figure(width_cm=14, height_cm=6.4)
x = np.arange(len(bars))
ax.bar(x, [b[1] for b in bars], 0.55, color=[b[2] for b in bars])
for xi, b in zip(x, bars):
    ax.text(xi, b[1] + 2, f"{b[1]:.0f}%", ha="center", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels([b[0] for b in bars], fontsize=8)
ax.set_ylim(0, 100)
ax.set_ylabel("Tỉ lệ trúng bộ nhớ đệm (%)")
figstyle.save(fig, sys.argv[1])
