import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from app.services.auth_service import hash_password, verify_password, create_access_token
from jose import jwt

client = TestClient(app)


def test_health_check():
    res = client.get("/api/auth/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_register_validation_failure_returns_400():
    res = client.post("/api/auth/register", json={
        "fullName": "",
        "email": "invalid-email",
        "password": "123"
    })
    assert res.status_code == 400
    data = res.json()
    assert data["ok"] is False
    assert "error" in data
    assert "details" in data["error"]
    assert len(data["error"]["details"]) > 0


def test_student_registration_missing_mssv_returns_400():
    res = client.post("/api/auth/register", json={
        "fullName": "Nguyen Van A",
        "email": "20012345@student.iuh.edu.vn",
        "password": "Password123",
        "userType": "student"
    })
    assert res.status_code == 400
    data = res.json()
    assert data["ok"] is False
    assert "MSSV" in data["error"]["message"] or "student_code" in str(data)


def test_student_registration_invalid_email_domain_returns_400():
    res = client.post("/api/auth/register", json={
        "fullName": "Nguyen Van A",
        "email": "nguyenvana@gmail.com",
        "password": "Password123",
        "studentCode": "20012345",
        "department": "Khoa CNTT",
        "major": "KTPM",
        "userType": "student"
    })
    assert res.status_code == 400
    data = res.json()
    assert data["ok"] is False
    assert "@student.iuh.edu.vn" in data["error"]["message"] or "@iuh.edu.vn" in data["error"]["message"]


def test_register_conflict_duplicate_email_returns_409():
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
        assert data["error"]["message"] == "Email đã được sử dụng"


def test_register_conflict_duplicate_student_code_returns_409():
    with patch("app.services.auth_service.get_supabase") as mock_sb:
        mock_client = MagicMock()
        mock_client.table().select().ilike().execute.return_value.data = []
        mock_client.table().select().eq().execute.return_value.data = [{"id": "existing-student-uuid"}]
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
        assert data["error"]["message"] == "Mã số sinh viên đã tồn tại"


def test_register_student_success_returns_201():
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
        assert data["data"]["user"]["studentCode"] == "20012345"


def test_register_public_user_success_returns_201():
    with patch("app.services.auth_service.get_supabase") as mock_sb:
        mock_client = MagicMock()
        mock_client.table().select().ilike().execute.return_value.data = []
        mock_client.table().insert().execute.return_value.data = [{"id": "new-public-uuid"}]
        mock_sb.return_value = mock_client

        res = client.post("/api/auth/register", json={
            "fullName": "Tran Thi Mai",
            "email": "tranmai@gmail.com",
            "password": "Password123",
            "role": "public"
        })
        assert res.status_code == 201
        data = res.json()
        assert data["ok"] is True
        assert data["data"]["user"]["role"] == "public"
        assert data["data"]["user"]["studentCode"] is None


def test_login_invalid_credentials_returns_401():
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
        assert data["error"]["message"] == "Tài khoản hoặc mật khẩu không chính xác"


def test_login_success_returns_200_and_jwt():
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
        assert token is not None

        # Verify JWT payload
        payload = jwt.decode(token, "super-secret-key-iuh-chatbot-2026", algorithms=["HS256"])
        assert payload["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert payload["email"] == "20012345@student.iuh.edu.vn"
        assert payload["role"] == "student"
        assert payload["student_code"] == "20012345"
