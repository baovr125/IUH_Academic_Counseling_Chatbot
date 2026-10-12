# Unit Test — Nạp từ điển, cache, định tuyến /text (bổ sung đợt này) (Phase 4.4)

## A. Thông tin chạy test

| Mục | Nội dung |
|---|---|
| Thời gian | 2026-10-10 16:51:23 → 16:51:34 (+0700) |
| Mã nguồn | Git HEAD `7e846214` + thay đổi chưa commit; vân tay `app/**/*.py` = `5ac072ebfd20` |
| Python / runner | Python 3.11.8, pytest 8.4.2, pytest-asyncio 1.4.0 (`asyncio_mode=auto`), coverage 7.15.4 (pytest-cov) |
| Lệnh chạy chính xác | `cd services/realtime_translation_service && python -m pytest tests/unit/test_domain_support_units.py tests/unit/test_redis_cache.py -p no:cacheprovider -o addopts= -q -rA --junitxml=<report>/test_artifacts\unit_4_4_junit.xml --cov=app.services.domain_service --cov=app.services.domain_dict_service --cov=app.services.cache_service --cov=app.services.domain_index --cov=app.services.translation_service --cov-report=term --cov-report=json:<report>/test_artifacts\unit_4_4_coverage.json` |
| File test | `tests/unit/test_domain_support_units.py`, `tests/unit/test_redis_cache.py` |
| Cô lập dependency | Redis, Supabase (kể cả phân trang `.range()`), `collect_domain_translation`, `aresolve_source_language`, NLLB đều là `MagicMock`/`AsyncMock`. |
| Bằng chứng | JUnit XML `test_artifacts/unit_4_4_junit.xml`, log `test_artifacts/unit_4_4_pytest.log`, coverage `test_artifacts/unit_4_4_coverage.json` |
| Mã thoát pytest | 0 |

Ghi chú cột: *Expected Result* của từng test là các khẳng định (`assert`) viết trong test; *Actual Result* lấy từ JUnit XML.
*Precondition* chung của nhóm ghi ở hàng "Cô lập dependency".

## B. Bảng test case chi tiết

