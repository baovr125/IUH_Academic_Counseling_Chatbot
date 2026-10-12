# Kế hoạch Unit Test — Realtime Translation Service

> Trạng thái: **KẾ HOẠCH** (lập 2026-10-10, Phase 3). Cột *Status* là trạng thái kế hoạch; kết quả thực tế nằm trong `unit_test_*_report.md`.

## 1. Rà soát test hiện có

- `tests/unit`: **271 test có sẵn** trong 12 file, tất cả chạy được không cần mạng (đã chạy thử: 271 passed, 12,45 s). Coverage dòng lệnh toàn `app/` khi chỉ chạy unit test: **63%** (`test_artifacts/coverage_baseline.json`).
- Module của tính năng chính có coverage cao: `language_detection` 93%, `domain_detection` 95%, `domain_translation` 95%, `domain_llm` 93%, `domain_index` 81%.
- **Khoảng trống có ý nghĩa** (logic thuộc tính năng nhưng chưa có test): nạp từ điển từ Redis/Supabase + phân trang (`domain_service.get_all_dictionaries` 21%), đồng bộ Redis (`domain_dict_service` 15%), cache kết quả domain và version (`cache_service` 34%), định tuyến `/text` sang luồng chuyên ngành và chọn trường `warning` cũ (`translation_service` 16%), chỉ mục theo version (`domain_index.get_index`), biến thể từ của tra cứu chính xác (`_variants`), bộ lọc sự kiện nội bộ của wrapper SSE.
- **Đã bổ sung 33 test** trong file mới `tests/unit/test_domain_support_units.py` cho các khoảng trống trên (không sửa code sản phẩm). Không viết test cho phần ngoài phạm vi tính năng (MinIO, RabbitMQ, admin router, TTS edge) chỉ để tăng coverage.
- Không thuộc unit test (không chạy): `tests/integration/*` (TestClient qua nhiều lớp, 42 test), `tests/e2e/*` (trình duyệt).

## 2. Nhóm và thứ tự chạy

| Phase | Nhóm | File test | Số test |
|---|---|---|---:|
| 4.1 | Language Detection | `test_language_detection.py`, `test_detection_status.py` | 129 |
| 4.2 | Domain Detection (parser, quyết định, chỉ mục, prompt) | `test_domain_detection.py` | 44 |
| 4.3 | LLM streaming, fallback, điều phối | `test_domain_translation.py`, `test_terminology_backend.py` | 61 |
| 4.4 | Nạp từ điển, cache, định tuyến (mới + cache cũ) | `test_domain_support_units.py`, `test_redis_cache.py` | 38 |
| 4.5 | TTS & phân tích từ | `test_voice_resolver.py`, `test_cas_deduplication.py`, `test_word_analysis.py` | 25 |
| 4.6 | Công cụ đo | `test_detection_metrics_phase2.py`, `test_benchmark_contract.py` | 7 |
| | **Tổng** | | **304** |

## 3. Bảng test case (theo nhóm chức năng)

Mỗi dòng là một nhóm test case có cùng mục tiêu; ID chi tiết từng test (ví dụ `UT-LF-012`) được sinh trong report thực thi từ JUnit XML.

