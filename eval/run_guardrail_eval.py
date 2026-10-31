"""Thí nghiệm E4: đánh giá bộ lọc an toàn (guardrails/query_filter.check_safety_and_jailbreak) của chatbot.

Nạp hàm của dự án bằng importlib (chỉ đọc, không cần Supabase, Redis hay LLM). Hai bộ dữ liệu trong eval/data/:
- guardrail_attacks.jsonl: câu tấn công, kỳ vọng bị chặn;
- guardrail_benign.jsonl: câu hỏi học vụ hợp lệ, kỳ vọng cho qua.
Kết quả: eval/results/guardrail_eval.json (tổng hợp, theo nhóm và danh sách câu sai).
"""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(r"B:\KhoaLuan\IUH_Academic_Counseling_Chatbot\services\academic_chatbot_service\app\guardrails\query_filter.py")
spec = importlib.util.spec_from_file_location("query_filter", SRC)
qf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qf)


def load(name):
    return [json.loads(l) for l in (HERE / "data" / name).read_text(encoding="utf-8").splitlines() if l.strip()]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((c - m) / d, (c + m) / d)


def run(rows):
    for r in rows:
        r["blocked"] = qf.check_safety_and_jailbreak(r["text"]) is not None
    return rows


attacks, benign = run(load("guardrail_attacks.jsonl")), run(load("guardrail_benign.jsonl"))
by_cat = {}
for r in attacks:
    c = by_cat.setdefault(r["category"], {"n": 0, "blocked": 0})
    c["n"] += 1
    c["blocked"] += r["blocked"]
blocked_attacks = sum(r["blocked"] for r in attacks)
blocked_benign = sum(r["blocked"] for r in benign)
trig = [r for r in benign if r["category"] == "trigger_words"]
plain = [r for r in benign if r["category"] != "trigger_words"]
out = {
    "patterns": {"jailbreak": len(qf.JAILBREAK_PATTERNS), "structural": len(qf.STRUCTURAL_TAG_PATTERNS)},
    "attacks": {"n": len(attacks), "blocked": blocked_attacks, "recall": blocked_attacks / len(attacks),
                "recall_ci95": wilson(blocked_attacks, len(attacks)), "by_category": by_cat,
                "missed": [(r["id"], r["text"]) for r in attacks if not r["blocked"]]},
    "benign": {"n": len(benign), "blocked": blocked_benign, "false_positive_rate": blocked_benign / len(benign),
               "fpr_ci95": wilson(blocked_benign, len(benign)),
               "plain": {"n": len(plain), "blocked": sum(r["blocked"] for r in plain)},
               "trigger_words": {"n": len(trig), "blocked": sum(r["blocked"] for r in trig)},
               "wrongly_blocked": [(r["id"], r["text"]) for r in benign if r["blocked"]]},
}
(HERE / "results").mkdir(exist_ok=True)
(HERE / "results" / "guardrail_eval.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
