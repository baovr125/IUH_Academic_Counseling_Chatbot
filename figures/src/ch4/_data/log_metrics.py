"""Trích số liệu từ các log truy vấn đầy đủ của chatbot (logs/academic_chatbot/<ngày>/HHMMSS-*.md).

Chỉ đọc log, không sửa. Bỏ qua tệp CACHE-HIT và BLOCKED. In JSON để chép vào mục 4.2.8 của báo cáo.
Cách dùng: python log_metrics.py <thư mục ngày> <tệp JSON ra>
"""
import json
import re
import sys
from pathlib import Path

day = Path(sys.argv[1])
rows = []
for f in sorted(day.glob("*.md")):
    if "CACHE-HIT" in f.name or "BLOCKED" in f.name:
        continue
    t = f.read_text(encoding="utf-8")

    def grab(pattern, cast=str, default=None):
        m = re.search(pattern, t)
        return cast(m.group(1)) if m else default

    rows.append({
        "file": f.name,
        "query": grab(r"^# Query: (.*)$".replace("^", "(?m)^")),
        "intent": grab(r"\*\*Detected Intent:\*\* (\w+)"),
        "sub_queries": len(re.findall(r"(?m)^- Query \d+:", t)) or 1,
        "router_ms": grab(r"Standalone Router Latency:\*\* (\d+) ms", int),
        "retrieval_ms": grab(r"Retrieval - \*\*Latency:\*\* (\d+) ms", int),
        "generation_ms": grab(r"LLM Generation Latency:\*\* (\d+) ms", int),
        "prompt_tokens": grab(r"Prompt Tokens:\*\* (\d+)", int),
        "completion_tokens": grab(r"Completion Tokens:\*\* (\d+)", int),
        "doc_relevance": grab(r"Doc Relevance \(ISREL\):\*\* `(\w+)`"),
        "conflict": grab(r"Conflict Detected:\*\* `(\w+)`"),
        "confidence": grab(r"Answer Confidence \(ISSUP\):\*\* `(\w+)`"),
        "chunks": grab(r"Retrieved Context Chunks \((\d+) chunks\)", int, 0),
    })

Path(sys.argv[2]).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
for r in rows:
    print(r["file"][:42].ljust(44), r["intent"], r["sub_queries"], r["router_ms"], r["retrieval_ms"], r["generation_ms"],
          r["prompt_tokens"], r["completion_tokens"], r["doc_relevance"], r["conflict"], r["confidence"], r["chunks"])
