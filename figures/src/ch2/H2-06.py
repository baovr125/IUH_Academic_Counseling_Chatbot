"""H2-06 Lấy mẫu top-p với p = 0,8 (công thức 2-7). Số liệu minh họa."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402

tokens = ["học kỳ", "tín chỉ", "năm học", "đợt", "tháng", "môn", "quý", "lần", "kỳ thi", "ngày"]
logits = np.array([3.0, 2.2, 1.5, 0.8, 0.2, -0.5, -0.9, -1.2, -1.6, -2.0])
p = np.exp(logits) / np.exp(logits).sum()
cum = np.cumsum(p)
n_nucleus = int(np.argmax(cum >= 0.8)) + 1

fig, ax = figstyle.figure(width_cm=14, height_cm=6.8)
x = np.arange(len(tokens))
colors = [figstyle.SERIES[0] if i < n_nucleus else "#CBD5E1" for i in x]
ax.bar(x, p, 0.6, color=colors)
ax2 = ax.twinx()
ax2.plot(x, cum, "o-", color=figstyle.SERIES[1], ms=3.5, lw=1.4, label="Xác suất tích lũy")
ax2.axhline(0.8, color="#6B7280", ls="--", lw=0.9)
ax2.text(len(tokens) - 0.6, 0.8, "p = 0,8", va="bottom", ha="right", fontsize=8.5, color="#374151")
ax2.set_ylim(0, 1.05)
ax2.set_ylabel("Xác suất tích lũy")
ax2.grid(False)
ax2.spines["right"].set_visible(True)
ax.set_xticks(x, tokens, rotation=30, ha="right")
ax.set_ylabel("Xác suất của token")
ax.set_ylim(0, 0.6)
ax.grid(axis="x", visible=False)
for a in (ax, ax2):
    a.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}".replace(".", ","))
ax.text(n_nucleus / 2 - 0.5, 0.56, f"tập hạt nhân V_p ({n_nucleus} token)", ha="center", fontsize=8.5, color=figstyle.SERIES[0])
ax2.legend(loc="center right")
figstyle.save(fig, sys.argv[1])
