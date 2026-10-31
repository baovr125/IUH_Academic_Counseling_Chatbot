# Thư mục eval: script đo cho Chương 5

Mọi script chạy từ thư mục `Report` bằng `python -B -X utf8 eval/<tên>.py`. Máy cần có các thư viện của dự án và tệp `.env` của dự án (Supabase, khóa Gemini). Script chỉ **đọc** mã dự án và Supabase; không script nào ghi vào cơ sở dữ liệu.

| Thí nghiệm | Script | Gọi dịch vụ ngoài? | Kết quả |
|---|---|---|---|
| Môi trường | `env_info.py` | Không | `results/env_info.json` |
| Thống kê kho (Bảng 4.2) | `kb_stats.py` | Đọc Supabase | `results/kb_stats.json` |
| E1 Truy xuất | `run_retrieval_ablation.py` | Đọc Supabase, mô hình chạy cục bộ | `results/retrieval_ablation.json` |
| E2 Câu trả lời | `run_answer_eval.py`, rồi `rating_tools.py make` / `merge` / `report` | **Gọi LLM (Gemini)**, đọc Supabase | `results/answers_V1.jsonl`, `answers_V2.jsonl`, `rating_*.csv`, `answer_eval.json` |
| E3 Bộ nhớ đệm | `run_cache_eval.py` | Không (mô phỏng quy tắc trong bộ nhớ) | `results/cache_eval.json` |
| E4 Bộ lọc an toàn | `run_guardrail_eval.py` | Không | `results/guardrail_eval.json` |
| E5 Độ trễ | `run_answer_eval.py --versions V2`, rồi `run_latency_eval.py` | Gọi LLM | `results/latency_summary.json` |
| E6 Kiểm thử tự động | `run_test_suites.py` | Không | `results/test_suites.json` |

Dữ liệu vào nằm trong `data/`: `questions.jsonl` (45 câu hỏi có nhãn nguồn đúng, Phụ lục F), `key_phrases.json` (cụm khóa để xác định nguồn tương đương), `cache_pairs.jsonl` (23 cặp câu cho E3), `guardrail_attacks.jsonl` và `guardrail_benign.jsonl` (E4). Hình 5.1 đến 5.3 được vẽ bằng `figures/src/ch5/H5-02.py`, `H5-03.py`, `H5-04.py` từ các tệp kết quả ở trên.

## Chạy lại từ đầu

```
python -B -X utf8 eval/kb_stats.py
python -B -X utf8 eval/run_retrieval_ablation.py
python -B -X utf8 eval/run_cache_eval.py
python -B -X utf8 eval/run_guardrail_eval.py
python -B -X utf8 eval/run_answer_eval.py                 # tốn hạn mức API: 45 câu x (V1: 1 lời gọi, V2: 2 lời gọi)
python -B -X utf8 eval/run_latency_eval.py --skip-first
python -B -X utf8 eval/rating_tools.py make               # rồi hai người chấm độc lập rating_r1.csv, rating_r2.csv
python -B -X utf8 eval/rating_tools.py merge              # thống nhất các ô khác nhau trong rating_final.csv
python -B -X utf8 eval/rating_tools.py report
python -B -X utf8 build/render_figures.py H5-02 H5-03 H5-04
```

## Lưu ý khi diễn giải

- E1 dùng nguyên văn câu hỏi làm truy vấn (không qua bộ định tuyến). Nhánh toàn văn của hàm lai ghép các từ truy vấn bằng phép AND (`websearch_to_tsquery`), nên với câu hỏi dài hầu như không có kết quả; đây là lý do C3 giống C1.
- Nhãn gold chỉ ghi một hoặc vài tài liệu chính, trong khi nhiều quy định xuất hiện ở nhiều tài liệu; vì vậy E1 báo cả đánh giá chặt và đánh giá nới lỏng (tài liệu chứa đủ cụm khóa trong `key_phrases.json`).
- E3 mô phỏng quy tắc quyết định, không đo trên bảng `semantic_cache` thật (để không ghi vào CSDL). Chỉ mục mô phỏng chỉ có 23 câu `q1`, nhỏ hơn bộ nhớ đệm thật.
- Độ trễ ở E5 đo trong tiến trình (không gồm Kong, nginx, mạng của client) và phụ thuộc tải của API Gemini tại thời điểm chạy.
