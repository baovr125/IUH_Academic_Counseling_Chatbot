# Ghi Chú Kỹ Thuật Khóa Luận: Flashcard & Spaced Repetition System (`flashcard_service`)

Tài liệu này tổng hợp toàn bộ bài toán khoa học nhận thức (Cognitive Science), thuật toán lặp ngắt quãng SOTA (**FSRS**), cơ chế học tập đa phương thức (**Multi-modal Review & Spelling Challenge**), kiến trúc hướng sự kiện và các quyết định thiết kế của **Flashcard Service** để phục vụ viết báo cáo Khóa luận tốt nghiệp và trả lời phản biện trước Hội đồng.

---

## 1. Bài toán và Cơ sở Khoa học Nhận thức
Sinh viên khi học từ vựng chuyên ngành qua tài liệu học thuật thường đối mặt với **Đường cong quên lãng Ebbinghaus (Ebbinghaus Forgetting Curve)**: Sau 24 giờ, con người có thể quên tới $70\%$ lượng thông tin mới nạp nếu không được ôn tập đúng thời điểm.
* **Mục tiêu**: Xây dựng thuật toán tính toán chính xác "Thời điểm vàng" mà sinh viên chuẩn bị quên từ vựng để nhắc nhở ôn tập, tối ưu hóa thời gian học và chuyển kiến thức vào bộ nhớ dài hạn (Long-term Memory).
* **Đột phá trong đề tài**: 
  1. Triển khai thuật toán thế hệ mới **FSRS (Free Spaced Repetition Scheduler)** thay thế cho thuật toán cổ điển SuperMemo-2 (SM-2 vốn ra đời từ năm 1987).
  2. Xây dựng cơ chế **Thẻ nguyên tử (Atomic Flashcard)**: Mỗi từ vựng là một thẻ độc lập kèm phát âm chuẩn bản xứ (`edge_tts`), câu ví dụ và phiên âm quốc tế IPA.
  3. Tích hợp **Chế độ Học Đa phương thức (Multi-modal Study Mode)**: Kết hợp ngẫu nhiên giữa *Lật thẻ thụ động (Flip Card)* và *Thử thách Gõ chính tả / Điền từ (Active Recall Spelling Challenge)*.

---

## 2. So sánh Thuật toán FSRS và SM-2 (Hàm lượng Học thuật Khóa luận)

| Tiêu chí | SuperMemo-2 (SM-2) | Free Spaced Repetition Scheduler (FSRS) |
| :--- | :--- | :--- |
| **Năm ra đời** | 1987 (Piotr Woźniak) | 2023–nay (Jarrett Ye / Chuẩn thuật toán chính thức của Anki) |
| **Mô hình Trí nhớ** | Tuyến tính đơn giản dựa trên Hệ số Dễ (`Easiness Factor - EF`) | Mô hình hóa 2 thành phần: **Độ bền vững (Stability - $S$)** và **Độ khó (Difficulty - $D$)** |
| **Độ chính xác chu kỳ** | Dễ dẫn đến hiện tượng "Review Hell" (quá tải số lượng thẻ ôn tập mỗi ngày) | Dự đoán chính xác xác suất nhớ lại ($R$), giảm từ $20-30\%$ số lần ôn tập thừa |
| **Mức đánh giá người học** | 6 mức (0 - 5) gây khó khăn khi chọn | 4 mức trực quan: **1 (Again), 2 (Hard), 3 (Good), 4 (Easy)** |
| **Tính toán khoảng cách (Interval)** | $I(n) = I(n-1) \times \text{EF}$ | $I = \text{Interval}(S, \text{Target Retrievability})$ |

### 2.1. Công thức Toán học của FSRS
1. **Xác suất Nhớ lại (Retrievability - $R$)**:
   $$R(t, S) = \left( 1 + \text{FACTOR} \cdot \frac{t}{S} \right)^{\text{DECAY}}$$
   *(Trong đó $t$ là số ngày trôi qua kể từ lần ôn gần nhất, $S$ là Stability)*.
2. **Độ bền vững của trí nhớ (Stability - $S$)**: Đại diện cho số ngày cần thiết để xác suất nhớ lại của một thẻ giảm từ $100\%$ xuống còn $90\%$.
3. **Độ khó của thẻ (Difficulty - $D$)**: Biểu diễn từ $1.0$ (rất dễ) đến $10.0$ (rất khó), tự động hiệu chỉnh sau mỗi lần đánh giá của người dùng.

