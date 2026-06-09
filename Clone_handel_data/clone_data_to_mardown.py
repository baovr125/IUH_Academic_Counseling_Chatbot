import requests
from bs4 import BeautifulSoup
import urllib3
import re
import os
from urllib.parse import urljoin, urlparse
from tqdm.auto import tqdm
from datetime import datetime
from markdownify import markdownify
import pymupdf4llm 
from docling.document_converter import DocumentConverter
# --- 1. CẤU HÌNH HỆ THỐNG ĐỊNH TUYẾN LAI (HYBRID ROUTER CONFIG) ---

START_URLS = [
    "https://camnang.iuh.edu.vn/",
    "https://iuh.edu.vn/"
]

OUTPUT_DIR = r"G:\Khoa_Luan\Source_code\data\markdown_crawl1"

ALLOWED_DOMAINS = {urlparse(url).netloc.lower().replace("www.", "") for url in START_URLS}

# [BỘ LỌC TOÀN CỤC]: Chặn file tĩnh/rác trên mọi tên miền
GLOBAL_BLACK_LIST = ["video.php", "/gallery/", "youtube.com", "facebook.com"]

# [BỘ LỌC CHO PHÉP ĐẶC THÙ]: Chỉ áp dụng cho iuh.edu.vn
IUH_SPECIFIC_ALLOW_LIST = [
    "/thong-bao",             # Bắt trang chủ thông báo VÀ tất cả các bài thông báo chi tiết
    "so-do-bo-may-to-chuc",   # Bắt trang sơ đồ tổ chức gốc
    "/phong-",                # Bắt tất cả các phòng ban
    "/khoa-",                 # Bắt tất cả các khoa
    "/vien-",                 # Bắt tất cả các viện
    "/trung-tam-",            # Bắt tất cả các trung tâm
    "/phan-hieu-",            # Bắt các phân hiệu
    "/co-so-",                # Bắt các cơ sở
    "ban-giam-hieu",          # Bắt trang ban giám hiệu
    "dang-uy"                 # Bắt trang Đảng ủy
]

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}


# --- HÀM TẢI VÀ CHUYỂN ĐỔI PDF SANG MARKDOWN ---
# Cấu hình Docling ở đầu file
converter = DocumentConverter()

