"""
test_tunnel_connectivity.py
===========================
Script chạy từ Local để verify tunnel Kaggle → Ollama hoạt động đúng
trước khi deploy thật hoặc để debug khi gặp lỗi.

Cách dùng:
    python test_tunnel_connectivity.py
    python test_tunnel_connectivity.py --host https://bondless-immerse-paternal.ngrok-free.dev
    python test_tunnel_connectivity.py --host https://xxx.trycloudflare.com --model qwen2.5:7b
"""
import argparse, os, sys, time
import httpx

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def get_args():
    parser = argparse.ArgumentParser(description="Test Kaggle Ollama tunnel connectivity")
    parser.add_argument(
        "--host",
        default=os.getenv("OLLAMA_HOST", "https://bondless-immerse-paternal.ngrok-free.dev"),
        help="Public URL của tunnel (default: OLLAMA_HOST env hoặc ngrok static domain)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        help="Tên model Ollama để test inference (default: OLLAMA_MODEL env hoặc qwen2.5:7b)",
    )
    return parser.parse_args()


BYPASS_HEADERS = {
    "ngrok-skip-browser-warning": "true",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

SEP = "=" * 60

def log_ok(msg): print(f"  ✅ {msg}")
def log_err(msg): print(f"  ❌ {msg}")
def log_warn(msg): print(f"  ⚠️  {msg}")


def test_health(host: str, is_vllm: bool = False) -> bool:
    """Test health endpoint (GET /v1/models cho vLLM hoặc GET /api/tags cho Ollama)"""
    endpoint = f"{host}/v1/models" if is_vllm else f"{host}/api/tags"
    print(f"\n[TEST 1] Health check → GET {endpoint}")
    headers = dict(BYPASS_HEADERS)
    if is_vllm:
        headers["Authorization"] = f"Bearer {os.getenv('VLLM_API_KEY', 'sk-dummy')}"

    try:
        t0 = time.time()
        r = httpx.get(endpoint, headers=headers, timeout=20.0, verify=False)
        latency = (time.time() - t0) * 1000
        if r.status_code != 200:
            log_err(f"HTTP {r.status_code} — Body: {r.text[:200]}")
            return False
        content_type = r.headers.get("content-type", "")
        if "application/json" not in content_type:
            log_err(f"Nhận được non-JSON (content-type={content_type}). Tunnel đang trả HTML!")
            log_err(f"Body đầu tiên: {r.text[:300]}")
            return False
        data = r.json()
        if is_vllm:
            models = [m.get("id", "") for m in data.get("data", [])]
        else:
            models = [m.get("name", "") for m in data.get("models", [])]
        log_ok(f"HTTP 200 | Latency: {latency:.0f}ms | Models: {models}")
        return True
    except httpx.TimeoutException:
        log_err("Timeout 20s — tunnel không respond hoặc LLM server đang khởi động.")
        return False
    except Exception as e:
        log_err(f"Exception: {e}")
        return False


def test_inference(host: str, model: str, is_vllm: bool = False) -> bool:
    """Test inference (vLLM /v1/chat/completions hoặc Ollama /api/generate)"""
    headers = {**BYPASS_HEADERS, "Content-Type": "application/json"}
    if is_vllm:
        url = f"{host}/v1/chat/completions"
        headers["Authorization"] = f"Bearer {os.getenv('VLLM_API_KEY', 'sk-dummy')}"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Reply with exactly two words: System Ready"}],
            "temperature": 0.0
        }
    else:
        url = f"{host}/api/generate"
        payload = {
            "model": model,
            "prompt": "Reply with exactly two words: System Ready",
            "stream": False,
            "options": {"temperature": 0.0}
        }

    print(f"\n[TEST 2] Inference → POST {url} (model={model})")
    try:
        t0 = time.time()
        r = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=90.0,
            verify=False,
        )
        latency = (time.time() - t0) * 1000
        if r.status_code != 200:
            log_err(f"HTTP {r.status_code} — Body: {r.text[:200]}")
            return False
        content_type = r.headers.get("content-type", "")
        if "application/json" not in content_type:
            log_err(f"Non-JSON response (content-type={content_type}). Tunnel trả HTML!")
            log_err(f"Body: {r.text[:300]}")
            return False
        data = r.json()
        if is_vllm:
            response_text = data["choices"][0]["message"]["content"].strip()
        else:
            response_text = data.get("response", "").strip()
        log_ok(f"HTTP 200 | Latency: {latency:.0f}ms | Response: '{response_text}'")
        return True
    except httpx.TimeoutException:
        log_err("Timeout 90s — model đang load hoặc GPU bị quá tải.")
        return False
    except Exception as e:
        log_err(f"Exception: {e}")
        return False


