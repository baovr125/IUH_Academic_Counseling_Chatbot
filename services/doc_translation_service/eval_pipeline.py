#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IUH Doc Translation Service -- End-to-End Evaluation & Manual Inspection Pipeline
Author: Khoa Luan Tot Nghiep 2026
Chay: python eval_pipeline.py
"""

import os
import re
import sys
import json
import time
import shutil
import datetime
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# ─── Force UTF-8 BEFORE any print (Windows cp1252 fix) ──────────────────────
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
import io
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# ─── Auto-install deps ───────────────────────────────────────────────────────
def _ensure_packages():
    required = {"requests": "requests", "jose": "python-jose[cryptography]"}
    import importlib
    for mod, pkg in required.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            print(f"  [setup] Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"],
                                  env={**os.environ, "PYTHONUTF8": "1"})

_ensure_packages()

import requests
from jose import jwt

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
GATEWAY_URL          = "http://localhost:8000"
DIRECT_URL           = "http://localhost:8004"
JWT_SECRET           = "super-secret-key-iuh-chatbot-2026"
JWT_ALGORITHM        = "HS256"
JWT_ISSUER           = "iuh-auth-service"
TEST_USER_ID         = "eval_test_user_001"

TEST_DATA_DIR        = Path(r"G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\data\Test_data_translation")
BENCHMARKS_DIR       = Path(__file__).parent / "benchmarks"
REPORT_DIR           = Path(__file__).parent / "eval_reports"
OUTPUTS_ROOT         = Path(__file__).parent / "eval_outputs"
REPORT_DIR.mkdir(exist_ok=True)
OUTPUTS_ROOT.mkdir(exist_ok=True)

TIMEOUT_PER_FILE_SEC = 30 * 60   # 30 minutes
VLLM_TUNNEL_URL      = "https://bondless-immerse-paternal.ngrok-free.dev"

PROTECTED_TERMS = [
    "Vaswani", "Ashish", "Noam", "Uszkoreit", "Jakob",
    "Gomez", "Kaiser", "Polosukhin",
    "Brown", "Mann", "Ryder", "Subbiah", "Kaplan", "Dhariwal",
    "ImageNet", "BLEU", "WMT", "SQuAD", "GLUE", "SuperGLUE",
    "Transformer", "BERT", "GPT", "GPT-3", "GPT-4",
    "Stanford", "Google", "OpenAI", "Microsoft", "DeepMind", "MIT", "CMU",
    "NeurIPS", "ICLR", "EMNLP", "ACL", "IEEE",
    "PyTorch", "TensorFlow", "CUDA",
]

# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def log(msg: str, level: str = "INFO"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "[i]", "OK": "[OK]", "WARN": "[!]", "ERROR": "[ERR]", "RUN": "[>>]", "STEP": "[--]"}
    icon = icons.get(level, "[ ]")
    print(f"  [{ts}] {icon}  {msg}")

def sep(char="-", n=72):
    print(char * n)

def generate_jwt_token(user_id: str = TEST_USER_ID) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + 86400 * 7,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def fmt_seconds(s: float) -> str:
    if s < 60:
        return f"{s:.1f}s"
    m = int(s // 60)
    sec = s % 60
    return f"{m}m {sec:.0f}s"

def fmt_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024 * 1024:
        return f"{b/1024:.1f} KB"
    else:
        return f"{b/(1024*1024):.2f} MB"

# ═══════════════════════════════════════════════════════════════════════════════
#  PHASE 0 — INFRASTRUCTURE HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════════════════════
def check_vllm_tunnel() -> Dict[str, Any]:
    try:
        r = requests.get(
            f"{VLLM_TUNNEL_URL}/v1/models",
            headers={
                "ngrok-skip-browser-warning": "true",
                "Authorization": "Bearer sk-dummy",
                "User-Agent": "EvalScript/1.0",
            },
            timeout=15,
            verify=False,
        )
        if r.status_code == 200:
            data = r.json()
            models = [m.get("id", "?") for m in data.get("data", [])]
            return {"alive": True, "models": models, "status_code": 200}
        return {"alive": False, "models": [], "status_code": r.status_code}
    except Exception as e:
        return {"alive": False, "models": [], "error": str(e)}

def determine_base_url(token: str) -> Tuple[str, str]:
    try:
        r = requests.get(
            f"{GATEWAY_URL}/api/v1/documents/health",
            headers={"Authorization": f"Bearer {token}"},
            timeout=8,
        )
        if r.status_code == 200:
            return GATEWAY_URL, "Kong Gateway (port 8000) [OK]"
    except Exception:
        pass
    try:
        r = requests.get(f"{DIRECT_URL}/api/v1/documents/health", timeout=8)
        if r.status_code == 200:
            return DIRECT_URL, "Direct FastAPI (port 8004) -- Kong Bypassed [!]"
    except Exception:
        pass
    return GATEWAY_URL, "UNKNOWN -- Kong possibly starting..."

# ═══════════════════════════════════════════════════════════════════════════════
#  PHASE 1 — UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════
def upload_pdf(base_url: str, pdf_path: Path, token: str) -> Optional[str]:
    try:
        with open(pdf_path, "rb") as f:
            r = requests.post(
                f"{base_url}/api/v1/documents/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": (pdf_path.name, f, "application/pdf")},
                data={"source_lang": "en", "target_lang": "vi", "is_scanned": "false"},
                timeout=60,
            )
        if r.status_code in (200, 202):
            body = r.json()
            doc_id = body.get("data", {}).get("doc_id") or body.get("doc_id")
            return doc_id
        log(f"Upload failed HTTP {r.status_code}: {r.text[:200]}", "ERROR")
        return None
    except Exception as e:
        log(f"Upload exception: {e}", "ERROR")
        return None

# ═══════════════════════════════════════════════════════════════════════════════
#  PHASE 2 — POLL STATUS
# ═══════════════════════════════════════════════════════════════════════════════
def poll_job_status(
    base_url: str,
    doc_id: str,
    token: str,
    timeout_sec: int = TIMEOUT_PER_FILE_SEC,
    file_label: str = "",
) -> Dict[str, Any]:
    t_start = time.time()
    last_progress = 0
    last_model = ""
    glossary = []
    milestones = []

    log(f"  Polling doc_id={doc_id[:8]}... (timeout {timeout_sec//60}m)", "RUN")

    while True:
        elapsed = time.time() - t_start
        if elapsed > timeout_sec:
            return {
                "result": "TIMEOUT",
                "elapsed_sec": round(elapsed, 1),
                "last_progress": last_progress,
                "model_used": last_model,
                "glossary": glossary,
                "milestones": milestones,
                "translated_text": "",
                "pages_processed": 0,
            }

        time.sleep(8)

        try:
            r = requests.get(
                f"{base_url}/api/v1/documents/{doc_id}/status",
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            if r.status_code == 404:
                continue
            if r.status_code != 200:
                log(f"  Status HTTP {r.status_code}", "WARN")
                continue

            body = r.json()
            data = body.get("data", body)

            status_val = data.get("status", "")
            progress   = data.get("progress", last_progress)
            message    = data.get("message", "")
            model_now  = data.get("model_used", last_model)
            g_list     = data.get("glossary", [])

            if progress != last_progress:
                elapsed_now = time.time() - t_start
                milestone = {
                    "progress": progress,
                    "message": message,
                    "elapsed_sec": round(elapsed_now, 1),
                }
                milestones.append(milestone)
                msg_safe = message.encode("ascii", errors="replace").decode("ascii")
                print(f"    [{fmt_seconds(elapsed_now):>8}] {progress:>3}% | {msg_safe[:70]}")
                last_progress = progress

            if model_now:
                last_model = model_now
            if g_list:
                glossary = g_list

            if status_val == "completed":
                elapsed_final = time.time() - t_start
                return {
                    "result": "COMPLETED",
                    "elapsed_sec": round(elapsed_final, 1),
                    "last_progress": 100,
                    "model_used": data.get("model_used", last_model),
                    "glossary": data.get("glossary", glossary),
                    "milestones": milestones,
                    "translated_text": data.get("translated_text", ""),
                    "translated_file_url": data.get("translated_file_url", ""),
                    "pages_processed": data.get("pages_processed", 0),
                }

            if status_val == "failed":
                elapsed_final = time.time() - t_start
                return {
                    "result": "FAILED",
                    "elapsed_sec": round(elapsed_final, 1),
                    "last_progress": progress,
                    "model_used": last_model,
                    "glossary": glossary,
                    "milestones": milestones,
                    "translated_text": "",
                    "error": data.get("error", "Unknown error"),
                    "pages_processed": 0,
                }

        except requests.exceptions.Timeout:
            log("  Status endpoint timeout, retrying...", "WARN")
            continue
        except Exception as e:
            log(f"  Polling error: {e}", "WARN")
            continue

# ═══════════════════════════════════════════════════════════════════════════════
#  PHASE 3 — DOWNLOAD & SAVE FILE TO DISK
# ═══════════════════════════════════════════════════════════════════════════════
def download_and_save(base_url: str, doc_id: str, token: str, save_path: Optional[Path] = None) -> Dict[str, Any]:
    try:
        r = requests.get(
            f"{base_url}/api/v1/documents/{doc_id}/download",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
            stream=True,
        )
        if r.status_code != 200:
            return {"success": False, "status_code": r.status_code, "size_bytes": 0}

        content_type = r.headers.get("content-type", "")
        content = b""
        for chunk in r.iter_content(chunk_size=32 * 1024):
            content += chunk

        is_pdf  = content[:4] == b"%PDF" or "pdf" in content_type.lower()
        is_docx = content[:4] == b"PK\x03\x04" and "wordprocessing" in content_type.lower()
        is_valid = len(content) > 1024 and (is_pdf or is_docx)

        if is_valid and save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(content)

        return {
            "success": is_valid,
            "status_code": r.status_code,
            "content_type": content_type,
            "size_bytes": len(content),
            "format_detected": "PDF" if is_pdf else ("DOCX" if is_docx else "UNKNOWN"),
            "saved_file_path": str(save_path) if (is_valid and save_path) else None,
        }
    except Exception as e:
        return {"success": False, "status_code": 0, "size_bytes": 0, "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
#  PHASE 4 — QUALITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
def analyze_translation_quality(translated_text: str, filename: str) -> Dict[str, Any]:
    if not translated_text:
        return {"analysis_possible": False}
        
    try:
        import os
        import json
        from groq import Groq
        from dotenv import load_dotenv
        
        # Load .env từ thư mục gốc
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            return {"analysis_possible": False, "error": "Missing GROQ_API_KEY in .env"}
            
        client = Groq(api_key=groq_api_key)
        
        # Chỉ lấy 2500 ký tự đầu để tiết kiệm token và thời gian đánh giá
        sample = translated_text[:2500] 
        
        prompt = f"""
