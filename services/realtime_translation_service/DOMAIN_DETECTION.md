# Domain Detection và dịch theo chuyên ngành (realtime_translation_service)

Tài liệu này mô tả chế độ **chuyên ngành** của service: người dùng chọn một lĩnh vực cụ thể hoặc chọn
"✨ Tự động nhận diện" (`domain=auto`). Ở chế độ này **bản dịch do LLM thực hiện**, không dùng NLLB
(NLLB chỉ còn là phao cứu sinh cuối khi mọi LLM đều hỏng). Chế độ "Dịch thông thường" vẫn dùng NLLB như cũ.
Language Detection là phần riêng, xem `LANGUAGE_DETECTION.md`; nhận diện ngôn ngữ luôn chạy trước.

## 1. Luồng xử lý

```
language detection (chỉ `detected` mới đi tiếp)
  └─ domain mode (domain ≠ "" và ≠ "Dịch thông thường (Mặc định)")
       1. Cache Redis (domtrans:*)  ── hit → phát lại domain + bản dịch + cảnh báo
       2. Từ/cụm ngắn khớp CHÍNH XÁC từ điển (EN→VI, ≤ số từ của thuật ngữ dài nhất, hiện 4)
            auto  : 1 domain  → dùng bản dịch từ điển, không gọi LLM
                    ≥2 domain → status=ambiguous + candidates (UI cho chọn), không dịch
            manual: có trong domain đã chọn → bản dịch từ điển; chỉ có ở domain khác → LLM + TERM_IN_OTHER_DOMAIN
       3. Quét thuật ngữ từ điển trong câu (EN→VI) → glossary đưa vào prompt (thuật ngữ dài nhất thắng, không chồng lấn)
       4. MỘT lời gọi LLM stream (Groq → Gemini, có circuit breaker)
            manual: bản dịch theo domain đã chọn
            auto  : dòng 1 `DOMAIN: <tên|unknown> | CONF: <0..1>`, dòng 2 `---`, rồi bản dịch
                    → `decide_domain` kết hợp lời khai LLM với bằng chứng lexical
       5. Kiểm tra bản dịch hỏng (rỗng / `---` / sao chép nguyên văn) → `reset` + NLLB
       6. LLM không dùng được → NLLB + FALLBACK_NLLB
```

Mã: `app/services/domain_translation.py` (điều phối, dùng chung `/text` và `/stream`),
`domain_detection.py` (prompt, parser giao thức, `decide_domain`), `domain_index.py` (chỉ mục từ điển),
`domain_llm.py` (Groq/Gemini streaming, timeout, circuit breaker).

Thay đổi ngưỡng văn bản ngắn: bỏ điều kiện "dưới 25 ký tự". Từ điển chứa thuật ngữ chứ không chứa câu nên
chỉ số **từ** mới phù hợp (dữ liệu thật: 246 mục, 1 từ: 16 · 2 từ: 183 · 3 từ: 40 · 4 từ: 7; 12 thuật ngữ dài ≥ 25 ký tự
sẽ bị sót nếu chỉ xét ký tự). Giới hạn trên của đường tra từ điển lấy từ chính từ điển (`DomainIndex.max_words`).

## 2. Hợp đồng SSE của `/stream`

Thứ tự: `detection` → `resolved_source_lang` → (chế độ domain) `domain` → `text`… → `warnings`.

| Event | Nội dung |
|---|---|
| `{"event":"domain","domain":{…}}` | `DomainDetails`: `status` (`selected`/`detected`/`ambiguous`/`unknown`/`skipped`), `domain`, `confidence`, `method` (`manual`/`exact`/`llm`/`lexical_llm`/`none`), `matched_terms`, `applied_terms`, `candidates`, `reason`, `translator` (`dictionary`/`llm:<provider>:<model>`/`nllb`). Có thể phát 2 lần: sớm (khi có header) và bản cuối kèm `applied_terms`. |
| `{"text":"…"}` | Đoạn bản dịch. |
| `{"warnings":[…]}` | Cảnh báo có cấu trúc `{code, severity, message, domain?, candidates?}` (xem bảng dưới). Client gộp theo `code`. |
| `{"event":"reset"}` | Xóa phần bản dịch đã stream (bản dịch LLM hỏng, ngay sau đó là bản NLLB). |
| `{"error":"…","code":"TRANSLATION_UNAVAILABLE"}` | Không dịch được bằng bất kỳ đường nào. |

