import pytesseract
from PIL import Image, ImageOps
import requests
from io import BytesIO
import re

# Trỏ đến file cài đặt Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def is_valid_image_metadata(img_url, img_class=""):
    """Tầng 1: Lọc mù qua URL và Class HTML"""
    junk_keywords = ['logo', 'icon', 'avatar', 'banner', 'thumb', 'background', 'gallery', 'slider']
    
    # Kiểm tra URL
    url_lower = img_url.lower()
    if any(keyword in url_lower for keyword in junk_keywords):
        return False
        
    # Kiểm tra Class HTML
    class_lower = img_class.lower()
    if any(keyword in class_lower for keyword in junk_keywords):
        return False
        
    return True

def preprocess_image(img):
    """Tiền xử lý ảnh để Tesseract đọc nét hơn"""
    # Chuyển sang ảnh xám (Grayscale)
    gray_img = ImageOps.grayscale(img)
    # Tăng độ tương phản (Auto contrast)
    better_img = ImageOps.autocontrast(gray_img)
    return better_img

def extract_text_from_image(img_url, img_class=""):
    # 1. Tầng 1: Lọc Metadata
    if not is_valid_image_metadata(img_url, img_class):
        return ""

    try:
        # Tải ảnh về memory
        response = requests.get(img_url, headers=headers, verify=False, timeout=5)
        if response.status_code != 200: return ""
        
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        
        # 2. Tầng 2: Lọc Kích thước và Tỷ lệ
        # Bỏ qua ảnh quá nhỏ (icon) hoặc quá mỏng (đường kẻ, banner)
        if width < 250 or height < 250: 
            return ""
        
        aspect_ratio = width / height
        # Bỏ qua ảnh quá dài ngang (banner) hoặc dài dọc bất thường
        if aspect_ratio > 4.0 or aspect_ratio < 0.25:
            return ""

        # 3. Tiền xử lý ảnh
        processed_img = preprocess_image(img)
        
        # 4. Chạy Tesseract OCR
        # config='--psm 3': Chế độ tự động phân tích bố cục trang (rất tốt cho văn bản)
        raw_text = pytesseract.image_to_string(processed_img, lang='vie', config='--psm 3')
        
        # Dọn dẹp text
        clean_txt = clean_text(raw_text)
        
        # 5. Tầng 4: Lọc sau OCR
        # Đếm số từ thực tế, loại bỏ ký tự đặc biệt vô nghĩa
        words = re.findall(r'\b\w+\b', clean_txt)
        
        # Nếu bức ảnh chỉ chứa dưới 8 từ, coi như đó là ảnh trang trí/hội thảo tình cờ có chữ
        if len(words) < 8:
            return ""
            
        return clean_txt

    except Exception as e:
        # Bỏ qua mượt mà nếu lỗi tải ảnh hoặc định dạng không hỗ trợ
        return ""