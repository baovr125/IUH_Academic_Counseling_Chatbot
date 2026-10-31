"""H5-02 Hit@K và MRR theo cấu hình truy xuất (E1).

Dữ liệu: eval/results/retrieval_ablation.json do eval/run_retrieval_ablation.py sinh ra (45 câu hỏi, 35 câu có đáp án).
Cột đậm: đánh giá chặt (chỉ tính tài liệu gold); cột nhạt: đánh giá nới lỏng (tính cả tài liệu chứa đủ cụm khóa).
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402

data = json.loads((Path(__file__).resolve().parents[3] / "eval" / "results" / "retrieval_ablation.json").read_text(encoding="utf-8"))
s = data["summary"]["tat_ca_co_dap_an"]
cfgs = ["C1", "C2", "C3", "C4", "C5"]
labels = ["C1\nvector", "C2\ntoàn văn", "C3\nlai (RRF)", "C4\nlai + xếp\nhạng lại", "C5\nđầy đủ"]
metrics = [("Hit@1", "hit@1", "hit@1_nl"), ("Hit@3", "hit@3", "hit@3_nl"), ("MRR@5", "mrr@5", "mrr@5_nl")]

fig, ax = figstyle.figure(width_cm=15, height_cm=7.2)
x = np.arange(len(cfgs))
w = 0.26
for i, (name, strict, relaxed) in enumerate(metrics):
    def val(cfg, key):
        v = s[cfg][key]
        return v["k"] / v["n"] if isinstance(v, dict) else v
    ys = [val(c, strict) for c in cfgs]
    yn = [val(c, relaxed) for c in cfgs]
    color = figstyle.SERIES[i]
    ax.bar(x + (i - 1) * w, yn, w, color=color, alpha=0.35, label=None)
    ax.bar(x + (i - 1) * w, ys, w, color=color, label=name)
    for xi, v in zip(x + (i - 1) * w, ys):
        ax.text(xi, v + 0.015, f"{v:.2f}", ha="center", fontsize=7.5)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=8.5)
ax.set_ylim(0, 1.08)
ax.set_ylabel("Tỉ lệ / điểm (0–1)")
ax.legend(ncol=3, loc="upper left")
figstyle.save(fig, sys.argv[1])
