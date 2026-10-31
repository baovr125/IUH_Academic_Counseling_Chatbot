# DANH MỤC HÌNH CỦA BÁO CÁO

Nguồn duy nhất của **chú thích chuẩn** cho từng hình. Sinh lần đầu từ mục 6.3 của `KE_HOACH_VIET_BAO_CAO.md` (30/10/2026).

- File PNG của hình `H4-13` nằm ở `figures/ch4/H4-13.png`; file nguồn (nếu vẽ bằng công cụ) ở `figures/src/ch4/H4-13.{mmd,puml,svg,py}`.
- **Ảnh giao diện (AC):** chụp xong thì lưu đè đúng tên file (ví dụ `figures/ch4/H4-23.png`). Script sẽ nhận ra đây là ảnh thật và không ghi đè.
- Cột *Trạng thái* do `python build/render_figures.py` tự cập nhật: `giữ chỗ` / `đã vẽ` / `ảnh thật`. Riêng `đã duyệt` do nhóm tự ghi, script giữ nguyên.
- Khi sửa chú thích ở đây, sửa luôn dòng `![Hình x.y. …]` trong bản thảo. `build_report.py` sẽ cảnh báo nếu hai nơi khác nhau.

## Chương 1

| Mã | Loại | Ưu tiên | Mục | Chú thích | Nguồn nội dung | Trạng thái |
|---|---|---|---|---|---|---|
| H1-01 | KT | A | 1.1 | Thông tin học vụ của IUH phân tán trên nhiều website và văn bản | `data_ingestion/sources.py` | đã vẽ |
| H1-02 | MH | A | bỏ (V2) | Ba nhu cầu của sinh viên và hướng hợp nhất trong một hệ thống | — | đã vẽ |
| H1-03 | KT | A | 1.3 | Tổng quan giải pháp: năm phân hệ và liên kết giữa chúng | README §1, §2.3 | đã vẽ |
| H1-04 | AC | B | bỏ (V2) | Giao diện bốn phân hệ chính của hệ thống | Phiên S | giữ chỗ |
| H1-05 | LĐ | A | bỏ (V2) | Quy trình nghiên cứu và phát triển của đề tài | README §8, `ci.yml` | đã vẽ |

## Chương 2

