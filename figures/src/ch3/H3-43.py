"""H3-43 Các thành phần của hệ thống thiết kế giao diện.
Đối chiếu 30/10/2026: frontend/tailwind.config.js (brand = colors.blue, darkMode "class"; cam cho tín hiệu đặc biệt,
amber cho cảnh báo, rose cho lỗi), frontend/src/assets/brand/ (iuh-logo.png, iuh-logo-dark.png),
lớp nền dark mode dùng nhiều nhất: slate-900, slate-800 (đếm trong src/**/*.tsx). Mã màu theo bảng màu mặc định của Tailwind 3.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402
import matplotlib.image as mpimg  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

BRAND_DIR = Path(__file__).resolve().parents[4] / "IUH_Academic_Counseling_Chatbot" / "frontend" / "src" / "assets" / "brand"
BLUE = [("50", "#EFF6FF"), ("100", "#DBEAFE"), ("200", "#BFDBFE"), ("300", "#93C5FD"), ("400", "#60A5FA"),
        ("500", "#3B82F6"), ("600", "#2563EB"), ("700", "#1D4ED8"), ("800", "#1E40AF"), ("900", "#1E3A8A"),
        ("950", "#172554")]
SIGNAL = [("#F97316", "cam (orange-500)", "chuỗi ngày học,\nthẻ cần ôn"),
          ("#F59E0B", "hổ phách (amber-500)", "cảnh báo"),
          ("#F43F5E", "đỏ hồng (rose-500)", "lỗi")]

fig, ax = figstyle.figure(width_cm=15.5, height_cm=9.6)
ax.set_xlim(0, 155)
ax.set_ylim(0, 96)
ax.axis("off")


def title(x, y, s):
    ax.text(x, y, s, fontsize=9.5, fontweight="bold", va="bottom")


# 1. Logo trên nền sáng và nền tối
title(2, 89, "Logo IUH")
ax.add_patch(Rectangle((2, 56), 22, 31, color="#FFFFFF", ec="#CBD5E1", lw=0.8))
ax.add_patch(Rectangle((26, 56), 22, 31, color="#0F172A"))
ax.imshow(mpimg.imread(BRAND_DIR / "iuh-logo.png"), extent=(5, 21, 58.5, 84.5), zorder=3)
ax.imshow(mpimg.imread(BRAND_DIR / "iuh-logo-dark.png"), extent=(29, 45, 58.5, 84.5), zorder=3)
ax.text(13, 52.5, "nền sáng", ha="center", fontsize=8, color="#6B7280")
ax.text(37, 52.5, "nền tối", ha="center", fontsize=8, color="#6B7280")

# 2. Dải màu chủ đạo brand = blue
title(54, 89, "Màu chủ đạo: brand = blue (Tailwind)")
w = 9.0
for i, (name, hexv) in enumerate(BLUE):
    x = 54 + i * w
    ax.add_patch(Rectangle((x, 66), w - 0.6, 20, color=hexv, ec="#CBD5E1" if i == 0 else hexv, lw=0.6))
    ax.text(x + (w - 0.6) / 2, 62.5, name, ha="center", fontsize=7.5)
ax.text(54, 56.5, "600: nút chính, liên kết · 50–100: nền nhấn · 800–950: nền nhấn ở chế độ tối",
        fontsize=7.8, color="#374151")

# 3. Màu tín hiệu
title(2, 44, "Màu tín hiệu (mỗi màu một ý nghĩa)")
for i, (hexv, name, use) in enumerate(SIGNAL):
    y = 33 - i * 13
    ax.add_patch(FancyBboxPatch((2, y), 9, 9, boxstyle="round,pad=0,rounding_size=1.5", color=hexv))
    ax.text(14, y + 6.3, name, fontsize=8, va="center")
    ax.text(14, y + 2.2, use.replace("\n", " "), fontsize=7.8, va="center", color="#6B7280")

# 4. Chế độ sáng và tối
title(70, 44, "Chế độ sáng / tối / theo hệ thống")
for x0, bg, card, fg, sub, label in [(70, "#F8FAFC", "#FFFFFF", "#0F172A", "#64748B", "Sáng"),
                                     (113, "#0F172A", "#1E293B", "#F1F5F9", "#94A3B8", "Tối")]:
    ax.add_patch(Rectangle((x0, 4), 40, 37, color=bg, ec="#CBD5E1", lw=0.8))
    ax.add_patch(FancyBboxPatch((x0 + 3, 9), 34, 27, boxstyle="round,pad=0,rounding_size=2", color=card,
                                ec="#E2E8F0" if label == "Sáng" else "#334155", lw=0.8))
    ax.text(x0 + 6, 30.5, "Ôn tập hôm nay", fontsize=8.5, fontweight="bold", color=fg)
    ax.text(x0 + 6, 25, "12 thẻ đến hạn", fontsize=7.8, color=sub)
    ax.add_patch(FancyBboxPatch((x0 + 6, 12), 18, 7, boxstyle="round,pad=0,rounding_size=1.5",
                                color="#2563EB" if label == "Sáng" else "#3B82F6"))
    ax.text(x0 + 15, 15.5, "Bắt đầu", fontsize=7.8, color="#FFFFFF", ha="center", va="center")
    ax.add_patch(FancyBboxPatch((x0 + 27, 12), 7, 7, boxstyle="round,pad=0,rounding_size=1.5", color="#F97316"))
    ax.text(x0 + 30.5, 15.5, "7", fontsize=7.8, color="#FFFFFF", ha="center", va="center", fontweight="bold")
    ax.text(x0 + 20, 0.5, label, ha="center", fontsize=8, color="#6B7280")

figstyle.save(fig, sys.argv[1])
