import os
import re
import httpx
import threading
import concurrent.futures
from typing import List, Optional, Tuple, Callable
from app.utils.logger import logger
from app.services.pdf_parser import markdown_hierarchical_chunking
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

OLLAMA_DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")

SYSTEM_TRANSLATION_PROMPT = (
    "<instructions>\n"
    "Bạn là chuyên gia dịch thuật tài liệu khoa học và báo cáo kỹ thuật chuyên nghiệp. "
    "Nhiệm vụ: Dịch văn bản từ ngôn ngữ nguồn sang ngôn ngữ đích được yêu cầu, giữ nguyên văn phong học thuật chuẩn mực.\n"
    "QUY TẮC CỨNG BẮT BUỘC (HARD RULES):\n"
    "1. BẢO TOÀN TÊN TÁC GIẢ & TÊN RIÊNG: TUYỆT ĐỐI KHÔNG dịch tên người, tên tác giả (ví dụ: Yann LeCun, Geoffrey Hinton, Vaswani, John Smith). Giữ nguyên 100% dạng chữ gốc Latin.\n"
    "2. BẢO TOÀN TÊN TRƯỜNG, VIỆN NGHIÊN CỨU & CƠ QUAN: Giữ nguyên tên cơ quan/trường học/viện nghiên cứu (ví dụ: Stanford University, Carnegie Mellon University, MIT, Google DeepMind, OpenAI, Microsoft Research).\n"
    "3. BẢO TOÀN ĐỊA DANH & ĐỊA ĐIỂM: Giữ nguyên tên địa danh trong địa chỉ tác giả hoặc tên phòng lab (ví dụ: Palo Alto, California; Seattle, WA; Zurich, Switzerland; Beijing, China).\n"
    "4. BẢO TOÀN TÊN BỘ DỮ LIỆU, MÔ HÌNH, THUẬT TOÁN, CÔNG NGHỆ & BENCHMARKS: Giữ nguyên tên gốc tiếng Anh (ví dụ: BERT, GPT-4, Transformer, ImageNet, GLUE, BLEU score, PyTorch, LoRA, Attention mechanism).\n"
    "5. BẢO TOÀN TRÍCH DẪN KHOA HỌC & LIÊN KẾT: Giữ nguyên cấu trúc trích dẫn tham chiếu như `(Tác_giả et al., Năm)` (ví dụ: `(Vaswani et al., 2017)`), các mã số `[1]`, `[2-4]`, email, URL, DOI.\n"
    "6. VỚI BẢNG BIỂU MARKDOWN (dạng `| cột 1 | cột 2 |`): BẮT BUỘC giữ nguyên tất cả ký tự gạch đứng `|`, số lượng cột, và dòng phân cách `|---|---|`. Chỉ dịch chữ tiếng Anh thành tiếng Việt trong từng ô cell. KHÔNG ĐƯỢC làm hỏng cấu trúc bảng.\n"
    "7. CẤU TRÚC MARKDOWN & CÔNG THỨC: TUYỆT ĐỐI KHÔNG xóa hoặc sửa các thẻ Markdown (#, ##, *, danh sách, liên kết ảnh `![](...)`) và công thức toán học LaTeX ($...$, $$...$$) hoặc code block (```...```).\n"
    "8. Chỉ dịch chữ văn bản, không tự ý thêm bớt ý, không kèm lời chào hay giải thích thừa.\n"
    "</instructions>\n"
    "<glossary>\n"
    "BẮT BUỘC sử dụng từ điển thuật ngữ chuyên ngành sau để dịch (nếu có):\n"
    "{glossary_context}\n"
    "</glossary>"
)


def get_ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", OLLAMA_DEFAULT_HOST).rstrip("/")


_TUNNEL_BYPASS_HEADERS = {
    "ngrok-skip-browser-warning": "true",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def check_ollama_health(host: Optional[str] = None) -> bool:
    """
    Kiểm tra xem LLM server (vLLM hoặc Ollama) và tunnel đang sống.
    - vLLM: GET /v1/models
    - Ollama: GET /api/tags
    """
    target = (host or get_ollama_host()).rstrip("/")
    is_vllm = os.getenv("USE_VLLM", "false").lower() == "true"
    endpoint = f"{target}/v1/models" if is_vllm else f"{target}/api/tags"
    headers = dict(_TUNNEL_BYPASS_HEADERS)
    if is_vllm:
        headers["Authorization"] = f"Bearer {os.getenv('VLLM_API_KEY', 'sk-dummy')}"

    try:
        with httpx.Client(timeout=15.0, verify=False) as client:
            r = client.get(endpoint, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if is_vllm:
                    models = [m.get("id", "") for m in data.get("data", [])]
                    logger.info(f"✅ vLLM health OK tại {target} — models: {models}")
                else:
                    models = [m.get("name", "") for m in data.get("models", [])]
                    logger.info(f"✅ Ollama health OK tại {target} — models: {models}")
                return True
            logger.warning(f"⚠️  LLM API health check trả về HTTP {r.status_code} tại {endpoint}")
            return False
    except Exception as exc:
        logger.warning(f"⚠️  Không thể kết nối LLM API/tunnel tại {endpoint}: {exc}")
        return False


def estimate_tokens(text: str) -> int:
    """Ước tính số token dựa trên số từ (1 từ ~ 1.3 token cho tiếng Anh/Việt)"""
    words = len(text.split())
    return int(words * 1.3)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=3, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError, RuntimeError)),
    reraise=True
)
def call_ollama_generate(
    prompt: str,
    system_instruction: str = SYSTEM_TRANSLATION_PROMPT,
    model: str = OLLAMA_DEFAULT_MODEL,
    host: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    format: Optional[str] = None
) -> str:
    """
    Gửi request synchronous tới Ollama REST API (/api/generate) hoặc vLLM (/v1/chat/completions).
    """
    if timeout_seconds is None:
        timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
    target_host = (host or get_ollama_host()).rstrip("/")
    
    is_vllm = os.getenv("USE_VLLM", "false").lower() == "true"

    if is_vllm:
        url = f"{target_host}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "top_p": 0.9
        }
        if format in ["json", "json_object"]:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('VLLM_API_KEY', 'sk-dummy')}",
            **_TUNNEL_BYPASS_HEADERS,
        }
    else:
        url = f"{target_host}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_gpu": 99,
                "num_ctx": 3072,
                "num_thread": 2,
            }
        }
        if format:
            payload["format"] = format
        headers = {
            "Content-Type": "application/json",
            **_TUNNEL_BYPASS_HEADERS,
        }

    try:
        with httpx.Client(timeout=timeout_seconds, verify=False, http2=False) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            
            content_type = resp.headers.get("content-type", "")
            if "application/json" not in content_type:
                logger.error(f"Tunnel trả về non-JSON response (content-type={content_type}). Body: {resp.text[:300]}")
                raise RuntimeError(f"Tunnel trả về response không phải JSON. content-type={content_type}")

            data = resp.json()
            
            if is_vllm:
                return data["choices"][0]["message"]["content"].strip()
            else:
                return data.get("response", "").strip()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} khi gọi {url}: {e.response.text[:200]}")
        raise RuntimeError(f"HTTP {e.response.status_code} từ LLM API tunnel: {e}")
    except (httpx.TimeoutException, httpx.RequestError):
        raise
    except Exception as e:
        logger.exception(f"Lỗi không xác định khi gọi API tại {url}: {e}")
        raise RuntimeError(f"Không thể kết nối dịch thuật LLM API: {e}")


