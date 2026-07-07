import os
import re
import json
import hashlib
import urllib3
import requests
import trafilatura
from urllib.parse import urljoin, urlparse
from datetime import datetime
from bs4 import BeautifulSoup

# =====================================================================
# 1. CẤU HÌNH THƯ MỤC TEST VÀ HỆ THỐNG
# =====================================================================

START_URLS = ["https://camnang.iuh.edu.vn/"] # Chạy thử 1 link gốc cho nhanh

# Đổi sang thư mục test để không ảnh hưởng dữ liệu thật
WORK_DIR = r"G:\Khoa_Luan\Source_code\data\markdown_test"
MD_UPDATES_DIR = os.path.join(WORK_DIR, "markdown_updates")
GRAPH_FILE = os.path.join(WORK_DIR, "test_web_structure.json")

os.makedirs(MD_UPDATES_DIR, exist_ok=True)

# Giới hạn số trang cào để test nhanh
MAX_TEST_PAGES = 5  

ALLOWED_DOMAINS = {urlparse(url).netloc.lower().replace("www.", "") for url in START_URLS}
GLOBAL_BLACK_LIST = ["video.php", "/gallery/", "youtube.com", "facebook.com", "zalo.me", "tin-tuc"]

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
session = requests.Session()
session.verify = False
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
session.headers.update(headers)

# =====================================================================
# 2. CÁC HÀM UTILITY VÀ BÓC TÁCH
# =====================================================================

def get_valid_filename(url):
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.strip('/')
    filename = re.sub(r'[\@\.\/\=\?\&]', '-', path)
    if not filename or filename.endswith("-"): filename = f"{domain}_index"
    return f"{filename}.md"

def should_crawl_url(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        path_query = (parsed.path + "?" + parsed.query if parsed.query else parsed.path).lower()
        
        if len(path_query) > 200 or domain not in ALLOWED_DOMAINS: return False
        if any(black in path_query for black in GLOBAL_BLACK_LIST): return False
        return True
    except:
        return False

def scrape_and_convert_to_markdown(url, html_text):
    try:
        page_title = "No Title"
        title_match = re.search(r'<title>(.*?)</title>', html_text, re.IGNORECASE)
        if title_match: page_title = title_match.group(1).strip()

        soup = BeautifulSoup(html_text, "html.parser")
        
        # 🟢 Trích xuất Breadcrumb
        breadcrumbs_text = ""
        breadcrumb_node = soup.find(class_=re.compile(r'breadcrumb|nav-path|pathway', re.I)) or \
                          soup.find(id=re.compile(r'breadcrumb|pathway', re.I))
        if breadcrumb_node:
            breadcrumbs_text = " > ".join(
                [text.strip() for text in breadcrumb_node.stripped_strings if text.strip() not in ['>', '/', '»', '|']]
            )

        # 🟡 Tiền xử lý & dọn dẹp HTML
        bad_classes = re.compile(r'menu|sidebar|breadcrumb|footer|nav|related|widget|pagination|popular|post-nav', re.I)
        for tag in soup.find_all(class_=bad_classes): tag.decompose()
        for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'noscript', 'img', 'svg']):
            tag.decompose()
            
        clean_html_text = str(soup)

        # 🟢 Bóc tách Markdown
        extracted_md = trafilatura.extract(
            clean_html_text, include_links=True, include_formatting=True, output_format="markdown", target_language="vi", favor_precision=True
        )

        if not extracted_md or len(extracted_md) < 50: return None, None

        # 🟢 Nhúng Front Matter
        front_matter = f"---\nsource_url: \"{url}\"\ntitle: \"{page_title}\"\nbreadcrumbs: \"{breadcrumbs_text}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
        return front_matter + extracted_md, page_title
        
    except Exception as e:
        print(f"Lỗi parse HTML: {e}")
        return None, None

# =====================================================================
# 3. LUỒNG CHẠY TEST (KHÔNG MULTI-THREAD ĐỂ DỄ THEO DÕI LOG)
# =====================================================================

def run_test_crawler():
    print("="*60)
    print(f"🚀 KHỞI ĐỘNG TEST CRAWLER (Giới hạn: {MAX_TEST_PAGES} trang)")
    print(f"📂 Thư mục xuất file: {MD_UPDATES_DIR}")
    print("="*60)
    
    links_to_crawl = list(START_URLS)
    visited_links = set()
    graph_data = {}
    pages_saved = 0
    
    while links_to_crawl and pages_saved < MAX_TEST_PAGES:
        current_url = links_to_crawl.pop(0)
        if current_url in visited_links:
            continue
            
        visited_links.add(current_url)
        print(f"\n[{pages_saved + 1}/{MAX_TEST_PAGES}] Đang tải: {current_url}")
        
        try:
            response = session.get(current_url, timeout=10)
            if response.status_code != 200 or not response.headers.get('content-type', '').startswith('text/html'):
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Tìm link mới
            new_links = []
            for a_tag in soup.find_all("a", href=True):
                new_url = urljoin(current_url, a_tag["href"]).split("#")[0].split("?")[0].rstrip('/')
                if should_crawl_url(new_url) and new_url not in visited_links:
                    new_links.append(new_url)
                    links_to_crawl.append(new_url)
            
            if new_links:
                graph_data[current_url] = list(set(new_links))

            # Bóc tách và Lưu file
            markdown_content, title = scrape_and_convert_to_markdown(current_url, response.text)
            
            if markdown_content:
                filename = get_valid_filename(current_url)
                output_path = os.path.join(MD_UPDATES_DIR, filename)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                
                print(f"✅ Đã lưu thành công: {filename}")
                print(f"   -> Tiêu đề: {title}")
                pages_saved += 1
                
        except Exception as e:
            print(f"❌ Lỗi khi xử lý {current_url}: {e}")

    # Lưu file Graph thử nghiệm
    with open(GRAPH_FILE, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=4, ensure_ascii=False)
        
    print("\n" + "="*60)
    print(f"🏁 ĐÃ HOÀN THÀNH BÀI TEST!")
    print(f"📁 Kiểm tra các file .md tại: {MD_UPDATES_DIR}")
    print(f"🌲 Kiểm tra sơ đồ web tại: {GRAPH_FILE}")
    print("="*60)

if __name__ == "__main__":
    run_test_crawler()