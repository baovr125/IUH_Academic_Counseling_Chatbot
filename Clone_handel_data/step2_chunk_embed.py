# =================================================================
# SCRIPT GIAI ĐOẠN 2 & 3: CHUNK VÀ EMBED (CẬP NHẬT DYNAMIC RAG)
# 
# Đầu vào: Thư mục 'markdown_crawl_output' (từ Giai đoạn 1)
# Đầu ra:  - json_documents/ (Thư mục chứa các file JSON nhỏ, mỗi file 1 trang web)
#          - camnang_faiss.index (Vector index)
# =================================================================

import os
import re
import json
import uuid
import glob
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import nltk
from collections import defaultdict

# --- 0. CÀI ĐẶT ---
# Yêu cầu cài đặt (nếu chưa có):
# pip install sentence-transformers faiss-cpu numpy nltk

try:
    nltk.data.find("tokenizers/punkt")
except:
    nltk.download("punkt")

from nltk.tokenize import sent_tokenize

# --- 1. CẤU HÌNH ---

# 🔽 CHỈNH SỬA: Trỏ đến thư mục output của Giai đoạn 1 (chứa các file .md)
input_dir = r"G:\Khoa_Luan\Source_code\data\markdown_crawl\markdown_updates" 
FILE_EXTENSION = ".md"

# Nơi lưu kết quả Giai đoạn 3
output_dir = r"G:\Khoa_Luan\Source_code\data\json_documents"
os.makedirs(output_dir, exist_ok=True)

# Thư mục lưu các file JSON nhỏ
json_docs_dir = os.path.join(output_dir, "json_documents")
os.makedirs(json_docs_dir, exist_ok=True)

# Cấu hình model và chunking
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MAX_CHILD_WORDS = 250
MIN_CHILD_WORDS =  5
INJECT_METADATA = True

# Tên file output FAISS (Vector DB)
output_faiss_index = os.path.join(output_dir, "camnang_faiss.index")


# --- 2. HÀM UTILITY ---

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
    """Hàm helper đọc front matter (YAML) khỏi nội dung."""
    source_url = None
    title = None
    content = raw_text
    
    if raw_text.startswith("---"):
        parts = raw_text.split("---", 2)
        if len(parts) >= 3:
            front_matter_raw = parts[1]
            content = parts[2].strip()
            
            # Regex tìm source_url và title
            url_match = re.search(r'source_url:\s*["\']?(.*?)["\']?\s*$', front_matter_raw, re.MULTILINE)
            title_match = re.search(r'title:\s*["\']?(.*?)["\']?\s*$', front_matter_raw, re.MULTILINE)
            
            if url_match:
                source_url = url_match.group(1).strip()
            if title_match:
                title = title_match.group(1).strip()
                
    return source_url, title, content

def inject_meta(text, meta):
    """Tạo văn bản cuối cùng để embedding."""
    if not INJECT_METADATA:
        return text
    
    title = meta.get("title", "")
    ancestors = " > ".join(meta.get("placeholder_ancestors", []))
    
    if ancestors:
        prefix = f"[Mục: {ancestors} > {title}] "
    else:
        prefix = f"[Mục: {title}] "
        
    return prefix + text

def format_source_for_user(child):
    """Format nguồn cho người dùng."""
    meta = child.get("metadata", {})
    if meta.get("source_url"):
        return meta["source_url"]
        
    parts = []
    if meta.get("source"):
        parts.append(f"File: {os.path.basename(meta['source'])}")
    if meta.get("title"):
        parts.append(f"Mục: {meta.get('title')}")
        
    return " — ".join(parts)


# --- 3. HÀM CHUNKING ---

def build_hierarchical_chunks_v6_2(input_file):
    raw = read_text(input_file).replace('\r\n', '\n').replace('\r', '\n')
    
    # Tách front matter
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
                "source_url": parsed_source_url, # Cập nhật source URL
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


# --- 4. HÀM EMBEDDING & SAVE ---

