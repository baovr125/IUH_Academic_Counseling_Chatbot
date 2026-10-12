import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app import config
from app.main import app
from app.services import auth_service as svc
from conftest import PASSWORD, USER_ID, make_user_row
from fixtures.fake_supabase import FakeAPIError

STUDENT_BODY = {
    "fullName": "Nguyen Van Bao",
    "email": "20012346@student.iuh.edu.vn",
    "password": "Str0ngPass-2026",
    "department": "Khoa CNTT",
    "major": "KTPM",
    "role": "student",
}
PUBLIC_BODY = {"fullName": "Guest User", "email": "guest@gmail.com", "password": "Str0ngPass-2026", "role": "public"}


def forge(claims, secret=None):
    base = {"iss": config.TOKEN_ISSUER, "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)}
    base.update(claims)
    return jwt.encode(base, secret or config.get_jwt_secret(), algorithm="HS256")


# --------------------------------------------------------------------------- hạ tầng
class TestInfrastructure:
    def test_health(self, client):
        res = client.get("/api/auth/health")
        assert res.status_code == 200 and res.json()["ok"] is True

    def test_docs_and_openapi_are_disabled_by_default(self, client):
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404

    def test_unknown_route_uses_standard_error_format(self, client):
        res = client.put("/api/auth/does-not-exist", json={})
        assert res.status_code == 404
        body = res.json()
        assert body["ok"] is False and "message" in body["error"]
        assert "detail" not in body

    def test_responses_are_not_cacheable_and_carry_request_id(self, client):
        res = client.get("/api/auth/health")
        assert res.headers["Cache-Control"] == "no-store"
        assert res.headers["X-Request-ID"]

    def test_valid_incoming_request_id_is_propagated_invalid_is_replaced(self, client):
        assert client.get("/health", headers={"X-Request-ID": "kong-req-12345678"}).headers["X-Request-ID"] == "kong-req-12345678"
        assert client.get("/health", headers={"X-Request-ID": "bad id\twith spaces"}).headers["X-Request-ID"] != "bad id\twith spaces"

    def test_cors_does_not_reflect_arbitrary_origin(self, client):
        res = client.options("/api/auth/login", headers={
            "Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
        assert "access-control-allow-origin" not in res.headers

    def test_unhandled_error_does_not_leak_details(self, db):
        db.fail_all = RuntimeError("secret internals: table users column password_hash")
        with TestClient(app, raise_server_exceptions=False) as c:
            res = c.post("/api/auth/login", json={"account": "20012345", "password": PASSWORD})
        assert res.status_code == 503
        assert "password_hash" not in res.text and "internals" not in res.text


# --------------------------------------------------------------------------- đăng ký
class TestRegister:
    def test_student_success_returns_201_and_minimal_token(self, client, empty_db):
        res = client.post("/api/auth/register", json=STUDENT_BODY)
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["user"]["role"] == "student" and data["user"]["studentCode"] == "20012346"  # suy ra từ email
        assert "password" not in str(data) and "password_hash" not in str(data)
        row = empty_db.user(email=STUDENT_BODY["email"])
        assert row["password_hash"].startswith("$2b$") and row["password_hash"] != STUDENT_BODY["password"]
        assert set(jwt.get_unverified_claims(data["token"])) == {"sub", "role", "tv", "oiat", "iat", "exp", "iss"}

    def test_public_success_drops_student_fields(self, client, empty_db):
        res = client.post("/api/auth/register", json={**PUBLIC_BODY, "studentCode": "20012345", "department": "x", "major": "y"})
        assert res.status_code == 201
        row = empty_db.user(email="guest@gmail.com")
        assert row["role"] == "public" and row["student_code"] is None and row["department"] is None

    @pytest.mark.parametrize("role", ["admin", "ADMIN", "superuser", "root"])
    def test_cannot_register_as_admin(self, client, empty_db, role):
        res = client.post("/api/auth/register", json={**STUDENT_BODY, "role": role})
        assert res.status_code == 201
        assert res.json()["data"]["user"]["role"] == "student"
        assert empty_db.user(email=STUDENT_BODY["email"])["role"] == "student"

    def test_extra_fields_cannot_set_privileged_columns(self, client, empty_db):
        res = client.post("/api/auth/register", json={**PUBLIC_BODY, "id": "attacker-id", "is_admin": True, "token_version": 99,
                                                      "password_hash": "x"})
        assert res.status_code == 201
        row = empty_db.user(email="guest@gmail.com")
        assert row["id"] != "attacker-id" and "is_admin" not in row and "token_version" not in row
        assert row["password_hash"] != "x"

    def test_duplicate_email_is_409_with_field(self, client, db):
        res = client.post("/api/auth/register", json={**STUDENT_BODY, "email": make_user_row()["email"]})
        assert res.status_code == 409
        assert res.json()["error"]["field"] == "email"

    def test_duplicate_student_code_derived_from_email_is_409_on_email_field(self, client, db):
        # Tài khoản cũ dùng email khác nhưng đã giữ MSSV 20012346 -> email sinh viên mới cùng MSSV bị từ chối.
        db.users.append(make_user_row(id="old", email="legacy@iuh.edu.vn", student_code="20012346"))
        res = client.post("/api/auth/register", json=STUDENT_BODY)
        assert res.status_code == 409
        assert res.json()["error"]["field"] == "email"

    def test_student_code_is_derived_from_student_email_only(self, client, empty_db):
        cases = [
            ("20012346@student.iuh.edu.vn", "20012346"),
            ("nguyenvana@student.iuh.edu.vn", None),   # local-part không phải 8 chữ số
            ("20012347@iuh.edu.vn", None),             # email giảng viên/nhân viên: không suy ra MSSV
            ("2001234@student.iuh.edu.vn", None),      # 7 chữ số
        ]
        for email, expected in cases:
            res = client.post("/api/auth/register", json=STUDENT_BODY | {"email": email})
            assert res.status_code == 201, email
            assert empty_db.user(email=email)["student_code"] == expected, email
            assert res.json()["data"]["user"]["studentCode"] == expected

    def test_client_cannot_choose_or_squat_a_student_code(self, client, empty_db):
        # Gửi MSSV của người khác kèm email của mình: giá trị client bị bỏ qua.
        for key in ("studentCode", "student_code", "studentId", "student_id"):
            res = client.post("/api/auth/register", json=STUDENT_BODY | {key: "99999999"} | {"email": f"nguyen.{key.lower()}@student.iuh.edu.vn"})
            assert res.status_code == 201, key
            assert empty_db.user(email=f"nguyen.{key.lower()}@student.iuh.edu.vn")["student_code"] is None

    def test_student_can_log_in_with_derived_student_code(self, client, empty_db):
        client.post("/api/auth/register", json=STUDENT_BODY)
        res = client.post("/api/auth/login", json={"account": "20012346", "password": STUDENT_BODY["password"]})
        assert res.status_code == 200 and res.json()["data"]["user"]["studentCode"] == "20012346"

    def test_duplicate_check_uses_exact_match_not_ilike_wildcards(self, client, db):
        client.post("/api/auth/register", json=PUBLIC_BODY)
        email_checks = [c for c in db.calls if c["op"] == "select" and c["filters"] and c["filters"][0][0] == "email"]
        assert email_checks and email_checks[0]["filters"] == [("email", "guest@gmail.com")]

    def test_underscore_in_email_does_not_collide_with_other_user(self, client, empty_db):
        empty_db.users.append(make_user_row(id="other", email="axb@gmail.com", student_code=None, role="public"))
        res = client.post("/api/auth/register", json={**PUBLIC_BODY, "email": "a_b@gmail.com"})
        assert res.status_code == 201

    def test_race_unique_violation_from_db_maps_to_409_without_leaking(self, client, empty_db):
        empty_db.fail_insert = FakeAPIError('duplicate key value violates unique constraint "users_email_key"', "23505")
        res = client.post("/api/auth/register", json=PUBLIC_BODY)
        assert res.status_code == 409 and res.json()["error"]["field"] == "email"

    def test_db_error_on_insert_is_generic_503(self, client, empty_db):
        empty_db.fail_insert = FakeAPIError('null value in column "x" of relation "users" violates not-null constraint', "23502")
        res = client.post("/api/auth/register", json=PUBLIC_BODY)
        assert res.status_code == 503
        assert "users" not in res.text and "constraint" not in res.text

    def test_rls_error_is_generic_not_a_configuration_hint(self, client, empty_db):
        empty_db.fail_insert = FakeAPIError("new row violates row-level security policy", "42501")
        res = client.post("/api/auth/register", json=PUBLIC_BODY)
        assert res.status_code == 503
        assert "Row Level Security" not in res.text and "RLS" not in res.text

    def test_db_check_failure_fails_closed(self, client, empty_db):
        empty_db.fail_all = RuntimeError("timeout")
        assert client.post("/api/auth/register", json=PUBLIC_BODY).status_code == 503
        assert empty_db.users == []

    def test_database_not_configured_is_503(self, client):
        with patch.object(svc, "get_supabase", return_value=None):
            assert client.post("/api/auth/register", json=PUBLIC_BODY).status_code == 503

    @pytest.mark.parametrize("patch_body,field", [
        ({"email": "nguyenvana@gmail.com"}, "email"),
        ({"department": ""}, "department"),
        ({"major": ""}, "major"),
        ({"password": "short1"}, "password"),
        ({"password": "Password123"}, "password"),
        ({"confirmPassword": "different123"}, "confirm_password"),
    ])
    def test_validation_errors_name_the_correct_field(self, client, empty_db, patch_body, field):
        res = client.post("/api/auth/register", json=STUDENT_BODY | patch_body)
        assert res.status_code == 400
        error = res.json()["error"]
        assert error["field"] == field
        assert error["details"][0]["field"] == field

    def test_field_level_errors_keep_field_names(self, client, empty_db):
        res = client.post("/api/auth/register", json=STUDENT_BODY | {"fullName": "A1"})
        assert res.status_code == 400 and res.json()["error"]["details"][0]["field"] == "full_name"

    def test_empty_body_is_400(self, client, empty_db):
        assert client.post("/api/auth/register", json={}).status_code == 400

    def test_non_object_body_is_400(self, client, empty_db):
        assert client.post("/api/auth/register", content="[1,2]", headers={"content-type": "application/json"}).status_code == 400


# --------------------------------------------------------------------------- đăng nhập
class TestLogin:
    def test_success_by_student_code_and_by_email(self, client, db):
        for account in ("20012345", "20012345@STUDENT.iuh.edu.vn"):
            res = client.post("/api/auth/login", json={"account": account, "password": PASSWORD})
            assert res.status_code == 200, account
            data = res.json()["data"]
            claims = jwt.decode(data["token"], config.get_jwt_secret(), algorithms=["HS256"], issuer=config.TOKEN_ISSUER)
            assert claims["sub"] == USER_ID and claims["role"] == "student"
            assert "password_hash" not in str(data)

    def test_frontend_payload_alias_identifier(self, client, db):
        assert client.post("/api/auth/login", json={"identifier": "20012345", "password": PASSWORD}).status_code == 200

    def test_wrong_password_and_unknown_account_have_identical_responses(self, client, db):
        wrong_pw = client.post("/api/auth/login", json={"account": "20012345", "password": "WrongPass123"})
        unknown = client.post("/api/auth/login", json={"account": "99999999", "password": "WrongPass123"})
        malformed = client.post("/api/auth/login", json={"account": "not an account!", "password": "WrongPass123"})
        assert wrong_pw.status_code == unknown.status_code == malformed.status_code == 401
        assert wrong_pw.json() == unknown.json() == malformed.json()

    def test_bcrypt_runs_even_for_unknown_account(self, client, db):
        with patch.object(svc, "verify_password", wraps=svc.verify_password) as spy:
            client.post("/api/auth/login", json={"account": "99999999", "password": "WrongPass123"})
        assert spy.call_count == 1  # chống đo thời gian để dò tài khoản tồn tại

    def test_login_query_uses_exact_match_on_the_right_column(self, client, db):
        client.post("/api/auth/login", json={"account": "20012345", "password": PASSWORD})
        client.post("/api/auth/login", json={"account": "Nguyen.Bao@Student.IUH.edu.vn", "password": PASSWORD})
        filters = [c["filters"] for c in db.calls if c["op"] == "select"]
        assert [("student_code", "20012345")] in filters
        assert [("email", "nguyen.bao@student.iuh.edu.vn")] in filters

    def test_injection_style_account_never_reaches_the_database(self, client, db):
        res = client.post("/api/auth/login", json={"account": "x,role.eq.admin", "password": "WrongPass123"})
        assert res.status_code == 401
        assert not [c for c in db.calls if c["op"] == "select" and any("role" in str(f) for f in c["filters"])]

    def test_user_without_password_hash_cannot_login(self, client, db):
        db.users[0]["password_hash"] = None
        assert client.post("/api/auth/login", json={"account": "20012345", "password": "anything123"}).status_code == 401

    def test_locks_out_after_repeated_failures_even_with_correct_password(self, client, db):
        for _ in range(config.LOGIN_MAX_FAILURES):
            assert client.post("/api/auth/login", json={"account": "20012345", "password": "WrongPass123"}).status_code == 401
        res = client.post("/api/auth/login", json={"account": "20012345", "password": PASSWORD})
        assert res.status_code == 429
        assert int(res.headers["Retry-After"]) > 0

    def test_successful_login_resets_failure_counter(self, client, db):
        for _ in range(config.LOGIN_MAX_FAILURES - 1):
            client.post("/api/auth/login", json={"account": "20012345", "password": "WrongPass123"})
        assert client.post("/api/auth/login", json={"account": "20012345", "password": PASSWORD}).status_code == 200
        assert client.post("/api/auth/login", json={"account": "20012345", "password": "WrongPass123"}).status_code == 401

    def test_db_down_is_503_not_500_and_not_a_credentials_error(self, client, db):
        db.fail_all = RuntimeError("connection refused")
        res = client.post("/api/auth/login", json={"account": "20012345", "password": PASSWORD})
        assert res.status_code == 503 and "connection" not in res.text

    def test_empty_fields_are_400(self, client, db):
        assert client.post("/api/auth/login", json={"account": "", "password": ""}).status_code == 400

    def test_login_failure_is_logged_without_password(self, client, db, caplog):
        import logging
        with caplog.at_level(logging.WARNING, logger="auth_service"):
            client.post("/api/auth/login", json={"account": "20012345", "password": "SuperSecretWrong1"})
        text = " ".join(r.getMessage() + str(r.__dict__) for r in caplog.records)
        assert "login_failed" in text and "SuperSecretWrong1" not in text
        assert "20012345" not in text.replace("****345", "")  # tài khoản được che


# --------------------------------------------------------------------------- phiên và token
class TestSession:
    def test_me_with_valid_token(self, client, db, auth_headers):
        res = client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["email"] == make_user_row()["email"] and data["hasPassword"] is True
        assert "password_hash" not in data

    def test_me_requires_bearer_scheme(self, client, db, token):
        assert client.get("/api/auth/me").status_code == 401
        assert client.get("/api/auth/me", headers={"Authorization": token}).status_code == 401
        assert client.get("/api/auth/me", headers={"Authorization": f"Basic {token}"}).status_code == 401

    def test_expired_token_rejected(self, client, db):
        expired = forge({"sub": USER_ID, "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5)})
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401

    def test_token_without_exp_or_with_wrong_secret_rejected(self, client, db):
        no_exp = jwt.encode({"sub": USER_ID, "iss": config.TOKEN_ISSUER, "role": "admin"}, config.get_jwt_secret(), algorithm="HS256")
        wrong = forge({"sub": USER_ID}, secret="a-completely-different-secret-key-0123456789")
        for t in (no_exp, wrong):
            assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {t}"}).status_code == 401

    def test_token_of_deleted_user_is_rejected_not_trusted_from_claims(self, client, db):
        forged_admin = forge({"sub": "ghost-user-id", "role": "admin", "tv": 0})
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged_admin}"}).status_code == 401

    def test_database_failure_is_503_not_fail_open(self, client, db, auth_headers):
        db.fail_all = RuntimeError("down")
        assert client.get("/api/auth/me", headers=auth_headers).status_code == 503

    def test_role_comes_from_database_not_from_token_claim(self, client, db):
        escalated = forge({"sub": USER_ID, "role": "admin", "tv": 0})
        res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {escalated}"})
        assert res.status_code == 200 and res.json()["data"]["role"] == "student"

    def test_refresh_issues_new_token_with_current_role_from_db(self, client, db, auth_headers):
        db.users[0]["role"] = "admin"
        res = client.post("/api/auth/refresh", headers=auth_headers)
        assert res.status_code == 200
        new_claims = jwt.get_unverified_claims(res.json()["data"]["token"])
        assert new_claims["role"] == "admin"

    def test_refresh_keeps_original_login_time_and_enforces_session_max_age(self, client, db):
        too_old = int((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=config.SESSION_MAX_AGE_DAYS + 1)).timestamp())
        old = forge({"sub": USER_ID, "tv": 0, "oiat": too_old})
        assert client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {old}"}).status_code == 401
        recent = int(datetime.datetime.now(datetime.timezone.utc).timestamp()) - 3600
        tok = forge({"sub": USER_ID, "tv": 0, "oiat": recent})
        res = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {tok}"})
        assert jwt.get_unverified_claims(res.json()["data"]["token"])["oiat"] == recent

    def test_refresh_rejects_expired_token_and_deleted_user(self, client, db):
        expired = forge({"sub": USER_ID, "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)})
        assert client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
        ghost = forge({"sub": "ghost"})
        assert client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {ghost}"}).status_code == 401

    def test_logout_revokes_existing_tokens_when_column_exists(self, client, db, auth_headers):
        db.users[0]["token_version"] = 0
        assert client.post("/api/auth/logout", headers=auth_headers).json()["data"] == {"revoked": True}
        assert db.users[0]["token_version"] == 1
        assert client.get("/api/auth/me", headers=auth_headers).status_code == 401
        assert client.post("/api/auth/refresh", headers=auth_headers).status_code == 401

    def test_logout_without_token_version_column_reports_not_revoked(self, client, db, auth_headers):
        res = client.post("/api/auth/logout", headers=auth_headers)
        assert res.status_code == 200 and res.json()["data"] == {"revoked": False}


# --------------------------------------------------------------------------- hồ sơ
class TestProfile:
    def test_update_allowed_fields(self, client, db, auth_headers):
        res = client.put("/api/auth/profile", headers=auth_headers, json={
            "fullName": "Nguyễn Văn Bảo", "phoneNumber": "0901234567", "department": "Khoa Điện", "major": "Điện tử"})
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["fullName"] == "Nguyễn Văn Bảo" and data["phoneNumber"] == "0901234567"
        assert db.users[0]["full_name"] == "Nguyễn Văn Bảo" and db.users[0]["major"] == "Điện tử"

    def test_cannot_change_email_role_mssv_or_hash_through_profile(self, client, db, auth_headers):
        before = dict(db.users[0])
        res = client.put("/api/auth/profile", headers=auth_headers, json={
            "fullName": "Valid Name", "email": "evil@x.com", "role": "admin", "studentCode": "99999999",
            "student_code": "99999999", "password_hash": "x", "id": "other", "token_version": 5})
        assert res.status_code == 200
        for key in ("email", "role", "student_code", "password_hash", "id"):
            assert db.users[0][key] == before[key], key
        assert "token_version" not in db.users[0]

    def test_only_specific_user_row_is_updated(self, client, db, auth_headers):
        client.put("/api/auth/profile", headers=auth_headers, json={"fullName": "Valid Name"})
        updates = [c for c in db.calls if c["op"] == "update"]
        assert updates and updates[-1]["filters"] == [("id", USER_ID)]

    @pytest.mark.parametrize("body,field", [
        ({"fullName": "A"}, "full_name"),
        ({"fullName": "<script>alert(1)</script>"}, "full_name"),
        ({"phoneNumber": "abc"}, "phone_number"),
        ({"avatarUrl": "javascript:alert(1)"}, "avatar_url"),
        ({"avatarUrl": "http://insecure.example/a.png"}, "avatar_url"),
        ({"avatarUrl": "data:text/html;base64,PHNjcmlwdD4="}, "avatar_url"),
        ({"avatarUrl": "https://x.example/" + "a" * 250_000}, "avatar_url"),
    ])
    def test_validation(self, client, db, auth_headers, body, field):
        res = client.put("/api/auth/profile", headers=auth_headers, json=body)
        assert res.status_code == 400 and res.json()["error"]["field"] == field

    def test_avatar_accepts_https_and_small_image_data_url_and_can_be_cleared(self, client, db, auth_headers):
        for url in ("https://cdn.example.com/a.png", "data:image/png;base64,iVBORw0KGgo="):
            assert client.put("/api/auth/profile", headers=auth_headers, json={"avatarUrl": url}).status_code == 200
        client.put("/api/auth/profile", headers=auth_headers, json={"avatarUrl": ""})
        assert db.users[0]["avatar_url"] is None

    def test_public_user_cannot_set_department_or_major(self, client, db):
        db.users[0]["role"] = "public"
        headers = {"Authorization": f"Bearer {svc.issue_token_for_user(db.users[0])}"}
        assert client.put("/api/auth/profile", headers=headers, json={"department": "Khoa X"}).status_code == 400

    def test_requires_authentication(self, client, db):
        assert client.put("/api/auth/profile", json={"fullName": "Valid Name"}).status_code == 401


# --------------------------------------------------------------------------- đổi mật khẩu
class TestChangePassword:
    BODY = {"currentPassword": PASSWORD, "newPassword": "NewStr0ng-Pass9", "confirmPassword": "NewStr0ng-Pass9"}

    def test_success_changes_hash_and_old_password_stops_working(self, client, db, auth_headers):
        res = client.post("/api/auth/change-password", headers=auth_headers, json=self.BODY)
        assert res.status_code == 200 and res.json()["data"]["token"]
        assert svc.verify_password("NewStr0ng-Pass9", db.users[0]["password_hash"])
        assert client.post("/api/auth/login", json={"account": "20012345", "password": PASSWORD}).status_code == 401
        assert client.post("/api/auth/login", json={"account": "20012345", "password": "NewStr0ng-Pass9"}).status_code == 200

    def test_old_tokens_are_revoked_when_token_version_column_exists(self, client, db, auth_headers):
        db.users[0]["token_version"] = 3
        old = {"Authorization": f"Bearer {svc.issue_token_for_user(db.users[0])}"}
        new_token = client.post("/api/auth/change-password", headers=old, json=self.BODY).json()["data"]["token"]
        assert client.get("/api/auth/me", headers=old).status_code == 401
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_token}"}).status_code == 200

    def test_wrong_current_password_is_rejected_and_hash_unchanged(self, client, db, auth_headers):
        before = db.users[0]["password_hash"]
        res = client.post("/api/auth/change-password", headers=auth_headers, json=self.BODY | {"currentPassword": "Wrong-Current1"})
        assert res.status_code == 400 and res.json()["error"]["field"] == "current_password"
        assert db.users[0]["password_hash"] == before

    def test_missing_current_password_is_400(self, client, db, auth_headers):
        res = client.post("/api/auth/change-password", headers=auth_headers, json={"newPassword": "NewStr0ng-Pass9"})
        assert res.status_code == 400 and res.json()["error"]["field"] == "current_password"

    @pytest.mark.parametrize("new_pw", ["short1", "nodigitsatall", "12345678", "Password123", PASSWORD])
    def test_weak_or_unchanged_new_password_rejected(self, client, db, auth_headers, new_pw):
        res = client.post("/api/auth/change-password", headers=auth_headers, json={"currentPassword": PASSWORD, "newPassword": new_pw})
        assert res.status_code == 400 and res.json()["error"]["field"] == "new_password"

    def test_brute_forcing_current_password_is_throttled(self, client, db, auth_headers):
        for _ in range(config.LOGIN_MAX_FAILURES):
            client.post("/api/auth/change-password", headers=auth_headers, json=self.BODY | {"currentPassword": "Wrong-Current1"})
        assert client.post("/api/auth/change-password", headers=auth_headers, json=self.BODY).status_code == 429

    def test_requires_authentication(self, client, db):
        assert client.post("/api/auth/change-password", json=self.BODY).status_code == 401


# --------------------------------------------------------------------------- cài đặt
class TestSettings:
    def test_get_merges_defaults_with_stored(self, client, db, auth_headers):
        data = client.get("/api/auth/settings", headers=auth_headers).json()["data"]
        assert data == {"theme": "dark", "language": "vi", "soundEnabled": True, "academicAlerts": True}

    def test_update_all_four_frontend_fields_are_persisted(self, client, db, auth_headers):
        res = client.put("/api/auth/settings", headers=auth_headers, json={
            "theme": "light", "language": "en", "soundEnabled": False, "academicAlerts": False})
        assert res.status_code == 200
        assert db.users[0]["settings"] == {"theme": "light", "language": "en", "soundEnabled": False, "academicAlerts": False}

    def test_partial_update_keeps_other_values(self, client, db, auth_headers):
        client.put("/api/auth/settings", headers=auth_headers, json={"language": "en"})
        assert db.users[0]["settings"]["theme"] == "dark" and db.users[0]["settings"]["language"] == "en"

    @pytest.mark.parametrize("body", [{"theme": "neon"}, {"language": "fr"}, {"soundEnabled": "yes please"}, {"theme": "x" * 10_000}])
    def test_invalid_values_rejected(self, client, db, auth_headers, body):
        assert client.put("/api/auth/settings", headers=auth_headers, json=body).status_code == 400

    def test_unknown_keys_are_not_stored(self, client, db, auth_headers):
        client.put("/api/auth/settings", headers=auth_headers, json={"theme": "light", "role": "admin", "junk": "x" * 1000})
        assert set(db.users[0]["settings"]) == {"theme", "language", "soundEnabled", "academicAlerts"}

    def test_read_failure_does_not_overwrite_saved_settings_with_defaults(self, client, db, auth_headers):
        token = svc.issue_token_for_user(db.users[0])
        original = dict(db.users[0]["settings"])
        with patch.object(svc, "_fetch_user_row", side_effect=svc.DatabaseConnectionException("x")):
            with patch.object(svc, "get_user_by_token", return_value={"id": USER_ID}):
                res = client.put("/api/auth/settings", headers={"Authorization": f"Bearer {token}"}, json={"language": "en"})
        assert res.status_code == 503 and db.users[0]["settings"] == original

    def test_requires_authentication(self, client, db):
        assert client.get("/api/auth/settings").status_code == 401
        assert client.put("/api/auth/settings", json={"theme": "light"}).status_code == 401


# --------------------------------------------------------------------------- endpoint đã gỡ
def test_verify_student_mock_endpoint_is_removed(client, db):
    assert client.post("/api/auth/verify-student", json={"studentId": "20012345"}).status_code == 404
