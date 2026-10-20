"""Hồi quy các tính năng có từ trước + ma trận IDOR ở mức HTTP (người dùng B tấn công tài nguyên của A)."""
import io
import json

import openpyxl
import pytest

from app import rabbitmq_consumer
from app.services import flashcard_service as fs
from conftest import USER_A, USER_B, make_headers

BASE = "/api/v1/flashcards"


@pytest.fixture
def events(monkeypatch):
    """Ghi lại các event flashcard.created thay vì gửi RabbitMQ."""
    sent = []

    async def record(**kw):
        sent.append(kw)

    import app.routers.flashcards as router
    import app.services.excel_importer as importer
    monkeypatch.setattr(router, "publish_flashcard_created_event", record)
    monkeypatch.setattr(importer, "publish_flashcard_created_event", record)
    monkeypatch.setattr(rabbitmq_consumer, "publish_flashcard_created_event", record)
    return sent


def xlsx(rows) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def upload(api, deck_id, headers, raw, name="words.xlsx", lang=None):
    query = f"?lang_code={lang}" if lang else ""
    return api.post(f"{BASE}/decks/{deck_id}/import-excel{query}", headers=headers, files={"file": (name, io.BytesIO(raw))})


class TestDeckAndCardCrud:
    def test_full_lifecycle(self, api, fake_db, events, headers_a):
        deck = api.post(f"{BASE}/decks", headers=headers_a, json={"title": "Mine", "description": "d", "lang_code": "en"}).json()["data"]
        assert fake_db.rows("flashcard_decks", id=deck["id"])[0]["user_id"] == USER_A

        card = api.post(f"{BASE}/cards", headers=headers_a, json={
            "deck_id": deck["id"], "front_text": "hello", "back_text": "xin chào", "phonetic": "/həˈloʊ/",
            "example_sentence": "Hello there.", "part_of_speech": "interjection", "lang_code": "en"}).json()["data"]
        assert events and events[0]["term"] == "hello"  # event tạo âm thanh được bắn
        row = dict(fake_db.rows("flashcards", id=card["id"])[0])  # bản sao: rows() trả về chính dòng trong bộ nhớ
        assert (row["term"], row["definition"], row["example"], row["state"]) == ("hello", "xin chào", "Hello there.", 0)
        assert row["audio_url"].startswith("/api/v1/translate/audio/terms/en_")

        assert api.put(f"{BASE}/cards/{card['id']}", headers=headers_a, json={"front_text": "hi", "back_text": "chào"}).status_code == 200
        updated = fake_db.rows("flashcards", id=card["id"])[0]
        assert (updated["term"], updated["definition"]) == ("hi", "chào") and updated["audio_url"] != row["audio_url"]

        assert api.get(f"{BASE}/decks", headers=headers_a).json()["data"][0]["cards_count"] == 1
        assert api.delete(f"{BASE}/cards/{card['id']}", headers=headers_a).json()["data"] == {"deleted": True}
        assert api.delete(f"{BASE}/decks/{deck['id']}", headers=headers_a).status_code == 200
        assert fake_db.rows("flashcard_decks") == [] and fake_db.rows("flashcards") == []

    def test_deleting_a_deck_removes_its_cards_and_logs(self, api, fake_db, headers_a):
        deck = fake_db.seed("flashcard_decks", user_id=USER_A, title="D", lang_code="en")
        card = fake_db.seed("flashcards", deck_id=deck["id"], user_id=USER_A, term="a", definition="b")
        api.post(f"{BASE}/review", headers=headers_a, json={"card_id": card["id"], "grade": 3})
        assert fake_db.rows("review_logs")
        assert api.delete(f"{BASE}/decks/{deck['id']}", headers=headers_a).status_code == 200
        assert fake_db.rows("flashcards") == [] and fake_db.rows("review_logs") == []

    @pytest.mark.parametrize("grade", [0, 5, -1, 99])
    def test_review_rejects_out_of_range_grades(self, api, fake_db, headers_a, grade):
        assert api.post(f"{BASE}/review", headers=headers_a, json={"card_id": "x", "grade": grade}).status_code == 422

    def test_review_of_unknown_card_is_404_not_a_phantom_card(self, api, fake_db, headers_a):
        res = api.post(f"{BASE}/review", headers=headers_a, json={"card_id": "00000000-0000-4000-8000-000000000000", "grade": 3})
        assert res.status_code == 404 and fake_db.rows("review_logs") == []

    def test_streak_endpoint(self, api, fake_db, headers_a):
        data = api.get(f"{BASE}/stats/streak?days=84", headers=headers_a).json()["data"]
        assert len(data["days"]) == 84 and data["current_streak"] == 0
        assert api.get(f"{BASE}/stats/streak?days=3", headers=headers_a).status_code == 422

    def test_health(self, api):
        assert api.get("/health").json()["ok"] is True