| Mã | Loại | Ưu tiên | Mục | Chú thích | Nguồn nội dung | Trạng thái |
|---|---|---|---|---|---|---|
| H2-01 | MH | A | 2.1.1 | Kiến trúc Transformer gồm bộ mã hóa và bộ giải mã (Vẽ lại theo [@vaswani2017]) | [EN] | đã vẽ |
| H2-02 | MH | A | 2.1.1 | Scaled dot-product attention (trái) và multi-head attention (phải) (Vẽ lại theo [@vaswani2017]) | [EN] | đã vẽ |
| H2-03 | MH | B | bỏ (V2) | Mô hình decoder-only sinh văn bản theo cơ chế tự hồi quy | — | đã vẽ |
| H2-04 | MH | B | bỏ (V2) | Bộ định tuyến Mixture-of-Experts chọn k chuyên gia cho mỗi token | Shazeer 2017 | đã vẽ |
| H2-05 | BĐ | A | bỏ (V2) | Phân phối xác suất của cùng một vector logit ở ba giá trị nhiệt độ (số liệu minh họa) | — | đã vẽ |
| H2-06 | BĐ | B | bỏ (V2) | Lấy mẫu top-p: tập hạt nhân là các token đầu tiên có xác suất tích lũy đạt p = 0,8 (số liệu minh họa) | — | đã vẽ |
| H2-07 | MH | B | bỏ (V2) | Cấu trúc prompt hệ thống của chatbot học vụ | `prompt_templates.py` | đã vẽ |
| H2-08 | MH | A | 2.1.4 | Ba hạn chế của LLM và hướng khắc phục trong đề tài | — | đã vẽ |
| H2-09 | MH | A | 2.2.1 | Kiến trúc RAG cơ bản gồm ba giai đoạn lập chỉ mục, truy xuất và sinh | Lewis 2020 | đã vẽ |
| H2-10 | MH | A | 2.2.1 | So sánh Naive RAG, Advanced RAG và Modular RAG (Vẽ lại theo [@gao2023rag]) | `paper/check_2312.10997v5.pdf` | đã vẽ |
| H2-11 | MH | A | 2.2.2 | Bi-Encoder mã hóa câu hỏi và văn bản độc lập, Cross-Encoder mã hóa chung một chuỗi | Reimers 2019 | đã vẽ |
| H2-12 | VD | B | bỏ (V2) | Không gian embedding: câu hỏi học vụ thật chiếu xuống 2 chiều (PCA), câu cùng chủ đề nằm gần nhau | câu hỏi trong `logs/academic_chatbot/`; mô hình bi-encoder cục bộ | giữ chỗ |
| H2-13 | MH | A | 2.2.3 | Đồ thị nhiều tầng của HNSW và đường tìm kiếm tham lam từ tầng trên xuống tầng 0 (số liệu minh họa) | Malkov 2018 | đã vẽ |
| H2-14 | MH | A | 2.2.4 | Hợp nhất hai danh sách xếp hạng bằng RRF với k = 60 (số liệu minh họa) | `schema_complete.sql` | đã vẽ |
| H2-15 | LĐ | B | bỏ (V2) | Các bước tìm kiếm toàn văn trong PostgreSQL với một câu hỏi ví dụ | `schema_complete.sql` | đã vẽ |
| H2-16 | MH | B | bỏ (V2) | Kỹ thuật trước truy xuất: viết lại câu hỏi, tách nhiều truy vấn, HyDE | `paper/` | giữ chỗ |
| H2-17 | BĐ | A | bỏ (V2) | Độ chính xác hỏi đáp theo vị trí của tài liệu chứa đáp án trong 20 tài liệu (Số liệu: [@liu2024lost], Bảng 6) | `paper/check2307.03172v3.pdf` | đã vẽ |
| H2-18 | MH | A | 2.2.5 | Truy xuất trên đoạn con, đưa đoạn cha vào ngữ cảnh (Small-to-Big) | — | đã vẽ |
| H2-19 | MH | B | bỏ (V2) | Luồng Self-RAG và CRAG | `paper/` | giữ chỗ |
| H2-20 | MH | B | bỏ (V2) | Ý tưởng semantic cache: so khớp theo nghĩa thay vì theo chuỗi | — | giữ chỗ |
| H2-21 | VD | A | 2.2.6 | Ba chiến lược phân đoạn áp dụng trên cùng một đoạn quy chế đào tạo (nguồn văn bản: camnang.iuh.edu.vn) | văn bản trong kho tri thức | đã vẽ |
| H2-22 | MH | B | bỏ (V2) | Ví dụ tính Hit@K, MRR, nDCG trên 3 câu hỏi (số liệu minh họa) | — | giữ chỗ |
| H2-23 | MH | A | bỏ (V2) | Mô hình mã hóa – giải mã với chú ý chéo cho bài toán dịch máy | NLLB 2022 | đã vẽ |
| H2-24 | MH | B | bỏ (V2) | Tìm kiếm chùm với B = 2 trên một câu ngắn (số liệu minh họa) | — | đã vẽ |
| H2-25 | MH | C | bỏ (V2) | NLLB-200: một mô hình cho nhiều cặp ngôn ngữ; mã `eng_Latn`, `vie_Latn`… | Realtime README §3.1 | giữ chỗ |
| H2-26 | BĐ | B | bỏ (V2) | Lượng tử hóa đối xứng INT8: giá trị gốc, giá trị khôi phục và sai số làm tròn (số liệu minh họa) | — | đã vẽ |
| H2-27 | LĐ ♻ | A | bỏ (V2) | Các bước nhận diện ngôn ngữ: luật theo hệ chữ, fastText, Lingua, fusion và hiệu chỉnh độ tin cậy | Realtime README §3.4, `LANGUAGE_DETECTION.md` | đã vẽ |
| H2-28 | LĐ | A | bỏ (V2) | Quy tắc quyết định chuyên ngành kết hợp lời khai của LLM với bằng chứng từ điển | `DOMAIN_DETECTION.md` §3 | đã vẽ |
| H2-29 | VD | B | bỏ (V2) | Thuật toán Lesk chọn nghĩa của từ “bank” trong hai ngữ cảnh khác nhau (kết quả chạy simple_lesk của pywsd trên WordNet) | WordNet | đã vẽ |
| H2-30 | MH | B | bỏ (V2) | Ví dụ so khớp n-gram khi tính BLEU | Papineni 2002 | giữ chỗ |
| H2-31 | BĐ | A | 2.4.1 | Khả năng nhớ khi không ôn và khi ôn theo lịch FSRS (tính bằng gói fsrs 6.3.2, mỗi lần ôn đều chọn Good) | tính bằng gói `fsrs` 6.3.2 | đã vẽ |
| H2-32 | MH | A | bỏ (V2) | Mô hình trí nhớ DSR: quan hệ giữa độ khó, độ ổn định và khả năng nhớ | Ye 2022 | đã vẽ |
| H2-33 | BĐ | A | bỏ (V2) | Khả năng nhớ R(t) theo FSRS với các độ ổn định S khác nhau (tính bằng gói fsrs 6.3.2, tham số mặc định) | `fsrs` 6.3.2 | đã vẽ |
| H2-34 | BĐ | A | bỏ (V2) | Khoảng ôn qua các lần ôn với bốn chuỗi đánh giá khác nhau (mô phỏng bằng gói fsrs 6.3.2, cấu hình như Flashcard Service, không fuzzing) | `fsrs` 6.3.2, tham số mặc định | đã vẽ |
| H2-35 | MH | A | 2.5.1 | Kiến trúc nguyên khối và kiến trúc microservices | Newman 2021 | đã vẽ |
| H2-36 | MH | A | bỏ (V2) | Mẫu cổng API: một điểm vào duy nhất đảm nhận các việc chung trước khi chuyển yêu cầu tới service | — | đã vẽ |
| H2-37 | BĐ | B | bỏ (V2) | Giới hạn tần suất theo cửa sổ cố định với L = 10 yêu cầu/phút và hiện tượng dồn yêu cầu ở ranh giới cửa sổ (số liệu minh họa) | — | đã vẽ |
| H2-38 | TT | A | bỏ (V2) | Ba kiểu giao tiếp REST, SSE và hàng đợi thông điệp trên trục thời gian | — | đã vẽ |
| H2-39 | MH | A | bỏ (V2) | Exchange loại topic của RabbitMQ chuyển thông điệp tới hàng đợi theo khóa định tuyến (khóa và hàng đợi lấy từ mã nguồn) | — | đã vẽ |
| H2-40 | MH | B | bỏ (V2) | Lưu trữ định địa chỉ theo nội dung: cùng một từ luôn cho cùng một khóa nên âm thanh chỉ được sinh một lần | — | đã vẽ |
| H2-41 | MH | A | bỏ (V2) | Cấu trúc JWT của hệ thống: header, payload với các claim thật và chữ ký HS256 | `utils/security.py` | đã vẽ |
| H2-42 | KT | A | 2.6 | Bản đồ công nghệ của hệ thống theo tầng | README §4 | đã vẽ |
| H2-43 | MH | B | bỏ (V2) | Dòng thời gian các kỹ thuật RAG liên quan và mức độ áp dụng trong đề tài | `paper/` | đã vẽ |

