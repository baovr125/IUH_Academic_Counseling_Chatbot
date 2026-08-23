import pytest
from app.services.auth_service import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_password_returns_valid_bcrypt_string(self):
        plain = "MySecretPassword123"
        hashed = hash_password(plain)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or len(hashed) > 20
        assert hashed != plain

    def test_verify_password_success_with_matching_password(self):
        plain = "CorrectHorseBatteryStaple"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_password_fails_with_wrong_password(self):
        plain = "CorrectPassword"
        wrong = "WrongPassword"
        hashed = hash_password(plain)
        assert verify_password(wrong, hashed) is False

    def test_hash_password_unique_salt_each_time(self):
        plain = "SamePasswordEveryTime"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2
        assert verify_password(plain, h1) is True
        assert verify_password(plain, h2) is True

    def test_verify_password_with_special_characters_and_vietnamese(self):
        plain = "MậtKhẩu_IUH@2026!#$%"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True
        assert verify_password("MatKhau_IUH@2026!#$%", hashed) is False
