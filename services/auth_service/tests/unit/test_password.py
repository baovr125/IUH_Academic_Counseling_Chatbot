import pytest

from app.schemas.auth import check_password_policy
from app.services import auth_service as svc


class TestPasswordHashing:
    def test_hash_is_bcrypt_and_not_plaintext(self):
        plain = "MySecretPassword123"
        hashed = svc.hash_password(plain)
        assert hashed.startswith("$2b$12$")  # bcrypt, cost 12
        assert plain not in hashed

    def test_verify_success_and_failure(self):
        hashed = svc.hash_password("CorrectHorse123")
        assert svc.verify_password("CorrectHorse123", hashed) is True
        assert svc.verify_password("WrongHorse123", hashed) is False

    def test_salt_is_unique_per_hash(self):
        h1, h2 = svc.hash_password("SamePassword123"), svc.hash_password("SamePassword123")
        assert h1 != h2
        assert svc.verify_password("SamePassword123", h1) and svc.verify_password("SamePassword123", h2)

    def test_vietnamese_and_special_characters(self):
        plain = "MậtKhẩu_IUH@2026!#$%"
        hashed = svc.hash_password(plain)
        assert svc.verify_password(plain, hashed) is True
        assert svc.verify_password("MatKhau_IUH@2026!#$%", hashed) is False

    def test_garbage_hash_returns_false_instead_of_raising(self):
        assert svc.verify_password("abc12345", "not-a-bcrypt-hash") is False


class TestPasswordPolicy:
    @pytest.mark.parametrize("pwd,fragment", [
        ("Ab1", "tối thiểu 8"),
        ("abcdefgh", "chữ số"),
        ("12345678", "chữ cái"),
        ("Password123", "phổ biến"),
        ("a1" + "x" * 80, "quá dài"),
    ])
    def test_rejects_weak_passwords(self, pwd, fragment):
        with pytest.raises(ValueError) as exc:
            check_password_policy(pwd)
        assert fragment in str(exc.value)

    def test_rejects_password_equal_to_email_local_part(self):
        with pytest.raises(ValueError):
            check_password_policy("20012345a", "20012345a@student.iuh.edu.vn")

    def test_accepts_reasonable_password(self):
        check_password_policy("Tr0ub4dor-Horse", "x@student.iuh.edu.vn")

    def test_multibyte_password_over_72_bytes_is_rejected_not_truncated(self):
        # 30 ký tự có dấu = 60-90 byte UTF-8; bcrypt sẽ cắt âm thầm ở 72 byte nếu không chặn.
        with pytest.raises(ValueError):
            check_password_policy("ắ1" + "ẩ" * 30)
