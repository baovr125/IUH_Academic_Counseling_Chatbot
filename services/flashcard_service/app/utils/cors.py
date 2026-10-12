"""Danh sách origin được phép gọi trực tiếp service (qua biến môi trường CORS_ALLOW_ORIGINS).

Trình duyệt thường đi qua Kong (Kong tự xử lý CORS); danh sách này chỉ là lớp dự phòng nên
mặc định chỉ gồm các origin phát triển cục bộ, không dùng ``*``.
"""
import os

_DEFAULT_ORIGINS = (
    "http://localhost,http://127.0.0.1,http://localhost:3000,"
    "http://localhost:5173,http://127.0.0.1:5173"
)

CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if origin.strip() and origin.strip() != "*"
]
