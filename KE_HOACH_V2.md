# KẾ HOẠCH VIẾT BÁO CÁO – PHIÊN BẢN 2 (PHẦN CHÍNH ≤ 130 TRANG, TRỌNG TÂM CHATBOT)

Lập ngày 31/10/2026, điều chỉnh cùng ngày: phần chính giảm từ 145 xuống ≤ 130 trang. Tài liệu này thay cho các mục 3 (dàn ý chương), 5, 6.3 (danh mục hình) và 9 (phiên làm việc) của `KE_HOACH_VIET_BAO_CAO.md`. Các mục khác của kế hoạch cũ **vẫn áp dụng**, xem mục 8.

## 1. Quyết định của nhóm

| # | Quyết định | Cách hiểu khi thực hiện |
|---|---|---|
| 1 | **Phần chính không vượt quá 130 trang** | Phần chính tính từ trang đầu Chương 1 đến hết Tài liệu tham khảo (các trang đánh số Ả Rập). Ngân sách ở mục 2 cộng lại **124 trang**, chừa 6 trang dự phòng. Phần đầu và phụ lục không tính vào giới hạn này nhưng vẫn giữ gọn, để cả cuốn khoảng 170 trang. |
| 2 | **Trọng tâm là Academic Chatbot Service** | Chatbot gồm pipeline tri thức và pipeline hỏi đáp RAG. Phần này được trình bày sâu ở mọi chương: lý thuyết, đặc tả, thiết kế, cài đặt, đánh giá. |
| 3 | **Các service còn lại chỉ là phụ, nói sơ qua** | Gồm Dịch thuật, Flashcard, Auth/Kong, Frontend. Mỗi phân hệ có ngân sách cố định (mục 3). Không đặc tả use case chi tiết trong chương. Không có công thức, trừ 2 công thức lõi của FSRS. Dịch tài liệu chỉ còn 2–3 câu. |
| 4 | **Tận dụng tối đa phần đã viết** | Chương 1–3 không viết lại từ đầu mà rút gọn, gộp, chuyển ra phụ lục. Hình đã vẽ nhưng không dùng nữa vẫn giữ trong `figures/`, chỉ đánh dấu trong `FIGURES.md`. |

## 2. Ngân sách trang

| Phần | Hiện tại | Ngân sách | Ghi chú |
|---|---|---|---|
| Chương 1. Tổng quan | 13 | **8** | |
| Chương 2. Cơ sở lý thuyết | 72 | **24** | LLM 4, RAG 14, nền tảng phân hệ phụ 3, kiến trúc và công nghệ 2, nghiên cứu liên quan 1 |
| Chương 3. Phân tích và thiết kế | 47 | **22** | |
| Chương 4. Xây dựng hệ thống | — | **42** | Pipeline tri thức 9, chatbot 24, phân hệ phụ 6, web và triển khai 3 |
| Chương 5. Kiểm thử và đánh giá | — | **18** | Chatbot 10 |
| Chương 6. Kết luận | — | **4** | |
| Tài liệu tham khảo | 8 | **6** | Khoảng 55 tài liệu (nâng từ 4 lên 6 trang ở Phiên R2) |
| **Phần chính** | 140 | **124** | dự phòng 6, giới hạn 130 |
| Phần đầu (số La Mã) | — | ~14 | Danh mục hình ≤ 2 trang |
| Phụ lục A–F | 44 | ~30 | |
| Nhật ký làm việc | — | 2 | |
| **Cả cuốn** | | **~168** | |

Các giới hạn đi kèm:
- **Hình:** ≤ 56 hình, gồm 47 hình trong chương và 9 hình trong phụ lục.
- **Công thức:** ≤ 18.
- **Ảnh chụp giao diện:** 4 ảnh bắt buộc (mục 6).

## 3. Nguyên tắc viết

1. **Chatbot:** viết theo khuôn vấn đề → lưu đồ → giải pháp → cài đặt → ví dụ thật → nhận xét. Mỗi kỹ thuật tối đa 1 lưu đồ và 1 ví dụ.
2. **Phân hệ phụ:** mỗi phân hệ là một tiểu mục 2–3 trang, gồm:
   - một đoạn nêu vai trò;
   - các kỹ thuật chính dạng gạch đầu dòng, có tham số thật;
   - tối đa 1 sơ đồ và 1 ảnh giao diện.
