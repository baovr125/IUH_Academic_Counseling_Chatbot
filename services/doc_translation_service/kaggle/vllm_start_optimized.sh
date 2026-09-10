#!/bin/bash
# ====================================================================================
# SCRIPT START vLLM TỐI ƯU HÓA: PREFIX CACHING & SPECULATIVE DECODING
# IUH Doc Translation Service - Kaggle 2x Tesla T4 GPU
# ====================================================================================

MODEL_PATH="${1:-/kaggle/input/notebooks/baonguyenvan/download-qwen-awqandvllm-offline-packages/Qwen2.5-14B-AWQ}"
SERVED_NAME="${2:-Qwen/Qwen2.5-14B-Instruct-AWQ}"
PORT="${3:-8000}"

echo "🚀 Đang khởi động vLLM OpenAI API Server với:"
echo "   - Model: $MODEL_PATH ($SERVED_NAME)"
echo "   - Tensor Parallel: 2 (2x Tesla T4 GPU)"
echo "   - Automatic Prefix Caching: BẬT (--enable-prefix-caching)"
echo "   - Max Model Len: 8192 (8K Context)"
echo "   - GPU Memory Utilization: 0.90"

python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "$SERVED_NAME" \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 8192 \
    --enable-prefix-caching \
    --dtype half \
    --port "$PORT" \
    --host 0.0.0.0
