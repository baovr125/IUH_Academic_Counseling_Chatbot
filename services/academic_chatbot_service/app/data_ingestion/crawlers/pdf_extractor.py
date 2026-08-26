import os
import io
import requests
import logging
import hashlib
from threading import Lock

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

from app.data_ingestion.crawlers.ocr_service import execute_ocr

logger = logging.getLogger(__name__)

class PDFExtractor:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.ocr_lock = Lock()
        
    def extract_text(self, pdf_url: str) -> str:
        pdf_name = pdf_url.split('/')[-1] or "document.pdf"
        try:
            res = requests.get(pdf_url, verify=False, timeout=15)
            if res.status_code == 200 and PdfReader:
                pdf_bytes = io.BytesIO(res.content)
                reader = PdfReader(pdf_bytes)
                text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                
                safe_name = hashlib.md5(pdf_url.encode('utf-8')).hexdigest()[:8] + "_" + pdf_name
                pdf_dir = os.path.join(self.output_dir, "pdfs")
                os.makedirs(pdf_dir, exist_ok=True)
                with open(os.path.join(pdf_dir, safe_name), "wb") as f:
                    f.write(res.content)
                
                if len(text.strip()) < 50:
                    logger.warning(f"PDF {pdf_url} có vẻ là bản scan. Kích hoạt OCR fallback...")
                    text = self._ocr_pdf(res.content)
                    
                return text
        except Exception as e:
            logger.error(f"Lỗi đọc PDF {pdf_url}: {e}")
        return ""

    def _ocr_pdf(self, pdf_bytes: bytes) -> str:
        if not fitz or not Image:
            return "[CẦN CÀI ĐẶT PyMuPDF VÀ Pillow ĐỂ OCR]"
            
        try:
            logger.info("Bắt đầu OCR PDF qua Gemini...")
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            full_text = ""
            
            MAX_OCR_PAGES = 30
            for i, page in enumerate(doc):
                if i >= MAX_OCR_PAGES:
                    full_text += f"\n\n[ĐÃ BỎ QUA CÁC TRANG SAU DO VƯỢT QUÁ GIỚI HẠN {MAX_OCR_PAGES} TRANG OCR]\n"
                    break
                    
                logger.info(f"Đang OCR trang {i+1}/{len(doc)}")
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                prompt = (
                    "Hãy trích xuất TẤT CẢ văn bản từ hình ảnh này chính xác như những gì xuất hiện trên ảnh. "
                    "Đảm bảo giữ đúng tiếng Việt, cấu trúc đoạn văn bản và bảng biểu (nếu có). "
                    "Không giải thích, không bình luận, chỉ trả về văn bản."
                )
                
                with self.ocr_lock:
                    try:
                        result = execute_ocr(prompt, img)
                        if result:
                            full_text += result + "\n\n"
                    except Exception as e:
                        if "API_OCR_FAILED" in str(e):
                            logger.error(f"Google API sập ở trang {i+1}. Thử dùng Tesseract làm giải pháp cứu hộ...")
                            if pytesseract:
                                try:
                                    tesseract_text = pytesseract.image_to_string(img, lang='vie')
                                    if len(tesseract_text.strip()) > 5:
                                        full_text += f"\n\n[DỮ LIỆU ĐƯỢC TRÍCH XUẤT CỨU HỘ BẰNG TESSERACT]\n" + tesseract_text.strip() + "\n\n"
                                        continue
                                except Exception:
                                    pass
                            
                            full_text += f"\n\n[ĐÃ DỪNG OCR Ở TRANG {i+1} DO LỖI API GOOGLE TỪ CHỐI VÀ KHÔNG CÓ TESSERACT CỨU HỘ]\n"
                            break
            doc.close()
            return "\n[DỮ LIỆU ĐƯỢC TRÍCH XUẤT BẰNG CÔNG NGHỆ AI OCR]\n" + full_text.strip()
            
        except Exception as e:
            logger.error(f"Lỗi khi OCR PDF: {e}")
            return "[CÓ LỖI XẢY RA KHI OCR PDF]"

    def extract_image_text(self, img_url: str) -> str:
        # Tạm thời bỏ qua trích xuất chữ từ ảnh theo yêu cầu
        return ""
