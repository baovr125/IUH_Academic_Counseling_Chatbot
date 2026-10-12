# Unit Test — Domain Detection (parser, quyết định, chỉ mục từ điển, prompt) (Phase 4.2)

## A. Thông tin chạy test

| Mục | Nội dung |
|---|---|
| Thời gian | 2026-10-10 16:50:58 → 16:51:10 (+0700) |
| Mã nguồn | Git HEAD `7e846214` + thay đổi chưa commit; vân tay `app/**/*.py` = `5ac072ebfd20` |
| Python / runner | Python 3.11.8, pytest 8.4.2, pytest-asyncio 1.4.0 (`asyncio_mode=auto`), coverage 7.15.4 (pytest-cov) |
| Lệnh chạy chính xác | `cd services/realtime_translation_service && python -m pytest tests/unit/test_domain_detection.py -p no:cacheprovider -o addopts= -q -rA --junitxml=<report>/test_artifacts\unit_4_2_junit.xml --cov=app.services.domain_detection --cov=app.services.domain_index --cov-report=term --cov-report=json:<report>/test_artifacts\unit_4_2_coverage.json` |
| File test | `tests/unit/test_domain_detection.py` |
| Cô lập dependency | Hàm thuần, dữ liệu từ điển giả trong test; không I/O. |
| Bằng chứng | JUnit XML `test_artifacts/unit_4_2_junit.xml`, log `test_artifacts/unit_4_2_pytest.log`, coverage `test_artifacts/unit_4_2_coverage.json` |
| Mã thoát pytest | 0 |

Ghi chú cột: *Expected Result* của từng test là các khẳng định (`assert`) viết trong test; *Actual Result* lấy từ JUnit XML.
*Precondition* chung của nhóm ghi ở hàng "Cô lập dependency".

## B. Bảng test case chi tiết

