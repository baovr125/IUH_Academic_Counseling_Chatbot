"""H2-21 Ba chiến lược phân đoạn trên cùng một đoạn quy chế đào tạo.

Văn bản: khoản "1. Khối lượng học tập" của Quy chế đào tạo theo hệ thống tín chỉ (camnang.iuh.edu.vn), chép nguyên văn
từ chunk được truy xuất trong logs/academic_chatbot/2026-10-29/142502-quy-trinh-ang-ky-hoc.md.
Tham số của ba chiến lược chỉ để minh họa (không phải cấu hình HybridChunker của hệ thống):
  - kích thước cố định: 200 ký tự, không chồng lấn;
  - đệ quy: tách theo xuống dòng rồi gộp tham lam đến tối đa 400 ký tự;
  - theo cấu trúc: mỗi điểm a), b), c) là một đoạn, kèm tiêu đề khoản làm tiền tố.
Phông Consolas (độ rộng ký tự cố định) nên vị trí cắt được vẽ đúng theo số ký tự.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

HEADING = "1. Khối lượng học tập:"
ITEMS = [
    "a) Sinh viên phải đăng ký các học phần dự định sẽ học trong học kỳ dựa trên danh sách học phần được mở "
    "và điều kiện đăng ký của mỗi học phần, gồm: những học phần mới, một số học phần chưa đạt (để học lại, "
    "nếu có) và một số học phần đã đạt (để cải thiện điểm, nếu có).",
    "b) Khối lượng học tập mà mỗi sinh viên phải đăng ký trong mỗi học kỳ chính (trừ học kỳ cuối) tối thiểu "
    "là 12 tín chỉ và tối đa là 30 tín chỉ.",
    "c) Riêng số tín chỉ tối thiểu để được xét học bổng Khuyến khích học tập được quy định trong Quy định về "
    "việc xét, cấp học bổng cho sinh viên đại học chính quy, học viên đang học tập, nghiên cứu tại Trường "
    "Đại học Công nghiệp Thành phố Hồ Chí Minh.",
]
FULL = HEADING + "\n" + "\n".join(ITEMS)

W = 86          # ký tự mỗi dòng
FS = 8          # cỡ chữ (pt)
CHAR_W = 0.5498 * FS  # độ rộng ký tự Consolas (pt)
LINE_H = 1.55 * FS
FILLS = ["#DBEAFE", "#FFEDD5", "#DCFCE7", "#F3E8FF"]
EDGES = ["#2563EB", "#EA580C", "#16A34A", "#7C3AED"]


def fixed(text, size=200):
    return [(text[i:i + size], k, False) for k, i in enumerate(range(0, len(text), size))]


def recursive(limit=400):
    pieces = [HEADING] + ITEMS
    chunks, cur = [], ""
    for p in pieces:
        cand = (cur + "\n" + p) if cur else p
        if len(cand) <= limit:
            cur = cand
        else:
            chunks.append(cur)
            cur = p
    chunks.append(cur)
    return [(c, k, False) for k, c in enumerate(chunks)]


def structural():
    segs = []
    for k, it in enumerate(ITEMS):
        segs.append((HEADING + " ", k, True))   # tiền tố ngữ cảnh lặp lại
        segs.append((it, k, False))
    return segs


def layout(segs, sep_between_chunks):
    """Trả về danh sách dòng; mỗi dòng là list (col, text, chunk, is_prefix)."""
    chars = []
    last = None
    for text, k, pre in segs:
        if sep_between_chunks and last is not None and k != last:
            chars.append(("\n", k, pre))
        for ch in text:
            chars.append((ch, k, pre))
        last = k
    lines, line = [], []
    word = []

    def flush_word():
        nonlocal line
        if len(line) + len(word) > W and line:
            lines.append(line)
            line = []
            while word and word[0][0] == " ":
                word.pop(0)
        line.extend(word)
        word.clear()

    for c in chars:
        if c[0] == "\n":
            flush_word()
            lines.append(line)
            line = []
            continue
        word.append(c)
        if c[0] == " ":
            flush_word()
    flush_word()
    if line:
        lines.append(line)
    return lines


def draw(ax, lines, y0, mark_cuts):
    y = y0
    for line in lines:
        col, i = 0, 0
        while i < len(line):
            j = i
            while j < len(line) and line[j][1:] == line[i][1:]:
                j += 1
            text = "".join(c[0] for c in line[i:j])
            k, pre = line[i][1], line[i][2]
            ax.add_patch(plt.Rectangle((col * CHAR_W, y - LINE_H * 0.78), (j - i) * CHAR_W, LINE_H * 0.98,
                                       facecolor=FILLS[k % 4], edgecolor="none", zorder=1))
            ax.text(col * CHAR_W, y - LINE_H * 0.3, text, fontfamily="Consolas", fontsize=FS, va="center",
                    color="#6B7280" if pre else "#111827", style="italic" if pre else "normal", zorder=2)
            if mark_cuts and j < len(line) and line[j][1] != k:
                x = (col + j - i) * CHAR_W
                ax.plot([x, x], [y - LINE_H * 0.85, y + LINE_H * 0.25], color="#DC2626", lw=1.6, zorder=3)
            col += j - i
            i = j
        y -= LINE_H
    return y


panels = [
    ("(a) Kích thước cố định: 200 ký tự", layout(fixed(FULL), False), True),
    ("(b) Đệ quy theo xuống dòng, gộp tối đa 400 ký tự", layout(recursive(), True), False),
    ("(c) Theo cấu trúc: mỗi điểm một đoạn, kèm tiêu đề khoản (chữ nghiêng)", layout(structural(), True), False),
]
total_lines = sum(len(p[1]) for p in panels)
height_pt = total_lines * LINE_H + len(panels) * 2.6 * LINE_H
width_pt = W * CHAR_W
fig = plt.figure(figsize=((width_pt + 12) / 72, (height_pt + 10) / 72))
ax = fig.add_axes([6 / (width_pt + 12), 5 / (height_pt + 10), width_pt / (width_pt + 12), height_pt / (height_pt + 10)])
ax.set_xlim(0, width_pt)
ax.set_ylim(0, height_pt)
ax.axis("off")
y = height_pt
for title, lines, cuts in panels:
    ax.text(0, y - LINE_H * 0.55, title, fontfamily="Arial", fontsize=FS + 0.5, fontweight="bold", va="center")
    y -= LINE_H * 1.4
    y = draw(ax, lines, y, cuts)
    y -= LINE_H * 1.2
ax.text(width_pt, LINE_H * 0.2, "Mỗi màu là một đoạn; vạch đỏ: vị trí cắt ngang giữa câu", fontfamily="Arial",
        fontsize=FS - 0.5, color="#6B7280", ha="right", va="bottom")
fig.savefig(sys.argv[1], dpi=figstyle.DPI)
