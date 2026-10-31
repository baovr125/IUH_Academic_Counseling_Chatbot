"""H2-37 Giới hạn tần suất theo cửa sổ cố định (công thức 2-52), L = 10 yêu cầu/phút. Số liệu minh họa."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402

L, W = 10, 60
times = [6, 18, 31, 54, 55, 56, 56.5, 57, 57.5, 58, 58.5, 59,
         60.5, 61, 61.5, 62, 62.5, 63, 63.5, 64, 64.5, 65, 72, 85, 101]
counts, acc, rej = {}, [], []
for t in times:
    w = int(t // W)
    if counts.get(w, 0) < L:
        counts[w] = counts.get(w, 0) + 1
        acc.append(t)
    else:
        rej.append(t)
burst = [t for t in acc if 54 <= t <= 65]

fig, ax = figstyle.figure(width_cm=14, height_cm=5.6)
ax.axvspan(54, 65.5, color="#FEF3C7", zorder=0)
ax.axvline(W, color="#334155", lw=1.2)
ax.text(30, 1.62, "Cửa sổ 1: [0, 60) giây", ha="center", fontsize=9)
ax.text(90, 1.62, "Cửa sổ 2: [60, 120) giây", ha="center", fontsize=9)
ax.scatter(acc, [1] * len(acc), s=36, color=figstyle.SERIES[0], zorder=3, label="cho qua")
ax.scatter(rej, [1] * len(rej), s=46, marker="x", color="#DC2626", zorder=3, label="bị từ chối (HTTP 429)")
ax.text(59.7, 0.62, f"{len(burst)} yêu cầu được cho qua trong ~11 giây (54–65 s)", ha="center", fontsize=8.5)
ax.set_xlim(0, 120)
ax.set_ylim(0.4, 1.9)
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.set_xlabel("Thời gian (giây)")
ax.grid(axis="y", visible=False)
ax.legend(loc="center right", bbox_to_anchor=(1, 0.6), fontsize=8.5)
figstyle.save(fig, sys.argv[1])
