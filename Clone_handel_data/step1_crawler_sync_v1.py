import os
import re
import json
import hashlib
from sympy import false
import urllib3
import threading
import requests
import trafilatura
import concurrent.futures
from urllib.parse import urljoin, urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm.auto import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 🟢 Khởi tạo Docling cho việc bóc tách PDF có OCR Tiếng Việt
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions

# 🟢 IMPORT hàm chunking từ file step2_chunk_embed của bạn
from step2_chunk_embed_v1 import process_single_markdown

# =====================================================================
# 1. CẤU HÌNH THƯ MỤC VÀ HỆ THỐNG
# =====================================================================

START_URLS = [
    "https://camnang.iuh.edu.vn/",
    "https://iuh.edu.vn/"
]

WORK_DIR = r"G:\Khoa_Luan\Source_code\data\markdown_craw5"
STATE_FILE = os.path.join(WORK_DIR, "website_state.json")
MD_UPDATES_DIR = os.path.join(WORK_DIR, "markdown_updates")

os.makedirs(MD_UPDATES_DIR, exist_ok=True)

# Bộ lọc nâng cao
ALLOWED_DOMAINS = {urlparse(url).netloc.lower().replace("www.", "") for url in START_URLS}
GLOBAL_BLACK_LIST = ["video.php", "/gallery/", "youtube.com", "facebook.com", "zalo.me", "guong-dien-hinh", "tin-tuc"]
IUH_SPECIFIC_ALLOW_LIST = [
    "/thong-bao", "so-do-bo-may-to-chuc", "/phong-", "/khoa-", "/vien-",
    "/trung-tam-", "/phan-hieu-", "/co-so-", "ban-giam-hieu", "dang-uy"
]

# Tắt cảnh báo SSL & Cấu hình mạng bền bỉ
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
session = requests.Session()
session.verify = False
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
session.headers.update(headers)
retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Cấu hình Pipeline để bật OCR tiếng Việt cho PDF
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True # Chỉ bật OCR khi cần thiết (nếu PDF có text layer thì không cần OCR) 
pipeline_options.ocr_options = EasyOcrOptions(lang=["vi"])
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)

# Lock dùng cho đa luồng khi ghi file trạng thái
state_lock = threading.Lock()

# =====================================================================
# 2. CÁC HÀM XỬ LÝ URL, FILE VÀ TRẠNG THÁI
# =====================================================================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state):
    with state_lock:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4)