3. **Không lặp nội dung giữa các chương.** Lý thuyết ở Chương 2, thiết kế ở Chương 3, cài đặt ở Chương 4. Chương sau nhắc lại bằng tham chiếu mục.
4. **Đưa ra phụ lục:** bảng cấu hình, danh sách endpoint, bảng thuộc tính CSDL, prompt đầy đủ, đặc tả use case phụ.
5. **Giải thích ký hiệu công thức viết thành câu văn,** không dùng danh sách gạch đầu dòng dài. Đây là nguyên nhân chính khiến Chương 2 hiện tại dài gấp đôi.
6. **Mọi mô tả kỹ thuật vẫn phải khớp mã nguồn,** và không dùng số liệu không có script đo.
7. **Kiểm soát độ dài:** mỗi lần build in số trang từng chương so với ngân sách. Chương nào vượt quá 10% phải cắt trước khi chuyển phiên.

## 4. Dàn ý và cách tận dụng phần đã viết

Ký hiệu: **Giữ** = giữ gần nguyên; **Rút** = viết gọn lại từ bản hiện có; **Chuyển** = đưa sang phụ lục; **Bỏ** = không dùng trong báo cáo.

### Chương 1. Tổng quan đề tài (13 → 8 trang)

| Mục | Xử lý |
|---|---|
| 1.1 Lý do chọn đề tài | **Rút.** Nhấn mạnh nhu cầu tra cứu học vụ. Nhu cầu dịch và học từ vựng chỉ còn một câu. Giữ H1-01. |
| 1.2 Khảo sát hiện trạng | **Rút** còn khoảng 1,5 trang. Gộp 1.2.1–1.2.4 thành hai tiểu mục: kênh tra cứu hiện nay; chatbot và trợ lý AI trong giáo dục. Bảng 1.1 chỉ giữ các tiêu chí về chatbot học vụ. |
| 1.3 Mục tiêu | **Rút.** Mục tiêu cụ thể tách thành hai nhóm: chatbot (chính) và tiện ích hỗ trợ (phụ). Giữ H1-03. |
| 1.4 Đối tượng, phạm vi | **Rút.** Ghi rõ phạm vi đánh giá sâu là chatbot. |
| 1.5 Phương pháp nghiên cứu | **Rút** thành một đoạn. Bỏ H1-05. |
| 1.6 Đóng góp chính | **Rút** còn 4–5 gạch đầu dòng; các đóng góp về RAG lên trước. |
| 1.7 Bố cục báo cáo | **Rút,** mỗi chương một câu. |

Hình: H1-01, H1-03. Bỏ H1-02, H1-04, H1-05.

### Chương 2. Cơ sở lý thuyết và công nghệ (72 → 24 trang)

| Mục | Lấy từ | Trang | Xử lý |
|---|---|---|---|
| 2.1 Mô hình ngôn ngữ lớn | 2.1 cũ (13 trang) | 4 | **Rút mạnh.** Transformer và attention (công thức attention); sinh văn bản với nhiệt độ và top-p (2 công thức, không hình); kỹ thuật prompt (một đoạn); hạn chế của LLM dẫn tới RAG; bảng các mô hình dùng trong đề tài. |
| 2.2 Sinh tăng cường truy xuất | 2.2 cũ (20 trang) | 14 | **Rút.** Giữ 7 tiểu mục, mỗi tiểu mục khoảng 2 trang: kiến trúc RAG; Bi/Cross-Encoder; HNSW; FTS và RRF; kỹ thuật nâng cao (viết lại câu hỏi, Parent–Child, Lost in the Middle, Self-RAG, semantic cache); phân đoạn; độ đo. Giữ tối đa 1 ví dụ cho cả mục. |
| 2.3 Nền tảng cho các phân hệ hỗ trợ | 2.3 + 2.4 cũ (20 trang) | 3 | **Rút mạnh.** Dịch máy NLLB-200 và CTranslate2, nhận diện ngôn ngữ và chuyên ngành, TTS: tổng cộng 1 trang, không công thức. Lặp lại ngắt quãng và FSRS: 1,5 trang, giữ 2 công thức R(t), I(r) và H2-31. |
| 2.4 Kiến trúc và công nghệ | 2.5 + 2.6 cũ (14 trang) | 2 | **Rút mạnh.** Microservices, cổng API, SSE và message broker, JWT: mỗi chủ đề 2–3 câu. Gộp Bảng 2.1 và 2.4 cũ thành một bảng công nghệ. Giữ H2-35, H2-42. |
| 2.5 Nghiên cứu liên quan | 2.7 cũ (5 trang) | 1 | **Rút.** Chỉ giữ chatbot RAG và chatbot giáo dục; bỏ bảng đối chiếu, viết thành một đoạn. |

