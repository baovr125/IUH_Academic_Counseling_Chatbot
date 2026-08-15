import os
import re
import json
import hashlib
import requests
import time
import threading
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
from data_pipeline.utils.logger import setup_logger
from data_pipeline.crawlers.pdf_extractor import PDFExtractor
from data_pipeline.crawlers.html_utils import (
    extract_published_date, clean_html_boilerplate, extract_markdown, get_pdf_links
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = setup_logger("content_crawler", "crawl.log")

class ContentCrawler:
    def __init__(self, output_dir, max_workers=5):
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.state_db_file = os.path.join(output_dir, "mock_supabase_state.json")
        self.state_lock = threading.Lock()
        self.pdf_extractor = PDFExtractor(output_dir)
        
        os.makedirs(output_dir, exist_ok=True)
        self.db_state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_db_file):
            with open(self.state_db_file, 'r') as f: return json.load(f)
        return {}

    def _save_state(self):
        with self.state_lock:
            with open(self.state_db_file, 'w') as f: json.dump(self.db_state, f, indent=4)

    def scrape_page(self, url):
        try:
            response = requests.get(url, verify=False, timeout=10)
            if response.status_code != 200:
                logger.error(f"Lỗi truy cập {url} (Code: {response.status_code})")
                return None
        except Exception as e:
            logger.error(f"Lỗi kết nối {url}: {e}")
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
        
        bc_node = soup.find('ol')
        breadcrumbs = " > ".join([t.strip() for t in bc_node.stripped_strings if t.strip() not in ['>', '/', '»', '|']]) if bc_node else ""
        published_date = extract_published_date(soup)
        
        pdf_urls = get_pdf_links(soup, url)
        clean_html_boilerplate(soup)
        clean_md = extract_markdown(soup)
            
        for pdf_url in pdf_urls:
            extracted = self.pdf_extractor.extract_text(pdf_url)
            if extracted:
                clean_md += f"\n\n--- NỘI DUNG FILE PDF ({pdf_url.split('/')[-1]}) ---\n{extracted}\n"
                
        clean_md = clean_md.strip()
        if not clean_md:
            logger.warning(f"Không trích xuất được nội dung (cả HTML và PDF đều rỗng): {url}")
            return None
            
        return {
            "url": url,
            "title": title,
            "breadcrumbs": breadcrumbs,
            "published_date": published_date,
            "hash": hashlib.md5(clean_md.encode('utf-8')).hexdigest(),
            "content": clean_md
        }

    def _process_url_worker(self, url):
        time.sleep(0.5)
        with self.state_lock:
            old_hash = self.db_state.get(url)
        
        result = self.scrape_page(url)
        if not result: return False
        
        new_hash = result['hash']
        if old_hash == new_hash:
            logger.info(f"[BỎ QUA]: Không thay đổi - {url}")
            return False
        
        logger.info(f"[THÊM MỚI]: {url}" if old_hash is None else f"[CẬP NHẬT]: Đã sửa đổi - {url}")
            
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url.replace('https://', '').replace('http://', ''))[:40] + "_" + hashlib.md5(url.encode('utf-8')).hexdigest()[:6]
        md_filepath = os.path.join(self.output_dir, f"{safe_name}.md")
        
        front_matter = (
            f"---\n"
            f"source_url: {json.dumps(result['url'], ensure_ascii=False)}\n"
            f"title: {json.dumps(result['title'], ensure_ascii=False)}\n"
            f"published_date: {json.dumps(result['published_date'], ensure_ascii=False)}\n"
            f"breadcrumbs: {json.dumps(result['breadcrumbs'], ensure_ascii=False)}\n"
            f"---\n\n"
        )
        
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(front_matter + result['content'])
            
        if "LỖI API GOOGLE" in result['content']:
            logger.warning(f"URL {url} bị lỗi OCR do API sập. Đã lưu file tạm nhưng không cập nhật Hash.")
        else:
            with self.state_lock:
                self.db_state[url] = new_hash
                
        return True

    def run_crawl(self, urls):
        logger.info(f"========== CÀO {len(urls)} URLs BẰNG ĐA LUỒNG ==========")
        success_count = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self._process_url_worker, url): url for url in urls}
            for future in as_completed(future_to_url):
                try:
                    if future.result(): success_count += 1
                except Exception as exc:
                    logger.error(f"Ngoại lệ: {exc}")

        self._save_state()
        logger.info(f"Hoàn tất crawl. Đã xử lý {len(urls)} links, {success_count} có cập nhật/thêm mới!")
