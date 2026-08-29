import os
import pymupdf4llm
from markdown_pdf import Section, MarkdownPdf
from app.utils.logger import logger

def extract_pdf_to_markdown(pdf_path: str, doc_id: str) -> tuple[str, str]:
    """
    Trích xuất file PDF thành văn bản Markdown và lưu ảnh vào thư mục tạm.
    Trả về: (markdown_text, image_dir_path)
    """
    image_dir = os.path.join("temp_images", doc_id)
    os.makedirs(image_dir, exist_ok=True)
    
    logger.info(f"Đang bóc tách PDF thành Markdown cho doc_id={doc_id}...")
    try:
        # Sử dụng force_text=True để tránh lỗi OCR
        md_text = pymupdf4llm.to_markdown(pdf_path, write_images=True, image_path=image_dir, force_text=True)
        return md_text, image_dir
    except Exception as e:
        logger.exception(f"Lỗi khi trích xuất PDF sang Markdown: {e}")
        raise e

TABLE_CSS = """
body {
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.6;
    color: #333;
    padding: 10px;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 11pt;
    page-break-inside: auto;
}
tr {
    page-break-inside: avoid;
    page-break-after: auto;
}
thead {
    display: table-header-group;
}
th, td {
    border: 1px solid #d1d5db;
    padding: 10px 12px;
    text-align: left;
    vertical-align: top;
    word-wrap: break-word;
}
th {
    background-color: #f3f4f6;
    font-weight: 600;
    color: #1f2937;
    border-bottom: 2px solid #9ca3af;
}
tr:nth-child(even) {
    background-color: #f9fafb;
}
img {
    max-width: 100%;
    height: auto;
    margin: 15px 0;
    page-break-inside: avoid;
}
code {
    background-color: #f3f4f6;
    padding: 2px 5px;
    border-radius: 4px;
    font-family: monospace;
}
pre {
    background-color: #f8f9fa;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    page-break-inside: avoid;
}
"""

def render_markdown_to_pdf(md_text: str, output_pdf_path: str):
    """
    Render chuỗi Markdown (bao gồm ảnh đã lưu cục bộ và bảng biểu đẹp) thành file PDF.
    """
    logger.info(f"Đang render Markdown thành PDF tại {output_pdf_path}...")
    try:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(md_text), user_css=TABLE_CSS)
        pdf.meta["title"] = "Translated Document"
        pdf.save(output_pdf_path)
    except Exception as e:
        logger.exception(f"Lỗi khi render PDF từ Markdown: {e}")
        raise e

