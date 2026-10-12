"""Kiểm thử xác thực JWT dùng chung (cùng nội dung ở cả 4 service sau Kong).

Chạy độc lập, không cần Redis/GPU/model: không phụ thuộc conftest của service.
"""
import datetime
import os
import sys
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt

_SERVICE_ROOT = Path(__file__).resolve().parents[2]
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))

SECRET = "test-only-secret-key-do-not-use-in-production-0123456789"
os.environ["JWT_SECRET_KEY"] = SECRET

from app.utils import security  # noqa: E402


def make_token(claims=None, secret=SECRET, algorithm="HS256", exp_delta=300, with_exp=True, with_iss=True):
    now = datetime.datetime.now(datetime.timezone.utc)
    body = {"sub": "user-1", "role": "student"}
    if with_iss:
        body["iss"] = security.TOKEN_ISSUER
    if with_exp:
        body["exp"] = now + datetime.timedelta(seconds=exp_delta)
    body.update(claims or {})
    return jwt.encode(body, secret, algorithm=algorithm)


@pytest.fixture(scope="module")
def client():
    app = FastAPI()

    @app.get("/user")
    def user(user_id: str = Depends(security.get_current_user_id)):
        return {"user_id": user_id}

    @app.get("/optional")
    def optional(user_id: str = Depends(security.get_optional_user_id)):
        return {"user_id": user_id}

    @app.get("/admin")
    def admin(admin_id: str = Depends(security.get_current_admin_user)):
        return {"admin_id": admin_id}

    return TestClient(app)


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


class TestUserAuthentication:
    def test_valid_token_is_accepted(self, client):
        res = client.get("/user", headers=bearer(make_token()))
        assert res.status_code == 200 and res.json() == {"user_id": "user-1"}

    def test_no_credentials_is_401(self, client):
        assert client.get("/user").status_code == 401

    @pytest.mark.parametrize("headers", [
        {"X-User-ID": "victim-user-id"},
        {"X-User-ID": "victim-user-id", "X-User-Role": "admin"},
    ])
    def test_client_supplied_identity_headers_are_ignored(self, client, headers):
        assert client.get("/user", headers=headers).status_code == 401
        assert client.get("/optional", headers=headers).json() == {"user_id": "anonymous"}

    def test_identity_header_cannot_override_a_valid_token(self, client):
        res = client.get("/user", headers={**bearer(make_token()), "X-User-ID": "victim"})
        assert res.json()["user_id"] == "user-1"

    @pytest.mark.parametrize("token", [
        make_token(exp_delta=-5),                                                     # hết hạn
        make_token(with_exp=False),                                                   # thiếu exp
        make_token(with_iss=False),                                                   # thiếu iss
        make_token(claims={"iss": "evil"}),                                           # sai issuer
        make_token(secret="a-different-secret-key-a-different-secret-key-00"),        # sai chữ ký
        make_token(algorithm="HS512"),                                                # thuật toán khác
        "invalid.token.structure",
    ])
    def test_invalid_tokens_are_rejected(self, client, token):
        assert client.get("/user", headers=bearer(token)).status_code == 401
        assert client.get("/optional", headers=bearer(token)).json() == {"user_id": "anonymous"}

    def test_old_leaked_default_secret_no_longer_works(self, client):
        leaked = make_token(secret="super-secret-key-iuh-chatbot-2026")
        assert client.get("/user", headers=bearer(leaked)).status_code == 401

    def test_scheme_must_be_bearer(self, client):
        token = make_token()
        assert client.get("/user", headers={"Authorization": token}).status_code == 401
        assert client.get("/user", headers={"Authorization": f"Basic {token}"}).status_code == 401

    def test_query_token_is_accepted_for_sse_and_header_takes_precedence(self, client):
        assert client.get("/user", params={"token": make_token()}).status_code == 200
        res = client.get("/user", params={"token": make_token({"sub": "from-query"})}, headers=bearer(make_token()))
        assert res.json()["user_id"] == "user-1"


class TestAdminAuthorization:
    def test_admin_role_in_token_is_accepted(self, client):
        res = client.get("/admin", headers=bearer(make_token({"sub": "admin-1", "role": "admin"})))
        assert res.status_code == 200 and res.json() == {"admin_id": "admin-1"}

    @pytest.mark.parametrize("role", ["student", "public", None, "ADMIN", "administrator"])
    def test_non_admin_roles_are_403(self, client, role):
        assert client.get("/admin", headers=bearer(make_token({"role": role}))).status_code == 403

    def test_header_spoofing_cannot_grant_admin(self, client):
        spoof = {"X-User-ID": "attacker", "X-User-Role": "admin"}
        assert client.get("/admin", headers=spoof).status_code == 401
        assert client.get("/admin", headers={**spoof, **bearer(make_token())}).status_code == 403

    def test_unauthenticated_is_401_not_403(self, client):
        assert client.get("/admin").status_code == 401

    def test_query_token_admin_for_event_source(self, client):
        assert client.get("/admin", params={"token": make_token({"role": "admin"})}).status_code == 200
        assert client.get("/admin", params={"token": make_token()}).status_code == 403


class TestSecretConfiguration:
    @pytest.mark.parametrize("value", ["", "short", "super-secret-key-iuh-chatbot-2026", "x" * 31])
    def test_weak_or_known_leaked_secret_refuses_to_start(self, monkeypatch, value):
        monkeypatch.setenv("JWT_SECRET_KEY", value)
        with pytest.raises(RuntimeError):
            security.validate_security_config()

    def test_missing_secret_refuses_to_start(self, monkeypatch):
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        with pytest.raises(RuntimeError):
            security.validate_security_config()

    def test_strong_secret_is_accepted(self, monkeypatch):
        monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
        security.validate_security_config()
