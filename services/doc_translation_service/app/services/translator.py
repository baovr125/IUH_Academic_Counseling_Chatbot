import os
from typing import List, Dict, Any, Tuple
from google import genai
from app.services.glossary_service import scan_document_for_glossary, get_glossary_prompt_instructions
from app.utils.logger import logger

def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Thiếu biến môi trường GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

def translate_chunk_with_gemini(
    text: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    parent_title: str = "",
    ancestors: List[str] = None,
    glossary: List[Dict[str, str]] = None
) -> str:
    """
    Dịch 1 đoạn văn bản sử dụng Gemini 2.5 Flash kết hợp Từ điển Thuật ngữ IUH & Context vị trí chương/mục.
    """
    if not text.strip():
        return ""

    ancestor_str = " > ".join(ancestors) if ancestors else ""
    context_prefix = f"Vị trí mục: [{ancestor_str} > {parent_title}]" if parent_title else ""
    glossary_instr = get_glossary_prompt_instructions(glossary or [])

    system_instruction = (
        "Bạn là Chuyên gia Dịch thuật Báo cáo Khoa học và Tài liệu Học vụ Đại học Công nghiệp TP.HCM (IUH).\n"
        "Nhiệm vụ: Dịch chính xác văn bản từ ngôn ngữ nguồn sang ngôn ngữ đích được yêu cầu, giữ nguyên văn phong học thuật, chuyên nghiệp.\n"
        f"{glossary_instr}\n"
        "LƯU Ý:\n"
        "1. Giữ nguyên cấu trúc định dạng markdown (tiêu đề #, danh sách, công thức, mã số).\n"
        "2. Không thêm bớt ý so với bản gốc.\n"
        "3. Trả về DUY NHẤT phần văn bản đã dịch, không kèm lời chào hay giải thích thừa."
    )

    prompt = (
        f"Dịch đoạn văn bản sau từ {source_lang.upper()} sang {target_lang.upper()}:\n"
        f"{context_prefix}\n\n"
        f"--- NỘI DUNG GỐC ---\n"
        f"{text}\n"
        f"--- BẢN DỊCH {target_lang.upper()} ---"
    )

    try:
        client = get_gemini_client()
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"system_instruction": system_instruction, "temperature": 0.2}
        )
        if res and res.text:
            return res.text.strip()
    except Exception as e:
        logger.exception(f"Lỗi khi dịch thuật với Gemini API: {e}")

    # Fallback return text if API error
    return text

def generate_document_summary_and_glossary(full_text: str) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """
    Tạo tóm tắt AI tự động (Executive summary, Key points) và trích xuất thuật ngữ chuyên ngành.
    """
    detected_glossary = scan_document_for_glossary(full_text)

    prompt = (
        "Phân tích tài liệu và trả về tóm tắt thông minh bằng tiếng Việt dưới định dạng JSON theo đúng cấu trúc:\n"
        "{\n"
        '  "executive_summary": "Tổng quan ngắn gọn 2-3 câu về nội dung tài liệu.",\n'
        '  "key_findings": ["Điểm cốt lõi 1", "Điểm cốt lõi 2", "Điểm cốt lõi 3"]\n'
        "}\n\n"
        f"Nội dung tài liệu:\n{full_text[:4000]}"
    )

    summary_json = {
        "executive_summary": "Tài liệu học vụ đã được dịch và phân tích chi tiết bằng mô hình AI.",
        "key_findings": [
            "Tài liệu phân tích các quy chế và yêu cầu học vụ của trường.",
            "Hệ thống hóa cấu trúc kỹ thuật và giải pháp triển khai.",
            "Đảm bảo tính chính xác học thuật và từ điển chuyên ngành IUH."
        ]
    }

    try:
        client = get_gemini_client()
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        if res and res.text:
            import json
            parsed = json.loads(res.text)
            if "executive_summary" in parsed and "key_findings" in parsed:
                summary_json = parsed
    except Exception as e:
        logger.warning(f"Không thể sinh JSON tóm tắt từ Gemini, dùng fallback default: {e}")

    return summary_json, detected_glossary
