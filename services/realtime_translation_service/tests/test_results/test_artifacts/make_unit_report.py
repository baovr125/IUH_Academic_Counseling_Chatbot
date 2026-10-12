"""Chạy một nhóm unit test bằng pytest (JUnit XML + coverage) và sinh report Markdown có bảng từng test case.

    python make_unit_report.py <group_key>

Kết quả trong bảng lấy từ JUnit XML do pytest thực sự sinh ra; không tự điền PASS.
Mô tả test case lấy từ docstring (nếu có) hoặc tên hàm test.
"""
import ast
import datetime
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

SERVICE = r"G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\realtime_translation_service"
REPORT_DIR = r"G:\Khoa_Luan\word\Report\realtime_translation"
ART = os.path.join(REPORT_DIR, "test_artifacts")

GROUPS = {
    "4.1": dict(
        title="Language Detection", report="unit_test_language_detection_report.md", prefix="UT-LD",
        files=["tests/unit/test_language_detection.py", "tests/unit/test_detection_status.py"],
        cov=["app.services.language_detection", "app.services.fasttext_detector"],
        isolation="fastText `lid.176.ftz` và Lingua là model cục bộ thật (không có mạng); các nhánh lỗi engine được mock bằng `unittest.mock.patch`. Không gọi LLM/Redis/Supabase.",
    ),
    "4.2": dict(
        title="Domain Detection (parser, quyết định, chỉ mục từ điển, prompt)", report="unit_test_domain_detection_report.md",
        prefix="UT-DD", files=["tests/unit/test_domain_detection.py"],
        cov=["app.services.domain_detection", "app.services.domain_index"],
        isolation="Hàm thuần, dữ liệu từ điển giả trong test; không I/O.",
    ),
    "4.3": dict(
        title="LLM streaming, fallback, điều phối dịch chuyên ngành", report="unit_test_llm_streaming_fallback_report.md",
        prefix="UT-LF", files=["tests/unit/test_domain_translation.py", "tests/unit/test_terminology_backend.py"],
        cov=["app.services.domain_llm", "app.services.domain_translation"],
        isolation="Client Groq/Gemini giả (async generator), `stream_llm` giả, NLLB giả (`_nllb` hoặc `get_nllb_translator`), chỉ mục từ điển giả, cache Redis bị patch. Không gọi mạng.",
    ),
    "4.4": dict(
        title="Nạp từ điển, cache, định tuyến /text (bổ sung đợt này)", report="unit_test_dictionary_cache_routing_report.md",
        prefix="UT-DC", files=["tests/unit/test_domain_support_units.py", "tests/unit/test_redis_cache.py"],
        cov=["app.services.domain_service", "app.services.domain_dict_service", "app.services.cache_service",
             "app.services.domain_index", "app.services.translation_service"],
        isolation="Redis, Supabase (kể cả phân trang `.range()`), `collect_domain_translation`, `aresolve_source_language`, NLLB đều là `MagicMock`/`AsyncMock`.",
    ),
    "4.5": dict(
        title="TTS (chọn giọng, hash CAS) và phân tích từ", report="unit_test_tts_word_analysis_report.md",
        prefix="UT-TW", files=["tests/unit/test_voice_resolver.py", "tests/unit/test_cas_deduplication.py",
                               "tests/unit/test_word_analysis.py"],
        cov=["app.routers.translation", "app.services.word_analysis_service"],
        isolation="`test_word_analysis.py` gọi endpoint qua FastAPI TestClient trong tiến trình, NLP nặng và Groq bị mock (fixture `mock_heavy_nlp`); MinIO/RabbitMQ/model preload bị patch trong `conftest.py`.",
    ),
    "4.6": dict(
        title="Công cụ đo (metric, kiểm tra dataset)", report="unit_test_evaluation_tooling_report.md",
        prefix="UT-EV", files=["tests/unit/test_detection_metrics_phase2.py", "tests/unit/test_benchmark_contract.py"],
        cov=["evaluation.metrics.compute_detection_metrics", "evaluation.metrics.calibrate_thresholds",
             "evaluation.validate_dataset"],
        isolation="Hàm thuần trên dữ liệu nhỏ trong test và các file dataset trong repo.",
    ),
}