**Hình giữ (13):**
- 2.1: H2-01, H2-02, H2-08.
- 2.2: H2-09, H2-10, H2-11, H2-13, H2-14, H2-18, H2-21.
- 2.3: H2-31.
- 2.4: H2-35, H2-42.

**Bỏ:** các hình còn lại đã vẽ của Chương 2. Các hình giữ chỗ không vẽ.

**Công thức:** 55 → khoảng 14 ở Chương 2. Đánh số lại bằng công cụ ở Phiên R1. Ở Phiên R2 lập danh sách công thức mà Chương 4 sẽ tham chiếu (cosine, RRF, R(t)…) để không cắt nhầm.

### Chương 3. Phân tích và thiết kế (47 → 22 trang)

| Mục | Trang | Xử lý |
|---|---|---|
| 3.1 Phân tích yêu cầu | 3 | **Rút.** Bảng 3.1 tác nhân giữ (bỏ H3-01, vì trùng với sơ đồ use case tổng quát). Bảng 3.2 còn khoảng 12 dòng: chatbot và quản trị tri thức chi tiết, mỗi phân hệ phụ 1–2 dòng. Bảng 3.3 còn khoảng 7 dòng. |
| 3.2 Mô hình hóa chức năng | 7 | Gồm bốn phần:<br>• 3.2.1 Use case tổng quát (H3-02).<br>• 3.2.2 Chatbot học vụ: H3-04, đặc tả UC05, H3-11.<br>• 3.2.3 Quản trị tri thức: đặc tả UC16, H3-20 (sơ đồ use case H3-07 chuyển sang Phụ lục B).<br>• 3.2.4 Các phân hệ hỗ trợ: một bảng liệt kê use case, mỗi use case một dòng. |
| 3.3 Kiến trúc tổng thể | 4 | **Rút.** H3-25; bảng route Kong gọn (5–6 dòng chính); một đoạn về giới hạn tần suất; luồng giao tiếp bằng lời; H3-30. |
| 3.4 Cơ sở dữ liệu | 4 | H3-32; H3-33 kèm đoạn về chỉ mục HNSW, GIN. Người dùng và hội thoại, Flashcard, Dịch thuật: mỗi nhóm một đoạn. H3-34, H3-35 chuyển sang Phụ lục E. |
| 3.5 Thiết kế API | 1,5 | **Rút:** quy ước và SSE, mỗi phần một đoạn. |
| 3.6 Thiết kế bảo mật | 1,5 | **Rút:** xác thực hai lớp, thu hồi token, bảng mô hình đe dọa còn khoảng 6 dòng. Bỏ H3-40. |
| 3.7 Thiết kế giao diện | 1 | H3-42 và một đoạn. H3-44 chuyển sang 4.4. |

**Hình trong chương (9):** H3-02, H3-04, H3-11, H3-20, H3-25, H3-30, H3-32, H3-33, H3-42.

### Chương 4. Xây dựng hệ thống (42 trang, viết mới)

| Mục | Trang | Nội dung | Hình |
|---|---|---|---|
| **4.1 Pipeline thu thập và xử lý tri thức** | 9 | Nguồn và thu thập URL (bảng nguồn); trích xuất HTML, PDF, OCR; Hybrid Chunker Parent–Child; sinh vector và ghi CSDL; API quản trị và tiến độ SSE; thống kê kho tri thức (bảng) | H4-01, H4-06, H4-08 (ảnh); H3-23 bỏ vì H4-01 đã bao quát |
| **4.2 Academic Chatbot Service** | 24 | 4.2.1 Vòng đời một câu hỏi · 4.2.2 Guardrail · 4.2.3 Router viết lại và tách câu hỏi · 4.2.4 Semantic cache hai tầng · 4.2.5 Truy xuất lai và rerank đa truy vấn · 4.2.6 Ngữ cảnh: Small-to-Big, Sandwich, cách ly · 4.2.7 Prompt theo intent và lớp nhà cung cấp LLM · 4.2.8 Self-RAG, streaming, trích dẫn · 4.2.9 Phiên hội thoại và log | H4-10, H4-11a, H4-11b, H4-13, H4-14, H4-16, H4-19, H4-21, H4-24 (ảnh) |
| **4.3 Các phân hệ hỗ trợ** | 6 | 4.3.1 Dịch thuật (2,5 trang): NLLB và dự phòng LLM, nhận diện ngôn ngữ, dịch chuyên ngành, TTS · 4.3.2 Flashcard (2,5 trang): FSRS, pipeline sinh từ vựng, bộ từ mẫu, trò chơi · 4.3.3 Xác thực và cổng API (1 trang, tham chiếu 3.3, 3.6) · Dịch tài liệu: 2–3 câu | H4-28, H4-33 (ảnh), H4-40, H4-45 (ảnh) |
| **4.4 Ứng dụng web và triển khai** | 3 | Cấu trúc frontend, luồng chat SSE phía client, responsive; Docker Compose, low-VRAM, CI, demo qua Tailscale Funnel | H3-44 (dùng lại) |

