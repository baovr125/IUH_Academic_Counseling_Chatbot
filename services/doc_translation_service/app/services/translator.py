import os
from typing import List, Dict, Any
from google import genai
from app.services.glossary_service import scan_document_for_glossary, get_glossary_prompt_instructions
from app.utils.logger import logger
from tenacity import retry, stop_after_attempt, wait_exponential


def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Thiếu biến môi trường GEMINI_API_KEY")
    return genai.Client(api_key=api_key)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=5, min=15, max=65),
    reraise=True
)
def translate_chunk_with_gemini(
    text: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    parent_title: str = "",
    ancestors: List[str] = None,
    glossary: List[Dict[str, str]] = None,
    glossary_context: str = ""
) -> str:
    """
    Dịch 1 đoạn văn bản sử dụng Gemini 2.5 Flash.
    Kết hợp Từ điển Thuật ngữ IUH tĩnh (glossary_service) và Glossary động trích xuất từ tài liệu (glossary_context).
    Tự động retry nếu gặp lỗi 429 Rate Limit.
    """
    if not text.strip():
        return ""

    ancestor_str = " > ".join(ancestors) if ancestors else ""
    context_prefix = f"Vị trí mục: [{ancestor_str} > {parent_title}]" if parent_title else ""

    # Kết hợp cả 2 nguồn glossary: IUH static dictionary + dynamic từ tài liệu
    glossary_instr = get_glossary_prompt_instructions(glossary or [])
    if glossary_context:
        dynamic_gloss = f"\nThuật ngữ chuyên ngành bổ sung được trích xuất từ tài liệu:\n{glossary_context}"
        glossary_instr = glossary_instr + dynamic_gloss if glossary_instr else dynamic_gloss

    system_instruction = (
        "Bạn là Chuyên gia Dịch thuật Báo cáo Khoa học và Tài liệu Học vụ chuyên nghiệp.\n"
        "Nhiệm vụ: Dịch chính xác văn bản từ ngôn ngữ nguồn sang ngôn ngữ đích được yêu cầu, giữ nguyên văn phong học thuật chuẩn mực.\n"
        f"{glossary_instr}\n"
        "QUY TẮC CỨNG BẮT BUỘC:\n"
        "1. BẢO TOÀN TÊN TÁC GIẢ & TÊN RIÊNG: TUYỆT ĐỐI KHÔNG dịch tên người, tên tác giả (ví dụ: Yann LeCun, Geoffrey Hinton, Vaswani, John Smith). Giữ nguyên 100% dạng chữ gốc Latin.\n"
        "2. BẢO TOÀN TÊN TRƯỜNG, VIỆN NGHIÊN CỨU & CƠ QUAN: Giữ nguyên tên cơ quan/trường học/viện nghiên cứu (ví dụ: Stanford University, Carnegie Mellon University, MIT, Google DeepMind, OpenAI, Microsoft Research).\n"
        "3. BẢO TOÀN ĐỊA DANH & ĐỊA ĐIỂM: Giữ nguyên tên địa danh trong địa chỉ tác giả hoặc tên phòng lab (ví dụ: Palo Alto, California; Seattle, WA; Zurich, Switzerland; Beijing, China).\n"
        "4. BẢO TOÀN TÊN BỘ DỮ LIỆU, MÔ HÌNH, THUẬT TOÁN, CÔNG NGHỆ & BENCHMARKS: Giữ nguyên tên gốc tiếng Anh (ví dụ: BERT, GPT-4, Transformer, ImageNet, GLUE, BLEU score, PyTorch, LoRA, Attention mechanism).\n"
        "5. BẢO TOÀN TRÍCH DẪN KHOA HỌC & LIÊN KẾT: Giữ nguyên cấu trúc trích dẫn tham chiếu như `(Tác_giả et al., Năm)` (ví dụ: `(Vaswani et al., 2017)`), các mã số `[1]`, `[2-4]`, email, URL, DOI.\n"
        "6. GIỮ NGUYÊN cấu trúc định dạng markdown (tiêu đề #, danh sách, công thức LaTeX, mã số code block, bảng biểu).\n"
        "7. Trả về DUY NHẤT phần văn bản đã dịch, không thêm bớt ý, không kèm lời chào hay giải thích thừa."
    )

    prompt = (
        f"Dịch đoạn văn bản sau từ {source_lang.upper()} sang {target_lang.upper()}:\n"
        f"{context_prefix}\n\n"
        f"--- NỘI DUNG GỐC ---\n"
        f"{text}\n"
        f"--- BẢN DỊCH {target_lang.upper()} ---"
    )

    client = get_gemini_client()
    res = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"system_instruction": system_instruction, "temperature": 0.2}
    )
    if res and res.text:
        return res.text.strip()
    return text
