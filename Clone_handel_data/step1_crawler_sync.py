import requests
from bs4 import BeautifulSoup
import urllib3
import re
import os
import json
import hashlib
from urllib.parse import urljoin, urlparse
from tqdm.auto import tqdm
from datetime import datetime
from markdownify import markdownify
from docling.document_converter import DocumentConverter

# 🟢 IMPORT hàm chunking từ file step2_chunk_embed của bạn
from step2_chunk_embed import process_single_markdown

# =====================================================================
# 1. CẤU HÌNH THƯ MỤC VÀ HỆ THỐNG
# =====================================================================

START_URLS = [
    "https://camnang.iuh.edu.vn/",
    "https://iuh.edu.vn/"
]

# Thư mục chứa các file đang vận hành
WORK_DIR = r"G:\Khoa_Luan\Source_code\data\markdown_craw"
STATE_FILE = os.path.join(WORK_DIR, "website_state.json")
MD_UPDATES_DIR = os.path.join(WORK_DIR, "markdown_updates")
JSON_DOCS_DIR = r"G:\Khoa_Luan\Source_code\data\json_documents"

os.makedirs(MD_UPDATES_DIR, exist_ok=True)
os.makedirs(JSON_DOCS_DIR, exist_ok=True)

# Bộ lọc nâng cao
ALLOWED_DOMAINS = {urlparse(url).netloc.lower().replace("www.", "") for url in START_URLS}
GLOBAL_BLACK_LIST = ["video.php", "/gallery/", "youtube.com", "facebook.com"]
IUH_SPECIFIC_ALLOW_LIST = [
    "/thong-bao", "so-do-bo-may-to-chuc", "/phong-", "/khoa-", "/vien-",
    "/trung-tam-", "/phan-hieu-", "/co-so-", "ban-giam-hieu", "dang-uy"
]

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# Cấu hình Docling chuyển đổi PDF
converter = DocumentConverter()

# =====================================================================
# 2. CÁC HÀM TIỀN XỬ LÝ (TẢI PDF, CLEAN HTML, CONVERT MARKDOWN)
# =====================================================================

