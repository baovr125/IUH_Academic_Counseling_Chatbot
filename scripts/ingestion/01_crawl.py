import os
import re
import json
import hashlib
import requests
import trafilatura
import logging
import time
import threading
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Xử lý đường dẫn tuyệt đối (Absolute Paths)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")
URL_LIST_FILE = os.path.join(DATA_DIR, "urls.json")
MARKDOWN_DIR = os.path.join(DATA_DIR, "crawled_markdown")
STATE_DB_FILE = os.path.join(MARKDOWN_DIR, "mock_supabase_state.json")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(MARKDOWN_DIR, exist_ok=True)

# Thiết lập Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "crawl.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

state_lock = threading.Lock()

def extract_published_date(soup):
    time_tag = soup.find('time')
    if time_tag and time_tag.get('datetime'):
        return time_tag['datetime']
    
    date_pattern = re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})')
    for tag in soup.find_all(['span', 'div', 'p', 'li', 'td', 'time']): 
        text = tag.get_text(strip=True)
        if "đăng" in text.lower() or "ngày" in text.lower() or re.search(r'^\d{1,2}[/-]\d{1,2}[/-]\d{4}', text):
            match = date_pattern.search(text)
            if match:
                date_str = match.group(1)
                try:
                    parsed_date = datetime.strptime(date_str.replace('-', '/'), "%d/%m/%Y")
                    return parsed_date.isoformat()
                except:
                    return date_str
    
    return datetime.now().isoformat()

def scrape_page(url):
    try:
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code != 200:
            logging.error(f"Lỗi truy cập {url} (Code: {response.status_code})")
            return None
    except Exception as e:
        logging.error(f"Lỗi kết nối {url}: {e}")
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    title = soup.title.string if soup.title else "No Title"
    title = title.strip()
    
    breadcrumbs = ""
    bc_node = soup.find('ol')
    if bc_node:
        breadcrumbs = " > ".join([t.strip() for t in bc_node.stripped_strings if t.strip() not in ['>', '/', '»', '|']])
        
    published_date = extract_published_date(soup)
        
    article_node = soup.find(class_='iuhArticleContent')
    if not article_node:
        article_node = soup.find('article')
        
    if article_node:
        html_to_parse = f"<html><body>{str(article_node)}</body></html>"
        clean_md = trafilatura.extract(html_to_parse, include_links=True, output_format="markdown")
    else:
        bad_classes = re.compile(r'menu|sidebar|breadcrumb|footer|nav|widget|pagination', re.I)
        for tag in soup.find_all(class_=bad_classes): 
            tag.decompose()
        clean_md = trafilatura.extract(str(soup), include_links=True, output_format="markdown")
        
    if not clean_md:
        logging.warning(f"Không trích xuất được nội dung: {url}")
        return None
        
    content_hash = hashlib.md5(clean_md.encode('utf-8')).hexdigest()
    
    return {
        "url": url,
        "title": title,
        "breadcrumbs": breadcrumbs,
        "published_date": published_date,
        "hash": content_hash,
        "content": clean_md
    }

def load_state():
    if os.path.exists(STATE_DB_FILE):
        with open(STATE_DB_FILE, 'r') as f: return json.load(f)
    return {}

def save_state(state):
    with state_lock:
        with open(STATE_DB_FILE, 'w') as f: json.dump(state, f, indent=4)
        
def process_url_worker(url, db_state):
    """Worker function để xử lý 1 URL trong ThreadPool"""
    time.sleep(0.5) # Chống rate limit
    
    with state_lock:
        old_hash = db_state.get(url)
    
    result = scrape_page(url)
    if not result: return False
    
    new_hash = result['hash']
    
    if old_hash == new_hash:
        logging.info(f"[BỎ QUA]: Không thay đổi - {url}")
        return False
    
    if old_hash is None:
        logging.info(f"[THÊM MỚI]: {url}")
    else:
        logging.info(f"[CẬP NHẬT]: Đã sửa đổi - {url}")
        
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url.replace('https://', '').replace('http://', ''))
    safe_name = safe_name[:40] + "_" + new_hash[:6]
    md_filepath = os.path.join(MARKDOWN_DIR, f"{safe_name}.md")
    
    front_matter = f"---\n"
    front_matter += f"source_url: '{result['url']}'\n"
    front_matter += f"title: '{result['title']}'\n"
    front_matter += f"published_date: '{result['published_date']}'\n"
    front_matter += f"breadcrumbs: '{result['breadcrumbs']}'\n"
    front_matter += f"---\n\n"
    
    with open(md_filepath, "w", encoding="utf-8") as f:
        f.write(front_matter + result['content'])
        
    with state_lock:
        db_state[url] = new_hash
        
    return True

if __name__ == "__main__":
    if not os.path.exists(URL_LIST_FILE):
        logging.error(f"Không tìm thấy file {URL_LIST_FILE}. Vui lòng chạy 00_link_extract.py trước!")
        exit(1)
        
    with open(URL_LIST_FILE, 'r', encoding='utf-8') as f:
        urls_to_crawl = json.load(f)
        
    logging.info(f"========== BƯỚC 1: CÀO {len(urls_to_crawl)} URLs BẰNG ĐA LUỒNG ==========")
    
    db_state = load_state()
    
    # Chỉ chạy 20 URL đầu để test, bỏ [:20] để chạy toàn bộ
    test_urls = urls_to_crawl[:20] 
    
    success_count = 0
    # Sử dụng ThreadPoolExecutor với 5 workers
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(process_url_worker, url, db_state): url for url in test_urls}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                changed = future.result()
                if changed: success_count += 1
            except Exception as exc:
                logging.error(f"{url} sinh ra ngoại lệ: {exc}")

    # Ghi file state một lần duy nhất vào cuối vòng lặp
    save_state(db_state)
    
    logging.info(f"Hoàn tất quá trình crawl dữ liệu. Đã xử lý {len(test_urls)} links, trong đó {success_count} links có cập nhật/thêm mới!")
