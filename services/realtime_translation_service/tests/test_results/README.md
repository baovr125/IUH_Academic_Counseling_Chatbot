# Kết quả Benchmark & Unit Test — Realtime Translation Service

Bản sao để xem nhanh trong repo. Bản gốc nằm ở `G:\Khoa_Luan\word\Report\realtime_translation\`
và được đồng bộ sang đây sau mỗi phase (lần đồng bộ gần nhất ghi ở cuối file).

## Bắt đầu đọc từ đây

- [benchmark_unit_test_master_report.md](benchmark_unit_test_master_report.md) — tổng quan, môi trường, tiến độ từng phase.

## Benchmark

| Phase | Report | Trạng thái |
|---|---|---|
| Kế hoạch | [benchmark_plan.md](benchmark_plan.md) | Xong |
| 2.1 Language Detection | [benchmark_language_detection_report.md](benchmark_language_detection_report.md) | 5/5 PASS |
| 2.2 Domain Detection | [benchmark_domain_detection_report.md](benchmark_domain_detection_report.md) | 5/5 PASS |
| 2.3 Thuật ngữ & chất lượng dịch | `benchmark_translation_quality_report.md` | Đang chạy |
| 2.4 Độ trễ | `benchmark_latency_streaming_report.md` | Chưa viết |
| 2.5 Fallback | `benchmark_fallback_report.md` | Chưa viết |

## Unit test

| Phase | Report | Kết quả |
|---|---|---|
| Kế hoạch | [unit_test_plan.md](unit_test_plan.md) | 304 test |
| 4.1 Language Detection | [unit_test_language_detection_report.md](unit_test_language_detection_report.md) | 129/129 PASS |
| 4.2 Domain Detection | [unit_test_domain_detection_report.md](unit_test_domain_detection_report.md) | 44/44 PASS |
| 4.3 LLM streaming & fallback | [unit_test_llm_streaming_fallback_report.md](unit_test_llm_streaming_fallback_report.md) | 61/61 PASS |
| 4.4 Từ điển, cache, định tuyến | [unit_test_dictionary_cache_routing_report.md](unit_test_dictionary_cache_routing_report.md) | 38/38 PASS |
| 4.5 TTS & phân tích từ | [unit_test_tts_word_analysis_report.md](unit_test_tts_word_analysis_report.md) | 25/25 PASS |
| 4.6 Công cụ đo | [unit_test_evaluation_tooling_report.md](unit_test_evaluation_tooling_report.md) | 7/7 PASS |

## Dữ liệu chi tiết

`test_artifacts/`: kết quả thô của benchmark (`*.jsonl`, `*.json`), log, JUnit XML và coverage của unit test,
script chạy (`run_llm_benchmarks.sh`, `make_unit_report.py`).

Lần đồng bộ gần nhất: 2026-10-10 (sau Phase 4).
