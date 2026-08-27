import pytest
from unittest.mock import patch, MagicMock


class TestAcademicChatbotApiIntegration:
    def test_health_check_returns_200(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["service"] == "academic_chatbot_service"

    def test_health_check_alias_returns_200(self, client):
        res = client.get("/api/chat/health")
        assert res.status_code == 200
        assert res.json()["ok"] is True

    def test_get_sessions_empty_when_no_database_connection(self, client):
        with patch("app.routers.sessions.get_supabase_client") as mock_sb:
            mock_sb.return_value = None
            res = client.get("/api/chat/sessions")
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert data["data"] == []

    def test_get_sessions_returns_conversation_list(self, client):
        with patch("app.routers.sessions.get_supabase_client") as mock_sb:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_query = MagicMock()

            mock_query.filter.return_value = mock_query
            mock_query.or_.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_query.range.return_value = mock_query
            mock_query.execute.return_value = MagicMock(data=[
                {"id": "conv-1", "title": "Tư vấn đăng ký môn học", "updated_at": "2026-08-20T10:00:00Z"},
                {"id": "conv-2", "title": "Hỏi về học bổng", "updated_at": "2026-08-21T11:00:00Z"}
            ])
            mock_table.select.return_value = mock_query
            mock_client.table.return_value = mock_table
            mock_sb.return_value = mock_client

            res = client.get("/api/chat/sessions")
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert len(data["data"]) == 2
            assert data["data"][0]["title"] == "Tư vấn đăng ký môn học"

    def test_get_session_messages(self, client):
        with patch("app.routers.sessions.get_supabase_client") as mock_sb:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_query = MagicMock()

            mock_query.eq.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_query.range.return_value = mock_query
            mock_query.execute.return_value = MagicMock(data=[
                {
                    "id": "123",
                    "role": "user",
                    "content": "Điều kiện tốt nghiệp?",
                    "created_at": "2026-08-21T10:00:00Z",
                    "sources": []
                }
            ])
            mock_table.select.return_value = mock_query
            mock_client.table.return_value = mock_table
            mock_sb.return_value = mock_client

            res = client.get("/api/chat/sessions/550e8400-e29b-41d4-a716-446655440000/messages")
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["content"] == "Điều kiện tốt nghiệp?"
