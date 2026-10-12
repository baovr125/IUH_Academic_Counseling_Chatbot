# Kế hoạch Benchmark — Realtime Translation Service

> Trạng thái: **KẾ HOẠCH** (lập 2026-10-10, Phase 1). Cột *Status* ở đây chỉ là trạng thái kế hoạch (`PLANNED`), chưa phải kết quả chạy.
> Kết quả thực tế nằm trong các file `benchmark_*_report.md`.

## 1. Nguyên tắc

- Gọi **đúng hàm production** (không viết lại logic): `detect_language_detailed` (`language_detection.py`), `DomainIndex`, `build_auto_system_prompt` + `JointStreamParser` + `decide_domain` + `domain_llm.stream_llm` (cùng chuỗi `translate_with_domain` dùng), `translate_with_domain`, `run_nllb_only`.
- Không qua HTTP/frontend (không E2E). Không chạy tải đồng thời.
- **Tiêu chí chấp nhận** lấy từ `evaluation.md` (mục 1.3 và 2.4, ghi "đề xuất" trong tài liệu đó). Hạng mục nào `evaluation.md` không có ngưỡng thì ghi **"Chưa có ngưỡng chính thức – chỉ báo cáo số đo"**; ngưỡng do tôi đề xuất được đánh dấu *(đề xuất, chờ duyệt)*.
- Không dùng dữ liệu đã dùng để chỉnh (lang_dev, domain_dev) làm bằng chứng đạt tiêu chí; dev chỉ dùng cho so sánh tương đối khi cần (TA-01) và được ghi rõ.
- Hạn mức Groq: tổng kế hoạch ≈ 390 lời gọi (còn 582 lúc bắt đầu). Giãn nhịp 5 s/lời gọi.

## 2. Nhóm benchmark được chọn và lý do

| Nhóm | Có trong service? | Chọn? | Lý do |
|---|---|---|---|
| Language detection (chất lượng, độ trễ) | Có | Có | Có dataset UTF-8 sạch (val) + nguồn công khai Tatoeba; chạy cục bộ |
| Domain detection (auto) | Có | Có | Có dev/val/hold-out; cần Groq thật |
| Độ chính xác thuật ngữ | Có (glossary trong prompt) | Có | Đo được bằng so khớp bản dịch từ điển, không cần bản dịch tham chiếu |
| Chất lượng dịch (chrF/BLEU) | Có | Có, giới hạn | Chỉ có 50 cặp tham chiếu chung (`ground_truth_dataset.json`), không phải câu chuyên ngành |
| Độ trễ / streaming | Có | Có | Đo token đầu & tổng thời gian ở mức hàm; NLLB cục bộ |
| Fallback khi LLM lỗi | Có | Có | Tiêm lỗi thật (model không tồn tại, timeout cực ngắn) |
| Tài nguyên (RAM) | — | Một phần | Chỉ đo bộ nhớ Python của chỉ mục từ điển (tracemalloc); RAM toàn service cần chạy server ⇒ không đo |
| Tải đồng thời | — | Không | Cần toàn hệ thống (Redis/Supabase/HTTP) — ngoài phạm vi |

## 3. Chi tiết từng benchmark

### Phase 2.1 — Language Detection (`benchmark_language_detection_report.md`)
- **Đối tượng:** `detect_language_detailed(text)` (đường production của `/text`, `/stream`, `/detect`).
- **Metric:** accuracy chặt (status `detected` và đúng nhãn / tổng), *sai-mà-tự-tin* (status `detected` nhưng sai nhãn / tổng), *false-accept ngoài phạm vi* (mẫu ngôn ngữ không hỗ trợ bị trả `detected` với một nhãn hỗ trợ / tổng mẫu ngoài phạm vi), tỉ lệ abstain (`uncertain`/`unknown`), accuracy theo ngôn ngữ.
- **Tiền xử lý Tatoeba:** tải `{lang}_sentences.tsv.bz2` theo ngôn ngữ; lấy ngẫu nhiên seed **20261010** (khác seed của giai đoạn 8); bỏ câu < 2 ký tự chữ; nhãn = ngôn ngữ của file. Ngôn ngữ hỗ trợ: en, vi, de, zh(cmn), ja, ko, fr, es, ru, th. Ngoài phạm vi: it, pt, nl, pl, tr, id, uk, ar, hi, sv.
- **Độ trễ:** gọi `detect_language_detailed` tuần tự sau warm-up; ghi p50/p95/p99 (ms), lặp 3 lượt trên cùng bộ để kiểm tra ổn định; tách lần gọi đầu (cold, trong tiến trình mới).

