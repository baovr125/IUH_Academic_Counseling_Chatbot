import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from jose import jwt, JWTError
from app.services.auth_service import create_access_token, get_user_by_token, get_user_settings, update_user_settings


class TestJWTTokenManagement:
    def test_create_access_token_contains_expected_claims(self):
        payload = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "20012345@student.iuh.edu.vn",
            "role": "student",
            "student_code": "20012345"
        }
        token = create_access_token(payload)
        assert isinstance(token, str)
        assert len(token) > 20

        decoded = jwt.decode(token, "super-secret-key-iuh-chatbot-2026", algorithms=["HS256"])
        assert decoded["id"] == payload["id"]
        assert decoded["email"] == payload["email"]
        assert decoded["role"] == payload["role"]
        assert decoded["student_code"] == payload["student_code"]
        assert "exp" in decoded

    def test_create_access_token_custom_expiry(self):
        payload = {"id": "user-custom-expiry", "role": "admin"}
        custom_expiry = timedelta(minutes=15)
        token = create_access_token(payload, expires_delta=custom_expiry)
        
        decoded = jwt.decode(token, "super-secret-key-iuh-chatbot-2026", algorithms=["HS256"])
        assert decoded["id"] == "user-custom-expiry"
        
        exp_timestamp = decoded["exp"]
        now_timestamp = datetime.now(timezone.utc).timestamp()
        diff = exp_timestamp - now_timestamp
        assert 800 < diff < 1000

    def test_decode_with_wrong_secret_raises_error(self):
        payload = {"id": "user-tampered"}
        token = create_access_token(payload)

        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret-key", algorithms=["HS256"])

    def test_get_user_by_token_with_invalid_token_returns_none(self):
        result = get_user_by_token("invalid.token.structure")
        assert result is None

    def test_get_user_by_token_fallback_when_db_unavailable(self):
        token = create_access_token({
            "id": "fallback-uuid",
            "email": "fallback@iuh.edu.vn",
            "role": "student",
            "student_code": "19001234",
            "full_name": "Fallback User"
        })
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_sb.return_value = None
            user = get_user_by_token(token)
            assert user is not None
            assert user["id"] == "fallback-uuid"
            assert user["email"] == "fallback@iuh.edu.vn"
            assert user["studentCode"] == "19001234"

    def test_get_user_settings_fallback_default(self):
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_sb.return_value = None
            settings = get_user_settings("any-user-id")
            assert settings == {"theme": "light", "language": "vi"}
