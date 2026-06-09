# =================================================================
# SCRIPT GIAI ĐOẠN 2 & 3: CHUNK VÀ EMBED (CẬP NHẬT CHROMADB DYNAMIC)
# 
# Luồng 1 (Chạy độc lập): Quét sạch thư mục Markdown -> Nạp vào ChromaDB
# Luồng 2 (Crawl gọi): Nhận 1 file Markdown thay đổi -> Upsert vào ChromaDB
# =================================================================

import os
import re
import json
import uuid
import glob
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
import nltk
import chromadb

# --- 0. KHỞI TẠO NLTK ---
try:
    nltk.data.find("tokenizers/punkt")
except:
    nltk.download("punkt", quiet=True)

from nltk.tokenize import sent_tokenize

# --- 1. CẤU HÌNH HỆ THỐNG ---

# Thư mục chứa các file .md đầu vào (Dùng khi chạy độc lập)
INPUT_DIR = r"G:\Khoa_Luan\Source_code\data\markdown_crawl\markdown_updates" 
FILE_EXTENSION = ".md"

# Nơi lưu trữ Cơ sở dữ liệu ChromaDB
CHROMA_DB_DIR = r"G:\Khoa_Luan\Source_code\data\chroma_db"
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Cấu hình Model và Chunking
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MAX_CHILD_WORDS = 250
MIN_CHILD_WORDS = 5
INJECT_METADATA = True

# --- 2. KHỞI TẠO CHROMADB & EMBEDDING MODEL ---
print(f"📦 Đang kết nối ChromaDB tại: {CHROMA_DB_DIR}")
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# Lấy hoặc tạo mới Collection (Sử dụng khoảng cách L2 tương tự FAISS cũ)
collection = chroma_client.get_or_create_collection(
    name="camnang_iuh_collection",
    metadata={"hnsw:space": "l2"}
)

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
    source_url = None
    title = None
    content = raw_text
    
    if raw_text.startswith("---"):
        parts = raw_text.split("---", 2)
        if len(parts) >= 3:
            front_matter_raw = parts[1]
            content = parts[2].strip()
            
            url_match = re.search(r'source_url:\s*["\']?(.*?)["\']?\s*$', front_matter_raw, re.MULTILINE)
            title_match = re.search(r'title:\s*["\']?(.*?)["\']?\s*$', front_matter_raw, re.MULTILINE)
            
            if url_match:
                source_url = url_match.group(1).strip()
            if title_match:
                title = title_match.group(1).strip()
                
    return source_url, title, content

def inject_meta(text, meta):
    if not INJECT_METADATA:
        return text
    
    title = meta.get("title", "")
    # Xử lý nếu placeholder_ancestors đang là list hoặc chuỗi kết hợp
    ancestors = meta.get("placeholder_ancestors", [])
    if isinstance(ancestors, list):
        ancestors_str = " > ".join(ancestors)
    else:
        ancestors_str = str(ancestors)
    
    if ancestors_str:
        prefix = f"[Mục: {ancestors_str} > {title}] "
    else:
        prefix = f"[Mục: {title}] "
        
    return prefix + text

def build_hierarchical_chunks_v6_2(input_file):
    raw = read_text(input_file).replace('\r\n', '\n').replace('\r', '\n')
    
    parsed_source_url, parsed_title, content_after_fm = parse_front_matter(raw)
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
                "source": os.path.basename(input_file),
                "source_url": parsed_source_url, 
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

    if not parents:
        fp_title = parsed_title or os.path.basename(input_file).replace('.md', '')
        fp = {
            "id": str(uuid.uuid4()), "title": fp_title, "level": 0,
            "text": content_after_fm,
            "metadata": {
                "title": fp_title, "level": 0, "page": 1,
                "source": os.path.basename(input_file),
                "source_url": parsed_source_url,
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


# --- 4. HÀM CHÍNH ĐỂ ĐẨY VÀO CHROMADB (DÙNG CHO CẢ 2 LUỒNG) ---

def process_single_markdown(file_path):
    """
    Hàm bóc tách một file Markdown đơn lẻ, tạo Embedding 
    và Upsert (Thêm/Cập nhật) trực tiếp vào ChromaDB.
    """
    try:
        filename = os.path.basename(file_path)
        parents, children = build_hierarchical_chunks_v6_2(file_path)
        
        if not children:
            return False

        # Chuẩn bị cấu trúc lưu trữ cho ChromaDB
        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for child in children:
            # Tạo văn bản giàu ngữ cảnh để Embedding
            injected_text = inject_meta(child["text"], child["metadata"])
            
            ids.append(child["id"])
            documents.append(child["text"]) # Chỉ lưu text gốc làm document để LLM đọc
            
            # Làm sạch và định dạng lại Metadata cho phù hợp với ChromaDB
            meta = child["metadata"].copy()
            if "placeholder_ancestors" in meta and isinstance(meta["placeholder_ancestors"], list):
                meta["placeholder_ancestors"] = " > ".join(meta["placeholder_ancestors"])
            
            # Loại bỏ giá trị None để tránh lỗi hệ thống của ChromaDB
            meta_cleaned = {k: (v if v is not None else "") for k, v in meta.items()}
            metadatas.append(meta_cleaned)
            
            # Tạo mã nhúng (Vector) từ văn bản ngữ cảnh
            vector = embedding_model.encode(injected_text, convert_to_numpy=True).tolist()
            embeddings.append(vector)

        # Tiến hành nạp/cập nhật vào DB
        if ids:
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            return True
            
    except Exception as e:
        print(f"❌ Lỗi xử lý ChromaDB cho file {file_path}: {e}")
        return False


# --- 5. CHẠY ĐỘC LẬP (MAIN SCRIPT) ---
# Khối lệnh này chỉ chạy khi bạn kích hoạt trực tiếp file này bằng lệnh `python step2_chunk_embed.py`

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 KHỞI CHẠY LUỒNG ĐỘC LẬP: TIẾN TRÌNH NẠP TOÀN BỘ VÀO CHROMADB")
    print("="*60)
    
    # Tìm kiếm toàn bộ file .md trong thư mục cấu hình mặc định
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
                
        print("\n" + "="*60)
        print("🎉 TIẾN TRÌNH HOÀN TẤT TỐT ĐẸP!")
        print(f"📊 Đồng bộ thành công: {success_count}/{len(file_paths)} files.")
        print(f"🗂️ Tổng số lượng bản ghi hiện có trong ChromaDB: {collection.count()}")
        print(f"💾 Vị trí cơ sở dữ liệu: {CHROMA_DB_DIR}")
        print("="*60)