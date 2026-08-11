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

def render_markdown_to_pdf(md_text: str, output_pdf_path: str):
    """
    Render chuỗi Markdown (bao gồm ảnh đã lưu cục bộ) thành file PDF 1 cột dễ đọc.
    """
    logger.info(f"Đang render Markdown thành PDF tại {output_pdf_path}...")
    try:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(md_text))
        pdf.meta["title"] = "Translated Document"
        pdf.save(output_pdf_path)
    except Exception as e:
        logger.exception(f"Lỗi khi render PDF từ Markdown: {e}")
        raise e
