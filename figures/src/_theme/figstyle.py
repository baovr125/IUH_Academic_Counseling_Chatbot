"""Style matplotlib chung cho biểu đồ của báo cáo (kế hoạch mục 6.2).

Dùng trong script hình:
    import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_theme"))
    import figstyle
    fig, ax = figstyle.figure(width_cm=14, height_cm=7)
    ...
    figstyle.save(fig, sys.argv[1])

Quy ước: không đặt tiêu đề trong hình (tiêu đề nằm ở caption), trục có đơn vị.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PALETTE = json.loads((Path(__file__).with_name("palette.json")).read_text(encoding="utf-8"))
# Dãy màu cho nhiều đường/cột: lấy theo thứ tự các thành phần, đủ phân biệt khi in màu
SERIES = ["#2563EB", "#EA580C", "#0D9488", "#7C3AED", "#16A34A", "#DB2777", "#B45309", "#475569"]
DPI = 300

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 9.5,
    "axes.labelsize": 9.5,
    "axes.edgecolor": "#475569",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "#E5E7EB",
    "grid.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.prop_cycle": matplotlib.cycler(color=SERIES),
    "xtick.color": "#334155",
    "ytick.color": "#334155",
    "legend.frameon": False,
    "legend.fontsize": 9,
    "lines.linewidth": 1.8,
    "savefig.facecolor": "white",
})


def figure(width_cm: float = 14.0, height_cm: float = 7.0, **kw):
    return plt.subplots(figsize=(width_cm / 2.54, height_cm / 2.54), **kw)


def save(fig, out: str) -> None:
    fig.tight_layout()
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