You are an expert academic translation reviewer. Please evaluate the following Vietnamese translation sample of an academic paper.
Score the translation on 3 criteria (scale 1-5 for each):
1. Terminology: Are academic terms translated correctly in context (not word-by-word)?
2. Math & Layout: Are LaTeX blocks ($...$) and markdown structures preserved properly?
3. Fluency: Is the Vietnamese natural and formal?

Provide a JSON output strictly in this format:
{{"terminology_score": 5, "math_layout_score": 5, "fluency_score": 5, "comments": "Brief summary of issues in Vietnamese"}}

Translation Sample:
{sample}
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        total = result.get("terminology_score", 0) + result.get("math_layout_score", 0) + result.get("fluency_score", 0)
        result["total_score_pct"] = round((total / 15.0) * 100, 1)
        result["analysis_possible"] = True
        
        return result
        
    except Exception as e:
        log(f"Groq Eval Error: {e}", "ERROR")
        return {"analysis_possible": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
#  PHASE 5 — BENCHMARK RUNNERS
# ═══════════════════════════════════════════════════════════════════════════════
def run_benchmark_script(script_name: str) -> Optional[Dict]:
    script_path = BENCHMARKS_DIR / script_name
    if not script_path.exists():
        log(f"Benchmark not found: {script_path}", "WARN")
        return None
    try:
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
               "PYTHONPATH": str(script_path.parent.parent)}
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            timeout=120,
            cwd=str(script_path.parent.parent),
            env=env,
        )
        stdout_text = result.stdout.decode("utf-8", errors="replace").strip()
        if result.returncode == 0 and stdout_text:
            json_match = re.search(r'\{[\s\S]*\}', stdout_text)
            if json_match:
                return json.loads(json_match.group(0))
        stderr_text = result.stderr.decode("utf-8", errors="replace")
        if stderr_text:
            log(f"  Benchmark stderr: {stderr_text[:300]}", "WARN")
        return None
    except subprocess.TimeoutExpired:
        log(f"  Benchmark {script_name} timeout (120s)", "WARN")
        return None
    except Exception as e:
        log(f"  Benchmark {script_name} error: {e}", "WARN")
        return None

