import os
import io
import time
import requests
import logging
from threading import Lock
import re
import hashlib

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
    from google import genai
except ImportError:
    genai = None

from dotenv import load_dotenv

load_dotenv()
gemini_client = None
if os.getenv("GEMINI_API_KEY") and genai:
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

logger = logging.getLogger(__name__)

class PDFExtractor:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.ocr_lock = Lock()
        
    def extract_text(self, pdf_url: str) -> str:
        """
        Tải file PDF từ URL và trích xuất text. 
        Nếu text trống hoặc quá ngắn (có thể là PDF scan), sẽ kích hoạt OCR.
        Đồng thời lưu file PDF xuống đĩa để tham chiếu.
        """
        if not PdfReader: 
            return ""
        try:
            logger.info(f"Đang tải & trích xuất PDF: {pdf_url}")
            res = requests.get(pdf_url, verify=False, timeout=30)
            if res.status_code == 200:
                # Lưu file PDF lại
                pdf_dir = os.path.join(self.output_dir, "pdfs")
                os.makedirs(pdf_dir, exist_ok=True)
                
                # Tạo tên file từ URL để tránh trùng lặp
                safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', pdf_url.split('/')[-1])
                if not safe_name.lower().endswith('.pdf'): safe_name += ".pdf"
                pdf_path = os.path.join(pdf_dir, safe_name)
                
                with open(pdf_path, 'wb') as f:
                    f.write(res.content)
                
                reader = PdfReader(io.BytesIO(res.content))
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted: text += extracted + "\n"
                
                # Nếu text quá ngắn (< 50 ký tự), khả năng cao đây là PDF scan (dạng ảnh)
                if len(text.strip()) < 50:
                    logger.warning(f"PDF {pdf_url} có vẻ là bản scan. Kích hoạt OCR fallback...")
                    text = self._ocr_pdf(res.content)
                    
                return text
        except Exception as e:
            logger.error(f"Lỗi đọc PDF {pdf_url}: {e}")
        return ""

    def _ocr_pdf(self, pdf_bytes: bytes) -> str:
        """
        Dùng PyMuPDF (fitz) chuyển PDF thành ảnh và dùng Gemini OCR.
        """
        if not fitz or not gemini_client or not Image:
            missing = []
            if not fitz: missing.append("PyMuPDF (fitz)")
            if not genai: missing.append("google-genai")
            elif not gemini_client: missing.append("GEMINI_API_KEY không có giá trị")
            if not Image: missing.append("Pillow (PIL)")
            logger.error(f"LỖI OCR: Thiếu {' và '.join(missing)}. Bỏ qua OCR.")
            return f"[CẦN CÀI ĐẶT/CẤU HÌNH: {', '.join(missing)} ĐỂ CHẠY OCR]"
            
        try:
            logger.info("Bắt đầu OCR qua Gemini 3.5 Flash Lite...")
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            full_text = ""
            
            MAX_OCR_PAGES = 30 # Giới hạn số trang tối đa để tránh cạn kiệt API
            for i, page in enumerate(doc):
                if i >= MAX_OCR_PAGES:
                    logger.warning(f"PDF quá dài (> {MAX_OCR_PAGES} trang). Đã ngắt OCR để bảo vệ quota API.")
                    full_text += f"\n\n[ĐÃ BỎ QUA CÁC TRANG SAU DO VƯỢT QUÁ GIỚI HẠN {MAX_OCR_PAGES} TRANG OCR]\n"
                    break
                    
                logger.info(f"Đang OCR trang {i+1}/{len(doc)}")
                pix = page.get_pixmap(dpi=150) # render to image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                prompt = (
                    "Hãy trích xuất TẤT CẢ văn bản từ hình ảnh này chính xác như những gì xuất hiện trên ảnh. "
                    "Đảm bảo giữ đúng tiếng Việt, cấu trúc đoạn văn bản và bảng biểu (nếu có). "
                    "Không giải thích, không bình luận, chỉ trả về văn bản."
                )
                
                models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemma-4-31b-it"]
                success = False
                
                with self.ocr_lock: # Bắt đầu xếp hàng
                    for model_name in models:
                        try:
                            logger.info(f"Đang thử OCR với model: {model_name}")
                            response = gemini_client.models.generate_content(
                                model=model_name,
                                contents=[prompt, img]
                            )
                            if response.text:
                                full_text += response.text + "\n\n"
                            time.sleep(4.5) # API Free tier limit 15 RPM
                            success = True
                            break # Thành công thì thoát vòng lặp fallback
                        except Exception as api_err:
                            err_msg = str(api_err).lower()
                            logger.warning(f"Model {model_name} thất bại: {api_err}")
                            # Thử tiếp model khác
                            time.sleep(2)
                            
                    if not success:
                        logger.error(f"Tất cả các model đều thất bại khi OCR trang {i+1}")
                
            doc.close()
            
            ocr_tag = "\n[DỮ LIỆU ĐƯỢC TRÍCH XUẤT BẰNG CÔNG NGHỆ AI OCR]\n"
            return ocr_tag + full_text.strip()
            
        except Exception as e:
            logger.error(f"Lỗi khi OCR PDF: {e}")
            return "[CÓ LỖI XẢY RA KHI OCR PDF]"
