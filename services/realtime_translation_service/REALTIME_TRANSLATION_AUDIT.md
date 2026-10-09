# Báo cáo tái-audit lần 2 — Realtime Translation Service

**Ngày:** 08/10/2026  
**Phạm vi:** working tree hiện tại của Realtime Translation Service và frontend gọi API dịch  
**Trọng tâm:** xác nhận các fix audit trước và rà lỗi tiềm ẩn trong dịch theo domain, cache, SSE, language detection, độ trễ và benchmark.  
**Phương pháp:** đọc source và diff hiện tại; không chạy test, benchmark hoặc Docker build.

> Repository hiện chỉ có một số file service/frontend đã sửa so với lần audit trước. Báo cáo đánh giá working tree, không thay đổi code service. File này là báo cáo được cập nhật.

## 1. Kết luận

Các fix trước đã đóng được nhiều vấn đề: fallback provider ở `/text` trả 503 thay vì placeholder; schema giới hạn mã ngôn ngữ; detector dùng top-2 margin và luật cho văn bản ngắn; cache domain dùng toàn văn bản; model FastText giờ có đường dẫn khớp downloader; UI đọc đúng event `resolved_source_lang`; log stream không còn ghi raw text; warning auto-domain được gửi trên stream; readiness đã tính Supabase; cache writes chính và Gemini non-stream ở flow thường đã chuyển sang async/thread; fixture FastText test dùng tuple ba phần tử.

**Trạng thái:** chưa thấy lại các lỗi P0 của audit trước, nhưng còn ít nhất một lỗi P1 có thể làm request dịch theo domain trả 500 và một lỗi P1 có thể trả nhầm bản dịch từ cache.

## 2. Fix đã xác nhận trong source

