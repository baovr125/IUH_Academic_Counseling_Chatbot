import os
import re
import httpx
from typing import List, Optional
from app.utils.logger import logger

OLLAMA_DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

SYSTEM_TRANSLATION_PROMPT = (
    "Bạn là chuyên gia dịch thuật tài liệu khoa học và báo cáo kỹ thuật chuyên nghiệp. "
    "Nhiệm vụ: Dịch văn bản từ ngôn ngữ nguồn sang ngôn ngữ đích được yêu cầu.\n"
    "RẤT QUAN TRỌNG (TUYỆT ĐỐI TUÂN THỦ DỰNG CẤU TRÚC BẢNG & ĐỊNH DẠNG):\n"
    "1. VỚI BẢNG BIỂU MARKDOWN (dạng `| cột 1 | cột 2 |`): Bạn BẮT BUỘC phải giữ nguyên tất cả ký tự gạch đứng `|`, số lượng cột, dòng tiêu đề và dòng phân cách `|---|---|`. Chỉ dịch chữ tiếng Anh thành tiếng Việt trong từng ô cell. KHÔNG ĐƯỢC xóa gộp dòng hay làm hỏng cấu trúc bảng.\n"
    "2. TUYỆT ĐỐI KHÔNG ĐƯỢC làm thay đổi hoặc xóa bỏ các thẻ Markdown (như #, *, danh sách, bảng HTML/MD, liên kết ảnh `![](...)`).\n"
    "3. TUYỆT ĐỐI KHÔNG dịch hoặc làm sai lệch các mã công thức toán học LaTeX (như $...$, $$...$$, \\begin{equation}...\\end{equation}).\n"
    "4. Chỉ dịch chữ văn bản từ ngôn ngữ nguồn thành ngôn ngữ đích, không tự ý thêm bớt ý, không kèm lời chào hay giải thích thừa."
)


def get_ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", OLLAMA_DEFAULT_HOST).rstrip("/")

def estimate_tokens(text: str) -> int:
    """Ước tính số token dựa trên số từ (1 từ ~ 1.3 token cho tiếng Anh/Việt)"""
    words = len(text.split())
    return int(words * 1.3)

def split_text_into_batches(text: str, max_tokens: int = 1200) -> List[str]:
    """
    Tách file raw.md theo dấu ngắt dòng kép \\n\\n (Paragraph boundary).
    Gộp các đoạn nhỏ thành từng Batch từ 1000 - 1500 tokens để tránh tràn context Ollama.
    """
    paragraphs = re.split(r'\n\s*\n', text)
    batches: List[str] = []
    current_batch: List[str] = []
    current_token_count = 0

    for para in paragraphs:
        para_trimmed = para.strip()
        if not para_trimmed:
            continue
            
        para_tokens = estimate_tokens(para_trimmed)

        # Nếu 1 paragraph quá lớn (> max_tokens), tự tách nhỏ hơn theo dòng
        if para_tokens > max_tokens:
            lines = para_trimmed.split("\n")
            for line in lines:
                line_tokens = estimate_tokens(line)
                if current_token_count + line_tokens > max_tokens and current_batch:
                    batches.append("\n\n".join(current_batch))
                    current_batch = [line]
                    current_token_count = line_tokens
                else:
                    current_batch.append(line)
                    current_token_count += line_tokens
            continue

        if current_token_count + para_tokens > max_tokens and current_batch:
            batches.append("\n\n".join(current_batch))
            current_batch = [para_trimmed]
            current_token_count = para_tokens
        else:
            current_batch.append(para_trimmed)
            current_token_count += para_tokens

    if current_batch:
        batches.append("\n\n".join(current_batch))

    return batches

def call_ollama_generate(
    prompt: str,
    system_instruction: str = SYSTEM_TRANSLATION_PROMPT,
    model: str = OLLAMA_DEFAULT_MODEL,
    host: Optional[str] = None,
    timeout_seconds: float = 120.0
) -> str:
    """
    Gửi request synchronous tới Ollama REST API (/api/generate).
    """
    target_host = (host or get_ollama_host()).rstrip("/")
    url = f"{target_host}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_instruction,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9
        }
    }

    headers = {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true"
    }

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()

    except Exception as e:
        logger.exception(f"Lỗi khi gọi Ollama API tại {url}: {e}")
        raise RuntimeError(f"Không thể kết nối dịch thuật Ollama API: {e}")

def translate_markdown_document_ollama(
    md_text: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    model: str = OLLAMA_DEFAULT_MODEL,
    max_batch_tokens: int = 1200
) -> str:
    """
    Thực hiện dịch Batching tài liệu Markdown qua Ollama API:
    1. Tách md_text thành các Batches (1000 - 1500 tokens).
    2. Gửi tuần tự các Batch lên Ollama qua REST API.
    3. Ghép các Batch trả về thành file translated.md.
    """
    if not md_text.strip():
        return ""

    batches = split_text_into_batches(md_text, max_tokens=max_batch_tokens)
    logger.info(f"Đã phân chia tài liệu Markdown thành {len(batches)} batches để dịch qua Ollama ({model}).")

    translated_batches: List[str] = []

    for idx, batch in enumerate(batches, 1):
        logger.info(f"Đang dịch Batch {idx}/{len(batches)} ({estimate_tokens(batch)} tokens)...")
        
        prompt = (
            f"Hãy dịch đoạn văn bản Markdown sau từ tiếng {source_lang.upper()} sang tiếng {target_lang.upper()}.\n"
            f"Lưu ý: Giữ nguyên thẻ Markdown và LaTeX.\n\n"
            f"Text:\n{batch}"
        )

        try:
            translated_text = call_ollama_generate(prompt=prompt, model=model)
            if translated_text:
                translated_batches.append(translated_text)
            else:
                translated_batches.append(batch) # Fallback if empty response
        except Exception as e:
            logger.warning(f"Lỗi khi dịch batch {idx}, sử dụng văn bản gốc fallback: {e}")
            translated_batches.append(batch)

    translated_md = "\n\n".join(translated_batches)
    return translated_md
