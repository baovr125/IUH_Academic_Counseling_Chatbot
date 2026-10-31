"""H2-33 Đường khả năng nhớ R(t) của FSRS với các độ ổn định S khác nhau.

Tính bằng chính gói `fsrs` (>=6,<7; máy dùng 6.3.2) qua Scheduler.get_card_retrievability, cấu hình
giống flashcard_service/app/services/fsrs_algorithm.py (learning_steps=(), relearning_steps=()).
Công thức trong thư viện: R(t, S) = (1 + F·t/S)^(-w20), F = 0.9^(-1/w20) - 1, nên R(S, S) = 0.9.
Chạy: python H2-33.py <đường dẫn PNG>
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_theme"))
import figstyle  # noqa: E402
from fsrs import Card, Scheduler, State  # noqa: E402

scheduler = Scheduler(learning_steps=(), relearning_steps=())
t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
days = [d / 4 for d in range(0, 4 * 90 + 1)]

def retrievability(t: float, s: float) -> float:
    """Dạng liên tục, dùng đúng hằng số của scheduler (thư viện chỉ tính ở số ngày nguyên)."""
    return (1 + scheduler._FACTOR * t / s) ** scheduler._DECAY


fig, ax = figstyle.figure(width_cm=14, height_cm=7.2)
for s in (2, 10, 30, 90):
    card = Card(state=State.Review, stability=s, difficulty=5.0, due=t0, last_review=t0)
    for d in range(0, 91, 7):  # đối chiếu với hàm của thư viện tại các ngày nguyên
        lib = scheduler.get_card_retrievability(card, t0 + timedelta(days=d))
        assert abs(lib - retrievability(d, s)) < 1e-9, (s, d, lib)
    r = [retrievability(d, s) for d in days]
    ax.plot(days, r, label=f"S = {s} ngày")
    if s <= 90:
        ax.plot([s], [0.9], "o", color=ax.lines[-1].get_color(), ms=4)

ax.axhline(0.9, color="#6B7280", lw=0.9, ls="--")
ax.text(91, 0.9, "R = 0,9", va="center", fontsize=8.5, color="#374151")
ax.set_xlim(0, 90)
ax.set_ylim(0.4, 1.01)
ax.set_xlabel("Số ngày kể từ lần ôn gần nhất, t (ngày)")
ax.set_ylabel("Khả năng nhớ R")
ax.legend(loc="lower left", ncol=2)
# Dấu thập phân kiểu Việt Nam trên trục tung
ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}".replace(".", ","))
figstyle.save(fig, sys.argv[1])
