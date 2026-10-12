import datetime
import os
import re
import threading
import uuid
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

try:
    from supabase import create_client
except ImportError:  # pragma: no cover - chỉ xảy ra khi thiếu thư viện
    create_client = None

from app import config
from app.utils.logger import logger
from app.utils.throttle import login_throttle

DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "light",
    "language": "vi",
    "soundEnabled": True,
    "academicAlerts": True,
}

_STUDENT_CODE_RE = re.compile(r"^\d{8}$")


# ---------------------------------------------------------------------------
# Ngoại lệ nghiệp vụ (router/handler chuyển thành mã HTTP, không lộ chi tiết nội bộ)
# ---------------------------------------------------------------------------
class DuplicateEmailException(Exception):
    """Email đã được sử dụng."""


class DuplicateStudentCodeException(Exception):
    """Mã số sinh viên đã tồn tại."""


class InvalidCredentialsException(Exception):
    """Sai tài khoản hoặc mật khẩu."""


class CurrentPasswordIncorrectException(Exception):
    """Mật khẩu hiện tại nhập sai khi đổi mật khẩu (không phải lỗi phiên đăng nhập)."""


class InvalidTokenException(Exception):
    """Token không hợp lệ, hết hạn hoặc đã bị thu hồi."""


class DatabaseConnectionException(Exception):
    """Không thể làm việc với cơ sở dữ liệu (mất kết nối, lỗi quyền, lỗi truy vấn)."""


class TooManyAttemptsException(Exception):
    def __init__(self, retry_after: int):
        super().__init__("Quá nhiều lần thử. Vui lòng thử lại sau.")
        self.retry_after = retry_after


# ---------------------------------------------------------------------------
# Supabase: tạo client MỘT lần (tạo mới mỗi request tốn ~200 ms CPU và rò kết nối)
# ---------------------------------------------------------------------------
_client = None
_client_lock = threading.Lock()


def get_supabase():
    global _client
    if _client is not None:
        return _client
    url = os.getenv("SUPABASE_URL")
    key = config.get_supabase_key()
    if not url or not key or create_client is None:
        logger.warning("Supabase credentials not configured in environment.")
        return None
    with _client_lock:
        if _client is None:
            try:
                _client = create_client(url, key)
            except Exception:
                logger.exception("Failed to initialize Supabase client")
                return None
    return _client


def _require_db():
    supabase = get_supabase()
    if not supabase:
        raise DatabaseConnectionException("Không thể kết nối đến cơ sở dữ liệu hệ thống")
    return supabase


# ---------------------------------------------------------------------------
# Mật khẩu
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    # bcrypt chỉ dùng 72 byte đầu; schema đã từ chối mật khẩu dài hơn khi đăng ký/đổi mật khẩu.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception as e:
        logger.warning(f"Error verifying password hash: {type(e).__name__}")
        return False


_dummy_hash: Optional[str] = None


def _get_dummy_hash() -> str:
    """Hash giả để mất cùng thời gian bcrypt khi tài khoản không tồn tại (chống đo thời gian)."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("dummy-password-for-timing-equalization-1")
    return _dummy_hash


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    claims = data.copy()
    claims.update({
        "iat": now,
        "exp": now + (expires_delta or datetime.timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)),
        "iss": config.TOKEN_ISSUER,
    })
    claims.setdefault("oiat", int(now.timestamp()))
    return jwt.encode(claims, config.get_jwt_secret(), algorithm=config.ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Giải mã + kiểm tra chữ ký, exp và iss (đều bắt buộc). Trả None nếu không hợp lệ."""
    try:
        return jwt.decode(
            token,
            config.get_jwt_secret(),
            algorithms=[config.ALGORITHM],
            issuer=config.TOKEN_ISSUER,
            options={"verify_aud": False, "require_exp": True, "require_iss": True, "require_sub": True},
        )
    except JWTError as e:
        logger.warning(f"Invalid or expired JWT token: {e}")
        return None


def _token_version(row: Dict[str, Any]) -> int:
    try:
        return int(row.get("token_version") or 0)
    except (TypeError, ValueError):
        return 0


