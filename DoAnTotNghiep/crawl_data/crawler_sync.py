import requests
from bs4 import BeautifulSoup, NavigableString
import urllib3
import re
import os
import json
import hashlib
from urllib.parse import urljoin, urlparse
from tqdm.auto import tqdm
from datetime import datetime


from step2_chunk_embed import process_single_markdown

# =====================================================================
# 1. CẤU HÌNH THƯ MỤC VÀ HỆ THỐNG
# =====================================================================
BASE_URL = "https://camnang.iuh.edu.vn/"



# Thư mục chứa các file đang vận hành
WORK_DIR = r"G:\ChatBot\Code\Version1\chatbox_IUH\dynamic_document_updates"
STATE_FILE = os.path.join(WORK_DIR, "website_state.json")
MD_UPDATES_DIR = os.path.join(WORK_DIR, "markdown_updates")
JSON_DOCS_DIR = r"G:\ChatBot\Code\Version1\chatbox_IUH\data_json\json_documents"

os.makedirs(MD_UPDATES_DIR, exist_ok=True)
os.makedirs(JSON_DOCS_DIR, exist_ok=True)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {"User-Agent": "Mozilla/5.0"}

# =====================================================================
# 2. CÁC HÀM TIỀN XỬ LÝ (GIỮ NGUYÊN BẢN GỐC CỦA BẠN)
# =====================================================================
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def html_table_to_markdown(table):
    rows = table.find_all("tr")
    markdown = []
    for i, row in enumerate(rows):
        cols = [clean_text(col.get_text()) for col in row.find_all(["td", "th"])]
        if not cols: continue
        markdown.append(" | ".join(cols))
        if i == 0:
            markdown.append(" | ".join(["---"] * len(cols)))
    return "\n" + "\n".join(markdown) + "\n\n"

def get_valid_filename(url):
    try:
        path = urlparse(url).path
        filename = path.strip('/')
        filename = re.sub(r'[\@\.\/]', '-', filename)
        if not filename: filename = "index"
        return f"{filename}.md"
    except Exception:
        return f"{datetime.now().timestamp()}.md"

def is_junk_text(text):
    s_lower = text.lower()
    junk_keywords = [
        "scroll to top", "jquery js", "popper js", "bootstrap js",
        "end page content", "end session footer", "end page wrapper",
        "search box start here", "tạo avatar tân sinh viên",
        "gsap animation", "isotope js", "scripts js", "end js",
        "blog details end", "title bar end"
    ]
    for keyword in junk_keywords:
        if keyword in s_lower: return True
    if len(s_lower) < 10 and not s_lower[0].isalnum():
        if re.fullmatch(r'[\W_]+', s_lower): return True
    return False

HEADER_REGEX = re.compile(r"^(#{1,6}\s+.*)", re.IGNORECASE)

def process_html_content(soup_element):
    markdown_lines = []
    for el in soup_element.children:
        if isinstance(el, NavigableString):
            text = clean_text(el.string)
            if text and not is_junk_text(text): markdown_lines.append(text)
            continue
        if el.name is None: continue
        if el.name in ["script", "style", "nav", "footer", "header", "form", "iframe", "aside", "button", "svg"]: continue
            
        if el.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(el.name[1])
            header_prefix = "#" * (level + 1) 
            text = clean_text(el.get_text())
            if text: markdown_lines.append(f"\n{header_prefix} {text}\n")
        elif el.name == "table":
            markdown_lines.append(html_table_to_markdown(el))
        elif el.name == "ul":
            for li in el.find_all("li", recursive=False):
                text = clean_text(li.get_text())
                if text: markdown_lines.append(f"- {text}")
            markdown_lines.append("")
        elif el.name == "ol":
            for i, li in enumerate(el.find_all("li", recursive=False)):
                text = clean_text(li.get_text())
                if text: markdown_lines.append(f"{i+1}. {text}")
            markdown_lines.append("")
        elif el.name == "p":
            text_content = clean_text(el.get_text())
            if not text_content: continue
            strong_child = el.find("strong", recursive=False)
            is_strong_header = False
            if strong_child:
                strong_text = clean_text(strong_child.get_text())
                if len(text_content) - len(strong_text) < 10: 
                    is_strong_header = True
            if is_strong_header:
                markdown_lines.append(f"\n### {text_content}\n")
            else:
                markdown_lines.append(text_content)
        elif el.name in ["div", "main", "article", "section"]:
            markdown_lines.extend(process_html_content(el))
        else: 
            text = clean_text(el.get_text())
            if text and not is_junk_text(text): markdown_lines.append(text)

    final_output = []
    prev_line = None
    for line in markdown_lines:
        if line == prev_line: continue
        final_output.append(line)
        prev_line = line
    return final_output

