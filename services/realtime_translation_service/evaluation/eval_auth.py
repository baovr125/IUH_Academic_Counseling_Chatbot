"""Tạo token đánh giá hợp lệ cho các script benchmark/đánh giá.

Các service không còn chấp nhận header X-User-ID để "bypass" xác thực. Script đánh giá phải gửi
JWT thật, ký bằng JWT_SECRET_KEY của môi trường (đặt biến này trước khi chạy, cùng giá trị với .env).
Gọi qua Kong (mặc định http://localhost:8000) vì cổng 8003 không còn publish ra host.
"""
import datetime
import os

from jose import jwt

GATEWAY_URL = os.getenv("EVAL_GATEWAY_URL", "http://localhost:8000")


def make_eval_token(user_id: str = "admin-evaluation", role: str = "student", minutes: int = 120) -> str:
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret) < 32:
        raise SystemExit("Hãy đặt biến môi trường JWT_SECRET_KEY (giống giá trị trong .env) trước khi chạy script đánh giá.")
    now = datetime.datetime.now(datetime.timezone.utc)
    claims = {"sub": user_id, "role": role, "iss": "iuh-auth-service", "iat": now, "exp": now + datetime.timedelta(minutes=minutes)}
    return jwt.encode(claims, secret, algorithm="HS256")


def eval_headers(extra=None):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {make_eval_token()}"}
    headers.update(extra or {})
    return headers
