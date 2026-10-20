"""Gộp các tệp kết quả thành một báo cáo Markdown (so sánh A/B, đoạn văn, IPA, prompt injection).

  python -m evaluation.report --out results/REPORT.md
Chỉ đọc các tệp đã có trong results/; tệp nào thiếu thì mục đó ghi "chưa chạy".
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from evaluation.common import EVAL_DIR, read_jsonl, summarise_runs

METRICS = [
    ("runs", "Số lần chạy"), ("ok", "Chạy thành công"), ("provider_outage", "Lỗi do provider (429/timeout)"),
    ("system_failures", "Lỗi hệ thống"), ("items", "Tổng số thẻ"), ("count_fulfilment_ge90pct", "Đạt ≥ 90% số lượng"),
    ("runs_with_duplicates", "Lần chạy có từ trùng"), ("schema_valid_rate_of_candidates", "Thẻ đúng schema / ứng viên"),
    ("reviewer_reject_rate", "Tỷ lệ bị reviewer loại"), ("reviewer_fix_rate", "Tỷ lệ reviewer sửa"),
    ("example_contains_term", "Ví dụ chứa từ khóa"), ("ipa_present_and_valid", "IPA hợp lệ (có)"),
    ("example_translation_present", "Có dịch câu ví dụ"), ("verified_share", "Thẻ đã qua kiểm duyệt"),
    ("latency_s", "Độ trễ (s)"), ("tokens_per_run", "Token / lần chạy"), ("tokens_per_returned_item", "Token / thẻ"),
    ("llm_calls_per_run", "Lời gọi LLM / lần chạy"), ("providers", "Provider"), ("error_codes", "Mã lỗi"),
]


def load(path: Path) -> Optional[List[Dict[str, Any]]]:
    return read_jsonl(path) if path.exists() else None


def cell(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, dict):
        return ", ".join(f"{k}: {v}" for k, v in value.items()) or "—"
    return str(value)


def table(columns: Dict[str, Dict[str, Any]]) -> str:
    names = list(columns)
    lines = ["| Chỉ số | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for key, label in METRICS:
        lines.append(f"| {label} | " + " | ".join(cell(columns[n].get(key)) for n in names) + " |")
    return "\n".join(lines)


def per_level(rows: List[Dict[str, Any]]) -> str:
    out = ["| Trình độ | Lần chạy | Thẻ | Ví dụ chứa từ khóa | IPA hợp lệ | Có dịch ví dụ |", "|---|---|---|---|---|---|"]
    for level in sorted({r["level"] for r in rows}):
        s = summarise_runs([r for r in rows if r["level"] == level])
        out.append(f"| {level} | {s['ok']}/{s['runs']} | {s['items']} | {s['example_contains_term']} | {s['ipa_present_and_valid']} | {s['example_translation_present']} |")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/REPORT.md")
    args = ap.parse_args()
    res = EVAL_DIR / "results"
    parts = ["# Báo cáo đánh giá sinh từ vựng bằng AI", "",
             "> Số liệu từ `evaluation/results/`. Mọi tỷ lệ kèm khoảng tin cậy Wilson 95% `[thấp-cao] (đạt/tổng)`. "
             "Mẫu nhỏ nên khoảng tin cậy rộng; xem README để biết các hạn chế.", ""]

    a, b = load(res / "topics_A.jsonl"), load(res / "topics_B.jsonl")
    parts += ["## 1. Chủ đề: phương án B (3 bước) so với đối chứng A (1 lời gọi)", ""]
    if a and b:
        parts += [table({"A: một lần gọi": summarise_runs(a), "B: SELECT→ENRICH→VERIFY": summarise_runs(b)}), "",
                  "### Phương án B theo trình độ", "", per_level(b), ""]
        both = {r["id"] for r in a if not r.get("error")} & {r["id"] for r in b if not r.get("error")}
        parts += [f"Số chủ đề chạy thành công ở cả hai biến thể: {len(both)}.", ""]
    else:
        parts += ["chưa chạy đủ cả hai biến thể (cần `results/topics_A.jsonl` và `results/topics_B.jsonl`).", ""]

    p = load(res / "passages_B.jsonl")
    parts += ["## 2. Đoạn văn (trích từ)", "", table({"B: đoạn văn": summarise_runs(p)}) if p else "chưa chạy.", ""]

    ipa = res / "ipa_check.json"
    parts += ["## 3. IPA so với từ điển", ""]
    parts += ["```json", json.dumps(json.loads(ipa.read_text(encoding="utf8"))["summary"], ensure_ascii=False, indent=2), "```", ""] if ipa.exists() else ["chưa chạy.", ""]

    inj = res / "injection.summary.json"
    parts += ["## 4. Prompt injection", ""]
    parts += ["```json", inj.read_text(encoding="utf8"), "```", ""] if inj.exists() else ["chưa chạy.", ""]

    out = Path(args.out) if Path(args.out).is_absolute() else EVAL_DIR / args.out
    out.write_text("\n".join(parts), encoding="utf8")
    print(f"Đã ghi {out}")


if __name__ == "__main__":
    main()
