import re
import fitz  # PyMuPDF
import nltk
from typing import List, Dict, Any, Tuple
from app.utils.logger import logger

# Safe NLTK init
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    try:
        nltk.download("punkt", quiet=True)
    except Exception:
        pass

from nltk.tokenize import sent_tokenize

HEADER_REGEX = re.compile(r"^(#{1,6}\s+.*|chapter\s+\d+.*|chương\s+\d+.*|mục\s+\d+.*|\d+(\.\d+)*\.?\s+.*)", re.IGNORECASE)
MAX_CHILD_WORDS = 350
MIN_CHILD_WORDS = 5

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def split_into_sentences_safe(text: str) -> List[str]:
    try:
        sents = sent_tokenize(text)
    except Exception:
        sents = re.split(r"(?<=[.!?])\s+", text)
    return [clean_text(s) for s in sents if clean_text(s)]

def is_header_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith("#"):
        return True
    if HEADER_REGEX.match(s):
        return True
    if len(s) < 80 and s.isupper() and not s.endswith("."):
        return True
    return False

def get_header_level(line: str) -> int:
    s = line.strip()
    if s.startswith("#"):
        count = len(s.split()[0])
        return min(count, 6)
    if re.match(r"^chương\s+\d+", s, re.IGNORECASE) or re.match(r"^chapter\s+\d+", s, re.IGNORECASE):
        return 1
    if re.match(r"^\d+\.\s+", s):
        return 2
    if re.match(r"^\d+\.\d+\s+", s):
        return 3
    return 2

def parse_pdf_document(file_path: str) -> List[Dict[str, Any]]:
    """
    Trích xuất văn bản từ PDF theo trang sử dụng PyMuPDF.
    Trả về danh sách dict: [{'page': 1, 'text': '...', 'lines': [...]}]
    """
    pages_data = []
    try:
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            cleaned = clean_text(text)
            lines = [clean_text(l) for l in text.split("\n") if clean_text(l)]
            pages_data.append({
                "page": page_num,
                "text": cleaned,
                "lines": lines
            })
        doc.close()
    except Exception as e:
        logger.exception(f"Lỗi khi đọc file PDF bằng PyMuPDF ({file_path}): {e}")
        raise e
    return pages_data

def hierarchical_chunk_pages(pages_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Thực hiện thuật toán Hierarchical Chunking v6.2 (Parent-Child Structure).
    Trả về: (parent_chunks, child_chunks)
    """
    parent_chunks = []
    child_chunks = []
    
    current_parent_id = "parent_root"
    current_parent_title = "Tổng quan tài liệu"
    current_ancestors = []
    header_stack: List[Tuple[int, str]] = []  # [(level, title)]

    parent_chunks.append({
        "id": current_parent_id,
        "title": current_parent_title,
        "level": 1,
        "page_number": 1,
        "ancestors": []
    })
    
    child_counter = 0

    for page_info in pages_data:
        page_num = page_info["page"]
        lines = page_info["lines"]
        
        current_paragraph_lines = []

        for line in lines:
            if is_header_line(line):
                # Flush paragraph hiện tại nếu có
                if current_paragraph_lines:
                    p_text = " ".join(current_paragraph_lines)
                    sents = split_into_sentences_safe(p_text)
                    _build_child_chunks_from_sentences(
                        sents=sents,
                        page_num=page_num,
                        parent_id=current_parent_id,
                        parent_title=current_parent_title,
                        ancestors=current_ancestors,
                        child_chunks=child_chunks,
                        child_counter_start=len(child_chunks)
                    )
                    current_paragraph_lines = []

                # Xử lý Header mới
                level = get_header_level(line)
                clean_title = re.sub(r"^#{1,6}\s*", "", line).strip()
                
                # Cập nhật stack tiêu đề
                while header_stack and header_stack[-1][0] >= level:
                    header_stack.pop()
                header_stack.append((level, clean_title))
                
                current_ancestors = [h[1] for h in header_stack[:-1]]
                current_parent_title = clean_title
                current_parent_id = f"parent_p{page_num}_{len(parent_chunks)}"
                
                parent_chunks.append({
                    "id": current_parent_id,
                    "title": current_parent_title,
                    "level": level,
                    "page_number": page_num,
                    "ancestors": current_ancestors[:]
                })
            else:
                current_paragraph_lines.append(line)

        # End of page paragraph flush
        if current_paragraph_lines:
            p_text = " ".join(current_paragraph_lines)
            sents = split_into_sentences_safe(p_text)
            _build_child_chunks_from_sentences(
                sents=sents,
                page_num=page_num,
                parent_id=current_parent_id,
                parent_title=current_parent_title,
                ancestors=current_ancestors,
                child_chunks=child_chunks,
                child_counter_start=len(child_chunks)
            )
            current_paragraph_lines = []

    return parent_chunks, child_chunks

def _build_child_chunks_from_sentences(
    sents: List[str],
    page_num: int,
    parent_id: str,
    parent_title: str,
    ancestors: List[str],
    child_chunks: List[Dict[str, Any]],
    child_counter_start: int
):
    current_sentences = []
    current_word_count = 0

    for s in sents:
        words = s.split()
        w_len = len(words)

        if current_word_count + w_len > MAX_CHILD_WORDS and current_sentences:
            chunk_text = " ".join(current_sentences)
            if len(chunk_text.split()) >= MIN_CHILD_WORDS:
                child_chunks.append({
                    "chunk_index": len(child_chunks) + 1,
                    "parent_id": parent_id,
                    "page_number": page_num,
                    "parent_title": parent_title,
                    "ancestors": ancestors[:],
                    "content": chunk_text
                })
            current_sentences = [s]
            current_word_count = w_len
        else:
            current_sentences.append(s)
            current_word_count += w_len

    if current_sentences:
        chunk_text = " ".join(current_sentences)
        if len(chunk_text.split()) >= MIN_CHILD_WORDS or not child_chunks:
            child_chunks.append({
                "chunk_index": len(child_chunks) + 1,
                "parent_id": parent_id,
                "page_number": page_num,
                "parent_title": parent_title,
                "ancestors": ancestors[:],
                "content": chunk_text
            })