### Phase 2.2 — Domain Detection (`benchmark_domain_detection_report.md`)
- **Đối tượng:** chuỗi auto một lời gọi (prompt auto + `stream_llm` Groq `qwen/qwen3.8-27b` + `JointStreamParser` + `decide_domain`), qua `evaluation/run_domain_raw.py`, phân tích bằng `evaluation/analyze_domain_raw.py`.
- **Metric:** accuracy, macro-F1 (6 lĩnh vực), abstain đúng ngoài domain, sai-mà-tự-tin (đoán một lĩnh vực nhưng sai), ECE (confidence LLM, chỉ trên các lần chọn lĩnh vực; 10 bin), tỉ lệ vi phạm định dạng, tỉ lệ bản dịch hỏng (rỗng/`---`/sao chép), độ trễ token đầu p50/p95, độ nhất quán (lặp 5 lần).
- **Đường ngắn (cục bộ):** `DomainIndex.exact()` trên toàn bộ 246 thuật ngữ thật + biến thể (viết hoa, có mạo từ, số nhiều) + 50 cụm không có trong từ điển ⇒ hit-rate và false-hit.

### Phase 2.3 — Thuật ngữ & chất lượng dịch (`benchmark_translation_quality_report.md`)
- **TA-01:** 54 câu in-domain của bộ dev, cùng model, 3 chế độ: không domain (prompt dịch thường), domain thủ công đúng, `auto`. Metric: *term accuracy* = số thuật ngữ từ điển (thuộc lĩnh vực nhãn, có trong câu) mà bản dịch chứa bản dịch từ điển / tổng số thuật ngữ đó. Dùng bộ dev vì đây là so sánh tương đối giữa 3 chế độ, không phải đo ngưỡng chỉnh.
- **TQ-01:** 50 cặp `ground_truth_dataset.json` (EN→VI chung): chrF và BLEU (sacrebleu) của NLLB (chế độ thường).
- **TQ-02:** cùng 50 cặp qua chế độ `auto` (LLM) — chrF/BLEU để so sánh với NLLB.

### Phase 2.4 — Độ trễ & streaming (`benchmark_latency_streaming_report.md`)
- NLLB (chế độ thường) trên 50 câu `ground_truth`: thời gian dịch p50/p95 sau warm-up.
- LLM chế độ domain: token đầu & tổng thời gian (lấy từ các lượt chạy Phase 2.2/2.3, cùng điều kiện).
- `DomainIndex.scan`: thời gian quét với từ điển 246 mục và từ điển tổng hợp 1.000 / 10.000 mục (nhân bản có hậu tố), văn bản 888 ký tự; bộ nhớ Python của chỉ mục.

### Phase 2.5 — Fallback (`benchmark_fallback_report.md`)
- **FB-01:** `GROQ_DOMAIN_MODEL` = model không tồn tại, chỉ Groq ⇒ 404 thật ⇒ NLLB. 10 câu. Metric: tỉ lệ có bản dịch, danh sách cảnh báo đúng `[FALLBACK_NLLB]`, độ trễ lần đầu và các lần sau (circuit breaker).
- **FB-02:** timeout token đầu 0,1 s với Groq thật ⇒ NLLB. 5 câu.
- **FB-03:** không provider nào (không client) ⇒ NLLB. 5 câu (không gọi mạng).

## 4. Bảng test case benchmark

