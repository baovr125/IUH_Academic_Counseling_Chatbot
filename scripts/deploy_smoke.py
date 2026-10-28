#!/usr/bin/env python3
"""Kiểm tra nhanh cổng vào sau khi triển khai bằng docker-compose.prod.yml (xem DEPLOY.md).

Chỉ gọi các endpoint GET (health, trang chủ, route đã khóa), KHÔNG ghi dữ liệu nào vào Supabase.
Để qua được lớp JWT của Kong, script tự ký một token thử nghiệm bằng JWT_SECRET_KEY lấy từ file env
(chỉ đọc cục bộ, không in ra, không gửi đi đâu ngoài chính hệ thống đang kiểm tra).

Cách dùng:
    python scripts/deploy_smoke.py                       # đọc .env.prod, gọi http://127.0.0.1:5173
    python scripts/deploy_smoke.py --base https://<ten>.ts.net
Mã thoát 0 nếu mọi ca đều đạt, 1 nếu có ca lỗi.
"""
import argparse
import base64
import hashlib
import hmac
import json
import sys
import time
import urllib.error
import urllib.request

TOKEN_ISSUER = "iuh-auth-service"  # khớp `key` của consumer JWT trong gateway/kong.template.yml


def load_secret(path):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("JWT_SECRET_KEY="):
                    value = line.split("=", 1)[1].strip()
                    return value[1:-1] if value[:1] in "\"'" else value
    except OSError as exc:
        sys.exit(f"Không đọc được {path}: {exc}")
    sys.exit(f"Không thấy JWT_SECRET_KEY trong {path}")


def b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def make_token(secret):
    head = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    claims = {"iss": TOKEN_ISSUER, "sub": "deploy-smoke", "role": "normal", "exp": int(time.time()) + 600}
    body = b64(json.dumps(claims).encode())
    sig = b64(hmac.new(secret.encode(), head + b"." + body, hashlib.sha256).digest())
    return (head + b"." + body + b"." + sig).decode()


def call(base, path, token=None):
    req = urllib.request.Request(base + path)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read(300).decode("utf-8", "replace"), time.time() - started
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(300).decode("utf-8", "replace"), time.time() - started
    except urllib.error.URLError as exc:
        return 0, str(exc.reason), time.time() - started


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env-file", default=".env.prod", help="file env chứa JWT_SECRET_KEY (mặc định .env.prod)")
    parser.add_argument("--base", default="http://127.0.0.1:5173", help="địa chỉ cần kiểm tra (mặc định http://127.0.0.1:5173)")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):  # console Windows mặc định không in được tiếng Việt
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    base = args.base.rstrip("/")
    token = make_token(load_secret(args.env_file))
    forged = token[:-3] + ("abc" if not token.endswith("abc") else "xyz")
    cases = [
        ("Trang chủ (frontend)", "/", None, 200),
        ("Auth /health (công khai)", "/api/v1/auth/health", None, 200),
        ("Chat /health, KHÔNG token", "/api/v1/chat/health", None, 401),
        ("Chat /health, có token", "/api/v1/chat/health", token, 200),
        ("Translate /health, có token", "/api/v1/translate/health", token, 200),
        ("Token sai chữ ký", "/api/v1/chat/health", forged, 401),
        ("Dịch tài liệu, KHÔNG token", "/api/v1/documents/x/status", None, 401),
        ("Dịch tài liệu, có token (đang khóa)", "/api/v1/documents/x/status", token, 503),
    ]
    failed = 0
    unreachable = False
    print(f"Kiểm tra {base}\n")
    for name, path, tok, expected in cases:
        status, body, elapsed = call(base, path, tok)
        ok = status == expected
        failed += not ok
        unreachable = unreachable or status == 0
        line = f"{'ĐẠT' if ok else 'LỖI'}  {name:38} http={status:<3} (mong {expected}) {elapsed:.2f}s"
        if not ok:
            line += f"  -> {body[:120]!r}"
        print(line)
    print(f"\n{'TẤT CẢ ĐẠT' if not failed else f'{failed} ca lỗi'} ({len(cases)} ca)")
    if unreachable:
        print("Gợi ý: không kết nối được. Kiểm tra `docker compose ps` và đợi ~2 phút sau khi khởi động (chatbot nạp model).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