`/text` trả cùng thông tin trong `data.domain` và `data.warnings`; trường chuỗi `data.warning` vẫn có
(cảnh báo mức cao nhất) để tương thích ngược.

### Thông báo hiển thị cho người dùng

Chế độ `auto` hoạt động giống nhận diện ngôn ngữ: kết quả chỉ hiện thành **nhãn trong ô chọn lĩnh vực**
("✨ Tự động nhận diện (Marketing)", hoặc không có tên lĩnh vực khi không xác định), không phát cảnh báo.
Lý do không xác định (`llm_unknown`, `low_confidence`, `format_error`…) nằm ở `domain.reason`; lý do lỗi kỹ thuật
(quota, timeout…) chỉ ghi log backend. Chỉ còn các mã sau (mỗi lượt dịch nhiều nhất một banner, vì loại trừ nhau):

| Mã | Mức | Nội dung | Khi nào | Người dùng cần làm gì |
|---|---|---|---|---|
| `DOMAIN_AMBIGUOUS` | warning | Từ này có nghĩa ở nhiều lĩnh vực. Hãy chọn một lĩnh vực. | `auto`, từ ngắn khớp từ điển của ≥ 2 lĩnh vực. UI hiện khung chọn trong vùng bản dịch (không phải banner) | Chọn lĩnh vực |
| `FALLBACK_NLLB` | warning | Chế độ chuyên ngành tạm gián đoạn, đã dịch thông thường. | LLM không dùng được (mọi lý do), NLLB thay thế | Không |
| `TRANSLATION_INTERRUPTED` | warning | Bản dịch bị ngắt giữa chừng, có thể chưa đầy đủ. Nhấn Ctrl+Enter để dịch lại. | Stream LLM đứt sau khi đã có chữ | Dịch lại |
| `TRANSLATION_UNAVAILABLE` (event `error`) | error | Không thể dịch lúc này. Vui lòng thử lại sau. | LLM và NLLB đều hỏng | Thử lại sau |

Đã bỏ (giai đoạn 9b): `DOMAIN_UNKNOWN`, `DOMAIN_FORMAT_ERROR` (thay bằng nhãn), `DOMAIN_SERVICE_ERROR` (hợp nhất vào
`FALLBACK_NLLB`), `GLOSSARY_UNAVAILABLE`, `GLOSSARY_NO_MATCH`, `TERM_NOT_IN_DICT`, `TERM_IN_OTHER_DOMAIN` (không ảnh hưởng
bản dịch nên không báo). Logic từ điển/glossary không đổi. Cache key nâng lên `domain_v4_` để kết quả cache cũ không phát
lại các cảnh báo đã bỏ. Câu chữ nằm ở các hằng `MSG_*` trong `app/services/domain_translation.py`.

## 3. Quyết định domain (`decide_domain`)

Confidence do LLM tự khai bão hòa (đã đo: 0,95–1,0 cả khi sai) nên không dùng một mình:

1. Không có header hợp lệ → `unknown` (`format_error`). `unknown` của LLM → `unknown`.
2. Tên domain không khớp danh sách (so không phân biệt hoa/thường, khoảng trắng) → `unknown` (`llm_out_of_list`).
3. Confidence thiếu / NaN / ngoài [0,1] / không phải số → `unknown` (`invalid_confidence`).
4. Confidence < `AUTO_DOMAIN_MIN_CONFIDENCE` (mặc định 0,75) → `unknown` (`low_confidence`).
5. Từ điển cho domain **khác** có bằng chứng mạnh hơn hẳn (điểm ≥ điểm domain LLM chọn + 2, tức ≥ 2 thuật ngữ
   hai từ) → `unknown` (`llm_lexical_conflict`).
6. Còn lại → `detected` (`lexical_llm` nếu từ điển cũng ủng hộ, ngược lại `llm`).

Các ngưỡng 0,75 và +2 là **giá trị mặc định, chưa được chỉnh bằng dữ liệu**: tập dev bão hòa (xem mục 6) nên không
phân biệt được các giá trị ngưỡng.

