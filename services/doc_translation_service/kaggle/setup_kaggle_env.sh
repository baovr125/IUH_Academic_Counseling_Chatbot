#!/bin/bash
# ====================================================================================
# SCRIPT SETUP MÔI TRƯỜNG KAGGLE NOTEBOOK CHO OLLAMA (QWEN 2.5 7B) & OCR WORKER
# ====================================================================================

echo "🚀 [1/4] Đang cài đặt Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo "⚡ [2/4] Khởi chạy Ollama service ngầm..."
ollama serve > ollama.log 2>&1 &
sleep 5

echo "📥 [3/4] Tải mô hình AI Qwen 2.5 7B GGUF..."
ollama pull qwen2.5:7b

echo "📦 [4/4] Cài đặt các thư viện Python cho Translation & OCR..."
pip install --quiet pymupdf pymupdf4llm markdown-pdf python-docx python-pptx paddlepaddle paddleocr httpx redis celery pyngrok

echo "✅ Hoàn tất cài đặt môi trường trên Kaggle Notebook!"
