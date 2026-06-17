import os
import re
import urllib3
import trafilatura
import concurrent.futures
from urllib.parse import urljoin, urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm.auto import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

# 🟢 Khởi tạo Docling cho việc bóc tách PDF
from docling.document_converter import DocumentConverter
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
# Cấu hình Pipeline để bật OCR tiếng Việt
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True  # Bắt buộc quét OCR
pipeline_options.ocr_options = EasyOcrOptions(lang=["vi"]) # Chỉ định ngôn ngữ tiếng Việt

# Khởi tạo converter với cấu hình mới
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# =====================================================================
# 1. CẤU HÌNH HỆ THỐNG VÀ BỘ LỌC ĐỊNH TUYẾN
# =====================================================================

START_URLS = [
    "https://camnang.iuh.edu.vn/",
    "https://iuh.edu.vn/vi/thong-bao.html" # Trỏ thẳng vào trang thông báo
]

OUTPUT_DIR = r"G:\Khoa_Luan\Source_code\data\markdown_crawl1"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lọc miền gốc
ALLOWED_DOMAINS = {urlparse(url).netloc.lower().replace("www.", "") for url in START_URLS}

# Danh sách đen: Chặn các file rác, mục tin tức và gương điển hình
GLOBAL_BLACK_LIST = [
    "video.php", "/gallery/", "youtube.com", "facebook.com", "zalo.me",
    "guong-dien-hinh", 
    "tin-tuc"
]

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Khởi tạo Session mạng bền bỉ
session = requests.Session()
session.verify = False
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
session.headers.update(headers)

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
session.mount("http://", adapter)
session.mount("https://", adapter)

# =====================================================================
# 2. CÁC HÀM XỬ LÝ URL VÀ BÓC TÁCH DỮ LIỆU
# =====================================================================

def should_crawl_url(url):
    """Kiểm tra xem URL có hợp lệ để cào và bóc tách không"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        path_query = (parsed.path + "?" + parsed.query if parsed.query else parsed.path).lower()
        
        # [CẦU CHÌ] Chống vòng lặp URL (Spider Trap)
        if len(path_query) > 200 or path_query.count("/vi/") > 2:
            return False

        # 1. Chặn theo Blacklist
        if any(black in path_query for black in GLOBAL_BLACK_LIST): 
            return False
            
        # 2. Xử lý riêng cho trang Cẩm Nang (Được phép lấy tất cả)
        if domain == "camnang.iuh.edu.vn":
            return True
            
        # 3. Xử lý KHÓA CỨNG cho trang IUH chính (Chỉ lấy Thông báo)
        if domain == "iuh.edu.vn":
            if "thong-bao" in path_query:
                return True
            return False
            
        return False
    except:
        return False

def get_valid_filename(url):
    """Tạo tên file hợp lệ từ URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        path = parsed.path.strip('/')
        query = parsed.query
        filename = f"{domain}_{path}_{query}" if query else f"{domain}_{path}"
        filename = re.sub(r'[\@\.\/\=\?\&]', '-', filename)
        if not filename or filename.endswith("-"): filename = f"{domain}_index"
        return f"{filename}.md"
    except:
        return f"unknown_{datetime.now().timestamp()}.md"