| Test Case ID | Module/Function | Test Case Description | Precondition | Test Data | Expected Result | Actual Result | Status | Failure Reason | Evidence/Log |
|---|---|---|---|---|---|---|---|---|---|
| UT-DC-001 | `test_domain_support_units.py::TestGetAllDictionaries::test_returns_redis_cache_without_touching_supabase` | returns redis cache without touching supabase | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (2668 ms) |
| UT-DC-002 | `test_domain_support_units.py::TestGetAllDictionaries::test_paginates_supabase_beyond_1000_rows_and_caches_result` | paginates supabase beyond 1000 rows and caches result | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (10 ms) |
| UT-DC-003 | `test_domain_support_units.py::TestGetAllDictionaries::test_supabase_error_returns_empty_list` | supabase error returns empty list | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (5 ms) |
| UT-DC-004 | `test_domain_support_units.py::TestGetAllDictionaries::test_no_supabase_and_no_redis_returns_empty_list` | no supabase and no redis returns empty list | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (3 ms) |
| UT-DC-005 | `test_domain_support_units.py::TestGetIndex::test_reuses_index_while_dictionary_version_is_unchanged` | reuses index while dictionary version is unchanged | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (5 ms) |
| UT-DC-006 | `test_domain_support_units.py::TestGetIndex::test_rebuilds_when_dictionary_version_changes` | rebuilds when dictionary version changes | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (5 ms) |
| UT-DC-007 | `test_domain_support_units.py::TestGetIndex::test_keeps_previous_index_when_fetch_temporarily_returns_nothing` | keeps previous index when fetch temporarily returns nothing | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (5 ms) |
| UT-DC-008 | `test_domain_support_units.py::TestGetIndex::test_empty_dictionary_gives_empty_index` | empty dictionary gives empty index | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (4 ms) |
| UT-DC-009 | `test_domain_support_units.py::TestVariants::test_last_word_inflections_are_reduced` | last word inflections are reduced | Mock/isolation theo mục A | queries-query | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-010 | `test_domain_support_units.py::TestVariants::test_last_word_inflections_are_reduced` | last word inflections are reduced | Mock/isolation theo mục A | caches-cache | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-011 | `test_domain_support_units.py::TestVariants::test_last_word_inflections_are_reduced` | last word inflections are reduced | Mock/isolation theo mục A | boxes-box | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-012 | `test_domain_support_units.py::TestVariants::test_last_word_inflections_are_reduced` | last word inflections are reduced | Mock/isolation theo mục A | leaks-leak | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-013 | `test_domain_support_units.py::TestVariants::test_last_word_inflections_are_reduced` | last word inflections are reduced | Mock/isolation theo mục A | deployed-deploy | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-014 | `test_domain_support_units.py::TestVariants::test_last_word_inflections_are_reduced` | last word inflections are reduced | Mock/isolation theo mục A | cached-cache | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-015 | `test_domain_support_units.py::TestVariants::test_last_word_inflections_are_reduced` | last word inflections are reduced | Mock/isolation theo mục A | caching-cache | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-016 | `test_domain_support_units.py::TestVariants::test_last_word_inflections_are_reduced` | last word inflections are reduced | Mock/isolation theo mục A | tokenizing-tokenize | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-017 | `test_domain_support_units.py::TestVariants::test_last_word_inflections_are_reduced` | last word inflections are reduced | Mock/isolation theo mục A | memory leaks-memory leak | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-018 | `test_domain_support_units.py::TestVariants::test_short_words_are_not_stripped` | short words are not stripped | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (0 ms) |
| UT-DC-019 | `test_domain_support_units.py::TestVariants::test_original_phrase_is_always_first` | original phrase is always first | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (0 ms) |
| UT-DC-020 | `test_domain_support_units.py::TestSyncDictionaryToRedis::test_writes_one_hash_per_domain_and_clears_versioned_cache_keys` | writes one hash per domain and clears versioned cache keys | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (5 ms) |
| UT-DC-021 | `test_domain_support_units.py::TestSyncDictionaryToRedis::test_does_nothing_without_supabase` | does nothing without supabase | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-022 | `test_domain_support_units.py::TestDomainResultCache::test_round_trip_keeps_unicode_and_structure` | round trip keeps unicode and structure | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (2 ms) |
| UT-DC-023 | `test_domain_support_units.py::TestDomainResultCache::test_missing_key_or_no_redis_returns_none` | missing key or no redis returns none | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (2 ms) |
| UT-DC-024 | `test_domain_support_units.py::TestDomainResultCache::test_redis_errors_are_swallowed` | redis errors are swallowed | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (3 ms) |
| UT-DC-025 | `test_domain_support_units.py::TestDomainResultCache::test_corrupted_json_returns_none` | corrupted json returns none | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-026 | `test_domain_support_units.py::TestDomainResultCache::test_domain_version_rules` | domain version rules | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (2 ms) |
| UT-DC-027 | `test_domain_support_units.py::TestDomainResultCache::test_translation_hash_is_case_sensitive_and_nfc_normalized` | translation hash is case sensitive and nfc normalized | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-028 | `test_domain_support_units.py::TestTranslateDomainText::test_legacy_warning_prefers_non_info_and_is_none_without_warnings` | legacy warning prefers non info and is none without warnings | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (7 ms) |
| UT-DC-029 | `test_domain_support_units.py::TestTranslateDomainText::test_error_becomes_http_503` | error becomes http 503 | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (3 ms) |
| UT-DC-030 | `test_domain_support_units.py::TestTranslateDomainText::test_translate_text_routes_domain_mode_away_from_nllb` | translate text routes domain mode away from nllb | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (3 ms) |
| UT-DC-031 | `test_domain_support_units.py::TestTranslateDomainText::test_default_label_stays_in_normal_flow` | default label stays in normal flow | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (6 ms) |
| UT-DC-032 | `test_domain_support_units.py::TestStreamWrapper::test_internal_events_are_not_sent_to_client` | internal events are not sent to client | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (2 ms) |
| UT-DC-033 | `test_domain_support_units.py::TestStreamWrapper::test_vietnamese_is_not_ascii_escaped_in_sse_payload` | vietnamese is not ascii escaped in sse payload | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-034 | `test_redis_cache.py::TestRedisCacheService::test_get_cached_translation_hit` | get cached translation hit | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (2 ms) |
| UT-DC-035 | `test_redis_cache.py::TestRedisCacheService::test_get_cached_translation_miss` | get cached translation miss | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |
| UT-DC-036 | `test_redis_cache.py::TestRedisCacheService::test_set_cached_translation_with_ttl` | set cached translation with ttl | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (2 ms) |
| UT-DC-037 | `test_redis_cache.py::TestRedisCacheService::test_get_and_set_cached_audio_url` | get and set cached audio url | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (2 ms) |
| UT-DC-038 | `test_redis_cache.py::TestRedisCacheService::test_redis_unavailable_handles_gracefully` | redis unavailable handles gracefully | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_4_junit.xml` (1 ms) |

## C. Tổng kết

| Tổng | PASS | FAIL | PENDING | BLOCKED | SKIPPED | Tỉ lệ pass (trên số đã chạy) |
|---:|---:|---:|---:|---:|---:|---:|
| 38 | 38 | 0 | 0 | 0 | 0 | 100.0% |

**Coverage (dòng lệnh) của các module được nhắm:** tổng 61.5%

| File | Số lệnh | Lệnh chưa chạy | Coverage |
|---|---:|---:|---:|
| `app/services/cache_service.py` | 140 | 66 | 52.9% |
| `app/services/domain_dict_service.py` | 40 | 6 | 85.0% |
| `app/services/domain_index.py` | 134 | 25 | 81.3% |
| `app/services/domain_service.py` | 47 | 7 | 85.1% |
| `app/services/translation_service.py` | 135 | 87 | 35.6% |
