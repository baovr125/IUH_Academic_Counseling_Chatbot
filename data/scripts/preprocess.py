"""
Pipeline tiền xử lý dữ liệu .md crawl từ IUH.
Đọc từng file .md → làm sạch → ghi lại file .md mới vào output_dir.

Các vấn đề được xử lý:
  1. Giữ nguyên YAML frontmatter (source_url, title, crawled_at) — chuẩn hoá lại
  2. Loại bỏ khối "File đính kèm" (chỉ là link PDF, không có nội dung)
  3. Loại bỏ file chỉ toàn link đính kèm (không có nội dung thật)
  4. Làm sạch link Markdown rỗng / link trùng URL
  5. Gộp dòng plain-text bị wrap vào dòng trước 
  6. Collapse whitespace thừa trong từng ô bảng, xóa ## lọt vào ô
  7. Normalize whitespace bên trong từng dòng
  8. Chuyển bảng Markdown → text "Key: Value | Key: Value" dễ embed hơn
  9. Xóa dòng nhiễu (--- thừa, dòng trống lặp lại)
"""

import re
from pathlib import Path


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_frontmatter(text: str) -> tuple[dict, str]:
    meta = {}
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    m = pattern.match(text)
    if m:
        for line in m.group(1).splitlines():
            kv = re.match(r'^(\w+):\s*"?([^"]*)"?\s*$', line.strip())
            if kv:
                meta[kv.group(1)] = kv.group(2).strip()
        body = text[m.end():]
    else:
        body = text
    return meta, body


def build_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key in ("source_url", "title", "crawled_at"):
        if key in meta:
            lines.append(f'{key}: "{meta[key]}"')
    lines.append("---\n")
    return "\n".join(lines)


def remove_attachment_block(text: str) -> str:
    text = re.sub(
        r"###\s*📎.*?File đính kèm.*?\n(- \[.*?\]\(.*?\)\n?)*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text


def clean_markdown_links(text: str) -> str:
    text = re.sub(r"\[[\)]*\]\((https?://[^\)]+)\)", r"\1", text)

    def replace_link(m):
        link_text, url = m.group(1).strip(), m.group(2).strip()
        return url if (not link_text or link_text == url) else link_text

    text = re.sub(r"\[([^\]]*)\]\((https?://[^\)]+)\)", replace_link, text)
    text = re.sub(r"\*(https?://[^\*]+)\*", r"\1", text)
    return text


def join_wrapped_lines(text: str) -> str:
    """
    Gộp dòng bị wrap vào dòng trước nó.
    Dòng wrap: không rỗng, không bắt đầu bằng | # - * > http
    và không là dấu phân cách bảng (|---|).
    Gộp vào bất kỳ dòng trước (kể cả dòng bảng có |).
    """
    lines = text.splitlines()
    result = []
    for line in lines:
        stripped = line.strip()
        # Dòng cấu trúc: rỗng, heading, list, bảng mới, url thuần
        is_structural = (
            not stripped
            or stripped.startswith(("#", "-", "*", ">", "http", "|"))
            or re.match(r"^[\|\-\s]+$", stripped)  # separator bảng
        )
        if not is_structural and result:
            result[-1] = result[-1].rstrip() + " " + stripped
        else:
            result.append(line)
    return "\n".join(result)


def clean_table_cells(text: str) -> str:
    """Collapse whitespace trong mỗi ô bảng, xóa ## lọt vào ô."""
    lines = text.splitlines()
    result = []
    for line in lines:
        if "|" in line:
            cells = line.split("|")
            cleaned = []
            for cell in cells:
                cell = re.sub(r"##\s*", "", cell)
                cell = re.sub(r"\s+", " ", cell).strip()
                cleaned.append(cell)
            result.append("|".join(cleaned))
        else:
            result.append(line)
    return "\n".join(result)


def normalize_whitespace_in_lines(text: str) -> str:
    lines = []
    for line in text.splitlines():
        lines.append(re.sub(r"[ \t]{2,}", " ", line.strip()))
    return "\n".join(lines)


def convert_table_to_text(text: str) -> str:
    """
    Chuyển bảng Markdown → text phẳng "Header: Value | Header: Value".
    Section header trong ô đơn → ## heading.
    """
    lines = text.splitlines()
    result_lines = []
    header = None
    i = 0

    while i < len(lines):
        line = lines[i]
        if "|" not in line:
            result_lines.append(line)
            i += 1
            continue

        cells = [c.strip() for c in line.split("|") if c.strip()]
        if not cells:
            i += 1
            continue

        # Dòng header: dòng sau là separator |---|
        if header is None and i + 1 < len(lines) and re.match(r"^[\|\-\s]+$", lines[i + 1]):
            header = cells
            i += 2
            continue

        # Ô đơn → section heading
        if len(cells) == 1:
            result_lines.append(f"\n## {cells[0]}")
            i += 1
            continue

        # Dòng data
        if header and len(cells) >= len(header):
            parts = [f"{h}: {c}" for h, c in zip(header, cells) if h and c]
            result_lines.append(" | ".join(parts) if parts else "")
        else:
            result_lines.append(" | ".join(cells))
        i += 1

    return "\n".join(result_lines)


def remove_noise_lines(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    prev_blank = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^-{3,}$", stripped):
            continue
        if stripped == "":
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False
    return "\n".join(cleaned)


def is_empty_content(text: str) -> bool:
    return len(text.strip()) < 30


def clean_body(body: str) -> str:
    body = remove_attachment_block(body)
    body = clean_markdown_links(body)
    body = join_wrapped_lines(body)          # gộp dòng wrap TRƯỚC khi xử lý bảng
    body = clean_table_cells(body)
    body = normalize_whitespace_in_lines(body)
    body = convert_table_to_text(body)
    body = remove_noise_lines(body)
    return body.strip()


# ── Main ──────────────────────────────────────────────────────────────────────

def process_files(input_dir: str, output_dir: str):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    md_files = sorted(input_path.glob("*.md"))
    print(f"Tìm thấy {len(md_files)} file .md trong '{input_dir}'")

    processed, skipped = [], []

    for fp in md_files:
        raw = fp.read_text(encoding="utf-8")
        meta, body = extract_frontmatter(raw)
        cleaned_body = clean_body(body)

        if is_empty_content(cleaned_body):
            skipped.append(fp.name)
            print(f"  ⚠ Bỏ qua (không có nội dung thật): {fp.name}")
            continue

        out_text = build_frontmatter(meta) + "\n" + cleaned_body + "\n"
        out_file = output_path / fp.name
        out_file.write_text(out_text, encoding="utf-8")

        processed.append(fp.name)
        print(f"  ✓ {fp.name}  ({len(raw)} → {len(out_text)} ký tự)")

    print(f"\n✅ Đã xử lý {len(processed)} file → '{output_dir}'")
    if skipped:
        print(f"⚠  Bỏ qua {len(skipped)} file (chỉ có link PDF): {skipped}")


if __name__ == "__main__":
    process_files(
        input_dir="./markdown_craw5/markdown_updates/",
        output_dir="/home/hao0107/workSpace/IUH_Academic_Counseling_Chatbot/data/preprocessed",
    )

    print("\n" + "=" * 70)
    for fp in sorted(Path("/home/hao0107/workSpace/IUH_Academic_Counseling_Chatbot/data/preprocessed").glob("*.md")):
        print(f"\n📄 {fp.name}\n")
        print(fp.read_text(encoding="utf-8"))