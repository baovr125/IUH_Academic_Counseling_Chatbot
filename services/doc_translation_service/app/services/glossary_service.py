import re
from typing import List, Dict, Any

# Từ điển Thuật ngữ Học vụ Chuẩn IUH (IUH Academic Terminology Dictionary)
IUH_ACADEMIC_GLOSSARY: Dict[str, Dict[str, str]] = {
    "academic regulations": {
        "vi": "Quy chế học vụ",
        "context": "Các quy định về đào tạo, tín chỉ và học tập tại IUH"
    },
    "credit system": {
        "vi": "Hệ thống đào tạo theo tín chỉ",
        "context": "Phương thức đào tạo áp dụng tại Trường ĐH Công nghiệp TP.HCM"
    },
    "cumulative grade point average": {
        "vi": "Điểm trung bình tích lũy (CGPA)",
        "context": "Điểm trung bình tính trên toàn bộ số tín chỉ đã tích lũy"
    },
    "cgpa": {
        "vi": "Điểm trung bình tích lũy",
        "context": "Viết tắt của Cumulative Grade Point Average"
    },
    "academic advisor": {
        "vi": "Cố vấn học tập",
        "context": "Giảng viên tư vấn và hỗ trợ sinh viên trong quá trình học tập"
    },
    "graduation internship report": {
        "vi": "Báo cáo thực tập tốt nghiệp",
        "context": "Báo cáo thu hoạch thực tế tại doanh nghiệp"
    },
    "course syllabus": {
        "vi": "Đề cương chi tiết học phần",
        "context": "Tài liệu mô tả mục tiêu, nội dung và chuẩn đầu ra môn học"
    },
    "academic transcript": {
        "vi": "Bảng điểm học tập",
        "context": "Bảng tổng hợp điểm số các học phần của sinh viên"
    },
    "tuition fee": {
        "vi": "Học phí",
        "context": "Mức phí đào tạo theo số tín chỉ đăng ký"
    },
    "prerequisite course": {
        "vi": "Học phần tiên quyết",
        "context": "Môn học phải bắt buộc đạt trước khi học môn tiếp theo"
    },
    "learning outcome": {
        "vi": "Chuẩn đầu ra học phần",
        "context": "Kiến thức và kỹ năng sinh viên cần đạt sau môn học"
    },
    "graduation thesis": {
        "vi": "Khóa luận tốt nghiệp",
        "context": "Đồ án nghiên cứu cuối khóa của sinh viên"
    },
    "software engineering": {
        "vi": "Kỹ thuật Phần mềm",
        "context": "Ngành đào tạo thuộc Khoa Công nghệ Thông tin IUH"
    },
    "industrial university of ho chi minh city": {
        "vi": "Trường Đại học Công nghiệp TP.Hồ Chí Minh (IUH)",
        "context": "Tên chính thức của trường"
    }
}

def scan_document_for_glossary(text: str) -> List[Dict[str, str]]:
    """
    Quét văn bản để phát hiện các thuật ngữ chuyên ngành học vụ IUH có trong bài.
    Trả về danh sách dict: [{'term': '...', 'vi': '...', 'context': '...'}]
    """
    found = []
    text_lower = text.lower()
    
    for term_key, data in IUH_ACADEMIC_GLOSSARY.items():
        pattern = r"\b" + re.escape(term_key) + r"\b"
        if re.search(pattern, text_lower):
            found.append({
                "term": term_key.title() if len(term_key) > 4 else term_key.upper(),
                "vi": data["vi"],
                "context": data["context"]
            })
            
    return found

def get_glossary_prompt_instructions(found_glossary: List[Dict[str, str]]) -> str:
    """
    Tạo prompt ràng buộc ép LLM Gemini phải dịch đúng theo Từ điển thuật ngữ IUH.
    """
    if not found_glossary:
        return ""
        
    lines = ["YÊU CẦU ÉP DỊCH ĐÚNG TỪ ĐIỂN THUẬT NGỮ HỌC VỤ IUH:"]
    for item in found_glossary:
        lines.append(f"- '{item['term']}' ➔ '{item['vi']}' ({item.get('context', '')})")
    lines.append("Tuyệt đối KHÔNG tự ý thay đổi các thuật ngữ chuẩn trên sang nghĩa khác.")
    return "\n".join(lines)