## 4. Cấu hình (biến môi trường)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `GROQ_DOMAIN_MODEL` | `qwen/qwen3.8-27b` | Model Groq cho chế độ chuyên ngành (chọn bằng bộ dev, xem mục 6). Phải nằm trong danh sách key được cấp quyền. |
| `GEMINI_DOMAIN_MODEL` | `gemini-2.5-flash` | Dự phòng. |
| `DOMAIN_LLM_PROVIDERS` | `groq,gemini` | Thứ tự provider. |
| `DOMAIN_LLM_FIRST_TOKEN_TIMEOUT_SECONDS` | `10` | Quá hạn → provider kế tiếp. |
| `DOMAIN_LLM_TOTAL_TIMEOUT_SECONDS` | `40` | Tổng thời gian một stream. |
| `AUTO_DOMAIN_MIN_CONFIDENCE` | `0.75` | Xem mục 3. |
| `GROQ_DOMAIN_REASONING_EFFORT` | `low` (gpt-oss) / `none` (qwen) | Giảm suy luận để token đầu đến nhanh. |

Chỉ chế độ chuyên ngành đọc các biến này. Các chỗ gọi `llama-3.1-8b-instant` ngoài phạm vi domain
(`llm_service.py` flow thường, `extract_flashcard`, `translation_service.py` fallback) **chưa đổi**; xem mục 7.

Circuit breaker: lỗi quota nghỉ 60 s (hoặc `Retry-After`, tối đa 300 s), timeout 10 s, lỗi chung 15 s, model không
tồn tại/sai khóa 600 s; trong lúc nghỉ provider bị bỏ qua để không gọi lại từng request.

## 5. Phía frontend

- Chế độ domain (auto hoặc thủ công) chỉ gửi request sau khi người dùng **ngừng gõ 1,5 s** (`DOMAIN_DEBOUNCE_MS`);
  dịch thông thường giữ 300 ms. Chỉ báo "Sẽ dịch sau 1,5 giây ngừng gõ (Ctrl+Enter để dịch ngay)." và phím
  **Ctrl/Cmd+Enter** để dịch ngay.
- `DomainSelector` nhận `detectedDomain` và hiện "✨ Tự động nhận diện ({lĩnh vực})". `TranslationBox` giữ nhãn cũ cho tới
  khi có kết quả mới (không nhấp nháy khi gõ), bỏ tên khi kết quả là `unknown`, xóa khi đổi lĩnh vực hoặc xóa văn bản.
- `ambiguous`: khung chọn lĩnh vực trong vùng bản dịch (cùng kiểu khung dừng ngôn ngữ); chọn một lĩnh vực thì chuyển sang
  lĩnh vực đó và dịch ngay, không chờ debounce.
- `DomainStatus` chỉ còn chỉ báo chờ và banner cảnh báo (gộp theo `code`); event `reset` xóa phần bản dịch đã hiển thị.

## 6. Dữ liệu đánh giá và kết quả đo

Không dùng bộ test đóng băng của `evaluation.md` để chỉnh. Ba bộ riêng (`evaluation/dataset/`):

| Bộ | Vai trò | Nguồn |
|---|---|---|
| `domain_dev.jsonl` (86) | chọn model, chỉnh quy tắc | tự viết (`build_domain_dev_set.py`) |
| `domain_val.jsonl` (57) | kiểm tra lại, không chỉnh theo | tự viết, tách biệt với dev |
| `domain_holdout.jsonl` (60) | chạy một lần cuối, không chỉnh theo | phần mở đầu bài Wikipedia tiếng Anh (độc lập hoàn toàn; nhãn theo chủ đề bài, có thể nhiễu ở bài giáp ranh) |

Quy trình: `evaluation/run_domain_raw.py` gọi LLM thật và lưu kết quả thô (`evaluation/results/domain_raw_*.jsonl`);
`evaluation/analyze_domain_raw.py` tính chỉ số **offline** từ file thô nên chỉnh quy tắc không tốn thêm quota.

### 6.1 Chọn model (chỉ trên bộ dev, 86 mẫu, giao thức một lời gọi, mỗi model 76 lượt gọi LLM)

| Model | Macro-F1 trong domain | Bản dịch hỏng* | Áp dụng thuật ngữ | Token đầu p50 / p95 |
|---|---|---|---|---|
| `openai/gpt-oss-20b` | 0,874 | **25/76** | 0,934 | 0,78 s / 1,05 s |
| `openai/gpt-oss-120b` | 1,000 | **5/76** | 0,974 | 0,82 s / 1,21 s |
| `qwen/qwen3.8-27b` | 1,000 | **0/76** | 0,987 | 0,45 s / 0,78 s |

