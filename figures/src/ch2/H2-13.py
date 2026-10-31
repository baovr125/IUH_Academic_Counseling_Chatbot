"""H2-13 Đồ thị nhiều tầng của HNSW và đường tìm kiếm tham lam (số liệu minh họa).
Điểm ngẫu nhiên (seed cố định); mỗi tầng nối mỗi điểm với 3 láng giềng gần nhất trong tầng;
tìm kiếm tham lam thật sự được chạy từ điểm vào ở tầng trên cùng xuống tầng 0."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402

rng = np.random.default_rng(7)
pts = rng.uniform(0, 1, size=(46, 2))
level = np.floor(-np.log(rng.uniform(size=len(pts))) * (1 / np.log(4))).astype(int)  # m_L = 1/ln M, M = 4
level = np.minimum(level, 2)
level[0] = 2  # điểm vào ở tầng cao nhất
query = np.array([0.82, 0.22])


def knn_edges(ids, k=3):
    edges = set()
    for i in ids:
        d = [(np.linalg.norm(pts[i] - pts[j]), j) for j in ids if j != i]
        for _, j in sorted(d)[:k]:
            edges.add(tuple(sorted((i, j))))
    return edges


def greedy(start, ids, edges):
    nbrs = {i: [] for i in ids}
    for a, b in edges:
        nbrs[a].append(b)
        nbrs[b].append(a)
    path, cur = [start], start
    while True:
        best = min(nbrs[cur] + [cur], key=lambda j: np.linalg.norm(pts[j] - query))
        if best == cur:
            return path
        path.append(best)
        cur = best


fig, axes = figstyle.figure(width_cm=15, height_cm=5.6, ncols=3)
cur = 0
for col, lv in enumerate([2, 1, 0]):
    ax = axes[col]
    ids = [i for i in range(len(pts)) if level[i] >= lv]
    edges = knn_edges(ids)
    for a, b in edges:
        ax.plot(*zip(pts[a], pts[b]), color="#CBD5E1", lw=0.8, zorder=1)
    ax.scatter(*pts[ids].T, s=14, color="#475569", zorder=2)
    path = greedy(cur, ids, edges)
    ax.plot(*pts[path].T, color="#DC2626", lw=1.8, zorder=3)
    ax.scatter(*pts[path[0]], s=40, color="#2563EB", zorder=4)
    ax.scatter(*query, marker="*", s=120, color="#EA580C", zorder=5)
    cur = path[-1]
    ax.set_title(f"Tầng {lv} ({len(ids)} điểm)", fontsize=9.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.03)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color("#CBD5E1")
from matplotlib.lines import Line2D  # noqa: E402

handles = [
    Line2D([], [], marker="*", ls="", color="#EA580C", ms=10, label="câu hỏi"),
    Line2D([], [], marker="o", ls="", color="#2563EB", ms=6, label="điểm bắt đầu ở mỗi tầng"),
    Line2D([], [], color="#DC2626", lw=1.8, label="đường đi tham lam"),
]
fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8.5)
fig.subplots_adjust(bottom=0.16)
figstyle.save(fig, sys.argv[1])