| Mục audit trước | Trạng thái | Bằng chứng |
|---|---|---|
| Placeholder được trả thành công khi provider lỗi | **Đã sửa**: HTTP 503 khi mọi provider non-stream thất bại | [`translation_service.py`](app/services/translation_service.py#L409-L410) |
| Mã nguồn/đích không hỗ trợ bị map sang Anh/Việt | **Đã sửa tại request schema** | [`translation.py`](app/schemas/translation.py#L4-L14) |
| FastText bỏ qua margin/short-input uncertainty | **Đã cải thiện**; vẫn cần dữ liệu thực để hiệu chỉnh threshold | [`fasttext_detector.py`](app/services/fasttext_detector.py#L33-L53), [`translation_service.py`](app/services/translation_service.py#L61-L124) |
| Cache phân loại domain băm 60 ký tự đầu | **Đã sửa**: hash toàn văn bản | [`cache_service.py`](app/services/cache_service.py#L70-L75) |
| FastText model path không khớp downloader | **Đã sửa theo source**: detector dùng `../../models`, downloader lưu trong service `models/` | [`fasttext_detector.py`](app/services/fasttext_detector.py#L6-L10), [`download_model.py`](download_model.py#L5-L20) |
| SSE event key backend/frontend khác nhau | **Đã sửa**: cả hai dùng `resolved_source_lang` | [`llm_service.py`](app/services/llm_service.py#L331-L346), [`translationService.ts`](../../frontend/src/services/translationService.ts#L107-L123) |
| Stream log nội dung gốc | **Đã sửa**: chỉ log length/domain | [`translation.py`](app/routers/translation.py#L158-L160) |
| Warning khi stream auto-domain fallback | **Đã thêm** | [`llm_service.py`](app/services/llm_service.py#L155-L192) |
| Readiness bỏ qua trạng thái Supabase | **Đã sửa**: Supabase nằm trong điều kiện degraded | [`main.py`](app/main.py#L103-L142) |
| Cache writes và general Gemini non-stream chặn event loop | **Đã cải thiện**, domain Gemini còn đồng bộ (xem phát hiện dưới) | [`translation_service.py`](app/services/translation_service.py#L327-L410) |
| Mock FastText test chưa theo tuple ba phần tử | **Đã sửa** | [`test_language_detection.py`](tests/unit/test_language_detection.py#L8-L13), [`test_language_detection.py`](tests/unit/test_language_detection.py#L92-L97) |
| Locust context manager thiếu `catch_response=True` | **Đã sửa**; nhưng kịch bản vẫn không kiểm tra lỗi bên trong SSE | [`locustfile.py`](evaluation/locustfile.py#L21-L55) |

Đường dẫn model được xác nhận bằng đối chiếu path trong source, chưa được xác nhận bằng Docker build/container runtime.

## 3. Phát hiện còn lại

### P1 — Nhánh dịch có domain và glossary truyền thừa tham số vào prompt builder

**Bằng chứng:** [`translation_service.py`](app/services/translation_service.py#L254-L270), [`text_normalizer.py`](app/utils/text_normalizer.py#L57-L73).

`build_context_aware_prompt` nhận 4 tham số: `(domain, found_terms, source_lang, target_lang)`, nhưng non-stream domain flow gọi với 5 tham số, thêm `text` ở dòng 258. Lời gọi này nằm trước khối `try` gọi Gemini, nên khi `found_terms` không rỗng và Gemini client có sẵn, Python sẽ raise `TypeError` trước khi fallback NLLB chạy. Kết quả có thể là HTTP 500 cho `/text` với thuật ngữ khớp glossary.

Luồng streaming trong `llm_service.py` gọi cùng helper với đúng 4 tham số, nên hai API có hành vi khác nhau.

**Khắc phục:** bỏ tham số thứ năm hoặc đổi chữ ký/helper theo ý định; đặt việc tạo prompt trong nhánh có kiểm soát lỗi phù hợp.  
**Xác minh:** `/text` domain request có thuật ngữ khớp glossary, với Gemini bật và tắt; đối chiếu với `/stream`.

### P1 — Cache dịch gộp nội dung chỉ khác chữ hoa/thường

**Bằng chứng:** [`translation_service.py`](app/services/translation_service.py#L299-L318).

Translation key được tạo từ `text.strip().lower()`. Hai input khác nghĩa do viết hoa nhưng có cùng source/target/domain dùng chung cache. Ví dụ `US` và `us`, hoặc `IT` và `it`, có thể nhận cùng bản dịch dù một dạng là tên/mã và dạng kia là từ thường.

**Tác động:** cache hit có thể trả bản dịch của văn bản trước đó mà không gọi model, nên lỗi khó nhận biết qua HTTP status.  
**Khắc phục:** tạo key từ nội dung nguyên bản đã chuẩn hóa Unicode và khoảng trắng một cách bảo toàn phân biệt chữ hoa/thường; nếu muốn case-insensitive cho từ điển thì chỉ áp dụng ở tầng dictionary lookup, không dùng chung cho toàn translation cache.  
**Xác minh:** gọi cùng cặp input chỉ khác case liên tiếp và xác nhận không dùng chéo cache khi ngữ nghĩa khác.

### P2 — Cache warning có thể giữ metadata cũ hoặc gắn nhầm nguồn domain

**Bằng chứng:** [`cache_service.py`](app/services/cache_service.py#L32-L49), [`translation_service.py`](app/services/translation_service.py#L302-L318).

`set_cached_translation` chỉ ghi `trans_warn:{key}` khi `warning` có giá trị; nếu update cùng key không warning, warning cũ không bị xóa. Ngoài ra auto-domain được resolve thành tên domain rồi dùng chung cache key với người dùng chọn thủ công cùng domain. Bản dịch có thể đúng nhưng cached warning vẫn nói hệ thống “tự động nhận diện” dù request hiện tại là chọn tay (hoặc warning cũ khác vẫn còn).

**Khắc phục:** xóa warning key khi ghi translation không có warning, hoặc lưu translation + warning atomically trong một object; nếu metadata phụ thuộc request mode, đưa mode/provenance vào cache contract hoặc không cache warning như một phần của translation.  
**Xác minh:** lần lượt gọi auto domain rồi manual cùng text/domain, và cập nhật key từ có warning sang không warning; response sau phải có metadata phù hợp.

### P2 — Domain Gemini non-stream vẫn dùng API đồng bộ trong async handler

**Bằng chứng:** [`translation_service.py`](app/services/translation_service.py#L254-L270), đối chiếu flow thường dùng async call tại [`translation_service.py`](app/services/translation_service.py#L393-L406).

Ở flow domain khi glossary khớp, `client.models.generate_content(...)` được gọi đồng bộ bên trong `async def`. Nếu provider chậm, event loop bị chặn trong thời gian chờ. Điều này làm giảm hiệu quả của các async/cache cải tiến ở các nhánh khác.

**Khắc phục:** dùng API async `client.aio.models.generate_content` hoặc đưa sync call vào thread pool có giới hạn; cấu hình timeout.  
**Xác minh:** tạo provider delay giả lập và đo event-loop lag/latency của request song song.

### P2 — Non-stream frontend vẫn bỏ qua ngôn ngữ server đã resolve

**Bằng chứng:** backend trả `resolved_source_lang` tại [`translation.py`](app/routers/translation.py#L144-L155), nhưng frontend non-stream gán `detectedSourceLang: req.sourceLang` tại [`translationService.ts`](../../frontend/src/services/translationService.ts#L35-L44).

SSE parser hiện đã sửa đúng; hàm `translateText` không-stream vẫn trả `auto` cho field client `detectedSourceLang`, thay vì đọc response `resolved_source_lang`. Nếu consumer dùng hàm này, UI/history/voice có thể giữ ngôn ngữ chưa resolve.

**Khắc phục:** map `data.data.resolved_source_lang` (có fallback theo contract) vào kiểu dữ liệu frontend.  
**Xác minh:** gọi non-stream với `source_lang="auto"` và kiểm tra giá trị `detectedSourceLang` sau parse.

### P2 — Locust stream vẫn tính SSE error event là request thành công

**Bằng chứng:** [`locustfile.py`](evaluation/locustfile.py#L45-L55).

`catch_response=True` và status-code validation đã thêm, nhưng loop chỉ đọc từng dòng rồi bỏ qua. API có thể trả HTTP 200 nhưng stream chứa `{"error": ...}` hoặc kết thúc trước khi có text; Locust vẫn ghi request thành công.

**Khắc phục:** parse SSE `data:` payload; đánh dấu failure nếu có error event hoặc không có event text/completion hợp lệ.  
**Xác minh:** mock stream 200 chứa error JSON và stream bị cắt; cả hai phải được Locust tính là failure.

### P2 — Domain fallback cho câu ngắn có thể ghi warning sai/khó hiểu

**Bằng chứng:** [`translation_service.py`](app/services/translation_service.py#L182-L245), [`llm_service.py`](app/services/llm_service.py#L159-L172), [`llm_service.py`](app/services/llm_service.py#L263-L271).

Với `domain=auto` và ngôn ngữ không phải EN→VI, code đặt domain rỗng rồi tiếp tục nhánh short-term. Non-stream có thể ghi đè warning “không hỗ trợ cặp ngôn ngữ” thành thông báo “không tìm thấy từ điển chuyên ngành ''”. Stream có thể phát warning auto-domain fallback rồi tiếp tục phát thêm warning word-by-word. Tác dụng dịch vẫn là NLLB, nhưng metadata dư thừa hoặc gây hiểu nhầm.

**Khắc phục:** tách rõ nhánh fallback sang general translation và return/route vào flow chung; chỉ phát một warning kết hợp nói rõ lý do và engine fallback.  
**Xác minh:** test text <=3 từ cho auto-domain với source/target không hỗ trợ và domain không có dictionary entry; xác nhận chỉ một warning chính xác.

## 4. Tình trạng auto-domain sau các fix

- Long-text auto-domain vẫn chỉ hỗ trợ EN→VI và gọi Groq classifier; hiện classifier trả domain string hoặc rỗng, chưa có confidence score/calibration. Đây là giới hạn sản phẩm cần hiển thị/đánh giá, không phải lỗi runtime đã tái hiện.
- Short text hiện được gọi rõ là “Multi-domain lookup”; nó trả nhiều nghĩa, không tự chọn một ngành và dùng glossary. Nếu yêu cầu sản phẩm là tự xác định domain cho từ/cụm ngắn, tính năng đó vẫn chưa có đủ tín hiệu ngữ cảnh.
- Non-stream nhánh glossary có lỗi tham số prompt builder ở trên; stream dùng đúng signature, vì thế không thể lấy stream pass làm bằng chứng `/text` domain flow hoạt động.

## 5. Các kiểm tra nên chạy sau khi xử lý

| Ưu tiên | Ca kiểm tra | Tiêu chí đạt |
|---|---|---|
| P1 | `/text` domain có glossary match, Gemini configured | Không 500; glossary prompt được gọi đúng |
| P1 | `US` rồi `us`, `IT` rồi `it`, cùng source/target/domain | Không trả chéo bản dịch do cache key |
| P2 | Auto domain rồi manual cùng domain/text; có/không warning | Warning chính xác theo request, không còn metadata cũ |
| P2 | Stream auto-domain short và unsupported language pair | Chỉ một warning, lý do đúng, output nói rõ general fallback |
| P2 | Non-stream `source_lang=auto` qua frontend | Client nhận resolved language, không giữ chuỗi `auto` |
| P2 | Locust SSE có HTTP 200 nhưng chứa error event | Request được tính là failure |
| Deploy | Docker build sạch và `/health/ready` | FastText/NLLB load đúng; status 200 khi dependencies thiết yếu sẵn sàng |
| Load | Domain Gemini provider chậm + request song song | Event loop không bị block; p95/p99 được ghi lại |

## 6. Thứ tự xử lý khuyến nghị

1. **Sửa P1 prompt builder signature** trong non-stream domain translation.
2. **Sửa translation cache key** để không gộp khác biệt case có ý nghĩa.
3. **Làm warning cache nhất quán** và phân biệt metadata auto/manual.
4. **Dùng async Gemini trong domain flow** và sửa parser non-stream frontend lấy resolved language.
5. **Hoàn thiện Locust SSE assertions**, sau đó chạy test/unit, integration và benchmark trong môi trường staging.

## 7. Giới hạn

Không chạy test, benchmark, Docker build hoặc gọi Redis/Supabase/Groq/Gemini trong lần audit này. Lỗi thừa tham số được xác định bằng đối chiếu chữ ký hàm và callsite; cần chạy test xác nhận runtime sau khi fix. Benchmark artifact cũ không xác nhận hiệu năng của working tree hiện tại.

## 8. Kế hoạch khắc phục đề xuất

Kế hoạch dưới đây chuyển các phát hiện còn mở thành các đầu việc có thứ tự phụ thuộc. Đây là kế hoạch triển khai; lượt này không sửa mã và không chạy kiểm thử.

### Giai đoạn 1 — Chặn lỗi dịch sai hoặc request thất bại (P1)

- [ ] **P1.1 Sửa lời gọi prompt builder trong nhánh domain non-stream.** Đồng bộ số lượng/thứ tự tham số giữa `translation_service.py` và `text_normalizer.py`; xác nhận luồng chỉ gọi prompt builder khi có glossary terms. Giữ cách xử lý lỗi provider rõ ràng, không biến lỗi nội bộ thành bản dịch thành công.
- [ ] **P1.2 Bảo toàn phân biệt chữ hoa/thường trong translation cache key.** Chuẩn hóa Unicode và khoảng trắng nếu cần, nhưng không lowercase nội dung trước khi băm. Thêm namespace/version mới cho key để dữ liệu cache cũ không được đọc nhầm sau thay đổi.
- [ ] **P1.3 Thêm kiểm thử hồi quy tập trung cho hai lỗi trên.** Tối thiểu kiểm tra domain + glossary ở `/text`, và cặp đầu vào `US`/`us`, `IT`/`it` có thể cho bản dịch khác nhau.

**Điều kiện hoàn tất:** nhánh non-stream domain không phát sinh `TypeError`; cache không trả kết quả của chuỗi khác biệt về case; lỗi provider vẫn được biểu diễn là lỗi rõ ràng.

### Giai đoạn 2 — Làm nhất quán metadata, warning và API/UI (P2)

- [ ] **P2.1 Sửa vòng đời warning trong cache.** Khi ghi một kết quả không có warning, xóa warning cũ tương ứng hoặc lưu translation và metadata warning trong cùng một record có tính nguyên tử. Không để cache hit phụ thuộc vào trạng thái warning từ request trước.
- [ ] **P2.2 Quyết định cách xử lý provenance auto/manual.** Nếu warning hoặc kết quả khác nhau theo cách chọn domain, đưa provenance vào cache key; nếu chỉ warning khác, giữ provenance ở metadata theo request và không tái sử dụng warning cũ. Ghi rõ contract để tránh key tăng không cần thiết.
- [ ] **P2.3 Đồng bộ source language đã resolve ở frontend non-stream.** Parse `resolved_source_lang` từ response và cập nhật kiểu dữ liệu/API contract; chỉ dùng giá trị request làm fallback khi server không cung cấp trường này.
- [ ] **P2.4 Chuẩn hóa warning của auto-domain fallback.** Các nhánh short/unsupported language chỉ trả một warning rõ nguyên nhân và nêu đúng chế độ dịch thay thế.

**Điều kiện hoàn tất:** auto rồi manual cùng domain không làm lộ warning cũ; client hiển thị ngôn ngữ nguồn đã resolve; fallback không phát warning trùng hoặc gây hiểu nhầm.

### Giai đoạn 3 — Tránh block event loop và cải thiện vận hành (P2)

- [ ] **P2.1 Chuyển lời gọi Gemini đồng bộ trong domain non-stream sang API async**, nhất quán với luồng generic hiện có. Nếu SDK/provider không hỗ trợ async ổn định, cô lập lời gọi blocking trong thread pool có giới hạn.
- [ ] **P2.2 Áp dụng timeout và retry có giới hạn** cho provider; không retry lỗi không thể khắc phục và không retry vô hạn. Giữ response lỗi phân biệt được timeout, provider unavailable và lỗi nội bộ.
- [ ] **P2.3 Bổ sung/kiểm tra metric theo từng giai đoạn**: detection, domain classification, cache, provider và tổng thời gian; ghi latency cùng outcome mà không ghi nội dung văn bản người dùng.

**Điều kiện hoàn tất:** request domain chậm không chặn request đồng thời khác; có số liệu p50/p95/p99 theo giai đoạn trong môi trường staging.

### Giai đoạn 4 — Biến kiểm thử tải thành tín hiệu đáng tin (P2)

- [ ] **P2.1 Hoàn thiện Locust assertion cho `/text` và SSE.** Đọc các SSE `data:` event, phát hiện error event, thiếu nội dung kết thúc hoặc response rỗng; chỉ tính là thành công khi payload ứng dụng hợp lệ, không chỉ dựa vào HTTP 200.
- [ ] **P2.2 Chạy kiểm thử theo tầng sau khi sửa:** unit cho cache/prompt builder, API integration cho `/text` và stream, sau đó staging load test với provider chậm và request song song.
- [ ] **P2.3 Ghi nhận baseline và ngưỡng chấp nhận trước khi tuyên bố latency đạt yêu cầu.** Báo cáo p50/p95/p99, tỷ lệ lỗi, cache hit rate và timeout; nêu rõ cấu hình tải, provider và môi trường.

**Điều kiện hoàn tất:** Locust không tính lỗi ứng dụng trong SSE là thành công; có kết quả staging tái lập được và ngưỡng latency/error rate được thống nhất.

### Giai đoạn 5 — Phát triển automatic domain detection thành tính năng có thể đánh giá (P3)

- [ ] **P3.1 Chốt kỳ vọng sản phẩm cho input ngắn.** Hiện chế độ “Multi-domain lookup” trả nhiều nghĩa theo domain; xác định rõ đây có phải trải nghiệm mong muốn hay cần phân loại một domain duy nhất. Không gọi multi-lookup là auto-classification nếu chưa chọn domain.
- [ ] **P3.2 Tạo tập dữ liệu có nhãn** bao phủ domain, ngôn ngữ, cặp dịch, câu ngắn/mơ hồ và nội dung ngoài phạm vi; tách tập phát triển và tập đánh giá.
- [ ] **P3.3 Đo confidence và đặt chính sách abstain/fallback.** Khi không chắc, trả fallback minh bạch hoặc hỏi người dùng chọn domain thay vì âm thầm chọn sai. Log domain được chọn, confidence và lý do ở dạng không chứa nội dung nhạy cảm.
- [ ] **P3.4 Mở rộng có kiểm soát theo ngôn ngữ và domain.** Chỉ bật domain sau khi có dữ liệu đánh giá cho từng phạm vi được hỗ trợ; kiểm tra glossary, thuật ngữ, đơn vị, ký hiệu và tên riêng.

**Điều kiện hoàn tất:** có metric chất lượng theo domain/ngôn ngữ và chính sách rõ cho trường hợp không chắc; người dùng/quan sát vận hành biết domain nào đã được chọn.

### Thứ tự phụ thuộc và cổng phát hành

1. Hoàn tất Giai đoạn 1 trước khi tin cậy kết quả dịch hoặc cache sau deploy.
2. Hoàn tất Giai đoạn 2 trước khi dùng warning và resolved language làm tín hiệu cho người dùng.
3. Hoàn tất Giai đoạn 3 trước khi chạy benchmark tải có concurrent domain requests.
4. Hoàn tất Giai đoạn 4 trước khi đưa ra kết luận về độ ổn định/latency.
5. Làm Giai đoạn 5 theo quyết định sản phẩm; không dùng benchmark tốc độ thay cho đánh giá chất lượng domain.

### 5 việc nên làm đầu tiên

1. Sửa call signature prompt builder ở domain non-stream.
2. Đổi cache key sang dạng phân biệt case và version namespace.
3. Thêm hồi quy cho lỗi 500 và cache collision trước khi phát hành hai thay đổi trên.
4. Sửa warning cache cùng việc frontend dùng `resolved_source_lang`.
5. Chuyển domain Gemini sang async, rồi mới hoàn thiện assertion Locust và đo staging.
