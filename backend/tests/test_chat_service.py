"""
Test suite for chat_service.py — UUID normalization and in-memory session fallback.

These tests run offline (no Supabase connection required) by testing:
- ensure_uuid() deterministic conversion
- session_memory fallback when Supabase is unavailable
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock
from app.services.chat_service import (
    ensure_uuid,
    save_user_msg_to_db,
    save_assistant_msg_to_db,
    save_turn_to_db,
    get_session_history_from_db,
    session_memory,
)


# ─── ensure_uuid() ───────────────────────────────────────────

class TestEnsureUUID:
    """Validates session_id → UUID conversion logic."""

    def test_none_generates_random_uuid(self):
        result = ensure_uuid(None)
        # Must be a valid UUID
        parsed = uuid.UUID(result)
        assert parsed.version == 4

    def test_empty_string_generates_random_uuid(self):
        result = ensure_uuid("")
        parsed = uuid.UUID(result)
        assert parsed.version == 4

    def test_valid_uuid_passthrough(self):
        original = str(uuid.uuid4())
        result = ensure_uuid(original)
        assert result == original

    def test_custom_string_deterministic(self):
        """Same input string must always produce the same UUID v5."""
        result1 = ensure_uuid("s_abc123")
        result2 = ensure_uuid("s_abc123")
        assert result1 == result2

    def test_custom_string_produces_uuid_v5(self):
        result = ensure_uuid("custom-session-id")
        parsed = uuid.UUID(result)
        assert parsed.version == 5

    def test_different_strings_produce_different_uuids(self):
        r1 = ensure_uuid("session-A")
        r2 = ensure_uuid("session-B")
        assert r1 != r2


# ─── In-memory session fallback ──────────────────────────────

class TestSessionMemoryFallback:
    """Tests that session_memory works when Supabase is unavailable."""

    def setup_method(self):
        """Clear in-memory session store before each test."""
        session_memory.clear()

    @patch("app.services.chat_service.get_supabase_client", return_value=None)
    def test_save_user_msg_stores_in_memory(self, _mock_sb):
        clean_id = save_user_msg_to_db("test-session", "Xin chào", "Cuộc trò chuyện")
        assert clean_id in session_memory
        assert len(session_memory[clean_id]) == 1
        assert session_memory[clean_id][0]["role"] == "user"
        assert session_memory[clean_id][0]["content"] == "Xin chào"

    @patch("app.services.chat_service.get_supabase_client", return_value=None)
    def test_save_assistant_msg_stores_in_memory(self, _mock_sb):
        clean_id = ensure_uuid("test-session")
        save_assistant_msg_to_db(clean_id, "Trả lời mẫu")
        assert clean_id in session_memory
        assert session_memory[clean_id][-1]["role"] == "assistant"
        assert session_memory[clean_id][-1]["content"] == "Trả lời mẫu"

    @patch("app.services.chat_service.get_supabase_client", return_value=None)
    def test_save_turn_stores_both_messages(self, _mock_sb):
        save_turn_to_db("turn-session", "Câu hỏi", "Câu trả lời", "Tiêu đề")
        clean_id = ensure_uuid("turn-session")
        assert len(session_memory[clean_id]) == 2
        assert session_memory[clean_id][0]["role"] == "user"
        assert session_memory[clean_id][1]["role"] == "assistant"

    @patch("app.services.chat_service.get_supabase_client", return_value=None)
    def test_get_history_returns_memory_fallback(self, _mock_sb):
        clean_id = save_user_msg_to_db("history-test", "Msg 1", "Title")
        save_assistant_msg_to_db(clean_id, "Reply 1")

        history = get_session_history_from_db(clean_id)
        assert len(history) == 2
        assert history[0]["content"] == "Msg 1"
        assert history[1]["content"] == "Reply 1"

    @patch("app.services.chat_service.get_supabase_client", return_value=None)
    def test_get_history_empty_for_unknown_session(self, _mock_sb):
        history = get_session_history_from_db("nonexistent-session")
        assert history == []

    @patch("app.services.chat_service.get_supabase_client", return_value=None)
    def test_multiple_messages_accumulate(self, _mock_sb):
        sid = "multi-msg"
        clean_id = save_user_msg_to_db(sid, "Q1", "Title")
        save_assistant_msg_to_db(clean_id, "A1")
        save_user_msg_to_db(clean_id, "Q2", "Title")
        save_assistant_msg_to_db(clean_id, "A2")

        assert len(session_memory[clean_id]) == 4
        roles = [m["role"] for m in session_memory[clean_id]]
        assert roles == ["user", "assistant", "user", "assistant"]
