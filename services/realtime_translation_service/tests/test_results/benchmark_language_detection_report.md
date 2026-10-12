# Benchmark — Language Detection (Phase 2.1)

## A. Thông tin chung

| Mục | Nội dung |
|---|---|
| Benchmark | Chất lượng, tính xác định, độ trễ của `detect_language_detailed` (`app/services/language_detection.py`) |
| Thời gian chạy | 2026-10-10, 16:26 – 16:32 (+07) |
| Mã nguồn | Git HEAD `7e846214` + thay đổi chưa commit; vân tay `app/**/*.py` = `5ac072ebfd20` |
| Môi trường | Windows 11, Python 3.11.8, fasttext-wheel 0.9.2 (`lid.176.ftz`), lingua-language-detector 2.1.1 (low-accuracy, mặc định), hiệu chỉnh `models/detect_calibration.json`; CPU (không dùng GPU) |
| Đối tượng | Hàm production dùng chung cho `/text`, `/stream`, `/detect` (không qua HTTP) |
| Dataset | (1) `evaluation/dataset/lang_val.jsonl` — 144 mẫu tự viết, bộ val (không dùng để fit hiệu chỉnh). (2) **Tatoeba hold-out mới**: 2.000 câu, seed `20261010` (khác seed giai đoạn 8): 10 ngôn ngữ hỗ trợ × 150 + 10 ngôn ngữ ngoài phạm vi × 50 (it, pt, nl, pl, tr, id, uk, ar, hi, sv). Lọc 2–300 ký tự, ≥ 2 ký tự chữ. Nhãn = ngôn ngữ của file Tatoeba |
| Tạo dữ liệu | `python -I evaluation/dataset/build_lang_tatoeba_holdout.py <thư_mục_bz2> test_artifacts/ld02_tatoeba_holdout.jsonl` (file nguồn: `downloads.tatoeba.org/exports/per_language/<lang>/<lang>_sentences.tsv.bz2`, tải 2026-10-10) |
| Lệnh chạy | `python evaluation/dev_gate.py --split val --show-errors --json test_artifacts/ld01_val_devgate.json` · `python evaluation/dev_gate.py --file test_artifacts/ld02_tatoeba_holdout.jsonl --show-errors --json test_artifacts/ld02_tatoeba_devgate.json` · `python evaluation/benchmarks/run_lang_detection_bench.py --file test_artifacts/ld02_tatoeba_holdout.jsonl --out test_artifacts/ld02_04_tatoeba_bench.json` · đo cold start: tiến trình Python mới, import + gọi 2 lần (3 lần lặp, `test_artifacts/ld05_cold_start.log`) |
| Cấu hình | Mặc định production; riêng đo độ trễ LD-04 **tắt cache LRU** (`DETECT_CACHE_SIZE=0`) để đo tính toán thật. Mẫu đo độ trễ/xác định lấy rải đều cả 20 ngôn ngữ |
| Tiêu chí | `evaluation.md` mục 1.3 (ghi "đề xuất" trong tài liệu đó) |

## B. Kết quả test case

| Test Case ID | Test Case Description | Test Data | Expected Result | Actual Result | Metric/Measurement | Status | Evidence/Log | Notes |
|---|---|---|---|---|---|---|---|---|
| LD-01 | Chất lượng trên bộ val tự viết (gồm câu ngắn, gõ dở, tiếng Việt không dấu/teencode, HTML/URL, ngoài phạm vi) | `lang_val.jsonl`, 144 mẫu | accuracy ≥ 95%; sai-mà-tự-tin ≤ 1–2%; false-accept ngoài phạm vi ≤ 10% | accuracy trên mẫu rõ ràng 100%; mọi mẫu: 87,1% đúng chặt, 100% đúng-hoặc-abstain; sai-mà-tự-tin 0/144; false-accept 0/19 | accuracy_clear_strict=1,000; accuracy_all_strict=0,871; wrong_confident=0,000; oos_false_accept=0,000; tiếng Việt 100% | PASS | `test_artifacts/ld01_val_devgate.{json,log}` | 16 mẫu không đúng chặt đều là **abstain minh bạch** (`uncertain`) ở câu 1–3 từ/gõ dở ("Thanks", "Es", "大学"), được tiêu chí cho phép ("input ngắn ≥ 90% **hoặc** abstain minh bạch") |
| LD-02 | Chất lượng trên nguồn công khai độc lập, chưa dùng để chỉnh | Tatoeba 2.000 câu (1.500 hỗ trợ + 500 ngoài phạm vi) | accuracy ≥ 95%; tiếng Việt ≥ 97%; sai-mà-tự-tin ≤ 1–2%; false-accept ≤ 10% | 1.467/1.500 câu hỗ trợ đúng (97,8%); 0 câu bị gán sai nhãn; 33 câu abstain; tiếng Việt 148/150 (98,7%); ngoài phạm vi: 472 `unsupported`, 27 `uncertain`, 1 bị gán nhãn (uk→ru) | accuracy chặt 97,8%; sai-mà-tự-tin 1/2.000 = 0,05%; false-accept 1/500 = 0,2%; nhận đúng `unsupported` 94,4% | PASS | `test_artifacts/ld02_tatoeba_devgate.{json,log}`, `ld02_04_tatoeba_bench.json` (khóa `per_language`, `outcomes_not_correct`) | Thấp nhất là `es` 135/150 (90%; 14 abstain + 1 bị coi là ngoài phạm vi). Ca sai duy nhất: "Де ти? — Я в саду." (tiếng Ukraina, gán `ru`, conf 0,98) |
| LD-03 | Tính xác định: cùng đầu vào cho cùng kết quả | 200 câu Tatoeba rải đều 20 ngôn ngữ, chạy 3 lần | 100% *(đề xuất, chờ duyệt)* | 200/200 giống hệt (status, ngôn ngữ, confidence 6 chữ số) | 100% | PASS | `ld02_04_tatoeba_bench.json` (`determinism`) | Ngưỡng 100% là đề xuất của người kiểm thử, `evaluation.md` không định nghĩa |
| LD-04 | Độ trễ warm (cache tắt) | 500 câu Tatoeba rải đều 20 ngôn ngữ × 3 lượt | P95 ≤ 50 ms | p50 0,089–0,091 ms; p95 0,250–0,266 ms; p99 0,342–0,375 ms; max 0,675 ms | p95 lớn nhất 0,266 ms | PASS | `ld02_04_tatoeba_bench.json` (`latency_rounds`) | Đo trong tiến trình, không gồm HTTP/serialize. dev_gate (cache bật) cho p95 0,47 ms trên val |
| LD-05 | Độ trễ cold: import module + lần gọi đầu trong tiến trình mới | 1 câu tiếng Anh, 3 lần lặp | Chưa có ngưỡng chính thức – chỉ báo cáo | import 0,406–0,409 s; lần gọi đầu 57–60 ms (nạp fastText + Lingua); lần gọi thứ hai 0,24 ms | như bên | PASS (chỉ đo) | `test_artifacts/ld05_cold_start.log` | Service gọi `warm_up()` lúc khởi động nên người dùng không gặp độ trễ lần đầu này |

