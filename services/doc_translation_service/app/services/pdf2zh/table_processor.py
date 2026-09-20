import logging
import fitz
import markdown
import copy
from typing import List, Tuple, Any

logger = logging.getLogger(__name__)

class TableProcessor:
    def __init__(self, doc_en: fitz.Document, doc_zh: fitz.Document, translator: Any):
        self.doc_en = doc_en
        self.doc_zh = doc_zh
        self.translator = translator
        self.translated_tables: List[Tuple[int, fitz.Rect, str]] = []
        
    def extract_and_translate_tables(self, page_num: int):
        """Extracts tables from a page, translates them, and stores the results."""
        page = self.doc_en[page_num]
        tables = page.find_tables()
        
        if not tables or not tables.tables:
            return
            
        for i, table in enumerate(tables.tables):
            try:
                markdown_content = table.to_markdown()
                if not markdown_content.strip():
                    continue
                    
                system_instruction = "You are a professional translator. Translate the following markdown table into Vietnamese. MUST keep the exact markdown table format (| - |) and structure. Only translate the text."
                
                translated_md = self.translator.translate(
                    text=markdown_content,
                    context=system_instruction
                )
                
                if "|" not in translated_md:
                    logger.warning(f"Translated table on page {page_num} seems to have lost markdown format.")
                    
                # Store the bbox of the table to mask it later
                self.translated_tables.append((page_num, fitz.Rect(table.bbox), translated_md))
                logger.info(f"Successfully extracted and translated table {i} on page {page_num}")
                
            except Exception as e:
                logger.error(f"Error processing table {i} on page {page_num}: {e}")

    def mask_original_tables(self, page_num: int):
        """No-op: Requirement dictates that original tables remain unmasked at their original positions."""
        pass

    def append_appendix(self):
        """Creates appendix pages at the end of the document for translated tables."""
        if not self.translated_tables:
            return
            
        page = self.doc_zh.new_page()
        y_cursor = 50
        
        page.insert_text(fitz.Point(50, y_cursor), "PHU LUC: CAC BANG DA DICH", fontsize=16, fontname="helv", color=(0, 0, 0))
        y_cursor += 30
        
        for idx, (page_num, bbox, translated_md) in enumerate(self.translated_tables):
            title = f"Bang {idx + 1} (Tham chieu tu trang {page_num + 1}):"
            
            if y_cursor > page.rect.height - 150:
                page = self.doc_zh.new_page()
                y_cursor = 50
                
            page.insert_text(fitz.Point(50, y_cursor), title, fontsize=12, fontname="helv", color=(0, 0, 0))
            y_cursor += 20
            
            # Convert Markdown to HTML
            html = markdown.markdown(translated_md, extensions=['tables'])
            
            # CSS for table to look nice in PDF
            styled_html = f"""
            <style>
                table {{ border-collapse: collapse; width: 100%; font-family: Helvetica; font-size: 10pt; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
            {html}
            """
            
            rect = fitz.Rect(50, y_cursor, page.rect.width - 50, page.rect.height - 50)
            
            try:
                ret = page.insert_htmlbox(rect, styled_html)
                if isinstance(ret, tuple) and len(ret) >= 1:
                    spare_height = ret[0]
                    if spare_height == -1:
                        # Bảng quá lớn so với khoảng trống còn lại, tạo trang mới
                        page = self.doc_zh.new_page()
                        y_cursor = 50
                        rect = fitz.Rect(50, y_cursor, page.rect.width - 50, page.rect.height - 50)
                        ret = page.insert_htmlbox(rect, styled_html)
                        if isinstance(ret, tuple) and len(ret) >= 1 and ret[0] != -1:
                            used_height = rect.height - ret[0]
                            y_cursor += used_height + 30
                        else:
                            y_cursor += 400 # fallback if it still doesn't fit a whole page
                    else:
                        used_height = rect.height - spare_height
                        y_cursor += used_height + 30
                else:
                    y_cursor += 200
            except Exception as e:
                logger.error(f"Failed to insert html table: {e}")
                page.insert_textbox(rect, translated_md, fontsize=10, fontname="helv")
                y_cursor += 150
