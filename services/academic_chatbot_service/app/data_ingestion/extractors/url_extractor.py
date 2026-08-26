import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from app.data_ingestion.utils.logger import setup_logger
from app.data_ingestion.utils.url_helpers import clean_and_verify_url

logger = setup_logger("url_extractor", "link_extract.log")

class URLExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        })

    def _random_sleep(self, min_sec=0.5, max_sec=2.0):
        time.sleep(random.uniform(min_sec, max_sec))

    def extract_from_sitemap(self, sitemap_url):
        logger.info(f"Đang đọc sitemap: {sitemap_url}")
        try:
            response = self.session.get(sitemap_url, timeout=20)
            if response.status_code != 200:
                return []
                
            if "html" in response.text[:100].lower():
                logger.warning(f"{sitemap_url} trả về HTML thay vì XML.")
                return []
                
            urls = set()
            # Handle environment where xml parser might be missing
            try:
                soup = BeautifulSoup(response.content, "xml")
            except Exception:
                soup = BeautifulSoup(response.content, "html.parser")
                
            for loc in soup.find_all("loc"):
                url = loc.text.strip()
                clean_url = clean_and_verify_url(url)
                if clean_url:
                    urls.add(clean_url)
                
            logger.info(f"Tìm thấy {len(urls)} links từ sitemap sau khi lọc.")
            return list(urls)
        except Exception as e:
            logger.error(f"Lỗi đọc sitemap: {e}")
            return []

    def extract_from_category(self, category_url, max_pages=None):
        logger.info(f"Đang quét danh mục: {category_url}")
        urls = set()
        page = 1
        
        try:
            while True:
                if max_pages and page > max_pages:
                    break
                    
                page_url = f"{category_url}/p={page-1}" if page > 1 else category_url
                response = self.session.get(page_url, timeout=15)
                
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
                
                if not found_new_links:
                    logger.info(f"Đã chạm đáy ở trang {page}, ngừng quét danh mục này.")
                    break
                    
                logger.info(f"Quét xong trang {page}, tổng link tạm thời: {len(urls)}")
                page += 1
                self._random_sleep()
                            
            logger.info(f"Hoàn thành quét danh mục. Tìm thấy {len(urls)} links.")
            return list(urls)
        except Exception as e:
            logger.error(f"Lỗi quét danh mục: {e}")
            return list(urls)

    def extract_from_bfs(self, start_url, max_depth=3):
        logger.info(f"\n🚀 BẮT ĐẦU QUÉT BFS: {start_url} (Độ sâu: {max_depth})")
        visited = set()
        queue = [(start_url, 0)]
        blacklist = ['video', 'gallery', '.pdf', '.doc', '.docx', '.png', '.jpg', '.zip', '.rar']
        collected_urls = set()

        while queue:
            current_url, depth = queue.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)
            
            logger.info(f"[BFS] 🔍 (Depth {depth}/{max_depth}) [Queue: {len(queue)}] Đang duyệt: {current_url}")
            
            try:
                response = self.session.get(current_url, timeout=15)
                if response.status_code != 200: continue
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    if not href or href.startswith(('javascript:', 'mailto:', 'tel:')): 
                        continue
                    
                    full_url = urljoin(current_url, href)
                    clean_url = clean_and_verify_url(full_url)
                    if not clean_url:
                        continue
                        
                    parsed = urlparse(clean_url)
                    path = parsed.path.lower()
                    
                    if any(b in path for b in blacklist): 
                        continue
                    
                    has_valid_extension = path.endswith('.html') or path.endswith('.php') or "." not in path.split('/')[-1]
                    
                    if "camnang.iuh.edu.vn" in parsed.netloc:
                        has_valid_extension = True
                        
                    if has_valid_extension:
                        if clean_url not in collected_urls:
                            collected_urls.add(clean_url)
                            logger.info(f"[BFS] 🔗 Phát hiện link mới: {clean_url}")
                            if depth < max_depth:
                                queue.append((clean_url, depth + 1))
                                
            except Exception as e:
                logger.error(f"Lỗi quét BFS tại {current_url}: {e}")
                
            self._random_sleep(0.2, 0.6)

        logger.info(f"✅ Hoàn thành quét BFS cho {start_url}. Vét được {len(collected_urls)} links.")
        return list(collected_urls)
