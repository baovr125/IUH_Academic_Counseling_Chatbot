# =================================================================
# SCRIPT GIAI ĐOẠN 2 & 3: CHUNK VÀ EMBED (CẬP NHẬT SUPABASE POSTGRESQL)
# 
# Luồng 1 (Chạy độc lập): Quét sạch thư mục Markdown -> Nạp vào Supabase PostgreSQL
# Luồng 2 (Crawl gọi): Nhận 1 file Markdown thay đổi -> Upsert vào Supabase PostgreSQL
# (Tương thích với schema_v2_hybrid_rag.sql)
# =================================================================

import os
import re
import json
import uuid
import glob
import hashlib
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
import nltk

try:
    import psycopg2
    from psycopg2.extras import Json, execute_values
except ImportError:
    raise ImportError("Vui lòng cài đặt thư viện psycopg2-binary bằng lệnh: pip install psycopg2-binary")

from dotenv import load_dotenv

# --- 0. KHỞI TẠO NLTK ---
try:
    nltk.data.find("tokenizers/punkt")
except:
    nltk.download("punkt", quiet=True)

from nltk.tokenize import sent_tokenize

# --- 1. CẤU HÌNH HỆ THỐNG ---

# Thư mục chứa các file .md đầu vào (Dùng khi chạy độc lập)
INPUT_DIR = r"G:\Khoa_Luan\Source_code\data\markdown_craw3\markdown_updates" 
FILE_EXTENSION = ".md"

# Cấu hình Model và Chunking
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MAX_CHILD_WORDS = 250
MIN_CHILD_WORDS = 5
INJECT_METADATA = True

# --- 2. KHỞI TẠO KẾT NỐI SUPABASE POSTGRESQL & EMBEDDING MODEL ---

# Load biến môi trường từ các file .env có thể có trong dự án
load_dotenv()
load_dotenv(r"G:\Khoa_Luan\Source_code\backend_api\.env")
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend_api", ".env"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://YOUR_USER:YOUR_URL_ENCODED_PASSWORD@YOUR_SUPABASE_POOLER_HOST:6543/postgres"
)

def get_db_connection():
    """Tạo và trả về connection tới Supabase PostgreSQL."""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        # Xử lý tự động chuẩn hóa URL nếu password chứa @ hoặc @@ (double @)
        try:
            url = DATABASE_URL
            if url.startswith("postgresql://") or url.startswith("postgres://"):
                prefix = url.split("://", 1)[1]
                if "@" in prefix:
                    auth_part, host_part = prefix.rsplit("@", 1)
                    if ":" in auth_part:
                        user, password = auth_part.split(":", 1)
                        if password.endswith("@"):
                            password = password[:-1]
                    else:
                        user = auth_part
                        password = ""
                    host_db = host_part.split("/", 1)
                    host_port = host_db[0].split(":", 1)
                    host = host_port[0]
                    port = host_port[1] if len(host_port) > 1 else 5432
                    dbname = host_db[1] if len(host_db) > 1 else "postgres"
                    return psycopg2.connect(
                        host=host,
                        port=int(port),
                        dbname=dbname,
                        user=user,
                        password=password
                    )
        except Exception:
            pass
        raise e

print(f"📦 Đang kết nối và chuẩn bị tải mô hình nhúng cho Supabase...")
print(f"🔗 Đang tải mô hình nhúng: {MODEL_NAME}")
embedding_model = SentenceTransformer(MODEL_NAME)

# --- 3. CÁC HÀM TIỀN XỬ LÝ VÀ CHUNKING (HÀM UTILITY) ---

def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def clean_whitespace(s):
    return re.sub(r'\s+', ' ', s).strip()

def is_page_number(line): 
    return False

def looks_like_junk(s):
    if s is None: return True
    s_stripped = s.strip()
    if not s_stripped: return True
    if re.fullmatch(r'[\W_]+', s_stripped): return True
    return False

HEADER_REGEX = re.compile(r"^(#{1,6}\s+.*)", re.IGNORECASE)

def heuristic_is_header(line):
    if not line: return False
    s = line.strip()
    if s.startswith('#'): return True
    return False

def get_header_level(line):
    if not line: return None
    s = line.strip()
    if s.startswith('#'):
        return len(s.split(' ')[0])
    return 6 

def split_paragraphs_preserving_code(text):
    parts = re.split(r"\n\n+", text)
    filtered = []
    prev = None
    for p in parts:
        clean_p = clean_whitespace(p)
        if clean_p == prev or looks_like_junk(clean_p):
            continue
        filtered.append(clean_p)
        prev = clean_p
    return filtered

def split_into_sentences_safe(text):
    try:
        sents = sent_tokenize(text)
    except Exception:
        sents = re.split(r'(?<=[.!?])\s+', text)
    return [clean_whitespace(s) for s in sents if s and not looks_like_junk(s)]

