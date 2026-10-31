"""H2-34 Khoảng ôn qua các lần ôn với bốn chuỗi đánh giá (mô phỏng bằng gói fsrs, cấu hình như Flashcard Service,
tắt fuzzing để tái lập). Khoảng ôn = số ngày từ lần ôn này đến hạn ôn kế tiếp."""
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402
from fsrs import Card, Rating, Scheduler  # noqa: E402

sch = Scheduler(learning_steps=(), relearning_steps=(), enable_fuzzing=False)
G, H, E, A = Rating.Good, Rating.Hard, Rating.Easy, Rating.Again
seqs = {
    "Good liên tục": [G] * 7,
    "Easy liên tục": [E] * 7,
    "Hard liên tục": [H] * 7,
    "Good, Good, Good, Again, Good, Good, Good": [G, G, G, A, G, G, G],
}
fig, ax = figstyle.figure(width_cm=14, height_cm=7.2)
for name, seq in seqs.items():
    card, now, ivls = Card(), datetime(2026, 1, 1, tzinfo=timezone.utc), []
    for rating in seq:
        card, _ = sch.review_card(card, rating, now)
        ivls.append((card.due - now).days)
        now = card.due
    ax.plot(range(1, len(seq) + 1), ivls, "o-", ms=4, label=name)
    print(name, ivls, file=sys.stderr)
ax.set_yscale("log")
ax.set_xlabel("Lần ôn thứ")
ax.set_ylabel("Khoảng ôn kế tiếp (ngày, thang log)")
ax.set_xticks(range(1, 8))
ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}")
ax.legend(fontsize=8, loc="upper left")
figstyle.save(fig, sys.argv[1])
