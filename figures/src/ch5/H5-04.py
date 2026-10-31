"""H5-04 Phân bố độ trễ từng giai đoạn của một lượt hỏi đáp (E5).

Dữ liệu: eval/results/latency_summary.json do eval/run_latency_eval.py sinh ra từ answers_V2.jsonl. Biểu đồ hộp: hộp là
khoảng từ phân vị 25 đến 75, vạch giữa là trung vị, râu kéo đến giá trị nhỏ nhất và lớn nhất trong 1,5 lần độ rộng hộp.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402

s = json.loads((Path(__file__).resolve().parents[3] / "eval" / "results" / "latency_summary.json").read_text(encoding="utf-8"))
raw = s["raw"]
order = [("router_ms", "Bộ định\ntuyến"), ("retrieval_ms", "Truy xuất và\nxếp hạng lại"), ("gen_ms", "Sinh câu\ntrả lời"),
         ("ttft_ms", "Đến chữ đầu\ntiên (TTFT)"), ("total_ms", "Tổng\ncả lượt")]
data = [[v / 1000 for v in raw[k] if v is not None] for k, _ in order]
fig, ax = figstyle.figure(width_cm=14.5, height_cm=7)
bp = ax.boxplot(data, widths=0.5, patch_artist=True, showfliers=True, flierprops={"markersize": 3, "markerfacecolor": "#94A3B8", "markeredgecolor": "#94A3B8"},
                medianprops={"color": "#111827", "linewidth": 1.6})
for patch, c in zip(bp["boxes"], figstyle.SERIES):
    patch.set_facecolor(c)
    patch.set_alpha(0.55)
ax.set_xticklabels([l for _, l in order], fontsize=8.5)
ax.set_yscale("log")
ax.set_ylim(0.4, 60)
ax.set_yticks([0.5, 1, 2, 5, 10, 30])
ax.set_yticklabels(["0,5", "1", "2", "5", "10", "30"])
ax.set_ylabel("Thời gian (giây, thang logarit)")
figstyle.save(fig, sys.argv[1])
