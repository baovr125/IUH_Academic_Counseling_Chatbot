"""Hàm dùng chung cho các script đánh giá chatbot (thư mục eval/).

- Nạp .env của dự án (chỉ đọc) và import mã của Academic Chatbot Service để dùng đúng cùng logic với hệ thống.
- Các độ đo: Hit@K, MRR, khoảng tin cậy Wilson, phân vị, hệ số Cohen's kappa.
Không script nào ghi vào mã dự án hay cơ sở dữ liệu, trừ khi tài liệu của script đó nói rõ.
"""
import json
import math
import os
import sys
import unicodedata
from pathlib import Path

REPO = Path(r"B:\KhoaLuan\IUH_Academic_Counseling_Chatbot")
SVC = REPO / "services" / "academic_chatbot_service"
HERE = Path(__file__).parent
DATA = HERE / "data"
RES = HERE / "results"
RES.mkdir(exist_ok=True)


def load_env(force: dict | None = None) -> None:
    """Nạp biến môi trường từ .env của dự án (không ghi đè biến đã có), rồi áp dụng `force`."""
    from dotenv import dotenv_values
    for k, v in dotenv_values(REPO / ".env").items():
        if v is not None:
            os.environ.setdefault(k, v)
    os.environ.setdefault("ORT_LOGGING_LEVEL_SEVERITY", "3")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")          # mô hình đã nằm trong bộ nhớ đệm HuggingFace
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    for k, v in (force or {}).items():
        os.environ[k] = v


def import_service(force_env: dict | None = None):
    """Import app.services.rag_service của chatbot (kèm khóa/biến môi trường từ .env)."""
    load_env(force_env)
    if str(SVC) not in sys.path:
        sys.path.insert(0, str(SVC))
    import warnings
    warnings.filterwarnings("ignore")
    import logging
    logging.getLogger("academic_chatbot_service").setLevel(logging.ERROR)
    from app.services import rag_service
    return rag_service


def supabase():
    load_env()
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"],
                         os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"])


def fetch_all(sb, table: str, columns: str, page: int = 1000) -> list:
    rows, off = [], 0
    while True:
        part = sb.table(table).select(columns).range(off, off + page - 1).execute().data
        rows += part
        if len(part) < page:
            return rows
        off += page


def read_jsonl(path: Path) -> list:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def write_json(path: Path, obj) -> None:
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def unaccent(text: str) -> str:
    """Bỏ dấu tiếng Việt, giống hàm unaccent dùng ở nhánh toàn văn của CSDL."""
    text = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def dedupe(seq):
    seen, out = set(), []
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ---------------------------------------------------------------- độ đo
def hit_at_k(ranked: list, gold: set, k: int) -> int:
    return int(any(d in gold for d in ranked[:k]))


def reciprocal_rank(ranked: list, gold: set, k: int) -> float:
    for i, d in enumerate(ranked[:k], 1):
        if d in gold:
            return 1.0 / i
    return 0.0


def recall_at_k(ranked: list, gold: set, k: int) -> float:
    return len(gold & set(ranked[:k])) / len(gold) if gold else 0.0


def wilson(k: int, n: int, z: float = 1.96):
    """Khoảng tin cậy Wilson 95% cho tỉ lệ k/n (công thức 5-2 trong báo cáo)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def percentile(values: list, q: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    pos = (len(s) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def cohen_kappa(a: list, b: list) -> float:
    """Hệ số Cohen's kappa không trọng số (công thức 5-1)."""
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    labels = set(a) | set(b)
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labels)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def fmt_ci(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    lo, hi = max(0.0, lo), min(1.0, hi)
    return f"{100 * k / n:.1f}% [{100 * lo:.0f}–{100 * hi:.0f}] ({k}/{n})" if n else "—"
