"""H2-43 Dòng thời gian các kỹ thuật RAG liên quan (năm theo tài liệu được trích dẫn) và mức áp dụng trong đề tài
(khớp Bảng 2.5 trong drafts/02_3_microservices_congnghe.md)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

# Các công trình cùng năm được dàn ngang trong năm đó để nhãn không chồng nhau.
items = [  # (vị trí trên trục năm, nhãn, mức: 2 = có, 1 = một phần, 0 = không, độ cao nhãn)
    (2020.0, "RAG gốc\n(Lewis và cs.)", 2, 1.0),
    (2023.0, "Viết lại câu hỏi\n(Ma và cs.)", 2, -1.0),
    (2023.3, "Khảo sát RAG\n(Gao Y. và cs.)", 2, 1.0),
    (2023.6, "HyDE\n(Gao L. và cs.)", 0, -1.8),
    (2024.0, "Lost in the Middle\n(Liu và cs.)", 2, 1.8),
    (2024.3, "Self-RAG\n(Asai và cs.)", 1, -1.0),
    (2024.6, "CRAG\n(Yan và cs.)", 1, 1.0),
    (2026.0, "Định tuyến prompt\n(SpatioRoute)", 2, 1.0),
]
style = {2: dict(color=figstyle.SERIES[2], mfc=figstyle.SERIES[2]),
         1: dict(color=figstyle.SERIES[1], mfc="white"),
         0: dict(color="#9CA3AF", mfc="white")}
fig, ax = figstyle.figure(width_cm=15, height_cm=6.4)
ax.axhline(0, color="#334155", lw=1.2, zorder=1)
offsets = {}
for year, label, level, h in items:
    k = offsets.get(year, 0)
    offsets[year] = k + 1
    x = year + (k - 0.0) * 0.0
    ax.plot([x, x], [0, h * 0.78], color="#CBD5E1", lw=1, zorder=1)
    ax.plot(x, 0, "o", ms=9, mew=2, zorder=3, **style[level])
    ax.text(x, h, label, ha="center", va="center", fontsize=8.5,
            color="#111827" if level else "#6B7280")
ax.set_xlim(2019.3, 2026.7)
ax.set_ylim(-2.3, 2.3)
ax.set_yticks([])
ax.set_xticks(range(2020, 2027))
ax.spines["left"].set_visible(False)
ax.grid(False)
handles = [Line2D([], [], marker="o", ls="", ms=8, mew=2, label=t, **style[k])
           for k, t in [(2, "áp dụng"), (1, "áp dụng một phần"), (0, "không áp dụng")]]
ax.legend(handles=handles, loc="lower right", ncol=1, fontsize=8)
figstyle.save(fig, sys.argv[1])
