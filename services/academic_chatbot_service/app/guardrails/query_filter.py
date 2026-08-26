import re
from typing import Optional, Tuple

JAILBREAK_PATTERNS = [
    r"(?i)\b(ignore|skip|forget|bypass|override|disregard|cancel|drop)\s+(all\s+|previous\s+|above\s+)*(instructions|rules|prompts|directives|guidelines|constraints)\b",
    r"(?i)\b(show|print|display|repeat|output|reveal|tell|give|share|provide|read)\s+(me\s+|us\s+)*(your\s+|the\s+)*(system|initial|original|base|developer)\s+(prompt|instruction|rules|message|directives)\b",
    r"(?i)\bwhat\s+(is|are)\s+(your\s+|the\s+)*(system|initial|original|base)\s+(prompt|instruction|rules)\b",
    r"(?i)\b(bỏ\s+qua|quên|vượt\s+qua|hủy)\s+(mọi\s+)*(câu\s+lệnh|lệnh|hướng\s+dẫn|quy\s+định|quy\s+tắc)\s*(trước|ban\s+đầu|trên)*\b",
    r"(?i)\b(hãy\s+)*(cho\s+tôi\s+biết|bật\s+mí|in|hiển\s+thị|lặp\s+lại|tiết\s+lộ|nói\s+cho\s+tôi|đọc)\s+(câu\s+lệnh|system\s+prompt|lệnh\s+hệ\s+thống|hướng\s+dẫn\s+ban\s+đầu|lệnh\s+gốc)\b",
    r"(?i)\byou\s+are\s+now\s+(DAN|unfiltered|jailbroken|evil|root|admin)\b",
    r"(?i)\bpretend\s+(you\s+have\s+no|you\s+are\s+not\s+bound\s+by)\s+(rules|safety|restrictions)\b",
    r"(?i)\b(từ\s+giờ|hãy)\s+(đóng\s+vai|hóa\s+thân|nhập\s+vai)\s+(người\s+dùng\s+root|hacker|AI\s+không\s+giới\s+hạn|admin)\b",
    r"(?i)\bbỏ\s+qua\s+mọi\s+(quy\s+định|giới\s+hạn|luật\s+an\s+toàn)\b",
    r"(?i)<\|im_start\|>",
    r"(?i)<\|im_end\|>",
    r"(?i)\[INST\]",
    r"(?i)\[/INST\]",
    r"(?i)</?system>",
    r"(?i)\bsudo\s+mode\b",
    r"(?i)\badmin\s+override\b",
    r"(?i)\blệnh\s+từ\s+phòng\s+đào\s+tạo\b",
    r"(?i)\bcập\s+nhật\s+hệ\s+thống\b"
]

COMPILED_JAILBREAK_REGEX = [re.compile(p) for p in JAILBREAK_PATTERNS]

REFUSAL_MESSAGE = (
    "⚠️ **Cảnh báo an toàn**: Câu lệnh của bạn chứa từ ngữ hoặc mục đích can thiệp hệ thống không phù hợp. "
    "Vui lòng chỉ đặt các câu hỏi liên quan đến quy chế, thủ tục và thông tin học vụ tại Trường Đại học Công nghiệp TP.HCM (IUH)."
)

OFF_TOPIC_MESSAGE = (
    "Tôi là Trợ lý Tư vấn Học vụ IUH. Hiện tại tôi chỉ hỗ trợ các câu hỏi liên quan đến quy chế đào tạo, "
    "tín chỉ, học phí, biểu mẫu và dịch vụ sinh viên tại Trường ĐH Công nghiệp TP.HCM. "
    "Bạn có cần tư vấn thông tin học tập nào không?"
)

def check_safety_and_jailbreak(query: str) -> Optional[str]:
    if not query:
        return None
    for pattern in COMPILED_JAILBREAK_REGEX:
        if pattern.search(query):
            return REFUSAL_MESSAGE
    return None


import numpy as np
import os
from app.utils.logger import logger

# Load the multi-domain centroids at startup
CENTROID_PATH = os.path.join(os.path.dirname(__file__), "multi_domain_centroids.npz")
try:
    if os.path.exists(CENTROID_PATH):
        npz_file = np.load(CENTROID_PATH)
        ACADEMIC_CENTROIDS = {key: npz_file[key] for key in npz_file.files}
    else:
        logger.warning(f"File {CENTROID_PATH} not found. Fallback to passing all.")
        ACADEMIC_CENTROIDS = {}
except Exception as e:
    logger.warning(f"Failed to load academic centroids: {e}. Semantic domain check will pass everything.")
    ACADEMIC_CENTROIDS = {}

def evaluate_domain_relevance(query_text: str, query_embedding: list = None) -> Tuple[bool, Optional[str]]:
    """
    Evaluates if the user query is relevant to the IUH academic domain using multiple sub-centroids.
    """
    if not query_text or len(query_text.strip()) < 2:
        return True, None
        
    if not ACADEMIC_CENTROIDS or not query_embedding:
        # Fallback if model/centroid fails
        return True, None
        
    # Convert query embedding to numpy array
    query_vec = np.array(query_embedding)
    
    # Normalize query vector just in case
    norm = np.linalg.norm(query_vec)
    if norm > 0:
        query_vec = query_vec / norm
        
    # Calculate cosine similarity against all sub-centroids
    max_similarity = -1.0
    best_domain = "unknown"
    
    for domain, centroid in ACADEMIC_CENTROIDS.items():
        sim = np.dot(query_vec, centroid)
        if sim > max_similarity:
            max_similarity = sim
            best_domain = domain
            
    logger.info(f"Domain Similarity Score for '{query_text[:30]}...': {max_similarity:.4f} (Matched: {best_domain})")
    
    # Lowered threshold to 0.15 to reduce false positives for short queries or slang
    if max_similarity < 0.15:
        return False, OFF_TOPIC_MESSAGE
        
    return True, None

def wrap_context_sandbox(chunks: list) -> str:
    if not chunks:
        return ""
    formatted_parts = []
    for idx, c in enumerate(chunks, 1):
        content = c.get("content", "").strip()
        formatted_parts.append(f'<source id="{idx}">\n{content}\n</source>')
    body = "\n\n".join(formatted_parts)
    return f"<retrieved_context>\n{body}\n</retrieved_context>"