| Test Case ID | Module/Function | Test Case Description | Precondition | Test Data | Expected Result | Test Type | Priority | Status |
|---|---|---|---|---|---|---|---|---|
| UT-LD-A | `language_detection.detect_language_detailed` (85 test, `test_language_detection.py`) | Nhận diện đúng 10 ngôn ngữ hỗ trợ; trả `uncertain`/`unsupported`/`unknown`/`invalid_input` đúng trường hợp; HTML/URL; tiếng Việt không dấu; câu CJK không dấu cách; regression (regex bậc hai, chuỗi rất dài) | fastText + Lingua cục bộ | Câu mẫu trong test, `tests/fixtures/language_detection_cases.jsonl` | status/ngôn ngữ/lý do đúng như khẳng định | Valid, invalid, boundary, regression | Cao | PLANNED |
| UT-LD-B | `TestFusionDecisions`, `TestScriptShortcuts`, `TestScriptProfile`, `TestCleaning`, `TestPolicyAndCompat`, `TestPackagedResources`, `TestUpperCaseAndMixedSelection` (44 test) | Quyết định fusion có hiệu chỉnh; luật hệ chữ (Hangul/Kana/Thái/Hán); làm sạch đầu vào; chính sách dừng & tương thích `detect_source_language`; tài nguyên đóng gói; câu viết hoa/trộn | Như trên, engine lỗi được mock | Đầu vào tổng hợp | Như khẳng định | Branch, exception, compat | Cao | PLANNED |
| UT-DD-A | `JointStreamParser` (15) | Tách header `DOMAIN:…\|CONF:…`, `---`, bản dịch; chunk nhỏ lẻ; thiếu header ⇒ `format_error` nhưng giữ bản dịch; confidence bất thường (`abc`, `nan`, `inf`, `1.5`, `-0.2`, `1e9`) ⇒ None; rào markdown; lặp `---`; bản dịch bắt đầu bằng `-` | Không | Chuỗi stream giả | Sự kiện đúng thứ tự, không mất chữ | Valid, malformed, boundary, regression | Cao | PLANNED |
| UT-DD-B | `decide_domain` (11) | Chấp nhận/abstain theo: `unknown`, tên ngoài danh sách, confidence thiếu/thấp, env ngưỡng hỏng, xung đột từ điển mạnh/yếu | Không | Header + bằng chứng lexical giả | `detected`/`unknown` với `reason` đúng | Branch | Cao | PLANNED |
| UT-DD-C | `DomainIndex` (14) + prompt (4) | Dựng chỉ mục, bỏ dòng hỏng/trùng; tra chính xác (hoa/thường, mạo từ, dấu câu, số nhiều); thuật ngữ dài thắng và không chồng lấn; giới hạn domain; điểm lexical; prompt có danh sách domain/glossary/ngôn ngữ | Không | Từ điển giả 10 mục | Như khẳng định | Valid, boundary | Cao | PLANNED |
| UT-LF-A | `domain_llm.stream_llm` (17) | Thành công qua Groq; model theo env; reasoning_effort; Groq lỗi ⇒ Gemini; quota ⇒ circuit breaker không gọi lại; 404 ⇒ `not_found`; không client; timeout token đầu ⇒ provider kế; timeout mọi nơi; đứt giữa chừng ⇒ `LLMInterrupted`; stream rỗng; phân loại lỗi (429/quota/404/401/timeout/khác) | Client Groq/Gemini giả | Async generator giả | Sự kiện/ngoại lệ/mã lỗi đúng | Valid, dependency error, timeout | Cao | PLANNED |
| UT-LF-B | `translate_with_domain` (44) | Đường ngắn (từ điển, `ambiguous`), domain thủ công (glossary đúng domain, biến thể), auto (domain trước bản dịch, unknown, confidence thấp/bất thường, lỗi định dạng, ngoài danh sách, HTML), lỗi (NLLB phao, NLLB cũng hỏng, đứt giữa chừng, rỗng), kiểm tra bản dịch hỏng (`reset`), cache, `collect` | `stream_llm`, NLLB, chỉ mục, cache giả | Như trên | Sự kiện SSE, cảnh báo đúng mã/câu, không cache khi lỗi | Branch, fallback, regression | Cao | PLANNED |
| UT-LF-C | `handle_flow_2_stream_translation`, `stream_translation` (8, `test_terminology_backend.py`) | Hợp đồng SSE mức wrapper; flow thường NLLB/Groq không bị ảnh hưởng | Client/NLLB giả | Câu mẫu | JSON event đúng | Contract, regression | Trung bình | PLANNED |
| UT-DC-A | `domain_service.get_all_dictionaries` (4, **mới**) | Trả cache Redis không gọi Supabase; phân trang > 1.000 hàng và ghi cache; Supabase lỗi ⇒ []; không Redis/Supabase ⇒ [] | Redis/Supabase giả | 1.001 hàng giả | Đủ 1.001 hàng; gọi `.range(0,999)`, `.range(1000,1999)` | Valid, dependency error, regression (cắt cụt 1.000 hàng) | Cao | PLANNED |
| UT-DC-B | `domain_index.get_index` (4, **mới**) | Dùng lại chỉ mục khi version không đổi; dựng lại khi đổi; giữ chỉ mục cũ khi tải lỗi tạm thời; từ điển rỗng | Version/tải giả | Hàng giả | Đúng số lần tải và số mục | Branch, robustness | Cao | PLANNED |
| UT-DC-C | `_variants` (11, **mới**) | -ies→-y, -es, -s, -ed, -ing (+e), cụm nhiều từ; từ ngắn không bị cắt | Không | Từ mẫu | Dạng gốc có trong danh sách | Boundary | Trung bình | PLANNED |
| UT-DC-D | `domain_dict_service.sync_dictionary_to_redis` (2, **mới**) | Ghi hash theo domain, chữ thường; xóa đúng key cache có version (`scan_iter`); không Supabase ⇒ không làm gì | Redis/Supabase giả | 2 hàng | `hset`, `delete` đúng key | Regression (lệch tên key) | Cao | PLANNED |
| UT-DC-E | `cache_service` (6 mới + 5 cũ) | Cache kết quả domain: khứ hồi Unicode, thiếu key, Redis lỗi, JSON hỏng; quy tắc version (`auto` dùng version toàn cục, nhãn mặc định = 0); hash phân biệt hoa/thường, chuẩn hóa NFC; cache bản dịch/audio cũ | Redis giả | Giá trị mẫu | Như khẳng định | Valid, exception, regression | Trung bình | PLANNED |
| UT-DC-F | `translation_service.translate_domain_text` / `translate_text` (4, **mới**) | Chọn trường `warning` cũ (ưu tiên mức không phải info, None khi không có cảnh báo); lỗi ⇒ HTTP 503; domain ⇒ luồng chuyên ngành, không chạm NLLB; nhãn mặc định ⇒ luồng thường | `collect_domain_translation`, nhận diện ngôn ngữ, NLLB, cache giả | Câu mẫu | Đúng nhánh, đúng tuple 8 phần tử | Branch, exception | Cao | PLANNED |
| UT-DC-G | Wrapper SSE (2, **mới**) | Sự kiện `_internal` không lộ ra client; tiếng Việt không bị escape ASCII | `translate_with_domain` giả | Sự kiện mẫu | JSON đúng | Contract | Trung bình | PLANNED |
| UT-TW-A | `resolve_voice`, hash CAS (21) | Chọn giọng TTS theo mã/locale và fallback; hash nội dung ổn định, phân biệt giọng/ngôn ngữ | Không | Mã ngôn ngữ | Giọng/hash đúng | Valid, boundary | Thấp | PLANNED |
| UT-TW-B | `/analyze_word` (4) | Phân tích từ (thành công, cache, danh từ/động từ) | NLP + Groq mock, TestClient trong tiến trình | Từ mẫu | Response đúng | Valid | Thấp | PLANNED |
| UT-EV-A | `evaluation/metrics`, `validate_dataset` (7) | Confusion matrix giữ mẫu bị từ chối; recall theo ngôn ngữ; ECE/Brier; đánh giá ngưỡng; dataset split không trùng, nhãn status đóng | Không | Dữ liệu nhỏ, dataset repo | Như khẳng định | Valid | Thấp | PLANNED |

## 4. Tiêu chí

- PASS/FAIL theo kết quả thật của pytest (JUnit XML). Test thất bại được ghi nhận trước, **không sửa code sản phẩm** khi chưa được duyệt.
- Coverage chỉ để tham khảo, không phải tiêu chí đạt.