def parse_front_matter(raw_text):
    """
    Hàm nâng cấp: Lấy thêm trường breadcrumbs từ front-matter
    """
    source_url = None
    title = None
    breadcrumbs = None
    content = raw_text
    
    if raw_text.startswith("---"):
        parts = raw_text.split("---", 2)
        if len(parts) >= 3:
            front_matter_raw = parts[1]
            content = parts[2].strip()
            
            url_match = re.search(r'source_url:\s*["\']?(.*?)["\']?\s*$', front_matter_raw, re.MULTILINE)
            title_match = re.search(r'title:\s*["\']?(.*?)["\']?\s*$', front_matter_raw, re.MULTILINE)
            breadcrumb_match = re.search(r'breadcrumbs:\s*["\']?(.*?)["\']?\s*$', front_matter_raw, re.MULTILINE)
            
            if url_match:
                source_url = url_match.group(1).strip()
            if title_match:
                title = title_match.group(1).strip()
            if breadcrumb_match:
                breadcrumbs = breadcrumb_match.group(1).strip()
                
    return source_url, title, breadcrumbs, content

def inject_meta(text, meta):
    """
    Hàm nâng cấp: Xây dựng tiền tố (prefix) chứa cả cấu trúc Web (Breadcrumbs)
    và cấu trúc bài viết (Ancestors/Headers) để tối ưu cho mô hình Vector.
    """
    if not INJECT_METADATA:
        return text
    
    title = meta.get("title", "")
    breadcrumbs = meta.get("breadcrumbs", "")
    ancestors = meta.get("placeholder_ancestors", [])
    
    if isinstance(ancestors, list):
        ancestors_str = " > ".join(ancestors)
    else:
        ancestors_str = str(ancestors)
    
    prefix_parts = []
    
    # 1. Thêm cấu trúc vĩ mô (Website Breadcrumbs)
    if breadcrumbs:
        prefix_parts.append(f"Đường dẫn: {breadcrumbs}")
        
    # 2. Thêm cấu trúc vi mô (Headers trong bài viết)
    if ancestors_str:
        prefix_parts.append(f"Mục: {ancestors_str} > {title}")
    elif title:
        prefix_parts.append(f"Mục: {title}")
        
    # 3. Nối tiền tố vào văn bản
    if prefix_parts:
        prefix = "[" + " | ".join(prefix_parts) + "] "
    else:
        prefix = ""
        
    return prefix + text