### Chi tiết theo ngôn ngữ (LD-02)

| Ngôn ngữ (hỗ trợ) | Đúng | Abstain | Gán sai | | Ngôn ngữ (ngoài phạm vi) | `unsupported` | `uncertain` | Bị gán nhãn |
|---|---:|---:|---:|---|---|---:|---:|---:|
| en | 143 | 7 | 0 | | it | 49 | 1 | 0 |
| vi | 148 | 2 | 0 | | pt | 45 | 5 | 0 |
| de | 150 | 0 | 0 | | nl | 42 | 8 | 0 |
| zh | 150 | 0 | 0 | | pl | 49 | 1 | 0 |
| ja | 150 | 0 | 0 | | tr | 48 | 2 | 0 |
| ko | 150 | 0 | 0 | | id | 44 | 6 | 0 |
| fr | 143 | 7 | 0 | | uk | 46 | 3 | **1** |
| es | 135 | 15* | 0 | | ar | 50 | 0 | 0 |
| ru | 148 | 2 | 0 | | hi | 50 | 0 | 0 |
| th | 150 | 0 | 0 | | sv | 49 | 1 | 0 |

\* `es`: 14 `uncertain` + 1 `unsupported` (một câu tiếng Tây Ban Nha bị coi là ngôn ngữ ngoài phạm vi).

Lý do abstain ở câu hỗ trợ: `low_confidence` 18, `out_of_scope` 10 (+1 `unsupported`), `short_input` 3, `engines_disagree` 1.

## C. Tổng hợp

| Tổng test case | PASS | FAIL | PENDING | BLOCKED | SKIPPED |
|---:|---:|---:|---:|---:|---:|
| 5 | 5 | 0 | 0 | 0 | 0 |

| Metric | val (144) | Tatoeba hold-out (2.000) | Tiêu chí `evaluation.md` |
|---|---|---|---|
| Accuracy (đúng chặt) | 100% (mẫu rõ ràng); 87,1% (mọi mẫu, phần còn lại là abstain) | 97,8% | ≥ 95% |
| Tiếng Việt | 100% | 98,7% | ≥ 97% |
| Sai-mà-tự-tin | 0% | 0,05% | ≤ 1–2% |
| False-accept ngoài phạm vi | 0% | 0,2% | ≤ 10% |
| P95 warm | 0,47 ms (cache bật) | 0,27 ms (cache tắt) | ≤ 50 ms |

Baseline: giai đoạn 8 ghi nhận trên Tatoeba hold-out cũ (seed khác, 2.690 câu, Lingua low-accuracy) accuracy chặt 97,95%, sai-mà-tự-tin 0,30%, false-accept 0,87%. Lần này 97,8% / 0,05% / 0,2% — cùng mức (khác mẫu nên không so trực tiếp từng điểm).

## D. Phân tích

- **Đạt:** cả 5 test case đạt tiêu chí. Hệ thống ưu tiên **abstain thay vì đoán sai**: trên 1.500 câu hỗ trợ không có câu nào bị gán sai nhãn; mọi sai sót đều là `uncertain` (người dùng được yêu cầu chọn ngôn ngữ).
- **Điểm yếu đã xác minh:** tiếng Tây Ban Nha abstain nhiều nhất (10%), một phần vì bị nghi là ngôn ngữ ngoài phạm vi gần (pt/it) — `reason=out_of_scope`. Cặp uk/ru: 1 câu tiếng Ukraina ngắn bị gán `ru` với confidence 0,98 (chữ Kirin chung, câu ngắn).
- **Hạn chế của phương pháp:** Tatoeba là câu sạch, ngắn, có nhãn nhiễu (câu sai ngôn ngữ trong file) — không đại diện nhập liệu thật trong ứng dụng. Không loại trừ được trùng lặp ngẫu nhiên với mẫu Tatoeba của giai đoạn 8 vì file mẫu cũ không còn. Bộ val do nhóm tự viết. Độ trễ đo trong tiến trình trên laptop; không gồm mạng/HTTP.
- **Nhận định (chưa kiểm chứng):** tỉ lệ abstain có thể giảm nếu hạ ngưỡng hiệu chỉnh, đổi lại sai-mà-tự-tin tăng; chưa thử trong đợt này.