def embed_and_save_faiss(all_children, model_name):
    if not all_children:
        print("⚠️ Không có children nào để embed. Dừng lại.")
        return

    print(f"\n🔗 Đang tải model embedding: {model_name}")
    model = SentenceTransformer(model_name)

    texts_for_embedding = []
    for i, c in enumerate(all_children):
        injected_text = inject_meta(c["text"], c["metadata"])
        c["text_for_embedding"] = injected_text
        c["original_index"] = i # Quan trọng: Giữ index gốc
        texts_for_embedding.append(injected_text)
    
    print(f"⏳ Bắt đầu tạo embedding cho {len(texts_for_embedding)} chunks...")
    embeddings = model.encode(
        texts_for_embedding, 
        show_progress_bar=True, 
        convert_to_numpy=True
    )
    print("✅ Tạo embedding hoàn tất.")

    # Tạo FAISS index
    d = embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    
    # Quan trọng: Dùng IndexIDMap để map ID của FAISS về 'original_index'
    ids_array = np.array([c['original_index'] for c in all_children]).astype('int64')
    index = faiss.IndexIDMap(index)
    index.add_with_ids(embeddings.astype('float32'), ids_array)

    # Lưu FAISS index
    faiss.write_index(index, output_faiss_index)
    print(f"💾 Đã lưu FAISS index vào: {output_faiss_index}")

    # =========================================================
    # CHIA NHỎ VÀ LƯU FILE JSON THEO TỪNG NGUỒN (SOURCE)
    # =========================================================
    print("⏳ Đang phân tách nội dung thành các file JSON riêng biệt...")
    
    chunks_by_source = defaultdict(list)
    for c in all_children:
        # Lấy tên file gốc làm key (ví dụ: buoc-thoi-hoc-php.md)
        source_file = c["metadata"].get("source", "unknown_source.md")
        chunks_by_source[source_file].append(c)

    # Lưu từng nhóm thành một file JSON
    for source_file, chunks in chunks_by_source.items():
        json_filename = source_file.replace(".md", ".json")
        json_filepath = os.path.join(json_docs_dir, json_filename)
        
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
            
    print(f"📁 Đã tạo {len(chunks_by_source)} file JSON trong thư mục: {json_docs_dir}")
# --- TRÍCH XUẤT HÀM DÙNG CHUNG CHO DYNAMIC UPDATE ---
def process_single_markdown(file_path, json_docs_dir):
    """
    Hàm này nhận đầu vào là 1 file Markdown, thực hiện Chunking,
    và lưu trực tiếp thành 1 file JSON vào thư mục json_docs_dir.
    """
    try:
        print(f"Đang xử lý Chunking cho file: {os.path.basename(file_path)}")
        parents, children = build_hierarchical_chunks_v6_2(file_path)
        
        if not children:
            print("⚠️ Không có chunk nào được tạo.")
            return False

        # Xác định tên file JSON
        source_file = children[0]["metadata"].get("source", "unknown_source.md")
        json_filename = source_file.replace(".md", ".json")
        json_filepath = os.path.join(json_docs_dir, json_filename)
        
        # Lưu file JSON
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(children, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Đã tạo file JSON: {json_filepath}")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi xử lý file {file_path}: {e}")
        return False


# --- 5. HÀM THỰC THI CHÍNH ---

if __name__ == "__main__":
    
    print("=== BẮT ĐẦU GIAI ĐOẠN 2: CHUNKING ===")
    search_path = os.path.join(input_dir, f"*{FILE_EXTENSION}")
    file_paths = glob.glob(search_path)
    
    if not file_paths:
        print(f"❌ Lỗi: Không tìm thấy file '.md' nào trong thư mục: {input_dir}")
        print("Hãy chắc chắn rằng đường dẫn 'input_dir' đúng và chứa các file .md")
    else:
        print(f"🔎 Tìm thấy {len(file_paths)} file .md để xử lý.")

        all_parents = []
        all_children = []

        for file_path in tqdm(file_paths, desc="Đang chunking các file Markdown"):
            try:
                parents, children = build_hierarchical_chunks_v6_2(file_path)
                all_parents.extend(parents)
                all_children.extend(children)
            except Exception as e:
                print(f" Lỗi khi xử lý file {file_path}: {e}")

        print(f"\n✅ Giai đoạn 2 hoàn tất.")
        print(f"  Tổng cộng Parents: {len(all_parents)}")
        print(f"  Tổng cộng Children (chunks): {len(all_children)}")

        print("\n=== BẮT ĐẦU GIAI ĐOẠN 3: EMBEDDING & SAVING ===")
        embed_and_save_faiss(all_children, MODEL_NAME)
        
        print("\n🎉🎉🎉 PIPELINE HOÀN TẤT! 🎉🎉🎉")
        print(f"Index Vector Database: {output_faiss_index}")
        print(f"Thư mục chứa Metadata (JSON): {json_docs_dir}")