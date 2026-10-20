import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

service_root = Path(__file__).resolve().parent.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

os.environ["RABBITMQ_DISABLED"] = "1"  # test không cần broker (tránh tra DNS/kết nối nền treo lúc thoát)
os.environ["SUPABASE_URL"] = "https://mock-supabase.test"
os.environ["SUPABASE_KEY"] = "mock-key-test"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-key-do-not-use-in-production-0123456789"

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------------------------
# Fixture dùng chung cho bộ test mở rộng (Supabase giả, LLM giả, JWT nhiều người dùng)
# ---------------------------------------------------------------------------------------------
import datetime

from jose import jwt

sys.path.insert(0, str(Path(__file__).resolve().parent))  # để import `fixtures.*` từ mọi test

from fixtures.fake_llm import FakeLLM  # noqa: E402
from fixtures.fake_supabase import FakeSupabase  # noqa: E402

JWT_TEST_SECRET = os.environ["JWT_SECRET_KEY"]
USER_A = "11111111-1111-4111-8111-111111111111"
USER_B = "22222222-2222-4222-8222-222222222222"
ADMIN = "99999999-9999-4999-8999-999999999999"


def make_headers(user_id: str = USER_A, role: str = "student") -> dict:
    token = jwt.encode(
        {"sub": user_id, "role": role, "iss": "iuh-auth-service",
         "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)},
        JWT_TEST_SECRET, algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def headers_a():
    return make_headers(USER_A)


@pytest.fixture
def headers_b():
    return make_headers(USER_B)


@pytest.fixture
def headers_admin():
    return make_headers(ADMIN, "admin")


@pytest.fixture
def fake_db(monkeypatch):
    """Thay Supabase bằng bản giả dùng chung cho mọi module và đặt lại mọi trạng thái trong bộ nhớ."""
    from app.routers import vocabulary
    from app.services import flashcard_service as fs, llm_client, vocab_quota

    db = FakeSupabase()
    monkeypatch.setattr(fs, "make_supabase", lambda url, key: db)
    fs.reset_supabase_client()
    fs.in_memory_decks.clear()
    fs.in_memory_cards.clear()
    vocab_quota._memory.clear()
    vocab_quota._warned_missing_table = False
    vocabulary._commit_cache.clear()
    llm_client.reset_cooldowns()
    yield db
    fs.in_memory_decks.clear()
    fs.in_memory_cards.clear()
    vocab_quota._memory.clear()
    vocabulary._commit_cache.clear()
    fs.reset_supabase_client()


@pytest.fixture
def fake_llm(monkeypatch):
    """Thay hàm gọi LLM bằng FakeLLM; test có thể gán lại thuộc tính (words, reject, fail...) trước khi gọi API."""
    from app.services import llm_client

    llm = FakeLLM()
    monkeypatch.setattr(llm_client, "generate_json", llm)
    return llm


@pytest.fixture
def api(client):
    return client