def download_and_convert_pdf(pdf_url, output_dir, json_dir, state):
    """
    Hàm tải file PDF: Chỉ tải & bóc tách khi PDF trên server thực sự có thay đổi
    thông qua việc kiểm tra Header (HEAD Request), bảo vệ các file đã chỉnh sửa tay.
    """
    try:
        pdf_dir = os.path.join(output_dir, "downloaded_pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = os.path.basename(urlparse(pdf_url).path)
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
            
        pdf_filepath = os.path.join(pdf_dir, filename)
        md_filename = filename.replace('.pdf', '.md')
        md_filepath = os.path.join(output_dir, f"pdf_{md_filename}")
        
        # --- 1. KIỂM TRA PHIÊN BẢN PDF TRÊN SERVER ---
        head_resp = requests.head(pdf_url, headers=headers, verify=False, timeout=10)
        last_modified = head_resp.headers.get('Last-Modified', '')
        content_length = head_resp.headers.get('Content-Length', '')
        
        # Tạo chữ ký phiên bản cho PDF
        pdf_version_hash = f"{last_modified}_{content_length}"
        if not last_modified and not content_length:
            pdf_version_hash = pdf_url # Dự phòng nếu server ẩn header

        # NẾU PDF KHÔNG ĐỔI -> BỎ QUA (Bảo vệ file sửa tay)
        if state.get(pdf_url) == pdf_version_hash and os.path.exists(md_filepath):
            return None
                
        # --- 2. NẾU LÀ PDF MỚI HOẶC BỊ CẬP NHẬT -> TẢI VÀ XỬ LÝ ---
        response = requests.get(pdf_url, headers=headers, stream=True, verify=False, timeout=15)
        if response.status_code == 200:
            with open(pdf_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        # Bóc tách bằng Docling
        if os.path.exists(pdf_filepath):
            tqdm.write(f"\n📄 [CẬP NHẬT PDF] Đang tải và bóc tách tài liệu mới/thay đổi: {filename}")
            result = converter.convert(pdf_filepath)
            md_content = result.document.export_to_markdown()
            
            front_matter = f"---\nsource_url: \"{pdf_url}\"\ntitle: \"[PDF Extracted] {filename}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
            
            with open(md_filepath, "w", encoding="utf-8") as f:
                f.write(front_matter + md_content)
            
            # Gọi Chunking cho file PDF
            process_single_markdown(md_filepath, json_dir)
            
            # Cập nhật trạng thái PDF vào state
            state[pdf_url] = pdf_version_hash
                
        return md_filepath
    except Exception as e:
        # tqdm.write(f"Lỗi xử lý PDF {pdf_url}: {e}")
        pass
    return None


def get_valid_filename(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        path = parsed.path.strip('/')
        filename = re.sub(r'[\@\.\/\=\?\&]', '-', path)
        if not filename or filename.endswith("-"): 
            filename = f"{domain}_index"
        return f"{filename}.md"
    except:
        return f"unknown_{datetime.now().timestamp()}.md"


def should_crawl_url(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        path_query = (parsed.path + "?" + parsed.query if parsed.query else parsed.path).lower()
        
        if domain not in ALLOWED_DOMAINS: return False
        if any(black in path_query for black in GLOBAL_BLACK_LIST): return False
        if domain == "iuh.edu.vn" and not any(allow_path.lower() in path_query for allow_path in IUH_SPECIFIC_ALLOW_LIST): return False
        return True
    except:
        return False


def scrape_and_convert_to_markdown(url, soup, output_dir, json_dir, state):
    try:
        page_title = soup.title.string.strip() if soup.title else "Không có tiêu đề"
        soup_copy = BeautifulSoup(str(soup), "html.parser")
        
        # Dọn rác (Bao gồm cả img, svg, picture chống ảnh lỗi)
        for tag in soup_copy(["footer", "header", "nav", "aside", "form", "script", "style", "noscript", "img", "svg", "picture", "figure"]): 
            tag.decompose()
        
        classes_to_remove = [
            ".sidebar", "#sidebar", ".left-sidebar", ".right-sidebar", ".menu-left", ".left-menu",
            ".widget", ".breadcrumb", ".pagination", ".tin-lien-quan", ".related-news", 
            ".other-news", ".tin-khac", ".related-posts", ".tien-ich", ".chu-de", ".tags", ".search-box",
            "pbmit-featured-img-wrapper", "pbmit-blog-meta", "comments-area", "post-navigation", "pbmit-social-share-links"
        ]
        for class_name in classes_to_remove:
            for element in soup_copy.select(class_name): element.decompose()
        
        content_div = None
        target_classes = ["post-content", "entry-content", "article-content", "chi-tiet", "detail-content", "noidung", "post-detail", "page-content"]
        for cls in target_classes:
            content_div = soup_copy.find("div", class_=re.compile(cls, re.IGNORECASE))
            if content_div: break
            
        if not content_div:
            content_div = soup_copy.find("main") or soup_copy.find("article") or soup_copy.body
        
        if not content_div: return None, None
        
        # TẢI PDF & XÓA THẺ LINK
        for a_tag in content_div.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(url, href).split("#")[0] 
            
            # Tải và cập nhật PDF nếu phát hiện
            if full_url.lower().endswith('.pdf'):
                download_and_convert_pdf(full_url, output_dir, json_dir, state)
            
            # Xóa thuộc tính link
            a_tag.replace_with(a_tag.get_text())
        
        # Dùng markdownify để xuất text chuẩn sạch
        raw_markdown = markdownify(str(content_div), heading_style="ATX")
        clean_md = re.sub(r'!\[.*?\]\(.*?\)', '', raw_markdown) # Lọc cú pháp ảnh sót lại
        clean_md = re.sub(r'\n{3,}', '\n\n', clean_md).strip()
        
        if len(clean_md) < 50: return None, None

        front_matter = f"---\nsource_url: \"{url}\"\ntitle: \"{page_title}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
        return front_matter + clean_md, page_title
    except Exception as e:
        # tqdm.write(f"  [Lỗi Scrape] {url}: {e}")
        return None, None

# =====================================================================
# 3. QUẢN LÝ TRẠNG THÁI VÀ AUTO CRAWLER
# =====================================================================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)

def run_dynamic_sync(start_urls):
    print("="*70)
    print(f"🌐 KHỞI ĐỘNG AUTO SYNC TỪ CÁC DOMAIN GỐC...")
    print("="*70)
    
    state = load_state()
    links_to_crawl = set(start_urls)
    visited_links = set()
    changes_detected = 0
    
    pbar = tqdm(total=len(links_to_crawl), desc="Đang quét web")

    while links_to_crawl:
        current_url = links_to_crawl.pop()
        
        if current_url in visited_links: continue
        visited_links.add(current_url)
        
        if not should_crawl_url(current_url): continue
        
        pbar.set_description(f"Quét: ...{urlparse(current_url).path[-30:]}")

        try:
            response = requests.get(current_url, headers=headers, verify=False, timeout=10)
            if response.status_code != 200 or not response.headers.get('content-type', '').startswith('text/html'):
                pbar.update(1)
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # --- KIỂM TRA THAY ĐỔI TRÊN BÀI VIẾT WEB ---
            markdown_content, title = scrape_and_convert_to_markdown(current_url, soup, MD_UPDATES_DIR, JSON_DOCS_DIR, state)
            
            if markdown_content:
                # Lấy phần nội dung bỏ qua Front Matter để Hash
                content_only = markdown_content.split("---", 2)[-1].strip()
                content_hash = hashlib.md5(content_only.encode('utf-8')).hexdigest()
                old_hash = state.get(current_url)
                
                # NẾU CÓ SỰ THAY ĐỔI VỀ MẶT NỘI DUNG (HOẶC BÀI MỚI TOANH)
                if content_hash != old_hash:
                    filename = get_valid_filename(current_url)
                    output_path = os.path.join(MD_UPDATES_DIR, filename)
                    
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                        
                    # Chạy hàm Chunking để đẩy file JSON
                    success = process_single_markdown(output_path, JSON_DOCS_DIR)
                    
                    if success:
                        state[current_url] = content_hash
                        changes_detected += 1
                        tqdm.write(f"✨ [CẬP NHẬT WEB] Đã phát hiện thay đổi và xử lý: {current_url}")

            # --- TÌM LINK MỚI ĐỂ TIẾP TỤC CRAWL ---
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                new_url = urljoin(current_url, href).split("#")[0].split("?")[0].rstrip('/')
                
                invalid_extensions = [".zip", ".rar", ".exe", ".mp4", ".mp3", ".doc", ".docx", ".xls", ".xlsx", "mailto:", "tel:", ".jpg", ".png"]
                if any(ext in new_url.lower() for ext in invalid_extensions): continue
                
                if should_crawl_url(new_url) and new_url not in visited_links:
                    links_to_crawl.add(new_url)
                    pbar.total = len(visited_links) + len(links_to_crawl)
            
            pbar.update(1)

        except requests.exceptions.RequestException as e:
            # tqdm.write(f" ❌ [Lỗi Mạng] {current_url}: {e}")
            pass
            
    pbar.close()
    
    # Lưu lại trạng thái mã Hash tổng thể
    save_state(state)
    print("\n" + "="*70)
    print(f"🏁 Hoàn thành đợt đồng bộ. Đã duyệt {len(visited_links)} links.")
    print(f"📈 Phát hiện và cập nhật thành công {changes_detected} trang web/file PDF thay đổi.")
    print("="*70)

if __name__ == "__main__":
    run_dynamic_sync(START_URLS)