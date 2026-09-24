import httpx
import json
import time
import os
import asyncio
from datetime import datetime
import re
from dotenv import load_dotenv

# Load environment variables (4 levels up from tests/integration/run_benchmark.py)
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.env")))

API_URL = "http://localhost:8003/api/v1/translate/text"
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "test_data.json")
REPORT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../realtime_qa_report.md"))

def extract_tags(html):
    return re.findall(r'<\/?[\w\s="\'\-]+>', html)

def evaluate_html_integrity(original, translated):
    if not original or not translated:
        return True
    
    orig_tags = extract_tags(original)
    trans_tags = extract_tags(translated)
    
    # Simple count check
    return len(orig_tags) == len(trans_tags)

async def test_text_endpoint(client, test_case):
    payload = {
        "text": test_case["input"],
        "source_lang": "en",
        "target_lang": "vi",
        "domain": test_case.get("domain", "")
    }
    start = time.perf_counter()
    try:
        response = await client.post(API_URL, json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        latency = (time.perf_counter() - start) * 1000
        actual = data.get("data", {}).get("translated_text", "")
        
        is_html_preserved = True
        if test_case["type"] == "html":
            is_html_preserved = evaluate_html_integrity(test_case["input"], actual)
            
        return {
            "id": test_case["id"],
            "type": test_case["type"],
            "domain": test_case.get("domain", ""),
            "input": test_case["input"],
            "expected": test_case["expected"],
            "actual": actual,
            "html_preserved": is_html_preserved,
            "latency_ms": round(latency, 2),
            "error": None
        }
    except Exception as e:
        return {
            "id": test_case["id"],
            "type": test_case["type"],
            "domain": test_case.get("domain", ""),
            "input": test_case["input"],
            "expected": test_case["expected"],
            "actual": None,
            "html_preserved": False,
            "latency_ms": None,
            "error": str(e)
        }

async def run_evaluation():
    if not os.path.exists(TEST_DATA_PATH):
        print(f"Test data not found at {TEST_DATA_PATH}")
        return

    # Mock Redis dictionary for "IT" and "Kinh tế" domain
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.hset("domain_dict:IT", mapping={
            "prerequisite": "môn học tiên quyết",
            "data structures": "cấu trúc dữ liệu",
            "database query": "truy vấn cơ sở dữ liệu"
        })
        r.hset("domain_dict:Kinh tế", mapping={
            "inflation rate": "tỷ lệ lạm phát",
            "stock market": "thị trường chứng khoán"
        })
        print("Successfully injected mock domain dictionary into Redis.")
    except Exception as e:
        print(f"Warning: Could not inject mock data into Redis: {e}")

    with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"Starting evaluation with {len(test_cases)} test cases...")
    
    results = []
    async with httpx.AsyncClient() as client:
        for case in test_cases:
            try:
                import redis
                r = redis.Redis(host="localhost", port=6379, decode_responses=True)
                cache_key = f"en_vi_{case['input'].strip().lower()}"
                r.delete(f"trans:{cache_key}")
            except Exception:
                pass
                
            print(f"Running [{case['id']}]...")
            res = await test_text_endpoint(client, case)
            results.append(res)
            print(f"  Latency: {res['latency_ms']} ms")
            
    # Generate Report
    generate_markdown_report(results)

def calculate_percentiles(latencies):
    if not latencies:
        return 0, 0, 0
    s = sorted(latencies)
    return s[len(s)//2], s[int(len(s)*0.9)], s[int(len(s)*0.99)]

def generate_markdown_report(results):
    nllb_latencies = [r['latency_ms'] for r in results if not r['domain'] and r['latency_ms'] is not None]
    llm_latencies = [r['latency_ms'] for r in results if r['domain'] and r['latency_ms'] is not None]
    
    nllb_p50, nllb_p90, nllb_p99 = calculate_percentiles(nllb_latencies)
    llm_p50, llm_p90, llm_p99 = calculate_percentiles(llm_latencies)
    
    html_cases = [r for r in results if r['type'] == 'html']
    html_preservation = sum(1 for r in html_cases if r['html_preserved']) / len(html_cases) * 100 if html_cases else 100
    
    errors = [r for r in results if not r['html_preserved'] or r['error']]

    report = f"""# 📊 Realtime Translation Service - Tự Đánh Giá (Manual Review Report)
Thời gian chạy: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 1. Tổng Quan (Executive Summary)
- Tổng số Testcase: {len(results)}
- Tỷ lệ bảo toàn cấu trúc HTML: {html_preservation:.1f}%

## 2. Hiệu Năng Tốc Độ (Latency Benchmarks)
| Luồng Dịch | P50 (ms) | P90 (ms) | P99 (ms) | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| **NLLB (Default)** | {nllb_p50}ms | {nllb_p90}ms | {nllb_p99}ms | Dịch tốc độ cao |
| **Gemini Bypass (IT/Econ)** | {llm_p50}ms | {llm_p90}ms| {llm_p99}ms | Ép từ điển chuyên ngành |

## 3. Lỗi Kỹ Thuật (HTML/Timeout Errors)
"""
    if errors:
        for err in errors:
            report += f"- **ID:** `{err['id']}`\n"
            report += f"  - **Lỗi:** {'Lỗi kết nối/Timeout' if err['error'] else 'Cấu trúc HTML Bị Hỏng'}\n"
            report += f"  - **Câu gốc:** `{err['input']}`\n"
            report += f"  - **Bản dịch:** `{err['actual']}`\n"
    else:
        report += "*(Không có testcase nào bị hỏng thẻ HTML hoặc lỗi mạng)*\n"

    report += """
## 4. Đối Chiếu Kết Quả Dịch Thuật (Translation Review)
| Thể Loại | Tốc độ | Cấu trúc HTML | Câu Gốc (Original Text) | Bản Dịch Thực Tế (Actual Translation) |
| :--- | :--- | :--- | :--- | :--- |
"""
    for r in results:
        html_status = "✅ Giữ nguyên" if r['html_preserved'] else "❌ Rách tag" if r['type'] == 'html' else "N/A"
        domain = r['domain'] if r['domain'] else r['type']
        
        # Format text code block syntax for markdown table compatibility
        orig_text = r['input'].replace('\\n', '<br>').replace('|', '\\|')
        act_text = str(r['actual']).replace('\\n', '<br>').replace('|', '\\|')
        
        report += f"| {domain} | {r['latency_ms']}ms | {html_status} | `{orig_text}` | `{act_text}` |\n"

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())

