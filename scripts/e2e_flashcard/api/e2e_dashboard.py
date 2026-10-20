"""E2E số liệu Flashcard cho Dashboard qua Kong + Supabase thật.
Tạo một NGƯỜI DÙNG THỬ riêng (email e2e-dash-<tag>@example.test) nên không đụng dữ liệu người dùng thật; dọn sạch trong finally
(xóa user kéo theo sổ/thẻ/nhật ký ôn nhờ ON DELETE CASCADE) rồi đếm lại để chắc không sót."""
import datetime
import os
import sys
import uuid

import httpx
from jose import jwt

ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[3])  # gốc dự án (scripts/e2e_flashcard/<api|ui>/file.py)
for line in open(os.path.join(ROOT, ".env"), encoding="utf8"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))
from supabase import create_client

sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
TAG = uuid.uuid4().hex[:6]
EMAIL = f"e2e-dash-{TAG}@example.test"
K = "http://localhost:8000/api/v1/flashcards"
c = httpx.Client(timeout=120)
ok = True
UID = None


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))


now = datetime.datetime.now(datetime.timezone.utc)
iso = lambda dt: dt.isoformat()  # noqa: E731
try:
    UID = sb.table("users").insert({"email": EMAIL, "full_name": f"E2E Dashboard {TAG}", "role": "student"}).execute().data[0]["id"]
    tok = jwt.encode({"sub": UID, "role": "student", "iss": "iuh-auth-service", "exp": now + datetime.timedelta(minutes=20)},
                     os.environ["JWT_SECRET_KEY"], algorithm="HS256")
    H = {"Authorization": f"Bearer {tok}"}

    def langs():
        r = c.get(f"{K}/languages", headers=H)
        assert r.status_code == 200, r.text
        return {l["code"]: l for l in r.json()["data"]["languages"]}

    def streak(days=84):
        r = c.get(f"{K}/stats/streak", headers=H, params={"days": days})
        assert r.status_code == 200, r.text
        return r.json()["data"]

    check("không token -> 401", c.get(f"{K}/languages").status_code == 401 and c.get(f"{K}/stats/streak").status_code == 401)

    # ---- người dùng mới: mọi thứ bằng 0
    L = langs()
    check("người dùng mới: mọi ngôn ngữ có mastered=0 (trường có mặt)", all(l.get("mastered") == 0 for l in L.values()), str({k: v.get("mastered") for k, v in L.items() if v.get("mastered") != 0}))
    s = streak()
    check("người dùng mới: today_cards=0, today_reviews=0", s.get("today_cards") == 0 and s["today_reviews"] == 0, str({k: s[k] for k in ("today_cards", "today_reviews")}))

    # ---- dữ liệu thử: 4 thẻ ja, 3 thẻ de
    decks = {}
    for lang, words in (("ja", ["水", "火", "木", "金"]), ("de", ["Haus", "Baum", "Tür"])):
        d = c.post(f"{K}/decks", headers=H, json={"title": f"E2E-DASH-{TAG}-{lang}", "lang_code": lang})
        assert d.status_code == 200, d.text
        decks[lang] = d.json()["data"]["id"]
        for w in words:
            r = c.post(f"{K}/cards", headers=H, json={"deck_id": decks[lang], "front_text": w, "back_text": f"nghĩa {w} {TAG}"})
            assert r.status_code == 200, r.text
    ja_cards = [x["id"] for x in sb.table("flashcards").select("id").eq("deck_id", decks["ja"]).order("created_at").execute().data]
    de_cards = [x["id"] for x in sb.table("flashcards").select("id").eq("deck_id", decks["de"]).order("created_at").execute().data]

    L = langs()
    check("ja: 4 thẻ mới, chưa thuộc", (L["ja"]["cards"], L["ja"]["new"], L["ja"]["mastered"]) == (4, 4, 0), str(L["ja"]))
    check("de: 3 thẻ mới, chưa thuộc", (L["de"]["cards"], L["de"]["new"], L["de"]["mastered"]) == (3, 3, 0), str(L["de"]))

    # ---- ôn thật qua API: thẻ ja[0] ôn 3 lần, ja[1] ôn 1 lần -> 4 lượt, 2 thẻ khác nhau
    for cid, times in ((ja_cards[0], 3), (ja_cards[1], 1)):
        for _ in range(times):
            r = c.post(f"{K}/review", headers=H, json={"card_id": cid, "grade": 3})
            assert r.status_code == 200, r.text
    s = streak()
    check("today_reviews đếm lượt (4)", s["today_reviews"] == 4, str(s["today_reviews"]))
    check("today_cards đếm thẻ khác nhau (2)", s.get("today_cards") == 2, str(s.get("today_cards")))
    check("chuỗi ngày = 1 sau khi ôn hôm nay", s["current_streak"] == 1, str(s["current_streak"]))
    check("heatmap ngày cuối có 4 lượt", s["days"][-1]["count"] == 4)
    check("days=7 cũng trả today_cards", streak(7).get("today_cards") == 2)

    # ---- đã thuộc: de[0] stability 25 (thuộc, đến hạn), de[1] stability 20.9 (chưa thuộc), de[2] vẫn mới
    past, future = iso(now - datetime.timedelta(days=1)), iso(now + datetime.timedelta(days=9))
    last = iso(now - datetime.timedelta(days=3))
    sb.table("flashcards").update({"state": 2, "reps": 4, "stability": 25.0, "difficulty": 3.0, "last_review": last, "due": past}).eq("id", de_cards[0]).execute()
    sb.table("flashcards").update({"state": 2, "reps": 3, "stability": 20.9, "difficulty": 3.0, "last_review": last, "due": future}).eq("id", de_cards[1]).execute()
    L = langs()
    check("de: mastered=1 (25 ngày tính, 20,9 không tính, thẻ mới không tính)", L["de"]["mastered"] == 1, str(L["de"]))
    check("de: due=1, new=1", (L["de"]["due"], L["de"]["new"]) == (1, 1), str(L["de"]))
    check("ja: mastered vẫn 0 sau khi ôn thật (stability còn thấp)", L["ja"]["mastered"] == 0, str(L["ja"]))
    total_mastered = sum(l["mastered"] for l in L.values())
    total_cards = sum(l["cards"] for l in L.values())
    check("tổng đã thuộc = 1, tổng thẻ = 7", (total_mastered, total_cards) == (1, 7), f"{total_mastered}/{total_cards}")

    # ---- cô lập giữa người dùng: người thứ hai không thấy gì
    UID2 = sb.table("users").insert({"email": f"e2e-dash-{TAG}-b@example.test", "full_name": "E2E B", "role": "student"}).execute().data[0]["id"]
    try:
        tok2 = jwt.encode({"sub": UID2, "role": "student", "iss": "iuh-auth-service", "exp": now + datetime.timedelta(minutes=20)}, os.environ["JWT_SECRET_KEY"], algorithm="HS256")
        H2 = {"Authorization": f"Bearer {tok2}"}
        L2 = {l["code"]: l for l in c.get(f"{K}/languages", headers=H2).json()["data"]["languages"]}
        s2 = c.get(f"{K}/stats/streak", headers=H2).json()["data"]
        check("người dùng khác không thấy thẻ/lượt ôn của người dùng thử", sum(l["cards"] for l in L2.values()) == 0 and s2["today_cards"] == 0)
    finally:
        sb.table("users").delete().eq("id", UID2).execute()
finally:
    if UID:
        sb.table("users").delete().eq("id", UID).execute()
    left_users = sb.table("users").select("id", count="exact").like("email", f"e2e-dash-{TAG}%").execute().count
    left_decks = sb.table("flashcard_decks").select("id", count="exact").like("title", f"E2E-DASH-{TAG}%").execute().count
    left_cards = sb.table("flashcards").select("id", count="exact").like("definition", f"%{TAG}").execute().count
    left_logs = sb.table("review_logs").select("id", count="exact").eq("user_id", UID or "00000000-0000-0000-0000-000000000000").execute().count
    print(f"còn sót: users={left_users} decks={left_decks} cards={left_cards} review_logs={left_logs}")
    check("đã dọn sạch (0 sót)", (left_users, left_decks, left_cards, left_logs) == (0, 0, 0, 0))

print("\nKẾT QUẢ:", "TẤT CẢ ĐẠT" if ok else "CÓ LỖI")
sys.exit(0 if ok else 1)
