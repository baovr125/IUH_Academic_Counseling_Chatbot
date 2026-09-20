import httpx
import json
import time
import os
import asyncio

API_URL = "http://localhost:8003/api/v1/translate/text"
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "test_data.json")

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
        return {
            "id": test_case["id"],
            "type": test_case["type"],
            "input": test_case["input"],
            "expected": test_case["expected"],
            "actual": actual,
            "status": "PASS" if actual == test_case["expected"] else "FAIL",
            "latency_ms": round(latency, 2),
            "error": None
        }
    except Exception as e:
        return {
            "id": test_case["id"],
            "type": test_case["type"],
            "input": test_case["input"],
            "expected": test_case["expected"],
            "actual": None,
            "status": "ERROR",
            "latency_ms": None,
            "error": str(e)
        }

async def run_evaluation():
    if not os.path.exists(TEST_DATA_PATH):
        print(f"Test data not found at {TEST_DATA_PATH}")
        return

    # Mock Redis dictionary for "IT" domain
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.hset("domain_dict:IT", mapping={
            "prerequisite": "môn học tiên quyết",
            "data structures": "cấu trúc dữ liệu"
        })
        print("Successfully injected mock domain dictionary into Redis.")
    except Exception as e:
        print(f"Warning: Could not inject mock data into Redis: {e}")

    with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"Starting evaluation with {len(test_cases)} test cases...")
    print("=" * 80)
    
    results = []
    async with httpx.AsyncClient() as client:
        for case in test_cases:
            # Bypass cache intentionally to ensure we test the translation pipeline
            try:
                import redis
                r = redis.Redis(host="localhost", port=6379, decode_responses=True)
                # clear the cache key so it actually translates
                cache_key = f"en_vi_{case['input'].strip().lower()}"
                r.delete(f"trans:{cache_key}")
            except Exception:
                pass
                
            print(f"Running [{case['id']}]...")
            res = await test_text_endpoint(client, case)
            results.append(res)
            print(f"  Status: {res['status']}")
            print(f"  Latency: {res['latency_ms']} ms")
            if res['status'] != 'PASS':
                print(f"  Expected: {res['expected']}")
                print(f"  Actual:   {res['actual']}")
            if res['error']:
                print(f"  Error: {res['error']}")
            print("-" * 40)
            
    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    
    print("=" * 80)
    print("EVALUATION SUMMARY")
    print(f"Total: {len(test_cases)} | Pass: {passed} | Fail: {failed} | Error: {errors}")
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), "eval_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
