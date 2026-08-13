import os
import re
import json
import hashlib
import requests
import trafilatura
import time
import threading
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import urllib3
from urllib.parse import urljoin
from data_pipeline.utils.logger import setup_logger
from data_pipeline.crawlers.pdf_extractor import PDFExtractor

from dotenv import load_dotenv

load_dotenv()

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

    def _extract_published_date(self, soup):
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
        
        breadcrumbs = ""
        bc_node = soup.find('ol')
        if bc_node:
            breadcrumbs = " > ".join([t.strip() for t in bc_node.stripped_strings if t.strip() not in ['>', '/', '»', '|']])
            
        published_date = self._extract_published_date(soup)
        
        for span in soup.find_all('span'):
            if span.string and "Chia sẻ:" in span.string:
                parent_div = span.find_parent('div', class_=re.compile(r'border-t|justify-between|flex'))
                if parent_div:
                    parent_div.decompose()
                    
        pdf_text = ""
        processed_pdfs = set()
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith('.pdf'):
                full_pdf_url = urljoin(url, href)
                if full_pdf_url not in processed_pdfs:
                    processed_pdfs.add(full_pdf_url)
                    extracted = self.pdf_extractor.extract_text(full_pdf_url)
                    if extracted:
                        pdf_text += f"\n\n--- NỘI DUNG FILE PDF ({href.split('/')[-1]}) ---\n{extracted}\n"
        
        for obj in soup.find_all('object', data=True):
            data_url = obj['data']
            if data_url.lower().endswith('.pdf'):
                full_pdf_url = urljoin(url, data_url)
                if full_pdf_url not in processed_pdfs:
                    processed_pdfs.add(full_pdf_url)
                    extracted = self.pdf_extractor.extract_text(full_pdf_url)
                    if extracted:
                        pdf_text += f"\n\n--- NỘI DUNG FILE PDF ({data_url.split('/')[-1]}) ---\n{extracted}\n"
                        
        # Dọn dẹp các rác hiển thị: lượt xem, nút tải file, câu thông báo (Thực hiện sau khi đã trích xuất PDF xong)
        for div in soup.find_all('div', class_=re.compile(r'pdf-download|viewpdf', re.I)):
            div.decompose()

        for pattern in [r'\d+\s*lượt xem', r'Tải file thiết kế', r'Download file', r'Vui lòng xem file pdf']:
            for node in soup.find_all(string=re.compile(pattern, re.I)):
                parent = node.parent
                if parent: parent.decompose()
                    
        # IUH developers hijacked 'pbmit-author-box' (author bio) to write Important Notes.
        # Create standard <p> tags so Trafilatura doesn't drop anything.
        for box in soup.find_all(class_=re.compile(r'pbmit-author-box|author-box', re.I)):
            container = soup.new_tag('div')
            text_parts = box.get_text(separator='\n').split('\n')
            for part in text_parts:
                if part.strip():
                    p = soup.new_tag('p')
                    p.string = part.strip()
                    container.append(p)
            box.replace_with(container)
            
        article_node = soup.find(class_=re.compile(r'iuhArticleContent|page-content', re.I)) or soup.find('main')
        if not article_node:
            article_node = soup.find('article')
            
        if article_node:
            html_to_parse = f"<html><body>{str(article_node)}</body></html>"
            clean_md = trafilatura.extract(html_to_parse, include_links=True, output_format="markdown")
        else:
            # Chỉ loại bỏ các thẻ HTML phân định bố cục (semantic tags)
            for tag in soup.find_all(['header', 'footer', 'nav', 'aside']):
                tag.decompose()
                
            # Cẩn thận loại bỏ các div có class CHÍNH XÁC là menu/footer/sidebar (tránh xóa nhầm "card-footer" hay "nav-tab" trong bài viết)
            exact_bad_classes = {'footer', 'header', 'menu', 'sidebar', 'widget-area', 'site-footer', 'site-header'}
            for tag in soup.find_all('div'):
                classes = set(tag.get('class', []))
                if exact_bad_classes.intersection(classes):
                    tag.decompose()
                    
            clean_md = trafilatura.extract(str(soup), include_links=True, output_format="markdown")
            
        if not clean_md:
            clean_md = ""
            
        # Fallback thủ công nếu Trafilatura bỏ qua nội dung (thường gặp ở các trang danh bạ, trang không có đoạn văn dài)
        if not clean_md and article_node:
            fallback_node = BeautifulSoup(str(article_node), "html.parser")
            for tag in fallback_node.find_all(['header', 'footer', 'nav']):
                tag.decompose()
            for a in fallback_node.find_all('a', href=True):
                href = a['href']
                text = a.get_text(strip=True)
                if text:
                    a.replace_with(f"[{text}]({href})")
            clean_md = fallback_node.get_text(separator='\n', strip=True)
            
        if pdf_text:
            clean_md += pdf_text
            
        clean_md = clean_md.strip()
            
        if not clean_md:
            logger.warning(f"Không trích xuất được nội dung (cả HTML và PDF đều rỗng): {url}")
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
        
        if old_hash is None:
            logger.info(f"[THÊM MỚI]: {url}")
        else:
            logger.info(f"[CẬP NHẬT]: Đã sửa đổi - {url}")
            
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url.replace('https://', '').replace('http://', ''))
        safe_name = safe_name[:40] + "_" + url_hash[:6]
        md_filepath = os.path.join(self.output_dir, f"{safe_name}.md")
        
        front_matter = f"---\n"
        front_matter += f"source_url: {json.dumps(result['url'], ensure_ascii=False)}\n"
        front_matter += f"title: {json.dumps(result['title'], ensure_ascii=False)}\n"
        front_matter += f"published_date: {json.dumps(result['published_date'], ensure_ascii=False)}\n"
        front_matter += f"breadcrumbs: {json.dumps(result['breadcrumbs'], ensure_ascii=False)}\n"
        front_matter += f"---\n\n"
        
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(front_matter + result['content'])
            
        with self.state_lock:
            self.db_state[url] = new_hash
            
        return True

    def run_crawl(self, urls):
        logger.info(f"========== CÀO {len(urls)} URLs BẰNG ĐA LUỒNG ==========")
        success_count = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self._process_url_worker, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    changed = future.result()
                    if changed: success_count += 1
                except Exception as exc:
                    logger.error(f"{url} sinh ra ngoại lệ: {exc}")

        self._save_state()
        logger.info(f"Hoàn tất crawl. Đã xử lý {len(urls)} links, {success_count} có cập nhật/thêm mới!")
