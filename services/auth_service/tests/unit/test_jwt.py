import datetime

import pytest
from jose import jwt

from app import config
from app.services import auth_service as svc

SECRET = config.get_jwt_secret()
NOW = datetime.datetime.now(datetime.timezone.utc)


def _forge(claims, secret=SECRET, algorithm="HS256"):
    return jwt.encode(claims, secret, algorithm=algorithm)


class TestTokenIssuing:
    def test_claims_are_minimal_and_contain_no_pii(self):
        row = {"id": "u-1", "role": "student", "email": "a@student.iuh.edu.vn", "full_name": "A", "student_code": "20012345"}
        claims = jwt.decode(svc.issue_token_for_user(row), SECRET, algorithms=["HS256"], issuer=config.TOKEN_ISSUER)
        assert set(claims) == {"sub", "role", "tv", "oiat", "iat", "exp", "iss"}
        assert claims["sub"] == "u-1" and claims["role"] == "student"

    def test_default_lifetime_is_access_token_minutes(self):
        claims = jwt.decode(svc.create_access_token({"sub": "u"}), SECRET, algorithms=["HS256"], issuer=config.TOKEN_ISSUER)
        assert claims["exp"] - claims["iat"] == config.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def test_custom_expiry(self):
        claims = jwt.decode(
            svc.create_access_token({"sub": "u"}, datetime.timedelta(minutes=15)),
            SECRET, algorithms=["HS256"], issuer=config.TOKEN_ISSUER,
        )
        assert claims["exp"] - claims["iat"] == 900


class TestTokenValidation:
    def test_valid_token_decodes(self):
        assert svc.decode_token(svc.create_access_token({"sub": "u"}))["sub"] == "u"

    def test_wrong_secret_rejected(self):
        bad = _forge({"sub": "u", "iss": config.TOKEN_ISSUER, "exp": NOW + datetime.timedelta(minutes=5)},
                     secret="another-secret-key-another-secret-key-0000")
        assert svc.decode_token(bad) is None

    def test_expired_token_rejected(self):
        expired = _forge({"sub": "u", "iss": config.TOKEN_ISSUER, "exp": NOW - datetime.timedelta(minutes=1)})
        assert svc.decode_token(expired) is None

    def test_token_without_exp_rejected(self):
        assert svc.decode_token(_forge({"sub": "u", "iss": config.TOKEN_ISSUER})) is None

    def test_token_without_or_wrong_issuer_rejected(self):
        future = NOW + datetime.timedelta(minutes=5)
        assert svc.decode_token(_forge({"sub": "u", "exp": future})) is None
        assert svc.decode_token(_forge({"sub": "u", "iss": "evil", "exp": future})) is None

    def test_token_without_subject_rejected(self):
        assert svc.decode_token(_forge({"iss": config.TOKEN_ISSUER, "exp": NOW + datetime.timedelta(minutes=5)})) is None

    def test_alg_none_and_other_algorithms_rejected(self):
        future = int((NOW + datetime.timedelta(minutes=5)).timestamp())
        header = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0"  # {"alg":"none","typ":"JWT"}
        import base64, json
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "u", "iss": config.TOKEN_ISSUER, "exp": future}).encode()).rstrip(b"=").decode()
        assert svc.decode_token(f"{header}.{payload}.") is None
        hs512 = _forge({"sub": "u", "iss": config.TOKEN_ISSUER, "exp": future}, algorithm="HS512")
        assert svc.decode_token(hs512) is None

    def test_garbage_token_rejected(self):
        assert svc.decode_token("invalid.token.structure") is None


class TestSecretConfiguration:
    @pytest.mark.parametrize("value", ["", "short", "super-secret-key-iuh-chatbot-2026", "x" * 31])
    def test_weak_or_leaked_secret_refuses_to_start(self, monkeypatch, value):
        monkeypatch.setenv("JWT_SECRET_KEY", value)
        with pytest.raises(RuntimeError):
            config.validate_config()

    def test_missing_secret_refuses_to_start(self, monkeypatch):
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        with pytest.raises(RuntimeError):
            config.get_jwt_secret()
