# Đánh giá chất lượng sinh từ vựng bằng AI (flashcard_service)

Bộ công cụ chạy **thủ công** (tốn lượt gọi LLM thật, không nằm trong CI). Chạy từ thư mục `services/flashcard_service`:
`python -m evaluation.<tên>`. Khóa API đọc từ `.env` ở thư mục gốc dự án hoặc biến môi trường; không bao giờ được in ra.

> **Giới hạn hạn mức (đã gặp khi đo thật):** Groq free = 8.000 token/phút (một lần sinh 20 từ cần ~6.000 token), Gemini 2.5 Flash free =
> 20 yêu cầu/ngày. Vì vậy `run_vocab_eval` nghỉ giữa các lần chạy và tự chờ khi provider báo 429; cả bộ có thể mất hơn một giờ.
> Dùng `--resume` để chạy tiếp, `--limit N` để thử nhanh.

## Thành phần

| Tệp | Việc làm |
|---|---|
| `dataset/topics.jsonl` | 30 chủ đề × trình độ A1–C2 × mục đích (IELTS/TOEIC/IT/giao tiếp...) |
| `dataset/passages.jsonl` | 8 đoạn văn tiếng Anh (tin tức, công nghệ, sức khỏe, thư, hội thoại...) |
| `dataset/injections.jsonl` | 20 payload prompt injection (đóng khung, đổi vai, đòi lộ khóa, Unicode lạ...) |
| `run_vocab_eval.py` | Chạy sinh từ, ghi từng lần (`results/*.jsonl`) + tổng hợp chỉ số (`*.summary.json`). Biến thể `three_stage` (production) và `single_call` (đối chứng) |
| `check_ipa.py` | Đối chiếu IPA với từ điển công khai (cận dưới độ chính xác) |
| `rating.py` | `make` phiếu chấm tay · `judge` LLM-judge · `score` tính điểm + kappa |
| `run_injection_eval.py` | Thử prompt injection thật, kiểm tra rò rỉ/trệch schema |

## Quy trình

```bash
# 1) Sinh dữ liệu bằng phương án B (production) và đối chứng A trên cùng mô hình
python -m evaluation.run_vocab_eval --variant three_stage --dataset topics   --out results/topics_B
python -m evaluation.run_vocab_eval --variant single_call --dataset topics   --out results/topics_A
python -m evaluation.run_vocab_eval --variant three_stage --dataset passages --out results/passages_B

# 2) IPA so với từ điển (mẫu 100 từ đơn)
python -m evaluation.check_ipa --results results/topics_B.jsonl --n 100 --out results/ipa_check.json

# 3) Chấm chất lượng nội dung: phiếu cho người + LLM-judge (nên khác mô hình sinh)
python -m evaluation.rating make  --results results/topics_B.jsonl --n 100 --out results/rating_sheet.csv
python -m evaluation.rating judge --results results/topics_B.jsonl --n 100 --out results/judge.jsonl --providers gemini
# ... người chấm điền results/rating_sheet.csv (thang điểm ở docstring rating.py) rồi:
python -m evaluation.rating score --sheet results/rating_sheet.csv --judge results/judge.jsonl

# 4) Prompt injection thật
python -m evaluation.run_injection_eval --repeat 2 --out results/injection
```

## Chỉ số và ngưỡng mục tiêu

Các ngưỡng là **mục tiêu ban đầu** (chưa hiệu chỉnh); số đo thật nằm trong `results/*.summary.json`.

| Chỉ số | Ngưỡng | Nguồn đo |
|---|---|---|
| Thẻ đúng schema trên số ứng viên | ≥ 98% | `run_vocab_eval` (`schema_valid_rate_of_candidates`) |
| Đạt ≥ 90% số lượng yêu cầu | ≥ 90% lượt chạy | `count_fulfilment_ge90pct` |
| Trùng từ trong một kết quả | 0 | `runs_with_duplicates` |
| Câu ví dụ chứa từ khóa | ≥ 95% | `example_contains_term` |
| IPA hợp lệ về cú pháp | ≥ 95% | `ipa_present_and_valid` |
| IPA khớp từ điển (từ có trong từ điển) | ≥ 85% | `check_ipa` |
| Nghĩa/ví dụ/bản dịch chấp nhận được | ≥ 90% | `rating score` (người chấm) |
| Đúng chủ đề / hợp trình độ | ≥ 90% / ≥ 80% | `rating score` |
| Độ trễ p50 / p95 (20 từ) | ≤ 12 s / ≤ 30 s | `latency_s` |
| Lỗi hệ thống (không tính provider hết hạn mức) | < 2% | `system_failures` / `runs` |
| Prompt injection | 0 rò rỉ, 0 trệch schema | `run_injection_eval` |

## Hạn chế phải nêu khi báo cáo

* **Một người chấm**: không tính được kappa giữa người với người. `score --judge` chỉ cho kappa giữa người và LLM-judge.
* LLM-judge khác mô hình sinh để giảm thiên lệch tự ưu ái nhưng vẫn là mô hình, không thay thế người chấm.
* `check_ipa` là cận dưới (từ điển trộn giọng Anh/Mỹ, thiếu mục từ cho nhiều từ/cụm từ).
* Kiểm tra prompt injection là thống kê trên mô hình ngẫu nhiên: không chứng minh an toàn tuyệt đối.
* Mẫu 30 chủ đề / 8 đoạn văn là cỡ nhỏ; khoảng tin cậy Wilson 95% được in kèm mọi tỷ lệ.
