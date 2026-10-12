# Master report — Benchmark & Unit Test, Realtime Translation Service

> Trạng thái file: **ĐANG CẬP NHẬT** (cập nhật sau mỗi phase). Lần cập nhật gần nhất: Phase 0 — 2026-10-10 16:24 (+07).

## 1. Mục tiêu và phạm vi

- **Mục tiêu:** đo hiệu năng/chất lượng các thành phần chính (benchmark) và kiểm tra từng hàm/module theo hành vi mong đợi (unit test) của `services/realtime_translation_service`, ghi kết quả thực tế để trích dẫn trong báo cáo đồ án.
- **Trong phạm vi:** benchmark cấp thành phần (gọi trực tiếp hàm production, không qua frontend) và unit test (`tests/unit`).
- **Ngoài phạm vi (không chạy):**
  - **E2E** — `tests/e2e/test_terminology_ui.py` (Playwright điều khiển trình duyệt): KHÔNG chạy.
  - **Test tích hợp API** — `tests/integration/*` (FastAPI TestClient, 42 test): không phải unit test, không chạy trong đợt này theo yêu cầu "chỉ benchmark và unit test" (ghi SKIPPED, lý do: ngoài phạm vi).
  - Script tích hợp trong `tests/integration/eval_realtime_pipeline.py`, `run_benchmark.py`, `tests/evaluate_domain_detection.py`: là pipeline/live script, không chạy.
  - Tải đồng thời (Locust): cần chạy cả service + Redis + Supabase như hệ thống thật ⇒ ngoài phạm vi.
  - Frontend (vitest): không thuộc service này.

## 2. Môi trường (đã kiểm tra thật)

| Hạng mục | Giá trị |
|---|---|
| Ngày chạy | 2026-10-10 |
| Mã nguồn | Git HEAD `7e846214` (branch `Bao`) **+ 88 file thay đổi chưa commit** (giai đoạn 8, 9, 9b). Dấu vân tay `app/**/*.py` (sha256 12 ký tự đầu): `5ac072ebfd20` |
| OS / CPU / GPU | Windows 11 (10.0.26300), 20 luồng CPU, NVIDIA GeForce RTX 4060 Laptop 8 GB (NLLB chạy CUDA float16) |
| Python | 3.11.8 |
| Thư viện chính | pytest 8.4.2, pytest-asyncio 1.4.0, pytest-cov 7.1.0, fastapi 0.115.7, pydantic 2.11.7, groq 0.33.0, google-genai 1.32.0, ctranslate2 4.6.0, transformers 4.57.6, fasttext-wheel 0.9.2, lingua-language-detector 2.1.1, redis 6.4.0, supabase 2.31.0, sacrebleu 2.6.0 |
| Dịch vụ ngoài | Redis cục bộ (localhost:6379) chạy; Supabase truy cập được (từ điển 246 mục, 6 lĩnh vực); Groq key truy cập `qwen/qwen3.8-27b`, `openai/gpt-oss-*` (KHÔNG có `llama-3.1-8b-instant`); Gemini key có, free tier dễ 429 |
| Hạn mức Groq lúc bắt đầu | 582/1.000 request còn lại trong ngày; 8.000 token/phút |
| Model cục bộ | NLLB-200 distilled 600M (CTranslate2 int8), fastText `lid.176.ftz`, Lingua (low-accuracy), hiệu chỉnh `models/detect_calibration.json` |

Không ghi API key/token vào report. Dữ liệu chi tiết (raw JSONL, JUnit XML, log) để trong `test_artifacts/` cạnh file này.

## 3. Module cần kiểm thử

| Module | Vai trò | Benchmark | Unit test hiện có |
|---|---|---|---|
| `app/services/language_detection.py` (+ `fasttext_detector.py`) | Nhận diện ngôn ngữ (fusion fastText+Lingua, hiệu chỉnh, dừng khi chưa chắc) | Có | `test_language_detection.py` (85), `test_detection_status.py` (44) |
| `app/services/domain_detection.py` | Prompt, parser giao thức `DOMAIN:…`, `decide_domain` | Có | `test_domain_detection.py` (44) |
| `app/services/domain_index.py` | Chỉ mục từ điển, khớp chính xác/quét thuật ngữ | Có (thời gian quét) | trong `test_domain_detection.py` |
| `app/services/domain_llm.py` | Gọi Groq→Gemini, timeout, circuit breaker | Có (fallback) | `test_domain_translation.py` (53) |
| `app/services/domain_translation.py` | Điều phối dịch chuyên ngành, fallback NLLB, cảnh báo | Có | `test_domain_translation.py`, `test_terminology_backend.py` (8) |
| `app/services/cache_service.py` | Cache Redis | — | `test_redis_cache.py` (5) |
| `app/routers/translation.py` (`resolve_voice`, hash TTS) | TTS/CAS | — | `test_voice_resolver.py` (16), `test_cas_deduplication.py` (5) |
| `app/services/word_analysis_service.py` | Phân tích từ | — | `test_word_analysis.py` (4, dùng TestClient + mock NLP) |
| `evaluation/metrics/*`, `evaluation/validate_dataset.py` | Công cụ đo | — | `test_detection_metrics_phase2.py` (5), `test_benchmark_contract.py` (2) |