Hình Chương 4: 18.

### Chương 5. Kiểm thử và đánh giá (18 trang, Phiên 10 dựng khung)

| Mục | Trang | Nội dung |
|---|---|---|
| 5.1 Môi trường và phương pháp | 2 | Cấu hình máy, mô hình, bộ dữ liệu, độ đo (tham chiếu 2.2.7) |
| **5.2 Đánh giá chatbot** | 10 | Truy xuất: Hit@K, MRR, ablation (dense / FTS / hybrid / +rerank / +small-to-big); chất lượng câu trả lời; semantic cache; guardrail; độ trễ và TTFT |
| 5.3 Kiểm thử phần mềm và phân hệ hỗ trợ | 4 | Bảng số test theo service; nhận diện ngôn ngữ; kiểm chứng giới hạn tần suất của Kong (kế hoạch cũ mục 11, điểm 26) |
| 5.4 Thảo luận | 2 | |

Hình: H5-01, H5-02, H5-03, H5-04, H5-05.

### Chương 6. Kết luận và hướng phát triển (4 trang)

| Mục | Trang | Nội dung |
|---|---|---|
| 6.1 Kết quả đạt được | 1 | Đối chiếu mục tiêu ở 1.3 |
| 6.2 Hạn chế | 1,5 | Chatbot chi tiết; phân hệ phụ và bảo mật mỗi nhóm 1–2 câu, dùng các điểm 18–28 của kế hoạch cũ mục 11 |
| 6.3 Hướng phát triển | 1,5 | Chatbot là chính; các phân hệ khác và dịch tài liệu mỗi nhóm một câu |

Không dùng hình.

### Phụ lục (không tính vào 130 trang, khoảng 30 trang)

| Phụ lục | Trang | Nội dung | Từ bản hiện có |
|---|---|---|---|
| A. Cài đặt và vận hành | 4 | Các bước cài đặt, `.env`, mô hình, khởi động, tạo admin, nạp tri thức; Bảng A.1 tài nguyên container | Giữ Bảng A.1, viết phần còn lại |
| B. Use case bổ sung | 8 | Sơ đồ use case H3-07 (quản trị), H3-03, H3-05, H3-06 (phân hệ phụ); đặc tả UC06, UC17 (chatbot, quản trị) và một đặc tả tiêu biểu cho mỗi phân hệ phụ: UC02, UC08, UC12 | **Rút từ Phụ lục B hiện tại:** 13 → 5 đặc tả; bỏ toàn bộ sơ đồ tuần tự của phân hệ phụ |
| C. Thiết kế API chi tiết | 7 | Bảng nhóm endpoint; danh sách endpoint của Chatbot đầy đủ, của service khác rút gọn; mã HTTP; định dạng phản hồi (H3-38); sự kiện SSE (bảng và H3-39) | Giữ, bỏ H3-26 |
| D. Prompt template | 5 | Prompt bộ định tuyến, prompt theo intent, Self-RAG của chatbot | Viết mới |
| E. Lược đồ CSDL | 4 | H3-34, H3-35, H3-37; bảng thuộc tính nhóm RAG (E.1–E.4) và người dùng, hội thoại (E.5–E.6) | Giữ; bỏ bảng thuộc tính Flashcard và từ điển |
| F. Bộ câu hỏi đánh giá chatbot | 2 | Danh sách câu hỏi có nhãn | Sau Chương 5 |

Hình phụ lục (9): H3-03, H3-05, H3-06, H3-07, H3-34, H3-35, H3-37, H3-38, H3-39.

## 5. Phiên làm việc

