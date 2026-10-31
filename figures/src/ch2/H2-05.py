"""H2-05 Phân phối xác suất của cùng một vector logit ở ba giá trị nhiệt độ (công thức 2-6). Số liệu minh họa."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402

tokens = ["học kỳ", "tín chỉ", "năm học", "đợt", "tháng", "môn"]
logits = np.array([3.0, 2.2, 1.5, 0.8, 0.2, -0.5])
temps = [0.5, 1.0, 2.0]

fig, ax = figstyle.figure(width_cm=14, height_cm=6.8)
x = np.arange(len(tokens))
w = 0.26
for k, t in enumerate(temps):
    p = np.exp(logits / t) / np.exp(logits / t).sum()
    bars = ax.bar(x + (k - 1) * w, p, w, label=f"T = {str(t).replace('.', ',')}")
ax.set_xticks(x, tokens)
ax.set_ylabel("Xác suất p")
ax.set_xlabel("Token ứng viên tiếp theo cho “Học phí được đóng theo …”")
ax.set_ylim(0, 1)
ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}".replace(".", ","))
ax.legend(loc="upper right")
ax.grid(axis="x", visible=False)
figstyle.save(fig, sys.argv[1])