| Test Case ID | Module/Function | Test Case Description | Precondition | Test Data | Expected Result | Actual Result | Status | Failure Reason | Evidence/Log |
|---|---|---|---|---|---|---|---|---|---|
| UT-DD-001 | `test_domain_detection.py::TestJointStreamParser::test_header_then_body` | header then body | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (2654 ms) |
| UT-DD-002 | `test_domain_detection.py::TestJointStreamParser::test_header_split_across_tiny_chunks` | header split across tiny chunks | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-003 | `test_domain_detection.py::TestJointStreamParser::test_missing_header_is_format_error_and_keeps_translation` | missing header is format error and keeps translation | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (0 ms) |
| UT-DD-004 | `test_domain_detection.py::TestJointStreamParser::test_missing_separator_still_yields_translation` | missing separator still yields translation | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-005 | `test_domain_detection.py::TestJointStreamParser::test_markdown_fence_before_header_is_skipped` | markdown fence before header is skipped | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (0 ms) |
| UT-DD-006 | `test_domain_detection.py::TestJointStreamParser::test_header_without_trailing_newline_at_end_of_stream` | header without trailing newline at end of stream | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (0 ms) |
| UT-DD-007 | `test_domain_detection.py::TestJointStreamParser::test_abnormal_confidence_becomes_none` | abnormal confidence becomes none | Mock/isolation theo mục A | abc | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-008 | `test_domain_detection.py::TestJointStreamParser::test_abnormal_confidence_becomes_none` | abnormal confidence becomes none | Mock/isolation theo mục A | nan | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-009 | `test_domain_detection.py::TestJointStreamParser::test_abnormal_confidence_becomes_none` | abnormal confidence becomes none | Mock/isolation theo mục A | inf | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-010 | `test_domain_detection.py::TestJointStreamParser::test_abnormal_confidence_becomes_none` | abnormal confidence becomes none | Mock/isolation theo mục A | 1.5 | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-011 | `test_domain_detection.py::TestJointStreamParser::test_abnormal_confidence_becomes_none` | abnormal confidence becomes none | Mock/isolation theo mục A | -0.2 | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-012 | `test_domain_detection.py::TestJointStreamParser::test_abnormal_confidence_becomes_none` | abnormal confidence becomes none | Mock/isolation theo mục A | 1e9 | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-013 | `test_domain_detection.py::TestJointStreamParser::test_repeated_separator_line_is_swallowed` | repeated separator line is swallowed | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-014 | `test_domain_detection.py::TestJointStreamParser::test_separator_only_translation_is_empty` | separator only translation is empty | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-015 | `test_domain_detection.py::TestJointStreamParser::test_translation_starting_with_dashes_is_not_swallowed_as_separator` | translation starting with dashes is not swallowed as separator | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-016 | `test_domain_detection.py::TestDecideDomain::test_accepts_confident_domain` | accepts confident domain | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (2 ms) |
| UT-DD-017 | `test_domain_detection.py::TestDecideDomain::test_accepts_domain_without_lexical_evidence` | accepts domain without lexical evidence | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-018 | `test_domain_detection.py::TestDecideDomain::test_name_match_is_case_and_space_insensitive` | name match is case and space insensitive | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-019 | `test_domain_detection.py::TestDecideDomain::test_unknown_from_llm` | unknown from llm | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-020 | `test_domain_detection.py::TestDecideDomain::test_domain_outside_list_is_rejected` | domain outside list is rejected | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-021 | `test_domain_detection.py::TestDecideDomain::test_no_header_is_format_error` | no header is format error | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-022 | `test_domain_detection.py::TestDecideDomain::test_missing_or_invalid_confidence_is_not_trusted` | missing or invalid confidence is not trusted | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-023 | `test_domain_detection.py::TestDecideDomain::test_low_confidence_abstains` | low confidence abstains | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-024 | `test_domain_detection.py::TestDecideDomain::test_threshold_env_garbage_falls_back_to_default` | threshold env garbage falls back to default | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-025 | `test_domain_detection.py::TestDecideDomain::test_strong_conflicting_lexical_evidence_abstains` | strong conflicting lexical evidence abstains | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-026 | `test_domain_detection.py::TestDecideDomain::test_single_conflicting_term_is_not_enough_to_override` | single conflicting term is not enough to override | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-027 | `test_domain_detection.py::TestDomainIndex::test_build_stats` | build stats | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-028 | `test_domain_detection.py::TestDomainIndex::test_build_skips_incomplete_and_duplicate_rows` | build skips incomplete and duplicate rows | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-029 | `test_domain_detection.py::TestDomainIndex::test_exact_normalisation` | exact normalisation | Mock/isolation theo mục A | memory leak | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-030 | `test_domain_detection.py::TestDomainIndex::test_exact_normalisation` | exact normalisation | Mock/isolation theo mục A | MEMORY LEAK | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-031 | `test_domain_detection.py::TestDomainIndex::test_exact_normalisation` | exact normalisation | Mock/isolation theo mục A | the memory leak | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-032 | `test_domain_detection.py::TestDomainIndex::test_exact_normalisation` | exact normalisation | Mock/isolation theo mục A | a memory leak! | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-033 | `test_domain_detection.py::TestDomainIndex::test_exact_normalisation` | exact normalisation | Mock/isolation theo mục A | memory leaks | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-034 | `test_domain_detection.py::TestDomainIndex::test_exact_handles_inflection_of_last_word` | exact handles inflection of last word | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-035 | `test_domain_detection.py::TestDomainIndex::test_exact_returns_every_domain_for_shared_term` | exact returns every domain for shared term | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-036 | `test_domain_detection.py::TestDomainIndex::test_exact_does_not_match_partial_phrase` | exact does not match partial phrase | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-037 | `test_domain_detection.py::TestDomainIndex::test_scan_prefers_longest_term_and_does_not_double_count` | scan prefers longest term and does not double count | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-038 | `test_domain_detection.py::TestDomainIndex::test_scan_matches_plural_and_reports_spans` | scan matches plural and reports spans | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-039 | `test_domain_detection.py::TestDomainIndex::test_scan_can_restrict_domains` | scan can restrict domains | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-040 | `test_domain_detection.py::TestDomainIndex::test_lexical_score_prefers_more_and_longer_terms` | lexical score prefers more and longer terms | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-041 | `test_domain_detection.py::TestPrompts::test_auto_prompt_lists_domains_glossary_and_protocol` | auto prompt lists domains glossary and protocol | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |
| UT-DD-042 | `test_domain_detection.py::TestPrompts::test_manual_prompt_without_glossary_has_no_glossary_block` | manual prompt without glossary has no glossary block | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (0 ms) |
| UT-DD-043 | `test_domain_detection.py::TestPrompts::test_manual_prompt_uses_language_names` | manual prompt uses language names | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (0 ms) |
| UT-DD-044 | `test_domain_detection.py::TestPrompts::test_confidence_helper_rejects_non_finite` | confidence helper rejects non finite | Mock/isolation theo mục A | — | Các assert trong test đều đúng | Đúng kỳ vọng (mọi assert đạt) | PASS | — | `test_artifacts/unit_4_2_junit.xml` (1 ms) |

## C. Tổng kết

| Tổng | PASS | FAIL | PENDING | BLOCKED | SKIPPED | Tỉ lệ pass (trên số đã chạy) |
|---:|---:|---:|---:|---:|---:|---:|
| 44 | 44 | 0 | 0 | 0 | 0 | 100.0% |

**Coverage (dòng lệnh) của các module được nhắm:** tổng 89.0%

| File | Số lệnh | Lệnh chưa chạy | Coverage |
|---|---:|---:|---:|
| `app/services/domain_detection.py` | 203 | 11 | 94.6% |
| `app/services/domain_index.py` | 134 | 26 | 80.6% |
