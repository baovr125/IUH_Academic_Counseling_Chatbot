"""E2E trò chơi qua Kong + Supabase thật. Dùng: python e2e_games.py [pre|post]. Tạo sổ thử rồi dọn sạch."""
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
UID = user["id"]
tok = jwt.encode({"sub": UID, "role": user.get("role") or "student", "iss": "iuh-auth-service",
                  "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=20)}, os.environ["JWT_SECRET_KEY"], algorithm="HS256")
H = {"Authorization": f"Bearer {tok}"}
K = "http://localhost:8000/api/v1/flashcards"
c = httpx.Client(timeout=120)
ok = True
TAG = uuid.uuid4().hex[:6]


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))


deck_ids = []
try:
    for lang, words in (("de", ["Haus", "Baum", "Tür", "Hund", "Katze", "Wasser"]), ("ja", ["水", "火", "木", "金", "土", "日"])):
        d = c.post(f"{K}/decks", headers=H, json={"title": f"E2E-GAME-{TAG}-{lang}", "lang_code": lang}).json()["data"]
        deck_ids.append(d["id"])
        for i, w in enumerate(words):
            r = c.post(f"{K}/cards", headers=H, json={"deck_id": d["id"], "front_text": w, "back_text": f"nghĩa {w} {TAG}"})
            assert r.status_code == 200, r.text
        # Làm các thẻ "đã học và đến hạn" để kiểm tra cập nhật lịch ôn.
        past = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)).isoformat()
        sb.table("flashcards").update({"state": 2, "reps": 1, "due": past, "last_review": past, "stability": 2.0, "difficulty": 3.0}).eq("deck_id", d["id"]).execute()
    de, ja = deck_ids

    check("không token -> 401", c.get(f"{K}/games/stats").status_code == 401)
    for game in ("match", "speed", "builder"):
        r = c.get(f"{K}/games/{game}/cards", headers=H, params={"deck_id": de})
        d = r.json()["data"]
        check(f"cards {game} (de) playable", r.status_code == 200 and d["playable"] and len(d["cards"]) >= 4 and d["due_count"] == len(d["cards"]), f"{len(d['cards'])} thẻ")
    sp = c.get(f"{K}/games/speed/cards", headers=H, params={"deck_id": de}).json()["data"]["cards"]
    check("speed: 4 đáp án gồm đáp án đúng", all(len(x["choices"]) == 4 and x["definition"] in x["choices"] for x in sp))
    r = c.get(f"{K}/games/builder/cards", headers=H, params={"deck_id": ja}).json()["data"]
    check("builder với tiếng Nhật -> không chơi được, có lý do", r["playable"] is False and "chữ cái" in r["reason"])
    check("match với tiếng Nhật chơi được", c.get(f"{K}/games/match/cards", headers=H, params={"deck_id": ja}).json()["data"]["playable"])

    if MODE == "pre":
        r = c.get(f"{K}/games/stats", headers=H)
        check("trước migration 006: /games/stats -> 503 MIGRATION_REQUIRED", r.status_code == 503 and r.json()["error"]["code"] == "MIGRATION_REQUIRED" and "006" in r.json()["error"]["message"], r.text[:100])
        mc = c.get(f"{K}/games/match/cards", headers=H, params={"deck_id": de}).json()["data"]["cards"]
        r = c.post(f"{K}/games/sessions", headers=H, json={"client_request_id": f"e2e-{TAG}-pre01", "game": "match", "deck_id": de,
                   "items": [{"card_id": x["id"], "correct": True} for x in mc]})
        check("trước migration 006: POST /games/sessions -> 503 và KHÔNG đổi lịch ôn", r.status_code == 503, r.text[:100])
        left = sb.table("review_logs").select("id").in_("card_id", [x["id"] for x in mc]).execute().data
        check("không có review_log nào bị ghi", len(left) == 0)
    else:
        mc = c.get(f"{K}/games/match/cards", headers=H, params={"deck_id": de}).json()["data"]["cards"]
        body = {"client_request_id": f"e2e-{TAG}-m1", "game": "match", "mode": "relax", "deck_id": de, "duration_ms": 20000,
                "items": [{"card_id": x["id"], "correct": True, "attempts": 0} for x in mc]}
        r = c.post(f"{K}/games/sessions", headers=H, json={**body, "score": 99999})
        d = r.json()["data"]
        check("ghi ván Ghép cặp: điểm do máy chủ tính (bỏ qua score client)", r.status_code == 200 and d["session"]["score"] == 600 and d["session"]["stars"] == 3, str(d["session"]))
        check("ván đầu là kỷ lục + tính lịch ôn cho 6 thẻ đến hạn", d["is_record"] and d["session"]["reviewed_count"] == 6)
        logs = sb.table("review_logs").select("grade").in_("card_id", [x["id"] for x in mc]).execute().data
        check("review_logs: 6 dòng, toàn Good (3), không Easy", len(logs) == 6 and all(l["grade"] == 3 for l in logs))
        again = c.post(f"{K}/games/sessions", headers=H, json=body).json()["data"]
        check("gửi lại cùng client_request_id -> phát lại, không ghi thêm", again["idempotent_replay"] and len(sb.table("review_logs").select("id").in_("card_id", [x["id"] for x in mc]).execute().data) == 6)
        worse = c.post(f"{K}/games/sessions", headers=H, json={**body, "client_request_id": f"e2e-{TAG}-m2",
                       "items": [{"card_id": x["id"], "correct": True, "attempts": 3} for x in mc]}).json()["data"]
        check("ván kém hơn không phải kỷ lục", worse["is_record"] is False and worse["previous_best"] == 600)
        sc = c.get(f"{K}/games/speed/cards", headers=H, params={"deck_id": de}).json()["data"]["cards"]
        sp_r = c.post(f"{K}/games/sessions", headers=H, json={"client_request_id": f"e2e-{TAG}-s1", "game": "speed", "mode": "challenge", "deck_id": de,
                      "items": [{"card_id": x["id"], "correct": True} for x in sc[:4]] + [{"card_id": sc[4]["id"], "correct": False, "attempts": 1}]}).json()["data"]
        check("Đua 60 giây: combo/điểm đúng", sp_r["session"]["score"] == 10 * 3 + 20 and sp_r["session"]["best_combo"] == 4, str(sp_r["session"]))
        r = c.post(f"{K}/games/sessions", headers=H, json={"client_request_id": f"e2e-{TAG}-b1", "game": "builder", "deck_id": ja, "items": [{"card_id": "x", "correct": True}]})
        check("Xếp chữ với tiếng Nhật -> 422", r.status_code == 422 and r.json()["error"]["code"] == "GAME_UNSUPPORTED_LANG", r.text[:100])
        st = c.get(f"{K}/games/stats", headers=H).json()["data"]
        check("stats: XP/cấp độ và kỷ lục", st["level"]["xp"] >= 90 and st["games"]["match"]["best"]["relax"]["score"] == 600 and st["plays_today"] >= 3, str(st["level"]))
        st_de = c.get(f"{K}/games/stats", headers=H, params={"lang_code": "de"}).json()["data"]
        st_ja = c.get(f"{K}/games/stats", headers=H, params={"lang_code": "ja"}).json()["data"]
        check("stats lọc theo ngôn ngữ", st_de["plays_total"] >= 3 and st_ja["plays_total"] == 0)

    # ---- Bắn bóng nghĩa
    sh = c.get(f"{K}/games/shooter/cards", headers=H, params={"deck_id": de}).json()["data"]
    check("shooter cards (de): chơi được, 4 đáp án/ thẻ", sh["playable"] and all(len(x["choices"]) == 4 for x in sh["cards"]), f"{len(sh['cards'])} thẻ")
    check("shooter cards (ja): chơi được (mọi ngôn ngữ)", c.get(f"{K}/games/shooter/cards", headers=H, params={"deck_id": ja}).json()["data"]["playable"])
    shooter_body = {"client_request_id": f"e2e-{TAG}-sh1", "game": "shooter", "mode": "challenge", "deck_id": de, "duration_ms": 40000,
                    "items": [{"card_id": x["id"], "correct": True, "attempts": 0} for x in sh["cards"][:3]]
                             + [{"card_id": sh["cards"][3]["id"], "correct": True, "attempts": 1}, {"card_id": sh["cards"][4]["id"], "correct": False}]}
    r = c.post(f"{K}/games/sessions", headers=H, json=shooter_body)
    if MODE == "pre":
        check("trước migration 007: lưu ván shooter -> 503 MIGRATION_REQUIRED nêu migration 007", r.status_code == 503 and "007" in r.text, r.text[:140])
    else:
        d = r.json()["data"]
        check("sau migration 007: ván shooter được chấm (10+10+10+7+0=37)", r.status_code == 200 and d["session"]["score"] == 37 and d["session"]["game"] == "shooter", str(d["session"]))
        st = c.get(f"{K}/games/stats", headers=H).json()["data"]
        check("stats có kỷ lục shooter", st["games"]["shooter"]["best"]["challenge"]["score"] == 37)
finally:
    for did in deck_ids:
        sb.table("flashcard_game_sessions").delete().eq("deck_id", did).execute() if MODE == "post" else None
        ids = [r["id"] for r in sb.table("flashcards").select("id").eq("deck_id", did).execute().data]
        if ids:
            sb.table("review_logs").delete().in_("card_id", ids).execute()
        sb.table("flashcards").delete().eq("deck_id", did).execute()
        sb.table("flashcard_decks").delete().eq("id", did).execute()

print("\nKẾT QUẢ:", "TẤT CẢ ĐẠT" if ok else "CÓ LỖI")
sys.exit(0 if ok else 1)
