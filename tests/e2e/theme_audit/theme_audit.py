"""Kiểm tra tương phản Dark/Light Mode bằng trình duyệt thật (Playwright + Chrome) với dữ liệu GIẢ.

- Không cần đăng nhập thật, không cần Supabase: token là JWT không chữ ký tự tạo, mọi lời gọi /api/** được mock
  trong trình duyệt (không ghi/đọc dữ liệu thật).
- Đo mọi đoạn chữ hiển thị theo WCAG 2.x (chữ thường >= 4,5:1; chữ lớn >= 3:1). KHÁC công cụ cũ: nền gradient
  KHÔNG bị bỏ qua mà được lấy mẫu tại các điểm dừng màu và điểm giữa.
    + "fail": tương phản tại TÂM gradient (hoặc nền đặc) dưới ngưỡng.
    + "warn": chỉ phần đầu/cuối gradient dưới ngưỡng.
- Phủ ma trận TRẠNG THÁI của các trò chơi (chọn, sai, đã ghép, combo, tạm dừng, đã giải, kết quả...).

Dùng (cần dev server đang chạy, mặc định http://localhost:5173):
    python -I -X utf8 tests/e2e/theme_audit/theme_audit.py --out <thư_mục_ra>
    python -I -X utf8 tests/e2e/theme_audit/theme_audit.py --out out --suite all --themes dark --viewports desktop
Mã thoát 1 nếu còn "fail". Xem README.md cùng thư mục.
"""
import argparse
import collections
import datetime
import json
import os
import re
import sys
import base64
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------- dữ liệu giả
LANGS = ["en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th", "vi"]
SUM = {c: dict(code=c, learnable=c != "vi", decks=0, cards=0, new=0, due=0, weak=0) for c in LANGS}
SUM["en"].update(decks=3, cards=128, new=12, due=18, weak=5)
SUM["de"].update(decks=1, cards=34, new=6, due=4, weak=1)
SUMMARY = {"languages": [SUM[c] for c in LANGS], "unconfirmed": {"decks": [], "cards": 0}}
DECKS = [
    dict(id="d1", title="Từ vựng IELTS Academic", description="Các từ học thuật thường gặp.", lang_code="en", icon_flag="🇬🇧", cards_count=64, lang_confirmed=True),
    dict(id="d2", title="Công nghệ thông tin", description="Thuật ngữ CNTT.", lang_code="en", icon_flag="🇬🇧", cards_count=40, lang_confirmed=True),
    dict(id="d3", title="Giao tiếp hằng ngày", description="", lang_code="en", icon_flag="🇬🇧", cards_count=24, lang_confirmed=True, is_default=True),
]
WORDS = [("resilient", "kiên cường"), ("mitigate", "giảm nhẹ"), ("ubiquitous", "có mặt khắp nơi"), ("scalable", "có thể mở rộng"),
         ("latency", "độ trễ"), ("deploy", "triển khai"), ("robust", "mạnh mẽ"), ("bandwidth", "băng thông")]
DEF_OF = dict(WORDS)
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()


def study_card(i, w, state=2):
    return dict(id=f"c{i}", deck_id="d1", term=w[0], definition=w[1], phonetic="/test/", part_of_speech="adj", lang_code="en",
                example_sentence=f"The team built a {w[0]} system.", example_translation="Nhóm đã xây dựng hệ thống.",
                state=state, lapses=1 if i % 4 == 0 else 0, is_new=state == 0, recommended_mode="flip", deck_title=DECKS[i % 3]["title"],
                due=NOW, choices=None)


CARDS = [study_card(i, w, 0 if i < 3 else 2) for i, w in enumerate(WORDS)]
STATS = dict(total=64, new=12, due=18, learning=9, mastered=25, weak=5)
TODAY = datetime.date.today()
STREAK = dict(days=[dict(date=(TODAY - datetime.timedelta(days=i)).isoformat(), count=(i * 7) % 11, intensity=(i * 7) % 5) for i in range(84)],
              current_streak=6, longest_streak=14, today_reviews=22, total_reviews=480)