class TestExcelImport:
    def deck(self, db):
        return db.seed("flashcard_decks", user_id=USER_A, title="Imp", lang_code="en")

    def test_import_with_headers_dedupe_and_pos_normalisation(self, api, fake_db, events, headers_a):
        deck = self.deck(fake_db)
        raw = xlsx([["Term", "Nghĩa", "IPA", "Từ loại", "Ví dụ"],
                    ["quickly", "nhanh", "/ˈkwɪkli/", "adv", "Run quickly."],
                    ["under", "dưới", "", "preposition", ""],
                    ["Quickly", "trùng", "", "", ""],
                    ["give up", "bỏ cuộc", "", "phrasal verb", ""],
                    ["", "no term", "", "", ""]])
        res = upload(api, deck["id"], headers_a, raw)
        data = res.json()["data"]
        assert res.status_code == 200 and (data["inserted"], data["skipped_duplicates"]) == (3, 0)  # trùng trong file bị lọc ở bước parse
        pos = {r["term"]: r["part_of_speech"] for r in fake_db.rows("flashcards")}
        assert pos == {"quickly": "adverb", "under": "preposition", "give up": "phrasal verb"}
        assert len(events) == 3

    def test_second_import_skips_existing_terms(self, api, fake_db, events, headers_a):
        deck = self.deck(fake_db)
        raw = xlsx([["term", "meaning"], ["a", "một"], ["b", "hai"]])
        upload(api, deck["id"], headers_a, raw)
        again = upload(api, deck["id"], headers_a, xlsx([["term", "meaning"], ["A", "một"], ["c", "ba"]])).json()["data"]
        assert (again["inserted"], again["skipped_duplicates"]) == (1, 1)

    def test_csv_and_headerless_files(self, api, fake_db, events, headers_a):
        deck = self.deck(fake_db)
        csv_bytes = "term,definition\nalpha,một\nbeta,hai\n".encode("utf-8")
        assert upload(api, deck["id"], headers_a, csv_bytes, "w.csv").json()["data"]["inserted"] == 2
        assert upload(api, deck["id"], headers_a, xlsx([["gamma", "ba"], ["delta", "bốn"]])).json()["data"]["inserted"] == 2

    @pytest.mark.parametrize("name,raw,status", [
        pytest.param("words.txt", b"a,b", 400, id="wrong-extension"),
        pytest.param("words.xlsx", b"this is not a zip", 400, id="corrupt-xlsx"),
        pytest.param("empty.csv", b"", 400, id="empty"),
        pytest.param("big.csv", b"a,b\n" + b"x" * (5 * 1024 * 1024 + 1), 400, id="over-5mb"),
        pytest.param("only_header.csv", b"term,definition\n", 400, id="header-only"),
    ])
    def test_bad_files_are_rejected(self, api, fake_db, events, headers_a, name, raw, status):
        deck = self.deck(fake_db)
        assert upload(api, deck["id"], headers_a, raw, name).status_code == status
        assert fake_db.rows("flashcards") == []

    def test_import_into_missing_deck_creates_it_for_the_caller(self, api, fake_db, events, headers_a):
        deck_id = "44444444-4444-4444-8444-444444444444"
        # Không có ngôn ngữ thì KHÔNG đoán: 422 và không tạo deck
        assert upload(api, deck_id, headers_a, xlsx([["a", "b"]])).status_code == 422
        assert fake_db.rows("flashcard_decks") == []
        assert upload(api, deck_id, headers_a, xlsx([["a", "b"]]), lang="de").status_code == 200
        assert fake_db.rows("flashcard_decks", id=deck_id)[0]["user_id"] == USER_A
        assert fake_db.rows("flashcard_decks", id=deck_id)[0]["lang_code"] == "de"

    def test_template_download(self, api):
        res = api.get(f"{BASE}/template")
        assert res.status_code == 200 and res.content[:2] == b"PK"


class _Message:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode()

    def process(self):
        class Ctx:
            async def __aenter__(self_inner):
                return self

            async def __aexit__(self_inner, *exc):
                return False

        return Ctx()


