#!/bin/sh
# Sinh cấu hình Kong từ template rồi khởi động Kong.
# Bí mật JWT lấy từ biến môi trường, không bao giờ nằm trong file được commit.
set -eu

if [ -z "${JWT_SECRET_KEY:-}" ] || [ "${#JWT_SECRET_KEY}" -lt 32 ]; then
  echo "[kong-entrypoint] JWT_SECRET_KEY chưa đặt hoặc ngắn hơn 32 ký tự. Dừng." >&2
  exit 1
fi
case "$JWT_SECRET_KEY" in
  super-secret-key-iuh-chatbot-2026|changeme|secret)
    echo "[kong-entrypoint] JWT_SECRET_KEY là giá trị mẫu đã bị lộ. Hãy đặt chuỗi ngẫu nhiên mới." >&2
    exit 1
    ;;
esac

PUBLIC_ORIGIN="${PUBLIC_ORIGIN:-http://localhost}"

# token_urlsafe chỉ gồm [A-Za-z0-9_-] nên an toàn với sed; kiểm tra thêm để chắc chắn.
case "$JWT_SECRET_KEY$PUBLIC_ORIGIN" in
  *'|'*|*'&'*|*'\'*|*'"'*)
    echo "[kong-entrypoint] Giá trị biến môi trường chứa ký tự không hợp lệ (| & \ \")." >&2
    exit 1
    ;;
esac

sed -e "s|__JWT_SECRET_KEY__|${JWT_SECRET_KEY}|g" \
    -e "s|__PUBLIC_ORIGIN__|${PUBLIC_ORIGIN}|g" \
    /etc/kong-template/kong.template.yml > /tmp/kong.yml

export KONG_DECLARATIVE_CONFIG=/tmp/kong.yml
exec /docker-entrypoint.sh kong docker-start