GSTAT = dict(lang_code="en", level=dict(level=3, xp=260, level_floor_xp=200, next_level_xp=400), plays_total=14, plays_today=2,
             games={g: dict(plays=3, last_played=None, best=dict(relax=dict(score=420, stars=2, best_combo=6), challenge=None)) for g in ("match", "speed", "builder", "shooter")})
CATALOG = [dict(id=f"k{i}", title=t, description="Bộ từ vựng theo chủ đề.", lang_code="en", icon_flag="🇬🇧", category=c, level=l, cards_count=n, added_deck_id=None)
           for i, (t, c, l, n) in enumerate([("Gia đình", "daily", "A1", 30), ("Du lịch", "travel", "A2", 45), ("Ẩm thực", "food", "A2", 38)])]
GAME_CARDS = [dict(id=f"g{i + 1}", term=w, definition=d, phonetic="/test/", audio_url=None, part_of_speech="adj", lang_code="en", is_due=True,
                   choices=[d] + [x[1] for x in WORDS if x[1] != d][:3]) for i, (w, d) in enumerate(WORDS)]
SESSION = dict(session=dict(id="s1", game="match", mode="relax", total=6, correct=6, mistakes=1, hints=0, best_combo=4, duration_ms=45000,
                            score=820, stars=3, xp=60, applied_review=True, reviewed_count=5),
               is_record=True, previous_best=640, idempotent_replay=False, level=dict(level=4, xp=420, level_floor_xp=400, next_level_xp=700))
USER = dict(id="audit-user", fullName="Người Dùng Thử", email="audit@example.com", role="student", studentCode="21000000",
            department="CNTT", major="KTPM", hasPassword=True)


def flashcard_body(path):
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
    if p == "/vocabulary/quota": return dict(limit=10, used=2, remaining=8)
    return {}


def fake_token():
    enc = lambda o: base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).timestamp())
    return f"{enc({'alg': 'none', 'typ': 'JWT'})}.{enc({'sub': USER['id'], 'role': 'student', 'exp': exp})}.x"