Tổng unit test có sẵn: **271** trong 12 file (`tests/unit`); đợt này bổ sung 33 test (`test_domain_support_units.py`) ⇒ 304.

## 4. Dữ liệu sẵn có

| Dataset | Số mẫu | Ghi chú |
|---|---|---|
| `lang_dev.jsonl` / `lang_val.jsonl` | 425 / 144 | Tự viết (giai đoạn 8); dev dùng để fit hiệu chỉnh, val để kiểm chứng. UTF-8 sạch |
| `lang_detection_{dev,validation,test}.jsonl` | 63 / 17 / 14 | Bộ cũ, **còn lỗi mojibake** (21/4/5 dòng) ⇒ không dùng để kết luận |
| Tatoeba (tải theo ngôn ngữ) | tải mới | Nguồn công khai độc lập để làm hold-out ngôn ngữ (seed mới) |
| `domain_dev/val/holdout.jsonl` | 86 / 57 / 60 | Giai đoạn 9; hold-out là phần mở đầu bài Wikipedia, chưa từng dùng để chỉnh |
| `ground_truth_dataset.json` | 50 | Cặp dịch tham chiếu cũ (dùng được cho chrF/BLEU nếu phù hợp) |

## 5. Danh sách phase và trạng thái

| Phase | Nội dung | Report | Trạng thái |
|---|---|---|---|
| 0 | Khảo sát code, môi trường, report cũ | file này | **DONE** |
| 1 | Kế hoạch benchmark | `benchmark_plan.md` | **DONE** (18 test case, PLANNED) |
| 2.1 | Benchmark Language Detection | `benchmark_language_detection_report.md` | **DONE** (5 PASS) |
| 2.2 | Benchmark Domain Detection | `benchmark_domain_detection_report.md` | **DONE** (5 PASS) |
| 2.3 | Benchmark thuật ngữ & chất lượng dịch | `benchmark_translation_quality_report.md` | TODO |
| 2.4 | Benchmark độ trễ | `benchmark_latency_streaming_report.md` | TODO |
| 2.5 | Benchmark fallback | `benchmark_fallback_report.md` | TODO |
| 3 | Kế hoạch unit test | `unit_test_plan.md` | **DONE** (304 test, gồm 33 test mới) |
| 4.1–4.6 | Chạy unit test theo nhóm | `unit_test_*_report.md` (6 file) | **DONE** (304 PASS / 0 FAIL) |
| 5 | Tổng hợp | file này | TODO |

## 6. Rủi ro, giới hạn, dependency

- **Hạn mức Groq** (1.000 request/ngày, 8.000 token/phút) giới hạn số mẫu benchmark domain/dịch; benchmark dùng giãn nhịp ~5 s/lời gọi.
- **Code chưa commit:** kết quả gắn với dấu vân tay mã nguồn ở mục 2, không gắn với một commit.
- **Mạng:** benchmark LLM phụ thuộc mạng/Groq; dao động độ trễ giữa các lần chạy.
- **Bộ dữ liệu nhỏ** cho domain (≤ 60 mẫu/bộ) ⇒ khoảng tin cậy rộng.
- **Report cũ:** thư mục report có `evaluation.md` (plan + tiêu chí), `language_detection_evaluation_review.md`, `update.md`, các báo cáo final. Không ghi đè file nào; chỉ tạo file mới `benchmark_*`, `unit_test_*`, file này và `test_artifacts/`.
- Các kết quả benchmark cũ trong service đã được xóa theo yêu cầu (33 file, 2026-10-10) để tránh nhầm lẫn.

## 7. Tiến độ tổng thể

Phase 0 hoàn tất. Tiếp theo: Phase 1 (kế hoạch benchmark).