\* Rỗng, chỉ có `---`, hoặc sao chép nguyên văn tiếng Anh. Toàn bộ trường hợp hỏng xảy ra khi model chọn `unknown`:
gpt-oss "bỏ qua" việc dịch ở nhánh này. Vì vậy mặc định là `qwen/qwen3.8-27b`, và bộ điều phối luôn kiểm tra bản dịch
(`is_untranslated`) rồi `reset` + NLLB nếu hỏng. Gemini 2.5 Flash chỉ được thử trên 14 lượt (định dạng đúng 14/14, domain
đúng 14/14) nhưng token đầu p50 ≈ 4,1 s và dính 429 sau khoảng 14 lượt gọi ở free tier, nên chỉ làm dự phòng.

### 6.2 Kết quả của model được chọn (`qwen/qwen3.8-27b`, quy tắc `decide_domain` mặc định)

| Chỉ số (tiêu chí định hướng trong `evaluation.md` 2.4) | dev (86) | val (57) | hold-out Wikipedia (60) |
|---|---|---|---|
| Accuracy / macro-F1 trong domain (≥ 0,85) | 1,000 / 1,000 (n=54) | 1,000 / 1,000 (n=36) | 1,000 / 1,000 (n=48) |
| Abstain đúng với văn bản ngoài domain (≥ 90%) | 16/16 | 12/12 | 12/12 |
| Thuật ngữ lạc ngữ cảnh (stray) abstain | 4/4 | 3/3 | (không có) |
| Sai-mà-tự-tin (≤ 5%) | 0/70 | 0/48 | 0/60 |
| ECE của confidence LLM, chỉ trên domain được chọn (≤ 0,10) | 0,035 | 0,040 | 0,032 |
| ECE tính cả câu trả lời `unknown` (không dùng làm kết luận)** | 0,111 | 0,150 | 0,151 |
| Vi phạm định dạng giao thức | 0/76 | 0/52 | 0/60 |
| Bản dịch hỏng | 0/76 | 0/52 | 0/60 |
| Độ trễ token đầu p50 / p95 (≤ ~1,5 s) | 0,45 / 0,78 s | 0,47 / 0,69 s | 0,56 / 0,88 s |
| Tổng thời gian một lời gọi p95 | 0,82 s | 0,73 s | 1,08 s |

\** Khi LLM trả `unknown` đúng thì confidence kèm theo thường thấp (0,1–0,9) dù quyết định đúng, nên ECE trên mọi câu trả lời
bị phóng đại; chỉ số có nghĩa là ECE trên các lần LLM *chọn* domain.

- **Lặp 5 lần giống nhau (≥ 98%):** 24 mẫu dev × 5 lần = 120 lời gọi: quyết định domain giống nhau 120/120 (100%), 24/24 mẫu
  nhất quán tuyệt đối. Bản dịch giống hệt nhau chỉ ở 8/24 mẫu (temperature 0,2) — nhất quán về *domain*, không về *câu chữ*.
- **Thuật ngữ (dev, cùng model, 54 câu có thuật ngữ, 76 lượt khớp):** không domain 0,605 · domain thủ công đúng 0,987 ·
  `auto` 0,987 ⇒ `auto` ngang domain thủ công (chênh 0 điểm, tiêu chí ≤ 5) và hơn không-domain 38 điểm. Phần tăng này chủ yếu
  đến từ glossary được tiêm vào prompt; trên hold-out chỉ có 6 lượt khớp thuật ngữ nên số 1,000 ở đó gần như không có sức nặng.
- **Quy tắc `decide_domain` so với tin LLM trần:** trên dev và hold-out hai cách cho kết quả y hệt; trên val, quy tắc có ngưỡng
  confidence + đối chiếu từ điển abstain đúng 3/3 ca stray còn tin LLM trần chỉ 2/3 (một mẫu, chưa đủ để kết luận).
- **Chi phí:** auto ≈ 300–380 token/lời gọi, domain thủ công ≈ 130–180 token (đo bằng `usage` của Groq). Với trần
  8.000 token/phút ≈ 21–26 lời gọi auto/phút hoặc 45–60 lời gọi thủ công/phút; trần 1.000 request/ngày (suy ra từ `reset` ≈ 8 giờ,
  đã quan sát số còn lại giảm theo ngày). Mô phỏng một phiên gõ trên component thật (60 ký tự, hai lần dừng): dịch thông thường
  3 request, chế độ domain 2 request (debounce 1,5 s).