# ---------------------------------------------------------------- đo tương phản (chạy trong trang)
CONTRAST_JS = r"""
(opts) => {
  const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const over = (top, bottom) => { const a = top.a + bottom.a * (1 - top.a); if (a === 0) return { r: 0, g: 0, b: 0, a: 0 };
    return { r: (top.r * top.a + bottom.r * bottom.a * (1 - top.a)) / a, g: (top.g * top.a + bottom.g * bottom.a * (1 - top.a)) / a,
             b: (top.b * top.a + bottom.b * bottom.a * (1 - top.a)) / a, a }; };
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const ratioOf = (a, b) => { const l1 = lum(a), l2 = lum(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
  const dark = document.documentElement.classList.contains('dark');
  const page = dark ? { r: 15, g: 23, b: 42, a: 1 } : { r: 255, g: 255, b: 255, a: 1 };
  const mix = (a, b, t) => ({ r: a.r + (b.r - a.r) * t, g: a.g + (b.g - a.g) * t, b: a.b + (b.b - a.b) * t, a: 1 });

  // Trả về danh sách màu nền cần thử: 1 phần tử cho nền đặc, nhiều phần tử (điểm dừng + điểm giữa) cho gradient.
  const bgSamples = (el) => {
    const layers = []; let e = el; let gradient = null;
    while (e) {
      const cs = getComputedStyle(e);
      const bi = cs.backgroundImage;
      if (bi && bi !== 'none') {
        if (/gradient/.test(bi)) {
          const stops = (bi.match(/rgba?\([^)]+\)/g) || []).map(parse).filter(Boolean);
          if (stops.length) { gradient = stops; break; }
        } else { return null; } // ảnh nền: không đo được
      }
      const c = parse(cs.backgroundColor); if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
      e = e.parentElement;
    }
    let base = page;
    // Các lớp nền bán trong suốt nằm TRÊN gradient (ví dụ bg-white/95) phải được phủ lên từng điểm màu của gradient.
    const paint = (c) => { let out = c; for (let i = layers.length - 1; i >= 0; i--) out = over(layers[i], out); return out; };
    if (gradient) {
      const flat = gradient.map((g) => paint(over(g, base)));
      const pts = [...flat];
      for (let i = 0; i < flat.length - 1; i++) pts.push(mix(flat[i], flat[i + 1], 0.5));
      const centre = flat.reduce((s, c) => ({ r: s.r + c.r / flat.length, g: s.g + c.g / flat.length, b: s.b + c.b / flat.length, a: 1 }), { r: 0, g: 0, b: 0, a: 1 });
      return { samples: pts, centre, gradient: true };
    }
    for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
    return { samples: [base], centre: base, gradient: false };
  };
  const opacityOf = (el) => { let o = 1, e = el; while (e) { o *= parseFloat(getComputedStyle(e).opacity || '1'); e = e.parentElement; } return o; };
  const dialog = document.querySelector('[role=dialog]');
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const own = Array.from(el.childNodes).filter((n) => n.nodeType === 3 && n.textContent.trim()).map((n) => n.textContent.trim()).join(' ');
    if (!own) continue;
    if (dialog && !dialog.contains(el)) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    if (el.closest('[disabled],[aria-disabled=true],.sr-only')) continue;
    const bg = bgSamples(el); if (!bg) continue;
    let fg = parse(cs.color); if (!fg) continue;
    fg = { ...fg, a: fg.a * opacityOf(el) };
    if (fg.a < 0.05) continue; // chữ trong suốt có chủ ý (ví dụ ô xếp chữ còn trống)
    const ratios = bg.samples.map((b) => ratioOf(over(fg, b), b));
    const centre = ratioOf(over(fg, bg.centre), bg.centre);
    const worst = Math.min(...ratios);
    const px = parseFloat(cs.fontSize); const bold = parseInt(cs.fontWeight) >= 700;
    const need = (px >= 24 || (px >= 18.66 && bold)) ? 3 : 4.5;
    const sev = centre < need ? 'fail' : (worst < need ? 'warn' : null);
    if (sev) out.push({ sev, text: own.slice(0, 40), ratio: Math.round((sev === 'fail' ? centre : worst) * 100) / 100, need, size: px,
      gradient: bg.gradient, tag: el.tagName,
      cls: ((el.className || '').toString().split(/\s+/).filter((c) => /text-|dark:text-|bg-|from-|to-/.test(c)).slice(0, 6).join(' ')
        || ('<' + el.tagName.toLowerCase() + '>')) + (() => { let a = el.parentElement; while (a) { const k = (a.className || '').toString().split(/\s+/).filter((c) => /^(bg-|from-|dark:bg-)/.test(c)).slice(0, 3).join(' '); if (k) return '  ⟵ nền: ' + k; a = a.parentElement; } return ''; })() });
  }
  return out;
}
"""

VIEWPORTS = {"desktop": (1280, 800), "mobile": (390, 800)}
DECK = "/flashcards/en/decks/d1"