def download_and_convert_pdf(pdf_url, output_dir):
    try:
        pdf_dir = os.path.join(output_dir, "downloaded_pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = os.path.basename(urlparse(pdf_url).path)
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
            
        pdf_filepath = os.path.join(pdf_dir, filename)
        
        if not os.path.exists(pdf_filepath):
            response = requests.get(pdf_url, headers=headers, stream=True, verify=False, timeout=15)
            if response.status_code == 200:
                with open(pdf_filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
        
        if os.path.exists(pdf_filepath):
            md_filename = filename.replace('.pdf', '.md')
            md_filepath = os.path.join(output_dir, f"pdf_{md_filename}")
            
            if not os.path.exists(md_filepath):
                # ----------------------------------------------------
                # THAY ĐỔI TẠI ĐÂY: DÙNG DOCLING THAY CHO PYMUPDF4LLM
                # ----------------------------------------------------
                result = converter.convert(pdf_filepath)
                md_content = result.document.export_to_markdown()
                
                front_matter = f"---\nsource_url: \"{pdf_url}\"\ntitle: \"[PDF Extracted] {filename}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
                
                with open(md_filepath, "w", encoding="utf-8") as f:
                    f.write(front_matter + md_content)
                    
            return md_filepath
    except Exception as e:
        print(f"Lỗi xử lý PDF {pdf_url}: {e}")
    return None

# --- 2. LOGIC KIỂM TRA ĐIỀU KIỆN (LAI PHÂN TẦNG) ---
def should_crawl_url(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        path_query = (parsed.path + "?" + parsed.query if parsed.query else parsed.path).lower()
        
        if domain not in ALLOWED_DOMAINS: 
            return False
            
        if any(black in path_query for black in GLOBAL_BLACK_LIST): 
            return False
            
        if domain == "iuh.edu.vn":
            if not any(allow_path.lower() in path_query for allow_path in IUH_SPECIFIC_ALLOW_LIST):
                return False
                
        return True
    except:
        return False


def get_valid_filename(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        path = parsed.path.strip('/')
        query = parsed.query
        filename = f"{domain}_{path}_{query}" if query else f"{domain}_{path}"
        filename = re.sub(r'[\@\.\/\=\?\&]', '-', filename)
        if not filename or filename.endswith("-"): 
            filename = f"{domain}_index"
        return f"{filename}.md"
    except:
        return f"unknown_{datetime.now().timestamp()}.md"


# --- 3. BÓC TÁCH NỘI DUNG SẠCH ---
def scrape_and_convert_to_markdown(url, soup, output_dir):
    try:
        page_title = soup.title.string.strip() if soup.title else "No Title"
        soup_copy = BeautifulSoup(str(soup), "html.parser")
        
        # Xóa các tag không cần thiết (Bao gồm cả img, svg, picture, figure)
        for tag in soup_copy(["footer", "header", "nav", "aside", "form", "script", "style", "noscript", "img", "svg", "picture", "figure"]): 
            tag.decompose()
        
        junk_selectors = [
            ".sidebar", "#sidebar", ".left-sidebar", ".right-sidebar",
            ".menu-left", ".left-menu", "#menu-left", "#left-menu",
            ".widget", ".widget-area", ".breadcrumb", ".pagination",
            ".tin-lien-quan", ".related-news", ".other-news", ".tin-khac", ".related-posts",
            ".tien-ich", ".box-right", ".box-left", ".chu-de", ".tags",
            ".search-box", ".scroll-to-top", ".comments-area",
            ".pbmit-featured-wrapper", ".pbmit-blog-meta"
        ]
        for selector in junk_selectors:
            for element in soup_copy.select(selector):
                element.decompose()
        
        # Tìm div chứa nội dung chính
        content_div = None
        target_classes = ["post-content", "entry-content", "article-content", "chi-tiet", "detail-content", "noidung", "post-detail", "page-content"]
        for cls in target_classes:
            content_div = soup_copy.find("div", class_=re.compile(cls, re.IGNORECASE))
            if content_div: break
            
        if not content_div:
            content_div = (
                soup_copy.find("main") or 
                soup_copy.find("article") or 
                soup_copy.find("div", id=re.compile(r"main-content|content-main", re.IGNORECASE)) or 
                soup_copy.find("div", class_="content") or
                soup_copy.body
            )
        
        if not content_div: return None
        
        # XỬ LÝ THẺ LINK VÀ TẢI PDF
        for a_tag in content_div.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(url, href).split("#")[0] 
            
            # CẬP NHẬT: Tải và tự động chuyển đổi PDF sang Markdown
            if full_url.lower().endswith('.pdf'):
                download_and_convert_pdf(full_url, output_dir)
            
            # Xóa thuộc tính link, chỉ giữ lại phần text hiển thị
            a_tag.replace_with(a_tag.get_text())
        
        # Convert qua Markdown
        raw_markdown = markdownify(str(content_div), heading_style="ATX")
        
        # Dọn dẹp Regex: Xóa mọi cú pháp ảnh Markdown ![alt](link) hoặc ![](link)
        clean_md = re.sub(r'!\[.*?\]\(.*?\)', '', raw_markdown)
        
        # Xóa các dòng trống thừa thãi
        clean_md = re.sub(r'\n{3,}', '\n\n', clean_md).strip()
        
        if len(clean_md) < 50: return None

        front_matter = f"---\nsource_url: \"{url}\"\ntitle: \"{page_title}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
        return front_matter + clean_md
    except:
        return None


# --- 4. LUỒNG ĐIỀU HƯỚNG CRAWLER ---
def crawl_and_save_all(start_urls, output_dir):
    print(f"🚀 Khởi động Multi-Domain Crawler (Bao gồm chuyển đổi PDF to MD)...")
    os.makedirs(output_dir, exist_ok=True)
    
    links_to_crawl = set(start_urls)
    visited_links = set()
    successfully_saved = []

    pbar = tqdm(total=len(links_to_crawl), desc="Tiến độ")

    while links_to_crawl:
        current_url = links_to_crawl.pop()
        if current_url in visited_links: continue
        visited_links.add(current_url)

        if not should_crawl_url(current_url): continue

        try:
            response = requests.get(current_url, headers=headers, verify=False, timeout=10)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            for a_tag in soup.find_all("a", href=True):
                new_url = urljoin(current_url, a_tag["href"]).split("#")[0].rstrip('/')
                invalid_extensions = [".pdf", ".zip", ".docx", ".rar", ".xlsx", ".mp4", ".7z", ".png", ".jpg", ".jpeg"]
                
                # Bỏ .pdf ra khỏi danh sách extension không hợp lệ nếu bạn muốn Crawler 
                # theo dấu trực tiếp vào link kết thúc bằng .pdf từ start_url 
                # (hiện tại bot chỉ tải PDF nếu nó nằm TRONG bài viết).
                if any(new_url.lower().endswith(ext) for ext in invalid_extensions): continue
                
                if should_crawl_url(new_url) and new_url not in visited_links:
                    links_to_crawl.add(new_url)
                    pbar.total = len(visited_links) + len(links_to_crawl)
            
            markdown = scrape_and_convert_to_markdown(current_url, soup, output_dir)
            
            if markdown:
                filename = get_valid_filename(current_url)
                with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
                    f.write(markdown)
                successfully_saved.append(current_url)
            
            pbar.update(1)
        except: 
            continue

    pbar.close()
    
    log_path = os.path.join(output_dir, "final_multi_hybrid_crawl_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        for link in sorted(successfully_saved): f.write(f"{link}\n")
    print(f"\n✅ Hoàn tất! Đã lưu thành công {len(successfully_saved)} file sạch cấu trúc.")


if __name__ == "__main__":
    crawl_and_save_all(START_URLS, OUTPUT_DIR)