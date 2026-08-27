import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from jose import jwt


def get_auth_headers(user_id="550e8400-e29b-41d4-a716-446655440000"):
    token = jwt.encode(
        {"id": user_id, "sub": user_id, "email": "test@student.iuh.edu.vn", "role": "student"},
        "super-secret-key-iuh-chatbot-2026",
        algorithm="HS256"
    )
    return {"Authorization": f"Bearer {token}"}


class TestFlashcardApiIntegration:
    def test_health_check_returns_200(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["service"] == "flashcard_service"

    def test_get_decks_requires_auth(self, client):
        res = client.get("/api/v1/flashcards/decks")
        assert res.status_code == 401

    def test_get_decks_returns_user_decks(self, client):
        headers = get_auth_headers()
        with patch("app.routers.flashcards.get_decks", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [
                {"id": "deck-1", "title": "Từ vựng CNTT", "cardCount": 25, "dueCount": 5}
            ]

            res = client.get("/api/v1/flashcards/decks", headers=headers)
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["title"] == "Từ vựng CNTT"

    def test_create_deck_endpoint(self, client):
        headers = get_auth_headers()
        with patch("app.routers.flashcards.create_deck", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                "id": "new-deck-uuid",
                "title": "Chuyên ngành KTPM",
                "description": "Thẻ thuật ngữ phần mềm",
                "lang_code": "en"
            }

            res = client.post("/api/v1/flashcards/decks", headers=headers, json={
                "title": "Chuyên ngành KTPM",
                "description": "Thẻ thuật ngữ phần mềm",
                "lang_code": "en"
            })
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert data["data"]["title"] == "Chuyên ngành KTPM"

    def test_tts_empty_text_returns_400(self, client):
        res = client.get("/api/v1/flashcards/tts?text=   &lang=en")
        assert res.status_code == 400
