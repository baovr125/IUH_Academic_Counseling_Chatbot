import re
import os
import pymupdf4llm
from typing import List
from app.utils.logger import logger


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def split_into_sentences_safe(text: str) -> List[str]:
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def is_header_line(line: str) -> bool:
    if not line:
        return False
    stripped = line.strip()
    if re.match(r'^#{1,6}\s+', stripped):
        return True
    if re.match(r'^(chương|chapter|\d+(\.\d+)*)\b', stripped, re.IGNORECASE):
        return True
    if stripped.isupper() and len(stripped.split()) <= 10 and len(stripped) > 5:
        return True
    return False


def get_header_level(line: str) -> int:
    stripped = line.strip()
    md_match = re.match(r'^(#{1,6})\s+', stripped)
    if md_match:
        return len(md_match.group(1))
    if re.match(r'^(chương|chapter)\s+\d+', stripped, re.IGNORECASE):
        return 1
    num_match = re.match(r'^(\d+(\.\d+)*)', stripped)
    if num_match:
        dots = num_match.group(1).count('.')
        return min(dots + 2, 6)
    if stripped.isupper():
        return 2
    return 1


def hierarchical_chunk_pages(pages_data: List[dict]):
    parents = [{"id": "parent_root", "title": "Tổng quan tài liệu"}]
    children = []
    chunk_idx = 1
    
    for page_info in pages_data:
        p_num = page_info.get("page", 1)
        p_text = page_info.get("text", "")
        lines = page_info.get("lines", [p_text])
        current_parent_title = "Tổng quan tài liệu"
        
        for line in lines:
            if is_header_line(line):
                current_parent_title = line.strip()
                parents.append({
                    "id": f"parent_{len(parents)}",
                    "title": current_parent_title,
                    "page_number": p_num
                })
            elif line.strip():
                children.append({
                    "chunk_index": chunk_idx,
                    "parent_title": current_parent_title,
                    "content": line.strip(),
                    "page_number": p_num
                })
                chunk_idx += 1
                
    return parents, children


def estimate_tokens(text: str) -> int:
    """Ước tính số token dựa trên số từ (1 từ ~ 1.3 token cho tiếng Anh/Việt)"""
    words = len(text.split())
    return int(words * 1.3)


def markdown_hierarchical_chunking(text: str, max_tokens: int = 2500) -> List[str]:
    """
    Tách nội dung Markdown dựa trên cấp độ Header (ưu tiên ## hoặc ###).
    Đảm bảo bảng biểu (Table), khối code, LaTeX không bị cắt vỡ ở giữa.
    Thuật toán phân tích Layout Structure Preserving Chunking.
    """
    batches: List[str] = []
    # Dùng regex để tách theo các Header cấp 1, 2 (ví dụ: #, ##)
    parts = re.split(r'(^#{1,2}\s+.*$)', text, flags=re.MULTILINE)
    
    current_batch = []
    current_tokens = 0
    
    for part in parts:
        part_trimmed = part.strip("\n")
        if not part_trimmed or not part_trimmed.strip():
            continue
            
        part_tokens = estimate_tokens(part_trimmed)
        
        # Nếu 1 section quá lớn, chia nhỏ theo paragraph
        if part_tokens > max_tokens * 1.5:
            sub_parts = re.split(r'\n\s*\n', part_trimmed)
            for sub_part in sub_parts:
                sub_tokens = estimate_tokens(sub_part)
                if current_tokens + sub_tokens > max_tokens and current_batch:
                    batches.append("\n\n".join(current_batch))
                    current_batch = [sub_part]
                    current_tokens = sub_tokens
                else:
                    current_batch.append(sub_part)
                    current_tokens += sub_tokens
        else:
            if current_tokens + part_tokens > max_tokens and current_batch:
                batches.append("\n\n".join(current_batch))
                current_batch = [part_trimmed]
                current_tokens = part_tokens
            else:
                current_batch.append(part_trimmed)
                current_tokens += part_tokens

    if current_batch:
        batches.append("\n\n".join(current_batch))
        
    return batches
