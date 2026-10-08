# Báo cáo tái-audit — Realtime Translation Service

**Ngày đánh giá:** 08/10/2026  
**Phạm vi:** working tree hiện tại của `services/realtime_translation_service` và luồng frontend gọi translation stream  
**Trọng tâm:** phát hiện ngôn ngữ, tự nhận diện chuyên ngành, cache, phản hồi lỗi, độ trễ và bộ đánh giá.  
**Phương pháp:** đọc mã nguồn và diff hiện tại, đối chiếu báo cáo/artifact có sẵn. Không chạy test hoặc benchmark trong lượt này.

> Repository có nhiều thay đổi chưa commit. Báo cáo đánh giá các thay đổi hiện có trên working tree; không sửa mã service hoặc các thay đổi đó. File này là báo cáo audit được cập nhật.

## 1. Kết luận

Các fix đã xử lý được nhiều điểm quan trọng của audit trước: placeholder dịch giả không còn trả thành công; API `/text` và `/stream` đã giới hạn mã ngôn ngữ; FastText trả cả top score và margin; hash phân loại domain dùng toàn văn bản; Supabase trong nhánh domain được đưa qua thread; có liveness/readiness; non-stream response có `resolved_source_lang`.

**Đánh giá hiện tại: tiến bộ rõ, nhưng vẫn còn việc cần sửa trước khi tin cậy production.** Phát hiện ưu tiên cao nhất còn lại:

1. Model FastText được tải vào một thư mục nhưng detector mặc định tìm ở thư mục khác; trong Docker khả năng cao detector báo thiếu model, làm readiness trả 503 và buộc nhận diện rơi về Lingua.
2. SSE backend gửi `resolved_source_lang`, nhưng frontend chỉ đọc `detected_source_lang`, nên luồng UI không nhận được ngôn ngữ vừa phát hiện.
3. `/stream` chưa trả warning khi auto-domain không hỗ trợ cặp ngôn ngữ hoặc không phân loại được; trong khi `/text` đã có warning.
4. Endpoint stream in nguyên văn đầu vào ra stdout qua debug print.
5. Short-text `domain=auto` vẫn là tra cứu nhiều nghĩa trên mọi ngành, không phải chọn một chuyên ngành và dùng glossary của ngành đó.

## 2. Trạng thái các phát hiện cũ

