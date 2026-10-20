"""E2E qua Kong + docker compose (flashcard-service thật, Supabase thật). Dùng 1 user có sẵn, tạo dữ liệu rồi dọn sạch."""
import datetime, os, sys, time
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
UID, ROLE = user["id"], user.get("role") or "student"
secret = os.environ["JWT_SECRET_KEY"]


def token(sub=UID, role=ROLE, key=secret, iss="iuh-auth-service", exp=15):
    return jwt.encode({"sub": sub, "role": role, "iss": iss, "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=exp)}, key, algorithm="HS256")


K = "http://localhost:8000/api/v1/flashcards"
H = {"Authorization": f"Bearer {token()}"}
c = httpx.Client(timeout=120)
ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))


# 1) xác thực qua Kong
check("không token -> 401", c.get(f"{K}/decks").status_code == 401)
check("chữ ký sai -> 401", c.get(f"{K}/decks", headers={"Authorization": "Bearer " + token(key="x" * 40)}).status_code == 401)
check("sai issuer -> 401", c.get(f"{K}/decks", headers={"Authorization": "Bearer " + token(iss="evil")}).status_code == 401)
check("token hết hạn -> 401", c.get(f"{K}/decks", headers={"Authorization": "Bearer " + token(exp=-5)}).status_code == 401)
r = c.get(f"{K}/decks", headers=H)
check("token hợp lệ -> 200", r.status_code == 200, f"{len(r.json()['data'])} deck hiện có")
before_decks = {d["id"] for d in r.json()["data"]}

# 2) Header rate limit: route /vocabulary phải chặt hơn route chung
rq = c.get(f"{K}/vocabulary/quota", headers=H)
rl_vocab = {k: v for k, v in rq.headers.items() if "ratelimit-limit" in k.lower()}
rc = c.get(f"{K}/catalog/decks", headers=H)
rl_catalog = {k: v for k, v in rc.headers.items() if "ratelimit-limit" in k.lower()}
print("   header vocabulary:", rl_vocab, "| header catalog:", rl_catalog)
check("route vocabulary có giới hạn 6/phút", any(v == "6" for v in rl_vocab.values()))
check("route catalog dùng giới hạn chung 1000/phút", any(v == "1000" for v in rl_catalog.values()) and not any(v == "6" for v in rl_catalog.values()))
quota = rq.json()["data"]
print("   quota:", quota)

# 3) Catalog: danh sách, xem trước, clone, idempotent
decks = rc.json()["data"]
check("catalog có bộ từ đã xuất bản", len(decks) >= 8, f"{len(decks)} bộ")
check("catalog không lộ trường nội bộ", all("user_id" not in d and "is_system" not in d for d in decks))
target = next(d for d in decks if d["slug"] == "introduce-yourself")
pv = c.get(f"{K}/catalog/decks/{target['id']}/preview?limit=5", headers=H).json()["data"]
check("preview 5 thẻ có nghĩa/ví dụ/dịch", len(pv["cards"]) == 5 and all(x["definition"] for x in pv["cards"]), pv["cards"][0]["term"])
check("preview bộ hệ thống không phải deck cá nhân", c.get(f"{K}/decks/{target['id']}/cards", headers=H).status_code == 403)
check("ghi vào bộ hệ thống qua API cá nhân -> 403", c.post(f"{K}/cards", headers=H, json={"deck_id": target["id"], "front_text": "x", "back_text": "y"}).status_code == 403)
check("xóa bộ hệ thống qua API cá nhân -> 403", c.delete(f"{K}/decks/{target['id']}", headers=H).status_code == 403)

TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date().isoformat()
prior_usage = sb.table("vocab_generation_usage").select("*").eq("user_id", UID).eq("usage_date", TODAY).execute().data
created = []
try:
    cl = c.post(f"{K}/catalog/decks/{target['id']}/clone", headers=H)
    d = cl.json()["data"]
    created.append(d["deck"]["id"])
    check("clone lần 1 tạo deck mới", cl.status_code == 200 and d["created"] and d["inserted"] == target["cards_count"], f"{d['inserted']} thẻ")
    cl2 = c.post(f"{K}/catalog/decks/{target['id']}/clone", headers=H).json()["data"]
    check("clone lần 2 idempotent", cl2["created"] is False and cl2["deck"]["id"] == d["deck"]["id"])
    mine = d["deck"]["id"]
    st = c.get(f"{K}/decks/{mine}/study-stats", headers=H).json()["data"]
    check("thống kê: toàn bộ thẻ là thẻ mới", st["total"] == st["new"] == target["cards_count"], str(st))
    q = c.get(f"{K}/decks/{mine}/study-queue?limit=50&new_limit=10", headers=H).json()["data"]
    check("study-queue tôn trọng new_limit", len(q) == 10 and all(x["is_new"] for x in q))
    check("có 4 đáp án trắc nghiệm", all(x["choices"] and len(x["choices"]) == 4 for x in q))
    rv = c.post(f"{K}/review", headers=H, json={"card_id": q[0]["id"], "grade": 3})
    check("review ghi FSRS thật", rv.status_code == 200 and rv.json()["data"]["state"] == 2 and rv.json()["data"]["stability"] > 0, f"S={rv.json()['data']['stability']}")
    q2 = c.get(f"{K}/decks/{mine}/study-queue?limit=50&new_limit=10", headers=H).json()["data"]
    check("thẻ vừa ôn rời khỏi hàng đợi", q0 := (q[0]["id"] not in {x["id"] for x in q2}))
    sk = c.get(f"{K}/stats/streak?days=84", headers=H).json()["data"]
    check("streak ghi nhận lượt ôn hôm nay", sk["today_reviews"] >= 1 and sk["current_streak"] >= 1, f"streak={sk['current_streak']}")
    row = sb.table("flashcards").select("source,level,state,user_id").eq("deck_id", mine).limit(1).execute().data[0]
    check("DB: thẻ clone có source=curated và thuộc user", row["source"] == "curated" and row["user_id"] == UID)
    orig = sb.table("flashcards").select("state,stability").eq("deck_id", target["id"]).execute().data
    check("DB: thẻ gốc của hệ thống không bị đổi", all(o["state"] == 0 and (o["stability"] or 0) == 0 for o in orig), f"{len(orig)} thẻ gốc")

    # 4) Sinh từ thật qua Kong (tốn 1 lượt + gọi LLM)
    if quota["remaining"] > 0 and "--no-llm" not in sys.argv:
        t0 = time.time()
        g = c.post(f"{K}/vocabulary/generate", headers=H, json={"topic": "Weather and seasons", "level": "A1", "count": 5})
        gj = g.json()
        if g.status_code == 200:
            data = gj["data"]
            check("sinh từ thật qua Kong", data["returned"] >= 4, f"{data['returned']}/5 trong {time.time()-t0:.1f}s, {data['providers']}")
            check("hạn mức tăng 1", data["quota"]["used"] == quota["used"] + 1)
            cm = c.post(f"{K}/decks/from-generated", headers=H, json={
                "client_request_id": f"e2e-{int(time.time())}", "deck": {"title": "[E2E] Weather", "description": "xóa được", "lang_code": "en"},
                "cards": [{"term": i["term"], "definition": i["definition"], "part_of_speech": i["part_of_speech"], "phonetic": i["ipa"],
                           "example": i["example"], "example_translation": i["example_translation"], "level": "A1"} for i in data["items"]],
                "source": {"mode": "topic", "topic": "Weather and seasons", "level": "A1"}})
            cd = cm.json()["data"]
            created.append(cd["deck"]["id"])
            check("lưu deck AI", cm.status_code == 200 and cd["inserted"] == data["returned"] and cd["extended_saved"] is True)
            r1 = sb.table("flashcards").select("source,level,example_translation").eq("deck_id", cd["deck"]["id"]).limit(1).execute().data[0]
            check("DB: cột mở rộng được lưu", r1["source"] == "ai_topic" and r1["level"] == "A1" and r1["example_translation"])
        else:
            print("   (bỏ qua kiểm tra sinh từ vì LLM lỗi:", g.status_code, gj.get("error"), ")")
            check("lỗi LLM trả đúng định dạng & không trừ lượt", gj.get("error", {}).get("code") in ("LLM_UNAVAILABLE", "LLM_TIMEOUT", "LLM_BAD_OUTPUT")
                  and c.get(f"{K}/vocabulary/quota", headers=H).json()["data"]["used"] == quota["used"])

    # 5) rate limit của route vocabulary
    codes = [c.get(f"{K}/vocabulary/quota", headers=H).status_code for _ in range(8)]
    check("route vocabulary bị Kong chặn 429 sau ~6 lượt/phút", 429 in codes, str(codes))
    check("route khác không bị ảnh hưởng", c.get(f"{K}/catalog/decks", headers=H).status_code == 200)
finally:
    for deck_id in created:
        c.delete(f"{K}/decks/{deck_id}", headers=H)
    sb.table("vocab_generation_usage").delete().eq("user_id", UID).eq("usage_date", TODAY).execute()
    if prior_usage:  # khôi phục đúng số lượt đã dùng trước khi chạy thử
        sb.table("vocab_generation_usage").insert(prior_usage).execute()
    left = {d["id"] for d in c.get(f"{K}/decks", headers=H).json()["data"]} - before_decks
    # dọn log ôn tập của thẻ test đã bị xóa theo cascade; kiểm tra không còn deck dư
    check("đã dọn sạch dữ liệu thử", not left, str(left))
print("\nKẾT QUẢ:", "TẤT CẢ ĐẠT" if ok else "CÓ MỤC FAIL")
sys.exit(0 if ok else 1)
