"""H2-26 Lượng tử hóa đối xứng INT8 (công thức 2-31, 2-32). Số liệu minh họa: 24 trọng số ngẫu nhiên (seed cố định)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402

rng = np.random.default_rng(3)
x = rng.normal(0, 0.05, 24).astype(np.float16).astype(np.float64)
s = np.abs(x).max() / 127
q = np.round(x / s)
xh = s * q
fig, (ax1, ax2) = figstyle.figure(width_cm=14, height_cm=7.4, nrows=2, sharex=True,
                                   gridspec_kw={"height_ratios": [2.2, 1]})
idx = np.arange(len(x))
ax1.vlines(idx, 0, x, color="#CBD5E1", lw=3, label="_")
ax1.plot(idx, x, "o", ms=4.5, color=figstyle.SERIES[0], label="giá trị gốc x (FP16)")
ax1.plot(idx, xh, "_", ms=11, mew=2, color=figstyle.SERIES[1], label="giá trị khôi phục s·q (INT8)")
ax1.axhline(0, color="#475569", lw=0.6)
ax1.set_ylabel("Trọng số")
ax1.legend(loc="upper right", ncol=2, fontsize=8)
ax1.set_ylim(min(x) * 1.25, max(x) * 1.6)
err = x - xh
ax2.bar(idx, err / s, color=figstyle.SERIES[2], width=0.6)
ax2.axhline(0.5, color="#6B7280", ls="--", lw=0.8)
ax2.axhline(-0.5, color="#6B7280", ls="--", lw=0.8)
ax2.set_ylim(-0.6, 0.6)
ax2.set_ylabel("Sai số / s")
ax2.set_xlabel(f"Chỉ số trọng số (s = max|x| / 127 ≈ {s:.2e})".replace(".", ",", 1))
for a in (ax1, ax2):
    a.yaxis.set_major_formatter(lambda v, _: f"{v:g}".replace(".", ","))
ax2.text(23.4, 0.52, "±s/2", fontsize=8, ha="right", va="bottom", color="#374151")
figstyle.save(fig, sys.argv[1])