class TestDocTranslatedConsumer:
    payload = {"user_id": USER_A, "file_name": "bai-giang.pdf", "doc_id": "d1", "source_lang": "en",
               "glossary_json": [{"term": "polymorphism", "definition": "đa hình", "example": "Polymorphism is key."},
                                 {"term": "inheritance", "translation": "kế thừa"},
                                 {"term": "", "definition": "bỏ"}]}

    async def test_creates_deck_and_cards_and_events(self, fake_db, events):
        await rabbitmq_consumer.process_doc_translated_event(_Message(self.payload))
        (deck,) = fake_db.rows("flashcard_decks", user_id=USER_A)
        assert deck["title"] == "Thuật ngữ: bai-giang.pdf"
        assert {r["term"] for r in fake_db.rows("flashcards", deck_id=deck["id"])} == {"polymorphism", "inheritance"}
        assert len(events) == 2

    async def test_redelivery_is_idempotent(self, fake_db, events):
        for _ in range(3):
            await rabbitmq_consumer.process_doc_translated_event(_Message(self.payload))
        assert len(fake_db.rows("flashcard_decks")) == 1 and len(fake_db.rows("flashcards")) == 2

    async def test_empty_glossary_creates_nothing(self, fake_db, events):
        await rabbitmq_consumer.process_doc_translated_event(_Message({**self.payload, "glossary_json": []}))
        assert fake_db.rows("flashcard_decks") == []

    async def test_database_failure_does_not_crash_the_consumer(self, fake_db, events):
        fake_db.fail_when("insert", "flashcard_decks")
        await rabbitmq_consumer.process_doc_translated_event(_Message(self.payload))  # lỗi được log, không ném ra
        assert fake_db.rows("flashcards") == []

    async def test_audio_ready_event_attaches_url(self, fake_db):
        deck = fake_db.seed("flashcard_decks", user_id=USER_A, title="D", lang_code="en")
        card = fake_db.seed("flashcards", deck_id=deck["id"], user_id=USER_A, term="a", definition="b", audio_url=None)
        await rabbitmq_consumer.process_audio_ready_event(_Message({"card_id": card["id"], "audio_url": "/minio/a.mp3"}))
        assert fake_db.rows("flashcards", id=card["id"])[0]["audio_url"] == "/minio/a.mp3"


