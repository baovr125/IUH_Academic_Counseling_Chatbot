import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

service_root = Path(__file__).resolve().parent.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

# Bí mật dành riêng cho test (không phải bí mật của hệ thống thật).
TEST_JWT_SECRET = "test-only-secret-key-do-not-use-in-production-0123456789"
os.environ["JWT_SECRET_KEY"] = TEST_JWT_SECRET
os.environ["SUPABASE_URL"] = "https://fake-supabase.invalid"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "fake-service-role-key"
os.environ.pop("ENABLE_API_DOCS", None)

from fixtures.fake_supabase import FakeSupabase  # noqa: E402
from app.main import app  # noqa: E402
from app.services import auth_service as svc  # noqa: E402
from app.utils.throttle import login_throttle  # noqa: E402

PASSWORD = "CorrectPass123"
USER_ID = "550e8400-e29b-41d4-a716-446655440000"


def make_user_row(**overrides):
    row = {
        "id": USER_ID,
        "email": "20012345@student.iuh.edu.vn",
        "student_code": "20012345",
        "password_hash": svc.hash_password(PASSWORD),
        "role": "student",
        "full_name": "Nguyen Van Bao",
        "department": "Khoa CNTT",
        "major": "KTPM",
        "phone_number": None,
        "avatar_url": None,
        "settings": {"theme": "dark", "language": "vi"},
    }
    row.update(overrides)
    return row


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    login_throttle.clear()
    monkeypatch.setattr(svc, "_client", None)
    yield
    login_throttle.clear()


@pytest.fixture
def db(monkeypatch):
    """Supabase giả có sẵn 1 sinh viên; mọi truy vấn của service đi qua đối tượng này."""
    fake = FakeSupabase([make_user_row()])
    monkeypatch.setattr(svc, "get_supabase", lambda: fake)
    return fake


@pytest.fixture
def empty_db(monkeypatch):
    fake = FakeSupabase([])
    monkeypatch.setattr(svc, "get_supabase", lambda: fake)
    return fake


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def token(db):
    return svc.issue_token_for_user(db.users[0])


@pytest.fixture
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
