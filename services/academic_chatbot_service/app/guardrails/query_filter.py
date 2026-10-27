import re
from typing import Optional

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
    r"(?i)\bsudo\s+mode\b",
    r"(?i)\badmin\s+override\b",
    r"(?i)\blệnh\s+từ\s+phòng\s+đào\s+tạo\b",
    r"(?i)\bcập\s+nhật\s+hệ\s+thống\b",
]

STRUCTURAL_TAG_PATTERNS = [
    # 1. RAG Context & Framing tags
    r"(?i)</?retrieved_context\b[^>]*>",
    r"(?i)</?source\b[^>]*>",
    r"(?i)</?user_query\b[^>]*>",
    r"(?i)</?query_reminder\b[^>]*>",

    # 2. Self-RAG & Thinking / Reasoning tags
    r"(?i)</?thinking\b[^>]*>",
    r"(?i)</?think\b[^>]*>",
    r"(?i)</?doc_relevance\b[^>]*>",
    r"(?i)</?conflict_detected\b[^>]*>",
    r"(?i)</?answer_confidence\b[^>]*>",
    r"(?i)</?suggested_queries\b[^>]*>",
    r"(?i)</?query\b[^>]*>",

    # 3. System / Role / Prompt injection tags
    r"(?i)</?system\b[^>]*>",
    r"(?i)</?system_instruction\b[^>]*>",
    r"(?i)</?instruction\b[^>]*>",
    r"(?i)</?context\b[^>]*>",
    r"(?i)</?prompt\b[^>]*>",
    r"(?i)</?rules\b[^>]*>",

    # 4. Chat template delimiters & LLM special tokens
    r"(?i)<\|(?:im_start|im_end|im_sep|system|user|assistant|start_header_id|end_header_id|eot_id)\|?>",
    r"(?i)\[/?INST\]",
    r"(?i)\[/?SYS\]",
    r"(?i)<<SYS>>",
    r"(?i)<</SYS>>",
]

ALL_SAFETY_PATTERNS = JAILBREAK_PATTERNS + STRUCTURAL_TAG_PATTERNS
COMPILED_JAILBREAK_REGEX = [re.compile(p) for p in ALL_SAFETY_PATTERNS]

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

def _sandwich_reorder(chunks: list) -> list:
    """
    Sắp xếp chunks theo Sandwich Pattern để giảm thiểu hiện tượng Lost-in-the-Middle.
    Input: Danh sách chunks đã sắp xếp giảm dần theo điểm liên quan (rerank_score).
    Output: [#1, #3, #5, ..., #4, #2] — đưa các tài liệu phù hợp nhất về 2 đầu (primacy & recency).
    """
    if len(chunks) <= 2:
        return chunks

    left = []   # rank 1, 3, 5... (chỉ số 0, 2, 4...)
    right = []  # rank 2, 4, 6... (chỉ số 1, 3, 5...)

    for i, chunk in enumerate(chunks):
        if i % 2 == 0:
            left.append(chunk)
        else:
            right.append(chunk)

    return left + list(reversed(right))


def wrap_context_sandbox(chunks: list, user_query: str = "") -> str:
    if not chunks:
        return ""
    
    reordered_chunks = _sandwich_reorder(chunks)
    formatted_parts = []
    for idx, c in enumerate(reordered_chunks, 1):
        content = c.get("content", "").strip()
        metadata = c.get("metadata", {}) or {}
        
        # Trích xuất các metadata hữu ích cho CF-RAG
        title = metadata.get("title", "")
        upload_time = metadata.get("created_at") or metadata.get("upload_time")
        
        meta_lines = []
        if title:
            meta_lines.append(f"Nguồn: {title}")
        if upload_time:
            meta_lines.append(f"Ngày cập nhật lên CSDL: {upload_time}")
        meta_str = "\n".join(meta_lines) + "\n" if meta_lines else ""
        
        formatted_parts.append(f'<source id="{idx}">\n{meta_str}{content}\n</source>')
    body = "\n\n".join(formatted_parts)

    echo_part = ""
    if user_query and user_query.strip():
        echo_part = f"\n\n<query_reminder>\nCâu hỏi cần trả lời: {user_query.strip()}\n</query_reminder>"

    return f"<retrieved_context>\n{body}{echo_part}\n</retrieved_context>"