def translate_markdown_document_ollama(
    md_text: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    model: str = OLLAMA_DEFAULT_MODEL,
    max_batch_tokens: int = 1200,
    status_callback: Optional[Callable[[int, str, str], None]] = None,
    glossary_context: str = ""
) -> Tuple[str, str]:
    """
    Thực hiện dịch Batching tài liệu Markdown qua Ollama/vLLM API với xử lý song song.
    Thread-safe: sử dụng threading.Lock() để bảo vệ biến đếm tiến độ.
    """
    if not md_text.strip():
        return "", "N/A"

    is_vllm = os.getenv("USE_VLLM", "false").lower() == "true"
    engine_label = "vLLM" if is_vllm else "Ollama"

    if not check_ollama_health():
        ollama_host = get_ollama_host()
        logger.error(
            f"❌ {engine_label}/tunnel KHÔNG KHẢ DỤNG tại {ollama_host}. "
            f"Bỏ qua toàn bộ {engine_label}, chuyển 100% sang Gemini fallback."
        )
        _ollama_reachable = False
    else:
        _ollama_reachable = True

    batches = markdown_hierarchical_chunking(md_text, max_tokens=max_batch_tokens)
    total_batches = len(batches)
    logger.info(f"Đã phân chia tài liệu Markdown thành {total_batches} batches để dịch song song ({engine_label}).")

    translated_batches: List[str] = [""] * total_batches
    models_used = set()

    system_instruction = SYSTEM_TRANSLATION_PROMPT.format(glossary_context=glossary_context or "Không có")

    # Thread-safe progress counter
    completed = 0
    _progress_lock = threading.Lock()

    def translate_single_batch(idx: int, batch: str) -> Tuple[int, str, str]:
        prompt = (
            f"Hãy dịch đoạn văn bản Markdown sau từ tiếng {source_lang.upper()} sang tiếng {target_lang.upper()}.\n"
            f"Lưu ý: Giữ nguyên thẻ Markdown và LaTeX.\n\n"
            f"Text:\n{batch}"
        )
        
        try:
            if not _ollama_reachable:
                raise RuntimeError(f"{engine_label}/tunnel không khả dụng (đã xác định bởi health check)")

            translated_text = call_ollama_generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=model,
                timeout_seconds=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180")),
            )
            model_used_name = f"{engine_label} ({model})"
            if not translated_text:
                translated_text = batch
        except Exception as e:
            logger.warning(f"Lỗi khi dịch batch {idx+1} với {engine_label} ({e}). Tự động dùng Gemini 2.5 Flash API...")
            try:
                from app.services.translator import translate_chunk_with_gemini
                translated_text = translate_chunk_with_gemini(
                    text=batch,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    glossary_context=glossary_context  # Truyền glossary xuống Gemini fallback
                )
                model_used_name = "Gemini 2.5 Flash"
            except Exception as gemini_err:
                logger.error(f"Lỗi cả Gemini API fallback ở batch {idx+1}: {gemini_err}")
                translated_text = batch
                model_used_name = "Fallback Failed"

        # Thread-safe increment
        nonlocal completed
        with _progress_lock:
            completed += 1
            current_completed = completed

        progress = 40 + int(40 * (current_completed / total_batches))
        msg = f"Đã dịch xong Batch {current_completed}/{total_batches} qua {model_used_name}..."
        if status_callback:
            status_callback(progress, msg, model_used_name)
            
        return idx, translated_text, model_used_name

    worker_count = 4 if is_vllm else 2
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(translate_single_batch, i, batch) for i, batch in enumerate(batches)]
        for future in concurrent.futures.as_completed(futures):
            idx, t_text, m_name = future.result()
            translated_batches[idx] = t_text
            if m_name != "Fallback Failed":
                models_used.add(m_name)

    translated_md = "\n\n".join(translated_batches)
    model_name = " & ".join(sorted(models_used)) if models_used else "Gemini 2.5 Flash"
    return translated_md, model_name