# ---------------------------------------------------------------- kịch bản
class Ctx:
    def __init__(self, pg, base, theme, vp, out, results):
        self.pg, self.base, self.theme, self.vp, self.out, self.results = pg, base, theme, vp, out, results
        self.measured = set()

    def goto(self, path):
        self.pg.goto(self.base + path, wait_until="networkidle")
        self.pg.wait_for_timeout(400)
        want = self.theme == "dark"
        have = self.pg.evaluate("document.documentElement.classList.contains('dark')")
        if want != have:
            self.record_raw("theme-mismatch", {"sev": "fail", "text": f"html.dark={have}, mong đợi {want}", "ratio": 0, "need": 0, "size": 0, "gradient": False, "tag": "HTML", "cls": ""})

    def record_raw(self, name, item):
        item.update(page=name, vp=self.vp, theme=self.theme)
        self.results.append(item)

    def measure(self, name):
        self.pg.wait_for_timeout(450)  # đợi hoạt ảnh vào (flip-in 0,28 s...) xong để không đo chữ đang mờ dần
        self.measured.add(name)
        for item in self.pg.evaluate(CONTRAST_JS, {}):
            self.record_raw(name, item)

    def shot(self, name):
        if self.out:  # chưa dùng trong lượt đo thường; gọi ctx.shot(tên) khi cần xem ảnh
            self.pg.screenshot(path=os.path.join(self.out, f"{name}__{self.vp}__{self.theme}.png"))


def safe(ctx, name, fn):
    try:
        fn()
    except Exception as e:  # kịch bản hỏng không được làm dừng cả lượt đo
        print(f"  [bỏ qua] {name}: {str(e).splitlines()[0][:110]}")


def open_game(ctx, kind, mode="relax"):
    ctx.goto(DECK)
    ctx.pg.get_by_role("tab", name=re.compile("Trò chơi")).click()
    if mode == "challenge":
        ctx.pg.get_by_role("radio", name=re.compile("Thử thách")).click()
    ctx.pg.get_by_test_id(f"game-card-{kind}").click()
    ctx.pg.wait_for_timeout(900)


def pages_suite(ctx):
    pg = ctx.pg
    for name, path in [("fc-lang-grid", "/flashcards"), ("fc-library-decks", "/flashcards/en"), ("fc-library-words", "/flashcards/en?tab=words"),
                       ("fc-deck-study", DECK)]:
        ctx.goto(path)
        ctx.measure(name)
    ctx.goto(DECK)
    safe(ctx, "fc-study-flipped", lambda: (pg.get_by_text(re.compile("Bấm vào thẻ")).click(), ctx.measure("fc-study-flipped")))
    ctx.goto(DECK)
    safe(ctx, "fc-deck-list", lambda: (pg.get_by_role("tab", name=re.compile("Danh sách")).click(), ctx.measure("fc-deck-list")))
    ctx.goto(DECK)
    safe(ctx, "fc-games-hub", lambda: (pg.get_by_role("tab", name=re.compile("Trò chơi")).click(), ctx.measure("fc-games-hub-relax"),
                                       pg.get_by_role("radio", name=re.compile("Thử thách")).click(), ctx.measure("fc-games-hub-challenge")))
    ctx.goto("/flashcards/en")
    safe(ctx, "fc-catalog", lambda: (pg.get_by_text("Thư viện bộ từ").first.click(), ctx.measure("fc-catalog")))
    ctx.goto("/flashcards/en")
    safe(ctx, "fc-menu-open", lambda: (pg.get_by_role("button", name=re.compile("Tùy chọn sổ")).first.click(), ctx.measure("fc-menu-open")))
    ctx.goto("/flashcards/en")
    safe(ctx, "fc-modal-create", lambda: (pg.get_by_role("button", name=re.compile("Tạo sổ")).first.click(), ctx.measure("fc-modal-create")))
    for name, item in [("fc-modal-add", "Thêm một từ"), ("fc-modal-ai", "Tạo thêm bằng AI"), ("fc-modal-import", "Nhập từ Excel / CSV")]:
        ctx.goto(DECK)
        safe(ctx, name, lambda item=item, name=name: (pg.get_by_role("button", name="Thêm từ vựng").click(), pg.get_by_role("menuitem", name=item).click(), ctx.measure(name)))
    ctx.goto(DECK)

    def summary():
        for _ in range(6):
            pg.get_by_text(re.compile("Bấm vào thẻ")).click()
            pg.get_by_role("button", name=re.compile("Tốt")).click()
            pg.wait_for_timeout(250)
        ctx.measure("fc-session-summary")
    safe(ctx, "fc-session-summary", summary)