## Chương 3

| Mã | Loại | Ưu tiên | Mục | Chú thích | Nguồn nội dung | Trạng thái |
|---|---|---|---|---|---|---|
| H3-01 | KT | A | bỏ (V2) | Sơ đồ ngữ cảnh: tác nhân, hệ thống và các dịch vụ bên ngoài | `AppRouter.tsx`, `kong.template.yml` | đã vẽ |
| H3-02 | UC | A | 3.2.1 | Sơ đồ use case tổng quát của hệ thống | — | đã vẽ |
| H3-03 | UC | A | PL B | Sơ đồ use case phân hệ Xác thực | `routers/*.py` | đã vẽ |
| H3-04 | UC | A | 3.2.2 | Sơ đồ use case phân hệ Chatbot học vụ | `routers/*.py` | đã vẽ |
| H3-05 | UC | A | PL B | Sơ đồ use case phân hệ Dịch thuật | `routers/*.py` | đã vẽ |
| H3-06 | UC | A | PL B | Sơ đồ use case phân hệ Flashcard | `routers/*.py` | đã vẽ |
| H3-07 | UC | A | PL B | Sơ đồ use case phân hệ Quản trị | `routers/*.py` | đã vẽ |
| H3-08a | TT | A | bỏ (V2) | Sơ đồ tuần tự UC01 Đăng ký tài khoản | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-08b | TT | A | bỏ (V2) | Sơ đồ tuần tự UC02 Đăng nhập | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-09 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC03 Làm mới phiên và đăng xuất | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-10 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC04 Quản lý hồ sơ, mật khẩu và cài đặt | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-11 | TT | A | 3.2.2 | Sơ đồ tuần tự UC05 Hỏi đáp học vụ (mức tổng quan) | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-12 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC06 Quản lý phiên hội thoại | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-13 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC07–UC08 Dịch văn bản và dịch theo chuyên ngành | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-14 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC09 Phân tích từ và nghe phát âm | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-15 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC10 Lưu từ thành thẻ học | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-16 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC11 Quản lý sổ thẻ và thẻ | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-17 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC12 Ôn tập theo FSRS | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-18 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC13 Sinh từ vựng bằng AI | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-19 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC14 Dùng bộ từ mẫu và nhập Excel | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-20 | TT | A | 3.2.3 | Sơ đồ tuần tự UC16 Nạp tri thức | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-21 | TT | A | bỏ (V2) | Sơ đồ tuần tự UC17–UC18 Quản lý tài liệu tri thức và từ điển chuyên ngành | `routers/*.py`, `services/*.py` | đã vẽ |
| H3-22 | HĐ | A | bỏ (V2) | Sơ đồ hoạt động UC12 Ôn tập theo FSRS | `fsrs_algorithm.py`, `StudyMode.tsx` | đã vẽ |
| H3-23 | HĐ | A | bỏ (V2): H4-01 thay thế | Sơ đồ hoạt động UC16 Nạp tri thức | `routers/admin_ingest.py` | đã vẽ |
| H3-24 | HĐ | B | bỏ (V2) | Sơ đồ hoạt động UC15 Trò chơi ôn từ (chấm điểm phía máy chủ) | `game_service.py`, `game_logic.py` | đã vẽ |
| H3-25 | KT ♻ | A | 3.3.1 | Kiến trúc tổng thể của hệ thống ở mức container | README §2.1 | đã vẽ |
| H3-26 | TT ♻ | A | bỏ (V2) | Các bước xử lý một yêu cầu tại Kong | gateway README §2 | đã vẽ |
| H3-27 | KT | A | bỏ (V2) | Ba kiểu giao tiếp trong hệ thống | README §2.2 | đã vẽ |
| H3-28 | TT ♻ | A | bỏ (V2) | Exchange, khóa định tuyến và hàng đợi của RabbitMQ | README §2.3 | đã vẽ |
| H3-29 | KT | A | bỏ (V2) | Kiến trúc phân lớp bên trong một service | README §9 | đã vẽ |
| H3-30 | Triển khai (PlantUML) | A | 3.3.4 | Sơ đồ triển khai của bản demo công khai | `docker-compose*.yml` | đã vẽ |
| H3-31 | KT | A | bỏ (V2) | Phân chia bảng theo service | db README §3 | đã vẽ |
| H3-32 | ERD ♻ | A | 3.4.1 | ERD tổng thể của hệ thống | db README §4 | đã vẽ |
| H3-33 | ERD | A | 3.4.2 | ERD nhóm bảng tri thức RAG | `schema_complete.sql`, `migrations/003–007` | đã vẽ |
| H3-34 | ERD | A | PL E | ERD nhóm bảng người dùng và hội thoại | `schema_complete.sql`, `migrations/003–007` | đã vẽ |
| H3-35 | ERD | A | PL E | ERD nhóm bảng Flashcard | `schema_complete.sql`, `migrations/003–007` | đã vẽ |
| H3-36 | ERD | A | bỏ (V2) | Lưu trữ của phân hệ Dịch thuật | `schema_complete.sql`, `migrations/003–007` | đã vẽ |
| H3-37 | LĐ | B | PL E | Chỉ mục và luồng xử lý của hàm match_chunks_hybrid_rrf | `schema_complete.sql` | đã vẽ |
| H3-38 | MH | B | PL C | Cấu trúc phản hồi thành công và các dạng phản hồi lỗi | README §9 | đã vẽ |
| H3-39 | TT | A | PL C | Dòng sự kiện SSE của endpoint hỏi đáp | Chatbot README §3 | đã vẽ |
| H3-40 | TT ♻ | A | bỏ (V2) | Vòng đời phiên đăng nhập và token | Auth README §4.2 | đã vẽ |
| H3-41 | KT | A | bỏ (V2) | Các lớp phòng thủ của hệ thống | README §6, Auth README §9 | đã vẽ |
| H3-42 | LĐ | A | 3.7 | Sơ đồ điều hướng và phân quyền route | `AppRouter.tsx` | đã vẽ |
| H3-43 | MH | B | bỏ (V2) | Các thành phần của hệ thống thiết kế giao diện | `assets/brand/`, `tailwind.config.*` | đã vẽ |
| H3-44 | AC | B | 4.4 (dùng lại) | Trang đăng nhập ở ba độ rộng màn hình 360, 768 và 1 280 px | `screenshots-responsive/theme-after/light/login-*.png` | đã vẽ |