def scrape_and_convert_to_markdown(url, soup):
    try:
        page_title = soup.title.string.strip() if soup.title else "Không có tiêu đề"
        tags_to_remove = ["script", "style", "nav", "footer", "header", "form", "iframe", "aside", "svg"]
        for tag in soup(tags_to_remove): tag.decompose()
            
        classes_to_remove = [
            "pbmit-featured-img-wrapper", "pbmit-blog-meta", "comments-area", 
            "post-navigation", "pbmit-social-share-links", "related-posts"
        ]
        for class_name in classes_to_remove:
            for element in soup.find_all(class_=class_name): element.decompose()
            
        content_div = (
            soup.find("div", class_="content") or soup.find("div", class_="entry-content")
            or soup.find("main") or soup.find("article") or soup.body 
        )
        if not content_div: return None, None

        markdown_lines = process_html_content(content_div)
        final_content = [f"# {page_title}\n"]
        prev = ""
        for l in markdown_lines:
            l = l.strip()
            if not l or l == prev: continue
            if l.lower().startswith("trang chủ") or "bài viết liên quan" in l.lower(): continue
            final_content.append(l)
            prev = l
            
        markdown_content = "\n\n".join(final_content)
        front_matter = f"---\nsource_url: \"{url}\"\ntitle: \"{page_title}\"\ncrawled_at: \"{datetime.now().isoformat()}\"\n---\n\n"
        return front_matter + markdown_content, page_title

    except Exception as e:
        print(f"  [Lỗi Scrape] {url}: {e}")
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

def run_dynamic_sync(base_url):
    print("="*70)
    print(f"🌐 KHỞI ĐỘNG AUTO SYNC TỪ: {base_url}")
    print("="*70)
    
    state = load_state()
    domain = urlparse(base_url).netloc
    
    links_to_crawl = {base_url}
    visited_links = set()
    changes_detected = 0
    
    pbar = tqdm(total=len(links_to_crawl), desc="Đang quét web")

    while links_to_crawl:
        current_url = links_to_crawl.pop()
        
        if current_url in visited_links:
            continue
            
        visited_links.add(current_url)
        pbar.set_description(f"Quét: ...{current_url.replace(base_url, '')[-40:]}")

        try:
            response = requests.get(current_url, headers=headers, verify=False, timeout=10)
            if response.status_code != 200 or not response.headers.get('content-type', '').startswith('text/html'):
                pbar.update(1)
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # --- KIỂM TRA THAY ĐỔI ---
            markdown_content, title = scrape_and_convert_to_markdown(current_url, soup)
            
            if markdown_content:
                # Băm toàn bộ nội dung Markdown (Đã loại bỏ rác/header/footer)
                content_hash = hashlib.md5(markdown_content.encode('utf-8')).hexdigest()
                old_hash = state.get(current_url)
                
                # NẾU CÓ SỰ THAY ĐỔI VỀ MẶT NỘI DUNG
                if content_hash != old_hash:
                    # 1. Lưu file Markdown để kiểm chứng
                    filename = get_valid_filename(current_url)
                    output_path = os.path.join(MD_UPDATES_DIR, filename)
                    
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                        
                    # 2. Chạy hàm Chunking để đẩy file JSON cho Watcher
                    # Hàm process_single_markdown sẽ lấy file .md, cắt và đẩy vào json_documents
                    success = process_single_markdown(output_path, JSON_DOCS_DIR)
                    
                    if success:
                        state[current_url] = content_hash
                        changes_detected += 1
                        # tqdm.write dùng để in text mà không làm vỡ thanh tiến trình (progress bar)
                        tqdm.write(f"✨ [CẬP NHẬT MỚI] Đã phát hiện thay đổi và xử lý: {current_url}")

            # --- TÌM LINK MỚI ĐỂ TIẾP TỤC CRAWL ---
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                new_url = urljoin(base_url, href).split("#")[0].split("?")[0]
                
                if (
                    new_url not in visited_links
                    and urlparse(new_url).netloc == domain
                    and not any(ext in new_url.lower() for ext in [
                        ".pdf", ".jpg", ".png", ".zip", ".rar", ".exe", ".mp4",
                        ".mp3", ".doc", ".docx", ".xls", ".xlsx", "mailto:", "tel:"
                    ])
                ):
                    links_to_crawl.add(new_url)
                    pbar.total = len(visited_links) + len(links_to_crawl)
            
            pbar.update(1)

        except requests.exceptions.RequestException as e:
            tqdm.write(f" ❌ [Lỗi Mạng] {current_url}: {e}")
            
    pbar.close()
    
    # Lưu lại trạng thái mã Hash cho lần quét ngày mai
    save_state(state)
    print("\n" + "="*70)
    print(f"🏁 Hoàn thành đợt đồng bộ. Đã duyệt {len(visited_links)} links.")
    print(f"📈 Phát hiện và cập nhật thành công {changes_detected} trang.")
    print("="*70)

if __name__ == "__main__":
    run_dynamic_sync(BASE_URL)