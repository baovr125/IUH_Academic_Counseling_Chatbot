"""Thống kê kho tri thức theo tên miền (Bảng 4.2): số tài liệu, đoạn cha, đoạn con. CHỈ ĐỌC Supabase.

Tương đương câu SQL trong mục 4.1.6 nhưng chạy qua API (không cần quyền SQL). Kết quả: eval/results/kb_stats.json.
"""
import datetime
from collections import defaultdict
from urllib.parse import urlparse

from common import RES, fetch_all, supabase, write_json

sb = supabase()
docs = fetch_all(sb, "documents", "id,source_url,title,updated_at")
parents = fetch_all(sb, "document_parents", "id,document_id")
chunks = fetch_all(sb, "document_chunks", "id,document_id")


def bucket(url: str) -> str:
    return urlparse(url).netloc if url.startswith("http") else "(tệp do quản trị viên tải lên)"


doc_bucket = {d["id"]: bucket(d["source_url"]) for d in docs}
stats = defaultdict(lambda: {"documents": 0, "parents": 0, "chunks": 0})
for d in docs:
    stats[doc_bucket[d["id"]]]["documents"] += 1
for p in parents:
    stats[doc_bucket.get(p["document_id"], "(không rõ)")]["parents"] += 1
for c in chunks:
    stats[doc_bucket.get(c["document_id"], "(không rõ)")]["chunks"] += 1

total = {k: sum(v[k] for v in stats.values()) for k in ("documents", "parents", "chunks")}
out = {
    "taken_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "updated_at_range": [min(d["updated_at"] for d in docs), max(d["updated_at"] for d in docs)],
    "by_domain": dict(sorted(stats.items(), key=lambda kv: -kv[1]["documents"])),
    "total": total,
}
write_json(RES / "kb_stats.json", out)
for k, v in out["by_domain"].items():
    print(f"{k:40s} {v['documents']:5d} {v['parents']:6d} {v['chunks']:6d}")
print(f"{'Tổng':40s} {total['documents']:5d} {total['parents']:6d} {total['chunks']:6d}")
print(out["taken_at"], out["updated_at_range"])