- **Chỉ mục từ điển:** dựng 2,8 ms, quét câu 888 ký tự 3,6 ms, bộ nhớ Python ≈ 330 KiB (246 mục).
- Ngân sách đã dùng cho toàn bộ phép đo: khoảng 470/1.000 request Groq trong ngày.

### 6.3 Cách đọc các con số này

Các bộ dữ liệu nhỏ và dễ (câu rõ chủ đề): mọi chỉ số chính chạm trần (1,000/0 lỗi) nên **không phân biệt được các ngưỡng**;
với 0 lỗi trên n mẫu, cận trên 95% của tỉ lệ lỗi xấp xỉ 3/n (≈ 6% với 48 mẫu in-domain, ≈ 5% với 60 mẫu hold-out) —
tức chưa đủ để khẳng định "sai-mà-tự-tin ≤ 5%" một cách chắc chắn. Đây là kết quả phát triển, **không phải** kết quả bài test
chính thức của `evaluation.md`, vốn chưa chạy.

## 7. Giới hạn và việc chưa làm

- **Model Groq cũ không dùng được:** key hiện tại trả 404 cho `llama-3.1-8b-instant`, nên auto-domain cũ chưa từng chạy được
  trên cấu hình này (mọi lỗi bị nuốt thành chuỗi rỗng). Ngoài phạm vi domain vẫn còn 3 chỗ gọi model đó
  (`llm_service.py` flow thường, `extract_flashcard`, `translation_service.py` fallback Groq); theo yêu cầu chỉ sửa phạm vi domain
  nên chúng **chưa đổi** và vẫn sẽ lỗi 404 rồi rơi sang Gemini/NLLB.
- **Ngưỡng chưa được chỉnh bằng dữ liệu:** `AUTO_DOMAIN_MIN_CONFIDENCE=0,75` và biên xung đột +2 là giá trị mặc định; dev/val/hold-out
  đều bão hòa. Cần bộ dữ liệu khó hơn (câu trộn nhiều lĩnh vực, câu ngắn mơ hồ, thuật ngữ đa nghĩa) trước khi chỉnh.
- **Chưa đo trên bộ test đóng băng của `evaluation.md`** (có chủ ý); các tiêu chí trong mục 6.2 chỉ là định hướng.
- **Hold-out có nhãn theo chủ đề bài Wikipedia** nên có thể nhiễu ở bài giáp ranh; chỉ 6 lượt khớp thuật ngữ từ điển.
- **Gemini** mới thử ~14 lượt: không có số liệu độ ổn định của giao thức một-lời-gọi trên Gemini ngoài mẫu nhỏ này.
- **Bản dịch LLM không được đo chất lượng văn phong** (không có bản dịch tham chiếu); chỉ đo việc áp dụng thuật ngữ từ điển,
  tỷ lệ bản dịch hỏng và độ trễ. Bản dịch giữa các lần gọi khác nhau về câu chữ (chỉ 8/24 mẫu giống hệt sau 5 lần).
- **Từ điển chỉ 246 mục** (~41 mỗi domain) và hiện không có từ nào thuộc hai domain, nên nhánh `ambiguous` mới được test bằng
  dữ liệu giả lập; nó sẽ xuất hiện thật khi admin thêm từ trùng domain.
- **Quota:** 1.000 request/ngày và 8.000 token/phút của key hiện tại là trần cứng cho mọi người dùng cùng lúc; debounce 1,5 s
  chỉ là phòng tuyến phía client, circuit breaker ở backend chặn việc gọi lại khi đã hết hạn mức (khi đó NLLB làm phao).
- **Chưa làm:** hạn mức theo người dùng ở backend; cache bản dịch cho chế độ "Dịch thông thường" của `/stream`;
  `Persentation.pdf`/báo cáo cuối chưa cập nhật theo kiến trúc mới.

## 8. Chạy test

```
cd services/realtime_translation_service
python -m pytest tests/unit tests/integration -q
cd ../../frontend && npx tsc --noEmit -p tsconfig.json && npx vitest run
# Đo thật (tốn quota Groq; không in key):
python evaluation/run_domain_raw.py --split dev --model qwen/qwen3.8-27b --out evaluation/results/domain_raw_dev_x.jsonl
python evaluation/analyze_domain_raw.py evaluation/results/domain_raw_dev_x.jsonl --show-errors
```
