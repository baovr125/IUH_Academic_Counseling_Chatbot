"""Chụp ảnh giao diện flashcard bằng dữ liệu GIẢ (mock API trong trình duyệt, không ghi/đọc dữ liệu flashcard thật).
Dùng: python -I -X utf8 shots.py <thư_mục_ra> [base_url]. Biến môi trường ONLY=desktop:light để chụp một cấu hình."""
import datetime, os, sys, json, re
from jose import jwt
from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5173"
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
user = sb.table("users").select("id,role").limit(1).execute().data[0]
tok = jwt.encode({"sub": user["id"], "role": user.get("role") or "student", "iss": "iuh-auth-service",
                  "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=50)},
                 os.environ["JWT_SECRET_KEY"], algorithm="HS256")

# ---------------- dữ liệu giả ----------------
LANGS = ["en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th", "vi"]
SUM = {c: dict(code=c, learnable=c != "vi", decks=0, cards=0, new=0, due=0, weak=0) for c in LANGS}
SUM["en"].update(decks=3, cards=128, new=12, due=18, weak=5)
SUM["de"].update(decks=1, cards=34, new=6, due=4, weak=1)
SUM["ja"].update(decks=1, cards=20, new=20, due=0, weak=0)
SUMMARY = {"languages": [SUM[c] for c in LANGS], "unconfirmed": {"decks": [], "cards": 0}}
DECKS = [
    dict(id="d1", title="Từ vựng IELTS Academic", description="Các từ học thuật thường gặp trong IELTS Reading và Writing.", lang_code="en", icon_flag="🇬🇧", cards_count=64, lang_confirmed=True),
    dict(id="d2", title="Công nghệ thông tin", description="Thuật ngữ CNTT: mạng, cơ sở dữ liệu, trí tuệ nhân tạo.", lang_code="en", icon_flag="🇬🇧", cards_count=40, lang_confirmed=True),
    dict(id="d3", title="Giao tiếp hằng ngày", description="", lang_code="en", icon_flag="🇬🇧", cards_count=24, lang_confirmed=True, is_default=True),
]
TERMS = [("resilient", "kiên cường, có khả năng phục hồi", "/rɪˈzɪliənt/", "adj"), ("mitigate", "giảm nhẹ, làm dịu bớt", "/ˈmɪtɪɡeɪt/", "verb"),
         ("ubiquitous", "có mặt khắp nơi", "/juːˈbɪkwɪtəs/", "adj"), ("scalable", "có thể mở rộng quy mô", "/ˈskeɪləbl/", "adj"),
         ("latency", "độ trễ", "/ˈleɪtənsi/", "noun"), ("deploy", "triển khai", "/dɪˈplɔɪ/", "verb"),
         ("robust", "mạnh mẽ, bền vững", "/rəʊˈbʌst/", "adj"), ("bandwidth", "băng thông", "/ˈbændwɪdθ/", "noun")]
def card(i, t, state=2):
    return dict(id=f"c{i}", deck_id="d1", term=t[0], definition=t[1], phonetic=t[2], part_of_speech=t[3], lang_code="en",
                example_sentence=f"The team built a {t[0]} system for the university.", example_translation="Nhóm đã xây dựng hệ thống cho trường đại học.",
                state=state, lapses=1 if i % 4 == 0 else 0, is_new=state == 0, recommended_mode="flip", deck_title=DECKS[i % 3]["title"],
                due=datetime.datetime.now(datetime.timezone.utc).isoformat(), choices=None)
CARDS = [card(i, t, 0 if i < 3 else 2) for i, t in enumerate(TERMS)]
STATS = dict(total=64, new=12, due=18, learning=9, mastered=25, weak=5)
today = datetime.date.today()
STREAK = dict(days=[dict(date=(today - datetime.timedelta(days=i)).isoformat(), count=(i * 7) % 11, intensity=(i * 7) % 5) for i in range(84)],
              current_streak=6, longest_streak=14, today_reviews=22, total_reviews=480)
GSTAT = dict(lang_code="en", level=dict(level=3, xp=260, level_floor_xp=200, next_level_xp=400), plays_total=14, plays_today=2,
             games={g: dict(plays=3, last_played=None, best=dict(relax=dict(score=420, stars=2, best_combo=6), challenge=None)) for g in ("match", "speed", "builder", "shooter")})
CATALOG = [dict(id=f"k{i}", title=t, description="Bộ từ vựng theo chủ đề đời sống hằng ngày.", lang_code="en", icon_flag="🇬🇧", category=c, level=l, cards_count=n, added_deck_id=None)
           for i, (t, c, l, n) in enumerate([("Gia đình", "daily", "A1", 30), ("Du lịch", "travel", "A2", 45), ("Ẩm thực", "food", "A2", 38), ("Công việc", "work", "B1", 52)])]

GAME_WORDS = [("resilient", "kiên cường"), ("mitigate", "giảm nhẹ"), ("ubiquitous", "có mặt khắp nơi"), ("scalable", "có thể mở rộng"),
              ("latency", "độ trễ"), ("deploy", "triển khai"), ("robust", "mạnh mẽ"), ("bandwidth", "băng thông")]
GAME_CARDS = [dict(id=f"g{i+1}", term=w, definition=d, phonetic="/test/", audio_url=None, part_of_speech="adj", lang_code="en", is_due=True,
                   choices=[d] + [x[1] for x in GAME_WORDS if x[1] != d][:3]) for i, (w, d) in enumerate(GAME_WORDS)]
SESSION = dict(session=dict(id="s1", game="match", mode="relax", total=6, correct=6, mistakes=1, hints=0, best_combo=4, duration_ms=45000,
                            score=820, stars=3, xp=60, applied_review=True, reviewed_count=5),
               is_record=True, previous_best=640, idempotent_replay=False, level=dict(level=4, xp=420, level_floor_xp=400, next_level_xp=700))


def body(path: str):
    p = path.split("/api/v1/flashcards", 1)[1].split("?")[0]
    if p == "/languages": return SUMMARY
    if p == "/decks": return DECKS
    if re.fullmatch(r"/decks/[^/]+/study-queue", p): return CARDS[:6]
    if re.fullmatch(r"/decks/[^/]+/study-stats", p): return STATS
    if re.fullmatch(r"/decks/[^/]+/cards", p): return CARDS
    if re.fullmatch(r"/languages/[^/]+/cards", p): return dict(items=CARDS, total=len(CARDS), limit=20, offset=0)
    if p == "/stats/streak": return STREAK
    if p == "/catalog/decks": return CATALOG
    if p == "/games/stats": return GSTAT
    m = re.fullmatch(r"/games/(\w+)/cards", p)
    if m: return dict(game=m.group(1), deck_id="d1", lang_code="en", playable=True, reason=None, min_required=4, total_cards=8, due_count=5, cards=GAME_CARDS[:6])
    if p == "/games/sessions": return SESSION
    if p == "/vocabulary/quota": return dict(limit=10, used=2, remaining=8)
    return {}





VIEWPORTS = {"desktop": (1280, 800), "tablet": (768, 900), "mobile": (390, 800)}
PAGES = [("01-lang-grid", "/flashcards", None), ("02-library-decks", "/flashcards/en", None),
         ("03-library-words", "/flashcards/en?tab=words", None),
         ("04-deck-study", "/flashcards/en/decks/d1", None), ("05-deck-list", "/flashcards/en/decks/d1", "Danh sách"),
         ("06-deck-games", "/flashcards/en/decks/d1", "Trò chơi"), ("07-catalog", "/flashcards/en", "catalog"),
         ("08-modal-create", "/flashcards/en", "modal"), ("09-menu-open", "/flashcards/en", "menu"), ("10-study-flipped", "/flashcards/en/decks/d1", "flip"), ("11-deck-add-menu", "/flashcards/en/decks/d1", "addmenu"), ("12-session-summary", "/flashcards/en/decks/d1", "summary"), ("13-confirm-delete", "/flashcards/en/decks/d1", "confirm"), ("14-game-match", "/flashcards/en/decks/d1", "game-match"), ("15-game-result", "/flashcards/en/decks/d1", "game-result"), ("16-game-speed", "/flashcards/en/decks/d1", "game-speed"), ("17-game-shooter", "/flashcards/en/decks/d1", "game-shooter"), ("18-modal-add", "/flashcards/en/decks/d1", "modal-add"), ("19-modal-ai", "/flashcards/en/decks/d1", "modal-ai"), ("20-modal-import", "/flashcards/en/decks/d1", "modal-import"), ("21-modal-delete-deck", "/flashcards/en", "modal-delete-deck"), ("22-modal-ai-de", "/flashcards/de", "modal-ai-lib"), ("23-modal-ai-ja", "/flashcards/ja", "modal-ai-lib")]
only = os.environ.get("ONLY")
if os.environ.get("PAGE"):
    PAGES = [x for x in PAGES if x[0].startswith(os.environ["PAGE"])]

def handle(route):
    req = route.request
    if req.method == "POST" and req.url.split("?")[0].endswith("/games/sessions"):
        return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "data": SESSION}))
    if "/api/v1/flashcards" not in req.url or req.method != "GET":
        return route.continue_() if "/api/v1/flashcards" not in req.url else route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "data": {}}))
    route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "data": body(req.url)}))

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    for vp, (w, h) in VIEWPORTS.items():
        for theme in ("light", "dark"):
            if only and only != f"{vp}:{theme}":
                continue
            ctx = b.new_context(viewport={"width": w, "height": int(os.environ.get("VH", h))})
            ctx.add_init_script("try{localStorage.setItem('iuh_portal_ai_token'," + json.dumps(tok) + ");localStorage.setItem('app_theme'," + json.dumps(theme) + ");}catch(e){}")
            ctx.route("**/api/v1/flashcards/**", handle)
            pg = ctx.new_page()
            for name, path, action in PAGES:
                pg.goto(BASE + path, wait_until="networkidle")
                pg.evaluate("t=>document.documentElement.classList.toggle('dark', t==='dark')", theme)
                try:
                    if action == "catalog":
                        pg.get_by_text("Thư viện bộ từ").first.click()
                    elif action == "flip":
                        pg.get_by_text(re.compile("Bấm vào thẻ")).click()
                    elif action == "addmenu":
                        pg.get_by_role("button", name="Thêm từ vựng").click()
                    elif action == "summary":
                        for _ in range(6):
                            pg.get_by_text(re.compile("Bấm vào thẻ")).click()
                            pg.get_by_role("button", name=re.compile("Tốt")).click()
                            pg.wait_for_timeout(250)
                    elif action == "confirm":
                        pg.get_by_role("tab", name=re.compile("Danh sách")).click()
                        pg.get_by_role("button", name=re.compile("Xóa thẻ")).first.click()
                    elif action and action.startswith("game-"):
                        pg.get_by_role("tab", name=re.compile("Trò chơi")).click()
                        kind = action.split("-", 1)[1] if action != "game-result" else "match"
                        pg.get_by_test_id(f"game-card-{kind}").click()
                        pg.wait_for_timeout(800)
                        if action == "game-result":
                            for i in range(1, 7):
                                pg.get_by_test_id(f"match-term-g{i}").click()
                                pg.get_by_test_id(f"match-def-g{i}").click()
                            pg.wait_for_timeout(1600)
                    elif action in ("modal-add", "modal-ai", "modal-import"):
                        pg.get_by_role("button", name="Thêm từ vựng").click()
                        pg.get_by_role("menuitem", name={"modal-add": "Thêm một từ", "modal-ai": "Tạo thêm bằng AI", "modal-import": "Nhập từ Excel / CSV"}[action]).click()
                    elif action == "modal-ai-lib":
                        pg.get_by_role("button", name="Tạo từ vựng với AI").first.click()
                    elif action == "modal-delete-deck":
                        pg.get_by_role("button", name=re.compile("Tùy chọn sổ")).first.click()
                        pg.get_by_role("menuitem", name="Xóa sổ thẻ").click()
                    elif action == "menu":
                        pg.get_by_role("button", name=re.compile("Tùy chọn sổ")).first.click()
                    elif action == "modal":
                        pg.get_by_role("button", name=re.compile("Tạo sổ")).first.click()
                    elif action:
                        pg.get_by_role("tab", name=re.compile(action)).first.click()
                except Exception as e:
                    print("bỏ qua thao tác", name, str(e)[:80])
                pg.wait_for_timeout(600)
                if os.environ.get("OVERFLOW"):
                    for item in pg.evaluate(OVERFLOW_JS):
                        item.update(page=name, vp=vp, theme=theme)
                        with open(os.path.join(OUT, "overflow.jsonl"), "a", encoding="utf8") as fh:
                            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
                elif os.environ.get("CONTRAST"):
                    for item in pg.evaluate(CONTRAST_JS):
                        item.update(page=name, vp=vp, theme=theme)
                        with open(os.path.join(OUT, "contrast.jsonl"), "a", encoding="utf8") as fh:
                            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
                else:
                    pg.screenshot(path=os.path.join(OUT, f"{name}__{vp}__{theme}.png"), full_page=bool(os.environ.get("FULL")))
            ctx.close()
    b.close()
print("xong ->", OUT)
