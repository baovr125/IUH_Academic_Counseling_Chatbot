"""H2-31 Khả năng nhớ khi không ôn và khi ôn theo lịch FSRS.
Mô phỏng bằng gói fsrs (>=6,<7), Scheduler(learning_steps=(), relearning_steps=(), enable_fuzzing=False):
cấu hình giống flashcard_service/app/services/fsrs_algorithm.py, chỉ tắt fuzzing để hình tái lập được.
Mỗi lần đến hạn, người học chọn Good. R(t) tính bằng hằng số _DECAY, _FACTOR của chính Scheduler."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402
from fsrs import Card, Rating, Scheduler  # noqa: E402

sch = Scheduler(learning_steps=(), relearning_steps=(), enable_fuzzing=False)
t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
HORIZON = 60
card, _ = sch.review_card(Card(), Rating.Good, t0)
first_s = card.stability
reviews = [(0.0, card.stability)]
while True:
    due_days = (card.due - t0).total_seconds() / 86400
    if due_days > HORIZON:
        break
    card, _ = sch.review_card(card, Rating.Good, card.due)
    reviews.append((due_days, card.stability))


def r(t, s):
    return (1 + sch._FACTOR * t / s) ** sch._DECAY


fig, ax = figstyle.figure(width_cm=14, height_cm=7)
ts = [i / 10 for i in range(0, HORIZON * 10 + 1)]
ax.plot(ts, [r(t, first_s) for t in ts], color="#94A3B8", lw=1.6, ls="--", label="Không ôn lại")
xs, ys = [], []
for k, (start, s) in enumerate(reviews):
    end = reviews[k + 1][0] if k + 1 < len(reviews) else HORIZON
    seg = [start + i / 10 for i in range(int((end - start) * 10) + 1)]
    xs += seg
    ys += [r(t - start, s) for t in seg]
ax.plot(xs, ys, color=figstyle.SERIES[0], lw=1.8, label="Ôn theo lịch FSRS (chọn Good)")
for start, s in reviews[1:]:
    ax.axvline(start, color="#CBD5E1", lw=0.8, zorder=0)
    ax.text(start, 1.012, f"S={s:.0f}", fontsize=7.5, ha="center", va="bottom", color="#334155")
ax.axhline(0.9, color="#6B7280", lw=0.8, ls=":")
ax.text(HORIZON, 0.9, " r = 0,9", fontsize=8, va="center", color="#374151")
ax.set_xlim(0, HORIZON)
ax.set_ylim(0.55, 1.06)
ax.set_xlabel("Số ngày kể từ lần học đầu tiên")
ax.set_ylabel("Khả năng nhớ R")
ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}".replace(".", ","))
ax.legend(loc="lower left")
figstyle.save(fig, sys.argv[1])
