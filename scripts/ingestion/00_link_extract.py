import os
import json
import requests
import logging
import time
import random
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from logging.handlers import MemoryHandler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Xử lý đường dẫn tuyệt đối (Absolute Paths)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")
URL_LIST_FILE = os.path.join(DATA_DIR, "urls.json")
GRAPH_FILE = os.path.join(DATA_DIR, "web_structure_graph.json")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Thiết lập Logging để tránh ghi ổ đĩa liên tục (Bảo vệ SSD)
# FileHandler sẽ nhận dữ liệu từ MemoryHandler
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "link_extract.log"), encoding='utf-8', mode='w')
# MemoryHandler lưu tạm trên RAM (tối đa 100,000 dòng) và chỉ ghi 1 lần xuống file khi kết thúc script
memory_handler = MemoryHandler(capacity=100000, flushLevel=logging.ERROR, target=file_handler)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        memory_handler,       # Ghi vào RAM, cuối cùng mới xả ra File
        logging.StreamHandler() # Ghi trực tiếp ra Màn hình Console để theo dõi real-time
    ]
)

# Cấu hình mạng chống chặn IP (Anti-ban / Rate-limit prevention)
session = requests.Session()
session.verify = False
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
]
session.headers.update({"User-Agent": random.choice(USER_AGENTS)})