def get_valid_filename(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        path = parsed.path.strip('/')
        filename = re.sub(r'[\@\.\/\=\?\&]', '-', path)
        if not filename or filename.endswith("-"): filename = f"{domain}_index"
        return f"{filename}.md"
    except:
        return f"unknown_{datetime.now().timestamp()}.md"

def should_crawl_url(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        path_query = (parsed.path + "?" + parsed.query if parsed.query else parsed.path).lower()
        
        # [CẦU CHÌ] Chống Spider Trap
        if len(path_query) > 200 or path_query.count("/vi/") > 2: return False
        if domain not in ALLOWED_DOMAINS: return False
        if any(black in path_query for black in GLOBAL_BLACK_LIST): return False
        
        if domain == "iuh.edu.vn":
            if not any(allow_path.lower() in path_query for allow_path in IUH_SPECIFIC_ALLOW_LIST): 
                return False
        return True
    except:
        return False

# =====================================================================
# 3. CÁC HÀM BÓC TÁCH (PDF & HTML)
# =====================================================================

def download_and_convert_pdf(pdf_url, output_dir, state):
    """Tải và convert PDF nếu có thay đổi trên server"""
    try:
        pdf_dir = os.path.join(output_dir, "downloaded_pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = os.path.basename(urlparse(pdf_url).path)
        if not filename.lower().endswith('.pdf'): filename += '.pdf'
        pdf_filepath = os.path.join(pdf_dir, filename)
        md_filepath = os.path.join(output_dir, f"pdf_{filename.replace('.pdf', '.md')}")
        
        # --- KIỂM TRA PHIÊN BẢN PDF TRÊN SERVER ---
        head_resp = session.head(pdf_url, timeout=10)
        last_modified = head_resp.headers.get('Last-Modified', '')
        content_length = head_resp.headers.get('Content-Length', '')
        pdf_version_hash = f"{last_modified}_{content_length}" if (last_modified or content_length) else pdf_url

        with state_lock:
            old_hash = state.get(pdf_url)
            
        if old_hash == pdf_version_hash and os.path.exists(md_filepath):
            return md_filepath # File không đổi, trả về path cũ
                
        # --- TẢI VÀ BÓC TÁCH PDF MỚI/CẬP NHẬT ---
        response = session.get(pdf_url, stream=True, timeout=15)
        if response.status_code == 200:
            with open(pdf_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
        
        if os.path.exists(pdf_filepath):
            result = converter.convert(pdf_filepath)
            md_content = result.document.export_to_markdown()
            front_matter = f"---\nsource_url: \"{pdf_url}\"\ntitle: \"[PDF Extracted] {filename}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
            
            with open(md_filepath, "w", encoding="utf-8") as f:
                f.write(front_matter + md_content)
            
            # Đồng bộ sang JSON
            process_single_markdown(md_filepath)
            
            with state_lock:
                state[pdf_url] = pdf_version_hash
                
        return md_filepath
    except Exception as e:
        return None

def scrape_and_convert_to_markdown(url, html_text, output_dir, state):
    """Quét HTML, tìm PDF, dọn rác và dùng trafilatura bóc tách"""
    try:
        page_title = "No Title"
        title_match = re.search(r'<title>(.*?)</title>', html_text, re.IGNORECASE)
        if title_match: page_title = title_match.group(1).strip()

        soup = BeautifulSoup(html_text, "html.parser")
        
        # 🟢 TÌM VÀ TẢI PDF TRƯỚC KHI DỌN DẸP HTML
        pdf_urls_to_download = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            text = a_tag.get_text(strip=True).lower()
            if href.lower().split('?')[0].endswith('.pdf') or "download" in text or "tải về" in text:
                pdf_urls_to_download.add(urljoin(url, href).split("#")[0])

        for iframe in soup.find_all("iframe", src=True):
            src = iframe["src"].strip()
            if ".pdf" in src.lower():
                if "url=" in src:
                    import urllib.parse
                    actual_pdf_url = re.search(r'url=([^&]+)', src)
                    if actual_pdf_url: pdf_urls_to_download.add(urllib.parse.unquote(actual_pdf_url.group(1)))
                else:
                    pdf_urls_to_download.add(urljoin(url, src).split("#")[0])

        pdf_markdown_links = []
        for pdf_url in pdf_urls_to_download:
            md_path = download_and_convert_pdf(pdf_url, output_dir, state)
            if md_path: pdf_markdown_links.append(f"- [Đã tải PDF đính kèm]({pdf_url})")

        # 🟡 TIỀN XỬ LÝ HTML BẰNG BEAUTIFULSOUP
        for tag in soup.find_all('div'):
            text_content = tag.get_text(strip=True)
            if text_content.startswith("Lưu ý:") or "Chậm nhất một tháng sau" in text_content:
                tag.name = 'blockquote'
        
        bad_classes = re.compile(r'menu|sidebar|breadcrumb|footer|nav|related|widget|pagination|popular|post-nav|post-relate', re.I)
        for tag in soup.find_all(class_=bad_classes): tag.decompose()
            
        for text_to_remove in ['Bài phổ biến nhất', 'Bài viết liên quan', 'BÀI TRƯỚC', 'XEM TIẾP']:
            elements = soup.find_all(lambda tag: tag.name in ['h2', 'h3', 'h4', 'a', 'span', 'div'] and text_to_remove in tag.get_text(strip=True))
            for el in elements:
                parent_div = el.find_parent('div')
                if parent_div: parent_div.decompose()
                else: el.decompose()

        for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'noscript', 'img', 'svg']):
            tag.decompose()
            
        clean_html_text = str(soup)

        # 🟢 BÓC TÁCH CHÍNH BẰNG TRAFILATURA
        extracted_md = trafilatura.extract(
            clean_html_text, include_links=True, include_formatting=True, output_format="markdown", target_language="vi", favor_precision=True
        )

        if not extracted_md or len(extracted_md) < 50: extracted_md = ""

        if pdf_markdown_links:
            pdf_section = "\n\n### 📎 File đính kèm trong bài viết:\n" + "\n".join(pdf_markdown_links) + "\n\n---\n\n"
            clean_md = pdf_section + extracted_md
        else:
            clean_md = extracted_md

        clean_md = re.sub(r'\n{3,}', '\n\n', clean_md).strip()
        if not clean_md: return None, None

        front_matter = f"---\nsource_url: \"{url}\"\ntitle: \"{page_title}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
        return front_matter + clean_md, page_title
        
    except Exception as e:
        return None, None

# =====================================================================
# 4. LUỒNG ĐIỀU HƯỚNG CRAWLER ĐA LUỒNG & SYNC
# =====================================================================

def process_single_url_sync(current_url, state):
    """Hàm xử lý 1 URL: Tải, kiểm tra hash, lưu file và trả về link mới"""
    new_links = []
    is_updated = False
    
    try:
        response = session.get(current_url, timeout=10)
        if response.status_code != 200 or not response.headers.get('content-type', '').startswith('text/html'):
            return new_links, is_updated

        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. Tìm link mới
        for a_tag in soup.find_all("a", href=True):
            new_url = urljoin(current_url, a_tag["href"]).split("#")[0].split("?")[0].rstrip('/')
            invalid_extensions = [".zip", ".rar", ".exe", ".mp4", ".mp3", ".doc", ".docx", ".xls", ".xlsx", "mailto:", "tel:", ".jpg", ".png"]
            if not any(ext in new_url.lower() for ext in invalid_extensions):
                new_links.append(new_url)

        # 2. Bóc tách và kiểm tra cập nhật (Hash)
        markdown_content, title = scrape_and_convert_to_markdown(current_url, response.text, MD_UPDATES_DIR, state)
        
        if markdown_content:
            content_only = markdown_content.split("---", 2)[-1].strip()
            content_hash = hashlib.md5(content_only.encode('utf-8')).hexdigest()
            
            with state_lock:
                old_hash = state.get(current_url)
                
            # Nếu phát hiện thay đổi
            if content_hash != old_hash:
                filename = get_valid_filename(current_url)
                output_path = os.path.join(MD_UPDATES_DIR, filename)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                    
                # Gọi đồng bộ Chunking
                success = process_single_markdown(output_path)
                
                if success:
                    with state_lock:
                        state[current_url] = content_hash
                    is_updated = True
                    
    except Exception as e:
        pass
        
    return new_links, is_updated

def run_dynamic_sync_threaded(start_urls, max_workers=10):
    print("="*70)
    print(f"🌐 KHỞI ĐỘNG AUTO SYNC MULTI-THREAD TỪ CÁC DOMAIN GỐC...")
    print("="*70)
    
    state = load_state()
    links_to_crawl = set(start_urls)
    visited_links = set()
    changes_detected = 0
    
    pbar = tqdm(desc="Đang quét web", unit=" link")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        while links_to_crawl:
            batch_urls = [links_to_crawl.pop() for _ in range(min(len(links_to_crawl), max_workers * 2))]
            visited_links.update(batch_urls)
            
            future_to_url = {executor.submit(process_single_url_sync, url, state): url for url in batch_urls}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    new_links, is_updated = future.result()
                    
                    if is_updated:
                        changes_detected += 1
                        tqdm.write(f"✨ [CẬP NHẬT WEB] Phát hiện thay đổi: {url}")

                    for link in new_links:
                        if should_crawl_url(link) and link not in visited_links and link not in links_to_crawl:
                            links_to_crawl.add(link)
                            
                except Exception as exc:
                    pass
                
                pbar.update(1)
                pbar.set_postfix({"Queue": len(links_to_crawl), "Updated": changes_detected})

    pbar.close()
    save_state(state) # Lưu lại JSON mã băm
    
    print("\n" + "="*70)
    print(f"🏁 Hoàn thành đợt đồng bộ đa luồng. Đã duyệt {len(visited_links)} links.")
    print(f"📈 Phát hiện và đẩy sang JSON thành công {changes_detected} trang web/file PDF thay đổi.")
    print("="*70)

if __name__ == "__main__":
    run_dynamic_sync_threaded(START_URLS, max_workers=2)