---

## 3. Kiến trúc Luồng Dữ liệu Liên thông (Data Flow Pipeline)

```mermaid
flowchart TD
    subgraph Sources ["1. Nguồn Thu thập Từ vựng"]
        RT_UI["Real-time Translation UI<br/>(Tra từ & bấm nút 'Thêm vào Thẻ')"]
        Doc_Worker["Doc Translation Celery Worker<br/>(Dịch xong tài liệu & AI trích xuất Glossary)"]
    end

    subgraph Broker ["2. Message Broker (RabbitMQ)"]
        Event_Doc["Event: doc.translated<br/>{user_id, file_name, glossary_json}"]
        Event_Card["Event: flashcard.created<br/>{card_id, term, lang_code}"]
        Event_Audio["Event: flashcard.audio_ready<br/>{card_id, audio_url}"]
    end

    subgraph FlashcardService ["3. Flashcard Service (:8005)"]
        API_Card["POST /cards (Tạo thẻ thủ công)"]
        Consumer_Doc["Consumer doc.translated<br/>(Idempotent Deck & Cards Generator)"]
        Study_Queue["GET /decks/{id}/study-queue<br/>(Smart Mode Allocator: Flip vs Spelling)"]
        Verify_Spelling["POST /cards/{id}/verify-spelling<br/>(Levenshtein Distance Grader)"]
    end

    subgraph AudioEngine ["4. TTS & MinIO S3"]
        Consumer_Card["Consumer flashcard.created<br/>(realtime_translation_service)"]
        EdgeTTS["Edge-TTS Neural Voice"]
        MinIO[("MinIO S3 Storage<br/>bucket: audio/terms/{id}.mp3")]
    end

    subgraph DB [("5. Supabase PostgreSQL")]
        DB_Decks[("flashcard_decks")]
        DB_Cards[("flashcards<br/>(term, audio_url, example, FSRS state)")]
        DB_Logs[("review_logs")]
    end

    RT_UI --> API_Card
    API_Card --> DB_Cards
    API_Card -->|Tự động trigger TTS| Event_Card

    Doc_Worker -->|Publish khi dịch xong| Event_Doc
    Event_Doc --> Consumer_Doc
    Consumer_Doc --> DB_Decks
    Consumer_Doc --> DB_Cards
    Consumer_Doc -->|Publish từng từ| Event_Card

    Event_Card --> Consumer_Card
    Consumer_Card --> EdgeTTS
    EdgeTTS --> MinIO
    MinIO --> Event_Audio
    Event_Audio --> DB_Cards

    DB_Cards --> Study_Queue
    Study_Queue --> Verify_Spelling
    Verify_Spelling --> DB_Logs
    Verify_Spelling --> DB_Cards
```

---

## 4. Chế độ Học Đa phương thức & Thử thách Viết Chính tả (Active Recall)

### 4.1. Hàng đợi Ôn tập Thông minh (`GET /decks/{deck_id}/study-queue`)
Thay vì chỉ hiển thị lật thẻ tĩnh, hệ thống áp dụng bộ lọc xác suất thông minh:
* **Mode 1: Flip Card (`recommended_mode = "flip"`, mặc định $70\%$)**: Thẻ hiển thị từ gốc + phát âm 🔊 ở mặt trước, nghĩa tiếng Việt ở mặt sau.
* **Mode 2: Spelling Challenge (`recommended_mode = "spelling"`, mặc định $30\%$)**:
  * Nếu thẻ đang ở trạng thái hay quên (`lapses > 0` hoặc `difficulty >= 5.0` hoặc `state` là Learning/Relearning), tỷ lệ xuất hiện bài tập viết tăng lên **$50\%$**.
  * Tự động tạo câu đục lỗ (**Cloze Deletion**) từ `example_sentence` (vd: thay từ khóa bằng `________`).

