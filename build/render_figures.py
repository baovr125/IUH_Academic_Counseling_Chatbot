"""Xuất hình của báo cáo và tạo ảnh giữ chỗ (kế hoạch mục 6.4).

  figures/src/chN/HN-XX.mmd   → Mermaid (build/tools/mermaid.min.js, Chromium của Playwright)
  figures/src/chN/HN-XX.puml  → PlantUML (build/tools/plantuml.jar)
  figures/src/chN/HN-XX.svg   → SVG viết tay + figures/src/_theme/svg.css, chụp bằng Playwright
  figures/src/chN/HN-XX.py    → matplotlib; script nhận đường dẫn PNG đầu ra làm tham số
  → figures/chN/HN-XX.png

Hình trong figures/FIGURES.md chưa có PNG thì được tạo ảnh giữ chỗ (khung xám ghi mã và chú thích),
có đánh dấu trong metadata PNG. Ảnh thật (ví dụ ảnh chụp giao diện) lưu đè đúng tên file sẽ không bị
ghi đè. Cuối cùng cột "Trạng thái" trong FIGURES.md được cập nhật.

Chạy (từ thư mục Report):
  python build/render_figures.py              # xuất hình có nguồn mới/đổi + tạo ảnh giữ chỗ
  python build/render_figures.py H4-11 H3-25  # chỉ xuất các hình này (luôn vẽ lại)
  python build/render_figures.py --all        # vẽ lại toàn bộ
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

BUILD = Path(__file__).resolve().parent
REPORT = BUILD.parent
FIG = REPORT / "figures"
SRC = FIG / "src"
THEME = SRC / "_theme"
TOOLS = BUILD / "tools"
CATALOG = FIG / "FIGURES.md"

SCALE = 3                      # hệ số chụp của Playwright → 288 dpi
SRC_EXT = (".mmd", ".puml", ".svg", ".py")
ID_RE = re.compile(r"^H(\d)-(\d\d)[a-z]?$")  # hậu tố a, b khi một hình được tách đôi
PLACEHOLDER_KEY = "iuh-placeholder"


# ---------------------------------------------------------------------------
# Danh mục
# ---------------------------------------------------------------------------
def read_catalog() -> dict[str, dict]:
    figs = {}
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and ID_RE.match(cells[0]):
            figs[cells[0]] = dict(id=cells[0], loai=cells[1], uu_tien=cells[2], muc=cells[3],
                                  caption=cells[4], nguon=cells[5], trang_thai=cells[6])
    return figs


def write_status(statuses: dict[str, str]) -> None:
    lines = CATALOG.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and cells[0] in statuses:
            if cells[6].startswith("bỏ"):
                continue
            if cells[6] == "đã duyệt" and statuses[cells[0]] != "giữ chỗ":
                continue
            cells[6] = statuses[cells[0]]
            lines[i] = "| " + " | ".join(cells) + " |"
    CATALOG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def png_path(fid: str) -> Path:
    return FIG / f"ch{fid[1]}" / f"{fid}.png"


def find_source(fid: str) -> Path | None:
    for ext in SRC_EXT:
        p = SRC / f"ch{fid[1]}" / f"{fid}{ext}"
        if p.exists():
            return p
    return None


def is_placeholder(png: Path) -> bool:
    try:
        with Image.open(png) as im:
            return im.info.get(PLACEHOLDER_KEY) == "1"
    except OSError:
        return False


def set_dpi(png: Path, dpi: int) -> None:
    """Ghi DPI vào PNG để pandoc đặt đúng kích thước in."""
    with Image.open(png) as im:
        im.load()
        img = im.copy()
    img.save(png, dpi=(dpi, dpi))


# ---------------------------------------------------------------------------
# Ảnh giữ chỗ
# ---------------------------------------------------------------------------
def _font(size: int, bold: bool = False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)
    except OSError:
        return ImageFont.load_default()


def make_placeholder(fig: dict) -> None:
    dpi = 200
    w = round(15.5 / 2.54 * dpi)
    h = round((8.7 if fig["loai"] == "AC" else 6.0) / 2.54 * dpi)
    img = Image.new("RGB", (w, h), "#F3F4F6")
    d = ImageDraw.Draw(img)
    # viền nét đứt
    for x in range(0, w, 28):
        d.line([(x, 2), (min(x + 16, w), 2)], fill="#9CA3AF", width=4)
        d.line([(x, h - 3), (min(x + 16, w), h - 3)], fill="#9CA3AF", width=4)
    for y in range(0, h, 28):
        d.line([(2, y), (2, min(y + 16, h))], fill="#9CA3AF", width=4)
        d.line([(w - 3, y), (w - 3, min(y + 16, h))], fill="#9CA3AF", width=4)
    is_ac = fig["loai"] == "AC"
    title = f"{'ẢNH GIAO DIỆN – CHỜ CHỤP' if is_ac else 'HÌNH CHƯA VẼ'}  ·  {fig['id']}  ·  {fig['loai']}  ·  mức {fig['uu_tien']}"
    lines = textwrap.wrap(fig["caption"].replace("`", ""), width=70)
    hint = (f"Lưu ảnh chụp vào: figures/ch{fig['id'][1]}/{fig['id']}.png" if is_ac
            else f"Nguồn: {fig['nguon'].replace('`', '')}")
    f_title, f_body, f_hint = _font(40, True), _font(36), _font(30)
    y = h // 2 - (len(lines) + 2) * 26
    for text, font, color in [(title, f_title, "#374151")] + [(l, f_body, "#111827") for l in lines] + [(hint, f_hint, "#6B7280")]:
        tw = d.textlength(text, font=font)
        d.text(((w - tw) / 2, y), text, font=font, fill=color)
        y += font.size + 22
    info = PngImagePlugin.PngInfo()
    info.add_text(PLACEHOLDER_KEY, "1")
    out = png_path(fig["id"])
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, pnginfo=info, dpi=(dpi, dpi))


# ---------------------------------------------------------------------------
# Bộ vẽ
# ---------------------------------------------------------------------------
def find_chromium() -> str | None:
    """Dùng Chromium đã có trong thư mục ms-playwright (bản nào cũng được) để khỏi tải thêm.
    Trả về None thì Playwright dùng bản mặc định của nó."""
    root = Path.home() / "AppData" / "Local" / "ms-playwright"
    found = sorted(root.glob("chromium-*/chrome-win*/chrome.exe"))
    return str(found[-1]) if found else None


class Browser:
    """Mở Chromium (Playwright) một lần cho mọi hình Mermaid/SVG."""

    def __init__(self):
        self._pw = self._browser = None

    def page(self):
        if self._browser is None:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            try:
                self._browser = self._pw.chromium.launch(executable_path=find_chromium())
            except Exception:
                self._pw.stop()
                self._pw = None
                raise
        return self._browser.new_page(device_scale_factor=SCALE, viewport={"width": 1100, "height": 800})

    def close(self):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()


def render_mermaid(src: Path, out: Path, browser: Browser) -> None:
    code = src.read_text(encoding="utf-8")
    lines = code.splitlines()
    first = next((i for i, l in enumerate(lines) if l.strip() and not l.strip().startswith("%%")), 0)
    if re.match(r"\s*(flowchart|graph)\b", lines[first]):
        lines.insert(first + 1, (THEME / "classes.mmd").read_text(encoding="utf-8").rstrip())
        code = "\n".join(lines)
    cfg = json.loads((THEME / "mermaid.json").read_text(encoding="utf-8"))
    page = browser.page()
    page.set_content("<html><body style='margin:0;background:#fff'><div id='c' style='display:inline-block;padding:8px'></div></body></html>")
    page.add_script_tag(path=str(TOOLS / "mermaid.min.js"))
    err = page.evaluate(
        """async ([code, cfg]) => {
            mermaid.initialize(cfg);
            try { const {svg} = await mermaid.render('fig', code);
                  document.getElementById('c').innerHTML = svg; return null; }
            catch (e) { return String(e.message || e); }
        }""", [code, cfg])
    if err:
        page.close()
        raise RuntimeError(f"Mermaid lỗi: {err}")
    # Giữ kích thước tự nhiên của SVG (Mermaid đặt max-width theo nội dung)
    page.evaluate("""() => { const s = document.querySelector('#c svg');
        const w = s.style.maxWidth || s.getAttribute('width'); if (w) { s.style.width = w; } }""")
    page.locator("#c").screenshot(path=str(out))
    page.close()
    set_dpi(out, 96 * SCALE)


def render_svg(src: Path, out: Path, browser: Browser) -> None:
    css = (THEME / "svg.css").read_text(encoding="utf-8")
    svg = src.read_text(encoding="utf-8")
    page = browser.page()
    page.set_content(f"<html><head><style>body{{margin:0;background:#fff}}{css}</style></head>"
                     f"<body><div id='c' style='display:inline-block'>{svg}</div></body></html>")
    page.wait_for_timeout(100)
    page.locator("#c svg").screenshot(path=str(out))
    page.close()
    set_dpi(out, 96 * SCALE)


def render_plantuml(src: Path, out: Path) -> None:
    res = subprocess.run(["java", "-jar", str(TOOLS / "plantuml.jar"), "-tpng", "-charset", "UTF-8",
                          "-o", str(out.parent.resolve()), str(src)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    produced = out.parent / f"{src.stem}.png"
    if res.returncode != 0 or not produced.exists():
        raise RuntimeError(f"PlantUML lỗi: {res.stderr.strip() or res.stdout.strip()}")
    if produced != out:
        produced.replace(out)
    set_dpi(out, 200)


def render_python(src: Path, out: Path) -> None:
    # -B: không sinh __pycache__ trong figures/src/_theme (làm sai mốc thời gian của theme)
    res = subprocess.run([sys.executable, "-B", str(src), str(out)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", cwd=src.parent)
    if res.returncode != 0 or not out.exists():
        raise RuntimeError(f"Script lỗi: {res.stderr.strip()[-800:]}")


def render(fid: str, src: Path, browser: Browser) -> None:
    out = png_path(fid)
    out.parent.mkdir(parents=True, exist_ok=True)
    {".mmd": lambda: render_mermaid(src, out, browser),
     ".svg": lambda: render_svg(src, out, browser),
     ".puml": lambda: render_plantuml(src, out),
     ".py": lambda: render_python(src, out)}[src.suffix]()


def theme_mtime() -> float:
    return max(p.stat().st_mtime for p in THEME.iterdir() if p.is_file())


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="mã hình cần vẽ lại, ví dụ H4-11")
    ap.add_argument("--all", action="store_true", help="vẽ lại mọi hình có nguồn")
    args = ap.parse_args()

    figs = read_catalog()
    tmt = theme_mtime()
    browser = Browser()
    statuses, errors, drawn = {}, [], []
    try:
        # hình có nguồn nhưng chưa có trong danh mục
        for p in SRC.glob("ch*/H*-*.*"):
            if p.stem not in figs:
                print(f"[CẢNH BÁO] {p.relative_to(REPORT)} không có trong FIGURES.md")
        for fid, fig in figs.items():
            src, out = find_source(fid), png_path(fid)
            if src:
                stale = (not out.exists() or is_placeholder(out) or src.stat().st_mtime > out.stat().st_mtime
                         or tmt > out.stat().st_mtime)
                if args.all or fid in args.ids or (not args.ids and stale):
                    try:
                        render(fid, src, browser)
                        drawn.append(fid)
                    except Exception as e:  # noqa: BLE001 - báo lỗi từng hình, vẽ tiếp hình khác
                        errors.append(f"{fid}: {e}")
            if not out.exists():
                make_placeholder(fig)
            statuses[fid] = "giữ chỗ" if is_placeholder(out) else ("đã vẽ" if src else "ảnh thật")
    finally:
        browser.close()
    write_status(statuses)

    for e in errors:
        print(f"[LỖI] {e}", file=sys.stderr)
    count = {s: list(statuses.values()).count(s) for s in ("đã vẽ", "ảnh thật", "giữ chỗ")}
    a_left = sum(1 for f, s in statuses.items() if s == "giữ chỗ" and figs[f]["uu_tien"] == "A")
    print(f"Đã vẽ lần này: {', '.join(drawn) or 'không có'}")
    print(f"Tổng {len(figs)} hình | đã vẽ {count['đã vẽ']} | ảnh thật {count['ảnh thật']} | "
          f"giữ chỗ {count['giữ chỗ']} (mức A còn {a_left})")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
