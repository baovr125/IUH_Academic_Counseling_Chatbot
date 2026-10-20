"""E2E qua Kong cho 10 bộ sưu tập ngôn ngữ (flashcard-service thật + Supabase thật). Dọn sạch dữ liệu thử khi xong.
Dùng: python e2e_languages.py [pre|post]   pre = trước migration 005 (kiểm tra suy giảm êm), post = sau migration."""
import datetime, os, sys, uuid
import httpx
from jose import jwt

MODE = sys.argv[1] if len(sys.argv) > 1 else "post"
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[3])  # gốc dự án (scripts/e2e_flashcard/<api|ui>/file.py)
for line in open(os.path.join(ROOT, ".env"), encoding="utf8"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))
from supabase import create_client

sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
user = sb.table("users").select("id,role").limit(1).execute().data[0]
UID, ROLE = user["id"], user.get("role") or "student"
secret = os.environ["JWT_SECRET_KEY"]


def token(sub=UID, exp=15):
    return jwt.encode({"sub": sub, "role": ROLE, "iss": "iuh-auth-service",
                       "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=exp)}, secret, algorithm="HS256")


K = "http://localhost:8000/api/v1/flashcards"
H = {"Authorization": f"Bearer {token()}"}
c = httpx.Client(timeout=120)
ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))


SAMPLES = {
    "en": ("Good morning", "Chào buổi sáng"), "de": ("Guten Morgen", "Chào buổi sáng"), "zh": ("早上好", "Chào buổi sáng"),
    "ja": ("おはようございます", "Chào buổi sáng"), "ko": ("좋은 아침", "Chào buổi sáng"), "fr": ("Bonjour", "Xin chào"),
    "es": ("Buenos días", "Chào buổi sáng"), "ru": ("Доброе утро", "Chào buổi sáng"), "th": ("สวัสดีตอนเช้า", "Chào buổi sáng"),
}
TAG = uuid.uuid4().hex[:6]
created_decks: set[str] = set()
before = {d["id"] for d in c.get(f"{K}/decks", headers=H).json()["data"]}

