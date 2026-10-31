"""H2-17 Lost in the Middle: độ chính xác theo vị trí tài liệu chứa đáp án, 20 tài liệu.
Số liệu chép từ Liu và cs. (2024), Phụ lục G.2, Bảng 6 (paper/check2307.03172v3.pdf, trang 18)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402

pos = [1, 5, 10, 15, 20]
data = {
    "GPT-3.5-Turbo": [75.8, 57.2, 53.8, 55.4, 63.2],
    "Claude-1.3": [59.9, 55.9, 56.8, 57.2, 60.1],
    "LongChat-13B (16K)": [68.6, 57.4, 55.3, 52.5, 55.0],
    "MPT-30B-Instruct": [53.7, 51.8, 52.2, 52.7, 56.3],
}
fig, ax = figstyle.figure(width_cm=14, height_cm=7)
for name, acc in data.items():
    ax.plot(pos, acc, "o-", ms=4, label=name)
ax.set_xticks(pos, [f"{p}" for p in pos])
ax.set_xlabel("Vị trí của tài liệu chứa đáp án trong ngữ cảnh (1 = đầu tiên)")
ax.set_ylabel("Độ chính xác (%)")
ax.set_ylim(48, 78)
ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}")
ax.legend(ncol=2, loc="upper center")
figstyle.save(fig, sys.argv[1])
