import re
from typing import Optional, Tuple

# =====================================================================
# 1. JAILBREAK & PROMPT INJECTION SHIELD (LAYER 1 & 2)
# =====================================================================

JAILBREAK_PATTERNS = [
    # System Prompt Exfiltration & Directive Overrides (English)
    r"(?i)\b(ignore|skip|forget|bypass|override|disregard|cancel|drop)\s+(all\s+|previous\s+|above\s+)*(instructions|rules|prompts|directives|guidelines|constraints)\b",
    r"(?i)\b(show|print|display|repeat|output|reveal|tell|give|share|provide|read)\s+(me\s+|us\s+)*(your\s+|the\s+)*(system|initial|original|base|developer)\s+(prompt|instruction|rules|message|directives)\b",
    r"(?i)\bwhat\s+(is|are)\s+(your\s+|the\s+)*(system|initial|original|base)\s+(prompt|instruction|rules)\b",

    # System Prompt Exfiltration & Directive Overrides (Vietnamese)
    r"(?i)\b(bỏ\s+qua|quên|vượt\s+qua|hủy)\s+(mọi\s+)*(câu\s+lệnh|lệnh|hướng\s+dẫn|quy\s+định|quy\s+tắc)\s*(trước|ban\s+đầu|trên)*\b",
    r"(?i)\b(hãy\s+)*(cho\s+tôi\s+biết|bật\s+mí|in|hiển\s+thị|lặp\s+lại|tiết\s+lộ|nói\s+cho\s+tôi|đọc)\s+(câu\s+lệnh|system\s+prompt|lệnh\s+hệ\s+thống|hướng\s+dẫn\s+ban\s+đầu|lệnh\s+gốc)\b",

    # Roleplay & Persona Hijacking
    r"(?i)\byou\s+are\s+now\s+(DAN|unfiltered|jailbroken|evil|root|admin)\b",
    r"(?i)\bpretend\s+(you\s+have\s+no|you\s+are\s+not\s+bound\s+by)\s+(rules|safety|restrictions)\b",
    r"(?i)\b(từ\s+giờ|hãy)\s+(đóng\s+vai|hóa\s+thân|nhập\s+vai)\s+(người\s+dùng\s+root|hacker|AI\s+không\s+giới\s+hạn|admin)\b",
    r"(?i)\bbỏ\s+qua\s+mọi\s+(quy\s+định|giới\s+hạn|luật\s+an\s+toàn)\b",

    # Control Token / Delimiter Injections
    r"(?i)<\|im_start\|>",
    r"(?i)<\|im_end\|>",
    r"(?i)\[INST\]",
    r"(?i)\[/INST\]",
    r"(?i)</?system>",

    # Fake Privilege Escalation & Admin Override
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
    """Inspects query for prompt injection, jailbreak attempts, or control token hijacking.
    Returns refusal message if an attack pattern is detected, otherwise None.
    """
    if not query:
        return None

    for pattern in COMPILED_JAILBREAK_REGEX:
        if pattern.search(query):
            return REFUSAL_MESSAGE
    return None


# =====================================================================
# 2. ACADEMIC QUERY SANITIZATION & ABBREVIATION NORMALIZER
# =====================================================================

ACADEMIC_ABBREVIATIONS = [
    (r"\bdkhp\b", "đăng ký học phần"),
    (r"\bdkhc\b", "đăng ký học cải thiện"),
    (r"\bdktc\b", "đăng ký tín chỉ"),
    (r"\bgpa\b", "điểm trung bình tích lũy"),
    (r"\btin chi\b", "tín chỉ"),
    (r"\btinchi\b", "tín chỉ"),
    (r"\bquy che\b", "quy chế"),
    (r"\bquyche\b", "quy chế"),
    (r"\bhoc phi\b", "học phí"),
    (r"\bhocphi\b", "học phí"),
    (r"\bhoc bong\b", "học bổng"),
    (r"\bhocbong\b", "học bổng"),
    (r"\bxet tot nghiep\b", "xét tốt nghiệp"),
    (r"\btot nghiep\b", "tốt nghiệp"),
]

COMPILED_ABBREVIATION_REGEX = [(re.compile(pattern, re.IGNORECASE), replacement) for pattern, replacement in ACADEMIC_ABBREVIATIONS]


def normalize_academic_query(query: str) -> str:
    """Replaces common student academic abbreviations with standard Vietnamese terminology."""
    if not query:
        return query
    
    cleaned = query
    for pattern, replacement in COMPILED_ABBREVIATION_REGEX:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


# =====================================================================
# 3. DOMAIN RELEVANCE EVALUATOR
# =====================================================================

ACADEMIC_DOMAIN_KEYWORDS = [
    "iuh", "học vụ", "tín chỉ", "học phần", "đăng ký", "học phí", "điểm", "gpa", "bảng điểm",
    "học bổng", "tốt nghiệp", "quy chế", "biểu mẫu", "khoa", "ngành", "lớp", "giảng viên",
    "chào", "chào bạn", "hello", "hi", "xin chào", "thời khóa biểu",
    "thi", "bảo lưu", "rút môn", "hoãn thi", "xét", "chứng chỉ", "thực tập", "đồ án", "khóa luận"
]


def evaluate_domain_relevance(query: str) -> Tuple[bool, Optional[str]]:
    """Evaluates if the query belongs to IUH academic counseling or general greetings.
    Returns (True, None) if relevant, or (False, off_topic_message) if out-of-domain.
    """
    if not query or len(query.strip()) < 2:
        return True, None

    lower_query = query.lower()

    # Check off-topic triggers FIRST to prevent generic keyword bypass
    OFF_TOPIC_TRIGGERS = [
        "nấu phở", "công thức nấu", "chứng khoán", "coin", "bitcoin", "crypto", "hack game",
        "viết code game", "nấu ăn", "soạn nhạc", "tiểu thuyết"
    ]
    if any(t in lower_query for t in OFF_TOPIC_TRIGGERS):
        return False, OFF_TOPIC_MESSAGE

    if any(k in lower_query for k in ACADEMIC_DOMAIN_KEYWORDS):
        return True, None

    return True, None


# =====================================================================
# 4. INDIRECT PROMPT INJECTION XML CONTEXT SANDBOXING
# =====================================================================

def wrap_context_sandbox(chunks: list) -> str:
    """Wraps retrieved RAG document chunks cleanly inside <retrieved_context> XML tags.
    This prevents Indirect Prompt Injection from malicious text inside ingested documents.
    """
    if not chunks:
        return ""

    formatted_parts = []
    for idx, c in enumerate(chunks, 1):
        content = c.get("content", "").strip()
        formatted_parts.append(f'<source id="{idx}">\n{content}\n</source>')

    body = "\n\n".join(formatted_parts)
    return f"<retrieved_context>\n{body}\n</retrieved_context>"