def build_hierarchical_chunks_v6_2(input_file):
    raw = read_text(input_file).replace('\r\n', '\n').replace('\r', '\n')
    
    # Lấy thêm breadcrumbs
    parsed_source_url, parsed_title, parsed_breadcrumbs, content_after_fm = parse_front_matter(raw)
    lines = content_after_fm.split('\n')

    parents = []
    current_parent = None
    content_lines = []
    current_chapter_title = None
    current_chapter_id = None

    for i, line in enumerate(lines):
        ls = line.strip()

        if is_page_number(ls):
            continue

        if HEADER_REGEX.match(ls) or heuristic_is_header(ls):
            if current_parent:
                current_parent['text'] = clean_whitespace("\n".join(content_lines))
                current_parent['is_placeholder'] = (len(current_parent['text'].strip()) == 0)
                parents.append(current_parent)
                content_lines = []

            title = re.sub(r"^#+\s*", "", ls).strip()
            level = get_header_level(ls)

            if level == 1:
                current_chapter_title = title
                current_chapter_id = str(uuid.uuid4())

            curr_meta = {
                "title": title,
                "level": level,
                "page": 1,
                # Ưu tiên lấy URL, nếu không có URL mới dùng tên file dự phòng
                "source": parsed_source_url if parsed_source_url else os.path.basename(input_file), 
                "source_url": parsed_source_url, 
                "breadcrumbs": parsed_breadcrumbs,
                "chapter_parent": current_chapter_title,
                "chapter_parent_id": current_chapter_id
            }

            current_parent = {
                "id": str(uuid.uuid4()),
                "title": title, "level": level, "text": "",
                "metadata": curr_meta,
                "child_ids": [], "is_placeholder": True
            }
            continue

        if ls and not looks_like_junk(ls):
            content_lines.append(ls)

    if current_parent:
        current_parent['text'] = clean_whitespace("\n".join(content_lines))
        current_parent['is_placeholder'] = (len(current_parent['text'].strip()) == 0)
        parents.append(current_parent)

    # Nếu không có thẻ Header nào, file sẽ được gom vào 1 cha duy nhất
    if not parents:
        fp_title = parsed_title or os.path.basename(input_file).replace('.md', '')
        fp = {
            "id": str(uuid.uuid4()), "title": fp_title, "level": 0,
            "text": content_after_fm,
            "metadata": {
                "title": fp_title, "level": 0, "page": 1,
                "source": parsed_source_url if parsed_source_url else os.path.basename(input_file),
                "source_url": parsed_source_url,
                "breadcrumbs": parsed_breadcrumbs, # Đưa breadcrumbs vào parent gốc
                "chapter_parent": None, "chapter_parent_id": None
            },
            "child_ids": [], "is_placeholder": False
        }
        parents.append(fp)

    for idx, parent in enumerate(parents):
        ancestors = []
        j = idx - 1
        while j >= 0 and parents[j].get('is_placeholder', False):
            ancestors.insert(0, parents[j]['title'])
            j -= 1
        parent['placeholder_ancestors'] = ancestors

    children = []
    for parent in parents:
        if parent.get('is_placeholder', False):
            continue

        paragraphs = split_paragraphs_preserving_code(parent['text'])
        for p in paragraphs:
            if len(p.split()) < MIN_CHILD_WORDS:
                continue
                
            if len(p.split()) > MAX_CHILD_WORDS:
                sents = split_into_sentences_safe(p)
                current_sub_chunk = ""
                for s in sents:
                    if len((current_sub_chunk + " " + s).split()) > MAX_CHILD_WORDS:
                        if len(current_sub_chunk.split()) >= MIN_CHILD_WORDS:
                            child_id = str(uuid.uuid4())
                            meta = parent['metadata'].copy()
                            meta['placeholder_ancestors'] = parent.get('placeholder_ancestors', [])
                            children.append({
                                "id": child_id, "parent_id": parent['id'],
                                "text": current_sub_chunk, "tokens": len(current_sub_chunk.split()),
                                "metadata": meta
                            })
                            parent['child_ids'].append(child_id)
                        current_sub_chunk = s
                    else:
                        current_sub_chunk += " " + s
                
                if len(current_sub_chunk.split()) >= MIN_CHILD_WORDS:
                    child_id = str(uuid.uuid4())
                    meta = parent['metadata'].copy()
                    meta['placeholder_ancestors'] = parent.get('placeholder_ancestors', [])
                    children.append({
                        "id": child_id, "parent_id": parent['id'],
                        "text": current_sub_chunk, "tokens": len(current_sub_chunk.split()),
                        "metadata": meta
                    })
                    parent['child_ids'].append(child_id)
            else:
                child_id = str(uuid.uuid4())
                meta = parent['metadata'].copy()
                meta['placeholder_ancestors'] = parent.get('placeholder_ancestors', [])
                children.append({
                    "id": child_id,
                    "parent_id": parent['id'],
                    "text": p,
                    "tokens": len(p.split()),
                    "metadata": meta
                })
                parent['child_ids'].append(child_id)
                
    return parents, children


# --- 4. HÀM CHÍNH ĐỂ ĐẨY VÀO SUPABASE POSTGRESQL (DÙNG CHO CẢ 2 LUỒNG) ---

