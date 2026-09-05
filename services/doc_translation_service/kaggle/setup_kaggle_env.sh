#!/bin/bash
# ====================================================================================
# SCRIPT SETUP MÃ”I TRÆ¯á»œNG KAGGLE NOTEBOOK CHO OLLAMA (QWEN 2.5 7B) & OCR WORKER
# ====================================================================================

echo "ðŸš€ [1/4] Äang cÃ i Ä‘áº·t Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo "âš¡ [2/4] Khá»Ÿi cháº¡y Ollama service ngáº§m..."
OLLAMA_HOST="0.0.0.0:11434" OLLAMA_ORIGINS="*" ollama serve > ollama.log 2>&1 &

# âœ… Health-check loop â€” Ä‘á»£i Ollama thá»±c sá»± sáºµn sÃ ng (tá»‘i Ä‘a 60s, thay vÃ¬ sleep 5 cá»©ng)
echo -n "â³ Chá» Ollama API sáºµn sÃ ng..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        echo " âœ… Ollama sáºµn sÃ ng sau $((i*2))s!"
        break
    fi
    echo -n "."
    sleep 2
done

# Kiá»ƒm tra xem Ollama cÃ³ thá»±c sá»± cháº¡y khÃ´ng
if ! curl -sf http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "âŒ Ollama khÃ´ng khá»Ÿi Ä‘á»™ng Ä‘Æ°á»£c trong 60s! Xem ollama.log Ä‘á»ƒ debug."
    tail -20 ollama.log
    exit 1
fi

echo "ðŸ“¥ [3/4] Táº£i mÃ´ hÃ¬nh AI Qwen 2.5 7B..."
ollama pull qwen2.5:14b

echo "ðŸ§ª Test inference nhanh..."
TEST_RESP=$(curl -sf -X POST http://127.0.0.1:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{"model":"qwen2.5:14b","prompt":"Say hello in one word.","stream":false}')

if echo "$TEST_RESP" | grep -q '"response"'; then
    echo "âœ… Inference OK!"
else
    echo "âŒ Inference FAILED! Response: $TEST_RESP"
    exit 1
fi

echo "ðŸ“¦ [4/4] CÃ i Ä‘áº·t cÃ¡c thÆ° viá»‡n Python cho Translation & OCR..."
pip install --quiet pymupdf pymupdf4llm markdown-pdf python-docx python-pptx httpx redis celery pyngrok

echo ""
echo "âœ… HoÃ n táº¥t cÃ i Ä‘áº·t mÃ´i trÆ°á»ng trÃªn Kaggle Notebook!"
echo "   â†’ BÃ¢y giá» cháº¡y tiáº¿p cÃ¡c cell trong kaggle_worker.ipynb"