def download_and_convert_pdf(pdf_url, output_dir):
    """Tải và chuyển đổi PDF sang Markdown bằng Docling"""
    try:
        pdf_dir = os.path.join(output_dir, "downloaded_pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = os.path.basename(urlparse(pdf_url).path)
        if not filename.lower().endswith('.pdf'): filename += '.pdf'
        pdf_filepath = os.path.join(pdf_dir, filename)
        md_filepath = os.path.join(output_dir, f"pdf_{filename.replace('.pdf', '.md')}")
        
        # Tải file PDF về máy nếu chưa tồn tại
        if not os.path.exists(pdf_filepath):
            response = session.get(pdf_url, stream=True, timeout=15)
            if response.status_code == 200:
                with open(pdf_filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
                    
        # Nếu đã tải PDF mà chưa có file MD thì chạy Docling
        if os.path.exists(pdf_filepath) and not os.path.exists(md_filepath):
            result = converter.convert(pdf_filepath)
            md_content = result.document.export_to_markdown()
            front_matter = f"---\nsource_url: \"{pdf_url}\"\ntitle: \"[PDF Extracted] {filename}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
            with open(md_filepath, "w", encoding="utf-8") as f:
                f.write(front_matter + md_content)
                
        return md_filepath
    except Exception as e:
        return None

def scrape_and_convert_to_markdown(url, html_text, output_dir):
    """Làm sạch HTML, bóc tách nội dung và bắt file PDF chủ động"""
    try:
        # Lấy tiêu đề trang
        page_title = "No Title"
        title_match = re.search(r'<title>(.*?)</title>', html_text, re.IGNORECASE)
        if title_match: page_title = title_match.group(1).strip()

        soup = BeautifulSoup(html_text, "html.parser")
        
        # =====================================================================
        # 🟢 TÌM VÀ TẢI PDF TRƯỚC KHI DỌN DẸP HTML
        # =====================================================================
        pdf_urls_to_download = set()
        
        # 1. Tìm trong tất cả các thẻ <a> (Bắt nút Download)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            text = a_tag.get_text(strip=True).lower()
            
            # Nếu link kết thúc bằng .pdf HOẶC có chữ "download file"
            if href.lower().split('?')[0].endswith('.pdf') or "download" in text or "tải về" in text:
                full_url = urljoin(url, href).split("#")[0]
                pdf_urls_to_download.add(full_url)

        # 2. Tìm trong các thẻ iframe (Bắt PDF được nhúng trên web)
        for iframe in soup.find_all("iframe", src=True):
            src = iframe["src"].strip()
            if ".pdf" in src.lower():
                if "url=" in src:
                    import urllib.parse
                    actual_pdf_url = re.search(r'url=([^&]+)', src)
                    if actual_pdf_url:
                        full_url = urllib.parse.unquote(actual_pdf_url.group(1))
                        pdf_urls_to_download.add(full_url)
                else:
                    full_url = urljoin(url, src).split("#")[0]
                    pdf_urls_to_download.add(full_url)

        # 3. Tiến hành tải và convert các PDF tìm được
        pdf_markdown_links = []
        for pdf_url in pdf_urls_to_download:
            md_path = download_and_convert_pdf(pdf_url, output_dir)
            if md_path:
                pdf_markdown_links.append(f"- [Đã tải PDF và bóc tách thành công]({pdf_url})")

        # =====================================================================
        # 🟡 TIỀN XỬ LÝ DỌN RÁC HTML VÀ BẢO TỒN DỮ LIỆU BẰNG BEAUTIFULSOUP
        # =====================================================================
        
        # 1. CỨU DỮ LIỆU BỊ THIẾU (Bảo tồn hộp "Lưu ý")
        # Chuyển các thẻ div chứa thông tin quan trọng thành thẻ blockquote
        for tag in soup.find_all('div'):
            text_content = tag.get_text(strip=True)
            if text_content.startswith("Lưu ý:") or "Chậm nhất một tháng sau" in text_content:
                tag.name = 'blockquote'
        
        # 2. XÓA DỮ LIỆU THỪA (Dọn rác class)
        bad_classes = re.compile(r'menu|sidebar|breadcrumb|footer|nav|related|widget|pagination|popular|post-nav|post-relate', re.I)
        for tag in soup.find_all(class_=bad_classes):
            tag.decompose()
            
        # 3. ĐẶC TRỊ CHO TRANG IUH: Cắt bỏ thủ công các khối tiêu đề nhiễu
        for text_to_remove in ['Bài phổ biến nhất', 'Bài viết liên quan', 'BÀI TRƯỚC', 'XEM TIẾP']:
            elements = soup.find_all(lambda tag: tag.name in ['h2', 'h3', 'h4', 'a', 'span', 'div'] and text_to_remove in tag.get_text(strip=True))
            for el in elements:
                parent_div = el.find_parent('div')
                if parent_div:
                    parent_div.decompose()
                else:
                    el.decompose()

        # Xóa các thẻ cơ bản không chứa nội dung bài viết
        for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'noscript']):
            tag.decompose()
            
        clean_html_text = str(soup)

        # =====================================================================
        # 🟢 BÓC TÁCH NỘI DUNG CHÍNH BẰNG TRAFILATURA
        # =====================================================================
        extracted_md = trafilatura.extract(
            clean_html_text,
            include_links=True,
            include_formatting=True,
            output_format="markdown",
            target_language="vi",
            favor_precision=True # Bật tính năng cắt rác nghiêm ngặt
        )

        if not extracted_md or len(extracted_md) < 50:
            extracted_md = ""

        # Chèn thêm thông báo về file PDF đã tải vào đầu bài viết
        if pdf_markdown_links:
            pdf_section = "\n\n### 📎 File đính kèm trong bài viết:\n" + "\n".join(pdf_markdown_links) + "\n\n---\n\n"
            clean_md = pdf_section + extracted_md
        else:
            clean_md = extracted_md

        clean_md = re.sub(r'\n{3,}', '\n\n', clean_md).strip()

        if not clean_md: return None

        # Gắn Front-matter metadata
        front_matter = f"---\nsource_url: \"{url}\"\ntitle: \"{page_title}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
        return front_matter + clean_md
        
    except Exception as e:
        print(f"Lỗi bóc tách nội dung: {e}")
        return None
    """Làm sạch HTML, bóc tách nội dung và bắt file PDF chủ động"""
    try:
        # Lấy tiêu đề trang
        page_title = "No Title"
        title_match = re.search(r'<title>(.*?)</title>', html_text, re.IGNORECASE)
        if title_match: page_title = title_match.group(1).strip()

        soup = BeautifulSoup(html_text, "html.parser")
        
        # =====================================================================
        # 🟢 BƯỚC MỚI: TÌM VÀ TẢI PDF TRƯỚC KHI DỌN DẸP HTML
        # =====================================================================
        pdf_urls_to_download = set()
        
        # 1. Tìm trong tất cả các thẻ <a> (Bắt nút Download)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            text = a_tag.get_text(strip=True).lower()
            
            # Nếu link kết thúc bằng .pdf HOẶC có chữ "download file" (như trên UI của bạn)
            if href.lower().split('?')[0].endswith('.pdf') or "download" in text or "tải về" in text:
                full_url = urljoin(url, href).split("#")[0]
                pdf_urls_to_download.add(full_url)

        # 2. Tìm trong các thẻ iframe (Bắt PDF được nhúng trên web)
        for iframe in soup.find_all("iframe", src=True):
            src = iframe["src"].strip()
            if ".pdf" in src.lower():
                # Xử lý trường hợp dùng google docs viewer
                if "url=" in src:
                    actual_pdf_url = re.search(r'url=([^&]+)', src)
                    if actual_pdf_url:
                        import urllib.parse
                        full_url = urllib.parse.unquote(actual_pdf_url.group(1))
                        pdf_urls_to_download.add(full_url)
                else:
                    full_url = urljoin(url, src).split("#")[0]
                    pdf_urls_to_download.add(full_url)

        # 3. Tiến hành tải và convert các PDF tìm được
        pdf_markdown_links = []
        for pdf_url in pdf_urls_to_download:
            md_path = download_and_convert_pdf(pdf_url, output_dir)
            if md_path:
                pdf_markdown_links.append(f"- [Đã tải PDF và bóc tách thành công]({pdf_url})")

        # =====================================================================
        # BƯỚC CŨ: TIỀN XỬ LÝ DỌN RÁC HTML VÀ BÓC TÁCH BẰNG TRAFILATURA
        # =====================================================================
        # Xóa các thẻ HTML điều hướng/chân trang
        for tag in soup(['nav', 'header', 'footer', 'aside']):
            tag.decompose()
            
        # Xóa các khối nghi ngờ là menu/sidebar
        for tag in soup.find_all(class_=re.compile(r'menu|sidebar|breadcrumb|footer|nav', re.I)):
            tag.decompose()
            
        clean_html_text = str(soup)

        extracted_md = trafilatura.extract(
            clean_html_text,
            include_links=True,
            include_formatting=True,
            output_format="markdown",
            target_language="vi"
        )

        if not extracted_md or len(extracted_md) < 50:
            extracted_md = "" # Nếu không có text, vẫn giữ để xuất file có chứa info PDF

        # Chèn thêm thông báo về file PDF đã tải vào đầu bài viết
        if pdf_markdown_links:
            pdf_section = "\n\n### 📎 File đính kèm trong bài viết:\n" + "\n".join(pdf_markdown_links) + "\n\n---\n\n"
            clean_md = pdf_section + extracted_md
        else:
            clean_md = extracted_md

        clean_md = re.sub(r'\n{3,}', '\n\n', clean_md).strip()

        # Tránh tạo file rỗng nếu không có text lẫn PDF
        if not clean_md: return None

        # Gắn Front-matter metadata
        front_matter = f"---\nsource_url: \"{url}\"\ntitle: \"{page_title}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
        return front_matter + clean_md
        
    except Exception as e:
        print(f"Lỗi bóc tách nội dung: {e}")
        return None