| Phiên | Nội dung | Ngân sách | Đầu ra |
|---|---|---|---|
| **R1** | Công cụ: build in số trang từng chương so với ngân sách; `renumber.py` đánh số lại cả công thức. Rút gọn Chương 1. | Ch.1: 8 | `01_tong_quan.md` |
| **R2** | Rút gọn Chương 2 (72 → 24): gộp 2.3–2.4 cũ, gộp 2.5–2.6 cũ, giữ 13 hình, khoảng 14 công thức; bỏ tài liệu tham khảo không còn được trích dẫn | Ch.2: 24 | `02_*.md`, `90_…md` |
| **R3** | Rút gọn Chương 3 (47 → 22) và sắp lại Phụ lục B, C, E | Ch.3: 22 | `03_*.md`, `91_…md` |
| **7** | 4.1 Pipeline thu thập và xử lý tri thức | 9 | `04_1_ingestion.md` |
| **8a** | 4.2.1–4.2.5 Chatbot: vòng đời, guardrail, router, cache, truy xuất | 12 | `04_2_chatbot.md` |
| **8b** | 4.2.6–4.2.9 Chatbot: ngữ cảnh, prompt, Self-RAG, streaming, phiên | 12 | `04_2_chatbot.md` |
| **9** | 4.3 Phân hệ hỗ trợ, 4.4 Ứng dụng web và triển khai, tiểu kết Chương 4 | 9 | `04_3_phan_he_ho_tro.md` |
| **10** | Khung Chương 5 (phương pháp, thiết kế thí nghiệm, bảng trống) | 18 | `05_kiem_thu_danh_gia.md` |
| **11** | Chương 6 và phần đầu (lời cảm ơn, tóm tắt, danh mục viết tắt) | 4 + ~14 | `06_ket_luan.md`, `00_phan_dau.md` |
| **12** | Phụ lục A, C (endpoint), D, F; rà tài liệu tham khảo | ~30 + 4 | `91_…md`, `90_…md` |
| **13** | Tổng hợp: bìa, phụ bìa, nhật ký; **kiểm tra phần chính ≤ 130 trang**; rà soát cuối | ≤ 130 | `IUH_EduBot_BaoCao.docx`, `.pdf` |
| S | Nhóm chụp 4 ảnh giao diện (mục 6) và gán vào ảnh giữ chỗ | — | `figures/` |

## 6. Ảnh giao diện cần chụp

| Ảnh | Màn hình | Ghi chú |
|---|---|---|
| H4-08 | Quản trị: nạp tri thức, đang hiện tiến độ | Có tài liệu đang nạp |
| H4-24 | Chatbot: câu trả lời kèm trích dẫn, đang mở một nguồn | Câu hỏi về quy chế hoặc học phí |
| H4-33 | Trang Dịch thuật, chế độ chuyên ngành | |
| H4-45 | Phiên ôn tập flashcard: mặt sau và bốn nút đánh giá | |

H3-44 (trang đăng nhập ở ba độ rộng) đã dựng từ ảnh có sẵn trong repo.

## 7. Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Phần chatbot ở Chương 4 vượt 24 trang | Bảng tham số và prompt đầy đủ đưa sang phụ lục. Build báo vượt ngân sách ngay khi xảy ra. |
| Chương 2 khó xuống 24 trang mà vẫn đủ lý thuyết cho RAG | Ưu tiên giữ 2.2. Phần 2.1, 2.3, 2.4 có thể ngắn hơn ngân sách để bù cho 2.2. |
| Chương 5 thiếu số liệu thật | Khung có bảng trống và ghi chú `[CHỜ SỐ LIỆU]`; ngân sách 18 trang đã tính sẵn cho bảng và biểu đồ. |
| Cắt Chương 2 làm mất công thức mà Chương 4 cần | Ở Phiên R2, lập danh sách công thức Chương 4 sẽ tham chiếu trước khi cắt. |

## 8. Những phần của kế hoạch cũ vẫn áp dụng

- **Mục 0, 1, 2:** quyết định định dạng, quy định trình bày của Khoa, quy ước viết nội dung.
- **Mục 6.1–6.2:** nguyên tắc vẽ hình, loại hình, phong cách và bảng màu. Mục 6.3 (danh mục hình) được thay bằng danh sách hình ở mục 4 của tài liệu này.
- **Mục 7, 8:** nguồn tài liệu và quy tắc tài liệu tham khảo.
- **Mục 10:** các thông tin nhóm cần bổ sung.
- **Mục 11:** 28 điểm phải đối chiếu với mã nguồn.
- **Mục 12:** danh sách kiểm tra cuối, thêm điều kiện "phần chính ≤ 130 trang".