def issue_token_for_user(row: Dict[str, Any], original_iat: Optional[int] = None) -> str:
    """Claims tối thiểu: không đưa email/họ tên/MSSV vào token (token còn xuất hiện trong URL SSE)."""
    claims: Dict[str, Any] = {
        "sub": str(row["id"]),
        "role": row.get("role") or "student",
        "tv": _token_version(row),
    }
    if original_iat is not None:
        claims["oiat"] = original_iat
    return create_access_token(claims)


# ---------------------------------------------------------------------------
# Người dùng
# ---------------------------------------------------------------------------
def user_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    """Dạng người dùng trả về client (một định dạng camelCase duy nhất, không có hash)."""
    return {
        "id": str(row["id"]),
        "email": row.get("email"),
        "fullName": row.get("full_name") or row.get("email"),
        "studentCode": row.get("student_code"),
        "department": row.get("department"),
        "major": row.get("major"),
        "phoneNumber": row.get("phone_number"),
        "role": row.get("role") or "student",
        "avatarUrl": row.get("avatar_url"),
        "hasPassword": bool(row.get("password_hash")),
        "googleId": row.get("google_id"),
    }


def mask_account(account: str) -> str:
    account = (account or "").strip()
    if "@" in account:
        local, _, domain = account.partition("@")
        return f"{local[:1]}***@{domain}"
    return f"****{account[-3:]}" if len(account) > 3 else "***"


def _fetch_user_row(user_id: str) -> Optional[Dict[str, Any]]:
    supabase = _require_db()
    try:
        res = supabase.table("users").select("*").eq("id", user_id).execute()
    except Exception:
        logger.exception("Error fetching user row")
        raise DatabaseConnectionException("Lỗi cơ sở dữ liệu")
    return res.data[0] if res.data else None


def _find_user_for_login(supabase, account: str) -> Optional[Dict[str, Any]]:
    acc = account.strip()
    if "@" in acc:
        column, value = "email", acc.lower()
    elif _STUDENT_CODE_RE.match(acc):
        column, value = "student_code", acc
    else:
        return None
    try:
        res = supabase.table("users").select("*").eq(column, value).execute()
    except Exception:
        logger.exception("Error querying user for login")
        raise DatabaseConnectionException("Lỗi cơ sở dữ liệu")
    return res.data[0] if res.data else None


