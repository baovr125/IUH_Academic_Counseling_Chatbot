"""H4-06 Một đoạn cha thật được HybridChunker tách thành các đoạn con.

Dữ liệu: đoạn cha "CHƯƠNG II – Kế hoạch và tổ chức đào tạo" của Quy chế đào tạo theo hệ thống tín chỉ
(camnang.iuh.edu.vn), chép từ log truy vấn logs/academic_chatbot/2026-10-29/142502-quy-trinh-ang-ky-hoc.md.
Kết quả tách: chạy chính chunkers/hybrid_chunker.py của dự án (max_child_size=600, overlap=100, max_parent_tokens=1200)
bằng script _data/H4-06_run_chunk.py, kết quả lưu ở _data/H4-06_chunks.json.
"""
import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

data = json.loads((Path(__file__).parent / "_data" / "H4-06_chunks.json").read_text(encoding="utf-8"))[0]
children = data["children"]
PREFIX = "[###### CHƯƠNG II]\n"

fig, ax = figstyle.figure(width_cm=15.5, height_cm=11.2)
ax.set_xlim(0, 100)
ax.set_ylim(0, 72)
ax.axis("off")

# Đoạn cha
ax.add_patch(FancyBboxPatch((1, 58), 98, 13, boxstyle="round,pad=0,rounding_size=1.2",
                            fc="#F0FDFA", ec="#0D9488", lw=1.2))
ax.text(3, 68.2, "Đoạn cha (document_parents)", fontsize=9, fontweight="bold", va="center")
ax.text(3, 64.4, "CHƯƠNG II – Kế hoạch và tổ chức đào tạo (Quy chế đào tạo tín chỉ)",
        fontsize=8, va="center")
ax.text(3, 60.8, f"{data['parent_len']:,} ký tự ≈ {data['parent_tokens']:,} token ≤ 1 200 → giữ nguyên cả mục"
        .replace(",", " "), fontsize=8, va="center", color="#374151")
ax.annotate("", xy=(50, 53.5), xytext=(50, 57.5), arrowprops=dict(arrowstyle="-|>", color="#334155", lw=1.1))
ax.text(52, 55.4, "tách theo đoạn → dòng → câu, chồng lấn 100 ký tự",
        fontsize=7.8, va="center", color="#374151")

# Đoạn con: 2 cột x 5 hàng
colors = ["#EFF6FF", "#FFF7ED"]
for i, c in enumerate(children):
    col, row = i % 2, i // 2
    x, y = 1 + col * 49.5, 42.5 - row * 10.6
    body = c[len(PREFIX):] if c.startswith(PREFIX) else c
    body = " ".join(body.replace("**", "").replace("######", "").split())
    snippet = textwrap.shorten(body, width=60, placeholder=" …")
    ax.add_patch(FancyBboxPatch((x, y), 48.5, 9.4, boxstyle="round,pad=0,rounding_size=1",
                                fc=colors[i % 2], ec="#94A3B8", lw=0.8))
    ax.text(x + 1.5, y + 7.3, f"Đoạn con {i + 1}", fontsize=8, fontweight="bold", va="center")
    ax.text(x + 47, y + 7.3, f"{len(c)} ký tự", fontsize=7.6, va="center", ha="right", color="#6B7280")
    ax.text(x + 1.5, y + 3.3, "\n".join(textwrap.wrap(snippet, 33)[:2]), fontsize=7.4, va="center",
            color="#111827", linespacing=1.15)
figstyle.save(fig, sys.argv[1])