try:
    check("không token -> 401", c.get(f"{K}/languages").status_code == 401)

    if MODE == "pre":
        r = c.get(f"{K}/languages", headers=H)
        check("trước migration: /languages -> 503 MIGRATION_REQUIRED nêu rõ migration 005",
              r.status_code == 503 and r.json()["error"]["code"] == "MIGRATION_REQUIRED" and "005" in r.json()["error"]["message"], r.text[:120])
        r = c.post(f"{K}/cards/from-translation", headers=H,
                   json={"client_request_id": f"e2e-{TAG}-0001", "source_lang": "de", "term": "Guten Morgen", "translation": "Chào buổi sáng"})
        check("trước migration: from-translation -> 503 MIGRATION_REQUIRED (không ghi dữ liệu dở dang)", r.status_code == 503, r.text[:120])
        r = c.post(f"{K}/cards/from-translation", headers=H, json={"client_request_id": f"e2e-{TAG}-0002", "term": "Hallo", "translation": "Xin chào"})
        check("thiếu ngôn ngữ -> 422 LANG_REQUIRED (kiểm tra trước cả migration)", r.status_code == 422 and r.json()["error"]["code"] == "LANG_REQUIRED", r.text[:120])
        r = c.get(f"{K}/decks", headers=H)
        check("API cũ GET /decks vẫn chạy trước migration", r.status_code == 200)
        r = c.post(f"{K}/decks", headers=H, json={"title": f"E2E-{TAG}", "lang_code": "de"})
        check("API cũ POST /decks (có lang_code) vẫn chạy trước migration", r.status_code == 200, r.text[:100])
        if r.status_code == 200:
            created_decks.add(r.json()["data"]["id"])
        r = c.post(f"{K}/decks", headers=H, json={"title": f"E2E-{TAG}-x"})
        check("POST /decks thiếu lang_code -> 422 (không còn mặc định 'en')", r.status_code == 422, r.text[:100])
    else:
        r = c.get(f"{K}/languages", headers=H)
        check("GET /languages -> 200 đủ 10 ngôn ngữ", r.status_code == 200 and [l["code"] for l in r.json()["data"]["languages"]] ==
              ["en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th", "vi"])
        base = {l["code"]: l["cards"] for l in r.json()["data"]["languages"]}

        for lang, (term, meaning) in SAMPLES.items():
            term_u = f"{term} {TAG}"
            r = c.post(f"{K}/cards/from-translation", headers=H, json={
                "client_request_id": f"e2e-{TAG}-{lang}", "source_lang": lang, "term": term_u, "translation": meaning, "phonetic": "x"})
            d = r.json().get("data") or {}
            check(f"lưu {lang}", r.status_code == 200 and d.get("created") and d["card"]["lang_code"] == lang and d["card"]["target_lang"] == "vi",
                  r.text[:110] if r.status_code != 200 else d["deck"]["title"])
            if r.status_code == 200:
                created_decks.add(d["deck"]["id"])

        after = c.get(f"{K}/languages", headers=H).json()["data"]
        got = {l["code"]: l["cards"] for l in after["languages"]}
        check("mỗi ngôn ngữ tăng đúng 1 thẻ, tiếng Việt không đổi", all(got[l] == base[l] + 1 for l in SAMPLES) and got["vi"] == base["vi"], str(got))

        r = c.get(f"{K}/languages/de/cards", headers=H, params={"q": TAG})
        items = r.json()["data"]["items"]
        check("GET /languages/de/cards?q= chỉ trả thẻ tiếng Đức", r.status_code == 200 and len(items) == 1 and items[0]["lang_code"] == "de" and items[0]["term"].startswith("Guten Morgen"))
        r = c.get(f"{K}/languages/ja/cards", headers=H, params={"q": "Guten"})
        check("tìm 'Guten' trong tiếng Nhật không ra thẻ tiếng Đức", r.status_code == 200 and not r.json()["data"]["items"])

        r = c.post(f"{K}/cards/from-translation", headers=H, json={
            "client_request_id": f"e2e-{TAG}-dup", "source_lang": "de", "term": f"  guten morgen {TAG} ", "translation": "khác"})
        check("trùng -> 409 DUPLICATE_CARD kèm thẻ cũ", r.status_code == 409 and r.json()["error"]["code"] == "DUPLICATE_CARD" and r.json()["error"]["data"]["card"]["id"], r.text[:120])
        r = c.post(f"{K}/cards/from-translation", headers=H, json={"client_request_id": f"e2e-{TAG}-auto", "source_lang": "auto", "term": "Hallo", "translation": "Xin chào"})
        check("source_lang=auto -> 422 LANG_REQUIRED", r.status_code == 422 and r.json()["error"]["code"] == "LANG_REQUIRED")
        r = c.post(f"{K}/cards/from-translation", headers=H, json={"client_request_id": f"e2e-{TAG}-vi", "source_lang": "vi", "term": "xin chào", "translation": "hello"})
        check("source_lang=vi -> 422", r.status_code == 422)
        again = c.post(f"{K}/cards/from-translation", headers=H, json={
            "client_request_id": f"e2e-{TAG}-de", "source_lang": "de", "term": f"Guten Morgen {TAG}", "translation": "Chào buổi sáng", "phonetic": "x"})
        check("gửi lại cùng client_request_id -> phát lại kết quả, không tạo thẻ thứ hai", again.status_code == 200 and again.json()["data"].get("idempotent_replay"), again.text[:120])

        de_deck = next(l for l in after["languages"] if l["code"] == "de")["default_deck_id"]
        r = c.post(f"{K}/cards/from-translation", headers=H, json={
            "client_request_id": f"e2e-{TAG}-mm", "source_lang": "fr", "term": "Salut", "translation": "Chào", "deck_id": de_deck})
        check("lưu từ Pháp vào sổ Đức -> 409 LANG_MISMATCH", r.status_code == 409 and r.json()["error"]["code"] == "LANG_MISMATCH", r.text[:100])
finally:
    # Dọn sạch: xóa thẻ rồi sổ do bài thử tạo.
    after_ids = {d["id"] for d in c.get(f"{K}/decks", headers=H).json()["data"]}
    for did in (after_ids - before) | created_decks:
        sb.table("flashcards").delete().eq("deck_id", did).execute()
        sb.table("flashcard_decks").delete().eq("id", did).execute()

print("\nKẾT QUẢ:", "TẤT CẢ ĐẠT" if ok else "CÓ LỖI")
sys.exit(0 if ok else 1)
