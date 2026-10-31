"""Tóm tắt lịch sử git của dự án theo tuần (gợi ý để điền Nhật ký làm việc). Chỉ đọc git, ghi eval/results/git_weekly.md."""
import subprocess
from collections import defaultdict
from datetime import date, timedelta

from common import REPO, RES

log = subprocess.run(["git", "log", "--pretty=%ad|%an|%s", "--date=short"], cwd=REPO, capture_output=True, text=True,
                     encoding="utf-8").stdout.splitlines()
weeks = defaultdict(list)
for line in log:
    d, author, subject = line.split("|", 2)
    y, m, dd = map(int, d.split("-"))
    day = date(y, m, dd)
    weeks[day - timedelta(days=day.weekday())].append((author, subject))
out = ["# Lịch sử git theo tuần (gợi ý cho Nhật ký làm việc)\n", f"Tổng {len(log)} commit.\n"]
for monday in sorted(weeks):
    items = weeks[monday]
    authors = sorted({a for a, _ in items})
    out.append(f"## Tuần {monday:%d/%m/%Y} – {monday + timedelta(days=6):%d/%m/%Y}: {len(items)} commit ({', '.join(authors)})\n")
    out.extend(f"- {s}" for _, s in items[:12])
    if len(items) > 12:
        out.append(f"- … và {len(items) - 12} commit khác")
    out.append("")
(RES / "git_weekly.md").write_text("\n".join(out), encoding="utf-8")
print(f"{len(weeks)} tuần, {len(log)} commit")