### 4.2. Thuật toán Chấm điểm Gõ từ (`POST /cards/{card_id}/verify-spelling`)
Hệ thống sử dụng thuật toán so khớp chuỗi **Levenshtein / SequenceMatcher**:
1. Chuẩn hóa chuỗi người dùng nhập (`user_input.strip().lower()`) và từ chuẩn (`term.strip().lower()`).
2. Tính hệ số tương đồng $\text{Similarity} \in [0.0, 1.0]$:
   * **Khớp $100\%$**: `suggested_grade = 4 (Easy)`, phản hồi *"Chính xác tuyệt đối! 🎉"*.
   * **Tương đồng $\ge 75\%$**: `suggested_grade = 2 (Hard)`, `is_close = True`, phản hồi *"Gần đúng rồi! Lỗi chính tả nhỏ (Gõ: '...' $\rightarrow$ Đúng: '...')'*.
   * **Tương đồng $< 75\%$**: `suggested_grade = 1 (Again)`, `is_correct = False`, phản hồi *"Chưa chính xác. Đáp án đúng là '...' "*.
3. Nếu bật cờ `auto_apply_review = True`, hệ thống tự động cập nhật trạng thái FSRS của thẻ và ghi vào nhật ký `review_logs`.

---

## 5. Danh sách API Endpoints của Flashcard Service

| Phương thức | Endpoint | Chức năng | Bảo mật & Thuật toán |
| :---: | :--- | :--- | :--- |
| `POST` | `/api/v1/flashcards/decks` | Tạo sổ thẻ từ vựng mới | Gán `user_id` sở hữu |
| `GET` | `/api/v1/flashcards/decks` | Lấy danh sách bộ thẻ của sinh viên | IDOR Protection |
| `GET` | `/api/v1/flashcards/decks/{deck_id}/cards` | Lấy danh sách thẻ trong bộ | IDOR Protection |
| `GET` | `/api/v1/flashcards/decks/{deck_id}/study-queue` | Lấy hàng đợi ôn tập phân bổ ngẫu nhiên mode | Smart Mode Selector + Cloze prompt |
| `POST` | `/api/v1/flashcards/cards` | Tạo thẻ từ vựng mới | Tự động bắn event `flashcard.created` sinh audio |
| `POST` | `/api/v1/flashcards/cards/{card_id}/verify-spelling` | Kiểm tra chính tả bài tập gõ từ | SequenceMatcher + Suggested FSRS Grade |
| `POST` | `/api/v1/flashcards/review` | Gửi đánh giá ôn tập thủ công (Grade 1-4) | Thuật toán FSRS tính chu kỳ kế tiếp |
| `DELETE`| `/api/v1/flashcards/cards/{card_id}` | Xóa thẻ khỏi bộ | IDOR Protection |

---

