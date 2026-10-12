"""Cấu hình auth-service, đọc từ biến môi trường.

Bí mật JWT là bắt buộc và không có giá trị mặc định: thiếu hoặc yếu thì service từ chối khởi động
(``validate_config()`` được gọi ở sự kiện startup) thay vì âm thầm chạy với khóa công khai.
"""
import os

ALGORITHM = "HS256"  # cố định, không cho cấu hình để tránh hạ cấp thuật toán
TOKEN_ISSUER = "iuh-auth-service"
MIN_SECRET_LENGTH = 32
KNOWN_INSECURE_SECRETS = frozenset({
    "super-secret-key-iuh-chatbot-2026",
    "your-secret-key",
    "changeme",
    "secret",
})

# Tuổi thọ access token (phút). Mặc định 60 phút; client làm mới qua POST /refresh.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
# Thời gian tối đa một phiên có thể được gia hạn kể từ lần đăng nhập bằng mật khẩu.
SESSION_MAX_AGE_DAYS = int(os.getenv("SESSION_MAX_AGE_DAYS", "7"))

LOGIN_MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))          # theo (IP, tài khoản)
LOGIN_MAX_FAILURES_PER_ACCOUNT = int(os.getenv("LOGIN_MAX_FAILURES_PER_ACCOUNT", "30"))
LOGIN_LOCK_SECONDS = int(os.getenv("LOGIN_LOCK_SECONDS", "900"))


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def docs_enabled() -> bool:
    """/docs và /openapi.json chỉ bật khi đặt rõ ENABLE_API_DOCS=true (mặc định tắt)."""
    return _truthy(os.getenv("ENABLE_API_DOCS", "false"))


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret) < MIN_SECRET_LENGTH or secret in KNOWN_INSECURE_SECRETS:
        raise RuntimeError(
            "JWT_SECRET_KEY chưa được cấu hình an toàn: cần chuỗi ngẫu nhiên dài ít nhất "
            f"{MIN_SECRET_LENGTH} ký tự và không phải giá trị mẫu."
        )
    return secret


def get_supabase_key() -> str:
    """Khóa phía server. Ưu tiên service-role; khóa publishable chỉ là phương án cuối cùng."""
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or ""


def validate_config() -> None:
    get_jwt_secret()
    if ACCESS_TOKEN_EXPIRE_MINUTES <= 0 or ACCESS_TOKEN_EXPIRE_MINUTES > 24 * 60:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES phải nằm trong khoảng 1..1440.")


def cors_origins() -> list:
    default = (
        "http://localhost,http://127.0.0.1,http://localhost:3000,"
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    return [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", default).split(",")
            if o.strip() and o.strip() != "*"]
