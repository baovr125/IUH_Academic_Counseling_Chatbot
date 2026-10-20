"""E2E sinh từ vựng đa ngôn ngữ qua Kong + Supabase thật. Tạo sổ thử (tiêu đề E2E-VOCAB-<mã>) rồi dọn sạch.
Có đúng 1 lượt sinh THẬT (LLM thật, tính 1 lượt hạn mức của người dùng thử); các kiểm tra còn lại không tốn lượt."""
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
user = sb.table("users").select("id,role").limit(1).execute().data[0]
tok = jwt.encode({"sub": user["id"], "role": user.get("role") or "student", "iss": "iuh-auth-service",
                  "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=20)},
                 os.environ["JWT_SECRET_KEY"], algorithm="HS256")
H = {"Authorization": f"Bearer {tok}"}
K = "http://localhost:8000/api/v1/flashcards"
c = httpx.Client(timeout=120)
TAG = uuid.uuid4().hex[:6]
ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))


def used():
    return c.get(f"{K}/vocabulary/quota", headers=H).json()["data"]["used"]


deck_ids = []
try:
    de = c.post(f"{K}/decks", headers=H, json={"title": f"E2E-VOCAB-{TAG}-de", "lang_code": "de"}).json()["data"]
    en = c.post(f"{K}/decks", headers=H, json={"title": f"E2E-VOCAB-{TAG}-en", "lang_code": "en"}).json()["data"]
    deck_ids += [de["id"], en["id"]]

    before = used()
    r = c.post(f"{K}/vocabulary/generate", headers=H, json={"topic": "Du lịch", "lang_code": "de", "count": 5, "level": "A2", "deck_id": en["id"]})
    check("sinh tiếng Đức vào sổ tiếng Anh -> 409 LANG_MISMATCH", r.status_code == 409 and r.json()["error"]["code"] == "LANG_MISMATCH", r.text[:140])
    check("lệch ngôn ngữ không tốn lượt AI", used() == before)

    r = c.post(f"{K}/vocabulary/generate", headers=H, json={"topic": "x", "lang_code": "vi"})
    check("lang_code=vi (ngôn ngữ giải nghĩa) -> 422", r.status_code == 422)

    r = c.post(f"{K}/vocabulary/generate", headers=H, json={"topic": "Du lịch", "lang_code": "de", "count": 5, "level": "A2", "deck_id": de["id"]})
    check("sinh THẬT tiếng Đức vào sổ tiếng Đức -> 200", r.status_code == 200, r.text[:160])
    data = r.json()["data"]
    items = data["items"]
    check("phản hồi mang lang_code=de", data["lang_code"] == "de")
    check("có từ và không có chữ Hán/Cyrillic", len(items) >= 3 and all(all(ord(ch) < 0x0250 for ch in i["term"]) for i in items), str([i["term"] for i in items]))
    check("danh từ có mạo từ der/die/das", any(i["term"].split(" ")[0] in ("der", "die", "das") for i in items), str([i["term"] for i in items]))
    check("nghĩa bằng tiếng Việt, có phiên âm IPA", all(i["definition"] for i in items) and any(i["ipa"].startswith("/") for i in items))
    check("tốn đúng 1 lượt", used() == before + 1)

    cards = [{"term": i["term"], "definition": i["definition"], "part_of_speech": i["part_of_speech"], "phonetic": i["ipa"],
              "example": i["example"], "example_translation": i["example_translation"], "level": "A2"} for i in items]
    r = c.post(f"{K}/decks/from-generated", headers=H, json={"client_request_id": f"e2e-{TAG}-1", "deck_id": de["id"], "cards": cards,
                                                              "source": {"mode": "topic", "topic": "Du lịch", "level": "A2", "lang_code": "de"}})
    check("lưu vào sổ tiếng Đức -> 200", r.status_code == 200 and r.json()["data"]["inserted"] == len(cards), r.text[:140])
    saved = c.get(f"{K}/decks/{de['id']}/cards", headers=H).json()["data"]
    check("thẻ đã lưu mang lang_code=de", saved and {x.get("lang_code") for x in saved} == {"de"}, str({x.get("lang_code") for x in saved}))

    r = c.post(f"{K}/decks/from-generated", headers=H, json={"client_request_id": f"e2e-{TAG}-2", "deck_id": en["id"], "cards": cards[:2],
                                                              "source": {"mode": "topic", "lang_code": "de"}})
    check("lưu thẻ Đức vào sổ tiếng Anh -> 409", r.status_code == 409 and r.json()["error"]["code"] == "LANG_MISMATCH", r.text[:140])
    check("sổ tiếng Anh vẫn rỗng", not c.get(f"{K}/decks/{en['id']}/cards", headers=H).json()["data"])

    r = c.post(f"{K}/decks/from-generated", headers=H, json={
        "client_request_id": f"e2e-{TAG}-3", "deck": {"title": f"E2E-VOCAB-{TAG}-ja"},
        "cards": [{"term": "食べる", "definition": "ăn", "part_of_speech": "verb", "phonetic": "たべる · taberu"},
                  {"term": "図書館", "definition": "thư viện", "part_of_speech": "noun"}],
        "source": {"mode": "topic", "lang_code": "ja"}})
    check("tạo sổ mới tiếng Nhật chỉ bằng source.lang_code", r.status_code == 200 and r.json()["data"]["inserted"] == 2, r.text[:140])
    if r.status_code == 200:
        ja_id = r.json()["data"]["deck"]["id"]
        deck_ids.append(ja_id)
        row = sb.table("flashcard_decks").select("lang_code").eq("id", ja_id).execute().data[0]
        check("sổ mới lưu lang_code=ja", row["lang_code"] == "ja")
finally:
    for did in deck_ids:
        ids = [r["id"] for r in sb.table("flashcards").select("id").eq("deck_id", did).execute().data]
        if ids:
            sb.table("review_logs").delete().in_("card_id", ids).execute()
        sb.table("flashcards").delete().eq("deck_id", did).execute()
        sb.table("flashcard_decks").delete().eq("id", did).execute()
    left = sb.table("flashcard_decks").select("id", count="exact").like("title", f"E2E-VOCAB-{TAG}%").execute().count
    print("sổ thử còn sót:", left)

print("\nKẾT QUẢ:", "TẤT CẢ ĐẠT" if ok else "CÓ LỖI")
sys.exit(0 if ok else 1)