| Phát hiện audit trước | Trạng thái hiện tại | Bằng chứng / ghi chú |
|---|---|---|
| Provider hỏng nhưng trả `[Bản dịch: ...]` với `ok=true` | **Đã sửa trong `/text`** | Cuối `translate_text` hiện raise HTTP 503: [`translation_service.py`](app/services/translation_service.py#L409-L410). Luồng stream cũng phát event lỗi khi không còn provider. |
| Source/target code không hợp lệ âm thầm map Anh/Việt | **Đã sửa ở request translation** | Pydantic giới hạn mã trong hai schema dịch: [`translation.py`](app/schemas/translation.py#L4-L14). Helper nội bộ vẫn có default map, nên giữ validation tại mọi entry point. |
| FastText bỏ qua kiểm tra margin và văn bản ngắn | **Đã cải thiện** | Detector lấy `k=2`, tính margin; nhánh FastText và Lingua đều tăng ngưỡng cho input dưới 3 từ: [`fasttext_detector.py`](app/services/fasttext_detector.py#L33-L53), [`translation_service.py`](app/services/translation_service.py#L61-L124). Chưa có kết quả benchmark để xác nhận calibration tốt. |
| Cache domain chỉ băm 60 ký tự đầu | **Đã sửa** | Hash hiện dùng toàn bộ text sau strip/lower: [`cache_service.py`](app/services/cache_service.py#L70-L75). |
| API không báo ngôn ngữ resolved | **Đã cải thiện một phần** | `/text` thêm `resolved_source_lang`; stream thêm `resolved_source_lang`, nhưng frontend đang đọc tên field cũ (phát hiện mới bên dưới). [`translation.py`](app/schemas/translation.py#L24-L31), [`llm_service.py`](app/services/llm_service.py#L331-L346). |
| Không có readiness | **Đã thêm, còn thiếu nhất quán** | Có liveness/readiness và kiểm tra dependency; nhưng Supabase được kiểm tra mà không tham gia quyết định `ready/degraded`: [`main.py`](app/main.py#L103-L141). |
| I/O sync trong domain path | **Đã giảm một phần** | Supabase domain lookup và một số Redis call dùng `asyncio.to_thread`; các cache write ở flow thường và Gemini non-stream vẫn đồng bộ trong async handler. [`translation_service.py`](app/services/translation_service.py#L217-L230), [`translation_service.py`](app/services/translation_service.py#L327-L410). |

## 3. Phát hiện còn lại

### P1 — FastText model path không khớp giữa detector và downloader/Docker

**Bằng chứng:** [`fasttext_detector.py`](app/services/fasttext_detector.py#L6-L10), [`download_model.py`](download_model.py#L5-L20), [`Dockerfile`](Dockerfile#L16-L21).

Detector dựng mặc định `MODEL_DIR` từ `app/services/../../../models`, tức đi ra `services/models` ở local và `/models` trong container. Downloader lại lưu file vào `realtime_translation_service/models/lid.176.ftz` (trong container là `/app/models/lid.176.ftz`). Hai vị trí không trùng nhau. File FastText đang có trong working tree nằm ở `services/models`, ngoài Docker build context `services/realtime_translation_service`; Docker không COPY file ngoài context. Trong khi đó `download_model.py` tải file vào bên trong build context nhưng app không tìm ở thư mục đó.

**Tác động:** theo cấu hình mặc định, FastText có thể không load được trong image; `/health/ready` sẽ thấy `fasttext_model=missing`, trả 503; auto-detection tiếp tục với Lingua nhưng mất fast path.  
**Khắc phục:** thống nhất một đường dẫn bên trong service, ví dụ `app/models/lid.176.ftz`, dùng cùng constant/env trong downloader và detector; thêm kiểm tra file/checksum sau download.  
**Xác minh:** build image sạch, kiểm tra file tồn tại tại đúng path trong container, xác nhận `_get_fasttext_model()` load thành công và readiness phản ánh đúng.

### P1 — Tên field phát hiện ngôn ngữ giữa SSE backend và frontend không khớp

**Bằng chứng:** backend stream gửi `resolved_source_lang` tại [`llm_service.py`](app/services/llm_service.py#L331-L346); frontend chỉ kiểm tra `detected_source_lang` tại [`translationService.ts`](../../frontend/src/services/translationService.ts#L107-L120).

Frontend vì vậy không gọi `onDetectedLanguage` khi server gửi event đã đổi tên. Mặc dù request vẫn được dịch bằng ngôn ngữ đã phát hiện, UI có thể không cập nhật ngôn ngữ, nút đổi hướng dịch và TTS có thể dùng state cũ. Đây là mismatch giữa hai phần của cùng feature.

**Khắc phục:** thống nhất contract một tên field end-to-end; cập nhật parser, TypeScript response/event types và component state cùng lúc.  
**Xác minh:** gửi `source_lang="auto"` qua SSE; assert event được parse, state UI đổi đúng ngôn ngữ và không bị stale khi bắt đầu request tiếp theo.

### P1 — Stream auto-domain không báo lý do fallback như `/text`

**Bằng chứng:** [`llm_service.py`](app/services/llm_service.py#L155-L188), đối chiếu nhánh `/text` tại [`translation_service.py`](app/services/translation_service.py#L175-L215).

Trong stream path, cặp ngôn ngữ khác EN→VI đặt `domain=""` mà không yield warning; long-text classifier không trả domain cũng đặt domain rỗng mà không cảnh báo. `/text` đã thêm warning cho cả hai trường hợp. Do frontend TranslationBox dùng streaming, người dùng chính có thể không biết domain detection đã bị bỏ qua và kết quả đang là dịch thường.

**Khắc phục:** dùng chung domain-resolution function giữa streaming và non-streaming, hoặc đảm bảo stream phát cùng warning/status và domain metadata.  
**Xác minh:** kiểm tra SSE với `source_lang=vi`, Groq thiếu key, classifier trả unknown và JSON lỗi; mỗi trường hợp cần thể hiện fallback rõ.

### P1 — Debug print ghi toàn bộ văn bản người dùng vào log

**Bằng chứng:** [`translation.py`](app/routers/translation.py#L158-L160).

`stream_translate_endpoint` in `payload.text` ra stdout cùng domain ở mọi request. Nội dung gửi dịch có thể chứa dữ liệu cá nhân hoặc tài liệu nhạy cảm; stdout thường được thu gom vào container logs. Đây là rủi ro riêng tư và vận hành, không cần lỗi provider mới xảy ra.

**Khắc phục:** bỏ debug print; nếu cần trace, log request ID, độ dài, domain đã chuẩn hóa và trạng thái xử lý, không log raw text mặc định.  
**Xác minh:** gửi chuỗi canary qua endpoint và kiểm tra application/container logs không chứa chuỗi đó.

### P1 — Auto-domain cho input ngắn vẫn không chọn chuyên ngành

**Bằng chứng:** [`translation_service.py`](app/services/translation_service.py#L182-L200), [`domain_service.py`](app/services/domain_service.py#L107-L134), [`llm_service.py`](app/services/llm_service.py#L159-L170).

Với từ/câu ngắn, backend quét các từ điển và trả một danh sách nghĩa từ nhiều ngành dưới dạng warning, rồi dịch bằng NLLB thông thường. Không có bước xếp hạng/chọn ngành, confidence hoặc dùng glossary theo ngữ cảnh. Hành vi này phù hợp hơn với “tra cứu đa nghĩa” chứ chưa phải auto-domain detection.

**Khắc phục:** hoặc đặt tên/UX đúng là tra cứu nghĩa đa ngành; hoặc chỉ auto chọn ngành khi có đủ context và confidence, còn lại abstain/hỏi người dùng. Không khẳng định đã áp dụng thuật ngữ ngành nếu bản dịch vẫn dùng NLLB chung.  
**Xác minh:** test các từ đa nghĩa như `cell`, `bond`, `charge` trong nhiều context; ghi nhận domain được chọn, confidence và glossary thực sự áp dụng.

### P2 — I/O sync còn ở đường dịch thường

**Bằng chứng:** [`translation_service.py`](app/services/translation_service.py#L327-L410), [`cache_service.py`](app/services/cache_service.py#L23-L49).

Các nhánh NLLB/Groq/Gemini vẫn gọi `set_cached_translation` đồng bộ trong async function; Gemini non-stream dùng `client.models.generate_content` đồng bộ. Điều này có thể block event loop khi cache/provider chờ mạng. Phần async hóa trong domain path chưa bao phủ flow thường, vốn là luồng phổ biến.

**Khắc phục:** dùng async client hoặc đưa các thao tác sync có I/O qua thread pool giới hạn; đặt timeout và đo stage latency. Ưu tiên Gemini non-stream và Redis writes.  
**Xác minh:** concurrency test có provider/cache delay; theo dõi event-loop lag, throughput và p95/p99.

### P2 — Readiness kiểm tra Supabase nhưng vẫn báo ready khi Supabase hỏng

**Bằng chứng:** [`main.py`](app/main.py#L103-L141).

Readiness ghi `supabase=disconnected/error`, nhưng điều kiện chuyển trạng thái `degraded` chỉ xét NLLB, FastText và Redis. Nếu Supabase là dependency cần cho domain dictionaries/classification thì health check có thể trả 200 `ready` trong khi tính năng chuyên ngành hỏng hoặc giảm chất lượng.

**Khắc phục:** quyết định rõ Supabase bắt buộc hay optional. Nếu bắt buộc cho readiness, đưa trạng thái vào điều kiện; nếu optional, trả trạng thái degraded feature-level và mô tả khả năng còn phục vụ.  
**Xác minh:** mô phỏng Supabase down và kiểm tra response/status code khớp chính sách.

### P2 — Unit test language detection chưa cập nhật contract FastText 3 giá trị

**Bằng chứng:** detector trả `(lang, confidence, margin)` tại [`fasttext_detector.py`](app/services/fasttext_detector.py#L33-L50), nhưng fixture/mock trong [`test_language_detection.py`](tests/unit/test_language_detection.py#L8-L13) và fast-path case tại [`test_language_detection.py`](tests/unit/test_language_detection.py#L92-L97) vẫn trả tuple hai giá trị.

Khi code destructure ba biến, mock hai giá trị sẽ phát sinh exception rồi bị bắt như lỗi FastText; test “fast path” không còn thực sự kiểm tra fast path. Một số test có thể vẫn qua bằng Lingua, nên pass cũng không chứng minh contract mới đúng.

**Khắc phục:** cập nhật mock sang tuple ba phần tử, thêm test margin cao/thấp và short-text threshold; assert Lingua có/không được gọi tương ứng.  
**Xác minh:** chạy test language detection sau khi sửa fixture. Lượt audit này chưa chạy test.

### P2 — Locust stream scenario vẫn lỗi và benchmark cũ chưa thể dùng

**Bằng chứng:** [`locustfile.py`](evaluation/locustfile.py#L33-L45) vẫn dùng context manager cho request mà thiếu `catch_response=True`; artifact cũ [`load_test_results_exceptions.csv`](evaluation/metrics/load_test_results_exceptions.csv) ghi nhận lỗi này. Stats cũ ghi latency tới 45 giây nhưng không phải benchmark sạch.

Evaluator BLEU [`run_bleu_chrf.py`](evaluation/run_bleu_chrf.py#L13-L20) vẫn ghi rõ output là dữ liệu giả lập và tham chiếu `eval_dataset.json`; vì vậy metric cũ không chứng minh chất lượng model hiện tại.  
**Khắc phục:** sửa Locust request handling, kiểm tra status/SSE terminal event và chạy lại trong môi trường ghi rõ cấu hình; thay evaluator giả lập bằng API output thật cùng dataset gán nhãn/versioned.

## 4. Đánh giá hai tính năng trọng tâm

### Phát hiện ngôn ngữ nguồn

**Đã cải thiện:** giới hạn vào 10 ngôn ngữ hỗ trợ; chạy FastText top-2 + margin; short text dưới 3 từ yêu cầu ngưỡng cao hơn; Lingua cũng dùng confidence và margin; input không chắc sẽ yêu cầu chọn thủ công. Backend trả resolved language trên `/text` và gửi event trong SSE.

**Còn cần xử lý:** FastText file path không khớp downloader và Docker context; frontend lắng nghe event key cũ; test mock FastText chưa theo tuple mới; không có benchmark kết quả hiện tại chứng minh threshold tối ưu. Rule marker Đức/Pháp/Tây Ban Nha vẫn là heuristic cần kiểm tra với câu trộn ngôn ngữ/tên riêng.

### Tự động nhận diện chuyên ngành

**Đã cải thiện:** prompt classifier tách system instruction khỏi text user; cache classifier đã dùng toàn bộ text; `/text` báo warning khi cặp dịch không hỗ trợ hoặc classifier không nhận diện; có lookup cache và dictionary version.

**Còn cần xử lý:** long-text classifier chỉ hỗ trợ EN→VI và phụ thuộc Groq; không có confidence; short text vẫn hiển thị nhiều nghĩa thay vì chọn domain; stream không phát warning fallback; cần đánh giá classifier trên tập domain/out-of-domain lớn và nhiều ngôn ngữ hơn.

## 5. Kịch bản xác minh ưu tiên

| Mục tiêu | Ca kiểm tra | Tiêu chí đạt |
|---|---|---|
| Model FastText | Build image sạch, không mount `services/models` bên ngoài | Model nằm đúng path trong image; readiness báo loaded; auto detect không cần tải model khi nhận request |
| SSE contract | Gửi `source_lang=auto` từ TranslationBox | Frontend nhận event resolved, cập nhật detected language và UI/TTS dùng đúng state |
| Language confidence | `ok`, `bonjour`, `gift`, tên riêng, URL, emoji, câu pha ngôn ngữ | Không ép ngôn ngữ khi detector thiếu confidence; có thể yêu cầu chọn thủ công |
| Domain short | `cell`, `bond`, `charge` trong y tế, IT, tài chính | Trả đúng nghĩa theo context hoặc nêu đây là danh sách đa nghĩa; không tuyên bố tự chọn domain nếu không có |
| Domain fallback stream | Non-EN→VI; Groq thiếu/lỗi; domain unknown | SSE phát cảnh báo và trạng thái dịch thường; UX không giấu fallback |
| Privacy logging | Gửi nội dung canary riêng tư qua `/stream` | Raw input không xuất hiện trong stdout/container log |
| Cache | Hai đoạn cùng prefix nhưng nội dung/domain khác; cùng text manual-vs-auto domain | Không reuse classification sai; warning metadata không bị gắn nhầm nguồn |
| Failure handling | Tất cả provider lỗi | `/text` HTTP 503; `/stream` phát error event và không gửi nội dung dịch giả |
| Load/quality | Cache hit/miss; text ngắn/dài; cặp ngôn ngữ/domain | Có p50/p95/p99 thật và accuracy/confusion matrix từ dataset có nhãn |

## 6. Lộ trình tiếp theo

### P0/P1

1. Sửa FastText path thống nhất giữa Docker downloader và runtime detector; xác nhận readiness trong container.
2. Đồng bộ tên event language giữa backend và frontend; cập nhật TypeScript contract và test.
3. Bỏ raw-text debug logging khỏi `/stream`.
4. Đồng bộ warning/status domain fallback giữa streaming và non-streaming.
5. Quyết định sản phẩm cho short-text auto-domain: tra đa nghĩa hay phân loại theo context.

### P2/P3

6. Hoàn thiện async I/O cho cache write và non-stream Gemini; thêm timeout/metrics từng stage.
7. Căn chính sách readiness với vai trò thật của Supabase và provider.
8. Cập nhật fixture language detector sang tuple ba phần tử; sửa Locust `catch_response`; thay evaluator giả lập bằng đánh giá có thể tái lập.
9. Thu thập benchmark language detection và domain classification trên tập đại diện, gồm case mơ hồ, mixed-language, domain đa nghĩa và out-of-domain.

## 7. Phạm vi chưa xác minh

Không chạy test, benchmark, Docker build hoặc gọi provider/Redis/Supabase trong lượt này. Vì vậy các nhận định về model path được suy ra từ path/config trong mã; cần xác nhận cuối bằng image build và container runtime. Không có số liệu mới để kết luận độ chính xác detector, chất lượng dịch hay latency đã cải thiện.
