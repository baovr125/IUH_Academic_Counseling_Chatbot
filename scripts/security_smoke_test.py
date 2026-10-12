"""Smoke test bảo mật cho stack docker-compose đang chạy (Kong ở :8000).

Chạy:  python scripts/security_smoke_test.py            (đọc JWT_SECRET_KEY từ biến môi trường hoặc .env)

Script CHỈ gửi các yêu cầu không ghi dữ liệu và không in bất kỳ bí mật nào. Token giả được ký bằng
chính JWT_SECRET_KEY của bạn để kiểm tra các nhánh phân quyền (đó là cách một kẻ biết khóa sẽ làm,
vì vậy khóa phải được giữ bí mật). Mỗi kiểm tra in PASS/FAIL; mã thoát khác 0 nếu có FAIL.
"""
import datetime
import os
import socket
import sys
import time
from pathlib import Path

import httpx
from jose import jwt

ROOT = Path(__file__).resolve().parent.parent
GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8000")
LEAKED_SECRET = "super-secret-key-iuh-chatbot-2026"  # giá trị đã từng nằm trong repo


def load_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "")
    env_file = ROOT / ".env"
    if not secret and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("JWT_SECRET_KEY="):
                secret = line.split("=", 1)[1].strip().strip('"').strip("'")
    if len(secret) < 32:
        sys.exit("Không tìm thấy JWT_SECRET_KEY (>= 32 ký tự) trong môi trường hoặc .env")
    return secret


SECRET = load_secret()
NOW = datetime.datetime.now(datetime.timezone.utc)


def token(role="student", secret=None, exp=300, with_exp=True, iss="iuh-auth-service", sub="00000000-0000-4000-8000-000000000001"):
    claims = {"sub": sub, "role": role, "iat": NOW}
    if iss:
        claims["iss"] = iss
    if with_exp:
        claims["exp"] = NOW + datetime.timedelta(seconds=exp)
    return jwt.encode(claims, secret or SECRET, algorithm="HS256")


def bearer(t):
    return {"Authorization": f"Bearer {t}"}


results = []


def check(name, condition, detail=""):
    results.append(condition)
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not condition else ""))


def port_closed(port):
    s = socket.socket()
    s.settimeout(1.5)
    try:
        return s.connect_ex(("127.0.0.1", port)) != 0
    finally:
        s.close()


def main():
    c = httpx.Client(timeout=10, base_url=GATEWAY)

    print("== Kong: xác thực JWT trên route được bảo vệ (chat)")
    probe = "/api/v1/chat/__smoke_test_no_such_path__"
    r = c.get(probe)
    check("không token -> 401", r.status_code == 401, r.status_code)
    check("token ký bằng secret CŨ đã lộ -> 401", c.get(probe, headers=bearer(token(secret=LEAKED_SECRET))).status_code == 401)
    check("token hết hạn -> 401 (Kong kiểm exp)", c.get(probe, headers=bearer(token(exp=-3600))).status_code == 401)
    check("token không có exp -> 401", c.get(probe, headers=bearer(token(with_exp=False))).status_code == 401)
    check("token sai issuer -> 401", c.get(probe, headers=bearer(token(iss="evil"))).status_code == 401)
    check("token hợp lệ đi qua Kong (upstream trả 404)", c.get(probe, headers=bearer(token())).status_code == 404)
    check("header X-User-ID giả không thay được token", c.get(probe, headers={"X-User-ID": "x", "X-User-Role": "admin"}).status_code == 401)

    print("== Phân quyền admin")
    admin = "/api/admin/ingest/status"
    check("/api/admin không token -> 401 tại Kong", c.get(admin).status_code == 401)
    check("/api/admin chỉ có X-User-ID/X-User-Role -> 401", c.get(admin, headers={"X-User-ID": "attacker", "X-User-Role": "admin"}).status_code == 401)
    check("token role=student -> 403", c.get(admin, headers=bearer(token("student"))).status_code == 403)
    check("token role=public -> 403", c.get(admin, headers=bearer(token("public"))).status_code == 403)
    with c.stream("GET", admin, headers=bearer(token("admin"))) as resp:
        check("token role=admin -> 200", resp.status_code == 200, resp.status_code)
    check("dictionary admin: student -> 403", c.get("/api/v1/admin/dictionary", headers=bearer(token("student"))).status_code == 403)
    check("dictionary admin: không token -> 401", c.get("/api/v1/admin/dictionary").status_code == 401)

    print("== Route dịch")
    check("/translate không token -> 401", c.post("/api/v1/translate/text", json={}).status_code == 401)
    check("/translate/tts vẫn mở (phục vụ <audio>), không bị Kong chặn", c.get("/api/v1/translate/tts").status_code != 401)

    print("== Cổng nội bộ không còn publish ra host")
    for port in (8001, 8002, 8003):
        check(f"cổng {port} đóng", port_closed(port))

    print("== auth-service qua Kong")
    r = c.get("/api/auth/health")
    check("health 200", r.status_code == 200)
    check("có X-Request-ID", bool(r.headers.get("x-request-id")))
    check("Cache-Control: no-store", r.headers.get("cache-control") == "no-store")
    check("/docs và /openapi.json không lộ", c.get("/docs").status_code == 404 and c.get("/api/auth/openapi.json").status_code == 404)
    r = c.put("/api/auth/does-not-exist", json={})
    check("404 cùng định dạng lỗi chuẩn {ok:false,error}", r.status_code == 404 and r.json().get("ok") is False and "detail" not in r.json())
    r = c.get("/api/auth/me")
    check("/me không token -> 401", r.status_code == 401)
    r = c.post("/api/auth/register", json={"fullName": "A", "email": "bad", "password": "x"})
    check("register sai dữ liệu -> 400 có field", r.status_code == 400 and bool(r.json()["error"].get("details")))
    r = c.post("/api/auth/register", json={"fullName": "An Binh", "email": "x@gmail.com", "password": "Password123", "role": "public"})
    check("mật khẩu phổ biến bị từ chối -> 400 field=password", r.status_code == 400 and r.json()["error"].get("field") == "password")
    check("tài khoản chưa tồn tại: đổi mật khẩu cần token", c.post("/api/auth/change-password", json={}).status_code == 401)

    print("== CORS")
    r = c.options("/api/auth/login", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    check("origin lạ không được cấp Access-Control-Allow-Origin", "access-control-allow-origin" not in r.headers)
    r = c.options("/api/auth/login", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    check("origin dev được phép", r.headers.get("access-control-allow-origin") == "http://localhost:5173")

    print("== Giới hạn tần suất đăng nhập tại Kong (10/phút) — dùng body sai để không chạm DB")
    statuses = []
    for _ in range(14):
        statuses.append(c.post("/api/auth/login", json={"account": "", "password": ""}).status_code)
        time.sleep(0.05)
    check("có 429 sau ~10 lần/phút", 429 in statuses, statuses)

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} kiểm tra đạt" + (f", {failed} KHÔNG đạt" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
