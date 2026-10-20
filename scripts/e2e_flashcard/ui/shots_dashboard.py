"""Chụp / đo tương phản / đo tràn ngang trang Dashboard với API Flashcard GIẢ (mock trong trình duyệt).
Dùng: python -I -X utf8 shots_dashboard.py <thư_mục_ra> [shots|contrast|overflow]
Tạo 2 người dùng thử (student + public) để xem cả hai vai trò, xóa ngay trong finally."""
import ast, datetime, json, os, re, sys, uuid

from jose import jwt
from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else "shots"
BASE = "http://localhost:5173"
os.makedirs(OUT, exist_ok=True)
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[3])  # gốc dự án (scripts/e2e_flashcard/<api|ui>/file.py)
for line in open(os.path.join(ROOT, ".env"), encoding="utf8"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))
from supabase import create_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui_checks import CONTRAST_JS, OVERFLOW_JS  # noqa: E402

sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
TAG = uuid.uuid4().hex[:6]
LANGS = ["en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th", "vi"]


def summary(over):
    s = {c: dict(code=c, learnable=c != "vi", decks=0, cards=0, new=0, due=0, mastered=0, weak=0) for c in LANGS}
    for c, o in over.items():
        s[c].update(o)
    return {"languages": [s[c] for c in LANGS], "unconfirmed": {"decks": [], "cards": 0}}


today = datetime.date.today()
def streak(cards):
    return dict(days=[dict(date=(today - datetime.timedelta(days=i)).isoformat(), count=(i * 7) % 11, intensity=(i * 7) % 5) for i in range(84)],
                current_streak=6, longest_streak=14, today_reviews=cards + 5, today_cards=cards, total_reviews=480)

SCENARIOS = {
    "ready": (summary({"en": dict(decks=3, cards=128, new=12, due=18, mastered=44, weak=5), "de": dict(decks=1, cards=34, new=6, due=4, mastered=9),
                       "ja": dict(decks=1, cards=20, new=20)}), streak(14)),
    "goal-reached": (summary({"en": dict(decks=3, cards=128, new=12, due=18, mastered=44)}), streak(26)),
    "done": (summary({"en": dict(decks=2, cards=90, new=10, mastered=60), "de": dict(decks=1, cards=20, mastered=3)}), streak(30)),
    "empty": (summary({}), streak(0)),
    "error": ("ERR", "ERR"),
    "loading": ("HANG", streak(14)),
}
CURRENT = {"name": "ready"}


def handle(route):
    req = route.request
    sm, st = SCENARIOS[CURRENT["name"]]
    path = req.url.split("/api/v1/flashcards", 1)[-1].split("?")[0]
    data = sm if path == "/languages" else st if path == "/stats/streak" else {}
    if data == "HANG":
        return  # không trả lời -> giữ trạng thái đang tải
    if data == "ERR":
        return route.fulfill(status=503, content_type="application/json", body=json.dumps({"ok": False, "error": {"code": "DB_ERROR", "message": "Không thể truy cập cơ sở dữ liệu."}}))
    route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "data": data}))


VIEWPORTS = {"desktop": (1280, 800), "tablet": (768, 900), "mobile": (390, 800)}
users = []
try:
    for role in ("student", "public"):
        u = sb.table("users").insert({"email": f"e2e-shot-{TAG}-{role}@example.test", "full_name": f"Nguyễn Văn {role.title()}", "role": role,
                                      **({"student_code": f"99{int(TAG, 16) % 1000000:06d}"} if role == "student" else {})}).execute().data[0]
        users.append((role, jwt.encode({"sub": u["id"], "role": role, "iss": "iuh-auth-service", "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=50)},
                                       os.environ["JWT_SECRET_KEY"], algorithm="HS256")))
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        for role, tok in users:
            for vp, (w, h) in VIEWPORTS.items():
                for theme in ("light", "dark"):
                    if os.environ.get("ONLY") and os.environ["ONLY"] != f"{role}:{vp}:{theme}":
                        continue
                    ctx = b.new_context(viewport={"width": w, "height": h})
                    ctx.add_init_script("try{localStorage.setItem('iuh_portal_ai_token'," + json.dumps(tok) + ");localStorage.setItem('app_theme'," + json.dumps(theme) + ");}catch(e){}")
                    ctx.route("**/api/v1/flashcards/**", handle)
                    pg = ctx.new_page()
                    for name in SCENARIOS:
                        if role == "public" and name not in ("ready", "error", "loading"):
                            continue
                        CURRENT["name"] = name
                        pg.goto(BASE + "/dashboard", wait_until="domcontentloaded")
                        pg.wait_for_timeout(1800 if name != "loading" else 900)
                        pg.evaluate("t=>document.documentElement.classList.toggle('dark', t==='dark')", theme)
                        pg.wait_for_timeout(300)
                        tag = f"{role}-{name}__{vp}__{theme}"
                        if MODE == "overflow":
                            for item in pg.evaluate(OVERFLOW_JS):
                                item.update(page=tag)
                                open(os.path.join(OUT, "overflow.jsonl"), "a", encoding="utf8").write(json.dumps(item, ensure_ascii=False) + "\n")
                        elif MODE == "contrast":
                            for item in pg.evaluate(CONTRAST_JS):
                                item.update(page=tag, theme=theme)
                                open(os.path.join(OUT, "contrast.jsonl"), "a", encoding="utf8").write(json.dumps(item, ensure_ascii=False) + "\n")
                        else:
                            pg.screenshot(path=os.path.join(OUT, f"{tag}.png"), full_page=True)
                    ctx.close()
        b.close()
finally:
    for role in ("student", "public"):
        sb.table("users").delete().like("email", f"e2e-shot-{TAG}-%").execute()
    left = sb.table("users").select("id", count="exact").like("email", f"e2e-shot-{TAG}-%").execute().count
    print("người dùng thử còn sót:", left)
print("xong ->", OUT, MODE)
