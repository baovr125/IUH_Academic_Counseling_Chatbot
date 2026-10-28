"""DELETE /api/chat/messages/cache chỉ dành cho admin (JWT role=admin), không còn token dev dùng chung."""
import datetime
import os
from unittest.mock import AsyncMock, patch

from jose import jwt

URL = "/api/chat/messages/cache"


def _token(role: str) -> str:
    claims = {
        "sub": "user-1",
        "role": role,
        "iss": "iuh-auth-service",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),
    }
    return jwt.encode(claims, os.environ["JWT_SECRET_KEY"], algorithm="HS256")


def _auth(role: str) -> dict:
    return {"Authorization": f"Bearer {_token(role)}"}


def test_clear_cache_requires_authentication(client):
    assert client.delete(URL).status_code == 401


def test_clear_cache_rejects_old_dev_token(client):
    res = client.delete(URL, headers={"x-dev-token": "iuh-dev-secret-2026"})
    assert res.status_code == 401


def test_clear_cache_rejects_non_admin(client):
    with patch("app.services.rag_service.invalidate_semantic_cache", new=AsyncMock()) as invalidate:
        res = client.delete(URL, headers=_auth("student"))
    assert res.status_code == 403
    invalidate.assert_not_called()


def test_clear_cache_allows_admin(client):
    with patch("app.services.rag_service.invalidate_semantic_cache", new=AsyncMock()) as invalidate:
        res = client.delete(URL, headers=_auth("admin"))
    assert res.status_code == 200
    invalidate.assert_awaited_once()
