import os
import json
import requests
import logging
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Xử lý đường dẫn tuyệt đối (Absolute Paths)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")
URL_LIST_FILE = os.path.join(DATA_DIR, "urls.json")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Thiết lập Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "link_extract.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def extract_urls_from_sitemap(sitemap_url):
    """Trích xuất danh sách URL từ sitemap.xml. Hỗ trợ fix lỗi URL nối chuỗi của camnang.iuh"""
    logging.info(f"Đang đọc sitemap: {sitemap_url}")
    try:
        response = requests.get(sitemap_url, verify=False, timeout=10)
        if response.status_code != 200:
            return []
            
        # Kiểm tra nếu trả về HTML thay vì XML
        if "html" in response.text[:100].lower():
            logging.warning(f"{sitemap_url} trả về HTML thay vì XML. Website này không có sitemap chuẩn.")
            return []
            
        urls = []
        soup = BeautifulSoup(response.content, "xml")
        for loc in soup.find_all("loc"):
            url = loc.text.strip()
            if "https://" in url[10:]:
                url = "https://" + url.split("https://")[-1]
                
            # Kiểm tra nghiêm ngặt: Chỉ lấy link thuộc domain IUH, bỏ link ảnh/Google
            parsed = urlparse(url)
            if "iuh.edu.vn" in parsed.netloc and "google" not in parsed.netloc:
                urls.append(url)
            
        logging.info(f"Tìm thấy {len(urls)} links từ sitemap.")
        return list(set(urls))
    except Exception as e:
        logging.error(f"Lỗi đọc sitemap: {e}")
        return []

def extract_urls_from_category(category_url, max_pages=None):
    """Trích xuất URL bằng cách cào các trang danh mục. Hỗ trợ Dynamic Pagination (Lật trang cho đến khi hết)"""
    logging.info(f"Đang quét danh mục: {category_url}")
    urls = set()
    domain = f"{urlparse(category_url).scheme}://{urlparse(category_url).netloc}"
    
    page = 1
    try:
        while True:
            if max_pages and page > max_pages:
                break
                
            page_url = f"{category_url}?page={page}" if page > 1 else category_url
            response = requests.get(page_url, verify=False, timeout=10)
            if response.status_code != 200: 
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            found_new_links = False
            
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if href.endswith(".html"):
                    full_url = urljoin(domain, href)
                    parsed_full = urlparse(full_url)
                    
                    # Kiểm tra nghiêm ngặt để loại bỏ link rác
                    if "iuh.edu.vn" in parsed_full.netloc and "google" not in parsed_full.netloc:
                        if full_url not in urls:
                            urls.add(full_url)
                            found_new_links = True
            
            # Nếu trang này không có link mới nào, có nghĩa là đã lật đến trang trắng/trang cuối
            if not found_new_links:
                logging.info(f"Đã chạm đáy ở trang {page}, ngừng quét danh mục này.")
                break
                
            logging.info(f"Quét xong trang {page}, tổng link tạm thời: {len(urls)}")
            page += 1
            time.sleep(0.5) # Tránh bị rate-limit
                        
        logging.info(f"Hoàn thành quét danh mục. Tìm thấy {len(urls)} links.")
        return list(urls)
    except Exception as e:
        logging.error(f"Lỗi quét danh mục: {e}")
        return list(urls)

if __name__ == "__main__":
    logging.info("========== BƯỚC 0: TRÍCH XUẤT TOÀN BỘ URL ==========")
    all_urls = set()
    
    # 1. Lấy từ sitemap của camnang
    camnang_urls = extract_urls_from_sitemap("https://camnang.iuh.edu.vn/sitemap.xml")
    all_urls.update(camnang_urls)
    
    # 2. Lấy từ danh mục của iuh.edu.vn
    # Dùng Dynamic Pagination để lấy toàn bộ lịch sử
    iuh_tin_tuc = extract_urls_from_category("https://iuh.edu.vn/vi/tin-tuc", max_pages=15) # Giới hạn 15 trang để test, bỏ max_pages để vét sạch
    iuh_thong_bao = extract_urls_from_category("https://iuh.edu.vn/vi/thong-bao", max_pages=15)
    all_urls.update(iuh_tin_tuc)
    all_urls.update(iuh_thong_bao)
    
    target_urls = list(all_urls)
    logging.info(f"Tổng hợp được {len(target_urls)} URLs. Tiến hành lưu vào {URL_LIST_FILE}")
    
    with open(URL_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(target_urls, f, indent=4, ensure_ascii=False)