## Chương 4

| Mã | Loại | Ưu tiên | Mục | Chú thích | Nguồn nội dung | Trạng thái |
|---|---|---|---|---|---|---|
| H4-01 | LĐ ♻ | A | 4.1 | Pipeline thu thập và xử lý tri thức | `data_ingestion/` (đối chiếu mã 31/10/2026) | đã vẽ |
| H4-02 | MH | A | 4.1.1 | Thu thập URL: sitemap, danh mục, BFS theo độ sâu cho từng domain | `sources.py`, `crawlers/` | bỏ (V2) |
| H4-03 | VD | A | 4.1.2 | Trang HTML gốc và văn bản sạch sau trafilatura, đặt cạnh nhau | một trang camnang thật | bỏ (V2) |
| H4-04 | LĐ | B | 4.1.2 | Nhánh PDF: PyMuPDF → OCR (Gemini, Tesseract dự phòng) | `extractors/` | bỏ (V2) |
| H4-05 | LĐ ♻ | A | 4.1.3 | HybridChunker | Ingestion README §3.4 | bỏ (V2) |
| H4-06 | VD | A | 4.1.3 | Một đoạn cha thật được tách thành 10 đoạn con (chạy HybridChunker của hệ thống) | `_data/H4-06_run_chunk.py` | đã vẽ |
| H4-07 | BĐ | A | 4.1.6 | Thống kê kho tri thức theo nguồn và loại tài liệu | truy vấn Supabase | bỏ (V2) |
| H4-08 | AC | A | 4.1.5 | Giao diện nạp tri thức và theo dõi tiến độ | Phiên S | giữ chỗ |
| H4-09 | KT ♻ | A | 4.2 | Kiến trúc Academic Chatbot Service | Chatbot README §2 | bỏ (V2) |
| H4-10 | KT | A | 4.2.1 | Pipeline đầy đủ của một câu hỏi | Chatbot README §3–4 | bỏ (V2) |
| H4-11a | TT ♻ | A | 4.2.1 | Tuần tự xử lý POST /messages/stream (1): tiếp nhận, định tuyến và tra cứu bộ nhớ đệm | Chatbot README §3 | đã vẽ |
| H4-11b | TT ♻ | A | 4.2.1 | Tuần tự xử lý POST /messages/stream (2): truy xuất, sinh câu trả lời và lưu kết quả | Chatbot README §3 | đã vẽ |
| H4-12 | LĐ + VD | A | 4.2.2 | Guardrail: các nhóm luật và ví dụ câu bị chặn | `guardrails/query_filter.py` và test | bỏ (V2) |
| H4-13 | VD | A | 4.2.3 | Ví dụ bộ định tuyến viết lại và tách một câu hỏi thật (log ngày 29/10/2026) | `logs/academic_chatbot/2026-10-29/142502-quy-trinh-ang-ky-hoc.md` | đã vẽ |
| H4-14 | LĐ ♻ | A | 4.2.4 | Bộ nhớ đệm ngữ nghĩa hai tầng và cổng chất lượng khi ghi | Chatbot README §4.3 | đã vẽ |
| H4-15 | VD | B | 4.2.4 | Ví dụ một lượt cache hit thật | log `…-CACHE-HIT-…md` | bỏ (V2) |
| H4-16 | LĐ ♻ | A | 4.2.5 | Truy xuất lai và xếp hạng lại đa truy vấn | Chatbot README §4.4 | đã vẽ |
| H4-17 | VD | A | 4.2.5 | Ví dụ thật: các chunk được chọn, điểm rerank, sub-query và nguồn | log 29/10/2026 | bỏ (V2) |
| H4-18 | MH | A | 4.2.6 | Sắp xếp Sandwich: thứ tự chunk trước và sau | `llm_generation_service.py` | bỏ (V2) |
| H4-19 | VD | A | 4.2.6 | Khung prompt gửi tới LLM và vị trí các thẻ cách ly (minh họa với 5 đoạn cha) | `prompt_templates.py` | đã vẽ |
| H4-20 | LĐ ♻ | A | 4.2.7 | Lớp nhà cung cấp LLM và chuỗi dự phòng | Chatbot README §4.7 | bỏ (V2) |
| H4-21 | VD | A | 4.2.8 | Văn bản mô hình sinh ra và phần được gửi tới giao diện (log ngày 29/10/2026) | log 29/10/2026 | đã vẽ |
| H4-22 | BĐ | B | 4.2.8 | Phân rã độ trễ của một lượt hỏi (router, truy xuất, sinh), ghi rõ là một lượt chạy | log 29/10/2026 | bỏ (V2) |
| H4-23 | AC | A | 4.2 | Giao diện hỏi đáp khi câu trả lời đang được sinh (streaming) | Phiên S | bỏ (V2) |
| H4-24 | AC | A | 4.2.8 | Giao diện hỏi đáp: câu trả lời kèm trích dẫn nguồn | Phiên S | giữ chỗ |
| H4-25 | AC | A | 4.2.10 | Danh sách phiên hội thoại | Phiên S | bỏ (V2) |
| H4-26 | KT ♻ | A | 4.3 | Kiến trúc Realtime Translation Service | Realtime README §2 | bỏ (V2) |
| H4-27 | LĐ ♻ | A | 4.3.1 | Luồng dịch thường `POST /text` | Realtime README §3.1 | bỏ (V2) |
| H4-28 | TT | A | 4.3.1 | Thứ tự xử lý và sự kiện của endpoint dịch streaming | router dịch, `DOMAIN_DETECTION.md` §2 | đã vẽ |
| H4-29 | VD | B | 4.3.2 | Ví dụ nhận diện văn bản trộn nhiều ngôn ngữ | `LANGUAGE_DETECTION.md` §7 | bỏ (V2) |
| H4-30 | LĐ ♻ | A | 4.3.3 | Dịch theo chuyên ngành | Realtime README §3.3 | bỏ (V2) |
| H4-31 | VD | A | 4.3.3 | Ví dụ: thuật ngữ từ điển được chèn vào prompt và kết quả dịch | gọi API thật | bỏ (V2) |
| H4-32 | LĐ ♻ | A | 4.3.5 | TTS và kho âm thanh CAS | Realtime README §3.6 | bỏ (V2) |
| H4-33 | AC | A | 4.3.1 | Giao diện Translation Studio | Phiên S | giữ chỗ |
| H4-34 | AC | A | 4.3.3 | Chọn chuyên ngành và thông báo kết quả nhận diện chuyên ngành | Phiên S | bỏ (V2) |
| H4-35 | AC | A | 4.3.4 | Cửa sổ phân tích từ (WordAnalysisPopup) | Phiên S | bỏ (V2) |
| H4-36 | AC | A | 4.3.6 | Giao diện quản trị từ điển chuyên ngành | Phiên S | bỏ (V2) |
| H4-37 | KT ♻ | A | 4.4 | Kiến trúc Flashcard Service | Flashcard README §2 | bỏ (V2) |
| H4-38 | TTh | A | 4.4.2 | Trạng thái thẻ thực tế trong hệ thống: New → Review; Again giữ ở Review và tăng `lapses`. Đặt cạnh mô hình 4 trạng thái của FSRS để so sánh | gói `fsrs` 6.3.2, `fsrs_algorithm.py` | bỏ (V2) |
| H4-39 | VD | B | 4.4.2 | Một thẻ cụ thể: 4 nút đánh giá cho ra 4 ngày ôn kế tiếp khác nhau | tính bằng `fsrs` | bỏ (V2) |
| H4-40 | LĐ ♻ | A | 4.4.4 | Pipeline sinh từ vựng bằng AI | Flashcard README §3.4 | đã vẽ |
| H4-41 | VD | A | 4.4.4 | Ví dụ đầu ra thật của pipeline: một thẻ JSON đã qua kiểm tra | `evaluation/results/topics_A.jsonl` | bỏ (V2) |
| H4-42 | LĐ | B | 4.4.5 | Clone-on-start bộ từ mẫu và nhập Excel | `excel_importer.py`, service catalog | bỏ (V2) |
| H4-43 | TT | B | 4.4.6 | Chấm điểm trò chơi phía máy chủ | `game_service.py` | bỏ (V2) |
| H4-44 | AC | A | 4.4.1 | Giao diện sổ thẻ | Phiên S | bỏ (V2) |
| H4-45 | AC | A | 4.4.2 | Phiên ôn tập: mặt trước, mặt sau và bốn nút đánh giá | Phiên S | giữ chỗ |
| H4-46 | AC | A | 4.4.4 | Sinh từ vựng bằng AI | Phiên S | bỏ (V2) |
| H4-47 | AC | A | 4.4.5 | Thư viện bộ từ mẫu | Phiên S | bỏ (V2) |
| H4-48 | AC | A | 4.4.6 | Bốn trò chơi ôn từ | Phiên S | bỏ (V2) |
| H4-49 | AC | A | 4.4.2 | Thống kê học tập và chuỗi ngày học | Phiên S | bỏ (V2) |
| H4-50 | LĐ | A | 4.5.1 | Lưu đồ đăng nhập: bcrypt luôn chạy, throttle hai tầng | `auth_service.py` | bỏ (V2) |
| H4-51 | TT | A | 4.5.2 | Cấp, làm mới, thu hồi token với `token_version` | `utils/security.py` | bỏ (V2) |
| H4-52 | KT | A | 4.5.3 | Chuỗi plugin của Kong theo thứ tự xử lý | `kong.template.yml` | bỏ (V2) |
| H4-53 | AC | A | 4.5 | Giao diện đăng nhập / đăng ký | Phiên S | bỏ (V2) |
| H4-54 | KT ♻ | A | 4.6.1 | Kiến trúc Document Translation (thử nghiệm, viền nét đứt) | doc_translation README §1 | bỏ (V2) |
| H4-55 | AC | B | 4.6.2 | Giao diện thể hiện chức năng dịch tài liệu đang khóa bằng cờ tính năng | Phiên S | bỏ (V2) |
| H4-56 | KT | A | 4.7.1 | Kiến trúc frontend: pages → components → hooks/context → services → API | frontend README §2 | bỏ (V2) |
| H4-57 | TT ♻ | A | 4.7.1 | Luồng chat SSE phía client | frontend README §4.2 | bỏ (V2) |
| H4-58 | AC | A | 4.7.2 | Dashboard (đánh dấu khối dữ liệu mẫu có `SampleDataBadge`) | Phiên S | bỏ (V2) |
| H4-59 | AC | B | 4.7.6 | Hồ sơ và Cài đặt | Phiên S | bỏ (V2) |
| H4-60 | AC | A | 4.7 | Responsive: cùng một trang ở 360 / 768 / 1280 px | Phiên S | bỏ (V2) |
| H4-61 | AC | B | 4.7 | Giao diện sáng và tối | Phiên S | bỏ (V2) |
| H4-62 | KT | A | 4.8.1 | Triển khai bằng Docker Compose: mạng, cổng, volume | `docker-compose*.yml` | bỏ (V2) |
| H4-63 | BĐ | B | 4.8.2 | Giới hạn RAM / CPU / GPU theo container (là cấu hình, không phải số đo) | các file compose | bỏ (V2) |
| H4-64 | LĐ | A | 4.8.3 | Pipeline CI trên GitHub Actions | `.github/workflows/ci.yml` | bỏ (V2) |
| H4-65 | KT ♻ | A | 4.8.4 | Demo công khai qua Tailscale Funnel | DEPLOY.md §2 | bỏ (V2) |

