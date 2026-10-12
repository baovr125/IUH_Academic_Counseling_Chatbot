# Unit Test — TTS (chọn giọng, hash CAS) và phân tích từ (Phase 4.5)

## A. Thông tin chạy test

| Mục | Nội dung |
|---|---|
| Thời gian | 2026-10-10 16:51:35 → 16:51:56 (+0700) |
| Mã nguồn | Git HEAD `7e846214` + thay đổi chưa commit; vân tay `app/**/*.py` = `5ac072ebfd20` |
| Python / runner | Python 3.11.8, pytest 8.4.2, pytest-asyncio 1.4.0 (`asyncio_mode=auto`), coverage 7.15.4 (pytest-cov) |
| Lệnh chạy chính xác | `cd services/realtime_translation_service && python -m pytest tests/unit/test_voice_resolver.py tests/unit/test_cas_deduplication.py tests/unit/test_word_analysis.py -p no:cacheprovider -o addopts= -q -rA --junitxml=<report>/test_artifacts\unit_4_5_junit.xml --cov=app.routers.translation --cov=app.services.word_analysis_service --cov-report=term --cov-report=json:<report>/test_artifacts\unit_4_5_coverage.json` |
| File test | `tests/unit/test_voice_resolver.py`, `tests/unit/test_cas_deduplication.py`, `tests/unit/test_word_analysis.py` |
| Cô lập dependency | `test_word_analysis.py` gọi endpoint qua FastAPI TestClient trong tiến trình, NLP nặng và Groq bị mock (fixture `mock_heavy_nlp`); MinIO/RabbitMQ/model preload bị patch trong `conftest.py`. |
| Bằng chứng | JUnit XML `test_artifacts/unit_4_5_junit.xml`, log `test_artifacts/unit_4_5_pytest.log`, coverage `test_artifacts/unit_4_5_coverage.json` |
| Mã thoát pytest | 0 |

Ghi chú cột: *Expected Result* của từng test là các khẳng định (`assert`) viết trong test; *Actual Result* lấy từ JUnit XML.
*Precondition* chung của nhóm ghi ở hàng "Cô lập dependency".

## B. Bảng test case chi tiết

| Test Case ID | Module/Function | Test Case Description | Precondition | Test Data | Expected Result | Actual Result | Status | Failure Reason | Evidence/Log |
|---|---|---|---|---|---|---|---|---|---|
| UT-TW-001 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | vi-vi-VN-HoaiMyNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (4 ms) |
| UT-TW-002 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | en-en-US-AriaNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-003 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | de-de-DE-KillianNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-004 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | zh-zh-CN-XiaoxiaoNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-005 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | ja-ja-JP-NanamiNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-006 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | ko-ko-KR-SunHiNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-007 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | fr-fr-FR-DeniseNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-008 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | es-es-ES-ElviraNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-009 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | ru-ru-RU-SvetlanaNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-010 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | th-th-TH-PremwadeeNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-011 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | vi-VN-vi-VN-HoaiMyNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-012 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | en-US-en-US-AriaNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-013 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | en-GB-en-GB-RyanNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-014 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | de-DE-de-DE-KillianNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-015 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_known_languages_and_locales` | resolve voice known languages and locales | Mock/isolation theo mục A | de_DE-de-DE-KillianNeural | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-016 | `test_voice_resolver.py::TestVoiceResolver::test_resolve_voice_fallback_for_unknown_language` | resolve voice fallback for unknown language | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (1 ms) |
| UT-TW-017 | `test_cas_deduplication.py::TestContentAddressableStorageDeduplication::test_identical_text_and_voice_generates_identical_hash` | identical text and voice generates identical hash | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (0 ms) |
| UT-TW-018 | `test_cas_deduplication.py::TestContentAddressableStorageDeduplication::test_case_insensitivity_and_whitespace_trimming` | case insensitivity and whitespace trimming | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (0 ms) |
| UT-TW-019 | `test_cas_deduplication.py::TestContentAddressableStorageDeduplication::test_different_voices_generate_distinct_hashes` | different voices generate distinct hashes | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (0 ms) |
| UT-TW-020 | `test_cas_deduplication.py::TestContentAddressableStorageDeduplication::test_different_languages_generate_distinct_hashes` | different languages generate distinct hashes | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (0 ms) |
| UT-TW-021 | `test_cas_deduplication.py::TestContentAddressableStorageDeduplication::test_object_name_path_structure` | object name path structure | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (0 ms) |
| UT-TW-022 | `test_word_analysis.py::test_spacy_to_wordnet_pos` | spacy to wordnet pos | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (5 ms) |
| UT-TW-023 | `test_word_analysis.py::test_analyze_word_endpoint_success` | Test standard English word analysis (Cache Miss first, then Hit) | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (5749 ms) |
| UT-TW-024 | `test_word_analysis.py::test_analyze_word_endpoint_noun` | Test the same word 'book' but as a Noun in different context | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (64 ms) |
| UT-TW-025 | `test_word_analysis.py::test_analyze_word_non_english` | Test non-English word analysis which skips NLTK and uses basic translation | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_5_junit.xml` (12 ms) |

## C. Tổng kết

| Tổng | PASS | FAIL | PENDING | BLOCKED | SKIPPED | Tỉ lệ pass (trên số đã chạy) |
|---:|---:|---:|---:|---:|---:|---:|
| 25 | 25 | 0 | 0 | 0 | 0 | 100.0% |

**Coverage (dòng lệnh) của các module được nhắm:** tổng 56.9%

| File | Số lệnh | Lệnh chưa chạy | Coverage |
|---|---:|---:|---:|
| `app/routers/translation.py` | 114 | 71 | 37.7% |
| `app/services/word_analysis_service.py` | 176 | 54 | 69.3% |
