"""Đánh số lại Hình/Bảng viết tay trong các bản thảo sau khi thêm, bớt hoặc chuyển hình/bảng.

Cách dùng:
    python build/renumber.py            # đánh số lại theo thứ tự các phần trong build/report_config.json
    python build/renumber.py --dry-run  # chỉ in bảng đối chiếu số cũ → số mới

Quy tắc:
  * Hình nhận diện theo mã ảnh (H3-25…) trong dòng ![Hình x.y. …](…/H3-25.png).
  * Bảng nhận diện theo nội dung chú thích ("Bảng 3.4. Đặc tả use case UC02 …" → khóa "Đặc tả use case UC02 …").
  * Chương: số chương tăng ở mỗi heading cấp 1 có đánh số; phụ lục: theo "## Phụ lục X." (Hình X.1, Bảng X.1).
  * Công thức: \tag{c-k} đánh lại theo thứ tự trong chương; câu nhắc dạng "(c-k)" đổi theo.
  * Mọi chỗ nhắc "Hình a.b"/"Bảng a.b" có trong bảng đối chiếu đều được đổi theo; số không có trong bảng
    (ví dụ của chương chưa viết) được giữ nguyên.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUM = r"[0-9A-Z]+\.\d+"
FIG_LINE = re.compile(r"!\[Hình (" + NUM + r")\. (.*?)\]\(([^)]*?/)(H\d-\d\d[a-z]?)\.png\)")
TAB_DEF = re.compile(r'(?m)(?:^|caption=")Bảng (' + NUM + r')\. ([^"\n]+)')
H1 = re.compile(r"(?m)^# (?!.*\{\.unnumbered)")
APPX = re.compile(r"(?m)^## Phụ lục ([A-Z])\.")
EQ_TAG = re.compile(r"\\tag\{(\d+-\d+)\}")


def draft_files() -> list[Path]:
    cfg = json.loads((ROOT / "build/report_config.json").read_text(encoding="utf-8"))
    parts = cfg["parts"]
    return [ROOT / p for name in ("main", "appendix") for p in parts.get(name, []) if (ROOT / p).exists()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    files = draft_files()
    texts = {f: f.read_text(encoding="utf-8") for f in files}

    # 1. Số cũ → khóa (mã hình / chú thích bảng)
    old_fig, old_tab = {}, {}
    for t in texts.values():
        for m in FIG_LINE.finditer(t):
            old_fig[m.group(1)] = m.group(4)
        for m in TAB_DEF.finditer(t):
            old_tab[m.group(1)] = m.group(2).strip()

    # 2. Khóa → số mới, theo thứ tự xuất hiện
    new_fig, new_tab = {}, {}
    chap, prefix, nf, nt = 0, None, 0, 0
    for f in files:
        t = texts[f]
        events = [(m.start(), "h1", None) for m in H1.finditer(t)]
        events += [(m.start(), "appx", m.group(1)) for m in APPX.finditer(t)]
        events += [(m.start(), "fig", m.group(4)) for m in FIG_LINE.finditer(t)]
        events += [(m.start(), "tab", m.group(2).strip()) for m in TAB_DEF.finditer(t)]
        for _, kind, val in sorted(events, key=lambda e: e[0]):
            if kind == "h1":
                chap += 1
                prefix, nf, nt = str(chap), 0, 0
            elif kind == "appx":
                prefix, nf, nt = val, 0, 0
            elif kind == "fig":
                nf += 1
                new_fig[val] = f"{prefix}.{nf}"
            else:
                nt += 1
                new_tab[val] = f"{prefix}.{nt}"

    # Công thức: \tag{c-k} đánh lại theo thứ tự trong từng chương; câu nhắc "(c-k)" đổi theo
    eq_map, chap, neq = {}, 0, 0
    for f in files:
        t = texts[f]
        events = [(m.start(), "h1", None) for m in H1.finditer(t)]
        events += [(m.start(), "appx", None) for m in APPX.finditer(t)]
        events += [(m.start(), "eq", m.group(1)) for m in EQ_TAG.finditer(t)]
        for _, kind, val in sorted(events, key=lambda e: e[0]):
            if kind == "h1":
                chap, neq = chap + 1, 0
            elif kind == "appx":
                chap = None
            elif chap is not None:
                neq += 1
                eq_map[val] = f"{chap}-{neq}"
    eq_changed = {o: n for o, n in eq_map.items() if o != n}

    fig_map = {o: new_fig[k] for o, k in old_fig.items() if k in new_fig}
    tab_map = {o: new_tab[k] for o, k in old_tab.items() if k in new_tab}
    changed = {o: n for o, n in {**{"Hình " + a: "Hình " + b for a, b in fig_map.items()},
                                  **{"Bảng " + a: "Bảng " + b for a, b in tab_map.items()}}.items() if o != n}
    for o, n in sorted(changed.items()):
        print(f"{o:12} → {n}")
    for o, n in sorted(eq_changed.items(), key=lambda kv: [int(x) for x in kv[0].split("-")]):
        print(f"({o}){'':6} → ({n})")
    if args.dry_run or not (changed or eq_changed):
        print("Không ghi tệp." if args.dry_run else "Không có gì thay đổi.")
        return 0

    # 3. Thay một lượt (dùng mã tạm để tránh đổi dây chuyền 3.4 → 3.5 → 3.6)
    pat = re.compile(r"(Hình|Bảng) (" + NUM + r")(?![\d.]*\d)")

    def repl(m):
        key = f"{m.group(1)} {m.group(2)}"
        return changed.get(key, key)

    eq_pat = re.compile(r"(\\tag\{|\()(\d+-\d+)(\}|\))")

    def eq_repl(m):
        if (m.group(1) == "(") != (m.group(3) == ")"):
            return m.group(0)
        return m.group(1) + eq_changed.get(m.group(2), m.group(2)) + m.group(3)

    for f, t in texts.items():
        nt_ = eq_pat.sub(eq_repl, pat.sub(repl, t))
        if nt_ != t:
            f.write_text(nt_, encoding="utf-8")
            print("đã ghi", f.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
