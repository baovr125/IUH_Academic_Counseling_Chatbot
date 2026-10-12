# Unit Test — Công cụ đo (metric, kiểm tra dataset) (Phase 4.6)

## A. Thông tin chạy test

| Mục | Nội dung |
|---|---|
| Thời gian | 2026-10-10 16:51:57 → 16:52:08 (+0700) |
| Mã nguồn | Git HEAD `7e846214` + thay đổi chưa commit; vân tay `app/**/*.py` = `5ac072ebfd20` |
| Python / runner | Python 3.11.8, pytest 8.4.2, pytest-asyncio 1.4.0 (`asyncio_mode=auto`), coverage 7.15.4 (pytest-cov) |
| Lệnh chạy chính xác | `cd services/realtime_translation_service && python -m pytest tests/unit/test_detection_metrics_phase2.py tests/unit/test_benchmark_contract.py -p no:cacheprovider -o addopts= -q -rA --junitxml=<report>/test_artifacts\unit_4_6_junit.xml --cov=evaluation.metrics.compute_detection_metrics --cov=evaluation.metrics.calibrate_thresholds --cov=evaluation.validate_dataset --cov-report=term --cov-report=json:<report>/test_artifacts\unit_4_6_coverage.json` |
| File test | `tests/unit/test_detection_metrics_phase2.py`, `tests/unit/test_benchmark_contract.py` |
| Cô lập dependency | Hàm thuần trên dữ liệu nhỏ trong test và các file dataset trong repo. |
| Bằng chứng | JUnit XML `test_artifacts/unit_4_6_junit.xml`, log `test_artifacts/unit_4_6_pytest.log`, coverage `test_artifacts/unit_4_6_coverage.json` |
| Mã thoát pytest | 0 |

Ghi chú cột: *Expected Result* của từng test là các khẳng định (`assert`) viết trong test; *Actual Result* lấy từ JUnit XML.
*Precondition* chung của nhóm ghi ở hàng "Cô lập dependency".

## B. Bảng test case chi tiết

| Test Case ID | Module/Function | Test Case Description | Precondition | Test Data | Expected Result | Actual Result | Status | Failure Reason | Evidence/Log |
|---|---|---|---|---|---|---|---|---|---|
| UT-EV-001 | `test_detection_metrics_phase2.py::test_confusion_matrix_keeps_rejected_predictions` | confusion matrix keeps rejected predictions | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_6_junit.xml` (2673 ms) |
| UT-EV-002 | `test_detection_metrics_phase2.py::test_per_language_recall_counts_rejection_as_false_negative` | per language recall counts rejection as false negative | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_6_junit.xml` (1 ms) |
| UT-EV-003 | `test_detection_metrics_phase2.py::test_confidence_metrics_return_ece_and_brier_score` | confidence metrics return ece and brier score | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_6_junit.xml` (1 ms) |
| UT-EV-004 | `test_detection_metrics_phase2.py::test_threshold_evaluation_rejects_low_confidence_and_margin` | threshold evaluation rejects low confidence and margin | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_6_junit.xml` (1 ms) |
| UT-EV-005 | `test_detection_metrics_phase2.py::test_calibration_skips_engines_without_scores` | calibration skips engines without scores | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_6_junit.xml` (3 ms) |
| UT-EV-006 | `test_benchmark_contract.py::test_phase1_dataset_splits_have_unique_valid_records` | phase1 dataset splits have unique valid records | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_6_junit.xml` (2 ms) |
| UT-EV-007 | `test_benchmark_contract.py::test_dataset_status_vocabulary_is_closed` | dataset status vocabulary is closed | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_6_junit.xml` (2 ms) |

## C. Tổng kết

| Tổng | PASS | FAIL | PENDING | BLOCKED | SKIPPED | Tỉ lệ pass (trên số đã chạy) |
|---:|---:|---:|---:|---:|---:|---:|
| 7 | 7 | 0 | 0 | 0 | 0 | 100.0% |

**Coverage (dòng lệnh) của các module được nhắm:** tổng 49.7%

| File | Số lệnh | Lệnh chưa chạy | Coverage |
|---|---:|---:|---:|
| `evaluation/metrics/calibrate_thresholds.py` | 50 | 16 | 68.0% |
| `evaluation/metrics/compute_detection_metrics.py` | 192 | 116 | 39.6% |
| `evaluation/validate_dataset.py` | 46 | 13 | 71.7% |
