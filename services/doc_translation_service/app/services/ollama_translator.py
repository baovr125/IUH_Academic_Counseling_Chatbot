import os
import re
import httpx
from typing import List, Optional
from app.utils.logger import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError)),
    reraise=True
)
def call_ollama_generate(
    prompt: str,
    system_instruction: str = SYSTEM_TRANSLATION_PROMPT,
    model: str = OLLAMA_DEFAULT_MODEL,
    host: Optional[str] = None,
    timeout_seconds: float = 120.0
) -> str:
    """
    Gửi request synchronous tới Ollama REST API (/api/generate).
    Tự động thử lại (retry) tối đa 3 lần nếu gặp lỗi Timeout/Connection Error.
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

from typing import List, Optional, Callable, Tuple

def translate_markdown_document_ollama(
    md_text: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    model: str = OLLAMA_DEFAULT_MODEL,
    max_batch_tokens: int = 1200,
    status_callback: Optional[Callable[[int, str, str], None]] = None
) -> Tuple[str, str]:
    """
    Thực hiện dịch Batching tài liệu Markdown qua Ollama API (kèm Gemini fallback):
    1. Tách md_text thành các Batches (1000 - 1500 tokens).
    2. Gửi tuần tự các Batch lên Ollama/Gemini API.
    3. Trả về (translated_md, model_used_name).
    """
    if not md_text.strip():
        return "", "N/A"

    batches = split_text_into_batches(md_text, max_tokens=max_batch_tokens)
    total_batches = len(batches)
    logger.info(f"Đã phân chia tài liệu Markdown thành {total_batches} batches để dịch.")

    translated_batches: List[str] = []
    models_used = set()

    for idx, batch in enumerate(batches, 1):
        progress = 40 + int(40 * (idx / total_batches))
        logger.info(f"Đang dịch Batch {idx}/{total_batches} ({estimate_tokens(batch)} tokens)...")
        
        prompt = (
            f"Hãy dịch đoạn văn bản Markdown sau từ tiếng {source_lang.upper()} sang tiếng {target_lang.upper()}.\n"
            f"Lưu ý: Giữ nguyên thẻ Markdown và LaTeX.\n\n"
            f"Text:\n{batch}"
        )

        try:
            current_msg = f"Đang dịch Batch {idx}/{total_batches} qua Ollama ({model})..."
            if status_callback:
                status_callback(progress, current_msg, f"Ollama ({model})")
            
            translated_text = call_ollama_generate(prompt=prompt, model=model)
            if translated_text:
                translated_batches.append(translated_text)
                models_used.add(f"Ollama ({model})")
            else:
                translated_batches.append(batch)
        except Exception as e:
            fallback_msg = f"Đang dịch Batch {idx}/{total_batches} qua Gemini 2.5 Flash API..."
            logger.warning(f"Lỗi khi dịch batch {idx} với Ollama ({e}). Tự động dùng Gemini 2.5 Flash API...")
            if status_callback:
                status_callback(progress, fallback_msg, "Gemini 2.5 Flash")
            try:
                from app.services.translator import translate_chunk_with_gemini
                gemini_text = translate_chunk_with_gemini(
                    text=batch,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
                translated_batches.append(gemini_text)
                models_used.add("Gemini 2.5 Flash")
            except Exception as gemini_err:
                logger.error(f"Lỗi cả Gemini API fallback: {gemini_err}")
                translated_batches.append(batch)

    translated_md = "\n\n".join(translated_batches)
    model_name = " & ".join(sorted(models_used)) if models_used else "Gemini 2.5 Flash"
    return translated_md, model_name