def _db_error_code(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    if code:
        return str(code)
    if exc.args and isinstance(exc.args[0], dict):
        return str(exc.args[0].get("code", ""))
    return ""


def register_user(
    email: str,
    password: str,
    full_name: str,
    role: str = "student",
    student_code: Optional[str] = None,
    department: Optional[str] = None,
    major: Optional[str] = None,
) -> Dict[str, Any]:
    supabase = _require_db()

    clean_email = email.strip().lower()
    clean_role = "public" if role == "public" else "student"  # không bao giờ tạo admin ở đây
    is_student = clean_role == "student"
    clean_student_code = student_code.strip() if (is_student and student_code) else None
    clean_department = department.strip() if (is_student and department) else None
    clean_major = major.strip() if (is_student and major) else None

    # Kiểm tra trùng (thân thiện với người dùng); ràng buộc UNIQUE của DB mới là lớp bảo đảm cuối cùng.
    try:
        if supabase.table("users").select("id").eq("email", clean_email).execute().data:
            raise DuplicateEmailException("Email đã được sử dụng")
        if clean_student_code and supabase.table("users").select("id").eq(
            "student_code", clean_student_code
        ).execute().data:
            raise DuplicateStudentCodeException("Mã số sinh viên đã tồn tại")
    except (DuplicateEmailException, DuplicateStudentCodeException):
        raise
    except Exception:
        logger.exception("Error checking duplicate user")
        raise DatabaseConnectionException("Lỗi cơ sở dữ liệu")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row = {
        "id": str(uuid.uuid4()),
        "email": clean_email,
        "password_hash": hash_password(password),
        "full_name": full_name.strip(),
        "student_code": clean_student_code,
        "department": clean_department,
        "major": clean_major,
        "role": clean_role,
        "avatar_url": None,
        "settings": dict(DEFAULT_SETTINGS),
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    try:
        res = supabase.table("users").insert(row).execute()
        if not res.data:
            raise RuntimeError("insert returned no data")
    except Exception as e:
        code = _db_error_code(e)
        text = str(e).lower()
        if code == "23505" or "duplicate key" in text or "unique" in text:
            if "student_code" in text:
                raise DuplicateStudentCodeException("Mã số sinh viên đã tồn tại")
            raise DuplicateEmailException("Email đã được sử dụng")
        # Chi tiết (tên bảng/cột/RLS) chỉ ghi log; client chỉ nhận thông điệp chung.
        logger.error("Failed to insert user", extra={"db_error_code": code, "error_type": type(e).__name__})
        raise DatabaseConnectionException("Lỗi cơ sở dữ liệu")

    logger.info("register_success", extra={"event": "register_success", "user_id": row["id"], "role": clean_role})
    return {
        "message": "Đăng ký tài khoản thành công!",
        "token": issue_token_for_user(row),
        "user": user_to_dict(row),
    }


def login_user(account: str, password: str, client_ip: str = "unknown") -> Dict[str, Any]:
    clean_acc = account.strip()
    wait = login_throttle.retry_after(client_ip, clean_acc)
    if wait:
        logger.warning("login_throttled", extra={"event": "login_throttled", "account": mask_account(clean_acc), "ip": client_ip})
        raise TooManyAttemptsException(wait)

    supabase = _require_db()
    row = _find_user_for_login(supabase, clean_acc)
    stored_hash = (row or {}).get("password_hash")
    # Luôn chạy bcrypt (với hash giả nếu không có user) để thời gian phản hồi không lộ tài khoản tồn tại.
    password_ok = verify_password(password, stored_hash or _get_dummy_hash())

    if not row or not stored_hash or not password_ok:
        login_throttle.record_failure(client_ip, clean_acc)
        logger.warning("login_failed", extra={"event": "login_failed", "account": mask_account(clean_acc), "ip": client_ip})
        raise InvalidCredentialsException("Tài khoản hoặc mật khẩu không chính xác")

    login_throttle.reset(client_ip, clean_acc)
    logger.info("login_success", extra={"event": "login_success", "user_id": str(row["id"]), "ip": client_ip})
    return {
        "token": issue_token_for_user(row),
        "user": user_to_dict(row),
        "message": "Đăng nhập thành công",
    }


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Trả về người dùng theo token, hoặc None nếu token không hợp lệ / user không còn / bị thu hồi.

    Không còn nhánh "fallback từ claims của JWT": nếu DB không xác nhận được user thì không xác thực.
    Lỗi DB được ném lên (DatabaseConnectionException → HTTP 503) thay vì chấp nhận token mù quáng.
    """
    payload = decode_token(token)
    if not payload:
        return None
    row = _fetch_user_row(str(payload["sub"]))
    if not row:
        return None
    try:
        if int(payload.get("tv", 0)) != _token_version(row):
            return None
    except (TypeError, ValueError):
        return None
    return user_to_dict(row)


def refresh_access_token(token: str) -> Dict[str, Any]:
    """Cấp access token mới (vai trò lấy lại từ DB) nếu token cũ còn hạn và phiên chưa quá tuổi tối đa."""
    payload = decode_token(token)
    if not payload:
        raise InvalidTokenException("Token không hợp lệ hoặc đã hết hạn.")
    original_iat = int(payload.get("oiat") or payload.get("iat") or 0)
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    if now - original_iat > config.SESSION_MAX_AGE_DAYS * 86400:
        raise InvalidTokenException("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.")
    row = _fetch_user_row(str(payload["sub"]))
    if not row or int(payload.get("tv", 0)) != _token_version(row):
        raise InvalidTokenException("Token không hợp lệ hoặc đã hết hạn.")
    return {"token": issue_token_for_user(row, original_iat=original_iat), "user": user_to_dict(row)}


def _bump_token_version_fields(row: Dict[str, Any]) -> Dict[str, Any]:
    """Chỉ ghi token_version nếu cột đã tồn tại (xem db/migrations/002_auth_hardening.sql)."""
    return {"token_version": _token_version(row) + 1} if "token_version" in row else {}


def logout_user(user_id: str) -> bool:
    """Thu hồi mọi token đã cấp cho user. Trả False nếu DB chưa có cột token_version (chỉ đăng xuất phía client)."""
    row = _fetch_user_row(user_id)
    if not row:
        return False
    bump = _bump_token_version_fields(row)
    if not bump:
        return False
    supabase = _require_db()
    try:
        supabase.table("users").update(bump).eq("id", user_id).execute()
    except Exception:
        logger.exception("Error revoking tokens")
        raise DatabaseConnectionException("Lỗi cơ sở dữ liệu")
    logger.info("logout_revoked", extra={"event": "logout_revoked", "user_id": user_id})
    return True


def change_password(user_id: str, current_password: str, new_password: str, client_ip: str = "unknown") -> Dict[str, Any]:
    throttle_key = f"pw:{user_id}"
    wait = login_throttle.retry_after(client_ip, throttle_key)
    if wait:
        raise TooManyAttemptsException(wait)

    row = _fetch_user_row(user_id)
    if not row:
        raise InvalidTokenException("Token không hợp lệ hoặc đã hết hạn.")
    stored_hash = row.get("password_hash")
    if not stored_hash or not verify_password(current_password, stored_hash):
        login_throttle.record_failure(client_ip, throttle_key)
        logger.warning("change_password_failed", extra={"event": "change_password_failed", "user_id": user_id})
        raise CurrentPasswordIncorrectException("Mật khẩu hiện tại không chính xác")
    login_throttle.reset(client_ip, throttle_key)

    update = {
        "password_hash": hash_password(new_password),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        **_bump_token_version_fields(row),
    }
    supabase = _require_db()
    try:
        supabase.table("users").update(update).eq("id", user_id).execute()
    except Exception:
        logger.exception("Error updating password")
        raise DatabaseConnectionException("Lỗi cơ sở dữ liệu")

    new_row = {**row, **update}
    logger.info("change_password_success", extra={"event": "change_password_success", "user_id": user_id})
    return {"token": issue_token_for_user(new_row), "user": user_to_dict(new_row)}


_PROFILE_COLUMNS = {
    "full_name": "full_name",
    "phone_number": "phone_number",
    "department": "department",
    "major": "major",
    "avatar_url": "avatar_url",
}


def update_profile(user_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
    row = _fetch_user_row(user_id)
    if not row:
        raise InvalidTokenException("Token không hợp lệ hoặc đã hết hạn.")

    update: Dict[str, Any] = {}
    for key, value in changes.items():
        column = _PROFILE_COLUMNS.get(key)
        if column is None or value is None:
            continue
        if key in ("department", "major") and (row.get("role") != "student"):
            raise ValueError("Chỉ tài khoản Sinh viên / GV IUH mới có Khoa / Viện và Ngành học.")
        update[column] = value if value != "" else None
    if not update:
        return user_to_dict(row)

    update["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    supabase = _require_db()
    try:
        supabase.table("users").update(update).eq("id", user_id).execute()
    except Exception:
        logger.exception("Error updating profile")
        raise DatabaseConnectionException("Lỗi cơ sở dữ liệu")
    return user_to_dict({**row, **update})


def _merged_settings(raw: Any) -> Dict[str, Any]:
    merged = dict(DEFAULT_SETTINGS)
    if isinstance(raw, dict):
        for key in DEFAULT_SETTINGS:
            if key in raw and raw[key] is not None:
                merged[key] = raw[key]
    return merged


def get_user_settings(user_id: str) -> Dict[str, Any]:
    row = _fetch_user_row(user_id)
    return _merged_settings((row or {}).get("settings"))


def update_user_settings(user_id: str, new_settings: Dict[str, Any]) -> Dict[str, Any]:
    """Đọc–gộp–ghi. Nếu đọc lỗi thì báo lỗi (không ghi đè cài đặt cũ bằng giá trị mặc định)."""
    row = _fetch_user_row(user_id)
    current = _merged_settings((row or {}).get("settings"))
    for key, value in new_settings.items():
        if key in DEFAULT_SETTINGS and value is not None:
            current[key] = value
    supabase = _require_db()
    try:
        supabase.table("users").update({"settings": current}).eq("id", user_id).execute()
    except Exception:
        logger.exception("Error updating user settings")
        raise DatabaseConnectionException("Lỗi cơ sở dữ liệu")
    return current
