#!/bin/bash

# Kiểm tra xem người dùng có nhập ID chưa
if [ -z "$1" ]; then
  echo "❌ Lỗi: Bạn chưa nhập Runpod ID."
  echo "💡 Cách dùng: ./update_runpod_env.sh <RUNPOD_ID>"
  echo "Ví dụ: ./update_runpod_env.sh okq8qkec61r4j1"
  exit 1
fi

RUNPOD_ID=$1
MODEL_NAME="QuantTrio/Qwen3.6-35B-A3B-AWQ"

echo "🔄 Đang cập nhật file .env với Runpod ID: $RUNPOD_ID ..."

# Cập nhật OPENAI_BASE_URL
sed -i -E "s|OPENAI_BASE_URL=.*|OPENAI_BASE_URL=\"https://${RUNPOD_ID}-8000.proxy.runpod.net/v1\"|g" .env

# Cập nhật OPENAI_API_KEY (Theo chuẩn sk-[RUNPOD_ID])
sed -i -E "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=\"sk-${RUNPOD_ID}\"|g" .env

# Cập nhật Model Name
sed -i -E "s|OPENAI_MODEL_NAME=.*|OPENAI_MODEL_NAME=\"${MODEL_NAME}\"|g" .env
sed -i -E "s|OLLAMA_REWRITER_MODEL=.*|OLLAMA_REWRITER_MODEL=\"${MODEL_NAME}\"|g" .env

echo "✅ Đã cập nhật .env thành công!"
echo "🚀 Đang khởi động lại Chatbot..."
docker compose restart academic-chatbot-service
echo "🎉 Hoàn tất!"