def process_single_markdown(file_path):
    """
    Hàm bóc tách một file Markdown đơn lẻ, tạo Embedding 
    và Upsert (Thêm/Cập nhật) trực tiếp vào Supabase PostgreSQL
    theo cấu trúc bảng documents và document_chunks (schema_v2_hybrid_rag.sql).
    """
    try:
        filename = os.path.basename(file_path)
        
        # Đọc file và parse front-matter
        raw = read_text(file_path).replace('\r\n', '\n').replace('\r', '\n')
        parsed_source_url, parsed_title, parsed_breadcrumbs, content_after_fm = parse_front_matter(raw)
        
        # Xác định URL nguồn và tiêu đề (ưu tiên front-matter, nếu không có fallback theo tên file)
        source_url = parsed_source_url if parsed_source_url else f"file://{filename}"
        title = parsed_title if parsed_title else filename.replace('.md', '')
        breadcrumbs = parsed_breadcrumbs if parsed_breadcrumbs else ""
        
        # Tính mã băm MD5 cho nội dung để kiểm soát phiên bản
        content_only = content_after_fm.strip()
        content_hash = hashlib.md5(content_only.encode('utf-8')).hexdigest()
        
        # Lấy danh sách các chunk phân cấp
        parents, children = build_hierarchical_chunks_v6_2(file_path)
        
        if not children:
            return False

        # Kết nối tới Supabase PostgreSQL trong một transaction đồng bộ
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. UPSERT vào bảng `documents` theo source_url UNIQUE
                upsert_doc_query = """
                    INSERT INTO documents (title, source_url, breadcrumbs, content_hash, updated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (source_url) 
                    DO UPDATE SET 
                        title = EXCLUDED.title,
                        breadcrumbs = EXCLUDED.breadcrumbs,
                        content_hash = EXCLUDED.content_hash,
                        updated_at = NOW()
                    RETURNING id;
                """
                cur.execute(upsert_doc_query, (title, source_url, breadcrumbs, content_hash))
                doc_row = cur.fetchone()
                if not doc_row:
                    print(f"❌ Không thể upsert document cho '{source_url}'")
                    return False
                document_id = doc_row[0]
                
                # 2. Xóa các chunk cũ của document này (tránh orphan/duplicate khi bài viết cập nhật)
                cur.execute("DELETE FROM document_chunks WHERE document_id = %s;", (document_id,))
                
                # 3. Tạo embedding vector 384 chiều và chuẩn bị danh sách record cho document_chunks
                chunk_records = []
                for idx, child in enumerate(children):
                    injected_text = inject_meta(child["text"], child["metadata"])
                    
                    # Xử lý metadata danh sách thành chuỗi và chuẩn hóa None
                    meta = child["metadata"].copy()
                    if "placeholder_ancestors" in meta and isinstance(meta["placeholder_ancestors"], list):
                        meta["placeholder_ancestors"] = " > ".join(meta["placeholder_ancestors"])
                    meta_cleaned = {k: (v if v is not None else "") for k, v in meta.items()}
                    
                    # Encode thành vector 384 chiều của model paraphrase-multilingual-MiniLM-L12-v2
                    vector = embedding_model.encode(injected_text, convert_to_numpy=True).tolist()
                    vector_str = "[" + ",".join(str(x) for x in vector) + "]"
                    
                    tokens_count = child.get("tokens", len(child["text"].split()))
                    
                    # Bảng document_chunks: (document_id, chunk_index, content, injected_content, metadata, embedding, tokens_count)
                    # Cột fts_tokens tự động sinh GENERATED ALWAYS AS (to_tsvector('simple', ...))
                    chunk_records.append((
                        document_id,
                        idx,
                        child["text"],
                        injected_text,
                        Json(meta_cleaned),
                        vector_str,
                        tokens_count
                    ))
                
                # 4. Bulk insert toàn bộ chunk mới
                insert_chunks_query = """
                    INSERT INTO document_chunks (
                        document_id,
                        chunk_index,
                        content,
                        injected_content,
                        metadata,
                        embedding,
                        tokens_count
                    ) VALUES %s;
                """
                execute_values(
                    cur,
                    insert_chunks_query,
                    chunk_records,
                    template="(%s, %s, %s, %s, %s, %s::vector, %s)"
                )
                
            # Commit transaction khi mọi thao tác cho document + chunks thành công
            conn.commit()
            
        return True
            
    except Exception as e:
        print(f"❌ Lỗi xử lý Supabase PostgreSQL cho file {file_path}: {e}")
        return False


# --- 5. CHẠY ĐỘC LẬP (MAIN SCRIPT) ---

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 KHỞI CHẠY LUỒNG ĐỘC LẬP: TIẾN TRÌNH NẠP TOÀN BỘ VÀO SUPABASE POSTGRESQL")
    print("="*60)
    
    search_path = os.path.join(INPUT_DIR, f"*{FILE_EXTENSION}")
    file_paths = glob.glob(search_path)
    
    if not file_paths:
        print(f"❌ Thất bại: Không tìm thấy file '.md' nào trong thư mục: {INPUT_DIR}")
        print("Vui lòng kiểm tra lại cấu hình đường dẫn 'INPUT_DIR' ở mục 1.")
    else:
        print(f"🔎 Tìm thấy tổng cộng {len(file_paths)} file .md để bắt đầu nạp.")
        
        success_count = 0
        for path in tqdm(file_paths, desc="Đang xử lý nạp dữ liệu"):
            if process_single_markdown(path):
                success_count += 1
                
        doc_count = 0
        chunk_count = 0
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM documents;")
                    doc_count = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM document_chunks;")
                    chunk_count = cur.fetchone()[0]
        except Exception as e:
            print(f"⚠️ Không thể thống kê số lượng bản ghi từ Supabase: {e}")

        print("\n" + "="*60)
        print("🎉 TIẾN TRÌNH HOÀN TẤT TỐT ĐẸP!")
        print(f"📊 Đồng bộ thành công: {success_count}/{len(file_paths)} files.")
        print(f"🗂️ Tổng số bài viết (documents) trong Supabase: {doc_count}")
        print(f"🧩 Tổng số đoạn văn bản (chunks) trong Supabase: {chunk_count}")
        print(f"💾 Cơ sở dữ liệu: Supabase PostgreSQL (schema_v2_hybrid_rag.sql)")
        print("="*60)