class TestIdorMatrixOverHttp:
    @pytest.fixture
    def victim(self, fake_db):
        deck = fake_db.seed("flashcard_decks", user_id=USER_A, title="Private", lang_code="en")
        card = fake_db.seed("flashcards", deck_id=deck["id"], user_id=USER_A, term="secret", definition="bí mật", state=0)
        return deck, card

    def test_user_b_cannot_touch_user_a_resources(self, api, fake_db, victim, headers_b):
        deck, card = victim
        d, c = deck["id"], card["id"]
        attempts = {
            "get cards": api.get(f"{BASE}/decks/{d}/cards", headers=headers_b),
            "study queue": api.get(f"{BASE}/decks/{d}/study-queue", headers=headers_b),
            "study stats": api.get(f"{BASE}/decks/{d}/study-stats", headers=headers_b),
            "update deck": api.put(f"{BASE}/decks/{d}", headers=headers_b, json={"title": "pwned"}),
            "delete deck": api.delete(f"{BASE}/decks/{d}", headers=headers_b),
            "create card": api.post(f"{BASE}/cards", headers=headers_b, json={"deck_id": d, "front_text": "x", "back_text": "y"}),
            "update card": api.put(f"{BASE}/cards/{c}", headers=headers_b, json={"front_text": "pwned"}),
            "delete card": api.delete(f"{BASE}/cards/{c}", headers=headers_b),
            "review": api.post(f"{BASE}/review", headers=headers_b, json={"card_id": c, "grade": 4}),
            "verify spelling": api.post(f"{BASE}/cards/{c}/verify-spelling", headers=headers_b, json={"user_input": "secret"}),
            "import excel": upload(api, d, headers_b, xlsx([["a", "b"]])),
            "generate into deck": api.post(f"{BASE}/vocabulary/generate", headers=headers_b, json={"topic": "anything", "deck_id": d}),
            "commit into deck": api.post(f"{BASE}/decks/from-generated", headers=headers_b,
                                          json={"client_request_id": "req-idor-0001", "deck_id": d, "cards": [{"term": "a", "definition": "b"}]}),
        }
        failures = {name: r.status_code for name, r in attempts.items() if r.status_code != 403}
        assert failures == {}, f"các thao tác này lẽ ra phải bị 403: {failures}"
        # Dữ liệu của A nguyên vẹn
        assert fake_db.rows("flashcard_decks", id=d)[0]["title"] == "Private"
        assert [r["term"] for r in fake_db.rows("flashcards", deck_id=d)] == ["secret"]
        assert fake_db.rows("flashcards", id=c)[0]["state"] == 0 and fake_db.rows("review_logs") == []

    def test_user_b_does_not_see_user_a_decks_in_listing(self, api, fake_db, victim, headers_b):
        assert api.get(f"{BASE}/decks", headers=headers_b).json()["data"] == []

    def test_owner_still_has_access(self, api, fake_db, victim, headers_a):
        deck, card = victim
        assert api.get(f"{BASE}/decks/{deck['id']}/cards", headers=headers_a).status_code == 200
        assert api.post(f"{BASE}/review", headers=headers_a, json={"card_id": card["id"], "grade": 3}).status_code == 200

    @pytest.mark.parametrize("method,path", [
        ("get", "/decks"), ("post", "/decks"), ("get", "/decks/x/cards"), ("get", "/decks/x/study-queue"), ("get", "/decks/x/study-stats"),
        ("put", "/decks/x"), ("delete", "/decks/x"), ("post", "/cards"), ("put", "/cards/x"), ("delete", "/cards/x"),
        ("post", "/review"), ("post", "/cards/x/verify-spelling"), ("post", "/decks/x/import-excel"), ("get", "/stats/streak"),
        ("get", "/catalog/decks"), ("get", "/catalog/decks/x/preview"), ("post", "/catalog/decks/x/clone"),
        ("post", "/vocabulary/generate"), ("post", "/vocabulary/generate-image"), ("get", "/vocabulary/quota"), ("post", "/decks/from-generated"),
    ])
    def test_every_data_endpoint_requires_a_token(self, api, fake_db, method, path):
        assert getattr(api, method)(f"{BASE}{path}").status_code == 401

    def test_token_in_query_string_is_accepted_only_when_valid(self, api, fake_db):
        token = make_headers(USER_A)["Authorization"].split(" ", 1)[1]
        assert api.get(f"{BASE}/decks?token={token}").status_code == 200
        assert api.get(f"{BASE}/decks?token={token}x").status_code == 401


class TestRabbitMqStartup:
    async def test_retries_until_rabbitmq_is_reachable(self, monkeypatch):
        attempts = {"n": 0}
        sentinel = object()

        async def flaky_start():
            attempts["n"] += 1
            return sentinel if attempts["n"] == 3 else None

        sleeps = []

        async def fake_sleep(seconds):
            sleeps.append(seconds)

        import types

        monkeypatch.setattr(rabbitmq_consumer, "start_rabbitmq_consumer", flaky_start)
        # Chỉ thay `asyncio` bên trong module này; KHÔNG patch asyncio.sleep toàn cục (vòng thử lại nền của app sẽ quay vô hạn).
        monkeypatch.setattr(rabbitmq_consumer, "asyncio", types.SimpleNamespace(sleep=fake_sleep))
        assert await rabbitmq_consumer.connect_rabbitmq_with_retry(interval_seconds=2, max_interval_seconds=3) is sentinel
        assert attempts["n"] == 3 and sleeps == [2, 3.0]  # backoff tăng dần và bị chặn trần

    def test_service_starts_and_serves_requests_while_rabbitmq_is_down(self, api):
        assert api.get("/health").status_code == 200  # fixture `client` đã khởi động app khi RabbitMQ không tồn tại


class TestHealthDiagnostics:
    def test_reports_fsrs_llm_database_and_broker_state(self, api, fake_db, monkeypatch):
        for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENAI_BASE_URL"):
            monkeypatch.delenv(key, raising=False)
        body = api.get("/health").json()
        assert body["ok"] is True and body["fsrs"] is True  # nếu FSRS thật không nạp được thì health báo False
        assert body["llm_providers"] == [] and body["supabase"] is True and body["rabbitmq"] is False

        monkeypatch.setenv("GROQ_API_KEY", "gsk_distinctive_secret_value")
        monkeypatch.setenv("GEMINI_API_KEY", "AIza_distinctive_secret_value")
        res = api.get("/health")
        assert res.json()["llm_providers"] == ["groq", "gemini"]
        assert "distinctive_secret_value" not in res.text  # health không bao giờ lộ khóa