def match_suite(ctx):
    pg = ctx.pg
    open_game(ctx, "match")
    ctx.measure("game-match-initial")
    pg.get_by_test_id("match-term-g1").click()
    ctx.measure("game-match-term-selected")
    pg.get_by_test_id("match-def-g2").click()
    ctx.measure("game-match-wrong")
    pg.wait_for_timeout(1000)
    pg.get_by_test_id("match-term-g1").click()
    pg.get_by_test_id("match-def-g1").click()
    ctx.measure("game-match-matched")
    for i in range(2, 7):
        pg.get_by_test_id(f"match-term-g{i}").click()
        pg.get_by_test_id(f"match-def-g{i}").click()
    pg.wait_for_timeout(1600)
    ctx.measure("game-result")


def speed_suite(ctx):
    pg = ctx.pg

    def answer(correct):
        term = pg.get_by_test_id("speed-term").inner_text().strip()
        choices = pg.get_by_role("group", name="Các đáp án").get_by_role("button")
        texts = [choices.nth(i).inner_text() for i in range(choices.count())]
        want = DEF_OF[term]
        idx = next(i for i, t in enumerate(texts) if (want in t) == correct)
        choices.nth(idx).click()

    open_game(ctx, "speed", "relax")
    ctx.measure("game-speed-relax-initial")
    answer(False)
    ctx.measure("game-speed-relax-wrong")
    answer_btn = pg.get_by_role("button", name=re.compile("Tiếp tục"))
    if answer_btn.count():
        answer_btn.click()
    pg.wait_for_timeout(300)
    answer(True)
    ctx.measure("game-speed-relax-correct")

    open_game(ctx, "speed", "challenge")
    ctx.measure("game-speed-challenge-initial")
    for _ in range(3):
        answer(True)
        pg.wait_for_timeout(1300)
    ctx.measure("game-speed-challenge-combo3")
    answer(False)
    ctx.measure("game-speed-challenge-wrong-life-lost")


def builder_suite(ctx):
    pg = ctx.pg
    open_game(ctx, "builder")
    ctx.measure("game-builder-initial")
    meaning = pg.get_by_test_id("builder-meaning").inner_text().strip()
    term = next(w for w, d in WORDS if d == meaning)
    tiles = pg.get_by_role("group", name="Các chữ cái").get_by_role("button")

    def click_letter(ch):
        for i in range(tiles.count()):
            b = tiles.nth(i)
            if b.inner_text().strip() == ch and b.is_enabled():
                b.click()
                return
        raise RuntimeError(f"không có ô '{ch}'")

    click_letter(term[0])
    ctx.measure("game-builder-partial-and-used-tile")
    pg.get_by_role("button", name=re.compile("Gợi ý")).click()
    ctx.measure("game-builder-hint")
    for ch in term[2:]:
        click_letter(ch)
    ctx.measure("game-builder-near-complete")


def shooter_suite(ctx):
    pg = ctx.pg
    open_game(ctx, "shooter", "challenge")
    pg.wait_for_timeout(500)
    ctx.measure("game-shooter-initial")
    pg.get_by_role("button", name=re.compile("Ngắm hỗ trợ")).click()
    ctx.measure("game-shooter-assist-on")
    arena = pg.get_by_test_id("shooter-arena")
    box = arena.bounding_box()
    arena.click(position={"x": box["width"] * 0.5, "y": box["height"] * 0.3})
    ctx.measure("game-shooter-shot-fired")
    pg.get_by_role("button", name="Tạm dừng").click()
    ctx.measure("game-shooter-paused")
    pg.get_by_test_id("shooter-paused").click()


SYSTEM_ROUTES = [("sys-dashboard", "/dashboard"), ("sys-translation", "/translation"), ("sys-translation-doc", "/translation-doc"),
                 ("sys-chat", "/chat"), ("sys-settings", "/settings"), ("sys-profile", "/profile")]