def docstrings(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[(node.name, item.name)] = ast.get_docstring(item) or ""
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.setdefault((None, node.name), ast.get_docstring(node) or "")
    return out


def humanize(name):
    return name.replace("test_", "", 1).replace("_", " ")


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def main():
    key = sys.argv[1]
    g = GROUPS[key]
    tag = key.replace(".", "_")
    junit = os.path.join(ART, f"unit_{tag}_junit.xml")
    covjson = os.path.join(ART, f"unit_{tag}_coverage.json")
    log = os.path.join(ART, f"unit_{tag}_pytest.log")
    cmd = [sys.executable, "-m", "pytest", *g["files"], "-p", "no:cacheprovider", "-o", "addopts=", "-q", "-rA",
           f"--junitxml={junit}", *[f"--cov={c}" for c in g["cov"]], "--cov-report=term",
           f"--cov-report=json:{covjson}"]
    started = datetime.datetime.now().astimezone()
    proc = subprocess.run(cmd, cwd=SERVICE, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    ended = datetime.datetime.now().astimezone()
    open(log, "w", encoding="utf-8").write(proc.stdout + "\n" + proc.stderr)

    root = ET.parse(junit).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    docs = {}
    for f in g["files"]:
        docs[f] = docstrings(os.path.join(SERVICE, f))
    rows, counts = [], {"PASS": 0, "FAIL": 0, "SKIPPED": 0, "BLOCKED": 0, "PENDING": 0}
    for i, case in enumerate(suite.iter("testcase"), 1):
        classname = case.get("classname", "")
        name = case.get("name", "")
        base = re.sub(r"\[.*\]$", "", name)
        param = name[len(base):].strip("[]")
        mod_parts = classname.split(".")
        cls = mod_parts[-1] if mod_parts[-1].startswith("Test") else None
        file = "/".join(p for p in (mod_parts[:-1] if cls else mod_parts)) + ".py"
        doc = docs.get(file, {}).get((cls, base), "")
        desc = doc.split("\n")[0] if doc else humanize(base)
        # Lưu ý: Element không có con được đánh giá là False, nên phải so sánh với None.
        failure = case.find("failure")
        if failure is None:
            failure = case.find("error")
        skipped = case.find("skipped")
        if failure is not None:
            status, actual = "FAIL", "Không đạt"
            reason = esc((failure.get("message") or "")[:200])
        elif skipped is not None:
            status, actual, reason = "SKIPPED", "Không chạy", esc(skipped.get("message") or "")
        else:
            status, actual, reason = "PASS", "Đúng kỳ vọng (mọi assert đạt)", ""
        counts[status] += 1
        func = f"{os.path.basename(file)}::{cls + '::' if cls else ''}{base}"
        rows.append(f"| {g['prefix']}-{i:03d} | `{func}` | {esc(desc)} | Mock/isolation theo mục A | "
                    f"{esc(param) or '—'} | Các assert trong test đều đúng | {actual} | {status} | {reason or '—'} | "
                    f"`test_artifacts/unit_{tag}_junit.xml` ({float(case.get('time', 0)) * 1000:.0f} ms) |")

    cov = json.load(open(covjson, encoding="utf-8"))
    cov_rows = []
    for path, data in sorted(cov["files"].items()):
        s = data["summary"]
        cov_rows.append(f"| `{path.replace(os.sep, '/')}` | {s['num_statements']} | {s['missing_lines']} | {s['percent_covered']:.1f}% |")
    total = cov["totals"]["percent_covered"]
    ran = counts["PASS"] + counts["FAIL"]
    rate = f"{counts['PASS'] / ran * 100:.1f}%" if ran else "n/a"
    versions = subprocess.run([sys.executable, "-c", "import pytest,pytest_asyncio,coverage,platform;"
                               "print(platform.python_version(), pytest.__version__, pytest_asyncio.__version__, coverage.__version__)"],
                              capture_output=True, text=True).stdout.split()
    md = f"""# Unit Test — {g['title']} (Phase {key})

## A. Thông tin chạy test

| Mục | Nội dung |
|---|---|
| Thời gian | {started:%Y-%m-%d %H:%M:%S} → {ended:%H:%M:%S} ({started:%z}) |
| Mã nguồn | Git HEAD `7e846214` + thay đổi chưa commit; vân tay `app/**/*.py` = `5ac072ebfd20` |
| Python / runner | Python {versions[0]}, pytest {versions[1]}, pytest-asyncio {versions[2]} (`asyncio_mode=auto`), coverage {versions[3]} (pytest-cov) |
| Lệnh chạy chính xác | `cd services/realtime_translation_service && python {' '.join(cmd[1:]).replace(ART, '<report>/test_artifacts')}` |
| File test | {', '.join('`' + f + '`' for f in g['files'])} |
| Cô lập dependency | {g['isolation']} |
| Bằng chứng | JUnit XML `test_artifacts/unit_{tag}_junit.xml`, log `test_artifacts/unit_{tag}_pytest.log`, coverage `test_artifacts/unit_{tag}_coverage.json` |
| Mã thoát pytest | {proc.returncode} |

Ghi chú cột: *Expected Result* của từng test là các khẳng định (`assert`) viết trong test; *Actual Result* lấy từ JUnit XML.
*Precondition* chung của nhóm ghi ở hàng "Cô lập dependency".

## B. Bảng test case chi tiết

| Test Case ID | Module/Function | Test Case Description | Precondition | Test Data | Expected Result | Actual Result | Status | Failure Reason | Evidence/Log |
|---|---|---|---|---|---|---|---|---|---|
""" + "\n".join(rows) + f"""

## C. Tổng kết

| Tổng | PASS | FAIL | PENDING | BLOCKED | SKIPPED | Tỉ lệ pass (trên số đã chạy) |
|---:|---:|---:|---:|---:|---:|---:|
| {sum(counts.values())} | {counts['PASS']} | {counts['FAIL']} | {counts['PENDING']} | {counts['BLOCKED']} | {counts['SKIPPED']} | {rate} |

**Coverage (dòng lệnh) của các module được nhắm:** tổng {total:.1f}%

| File | Số lệnh | Lệnh chưa chạy | Coverage |
|---|---:|---:|---:|
""" + "\n".join(cov_rows) + "\n"
    path = os.path.join(REPORT_DIR, g["report"])
    open(path, "w", encoding="utf-8").write(md)
    print(json.dumps({"group": key, "report": g["report"], "counts": counts, "coverage": round(total, 1),
                      "returncode": proc.returncode}, ensure_ascii=False))


if __name__ == "__main__":
    main()
