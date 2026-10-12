#!/usr/bin/env bash
# Chuỗi benchmark dùng Groq thật (Phase 2.2, 2.3). Chạy tuần tự để không vượt 8.000 token/phút.
cd "G:/Khoa_Luan/IUH_Academic_Counseling_Chatbot/services/realtime_translation_service"
export PYTHONIOENCODING=utf-8
ART="G:/Khoa_Luan/word/Report/realtime_translation/test_artifacts"
M="qwen/qwen3.8-27b"
step() { echo "### $1 START $(date '+%F %T')"; shift; "$@" 2>&1 | grep -v "pkg_resources\|timestamp"; echo "### END $(date '+%F %T')"; }
step DD-01 python evaluation/run_domain_raw.py --split val --model "$M" --out "$ART/dd01_val_qwen.jsonl" --gap 5.0
step DD-02 python evaluation/run_domain_raw.py --split holdout --model "$M" --out "$ART/dd02_holdout_qwen.jsonl" --gap 5.0
step DD-03 python evaluation/run_domain_consistency.py --split val --model "$M" --per-domain 2 --ood 6 --repeats 5 --out "$ART/dd03_consistency_val_qwen.json"
step TA-01-plain  python evaluation/run_domain_raw.py --split dev --kinds in_domain --mode plain  --model "$M" --out "$ART/ta01_dev_plain_qwen.jsonl" --gap 5.0
step TA-01-manual python evaluation/run_domain_raw.py --split dev --kinds in_domain --mode manual --model "$M" --out "$ART/ta01_dev_manual_qwen.jsonl" --gap 5.0
step TA-01-auto   python evaluation/run_domain_raw.py --split dev --kinds in_domain --mode auto   --model "$M" --out "$ART/ta01_dev_auto_qwen.jsonl" --gap 5.0
step TQ-02 python evaluation/run_domain_raw.py --file "$ART/tq_ground_truth.jsonl" --mode auto --model "$M" --out "$ART/tq02_auto_qwen.jsonl" --gap 5.0
echo ALL_LLM_DONE