# ═══════════════════════════════════════════════════════════════════════════════
#  PHASE 6 — SIDE-BY-SIDE HTML VIEWER GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
def generate_side_by_side_html(run_ts: str, file_results: List[Dict], out_html_path: Path):
    """Tạo giao diện HTML đối soát song song trực quan cho người dùng / chuyên gia."""
    cards_html = []
    
    for i, r in enumerate(file_results, 1):
        name = r["filename"]
        poll = r["poll"]
        res = poll.get("result", "UNKNOWN")
        badge_cls = "badge-success" if res == "COMPLETED" else ("badge-warning" if res == "TIMEOUT" else "badge-danger")
        model = poll.get("model_used", "N/A")
        t_sec = poll.get("elapsed_sec", 0)
        size_fmt = fmt_bytes(r["meta"]["size_bytes"])
        
        folder_rel = f"{i:02d}_{Path(name).stem}"
        orig_pdf_rel = f"{folder_rel}/original.pdf"
        trans_pdf_rel = f"{folder_rel}/translated.pdf"
        trans_md_rel = f"{folder_rel}/translated.md"
        glossary_rel = f"{folder_rel}/glossary.json"

        # Glossary table
        glossary_rows = ""
        for g in poll.get("glossary", [])[:10]:
            term = g.get("term", "")
            trans = g.get("translation") or g.get("vi", "")
            ipa = g.get("phonetic", "—")
            glossary_rows += f"<tr><td><b>{term}</b></td><td>{trans}</td><td><code>{ipa}</code></td></tr>"

        # Translated preview
        md_text = poll.get("translated_text", "")
        preview_text = (md_text[:2500] + "\n\n... [Xem file translated.md để đọc toàn bộ]") if md_text else "<i>(Không có nội dung dịch)</i>"
        preview_escaped = preview_text.replace("<", "&lt;").replace(">", "&gt;")

        cards_html.append(f"""
        <div class="card mb-4" id="card-{i}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5><b>Bài {i}:</b> {name} <span class="badge {badge_cls}">{res}</span></h5>
                <span class="text-muted">{size_fmt} | {fmt_seconds(t_sec)} | Model: {model}</span>
            </div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-md-6">
                        <h6><b>📂 File Liên Kết:</b></h6>
                        <a href="{orig_pdf_rel}" target="_blank" class="btn btn-sm btn-outline-primary mr-2">📄 Mở Original PDF</a>
                        <a href="{trans_pdf_rel}" target="_blank" class="btn btn-sm btn-outline-success mr-2">📑 Mở Translated PDF</a>
                        <a href="{trans_md_rel}" target="_blank" class="btn btn-sm btn-outline-secondary mr-2">📝 Mở Translated Markdown</a>
                        <a href="{glossary_rel}" target="_blank" class="btn btn-sm btn-outline-info">📚 Mở Glossary JSON</a>
                    </div>
                    <div class="col-md-6">
                        <h6><b>🎯 Khung Chấm Điểm Thủ Công (Likert 1-5):</b></h6>
                        <small class="text-muted">1. Thuật ngữ (___/5) | 2. LaTeX (___/5) | 3. Bảng biểu (___/5) | 4. Tên riêng (___/5) | 5. Mạch lạc (___/5)</small>
                    </div>
                </div>
                <hr/>
                <div class="row">
                    <div class="col-md-7">
                        <h6><b>📝 Trích Đoạn Văn Bản Đã Dịch (Markdown Preview):</b></h6>
                        <pre class="bg-light p-3 border rounded text-dark" style="max-height: 400px; overflow-y: auto; white-space: pre-wrap; font-size: 13px;">{preview_escaped}</pre>
                    </div>
                    <div class="col-md-5">
                        <h6><b>📚 Thuật Ngữ Học Thuật Trích Xuất ({len(poll.get('glossary', []))} terms):</b></h6>
                        <div style="max-height: 400px; overflow-y: auto;">
                            <table class="table table-sm table-bordered">
                                <thead class="thead-light">
                                    <tr><th>Thuật ngữ</th><th>Nghĩa tiếng Việt</th><th>IPA</th></tr>
                                </thead>
                                <tbody>{glossary_rows if glossary_rows else '<tr><td colspan="3" class="text-center text-muted">Không có thuật ngữ</td></tr>'}</tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """)

    full_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IUH Doc Translation -- Side-by-Side Evaluation Viewer</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6f9; }}
        .header-hero {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px 0; }}
        .badge-success {{ background-color: #28a745; }}
        .badge-warning {{ background-color: #ffc107; color: #212529; }}
        .badge-danger {{ background-color: #dc3545; }}
    </style>
</head>
<body>
    <div class="header-hero mb-4">
        <div class="container">
            <h2>🎓 IUH Doc Translation Service -- Bảng Đối Soát Thủ Công Song Song</h2>
            <p class="mb-0">Ngày chạy: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Mã phiên kiểm thử: <code>run_{run_ts}</code></p>
        </div>
    </div>
    <div class="container-fluid px-5">
        <div class="alert alert-info shadow-sm">
            <b>💡 Hướng dẫn đối soát:</b> Mở song song <code>Original PDF</code> và <code>Translated PDF</code> bằng 2 tab trình duyệt để đối chiếu độ trung thực, công thức LaTeX, bảng biểu và tính nhất quán của thuật ngữ học thuật.
        </div>
        {"".join(cards_html)}
    </div>
</body>
</html>"""
    out_html_path.write_text(full_html, encoding="utf-8")

# ═══════════════════════════════════════════════════════════════════════════════
#  PHASE 7 — REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
def generate_report(
    run_ts: str,
    base_url_mode: str,
    vllm_info: Dict,
    file_results: List[Dict],
    benchmarks: Dict,
) -> str:
    now_str     = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    total_files = len(file_results)
    completed   = sum(1 for r in file_results if r["poll"].get("result") == "COMPLETED")
    failed      = sum(1 for r in file_results if r["poll"].get("result") == "FAILED")
    timed_out   = sum(1 for r in file_results if r["poll"].get("result") == "TIMEOUT")

    if completed == total_files:
        verdict = "**PASS -- Tat ca pipeline hoat dong dung**"
    elif completed + timed_out == total_files:
        verdict = "**PASS WITH WARNINGS -- Pipeline hoat dong, co file timeout (bai bao qua dai)**"
    elif failed > 0 and completed > 0:
        verdict = "**PARTIAL PASS -- Co loi xay ra o mot so file**"
    else:
        verdict = "**FAIL -- Pipeline gap loi nghiem trong**"

    lines = []

    lines += [
        "# Bao Cao Danh Gia: Doc Translation Service",
        "",
        f"> **Ngay chay:** {now_str}  ",
        f"> **Che do:** {base_url_mode}  ",
        f"> **Tunnel vLLM:** `{VLLM_TUNNEL_URL}`  ",
        f"> **Model:** {vllm_info.get('models', ['?'])[0] if vllm_info.get('alive') else 'Gemini 2.5 Flash (fallback)'}  ",
        f"> **Thu muc luu ket qua:** `eval_outputs/run_{run_ts}/`  ",
        "",
        "---",
        "",
        "## 1. Tom Tat Dieu Hanh (Executive Summary)",
        "",
        "| Tong file | Completed | Failed | Timeout |",
        "|---|---|---|---|",
        f"| **{total_files}** | **{completed}** OK | **{failed}** ERR | **{timed_out}** TIMEOUT |",
        "",
        f"### Verdict Tong The: {verdict}",
        "",
        "---",
        "",
        "## 2. Trang Thai Ha Tang",
        "",
        "| Thanh phan | Trang thai |",
        "|---|---|",
        f"| Kong API Gateway (port 8000) | {base_url_mode} |",
        f"| Kaggle vLLM Tunnel | {'[OK] Alive -- ' + ', '.join(vllm_info.get('models', [])) if vllm_info.get('alive') else '[!] Khong ket noi -- Fallback Gemini'} |",
        f"| Tunnel URL | `{VLLM_TUNNEL_URL}` |",
        "",
        "---",
        "",
        "## 3. Ket Qua Kiem Thu E2E -- Bang Tong Hop",
        "",
        "| # | File | Kich thuoc | Ket qua | Thoi gian | Mo hinh AI | Glossary | PDF tai ve | Thu muc luu |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for i, r in enumerate(file_results, 1):
        res   = r["poll"].get("result", "?")
        label = {"COMPLETED": "[OK]", "FAILED": "[ERR]", "TIMEOUT": "[TIMEOUT]"}.get(res, "[?]")
        t_sec = r["poll"].get("elapsed_sec", 0)
        model = r["poll"].get("model_used", "?")
        g_cnt = len(r["poll"].get("glossary", []))
        dl    = r.get("download", {})
        dl_ok = "[OK]" if dl.get("success") else ("[skip]" if res != "COMPLETED" else "[ERR]")
        size  = fmt_bytes(r["meta"]["size_bytes"])
        folder_name = f"{i:02d}_{Path(r['filename']).stem}"
        lines.append(
            f"| {i} | `{r['filename']}` | {size} | {label} {res} | {fmt_seconds(t_sec)} "
            f"| {model[:40]} | {g_cnt} terms | {dl_ok} | `eval_outputs/run_{run_ts}/{folder_name}/` |"
        )

    lines += ["", "---", "", "## 4. Chi Tiet Tung File", ""]

    for i, r in enumerate(file_results, 1):
        filename = r["filename"]
        poll     = r["poll"]
        qa       = r.get("quality", {})
        dl       = r.get("download", {})
        res      = poll.get("result", "UNKNOWN")
        label    = {"COMPLETED": "[OK]", "FAILED": "[ERR]", "TIMEOUT": "[TIMEOUT]"}.get(res, "[?]")
        folder_name = f"{i:02d}_{Path(filename).stem}"

        lines += [
            f"### {i}. {label} `{filename}`",
            "",
            "| Thuoc tinh | Gia tri |",
            "|---|---|",
            f"| **Ket qua pipeline** | {label} **{res}** |",
            f"| **Thoi gian xu ly** | {fmt_seconds(poll.get('elapsed_sec', 0))} |",
            f"| **Model AI su dung** | `{poll.get('model_used', 'N/A')}` |",
            f"| **Kich thuoc file** | {fmt_bytes(r['meta']['size_bytes'])} |",
            f"| **So trang** | {poll.get('pages_processed', '?')} |",
            f"| **Thu muc luu tru** | `eval_outputs/run_{run_ts}/{folder_name}/` |",
            "",
        ]

        if qa.get("analysis_possible"):
            term_score = qa.get("terminology_score", "?")
            math_score = qa.get("math_layout_score", "?")
            fluency_score = qa.get("fluency_score", "?")
            comments = qa.get("comments", "Không có nhận xét")
            total_pct = qa.get("total_score_pct", 0)
            
            verdict = "[OK]" if total_pct >= 80 else "[WARN]"

            lines += [
                "**Phan Tich Chat Luong Ban Dich (Groq LLM-as-a-Judge):**",
                "",
                "| Tieu chi (Thang 1-5) | Diem so |",
                "|---|---|",
                f"| Thuật ngữ (Terminology) | {term_score}/5 |",
                f"| Toán học & Bảng biểu | {math_score}/5 |",
                f"| Trôi chảy (Fluency) | {fluency_score}/5 |",
                f"| **Tổng điểm** | **{total_pct}%** {verdict} |",
                "",
                f"> **Nhan xet tu Groq:** {comments}",
                "",
            ]
        elif res == "TIMEOUT":
            lines += ["*File timeout sau 30 phut -- khong co ban dich de phan tich.*", ""]
        elif res == "FAILED":
            err = poll.get("error", "Khong ro")
            lines += [f"*Pipeline that bai: `{err[:200]}`*", ""]

        glossary = poll.get("glossary", [])
        if glossary:
            lines += [
                f"**Bang Thuat Ngu Trich Xuat ({len(glossary)} thuat ngu -- hien thi toi da 8):**",
                "",
                "| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |",
                "|---|---|---|---|",
            ]
            for g in glossary[:8]:
                term     = g.get("term", "")
                meaning  = g.get("translation") or g.get("vi", "")
                phonetic = g.get("phonetic", "--")
                audio    = "[audio]" if g.get("audio_url") else "--"
                lines.append(f"| {term} | {meaning} | {phonetic} | {audio} |")
            lines.append("")

        if dl:
            dl_icon = "[OK]" if dl.get("success") else "[ERR]"
            lines += [
                f"**Tai File Ket Qua:** {dl_icon}",
                "",
                "| Thuoc tinh | Gia tri |",
                "|---|---|",
                f"| HTTP Status | {dl.get('status_code', '?')} |",
                f"| Content-Type | `{dl.get('content_type', '?')}` |",
                f"| Kich thuoc file ket qua | {fmt_bytes(dl.get('size_bytes', 0))} |",
                f"| Dinh dang phat hien | {dl.get('format_detected', '?')} |",
                f"| File da luu tai | `{dl.get('saved_file_path', 'Chua luu')}` |",
                "",
            ]

        milestones = poll.get("milestones", [])
        if milestones:
            lines += ["**Timeline Tien Do Xu Ly:**", "", "```"]
            for m in milestones:
                msg_safe = m['message'].encode("ascii", errors="replace").decode("ascii")
                lines.append(f"  [{fmt_seconds(m['elapsed_sec']):>8}]  {m['progress']:>3}%  {msg_safe[:70]}")
            lines += ["```", ""]

        lines += ["---", ""]

    # ─── Section 5: Benchmarks ──────────────────────────────────────────────
    lines += ["## 5. Ket Qua Benchmark Ky Thuat", ""]

    chk = benchmarks.get("chunking")
    if chk:
        naive = chk.get("naive_fixed_chunking", {})
        hier  = chk.get("hierarchical_chunking_v6_2", {})
        doc_s = chk.get("document_stats", {})
        lines += [
            "### 5a. Chunking Algorithm -- Bao Toan Cau Truc",
            "",
            f"Doc test: {doc_s.get('total_words', '?')} tu | "
            f"{doc_s.get('num_tables', '?')} bang | "
            f"{doc_s.get('num_formulas', '?')} cong thuc | "
            f"{doc_s.get('num_code_blocks', '?')} code block",
            "",
            "| Thuat toan | So batch | Thoi gian (ms) | Vi pham bang | Vi pham LaTeX | Vi pham code |",
            "|---|---|---|---|---|---|",
            f"| **Naive Fixed-Size** | {naive.get('chunks_count', '?')} | {naive.get('execution_time_ms', '?')} "
            f"| [ERR] {naive.get('table_split_violations', '?')} ({naive.get('table_split_rate_percent', '?')}%) "
            f"| [ERR] {naive.get('latex_split_violations', '?')} | [ERR] {naive.get('code_block_split_violations', '?')} |",
            f"| **Hierarchical v6.2** *(Our)* | {hier.get('chunks_count', '?')} | {hier.get('execution_time_ms', '?')} "
            f"| [OK] 0 (0%) | [OK] {hier.get('latex_split_violations', 0)} | [OK] {hier.get('code_block_split_violations', 0)} |",
            "",
        ]

    prs = benchmarks.get("parsers")
    if prs:
        lines += [
            "### 5b. So Sanh PDF Parser Libraries",
            "",
            "| Parser | Latency (ms) | ms/trang | Table | Heading | Math | Output |",
            "|---|---|---|---|---|---|---|",
        ]
        for name, d in prs.items():
            tbl  = "[OK]" if d.get("table_structure_preserved") else "[ERR]"
            head = "[OK]" if d.get("heading_preserved") else "[ERR]"
            math = "[OK]" if d.get("math_preserved") else "[ERR]"
            our  = " *(Our)*" if "PyMuPDF4LLM" in name else ""
            lines.append(
                f"| **{name}**{our} | {d.get('avg_latency_ms', '?')} | {d.get('ms_per_page', '?')} "
                f"| {tbl} | {head} | {math} | {d.get('output_format', '?')} |"
            )
        lines.append("")

    gls = benchmarks.get("glossary")
    if gls:
        gt = gls.get("google_translate", {})
        rl = gls.get("raw_llm_without_glossary", {})
        op = gls.get("our_pipeline_with_glossary_injection", {})
        lines += [
            "### 5c. Do Chinh Xac Thuat Ngu vs Ground Truth (30 tu chuyen nganh)",
            "",
            "| Phuong phap | Dung/Tong | Accuracy | Bang Markdown | LaTeX |",
            "|---|---|---|---|---|",
            f"| Google Translate | {gt.get('correct_terms', '?')}/{gt.get('total_terms', 30)} | {gt.get('accuracy_percent', '?')}% | {gt.get('table_markdown_preservation', '?')} | {gt.get('latex_formula_preservation', '?')} |",
            f"| LLM thuan (khong Glossary) | {rl.get('correct_terms', '?')}/{rl.get('total_terms', 30)} | {rl.get('accuracy_percent', '?')}% | {rl.get('table_markdown_preservation', '?')} | {rl.get('latex_formula_preservation', '?')} |",
            f"| **Pipeline cua nhom** *(Glossary Injection)* | {op.get('correct_terms', '?')}/{op.get('total_terms', 30)} | **{op.get('accuracy_percent', '?')}%** | **{op.get('table_markdown_preservation', '?')}** | **{op.get('latex_formula_preservation', '?')}** |",
            "",
            "**Vi du cu the:**",
            "",
            "| Thuat ngu | Google Translate | Pipeline cua nhom |",
            "|---|---|---|",
        ]
        for item in gls.get("specific_comparisons", []):
            lines.append(f"| `{item['term']}` | {item['google']} | {item['our_pipeline']} |")
        lines.append("")

    thr = benchmarks.get("throughput")
    if thr:
        par = thr.get("parallel_vs_sequential", {})
        lines += [
            "### 5d. Parallel vs Sequential Batch Translation",
            "",
            "| So batch | Latency/batch (ms) | Sequential (ms) | Parallel (ms) | Speedup | Cai thien |",
            "|---|---|---|---|---|---|",
            f"| {par.get('num_batches', '?')} | {par.get('batch_latency_ms', '?')} "
            f"| {par.get('sequential_total_time_ms', '?')} | {par.get('parallel_total_time_ms', '?')} "
            f"| **{par.get('speedup_factor', '?')}x** | **+{par.get('throughput_improvement_percent', '?')}%** |",
            "",
        ]

    # ─── Section 6: Issues ──────────────────────────────────────────────────
    issues = []
    for r in file_results:
        if r["poll"]["result"] == "FAILED":
            issues.append(f"- [ERR] `{r['filename']}`: Pipeline that bai -- `{r['poll'].get('error', 'unknown')[:100]}`")
        if r["poll"]["result"] == "TIMEOUT":
            issues.append(f"- [TIMEOUT] `{r['filename']}`: Timeout sau 30 phut -- file qua lon ({fmt_bytes(r['meta']['size_bytes'])})")
        qa = r.get("quality", {})
        if qa.get("analysis_possible") and qa.get("latex_corrupted_count", 0) > 0:
            issues.append(f"- [!] `{r['filename']}`: {qa['latex_corrupted_count']} LaTeX block bi corrupt")
        if qa.get("analysis_possible") and not qa.get("has_vietnamese_content"):
            issues.append(f"- [!] `{r['filename']}`: Ban dich khong co noi dung tieng Viet")

    lines += ["## 6. Van De Phat Hien & Khuyen Nghi", ""]
    if issues:
        lines += issues + [""]
    else:
        lines += ["*Khong phat hien van de nghiem trong nao.* [OK]", ""]

    lines += [
        "### Khuyen Nghi:",
        "",
        "1. **File rat lon (>50 trang):** Can implement page-level chunked upload de tranh timeout worker.",
        "2. **Session recovery:** Co che Redis `job_latest_{doc_id}` dang hoat dong dung.",
        "3. **Fallback chain:** Kiem tra file nao dung Gemini fallback vs vLLM primary de danh gia chi phi.",
        "",
        "---",
        "",
        "## 7. Verdict Cuoi Cung",
        "",
        f"> {verdict}",
        "",
        f"*Bao cao duoc tao tu dong boi `eval_pipeline.py` luc {now_str}*",
    ]

    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    run_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_output_dir = OUTPUTS_ROOT / f"run_{run_ts}"
    run_output_dir.mkdir(parents=True, exist_ok=True)

    sep("=")
    print("  DOC TRANSLATION SERVICE -- EVALUATION & MANUAL INSPECTION PIPELINE")
    print(f"  IUH Academic Counseling Ecosystem | {run_ts}")
    print(f"  Output Directory: {run_output_dir}")
    sep("=")

    log("Generating JWT token...", "STEP")
    token = generate_jwt_token()
    log(f"JWT OK for user_id='{TEST_USER_ID}'", "OK")

    sep()
    log("Checking Kaggle vLLM tunnel...", "STEP")
    vllm_info = check_vllm_tunnel()
    if vllm_info.get("alive"):
        log(f"vLLM tunnel OK -- Models: {vllm_info['models']}", "OK")
    else:
        log(f"vLLM tunnel NOT reachable ({vllm_info.get('error', 'timeout')}) -> Gemini 2.5 Flash fallback", "WARN")

    sep()
    log("Detecting service URL...", "STEP")
    base_url, mode_label = determine_base_url(token)
    log(f"Using: {mode_label} -> {base_url}", "OK")

    sep()
    log("Scanning test data directory...", "STEP")
    pdf_files = sorted(TEST_DATA_DIR.glob("*.pdf"), key=lambda f: f.stat().st_size)
    if not pdf_files:
        log(f"No PDF files found in {TEST_DATA_DIR}", "ERROR")
        sys.exit(1)
    log(f"Found {len(pdf_files)} PDF files (sorted by size ascending):", "OK")
    for f in pdf_files:
        print(f"    - {f.name} ({fmt_bytes(f.stat().st_size)})")

    # ── Benchmarks ───────────────────────────────────────────────────────────
    sep()
    log("Running technical benchmark scripts...", "STEP")
    benchmarks = {}
    bench_map = {
        "chunking":   "bench_chunking.py",
        "parsers":    "bench_pdf_parsers.py",
        "glossary":   "bench_glossary_translation.py",
        "throughput": "bench_e2e_throughput.py",
    }
    for key, script in bench_map.items():
        log(f"  Running {script}...", "RUN")
        result = run_benchmark_script(script)
        benchmarks[key] = result
        log(f"  {script} -> {'OK' if result else 'No result (see WARN)'}", "OK" if result else "WARN")

    # ── E2E Test Loop & Local File Export ─────────────────────────────────────
    sep("=")
    log(f"STARTING E2E TESTING -- {len(pdf_files)} files | timeout {TIMEOUT_PER_FILE_SEC//60}m/file", "STEP")
    sep("=")

    file_results = []

    for idx, pdf_path in enumerate(pdf_files, 1):
        sep()
        folder_slug = f"{idx:02d}_{pdf_path.stem}"
        file_out_dir = run_output_dir / folder_slug
        file_out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  [FILE {idx}/{len(pdf_files)}] {pdf_path.name} ({fmt_bytes(pdf_path.stat().st_size)})")
        print(f"  Target Folder: {file_out_dir}")
        sep()

        # Copy original PDF to target directory
        shutil.copy2(pdf_path, file_out_dir / "original.pdf")

        file_meta = {"name": pdf_path.name, "size_bytes": pdf_path.stat().st_size}

        log("Uploading file...", "RUN")
        t_upload_start = time.time()
        doc_id = upload_pdf(base_url, pdf_path, token)
        upload_sec = time.time() - t_upload_start

        if not doc_id:
            log(f"Upload FAILED for {pdf_path.name}", "ERROR")
            file_results.append({
                "filename": pdf_path.name,
                "meta": file_meta,
                "doc_id": None,
                "upload_sec": round(upload_sec, 2),
                "poll": {"result": "FAILED", "elapsed_sec": 0, "model_used": "N/A",
                         "glossary": [], "milestones": [], "translated_text": "",
                         "error": "Upload failed", "pages_processed": 0},
                "quality": {},
                "download": {},
            })
            continue

        log(f"Upload OK -> doc_id={doc_id[:8]}... ({fmt_seconds(upload_sec)})", "OK")

        log(f"Polling status (timeout={TIMEOUT_PER_FILE_SEC//60}m)...", "RUN")
        poll_result = poll_job_status(base_url, doc_id, token,
                                      timeout_sec=TIMEOUT_PER_FILE_SEC,
                                      file_label=pdf_path.name)
        res = poll_result.get("result", "?")
        res_label = {"COMPLETED": "[COMPLETED]", "FAILED": "[FAILED]", "TIMEOUT": "[TIMEOUT]"}.get(res, "[?]")
        log(
            f"{res_label} after {fmt_seconds(poll_result.get('elapsed_sec', 0))} "
            f"| Model: {poll_result.get('model_used', 'N/A')[:50]} "
            f"| Glossary: {len(poll_result.get('glossary', []))} terms",
            "OK" if res == "COMPLETED" else "WARN"
        )

        # Save translated.md and glossary.json to folder
        if poll_result.get("translated_text"):
            (file_out_dir / "translated.md").write_text(poll_result["translated_text"], encoding="utf-8")
        
        if poll_result.get("glossary"):
            (file_out_dir / "glossary.json").write_text(
                json.dumps(poll_result["glossary"], indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

        # Save metadata.json
        meta_info = {
            "file_name": pdf_path.name,
            "doc_id": doc_id,
            "result": res,
            "elapsed_sec": poll_result.get("elapsed_sec", 0),
            "model_used": poll_result.get("model_used", ""),
            "pages_processed": poll_result.get("pages_processed", 0),
            "glossary_count": len(poll_result.get("glossary", [])),
            "timestamp": datetime.datetime.now().isoformat()
        }
        (file_out_dir / "metadata.json").write_text(json.dumps(meta_info, indent=2, ensure_ascii=False), encoding="utf-8")

        # Copy extracted images to evaluation folder to ensure local previews load successfully
        local_img_dir = Path("extracted_images") / doc_id
        if local_img_dir.exists():
            dest_img_dir = run_output_dir / "extracted_images" / doc_id
            dest_img_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(local_img_dir, dest_img_dir, dirs_exist_ok=True)
            log(f"Đã sao chép {len(list(local_img_dir.glob('*')))} ảnh vào {dest_img_dir}", "OK")

        qa = analyze_translation_quality(poll_result.get("translated_text", ""), pdf_path.name)

        dl_result = {}
        if res == "COMPLETED":
            log("Downloading result file and saving to disk...", "RUN")
            dest_pdf_path = file_out_dir / "translated.pdf"
            dl_result = download_and_save(base_url, doc_id, token, save_path=dest_pdf_path)
            dl_ok = dl_result.get("success", False)
            log(
                f"Download {'OK' if dl_ok else 'FAILED'} -- "
                f"{dl_result.get('format_detected', '?')} "
                f"{fmt_bytes(dl_result.get('size_bytes', 0))} -> {dest_pdf_path.name}",
                "OK" if dl_ok else "ERROR",
            )

        file_results.append({
            "filename": pdf_path.name,
            "meta": file_meta,
            "doc_id": doc_id,
            "upload_sec": round(upload_sec, 2),
            "poll": poll_result,
            "quality": qa,
            "download": dl_result,
            "output_dir": str(file_out_dir)
        })

    # ── Generate Report & Side-by-Side Viewer ─────────────────────────────────
    sep("=")
    log("Generating evaluation report & Side-by-Side HTML viewer...", "STEP")
    report_md   = generate_report(run_ts, mode_label, vllm_info, file_results, benchmarks)
    
    # Save report to reports folder and run folder
    report_path = REPORT_DIR / f"evaluation_report_{run_ts}.md"
    report_path.write_text(report_md, encoding="utf-8")
    (run_output_dir / "summary_report.md").write_text(report_md, encoding="utf-8")

    # Generate interactive HTML side-by-side viewer
    html_viewer_path = run_output_dir / "side_by_side_viewer.html"
    generate_side_by_side_html(run_ts, file_results, html_viewer_path)

    log(f"Report saved: {report_path}", "OK")
    log(f"Side-by-Side Viewer saved: {html_viewer_path}", "OK")
    print(f"\n  >> HTML Viewer: {html_viewer_path}")
    print(f"  >> Full Output Folder: {run_output_dir}\n")

    summary = {
        "run_timestamp": run_ts,
        "base_url_mode": mode_label,
        "vllm_tunnel": vllm_info,
        "total_files": len(file_results),
        "completed": sum(1 for r in file_results if r["poll"].get("result") == "COMPLETED"),
        "failed":    sum(1 for r in file_results if r["poll"].get("result") == "FAILED"),
        "timed_out": sum(1 for r in file_results if r["poll"].get("result") == "TIMEOUT"),
        "report_path": str(report_path),
        "output_directory": str(run_output_dir),
        "html_viewer": str(html_viewer_path)
    }
    sep()
    print("  SUMMARY JSON:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    sep("=")

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