retry_strategy = Retry(
    total=3, 
    backoff_factor=1.5, 
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
session.mount("http://", adapter)
session.mount("https://", adapter)

def random_sleep(min_s=0.3, max_s=1.2):
    """Nghỉ ngẫu nhiên để mô phỏng người dùng thật"""
    time.sleep(random.uniform(min_s, max_s))

# Bộ Regex chặn mạng xã hội
SOCIAL_MEDIA_PATTERN = re.compile(r'(facebook\.com|twitter\.com|x\.com|youtube\.com|youtu\.be|instagram\.com|tiktok\.com|zalo\.me|linkedin\.com)', re.IGNORECASE)

# Chặn các trang thừa, chỉ cho phép 3 trang chỉ định
ALLOWED_DOMAINS = ["camnang.iuh.edu.vn", "tuyensinh.iuh.edu.vn", "iuh.edu.vn"]

def clean_and_verify_url(url):
    """
    Sửa lỗi URL bị nối chuỗi (VD: https://domain/https://...)
    và kiểm tra xem URL có thuộc 3 domain cho phép không.
    """
    # 1. Sửa lỗi dính chuỗi 2 lần http (lấy phần http ở cuối cùng)
    if url.count("http") > 1:
        # Nếu có "/https://" hoặc "https://" bị nối
        parts = url.split("http")
        url = "http" + parts[-1]
        
    # 2. Xóa fragment
    url = url.split('#')[0]
    
    # 2.1 Sửa lỗi lặp path (VD: /vi/vi/, /en/en/) do urljoin nối nhầm link tương đối
    url = re.sub(r'(/vi)+/', '/vi/', url)
    url = re.sub(r'(/en)+/', '/en/', url)
    
    # 2.2 Sửa lỗi dính /p=0 sau .html
    if ".html/" in url:
        url = url.split(".html/")[0] + ".html"
        
    # 2.3 Chống lỗi dồn path (Stacked path) của iuh.edu.vn
    # Nếu /vi/ hoặc /en/ xuất hiện nhiều hơn 1 lần, đây chắc chắn là link lỗi do relative path sinh ra
    if url.count("/vi/") + url.count("/en/") > 1:
        return None
        
    # 2.4 Đồng bộ tên miền (Xóa www. để iuh.edu.vn và www.iuh.edu.vn gộp thành 1)
    if "://www." in url:
        url = url.replace("://www.", "://")
    
    # 3. Ép http thành https để không bị lệch chuẩn (tuyensinh.iuh.edu.vn)
    if url.startswith("http://"):
        url = url.replace("http://", "https://", 1)
        
    # 4. Kiểm tra xem domain có nằm trong danh sách cho phép không
    parsed = urlparse(url)
    netloc = parsed.netloc.replace("www.", "")
    if netloc not in ALLOWED_DOMAINS:
        return None
        
    # 4.5 Lọc các chuyên mục rác của iuh.edu.vn (Áp dụng toàn cục)
    if netloc == "iuh.edu.vn":
        iuh_blacklist = [
            "/hop-tac", "/tin-tuc-dao-tao", "/tin-tuc", "/tags", 
            "/guong-dien-hinh", "/nghien-cuu", "/su-kien", 
            "/thanh-tich-hoc-tap", "/ky-nang-mem", "/kham-pha-iuh", 
            "/hoat-dong-phong-trao", "/en/"
        ]
        if any(b in parsed.path.lower() for b in iuh_blacklist):
            return None
            
    # 4.6 Lọc chặt tuyensinh.iuh.edu.vn (Chỉ cho phép các trang tĩnh chỉ định)
    if netloc == "tuyensinh.iuh.edu.vn":
        tuyensinh_whitelist = [
            "/quyche", "/nganhdaotao", "/diemchuan", "/deants", 
            "/files_thongbao/thongbaotuyensinhlienthongdot12026.pdf"
        ]
        if not any(parsed.path.lower() == w for w in tuyensinh_whitelist):
            return None
            
    # 5. Kiểm tra mạng xã hội
    if SOCIAL_MEDIA_PATTERN.search(url):
        return None
        
    return url

def extract_urls_from_sitemap(sitemap_url):
    """Trích xuất danh sách URL từ sitemap.xml. Hỗ trợ fix lỗi URL nối chuỗi của camnang.iuh"""
    logging.info(f"Đang đọc sitemap: {sitemap_url}")
    try:
        response = session.get(sitemap_url, timeout=20)
        if response.status_code != 200:
            return []
            
        # Kiểm tra nếu trả về HTML thay vì XML
        if "html" in response.text[:100].lower():
            logging.warning(f"{sitemap_url} trả về HTML thay vì XML. Website này không có sitemap chuẩn.")
            return []
            
        urls = set()
        soup = BeautifulSoup(response.content, "xml")
        for loc in soup.find_all("loc"):
            url = loc.text.strip()
            clean_url = clean_and_verify_url(url)
            if clean_url:
                urls.add(clean_url)
            
        logging.info(f"Tìm thấy {len(urls)} links từ sitemap sau khi lọc.")
        return list(urls)
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
                
            # Sửa định dạng phân trang của IUH (Dùng /p= thay vì ?page=)
            page_url = f"{category_url}/p={page-1}" if page > 1 else category_url
            response = session.get(page_url, timeout=15)
            # Một số trang phân trang của CodeIgniter bị lỗi header 404 dù vẫn có HTML, nên ta nới lỏng điều kiện
            if response.status_code not in [200, 404]: 
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            found_new_links = False
            
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                if "/p=" in href: 
                    continue
                if href.endswith(".html"):
                    full_url = urljoin(category_url, href)
                    clean_url = clean_and_verify_url(full_url)
                    if clean_url and clean_url not in urls:
                        urls.add(clean_url)
                        found_new_links = True
            
            # Nếu trang này không có link mới nào, có nghĩa là đã lật đến trang trắng/trang cuối
            if not found_new_links:
                logging.info(f"Đã chạm đáy ở trang {page}, ngừng quét danh mục này.")
                break
                
            logging.info(f"Quét xong trang {page}, tổng link tạm thời: {len(urls)}")
            page += 1
            random_sleep()
                        
        logging.info(f"Hoàn thành quét danh mục. Tìm thấy {len(urls)} links.")
        return list(urls)
    except Exception as e:
        logging.error(f"Lỗi quét danh mục: {e}")
        return list(urls)

def extract_urls_from_bfs(start_url, max_depth=3):
    """
    Quét theo chiều rộng (BFS) để vét cạn các trang trên website.
    In ra log chi tiết để theo dõi quá trình.
    """
    logging.info(f"\n🚀 BẮT ĐẦU QUÉT BFS: {start_url} (Độ sâu tối đa: {max_depth})")
    visited = set()
    queue = [(start_url, 0)]
    
    # Những từ khóa bỏ qua (file rác hoặc trang không chứa tri thức)
    blacklist = ['video', 'gallery', '.pdf', '.doc', '.docx', '.png', '.jpg', '.zip', '.rar']
    
    collected_urls = set()

    while queue:
        current_url, depth = queue.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)
        
        logging.info(f"[BFS] 🔍 (Depth {depth}/{max_depth}) [Queue: {len(queue)}] Đang duyệt: {current_url}")
        
        try:
            response = session.get(current_url, timeout=15)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                if not href or href.startswith(('javascript:', 'mailto:', 'tel:')): 
                    continue
                
                # Sửa lỗi URL và kiểm tra domain
                full_url = urljoin(current_url, href)
                clean_url = clean_and_verify_url(full_url)
                if not clean_url:
                    continue
                    
                parsed = urlparse(clean_url)
                path = parsed.path.lower()
                
                if any(b in path for b in blacklist): 
                    continue
                
                # Nới lỏng: Cho phép .html, .php, hoặc các thư mục không có đuôi mở rộng
                has_valid_extension = path.endswith('.html') or path.endswith('.php') or "." not in path.split('/')[-1]
                
                # Bỏ qua kiểm tra đuôi mở rộng nếu là trang camnang (Vét cạn mọi ngóc ngách)
                if "camnang.iuh.edu.vn" in parsed.netloc:
                    has_valid_extension = True
                    
                if has_valid_extension:
                    if clean_url not in collected_urls:
                        collected_urls.add(clean_url)
                        logging.info(f"[BFS] 🔗 Phát hiện link mới: {clean_url}")
                        # Đẩy vào hàng đợi nếu chưa vượt quá độ sâu
                        if depth < max_depth:
                            queue.append((clean_url, depth + 1))
                            
        except Exception as e:
            logging.error(f"Lỗi quét BFS tại {current_url}: {e}")
            
        random_sleep(0.2, 0.6) # Đẩy nhanh tốc độ một chút

    logging.info(f"✅ Hoàn thành quét BFS cho {start_url}. Vét được {len(collected_urls)} links.")
    return list(collected_urls)