# =====================================================================
# 3. LUỒNG ĐIỀU HƯỚNG CRAWLER (ĐA LUỒNG)
# =====================================================================

def process_single_url(current_url, output_dir):
    """Hàm tải trang, lấy link mới và bóc tách (phục vụ cho ThreadPool)"""
    try:
        response = session.get(current_url, timeout=10)
        if response.status_code != 200: 
            return [], None
            
        # 1. Quét tìm liên kết mới để đi tiếp
        soup = BeautifulSoup(response.text, "html.parser")
        new_links = []
        for a_tag in soup.find_all("a", href=True):
            new_url = urljoin(current_url, a_tag["href"]).split("#")[0].rstrip('/')
            new_links.append(new_url)
            
        # 2. Tiến hành bóc tách nội dung
        markdown = scrape_and_convert_to_markdown(current_url, response.text, output_dir)
        
        if markdown:
            filename = get_valid_filename(current_url)
            with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
                f.write(markdown)
            return new_links, current_url
            
    except Exception as e:
        pass
    return [], None

def crawl_and_save_all_threaded(start_urls, output_dir, max_workers=10):
    """Hàm vận hành tổng thể Crawler Đa luồng"""
    print("🚀 Khởi động Multi-Domain Threaded Crawler...")
    links_to_crawl = set(start_urls)
    visited_links = set()
    successfully_saved = []

    pbar = tqdm(desc="Đang quét URL", unit=" link")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        while links_to_crawl:
            # Lấy ra batch để xử lý song song
            batch_urls = [links_to_crawl.pop() for _ in range(min(len(links_to_crawl), max_workers * 2))]
            visited_links.update(batch_urls)
            
            # Khởi chạy các luồng xử lý
            future_to_url = {executor.submit(process_single_url, url, output_dir): url for url in batch_urls}
            
            for future in concurrent.futures.as_completed(future_to_url):
                new_links, saved_url = future.result()
                
                if saved_url:
                    successfully_saved.append(saved_url)
                    
                # Phân loại link mới thu thập được
                for link in new_links:
                    invalid_extensions = [".pdf", ".zip", ".docx", ".rar", ".xlsx", ".mp4", ".7z", ".png", ".jpg", ".jpeg"]
                    if not any(link.lower().endswith(ext) for ext in invalid_extensions):
                        if should_crawl_url(link) and link not in visited_links and link not in links_to_crawl:
                            links_to_crawl.add(link)
                            
                pbar.update(1)
                pbar.set_postfix({"Queue": len(links_to_crawl), "Saved": len(successfully_saved)})

    pbar.close()
    
    # Ghi lại lịch sử tải thành công
    log_path = os.path.join(output_dir, "final_multi_hybrid_crawl_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        for link in sorted(successfully_saved): f.write(f"{link}\n")
    print(f"\n✅ Hoàn tất! Đã bóc tách thành công {len(successfully_saved)} bài viết chuẩn cấu trúc.")

if __name__ == "__main__":
    # Bắt đầu quét với 10 luồng xử lý đồng thời
    crawl_and_save_all_threaded(START_URLS, OUTPUT_DIR, max_workers=10)