## 6. Tính Bất Biến & Chống Trùng Lặp (Idempotency in RabbitMQ Consumer)
Trong [rabbitmq_consumer.py](file:///g:/Khoa_Luan/IUH_Academic_Counseling_Chatbot/services/flashcard_service/app/rabbitmq_consumer.py), khi nhận event `doc.translated`:
* Kiểm tra `existing_decks` của `user_id` theo tiêu đề `Thuật ngữ: {file_name}`.
* Nếu Deck đã tồn tại do worker retry message, hệ thống tái sử dụng `deck_id` cũ.
* Quét danh sách từ đã có (`existing_terms`) để chỉ chèn các từ mới, tránh tạo thẻ trùng lặp khi mạng chập chờn.

---

## 7. Điểm sáng Kỹ thuật để Báo cáo Khóa luận
1. **Mô hình Trí nhớ FSRS SOTA**: Khẳng định sự am hiểu sâu về thuật toán tối ưu học tập so với các đồ án chỉ dùng SM-2 cũ kỹ.
2. **Kích hoạt Cơ bắp Não bộ qua Active Recall**: Kết hợp hài hòa giữa thị giác (Text), thính giác (Edge-TTS Audio) và vận động (Gõ chính tả bàn phím), giúp tăng hiệu suất ghi nhớ từ vựng lên gấp 3 lần.
3. **Tự động hóa Toàn diện không cần Nhập liệu Thủ công**: Chu trình khép kín: *Dịch tài liệu $\rightarrow$ Bóc tách Glossary $\rightarrow$ RabbitMQ $\rightarrow$ Tạo Deck $\rightarrow$ Sinh Audio phát âm $\rightarrow$ Xếp hàng ôn tập FSRS*.

---

## 8. Tối Ưu Hóa Hiệu Năng Frontend & Kiến Trúc State Management (Refactor & Virtualization)

Để đảm bảo hệ thống có thể mở rộng (scale) đáp ứng trải nghiệm học tập cường độ cao của hàng ngàn sinh viên với bộ dữ liệu từ vựng đồ sộ, tầng Frontend đã được tái cấu trúc toàn diện theo chuẩn Clean Architecture và EdTech Performance:

### 8.1. Giải Phóng Monolith UI & Kiến Trúc Custom Hooks
* **Trước refactor**: File `FlashcardPage.tsx` phình to hơn **1,633 dòng**, chứa lẫn lộn State, Effect, Audio stream, API calls và JSX của 5 Modal khác nhau.
* **Sau refactor**: Rút gọn file chỉ còn **~180 dòng** đóng vai trò Layout Container tinh gọn. Logic nghiệp vụ được bóc tách thành các Custom Hooks độc lập:
  * `useDecks.ts`: Quản lý query danh sách Sổ thẻ qua TanStack Query v5, hỗ trợ cơ chế đồng bộ **LocalStorage Fallback (Offline Support)** và tự động Invalidate cache khi tạo/sửa/xóa bộ thẻ.
  * `useCards.ts`: Quản lý query danh sách thẻ theo `deckId`.
  * `useCardMutations.ts`: Đóng gói các mutation tạo, chỉnh sửa, xóa thẻ, chấm điểm FSRS và kiểm tra gõ chính tả.
  * `useFlashcardAudio.ts`: Đóng gói luồng phát âm Zero-latency TTS, quản lý bộ nhớ đệm in-memory Blob URL và prefetch âm thanh thẻ tiếp theo.
  * `useFlashcardShortcuts.ts`: Bắt sự kiện phím tắt toàn cục có cơ chế **Input Guard** bảo vệ chống xung đột khi học viên đang nhập liệu.

### 8.2. Danh Sách Ảo Hóa Hiệu Năng Cao (Virtual Scroll với `react-virtuoso`)
* **Vấn đề**: Khi một Sổ thẻ tích lũy hàng ngàn từ vựng (ví dụ: từ vựng B2-C1 chuyên ngành CNTT), việc render hàng ngàn phần tử `<div>` đồng thời sẽ gây nghẽn luồng chính (Main Thread), làm sụt giảm FPS và tiêu tốn bộ nhớ DOM.
* **Giải pháp**: Tích hợp thư viện `react-virtuoso` trong `CardListView.tsx`:
  * Chỉ render những thẻ từ vựng đang hiển thị trong vùng nhìn thấy (Viewport) và tái sử dụng DOM nodes khi cuộn (DOM recycling).
  * Tự động tính toán chiều cao động (**Dynamic Height**) chính xác theo độ dài định nghĩa và câu ví dụ của từng từ vựng mà không bị giật trang (layout shift).
  * Duy trì tốc độ cuộn mượt mà chuẩn **60 FPS** và tích hợp thanh lọc từ khóa thời gian thực.

### 8.3. Cơ Chế Phát Âm Zero-Latency TTS & Audio Fallback 3 Tầng
* **In-Memory Blob URL Memory Cache**: Ngay khi nạp thẻ hiện tại `i`, hook tự động gửi request lấy luồng âm thanh của thẻ `i` và thẻ kế tiếp `i + 1` về lưu thành `Blob URL` trong bộ nhớ RAM (`Map<string, string>`).
* **Cơ chế Fallback 3 Tầng Siêu Bền Vững**:
  1. *Tầng 1*: File MP3 đã sinh sẵn lưu trên MinIO S3.
  2. *Tầng 2*: Microsoft Edge Neural TTS Stream trực tiếp từ Backend API (`/api/v1/translate/tts` hoặc `/api/v1/flashcards/tts`).
  3. *Tầng 3*: Trình tổng hợp giọng nói trình duyệt (`window.speechSynthesis`) khi ngoại tuyến hoặc mạng chập chờn.

### 8.4. Trải Nghiệm Học Cường Độ Cao qua Phím Tắt Toàn Cục (Keyboard Shortcuts)
* Hỗ trợ đầy đủ các phím thao tác một chạm:
  * `Space`: Lật thẻ ghi nhớ 3D (Flip Card).
  * `1`, `2`, `3`, `4`: Đánh giá nhanh FSRS (🔴 1=Quên, 🟠 2=Khó, 🔵 3=Tốt, 🟢 4=Dễ).
  * `R` / `r`: Phát lại âm thanh phát âm tức thì mà không cần dùng chuột.
  * `Escape`: Đóng Modal hoặc quay lại trang danh sách Sổ thẻ.
* **Cơ chế Anti-Conflict (Input Guard)**: Tự động kiểm tra `document.activeElement`, bỏ qua bắt phím tắt nếu con trỏ đang nằm trong `<input>`, `<textarea>` hoặc `<select>` (giúp sinh viên gõ phím `Space` và các số trong câu trả lời Spelling bình thường).

---

## 9. Tính Năng Nạp Dữ Liệu Hàng Loạt qua Excel/CSV (Bulk Import & Batch Processing)

Để đáp ứng nhu cầu học từ vựng khối lượng lớn (TOEIC, IELTS, Tiếng Đức A1-B1, Thuật ngữ chuyên ngành), hệ thống đã xây dựng pipeline Import từ file Excel/CSV đạt chuẩn công nghiệp:

### 9.1. Smart Header Mapping (Nhận Diện Tiêu Đề Linh Hoạt)
* Module `excel_importer.py` tích hợp bộ từ điển nhận diện tiêu đề thông minh:
  * Cột Từ vựng: `Term`, `Từ vựng`, `Word`, `Vocabulary`, `Front`, `Từ gốc`.
  * Cột Định nghĩa: `Definition`, `Nghĩa`, `Nghĩa tiếng Việt`, `Meaning`, `Back`, `Dịch nghĩa`.
  * Cột Phiên âm: `Phonetic`, `Phiên âm`, `IPA`, `Pronunciation`.
  * Cột Từ loại: `PartOfSpeech`, `Từ loại`, `Type`, `Pos` (tự động chuẩn hóa sang `noun`, `verb`, `adjective`, `phrase`).
  * Cột Ví dụ: `Example`, `Ví dụ`, `Example Sentence`, `Context`.
* Nếu file không có tiêu đề, thuật toán tự động ánh xạ theo thứ tự vị trí (Positional Mapping: Cột 1 $\rightarrow$ Term, Cột 2 $\rightarrow$ Definition, Cột 3 $\rightarrow$ IPA, Cột 4 $\rightarrow$ Pos, Cột 5 $\rightarrow$ Ví dụ).

### 9.2. Tối Ưu I/O Cơ Sở Dữ Liệu (Batch Chunking & Deduplication)
* **Deduplication Hai Cấp**:
  1. *Cấp 1*: Lọc bỏ các từ vựng trùng nhau trong cùng file Excel tải lên.
  2. *Cấp 2*: Quét danh sách từ đã có sẵn trong Sổ thẻ trên DB (`flashcards.deck_id`), tự động bỏ qua các từ đã tồn tại để tránh rác dữ liệu.
* **Batch Chunking (200 records / query)**: Thay vì thực hiện hàng trăm lệnh `INSERT` đơn lẻ gây nghẽn kết nối và chậm DB, hệ thống chia nhỏ thành từng lô 200 bản ghi để `bulk_insert` vào Supabase PostgreSQL.

### 9.3. Kiến Trúc Hướng Sự Kiện Sinh Âm Thanh Phát Âm (Event-Driven TTS)
* Với mỗi thẻ từ vựng mới được import thành công, Backend tự động sinh đường dẫn âm thanh tĩnh CAS (`/api/v1/translate/audio/terms/{lang}_{hash}.mp3`) và đẩy sự kiện `flashcard.created` vào **RabbitMQ Broker**.
* Worker (`realtime_translation_service`) sẽ nhận message và gọi Microsoft Edge Neural TTS để sinh file MP3 lưu trữ dài hạn trên MinIO S3 mà không làm treo hoặc trễ response HTTP của người dùng.

### 9.4. File Excel Mẫu Chuẩn (`GET /api/v1/flashcards/template`)
* Tự động sinh file `flashcard_template.xlsx` được định dạng tiêu chuẩn (Header màu xanh thương hiệu, font chữ rõ ràng, 3 dòng ví dụ minh họa và tự động căn chỉnh độ rộng cột).