## Chương 5

| Mã | Loại | Ưu tiên | Mục | Chú thích | Nguồn nội dung | Trạng thái |
|---|---|---|---|---|---|---|
| H5-01 | BĐ | A | 5.2 | Số test và kết quả theo service | lần chạy `run_tests.sh all` | bỏ (V2) |
| H5-02 | BĐ | A | 5.2.1 | Hit@K và MRR theo cấu hình truy xuất (35 câu hỏi có đáp án) | `eval/run_retrieval_ablation.py` | đã vẽ |
| H5-03 | BĐ | B | 5.2.3 | Tỉ lệ trúng của bộ nhớ đệm với cặp diễn đạt lại và cặp khác con số | `eval/run_cache_eval.py` | đã vẽ |
| H5-04 | BĐ | B | 5.2.5 | Phân bố độ trễ từng giai đoạn của một lượt hỏi đáp | `eval/run_latency_eval.py` | đã vẽ |
| H5-05 | BĐ | A | 5.4 | Ma trận nhầm lẫn nhận diện ngôn ngữ | `tests/test_results/benchmark_language_detection_report.md` (**đã có**) | bỏ (V2) |
| H5-06 | BĐ | A | 5.4 | Kết quả nhận diện chuyên ngành | `benchmark_domain_detection_report.md` (**đã có**) | bỏ (V2) |
| H5-07 | BĐ | A | 5.4 | BLEU / chrF theo cặp ngôn ngữ | `evaluation/run_bleu_chrf.py` | bỏ (V2) |
| H5-08 | BĐ | A | 5.5 | Một lời gọi và pipeline 3 bước khi sinh từ vựng | `flashcard_service/evaluation/results/REPORT.md` (**đã có**) | bỏ (V2) |
| H5-09 | AC | C | 5.4 | Minh chứng e2e dịch chuyên ngành (ghi rõ là giao diện cũ) | `tests/e2e/screenshots/terminology/` | bỏ (V2) |
| H5-10 | BĐ | B | 5.7 | RAM / VRAM đo thực tế theo container | `docker stats` | bỏ (V2) |

## Chương 6

| Mã | Loại | Ưu tiên | Mục | Chú thích | Nguồn nội dung | Trạng thái |
|---|---|---|---|---|---|---|
| H6-01 | MH | B | 6.1 | Mức hoàn thành mục tiêu theo phân hệ |  | giữ chỗ |
| H6-02 | KT | A | 6.3.1 | Kiến trúc đề xuất để đưa Document Translation vào vận hành |  | giữ chỗ |
| H6-03 | MH | B | 6.3 | Lộ trình phát triển theo giai đoạn |  | giữ chỗ |
