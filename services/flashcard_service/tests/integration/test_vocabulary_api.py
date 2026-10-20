import io

import pytest

from app.services import llm_client
from app.services.llm_client import LLMUnavailable
from conftest import ADMIN, USER_A, USER_B, make_headers

GEN = "/api/v1/flashcards/vocabulary/generate"
IMG = "/api/v1/flashcards/vocabulary/generate-image"
QUOTA = "/api/v1/flashcards/vocabulary/quota"
COMMIT = "/api/v1/flashcards/decks/from-generated"

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 64


def body(**kw):
    base = {"topic": "Environment", "level": "B1", "count": 6}
    base.update(kw)
    return base


def cards_from(data, n=None):
    items = data["items"][:n] if n else data["items"]
    return [{"term": i["term"], "definition": i["definition"], "part_of_speech": i["part_of_speech"],
             "phonetic": i["ipa"], "example": i["example"], "example_translation": i["example_translation"], "level": "B1"}
            for i in items]


class TestAuth:
    @pytest.mark.parametrize("method,url,kw", [
        ("get", QUOTA, {}), ("post", GEN, {"json": body()}), ("post", COMMIT, {"json": {}}),
        ("post", IMG, {"files": {"file": ("a.png", PNG)}}),
    ])
    def test_requires_token(self, api, fake_db, method, url, kw):
        assert getattr(api, method)(url, **kw).status_code == 401

    def test_rejects_forged_expired_and_wrong_issuer_tokens(self, api, fake_db):
        import datetime
        from jose import jwt
        from conftest import JWT_TEST_SECRET

        def tok(secret=JWT_TEST_SECRET, iss="iuh-auth-service", exp=10):
            return {"Authorization": "Bearer " + jwt.encode(
                {"sub": USER_A, "iss": iss, "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=exp)},
                secret, algorithm="HS256")}

        assert api.get(QUOTA, headers=tok()).status_code == 200
        assert api.get(QUOTA, headers=tok(secret="x" * 40)).status_code == 401
        assert api.get(QUOTA, headers=tok(iss="evil")).status_code == 401
        assert api.get(QUOTA, headers=tok(exp=-5)).status_code == 401
        assert api.get(QUOTA, headers={"Authorization": "Bearer garbage"}).status_code == 401


class TestQuotaEndpoint:
    def test_defaults_for_student_public_and_admin(self, api, fake_db, headers_a, headers_admin):
        data = api.get(QUOTA, headers=headers_a).json()["data"]  # headers_a: role=student (sinh viên/giảng viên IUH)
        assert (data["tier"], data["tier_label"], data["limit"], data["used"], data["remaining"]) == ("student", "SINH VIÊN IUH", 10, 0, 10)
        public = api.get(QUOTA, headers=make_headers(USER_B, role="public")).json()["data"]
        assert (public["tier"], public["tier_label"], public["limit"]) == ("normal", "THƯỜNG", 3)
        admin = api.get(QUOTA, headers=headers_admin).json()["data"]
        assert (admin["tier"], admin["tier_label"], admin["limit"]) == ("admin", "QUẢN TRỊ", 50)


class TestGenerate:
    def test_topic_generation_response_shape(self, api, fake_db, fake_llm, headers_a):
        res = api.post(GEN, headers=headers_a, json=body(count=6))
        assert res.status_code == 200
        data = res.json()["data"]
        assert res.json()["ok"] is True
        assert data["returned"] == 6 and data["mode"] == "topic" and data["level"] == "B1"
        assert data["quota"]["used"] == 1 and data["quota"]["remaining"] == 9
        item = data["items"][0]
        assert {"temp_id", "term", "part_of_speech", "ipa", "definition", "example", "example_translation", "warnings", "verified"} <= item.keys()

    def test_text_mode(self, api, fake_db, fake_llm, headers_a):
        fake_llm.words = ["habitat", "ozone", "compost", "drought", "erosion", "organic"]
        res = api.post(GEN, headers=headers_a, json={"mode": "text", "text": "A passage about habitat, ozone and compost.", "level": "B2", "count": 5})
        assert res.status_code == 200 and res.json()["data"]["mode"] == "text"

    def test_nothing_is_written_to_the_database(self, api, fake_db, fake_llm, headers_a):
        api.post(GEN, headers=headers_a, json=body())
        assert fake_db.rows("flashcards") == [] and fake_db.rows("flashcard_decks") == []

    def test_quota_is_exhausted_after_three_successes_for_public_accounts(self, api, fake_db, fake_llm):
        headers_a = make_headers(USER_A, role="public")
        for _ in range(3):
            assert api.post(GEN, headers=headers_a, json=body()).status_code == 200
        res = api.post(GEN, headers=headers_a, json=body())
        assert res.status_code == 429
        assert res.json() == {"ok": False, "error": {"code": "QUOTA_EXCEEDED", "message": res.json()["error"]["message"]}}
        assert api.post(GEN, headers=make_headers(USER_B), json=body()).status_code == 200  # người khác vẫn dùng được

    @pytest.mark.parametrize("stage_error,status,code", [
        (LLMUnavailable("quota", "x"), 503, "LLM_UNAVAILABLE"),
        (LLMUnavailable("timeout", "x"), 504, "LLM_TIMEOUT"),
    ])
    def test_failed_generation_does_not_consume_quota(self, api, fake_db, fake_llm, headers_a, stage_error, status, code):
        fake_llm.fail = {"select": stage_error}
        res = api.post(GEN, headers=headers_a, json=body())
        assert res.status_code == status and res.json()["error"]["code"] == code
        assert api.get(QUOTA, headers=headers_a).json()["data"]["used"] == 0

    def test_invalid_topic_is_400_and_refunded(self, api, fake_db, fake_llm, headers_a):
        fake_llm.reason = "invalid_topic"
        res = api.post(GEN, headers=headers_a, json=body(topic="asdf qwer"))
        assert (res.status_code, res.json()["error"]["code"]) == (400, "INVALID_TOPIC")
        assert api.get(QUOTA, headers=headers_a).json()["data"]["used"] == 0

    def test_unexpected_exception_is_500_with_refund(self, api, fake_db, headers_a, monkeypatch):
        async def boom(*a, **k):
            raise RuntimeError("kaboom")

        monkeypatch.setattr(llm_client, "generate_json", boom)
        res = api.post(GEN, headers=headers_a, json=body())
        assert (res.status_code, res.json()["error"]["code"]) == (500, "INTERNAL_ERROR")
        assert "kaboom" not in res.text  # không lộ chi tiết nội bộ
        assert api.get(QUOTA, headers=headers_a).json()["data"]["used"] == 0

    @pytest.mark.parametrize("payload", [
        {"topic": "", "level": "B1", "count": 10}, {"topic": "ok topic", "level": "Z9", "count": 10},
        {"topic": "ok topic", "level": "B1", "count": 4}, {"topic": "ok topic", "level": "B1", "count": 51},
        {"topic": "x" * 101, "level": "B1", "count": 10}, {"mode": "text", "text": "short", "count": 10},
        {"topic": "ok topic", "lang_code": "vi"}, {"topic": "ok topic", "lang_code": "xx"}, {"topic": "ok", "purpose": "hacking"},
    ])
    def test_validation_errors_are_422_and_free(self, api, fake_db, fake_llm, headers_a, payload):
        assert api.post(GEN, headers=headers_a, json=payload).status_code == 422
        assert fake_llm.calls == []
        assert api.get(QUOTA, headers=headers_a).json()["data"]["used"] == 0

    def test_existing_deck_terms_are_excluded(self, api, fake_db, fake_llm, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_A, title="Mine", lang_code="en")
        for term in ("sustainable", "pollution"):
            fake_db.seed("flashcards", deck_id=deck["id"], user_id=USER_A, term=term, definition="x")
        res = api.post(GEN, headers=headers_a, json=body(count=5, deck_id=deck["id"]))
        assert res.status_code == 200
        terms = {i["term"] for i in res.json()["data"]["items"]}
        assert not ({"sustainable", "pollution"} & terms)

    def test_other_users_deck_is_403_and_costs_nothing(self, api, fake_db, fake_llm, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_B, title="Theirs", lang_code="en")
        res = api.post(GEN, headers=headers_a, json=body(deck_id=deck["id"]))
        assert res.status_code == 403 and fake_llm.calls == []
        assert api.get(QUOTA, headers=headers_a).json()["data"]["used"] == 0

    def test_student_is_exhausted_after_ten(self, api, fake_db, fake_llm, headers_a):
        for _ in range(10):
            assert api.post(GEN, headers=headers_a, json=body()).status_code == 200
        res = api.post(GEN, headers=headers_a, json=body())
        assert res.status_code == 429 and res.json()["error"]["code"] == "QUOTA_EXCEEDED"
        assert "10 lượt" in res.json()["error"]["message"]

    def test_admin_gets_the_larger_quota(self, api, fake_db, fake_llm, headers_admin):
        for _ in range(12):  # vượt hạn mức của sinh viên (10) và tài khoản thường (3)
            assert api.post(GEN, headers=headers_admin, json=body()).status_code == 200

    def test_client_supplied_identity_headers_are_ignored(self, api, fake_db, fake_llm, headers_a):
        headers = {**make_headers(USER_A, role="public"), "X-User-ID": USER_B, "X-User-Role": "admin"}
        api.post(GEN, headers=headers, json=body())
        assert api.get(QUOTA, headers=headers).json()["data"]["tier"] == "normal"
        assert api.get(QUOTA, headers=make_headers(USER_B)).json()["data"]["used"] == 0


class TestGenerateFromImage:
    def post(self, api, headers, raw, name="pic.png", **form):
        data = {"level": "B1", "count": "6", **form}
        return api.post(IMG, headers=headers, files={"file": (name, io.BytesIO(raw))}, data=data)

    @pytest.mark.parametrize("raw", [PNG, JPEG, WEBP])
    def test_supported_formats_reach_the_llm_as_images(self, api, fake_db, fake_llm, headers_a, raw):
        fake_llm.words = ["warning", "hazardous", "disposal", "personnel", "protective", "authorized"]
        res = self.post(api, headers_a, raw)
        assert res.status_code == 200 and res.json()["data"]["mode"] == "image"
        images = fake_llm.calls[0]["images"]
        assert len(images) == 1 and images[0][1] == raw

    def test_extension_is_irrelevant_only_content_is_checked(self, api, fake_db, fake_llm, headers_a):
        assert self.post(api, headers_a, b"%PDF-1.7 not an image", name="evil.png").status_code == 415
        fake_llm.words = ["warning", "hazardous", "disposal", "personnel", "protective", "authorized"]
        assert self.post(api, headers_a, PNG, name="renamed.txt").status_code == 200

    @pytest.mark.parametrize("raw", [b"", b"GIF89a....", b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", b"\x00" * 50])
    def test_non_images_are_415_and_free(self, api, fake_db, fake_llm, headers_a, raw):
        res = self.post(api, headers_a, raw)
        assert (res.status_code, res.json()["error"]["code"]) == (415, "UNSUPPORTED_IMAGE")
        assert fake_llm.calls == [] and api.get(QUOTA, headers=headers_a).json()["data"]["used"] == 0

    def test_over_5mb_is_413(self, api, fake_db, fake_llm, headers_a):
        res = self.post(api, headers_a, PNG + b"\x00" * (5 * 1024 * 1024))
        assert (res.status_code, res.json()["error"]["code"]) == (413, "IMAGE_TOO_LARGE")
        assert fake_llm.calls == []

    @pytest.mark.parametrize("form", [{"count": "3"}, {"count": "99"}, {"level": "Z1"}, {"count": "abc"}])
    def test_invalid_options_are_rejected(self, api, fake_db, fake_llm, headers_a, form):
        assert self.post(api, headers_a, PNG, **form).status_code in (422,)

    def test_no_readable_content_is_422_no_content_and_refunded(self, api, fake_db, fake_llm, headers_a):
        fake_llm.reason = "no_content"
        res = self.post(api, headers_a, PNG)
        assert (res.status_code, res.json()["error"]["code"]) == (422, "NO_CONTENT")
        assert api.get(QUOTA, headers=headers_a).json()["data"]["used"] == 0

    def test_without_vision_provider_is_unavailable(self, api, fake_db, headers_a, monkeypatch):
        for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENAI_BASE_URL"):
            monkeypatch.delenv(key, raising=False)
        res = self.post(api, headers_a, PNG)
        assert (res.status_code, res.json()["error"]["code"]) == (503, "LLM_UNAVAILABLE")
        assert api.get(QUOTA, headers=headers_a).json()["data"]["used"] == 0


class TestCommit:
    def commit_body(self, cards, rid="req-00000001", **kw):
        base = {"client_request_id": rid, "deck": {"title": "Environment (B1)", "description": "AI", "lang_code": "en"},
                "cards": cards, "source": {"mode": "topic", "topic": "Environment", "level": "B1"}}
        base.update(kw)
        return base

    def generated(self, api, headers, count=6):
        return api.post(GEN, headers=headers, json=body(count=count)).json()["data"]

    def test_creates_deck_and_cards_with_metadata(self, api, fake_db, fake_llm, headers_a):
        cards = cards_from(self.generated(api, headers_a))
        res = api.post(COMMIT, headers=headers_a, json=self.commit_body(cards))
        assert res.status_code == 200
        data = res.json()["data"]
        assert (data["inserted"], data["skipped_duplicates"], data["extended_saved"]) == (6, 0, True)
        (deck,) = fake_db.rows("flashcard_decks", user_id=USER_A)
        assert deck["title"] == "Environment (B1)" and deck["id"] == data["deck"]["id"]
        rows = fake_db.rows("flashcards", deck_id=deck["id"])
        assert len(rows) == 6 and {r["source"] for r in rows} == {"ai_topic"} and {r["level"] for r in rows} == {"B1"}
        assert all(r["user_id"] == USER_A and r["state"] == 0 and r["example_translation"] for r in rows)

    def test_idempotent_by_client_request_id(self, api, fake_db, fake_llm, headers_a):
        payload = self.commit_body(cards_from(self.generated(api, headers_a)))
        first = api.post(COMMIT, headers=headers_a, json=payload).json()["data"]
        second = api.post(COMMIT, headers=headers_a, json=payload).json()["data"]
        assert second["idempotent_replay"] is True and second["deck"]["id"] == first["deck"]["id"]
        assert len(fake_db.rows("flashcard_decks")) == 1 and len(fake_db.rows("flashcards")) == 6

    def test_same_request_id_from_another_user_is_not_a_replay(self, api, fake_db, fake_llm, headers_a, headers_b):
        payload = self.commit_body(cards_from(self.generated(api, headers_a, 5)))
        api.post(COMMIT, headers=headers_a, json=payload)
        other = api.post(COMMIT, headers=headers_b, json=payload).json()["data"]
        assert "idempotent_replay" not in other and len(fake_db.rows("flashcard_decks")) == 2

    def test_add_to_existing_deck_skips_duplicates(self, api, fake_db, fake_llm, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_A, title="Mine", lang_code="en")
        fake_db.seed("flashcards", deck_id=deck["id"], user_id=USER_A, term="Sustainable", definition="x")
        cards = cards_from(self.generated(api, headers_a, 5))
        res = api.post(COMMIT, headers=headers_a, json={"client_request_id": "req-00000002", "deck_id": deck["id"], "cards": cards})
        data = res.json()["data"]
        assert data["skipped_duplicates"] == 1 and data["inserted"] == len(cards) - 1
        assert len(fake_db.rows("flashcard_decks")) == 1

    def test_other_users_deck_is_403(self, api, fake_db, fake_llm, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_B, title="Theirs", lang_code="en")
        res = api.post(COMMIT, headers=headers_a, json={"client_request_id": "req-00000003", "deck_id": deck["id"],
                                                         "cards": [{"term": "a", "definition": "b"}]})
        assert res.status_code == 403 and fake_db.rows("flashcards") == []

    def test_database_failure_is_503_and_leaves_no_empty_deck(self, api, fake_db, fake_llm, headers_a):
        payload = self.commit_body(cards_from(self.generated(api, headers_a)))
        fake_db.fail_when("insert", "flashcards")
        res = api.post(COMMIT, headers=headers_a, json=payload)
        assert res.status_code == 503 and fake_db.rows("flashcard_decks") == []
        fake_db.fail.clear()
        retry = api.post(COMMIT, headers=headers_a, json=payload)  # lỗi không bị cache: thử lại thành công
        assert retry.status_code == 200 and retry.json()["data"]["inserted"] == 6

    @pytest.mark.parametrize("payload", [
        {"client_request_id": "short", "deck": {"title": "T"}, "cards": [{"term": "a", "definition": "b"}]},
        {"client_request_id": "req-00000004", "cards": [{"term": "a", "definition": "b"}]},
        {"client_request_id": "req-00000004", "deck": {"title": "T"}, "cards": []},
        {"client_request_id": "req-00000004", "deck": {"title": ""}, "cards": [{"term": "a", "definition": "b"}]},
        {"client_request_id": "req-00000004", "deck": {"title": "T"}, "cards": [{"term": "", "definition": "b"}]},
        {"client_request_id": "req-00000004", "deck": {"title": "T"}, "cards": [{"term": "a", "definition": "b" * 1001}]},
        {"client_request_id": "req-00000004", "deck": {"title": "T"}, "cards": [{"term": "a", "definition": "b"}] * 201},
    ])
    def test_invalid_payloads_are_422(self, api, fake_db, headers_a, payload):
        assert api.post(COMMIT, headers=headers_a, json=payload).status_code == 422
        assert fake_db.rows("flashcard_decks") == []

    def test_pos_is_normalised_and_unknown_defaults_sensibly(self, api, fake_db, headers_a):
        cards = [{"term": "run", "definition": "chạy", "part_of_speech": "v."},
                 {"term": "give up", "definition": "bỏ cuộc", "part_of_speech": "???"},
                 {"term": "cat", "definition": "mèo"}]
        api.post(COMMIT, headers=headers_a, json=self.commit_body(cards, rid="req-00000005"))
        pos = {r["term"]: r["part_of_speech"] for r in fake_db.rows("flashcards")}
        assert pos == {"run": "verb", "give up": "phrase", "cat": "noun"}

    def test_markup_in_text_is_stored_verbatim_not_executed(self, api, fake_db, headers_a):
        cards = [{"term": "<img src=x onerror=alert(1)>", "definition": "<script>alert(1)</script>"}]
        res = api.post(COMMIT, headers=headers_a, json=self.commit_body(cards, rid="req-00000006"))
        assert res.status_code == 200  # React escape khi hiển thị; backend chỉ lưu chuỗi thô
        assert fake_db.rows("flashcards")[0]["definition"] == "<script>alert(1)</script>"

    def test_end_to_end_generate_commit_study_review(self, api, fake_db, fake_llm, headers_a):
        cards = cards_from(self.generated(api, headers_a, 6))
        deck_id = api.post(COMMIT, headers=headers_a, json=self.commit_body(cards, rid="req-00000007")).json()["data"]["deck"]["id"]
        queue = api.get(f"/api/v1/flashcards/decks/{deck_id}/study-queue", headers=headers_a).json()["data"]
        assert len(queue) == 6 and all(c["is_new"] and c["recommended_mode"] == "flip" for c in queue)
        assert all(len(c["choices"]) == 4 for c in queue)
        review = api.post("/api/v1/flashcards/review", headers=headers_a, json={"card_id": queue[0]["id"], "grade": 3})
        assert review.status_code == 200 and review.json()["data"]["state"] == 2
        stats = api.get(f"/api/v1/flashcards/decks/{deck_id}/study-stats", headers=headers_a).json()["data"]
        assert (stats["total"], stats["new"], stats["learning"]) == (6, 5, 1)
        assert len(api.get(f"/api/v1/flashcards/decks/{deck_id}/study-queue", headers=headers_a).json()["data"]) == 5