def system_suite(ctx):
    for name, path in SYSTEM_ROUTES:
        safe(ctx, name, lambda path=path, name=name: (ctx.goto(path), ctx.measure(name)))


# ---------------------------------------------------------------- chạy
def run(args):
    results = []
    if args.out:
        os.makedirs(args.out, exist_ok=True)
    token = fake_token()

    def handle(route):
        req = route.request
        url = req.url
        path = url.split("?")[0]
        if req.method == "POST" and path.endswith("/games/sessions"):
            data = SESSION
        elif "/api/v1/flashcards" in url and req.method == "GET":
            data = flashcard_body(url)
        elif path.endswith("/api/auth/me"):
            data = USER
        elif path.endswith("/api/auth/settings"):
            data = dict(theme=state["theme"], language="vi", soundEnabled=True, academicAlerts=True)
        else:
            data = {}
        route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "data": data}))

    state = {"theme": "light"}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for vp in args.viewports:
            w, h = VIEWPORTS[vp]
            for theme in args.themes:
                state["theme"] = theme
                context = browser.new_context(viewport={"width": w, "height": h})
                context.add_init_script("try{localStorage.setItem('iuh_portal_ai_token'," + json.dumps(token) + ");localStorage.setItem('app_theme'," + json.dumps(theme) + ");}catch(e){}")
                context.route("**/api/**", handle)
                pg = context.new_page()
                ctx = Ctx(pg, args.base, theme, vp, args.out, results)
                print(f"== {vp} / {theme}")
                suites = []
                if args.suite in ("flashcard", "all"):
                    suites += [("trang flashcard", pages_suite), ("Ghép cặp", match_suite), ("Đua 60 giây", speed_suite),
                               ("Xếp chữ", builder_suite), ("Bắn bóng", shooter_suite)]
                if args.suite in ("system", "all"):
                    suites += [("toàn hệ thống", system_suite)]
                for label, fn in suites:
                    safe(ctx, label, lambda fn=fn: fn(ctx))
                print(f"   đã đo {len(ctx.measured)} trạng thái/màn hình")
                context.close()
        browser.close()
    return results


def report(results, out):
    if out:
        with open(os.path.join(out, "contrast.jsonl"), "w", encoding="utf8") as fh:
            for r in results:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    fails = [r for r in results if r["sev"] == "fail"]
    warns = [r for r in results if r["sev"] == "warn"]
    print(f"\nTổng: {len(fails)} fail, {len(warns)} warn (gradient: chỉ đầu/cuối dải màu)")
    grouped = collections.defaultdict(lambda: {"n": 0, "min": 99, "pages": set(), "text": ""})
    for r in fails + warns:
        key = (r["sev"], r["theme"], r["cls"])
        g = grouped[key]
        g["n"] += 1
        g["min"] = min(g["min"], r["ratio"])
        g["pages"].add(r["page"])
        g["text"] = g["text"] or r["text"]
    for (sev, theme, cls), g in sorted(grouped.items(), key=lambda kv: (kv[0][0], kv[1]["min"])):
        pages = ",".join(sorted(g["pages"]))
        print(f"[{sev:4}][{theme:5}] min {g['min']:<5} x{g['n']:<3} '{g['text'][:26]}' :: {cls}\n          trang: {pages[:150]}")
    return len(fails)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://localhost:5173")
    ap.add_argument("--out", default="", help="thư mục ghi contrast.jsonl ")
    ap.add_argument("--suite", choices=["flashcard", "system", "all"], default="flashcard")
    ap.add_argument("--themes", nargs="+", choices=["light", "dark"], default=["light", "dark"])
    ap.add_argument("--viewports", nargs="+", choices=list(VIEWPORTS), default=["desktop", "mobile"])
    cli = ap.parse_args()
    sys.exit(1 if report(run(cli), cli.out) else 0)
