"""Chạy bộ kiểm thử pytest của từng service (không cần Docker) và ghi tóm tắt vào eval/results/test_suites.json.

Chỉ đọc mã dự án: dùng -p no:cacheprovider và PYTHONDONTWRITEBYTECODE để không tạo tệp trong thư mục dự án.
Kết quả chi tiết từng service lưu ở eval/results/junit_<service>.xml.
Cách dùng: python -B -X utf8 eval/run_test_suites.py [service ...]   (mặc định: cả năm service)
"""
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(r"B:\KhoaLuan\IUH_Academic_Counseling_Chatbot")
OUT = Path(__file__).parent / "results"
SERVICES = ["auth_service", "academic_chatbot_service", "flashcard_service",
            "realtime_translation_service", "doc_translation_service"]
TIMEOUT_S = 1200

OUT.mkdir(exist_ok=True)
wanted = sys.argv[1:] or SERVICES
summary_path = OUT / "test_suites.json"
summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}

for name in wanted:
    cwd = REPO / "services" / name
    xml = OUT / f"junit_{name}.xml"
    cmd = [sys.executable, "-B", "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "--no-header",
           "--tb=line", "-o", "addopts=", f"--junitxml={xml}"]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=TIMEOUT_S, encoding="utf-8", errors="replace")
        timed_out = False
    except subprocess.TimeoutExpired:
        proc, timed_out = None, True
    elapsed = round(time.time() - t0, 1)

    entry = {"elapsed_s": elapsed, "timed_out": timed_out, "failed_tests": []}
    if xml.exists():
        suite = ET.parse(xml).getroot()
        suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
        entry.update({k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")})
        entry["passed"] = entry["tests"] - entry["failures"] - entry["errors"] - entry["skipped"]
        for case in suite.iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                entry["failed_tests"].append(f"{case.get('classname')}::{case.get('name')}")
    elif proc is not None:
        entry["note"] = (proc.stdout + proc.stderr)[-400:]
    summary[name] = entry
    print(name, {k: v for k, v in entry.items() if k != "failed_tests"}, entry["failed_tests"][:6], flush=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
