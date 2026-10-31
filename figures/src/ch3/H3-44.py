"""H3-44 Trang đăng nhập ở 360, 768, 1280 px (ảnh có sẵn, không chứa dữ liệu người dùng).
Nguồn: frontend/screenshots-responsive/theme-after/light/login-{360,768,1280}.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SRC = (Path(__file__).resolve().parents[4] / "IUH_Academic_Counseling_Chatbot" / "frontend"
       / "screenshots-responsive" / "theme-after" / "light")
DPI = 200
H = 900                      # chiều cao chung của ba ảnh (px), trước khi thêm nhãn
GAP, PAD, LABEL = 36, 12, 70

shots = []
for w in (360, 768, 1280):
    im = Image.open(SRC / f"login-{w}.png").convert("RGB")
    # Ảnh chụp toàn trang có thể rất dài: chỉ lấy phần đầu theo tỉ lệ màn hình thật của từng thiết bị.
    view_h = {360: 780, 768: 1024, 1280: 800}[w]
    im = im.crop((0, 0, im.width, min(im.height, round(view_h * im.width / w))))
    im = im.resize((round(im.width * H / im.height), H), Image.LANCZOS)
    shots.append((w, im))

total_w = sum(im.width for _, im in shots) + GAP * (len(shots) - 1) + 2 * PAD
canvas = Image.new("RGB", (total_w, H + LABEL + 2 * PAD), "white")
draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("arial.ttf", 44)
except OSError:
    font = ImageFont.load_default()
x = PAD
for w, im in shots:
    canvas.paste(im, (x, PAD))
    draw.rectangle((x - 1, PAD - 1, x + im.width, PAD + im.height), outline="#94A3B8", width=2)
    label = f"{w} px"
    tw = draw.textlength(label, font=font)
    draw.text((x + (im.width - tw) / 2, PAD + H + 14), label, fill="#374151", font=font)
    x += im.width + GAP

# Rộng 15,5 cm khi in
scale_dpi = round(canvas.width / (15.5 / 2.54))
canvas.save(sys.argv[1], dpi=(scale_dpi, scale_dpi))