if __name__ == "__main__":
    logging.info("========== BƯỚC 0: TRÍCH XUẤT TOÀN BỘ URL (HYBRID APPROACH) ==========")
    all_urls = set()
    
    # 1. Lấy từ sitemap của camnang
    camnang_urls = extract_urls_from_sitemap("https://camnang.iuh.edu.vn/sitemap.xml")
    all_urls.update(camnang_urls)
    
    # 2. Lấy từ danh mục Thông Báo của iuh.edu.vn (Đã bỏ qua tin-tuc theo yêu cầu)
    iuh_thong_bao = extract_urls_from_category("https://iuh.edu.vn/vi/thong-bao.html", max_pages=10)
    all_urls.update(iuh_thong_bao)
    
    # 3. Lấy các trang Tĩnh, Cơ cấu tổ chức từ trang chủ iuh.edu.vn bằng BFS
    # Giảm độ sâu xuống 0 (Chỉ lấy link trực tiếp từ trang chủ)
    iuh_static = extract_urls_from_bfs("https://iuh.edu.vn/", max_depth=0)
    all_urls.update(iuh_static)
    
    # 4. Vét cạn camnang.iuh.edu.vn bằng BFS (Độ sâu 10 - Quét sâu nhất có thể)
    camnang_bfs = extract_urls_from_bfs("https://camnang.iuh.edu.vn/", max_depth=10)
    all_urls.update(camnang_bfs)
    
    # 5. Lấy các trang quan trọng từ tuyensinh.iuh.edu.vn (Hardcoded theo yêu cầu)
    tuyensinh_urls = [
        "https://tuyensinh.iuh.edu.vn/quyChe",
        "https://tuyensinh.iuh.edu.vn/nganhDaoTao",
        "https://tuyensinh.iuh.edu.vn/diemChuan",
        "https://tuyensinh.iuh.edu.vn/deAnTS",
        # "https://tuyensinh.iuh.edu.vn/Files_thongBao/thongbaotuyensinhlienthongdot12026.pdf"
    ]
    all_urls.update(tuyensinh_urls)
    
    target_urls = list(all_urls)
    
    # 4. Nhóm URL theo Domain để tạo đồ thị (web_structure_graph.json)
    graph_data = {}
    for url in target_urls:
        domain_key = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
        if domain_key not in graph_data:
            graph_data[domain_key] = []
        graph_data[domain_key].append(url)
        
    with open(GRAPH_FILE, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=4, ensure_ascii=False)
    logging.info(f"Đã lưu sơ đồ cấu trúc web (Domain Grouped) vào {GRAPH_FILE}")
    
    logging.info(f"Tổng hợp được {len(target_urls)} URLs. Tiến hành lưu vào {URL_LIST_FILE}")
    
    with open(URL_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(target_urls, f, indent=4, ensure_ascii=False)
        
    # Ép xả toàn bộ log từ RAM xuống ổ cứng 1 lần duy nhất trước khi tắt
    logging.shutdown()
