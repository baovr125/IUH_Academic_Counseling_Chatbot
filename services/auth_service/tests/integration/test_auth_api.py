import pytest
from unittest.mock import patch, MagicMock
from app.services.auth_service import hash_password, create_access_token
from jose import jwt


class TestAuthApiIntegration:
    def test_health_check_returns_200(self, client):
        res = client.get("/api/auth/health")
        assert res.status_code == 200
        assert res.json()["ok"] is True

    def test_register_validation_failure_empty_body(self, client):
        res = client.post("/api/auth/register", json={
            "fullName": "",
            "email": "invalid-email",
            "password": "123"
        })
        assert res.status_code == 400
        data = res.json()
        assert data["ok"] is False
        assert "error" in data

    def test_student_registration_missing_mssv_returns_400(self, client):
        res = client.post("/api/auth/register", json={
            "fullName": "Nguyen Van A",
            "email": "20012345@student.iuh.edu.vn",
            "password": "Password123",
            "userType": "student"
        })
        assert res.status_code == 400
        data = res.json()
        assert data["ok"] is False

    def test_student_registration_invalid_email_domain_returns_400(self, client):
        res = client.post("/api/auth/register", json={
            "fullName": "Nguyen Van A",
            "email": "nguyenvana@gmail.com",
            "password": "Password123",
            "studentCode": "20012345",
            "department": "Khoa CNTT",
            "major": "KTPM",
            "role": "student"
        })
        assert res.status_code == 400
        data = res.json()
        assert data["ok"] is False

    def test_register_conflict_duplicate_email_returns_409(self, client):
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_client = MagicMock()
            mock_client.table().select().ilike().execute.return_value.data = [{"id": "existing-uuid"}]
            mock_sb.return_value = mock_client

            res = client.post("/api/auth/register", json={
                "fullName": "Nguyen Van A",
                "email": "20012345@student.iuh.edu.vn",
                "password": "Password123",
                "studentCode": "20012345",
                "department": "Khoa CNTT",
                "major": "KTPM",
                "role": "student"
            })
            assert res.status_code == 409
            data = res.json()
            assert data["ok"] is False
            assert "Email đã được sử dụng" in data["error"]["message"]

    def test_register_conflict_duplicate_student_code_returns_409(self, client):
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_client = MagicMock()
            mock_client.table().select().ilike().execute.return_value.data = []
            mock_client.table().select().eq().execute.return_value.data = [{"id": "existing-code"}]
            mock_sb.return_value = mock_client

            res = client.post("/api/auth/register", json={
                "fullName": "Nguyen Van A",
                "email": "20012345@student.iuh.edu.vn",
                "password": "Password123",
                "studentCode": "20012345",
                "department": "Khoa CNTT",
                "major": "KTPM",
                "role": "student"
            })
            assert res.status_code == 409
            data = res.json()
            assert data["ok"] is False

    def test_register_student_success_returns_201(self, client):
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_client = MagicMock()
            mock_client.table().select().ilike().execute.return_value.data = []
            mock_client.table().select().eq().execute.return_value.data = []
            mock_client.table().insert().execute.return_value.data = [{"id": "new-student-uuid"}]
            mock_sb.return_value = mock_client

            res = client.post("/api/auth/register", json={
                "fullName": "Nguyen Van Bao",
                "email": "20012345@student.iuh.edu.vn",
                "password": "Password123",
                "studentCode": "20012345",
                "department": "Khoa Cong nghe Thong tin",
                "major": "Ky thuat Phan mem",
                "role": "student"
            })
            assert res.status_code == 201
            data = res.json()
            assert data["ok"] is True
            assert "token" in data["data"]
            assert data["data"]["user"]["role"] == "student"

    def test_register_public_user_success_returns_201(self, client):
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_client = MagicMock()
            mock_client.table().select().ilike().execute.return_value.data = []
            mock_client.table().insert().execute.return_value.data = [{"id": "public-uuid"}]
            mock_sb.return_value = mock_client

            res = client.post("/api/auth/register", json={
                "fullName": "Guest User",
                "email": "guest@gmail.com",
                "password": "Password123",
                "role": "public"
            })
            assert res.status_code == 201
            data = res.json()
            assert data["ok"] is True

    def test_login_invalid_credentials_returns_401(self, client):
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_client = MagicMock()
            mock_client.table().select().or_().execute.return_value.data = [{
                "id": "user-123",
                "email": "20012345@student.iuh.edu.vn",
                "student_code": "20012345",
                "password_hash": hash_password("CorrectPassword123"),
                "role": "student",
                "full_name": "Nguyen Van Bao"
            }]
            mock_sb.return_value = mock_client

            res = client.post("/api/auth/login", json={
                "account": "20012345",
                "password": "WrongPassword123"
            })
            assert res.status_code == 401
            data = res.json()
            assert data["ok"] is False

    def test_login_success_returns_jwt_token(self, client):
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_client = MagicMock()
            mock_client.table().select().or_().execute.return_value.data = [{
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "20012345@student.iuh.edu.vn",
                "student_code": "20012345",
                "password_hash": hash_password("CorrectPassword123"),
                "role": "student",
                "full_name": "Nguyen Van Bao",
                "department": "Khoa CNTT",
                "major": "KTPM",
                "avatar_url": None
            }]
            mock_sb.return_value = mock_client

            res = client.post("/api/auth/login", json={
                "account": "20012345",
                "password": "CorrectPassword123"
            })
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            token = data["data"]["token"]
            payload = jwt.decode(token, "super-secret-key-iuh-chatbot-2026", algorithms=["HS256"])
            assert payload["id"] == "550e8400-e29b-41d4-a716-446655440000"
            assert payload["role"] == "student"

    def test_verify_student_endpoint(self, client):
        res = client.post("/api/auth/verify-student", json={"studentId": "20012345"})
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["data"]["verified"] is True
        assert data["data"]["studentId"] == "20012345"

    def test_get_me_with_valid_token(self, client):
        token = create_access_token({
            "id": "user-uuid-123",
            "email": "20012345@student.iuh.edu.vn",
            "role": "student",
            "student_code": "20012345",
            "full_name": "Nguyen Van Bao"
        })
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_client = MagicMock()
            mock_client.table().select().eq().execute.return_value.data = [{
                "id": "user-uuid-123",
                "email": "20012345@student.iuh.edu.vn",
                "full_name": "Nguyen Van Bao",
                "student_code": "20012345",
                "role": "student",
                "department": "CNTT",
                "major": "KTPM",
                "avatar_url": None
            }]
            mock_sb.return_value = mock_client

            res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert data["data"]["email"] == "20012345@student.iuh.edu.vn"

    def test_get_me_missing_token_returns_401(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401

    def test_get_settings_success(self, client):
        token = create_access_token({"id": "user-123", "role": "student"})
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_client = MagicMock()
            mock_client.table().select().eq().execute.return_value.data = [{
                "id": "user-123",
                "role": "student",
                "settings": {"theme": "dark", "language": "vi"}
            }]
            mock_sb.return_value = mock_client

            res = client.get("/api/auth/settings", headers={"Authorization": f"Bearer {token}"})
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert data["data"]["theme"] == "dark"

    def test_update_settings_success(self, client):
        token = create_access_token({"id": "user-123", "role": "student"})
        with patch("app.services.auth_service.get_supabase") as mock_sb:
            mock_client = MagicMock()
            mock_client.table().select().eq().execute.return_value.data = [{
                "id": "user-123",
                "role": "student",
                "settings": {"theme": "light", "language": "vi"}
            }]
            mock_client.table().update().eq().execute.return_value.data = [{
                "settings": {"theme": "dark", "language": "en"}
            }]
            mock_sb.return_value = mock_client

            res = client.put(
                "/api/auth/settings",
                headers={"Authorization": f"Bearer {token}"},
                json={"theme": "dark", "language": "en"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert data["data"]["theme"] == "dark"