| Test Case ID | Hạng mục | Mục tiêu | Dataset/Test Data | Điều kiện chạy | Metric | Expected Result/Acceptance Criteria | Status |
|---|---|---|---|---|---|---|---|
| LD-01 | Language detection | Chất lượng trên bộ val tự viết | `lang_val.jsonl` (144) | Cục bộ, `dev_gate.py --split val` | accuracy, sai-mà-tự-tin, false-accept OOS | evaluation.md 1.3: accuracy ≥ 95%; sai-mà-tự-tin ≤ 1–2%; false-accept ≤ 10% | PLANNED |
| LD-02 | Language detection | Chất lượng trên nguồn công khai độc lập | Tatoeba, seed 20261010: 10 ngôn ngữ hỗ trợ × 150 + 10 ngôn ngữ ngoài phạm vi × 50 | Cục bộ | như LD-01 + theo ngôn ngữ | như LD-01; tiếng Việt ≥ 97% | PLANNED |
| LD-03 | Language detection | Tính xác định | 200 mẫu LD-02, chạy 3 lần | Cục bộ, cùng tiến trình | % mẫu cho kết quả giống hệt nhau | *(đề xuất, chờ duyệt)* 100% | PLANNED |
| LD-04 | Language detection | Độ trễ warm | 500 mẫu LD-02 | Sau warm-up, tuần tự, 3 lượt | p50/p95/p99 (ms) | evaluation.md 1.3: P95 ≤ 50 ms | PLANNED |
| LD-05 | Language detection | Độ trễ cold (lần gọi đầu trong tiến trình mới, chưa preload) | 1 câu | Tiến trình Python mới | ms | Chưa có ngưỡng chính thức – chỉ báo cáo | PLANNED |
| DD-01 | Domain detection | Chất lượng trên val | `domain_val.jsonl` (57) | Groq `qwen/qwen3.8-27b` | macro-F1, abstain OOD, sai-mà-tự-tin, ECE, định dạng, bản dịch hỏng | evaluation.md 2.4: macro-F1 ≥ 0,85; accuracy ≥ 90%; abstain ≥ 90%; sai-mà-tự-tin ≤ 5%; ECE ≤ 0,10 | PLANNED |
| DD-02 | Domain detection | Chất lượng trên hold-out độc lập | `domain_holdout.jsonl` (60, Wikipedia) | như DD-01 | như DD-01 | như DD-01 | PLANNED |
| DD-03 | Domain detection | Nhất quán khi lặp | 12 mẫu (2/lĩnh vực) + 6 OOD từ `domain_val`, lặp 5 lần | như DD-01 | % lời gọi trùng quyết định đa số | evaluation.md 2.4: ≥ 98% | PLANNED |
| DD-04 | Domain detection | Độ trễ phân loại | các lời gọi DD-01, DD-02 | như DD-01 | token đầu p95 (domain có ngay ở dòng đầu) | evaluation.md 2.4: ≤ ~1,5 s; timeout < 20 s | PLANNED |
| DD-05 | Domain detection (đường ngắn) | Tra từ điển chính xác | 246 thuật ngữ thật × 4 biến thể + 50 cụm không có | Cục bộ, `DomainIndex.exact` | hit-rate, false-hit | *(đề xuất, chờ duyệt)* hit-rate 100% với dạng gốc; false-hit 0 | PLANNED |
| TA-01 | Thuật ngữ | So 3 chế độ | `domain_dev.jsonl` 54 câu in-domain | Groq qwen, 3 chế độ | term accuracy | evaluation.md 2.4: auto ≥ không-domain; chênh so với thủ công ≤ 5 điểm | PLANNED |
| TQ-01 | Chất lượng dịch | NLLB chế độ thường | `ground_truth_dataset.json` (50) | NLLB GPU | chrF, BLEU | Chưa có ngưỡng chính thức – chỉ báo cáo | PLANNED |
| TQ-02 | Chất lượng dịch | LLM chế độ auto | như TQ-01 | Groq qwen | chrF, BLEU, Δ so với TQ-01 | Chưa có ngưỡng chính thức – chỉ báo cáo | PLANNED |
| LT-01 | Độ trễ | NLLB chế độ thường | 50 câu TQ-01 | GPU, sau warm-up | p50/p95 (ms) | Chưa có ngưỡng chính thức – chỉ báo cáo | PLANNED |
| LT-02 | Độ trễ | Quét thuật ngữ | 246 / 1.000 / 10.000 mục | Cục bộ | ms/lần quét, KiB | Chưa có ngưỡng chính thức – chỉ báo cáo | PLANNED |
| FB-01 | Fallback | Model không tồn tại (404 thật) | 10 câu `domain_val` | Groq model sai, không Gemini | % có bản dịch, cảnh báo, độ trễ | Theo thiết kế (`DOMAIN_DETECTION.md`): 100% có bản dịch NLLB; cảnh báo đúng `[FALLBACK_NLLB]`; lần sau bỏ qua Groq (circuit breaker) | PLANNED |
| FB-02 | Fallback | Timeout token đầu | 5 câu | Groq thật, timeout 0,1 s | như FB-01 | như FB-01 | PLANNED |
| FB-03 | Fallback | Không có provider | 5 câu | client = None (không mạng) | như FB-01 | như FB-01 | PLANNED |

## 5. Yếu tố ảnh hưởng độ tin cậy

- Độ trễ LLM phụ thuộc mạng và tải Groq tại thời điểm chạy; độ trễ cục bộ phụ thuộc máy (laptop, chạy song song với IDE).
- LLM không tất định (temperature 0,2): kết quả bản dịch thay đổi giữa các lần.
- Tatoeba có nhãn nhiễu (câu ngôn ngữ khác nằm trong file của một ngôn ngữ); câu ngắn, sạch, không đại diện nhập liệu thật.
- Nhãn domain hold-out lấy theo chủ đề bài Wikipedia (có thể nhiễu ở bài giáp ranh); bộ domain nhỏ.
- `ground_truth_dataset.json` có 50 câu chung (không chuyên ngành), một bản tham chiếu/câu ⇒ chrF/BLEU chỉ mang tính so sánh tương đối.