def test_content_type_protection(host: str) -> None:
    """Kiểm tra xem tunnel có trả về HTML warning page không"""
    print(f"\n[TEST 3] Content-Type guard — không có bypass headers")
    try:
        r = httpx.get(
            f"{host}/api/tags",
            headers={"User-Agent": "curl/7.68.0"},  # minimal headers
            timeout=10.0,
            verify=False,
        )
        ct = r.headers.get("content-type", "")
        if "text/html" in ct:
            log_warn(f"Không có bypass headers → tunnel trả HTML (content-type={ct})")
            log_warn(f"Điều này BÌNH THƯỜNG — code đã xử lý bằng bypass headers đúng.")
        else:
            log_ok(f"Tunnel không chặn request cơ bản (content-type={ct})")
    except Exception as e:
        log_warn(f"Không test được (lỗi: {e})")


def main():
    args = get_args()
    host = args.host.rstrip("/")
    model = args.model
    is_vllm = os.getenv("USE_VLLM", "false").lower() == "true"
    engine_name = "vLLM" if is_vllm else "Ollama"

    print(SEP)
    print(f"🧪 Kaggle Tunnel Connectivity Test ({engine_name})")
    print(f"   HOST    : {host}")
    print(f"   MODEL   : {model}")
    print(f"   ENGINE  : {engine_name}")
    print(SEP)

    results = []

    # Test 1: Health
    ok1 = test_health(host, is_vllm=is_vllm)
    results.append((f"Health check ({engine_name})", ok1))

    # Test 2: Inference (chỉ chạy nếu health pass)
    if ok1:
        ok2 = test_inference(host, model, is_vllm=is_vllm)
        results.append((f"Inference ({engine_name})", ok2))
    else:
        results.append((f"Inference ({engine_name})", None))
        print(f"\n[TEST 2] Bỏ qua inference vì health check đã FAIL.")

    # Test 3: Content-type guard info
    test_content_type_protection(host)

    # Summary
    print(f"\n{SEP}")
    print("📊 KẾT QUẢ:")
    all_pass = True
    for name, result in results:
        if result is True:
            print(f"  ✅ PASS  — {name}")
        elif result is False:
            print(f"  ❌ FAIL  — {name}")
            all_pass = False
        else:
            print(f"  ⏭️  SKIP  — {name}")

    print(SEP)
    if all_pass:
        print("🎉 TẤT CẢ TEST PASS! Tunnel hoạt động tốt.")
        print(f"   Cập nhật .env: OLLAMA_HOST=\"{host}\"")
        sys.exit(0)
    else:
        print("💥 MỘT SỐ TEST FAIL. Kiểm tra lại tunnel trên Kaggle.")
        print("   Các nguyên nhân thường gặp:")
        print("   1. Kaggle notebook chưa chạy cell [4] (ngrok tunnel)")
        print("   2. Kaggle session đã hết thời gian (timeout)")
        print("   3. OLLAMA_HOST trong .env trỏ sai URL")
        sys.exit(1)


if __name__ == "__main__":
    main()
