# TIẾN ĐỘ VIẾT BÁO CÁO KHÓA LUẬN

Từ 31/10/2026 theo dõi các phiên trong mục 5 của `KE_HOACH_V2.md` (phần chính ≤ 130 trang, trọng tâm chatbot). Các phiên 0–6b làm theo kế hoạch cũ. Mỗi phiên xong thì cập nhật file này và chờ nhóm duyệt.

## Tổng quan

### Các phiên đã làm (kế hoạch cũ)

| Phiên | Nội dung | Trạng thái | Ngày |
|---|---|---|---|
| 0 | Dựng công cụ, file mẫu định dạng | **Đã duyệt** (theo các mặc định đề xuất) | 30/10/2026 |
| — | Lập lại kế hoạch hình minh họa (mục 6 của kế hoạch) | **Đã duyệt** | 30/10/2026 |
| 0b | Dựng công cụ vẽ hình + 7 hình mẫu | **Đã duyệt** | 30/10/2026 |
| 1 | Chương 1 | **Đã duyệt** | 30/10/2026 |
| 2 | 2.1 LLM + 2.2 RAG | **Đã duyệt** | 30/10/2026 |
| 3 | 2.3 Dịch máy + 2.4 Lặp lại ngắt quãng | **Đã duyệt** | 30/10/2026 |
| 4 | 2.5–2.7 + tiểu kết Chương 2 | **Đã duyệt** | 30/10/2026 |
| 5a | 3.1–3.2 Yêu cầu, use case, bảng đặc tả | **Đã duyệt** | 30/10/2026 |
| 5b | 3.2 Sơ đồ tuần tự, sơ đồ hoạt động | **Đã duyệt** | 30/10/2026 |
| 6 | 3.3–3.7 Kiến trúc, CSDL, API, bảo mật, giao diện | **Đã duyệt** (yêu cầu rút gọn) | 31/10/2026 |
| 6b | Rút gọn Chương 3 về ~45 trang; dựng Phụ lục B, C, E | Thay bằng R3 của kế hoạch V2 | 31/10/2026 |
| V2 | Lập kế hoạch V2: phần chính ≤ 130 trang (ban đầu ≤ 200 trang cả cuốn), trọng tâm chatbot | **Đã duyệt** | 31/10/2026 |

### Các phiên theo kế hoạch V2

| Phiên | Nội dung | Ngân sách (trang) | Trạng thái |
|---|---|---|---|
| R1 | Công cụ kiểm tra ngân sách trang, đánh số lại công thức; rút gọn Chương 1 | Ch.1: 8 | **Đã duyệt** (Ch.1 = 8 trang) |
| R2 | Rút gọn Chương 2 (72 → 24) | 24 | **Đã duyệt** (Ch.2 = 24 trang; TLTK nâng lên 6 trang) |
| R3 | Rút gọn Chương 3 (47 → 22); sắp lại Phụ lục B, C, E | 22 | **Đã duyệt** (Ch.3 = 22 trang) |
| 7 | 4.1 Pipeline tri thức | 9 | **Đã duyệt** (8 trang) |
| 8a | 4.2.1–4.2.5 Chatbot | 12 | **Đã duyệt** (12 trang) |
| 8b | 4.2.6–4.2.9 Chatbot | 12 | **Đã duyệt** (10 trang) |
| 9 | 4.3 Phân hệ hỗ trợ, 4.4 Web và triển khai, tiểu kết Ch.4 | 10 | **Đã duyệt** (11 trang) |
| 10 | Khung Chương 5 | 18 | **Đã duyệt** (15 trang, còn bảng trống) |
| 10b | Viết script đo E1–E3, E5 và bộ câu hỏi (Phụ lục F); chạy thử và điền số liệu Chương 5 | — | **Đã duyệt** |
| 11 | Chương 6 + phần đầu | 4 + ~14 | **Đã duyệt** (Ch.6 = 4 trang, phần đầu 14 trang số La Mã) |
| 12 | Phụ lục A, C, D, F; tài liệu tham khảo | ~30 + 4 | **Đã duyệt** (phụ lục 35 trang) |
| 13 | Tổng hợp, kiểm tra phần chính ≤ 130 trang, rà soát | ≤ 130 | Chưa làm |
| S | 4 ảnh giao diện (KE_HOACH_V2 mục 6) | — | Nhóm tự làm sau |

---

## Phiên 0 – Dựng công cụ (30/10/2026)

### Đã làm

1. **Thư mục:** `drafts/`, `figures/` (`src/`, `screenshots/`), `build/` (`sample/`, `tools/`).
2. **Công cụ:** cài `pypandoc_binary` (pandoc 3.9). Máy có sẵn Python 3.11, `python-docx` 1.2, Java 25, Word 16.
3. **`build/make_reference.py` → `build/reference.docx`:** A4, lề 3/3/3,5/2 cm; style lấy đúng thông số trong PDF của Khoa (tr.15–19): Heading 1–4, Content, Bullet, Caption, danh mục (toc 1–3, table of figures), cùng một số style riêng (Table Text, Source Code, Equation, Reference, TODO).
4. **`build/filters.lua`** (Lua filter cho pandoc):
   - bỏ số viết tay ở heading để Word tự đánh số, và cảnh báo nếu số viết tay lệch với số thực tế;
   - tạo caption hình/bảng bằng trường `STYLEREF`/`SEQ`, giống Insert Caption của Word;
   - đánh số công thức `\tag{x-y}`;
   - chèn trường mục lục và danh mục hình/bảng (`[[TOC]]`, `[[LOF]]`, `[[LOT]]`);
   - tô nền vàng các ghi chú `[TODO]` / `[CHỜ SỐ LIỆU]`.
5. **`build/build_report.py`:**
   - ghép 3 phần: phần đầu → nội dung chính → phụ lục;
   - đánh số heading tự động `CHƯƠNG x` / `x.y` / `x.y.z` / `x.y.z.t`;
   - bảng chỉ kẻ ngang, dòng tiêu đề in đậm và lặp lại khi sang trang;
   - công thức đặt trong bảng 3 cột không viền, số hiệu căn phải;
   - thu nhỏ hình rộng quá 15,5 cm;
   - chia section, header/footer, số trang;
   - kiểm tra mỗi hình/bảng đã được nhắc trong văn bản trước khi xuất hiện;
   - cờ `--word --pdf`: gọi `word_update.ps1` để cập nhật mục lục, danh mục, số caption và xuất PDF.
6. **Cấu hình:** `build/report_config.json` chứa tên sinh viên, header, thứ tự file và các tùy chọn định dạng.
7. **Bản mẫu để duyệt:** `build/MAU_DINH_DANG.docx` và `.pdf` (13 trang), ghép từ `build/sample/*.md`. Kết quả chạy: 2 chương, 2 hình, 3 bảng, 4 công thức, 0 cảnh báo.
8. **Logo IUH mới** trích từ bìa cuốn QuyLong, lưu ở `figures/iuh_logo_new.png` (653×186 px), dùng cho bìa ở Phiên 16.

### Đã kiểm tra trên PDF xuất từ Word

- Phần đầu đánh số La Mã (i–vi). Chương 1 bắt đầu từ trang 1. Phụ lục không có số trang.
- Header `IUH_Academic_Counseling_Chatbot` (căn phải, nghiêng). Footer: tên 2 sinh viên bên trái, số trang sát lề phải.
- Mục lục đến cấp 3. Có TÀI LIỆU THAM KHẢO, PHỤ LỤC và các mục "Tiểu kết chương". Heading 4 không vào mục lục.
- Danh mục hình và danh mục bảng sinh tự động. Số hình, bảng, công thức đánh lại từ đầu ở mỗi chương.
- Công thức OMML sửa được trong Word: cosine, RRF, BM25 (phân số lồng nhau), MRR.
- Tài liệu tham khảo thụt treo 1 cm.

### Kết quả duyệt (30/10/2026)

Nhóm đồng ý toàn bộ mặc định đề xuất:
- Heading 1 một dòng, căn trái.
- Caption dạng `Hình 2.1: …`.
- Phần đầu đánh số La Mã.
- Header căn phải, nghiêng.
- Footer: tên bên trái, số trang bên phải.

Mục 0 và 1.1–1.3 của kế hoạch đã sửa theo. Bảng bên dưới giữ lại để tra cứu.

### Các điểm đã đưa ra cho nhóm quyết định

Kế hoạch và PDF của Khoa khác nhau ở các điểm dưới đây. Mặc định hiện **theo PDF của Khoa**; mỗi điểm chỉ cần đổi một dòng trong `report_config.json`.

| # | Điểm | Kế hoạch ghi | PDF của Khoa | Mặc định hiện tại | Khóa cấu hình |
|---|---|---|---|---|---|
| 1 | Heading 1 | Căn giữa, hai dòng | "căn lề trái", một dòng `CHƯƠNG 2 ⇥ ĐỊNH DẠNG` (tr.17) | Theo PDF | `heading1_layout`: `one_line_left` / `two_lines_center` |
| 2 | Dấu sau số caption | `Hình 4.3. …` | Ví dụ ghi `Hình 2.1: Bìa mẫu` (QuyLong cũng dùng dấu `:`) | `:` | `caption_sep`: `colon` / `period` |
| 3 | Số trang phần đầu | Chưa chốt | Mục lục mẫu đánh La Mã (x, xi) | La Mã | `front_page_numbers`: `roman` / `none` |
| 4 | Header | Căn phải, nghiêng | Căn trái, chữ đứng (chỉ thấy qua ví dụ, quy định không nói rõ) | Theo kế hoạch | `header_align`, `header_italic` |
| 5 | Footer | Tên bên trái, số trang bên phải | Tên và số trang cùng căn phải, dính liền nhau | Theo kế hoạch (vẫn đúng quy định "số trang bên phải, phía dưới") | — |

Bản PDF của biến thể "hai dòng căn giữa + dấu chấm" để so sánh: `build/MAU_DINH_DANG_bien_the_2dong.pdf`.

### Còn tồn đọng

- **PlantUML chưa tải:** quyền tải file `.jar` từ Internet bị chặn trong phiên này. Nhóm có thể tự tải, hoặc cấp quyền để tôi tải ở phiên sau:
  ```powershell
  Invoke-WebRequest https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar -OutFile B:\KhoaLuan\Report\build\tools\plantuml.jar
  java -jar B:\KhoaLuan\Report\build\tools\plantuml.jar -version
  ```
  PlantUML cần từ Phiên 5 (sơ đồ use case, sơ đồ tuần tự). Phiên 1–4 chưa cần.
- **Bảng con lồng trong bảng đặc tả use case:** Markdown không hỗ trợ bảng lồng nhau. Bản mẫu (Bảng 2.1, 2.2) tách "Luồng sự kiện chính" thành một bảng hai cột riêng đặt ngay sau bảng đặc tả. Nếu nhóm muốn lồng đúng như cuốn QuyLong, sẽ bổ sung bước hậu xử lý ở Phiên 5.
- **Trang bìa, phụ bìa, các trang nhận xét:** làm ở Phiên 16, như kế hoạch.
- **Thông tin nhóm** (mục 10 của kế hoạch): họ tên, MSSV, GVHD… Footer đang dùng chữ giữ chỗ "Họ tên Sinh viên 1 – Họ tên Sinh viên 2".

---

## Lập lại kế hoạch hình minh họa (30/10/2026)

Theo yêu cầu của nhóm (bổ sung sơ đồ và hình minh họa để báo cáo đỡ nhàm chán), tôi đã sửa `KE_HOACH_VIET_BAO_CAO.md`:
- **Mục 6** viết lại toàn bộ:
  - nguyên tắc;
  - 11 loại hình;
  - quy chuẩn và bảng màu;
  - danh mục 170 hình, trong đó 129 hình mức A;
  - quản lý hình;
  - danh sách 36 ảnh giao diện cần chụp.
- **Mục 3.2** cập nhật bảng công cụ: Mermaid, PlantUML, SVG, matplotlib, Playwright, Pillow. Bỏ draw.io vì máy chưa cài.
- **Mục 4**:
  - Chương 2 thêm bước "hình trước công thức" và hộp "Ví dụ";
  - Chương 4 thêm sơ đồ kiến trúc mở đầu mỗi service, ví dụ thực tế và mục "Kết quả trên giao diện".
- **Mục 9**: thêm Phiên 0b, Phiên S; tách Phiên 5 thành 5a/5b; thêm cột số hình của mỗi phiên.
- **Mục 10, 12**: thêm thông tin cần cung cấp và checklist cho hình.

Các phát hiện khi khảo sát repo để lập kế hoạch:
- Repo có sẵn **23 sơ đồ Mermaid** trong các README. Các sơ đồ này được tái sử dụng sau khi đối chiếu với code.
- **Không dùng được** ảnh nội dung trong `frontend/screenshots-responsive/`. Đó là dữ liệu giả từ `src/mock/mockData.ts`: frontend tự chuyển sang dữ liệu giả khi không gọi được backend. Phải chụp lại khi hệ thống chạy thật.
- Ảnh e2e của phân hệ dịch chụp giao diện phiên bản cũ, nên chỉ dùng ở Chương 5.
- `logs/academic_chatbot/2026-10-29/` có 10 log thật, ghi từng bước của pipeline. Đây là nguồn cho các hình "ví dụ thực tế" của 4.2.
- Gói `fsrs` 6.3.2 đã cài trên máy, đủ để vẽ đường cong quên và lịch ôn bằng chính thư viện hệ thống dùng.

---

## Phiên 0b – Dựng công cụ vẽ hình (30/10/2026)

Quyết định của nhóm: cho phép tải công cụ; **tạm chưa chạy Docker**, chỉ đặt chỗ cho ảnh giao diện, nhóm gán ảnh sau.

### Đã làm

1. **Tải công cụ** vào `build/tools/`:
   - `plantuml.jar` 1.2026.9 (đã có Graphviz);
   - `mermaid.min.js` 11.4.1.

   Playwright dùng Chromium có sẵn trên máy (`ms-playwright/chromium-1223`), không tải thêm.
2. **Theme chung** trong `figures/src/_theme/`:
   - `palette.json`: bảng màu theo thành phần;
   - `plantuml.iuml`;
   - `mermaid.json`, `classes.mmd`;
   - `svg.css`;
   - `figstyle.py` cho matplotlib.
3. **`build/render_figures.py`**:
   - xuất `figures/src/chN/<mã>.{puml,mmd,svg,py}` → `figures/chN/<mã>.png` và ghi DPI để Word đặt đúng kích thước;
   - chỉ vẽ lại hình có nguồn hoặc theme thay đổi;
   - **tạo ảnh giữ chỗ** cho mọi hình chưa có, đánh dấu trong metadata PNG nên không ghi đè ảnh thật;
   - tự cập nhật cột "Trạng thái" trong `FIGURES.md`.
4. **`figures/FIGURES.md`**: danh mục 171 hình kèm chú thích chuẩn, sinh từ mục 6.3 của kế hoạch. Các dải mã đã được tách thành từng hình (ví dụ 14 sơ đồ tuần tự H3-08 → H3-21 được gán sẵn cho từng UC).
5. **`build_report.py`** cảnh báo khi chú thích hình trong bản thảo khác `FIGURES.md`. **`reference.docx`** có thêm style `Example Box` (hộp ví dụ).
6. **7 hình mẫu**. Mỗi hình đã đối chiếu với code; dòng chú thích đầu file nguồn ghi rõ file và dòng code được đối chiếu.

| Mã | Loại | Công cụ | Kích thước khi in |
|---|---|---|---|
| H3-25 Kiến trúc tổng thể | KT | SVG | 15,5 × 16,9 cm |
| H3-02 Use case tổng quát | UC | PlantUML | 15,5 × 14,7 cm |
| H4-14 Semantic cache hai tầng | LĐ | PlantUML (hoạt động) | 14,3 × 15,2 cm |
| H4-11a, H4-11b Tuần tự `/messages/stream` | TT | PlantUML | 15,5 × 19,2 và 15,5 × 12,8 cm |
| H2-33 Đường R(t) của FSRS | BĐ | matplotlib + gói `fsrs` 6.3.2 | 14 × 7,2 cm |
| H4-13 Ví dụ Router từ log thật | VD | SVG | 15,5 × 9,5 cm |

7. **Bản mẫu để duyệt:** `build/MAU_DINH_DANG.pdf` (22 trang). Chương 3 của bản mẫu (trang 6–14) gồm 7 hình trên, một hộp ví dụ và một ảnh giao diện giữ chỗ (H4-23).

### Rút ra khi vẽ thử (đã ghi vào kế hoạch mục 3.2, 6.1, 6.2)

- **Lưu đồ và sơ đồ tuần tự chuyển sang PlantUML.** Với cùng nội dung:
  - lưu đồ semantic cache bằng Mermaid cao gấp 3,2 lần chiều rộng;
  - sơ đồ tuần tự bằng Mermaid rộng 37 cm (chữ còn khoảng 4 pt khi thu về khổ giấy).

  PlantUML cho hình gọn, chữ 9 pt. Mermaid chỉ còn dùng cho ERD và sơ đồ trạng thái.
- Sơ đồ tuần tự dài hơn 12–15 bước thì tách hai hình (a, b).
- Trên hình không đặt tên hàm dài; dùng nhãn tiếng Việt ngắn.
- Sơ đồ use case tổng quát chỉ vẽ ở mức chức năng lớn; 19 use case chi tiết nằm trong 5 sơ đồ phân hệ.

### Phát hiện mới khi đối chiếu code (đã thêm vào kế hoạch mục 11, điểm 16–18)

- **16 – Trạng thái thẻ FSRS:**
  - Service dùng `Scheduler(learning_steps=(), relearning_steps=())`.
  - Chạy thử gói `fsrs` 6.3.2 với đúng cấu hình này: thẻ đi thẳng New → Review, và Again vẫn giữ ở Review. Learning và Relearning không bao giờ xuất hiện.
  - H4-38 sẽ vẽ theo thực tế này.
- **17 – Trang dịch tài liệu:** khi tắt cờ tính năng, `/translation-doc` chuyển hướng về `/translation`, không có trang khóa.
- **18 – README chatbot thiếu một bước:** sơ đồ trong README không có bước tính embedding của `queries[0]` sau Router. H4-11a đã vẽ theo code.

### Cách gán ảnh giao diện sau này

1. Chụp màn hình theo danh sách ở mục 6.5 của kế hoạch.
2. Lưu **đè đúng tên file** ảnh giữ chỗ, ví dụ `figures/ch4/H4-23.png`. Kích thước nào cũng được; script tự thu về rộng tối đa 15,5 cm.
3. Chạy `python build/render_figures.py`: trạng thái trong `FIGURES.md` chuyển sang "ảnh thật".
4. Ghép lại báo cáo bằng `python build/build_report.py --word --pdf`.

---

## Phiên 1 – Chương 1. Tổng quan đề tài (30/10/2026)

### Đã làm

- **Bản thảo** `drafts/01_tong_quan.md`: đủ các mục 1.1–1.7 và tiểu kết. Khoảng 13 trang khi ghép, gồm cả hình.
- **Hình:**
  - Đã vẽ: H1-01 (các nguồn thông tin học vụ), H1-02 (ba nhu cầu và hướng hợp nhất), H1-03 (năm phân hệ và liên kết), H1-05 (quy trình nghiên cứu).
  - Ảnh giữ chỗ: H1-04 (ghép ảnh giao diện, mức B).
  - **Bảng 1.1** so sánh các nhóm giải pháp theo 6 tiêu chí.
- **Trích dẫn theo khóa:** viết `[@khóa]` trong bản thảo, khi ghép tự đổi thành `[n]` theo thứ tự trong `drafts/90_tai_lieu_tham_khao.md`. Dãy từ 3 số liên tiếp trở lên được gộp thành `[3]–[5]`. Script báo khi có khóa không tồn tại hoặc tài liệu chưa được trích dẫn.
- **Danh mục tài liệu tham khảo ban đầu:** 10 mục. Chi tiết xuất bản sẽ kiểm tra lại ở Phiên 15.
- **`build_report.py`:** bảng ngắn (≤ 20 dòng) được giữ trọn trên một trang.
- **Bản ghép:** `build/IUH_EduBot_BaoCao.pdf` (15 trang: Chương 1 + tài liệu tham khảo).

### Đối chiếu với code

| Nội dung trong chương | Nguồn |
|---|---|
| 5 tên miền nguồn tri thức, độ sâu BFS, 4 URL tuyển sinh cố định | `data_ingestion/sources.py` |
| Dịch 10 ngôn ngữ: en, de, zh, ja, ko, fr, es, ru, th, vi | `LANG_MAP` trong `realtime_translation_service/app/services/llm_service.py` |
| 6 chuyên ngành định sẵn | `_PREDEFINED_DOMAINS` trong `domain_service.py` |
| Flashcard: 10 mã ngôn ngữ, **9 ngôn ngữ học được** (tiếng Việt là ngôn ngữ giải nghĩa) | `flashcard_service/app/utils/languages.py`. Mục 11 điểm 14 của kế hoạch đã được làm rõ: cả "9" và "10" đều đúng, tùy ngữ cảnh |
| Sự kiện `flashcard.created` / `flashcard.audio_ready` | `rabbitmq_consumer.py` của hai service |
| CI có 3 job; job `rag-eval-benchmark` chỉ kiểm tra công thức | `.github/workflows/ci.yml`, README §8 |

### Phát hiện

File `B:\KhoaLuan\tb-892-2025-Quy dinh ve hoc tieng Anh.pdf` **thực chất là bản sao cuốn khóa luận QuyLong**, không phải Thông báo 892 về học tiếng Anh. Mục 1.1 vì vậy không trích dẫn file này. Mục 8.1 của kế hoạch đã ghi chú.

### Cần nhóm bổ sung

Bản ghép hiện có 4 ghi chú TODO, tô nền vàng:

1. Vai trò của hai trang `ctsv.iuh.edu.vn` và `csm.iuh.edu.vn` (mục 1.1, hình H1-01 đang ghi "Trang đơn vị").
2. Văn bản chính thức về yêu cầu ngoại ngữ, nếu có (mục 1.1).
3. Kết quả khảo sát sinh viên, nếu có (mục 1.2.1).
4. Kiểm tra lại các ô đánh giá sản phẩm bên ngoài trong Bảng 1.1.

Ngoài ra, trong danh mục tài liệu tham khảo còn thiếu:
- số hiệu và năm ban hành của Quy chế đào tạo IUH;
- ngày truy cập các trang web.

---

## Phiên 2 – Mục 2.1 LLM và 2.2 RAG (30/10/2026)

### Đã làm

- **Bản thảo** `drafts/02_1_llm_rag.md`: phần mở đầu Chương 2, mục 2.1.1–2.1.5 và 2.2.1–2.2.7. Khoảng 33 trang khi ghép.
- **Công thức:** đủ 27 công thức (2-1)…(2-27), mỗi công thức có giải thích từng ký hiệu. Các công thức có tham số trong hệ thống đều ghi giá trị thực tế:
  - temperature 0,2, top-p 0,8;
  - HNSW `m = 16`, `ef_construction = 64`;
  - RRF k = 60;
  - ngưỡng 0,20 / 0,65 / 0,80;
  - $n_{\max} = 4$.
- **Hai hộp ví dụ:** tính RRF; tính Hit Rate và MRR.
- **Hai bảng:** Bảng 2.1 (mô hình và vai trò), Bảng 2.2 (chiến lược phân đoạn).
- **17 hình** (mức A: 12/12; mức B: 5):

| Loại | Hình |
|---|---|
| Biểu đồ matplotlib | H2-05 (nhiệt độ), H2-06 (top-p), H2-13 (HNSW, tìm kiếm tham lam chạy thật trên dữ liệu đồ chơi), H2-17 (Lost in the Middle, **số liệu gốc Bảng 6** của bài báo) |
| SVG khái niệm | H2-01 Transformer, H2-02 attention, H2-03 decoder-only, H2-04 MoE, H2-08 hạn chế LLM, H2-09 Naive RAG, H2-10 ba mô hình RAG, H2-11 Bi/Cross-Encoder, H2-18 Parent–Child |
| SVG có ví dụ cụ thể | H2-07 cấu trúc prompt (theo `build_dynamic_system_instruction`), H2-14 ví dụ RRF, H2-15 FTS của PostgreSQL với ví dụ |
| Ví dụ thật | H2-21 ba chiến lược phân đoạn trên **đoạn quy chế thật** lấy từ log |

- **Hình mức B chưa làm** (không đặt vào bản thảo):
  - H2-12: cần chạy mô hình bi-encoder cục bộ;
  - H2-16, H2-19, H2-20: nội dung đã có trong phần lời;
  - H2-22: thay bằng hộp Ví dụ 2.2.
- **Tài liệu tham khảo:** danh mục có 37 mục (thêm 27). Phiên 15 sẽ kiểm tra lại thông tin xuất bản.
- **Sửa bộ công cụ:** bật extension `lists_without_preceding_blankline` của pandoc. Trước đó, danh sách đứng ngay sau dòng "trong đó:" bị gộp thành một đoạn văn; lỗi này ảnh hưởng cả Chương 1.

### Đối chiếu với code (điểm mới, đã ghi vào kế hoạch mục 11)

- **Điểm 19:** `top_k=8` không được dùng; số đoạn đưa vào prompt do quota quyết định (tối đa 5 hoặc 8).
- **Điểm 20:** mã nguồn không đặt `hnsw.ef_search` (mặc định 40), trong khi nhánh vector yêu cầu 100 ứng viên. **Cần kiểm tra trên CSDL thật.**
- Hệ thống dùng `ts_rank_cd` với cấu hình `'simple'` và `unaccent`, không dùng BM25 (đã ghi rõ trong mục 2.2.4).
- Phân hệ dịch chuyên ngành dùng mô hình riêng là Groq `qwen/qwen3.8-27b`, khác với mô hình dịch dự phòng `llama-3.1-8b-instant`.

### Cần nhóm bổ sung hoặc quyết định

1. Cấu hình LLM thực tế dùng khi demo và khi đo (Bảng 2.1).
2. Xác nhận chế độ pooling của `vietnamese-bi-encoder` khi tải mô hình về.
3. Kiểm tra `hnsw.ef_search` trên Supabase.
4. **Độ dài:** riêng mục 2.1–2.2 đã khoảng 33 trang. Nếu giữ mức chi tiết này, Chương 2 sẽ khoảng 55–60 trang, vượt kế hoạch 40–45 trang. Có thể rút gọn mục 2.1, vốn là lý thuyết phổ thông, nếu GVHD yêu cầu.

---

## Phiên 3 – Mục 2.3 Dịch máy và 2.4 Lặp lại ngắt quãng (30/10/2026)

### Đã làm

- **Bản thảo** `drafts/02_2_dich_may_srs.md`: mục 2.3.1–2.3.7 và 2.4.1–2.4.3. Khoảng 21 trang khi ghép.
- **Công thức (2-28)…(2-51):** đánh số lại so với kế hoạch, chi tiết ở kế hoạch mục 5. Phiên 4 bắt đầu từ (2-52).
- **Hộp Ví dụ 2.3:** tính BLEU bằng tay (≈ 0,661), đã kiểm tra lại bằng code.
- **Bảng 2.3:** so sánh SM-2 và FSRS.
- **10 hình** (mức A: 7/7, mức B: 3):

| Hình | Cách làm, nguồn số liệu |
|---|---|
| H2-23 mã hóa – giải mã, chú ý chéo | SVG khái niệm |
| H2-24 beam search B = 2 | SVG, số liệu minh họa |
| H2-26 lượng tử hóa INT8 | matplotlib, số liệu minh họa |
| H2-27 nhận diện ngôn ngữ | PlantUML, theo `language_detection.py` |
| H2-28 `decide_domain` | PlantUML, theo `domain_detection.py` |
| H2-29 thuật toán Lesk | **kết quả chạy thật** `simple_lesk` (pywsd) trên WordNet. Câu 1: hai nghĩa hòa điểm 2. Câu 2: nghĩa *bờ sông* trùng 4 từ |
| H2-31 đường cong quên và ôn theo lịch | mô phỏng bằng gói `fsrs` 6.3.2 |
| H2-32 mô hình DSR | SVG khái niệm |
| H2-33 đường R(t) | đã vẽ ở Phiên 0b |
| H2-34 khoảng ôn theo 4 chuỗi đánh giá | mô phỏng bằng `fsrs` 6.3.2: Good liên tục 2 → 11 → 46 → 163 ngày; sau Again rút còn 3 ngày |

- **Chưa làm:** H2-25 (NLLB, mức C; nội dung đã có trong phần lời); H2-30 (BLEU, thay bằng hộp Ví dụ 2.3).
- **Tài liệu tham khảo:** danh mục có 53 mục (thêm 16), 52 mục được trích dẫn.

### Đối chiếu với code

| Nội dung | Nguồn |
|---|---|
| NLLB qua CTranslate2: `float16` trên GPU, `int8` trên CPU; `beam_size = 2`, `length_penalty = 1` (mặc định CTranslate2, service không ghi đè) | `llm_service.get_nllb_translator`, `translation_service.py`, docstring của `translate_batch` (CTranslate2 4.6 trên máy) |
| Fusion: trọng số (0,55; 0,45), đảo khi văn bản ngắn; 7 đặc trưng meta; ngưỡng 0,80 / 0,88 / 0,85; hiệu chỉnh trên 327 mẫu dev | `language_detection.py`, `models/detect_calibration.json` |
| Điểm từ vựng min(2; 1 + 0,5(n − 1)); κ_min = 0,75; δ = 2 (chưa tinh chỉnh bằng dữ liệu) | `domain_detection.py`, `DOMAIN_DETECTION.md` §3 |
| Lesk = `simple_lesk` (pywsd), từ loại lấy từ spaCy, dự phòng là nghĩa phổ biến nhất | `word_analysis_service.py` |
| `edge-tts` 7.3.1, `VOICE_MAP` | `tts_service.py`, `requirements.txt` |
| BLEU/chrF bằng sacreBLEU, cấu hình mặc định | `evaluation/run_bleu_chrf.py` |
| FSRS-6: 21 tham số mặc định, các công thức S₀, D, S_r, S_f, ngắn hạn | mã nguồn gói `fsrs` 6.3.2 |

### Cần nhóm bổ sung

- Danh mục tài liệu tham khảo còn thiếu ngày truy cập của các trang web (CTranslate2, Lingua, edge-tts, FSRS wiki). Các mục này sẽ được rà lại ở Phiên 15.

---

## Phiên 4 – Mục 2.5–2.7 và tiểu kết Chương 2 (30/10/2026)

### Đã làm

- **Bản thảo** `drafts/02_3_microservices_congnghe.md`. Khoảng 19 trang khi ghép. Gồm các phần:
  - 2.5.1–2.5.5: microservices, cổng API, REST/SSE/message broker, cache và CAS, JWT và bcrypt;
  - 2.6.1–2.6.5: công nghệ sử dụng, kèm **Bảng 2.4** về các mô hình AI;
  - 2.7: nghiên cứu liên quan, kèm **Bảng 2.5** đối chiếu với hệ thống;
  - tiểu kết Chương 2.
- **Công thức (2-52)…(2-55):** rate limit cửa sổ cố định, khóa CAS, chữ ký HS256, chi phí bcrypt.
- **9 hình** (mức A: 6/6; mức B: 3):

| Hình | Nguồn |
|---|---|
| H2-35 nguyên khối và microservices | Vế phải thể hiện đúng thực tế: dùng chung một Supabase, chia bảng theo service |
| H2-36 mẫu cổng API | Route lấy từ `kong.template.yml` |
| H2-37 cửa sổ cố định, L = 10 | Số liệu minh họa: 17 yêu cầu được cho qua trong khoảng 11 giây ở ranh giới cửa sổ |
| H2-38 REST / SSE / message broker | PlantUML, sự kiện thật của hệ thống |
| H2-39 topic exchange | Exchange, khóa và hàng đợi **thật**: `chatbot_events`, 3 khóa, 3 hàng đợi |
| H2-40 CAS | Khóa MD5 **tính thật**: "Tuition" và "tuition " cho cùng một khóa |
| H2-41 cấu trúc JWT | 7 claim thật, theo `auth_service.py` |
| H2-42 bản đồ công nghệ | Theo `package.json`, `requirements*.txt`, compose |
| H2-43 dòng thời gian RAG | Khớp Bảng 2.5 |

- **Tài liệu tham khảo:** danh mục có 70 mục (thêm 17), 69 mục được trích dẫn. Trong đó có:
  - cuốn khóa luận QuyLong, dùng làm công trình liên quan trong nước;
  - SpatioRoute, chỉ trích khi nói về định tuyến prompt, đúng lưu ý của kế hoạch.

### Đối chiếu với code (điểm mới)

| Nội dung | Ghi chú |
|---|---|
| Rate limit | Toàn cục 1 000/phút; route TTS 100/phút; đăng nhập/đăng ký 10/phút và 100/giờ; `policy: local` |
| JWT | Có **7 claim**, gồm cả `oiat` (thời điểm đăng nhập gốc, giới hạn phiên 7 ngày); kế hoạch cũ thiếu claim này. Kong kiểm tra `exp`, thời hạn tối đa 86 400 giây, khóa tra theo `iss = iuh-auth-service` |
| Khóa CAS | Là `terms/{ℓ₂}_{MD5(ℓ₂ + "_" + lower(strip(w)))}.mp3`. Chuỗi được băm **có chứa cả mã ngôn ngữ**, khác công thức ghi trong kế hoạch |
| Khóa cache dịch | SHA-256 của văn bản đã chuẩn hóa NFC, kèm cặp ngôn ngữ, chuyên ngành và phiên bản từ điển |
| Hạ tầng | Redis `--maxmemory 128mb --maxmemory-policy allkeys-lru`; image `kong:3.9.3`, `python:3.11-slim`, `node:22-alpine`, `nginx:alpine` |

### Lưu ý về độ dài

Chương 2 hiện khoảng **72 trang** (trang 14–85 trong bản ghép), gần gấp đôi kế hoạch 40–45 trang. Nguyên nhân chính:
- giải thích ký hiệu được trình bày thành danh sách gạch đầu dòng;
- có 39 hình;
- có 55 công thức.

Các cách rút gọn có thể chọn khi GVHD góp ý:
1. Gộp phần "trong đó" của các công thức đơn giản thành một câu.
2. Bỏ bớt các hình mức B: H2-03, H2-04, H2-06, H2-24, H2-26, H2-37, H2-43.
3. Rút gọn mục 2.1, vốn là lý thuyết LLM phổ thông.

## Phiên 5a – Mục 3.1 Phân tích yêu cầu và 3.2 Use case (30/10/2026)

### Đã làm

- **Bản thảo** `drafts/03_1_yeu_cau_usecase.md`. Khoảng 31 trang khi ghép (trang 86–116). Gồm các phần:
  - phần mở đầu Chương 3;
  - 3.1.1 tác nhân, kèm **Bảng 3.1** và sơ đồ ngữ cảnh H3-01;
  - 3.1.2 yêu cầu chức năng, kèm **Bảng 3.2** gồm 23 yêu cầu YC01–YC23, mỗi yêu cầu gắn với use case;
  - 3.1.3 yêu cầu phi chức năng, kèm **Bảng 3.3**. Bảng chỉ nêu biện pháp đã cài đặt, không ghi số đo hiệu năng; mức đáp ứng để Chương 5 đánh giá;
  - 3.2.1–3.2.6: sơ đồ tổng quát, 5 sơ đồ phân hệ và **18 bảng đặc tả UC01–UC18** (Bảng 3.4–3.21). Mỗi use case có một heading cấp 4 riêng.
- **7 hình** (H3-01, H3-03…H3-07 vẽ mới; H3-02 sửa tác nhân thành "Người dùng (IUH, công cộng)"). Tất cả vẽ bằng PlantUML và tô màu theo phân hệ. Trên các sơ đồ phân hệ có quan hệ «include» và «extend».
- **Công cụ:**
  - `filters.lua` có thêm khối ```` ```{.usecase caption="Bảng 3.x. …"} ```` để sinh bảng đặc tả theo mẫu ở mục 2.3 của kế hoạch. Cột nhãn được gộp dọc. Luồng chính chia hai cột Tác nhân | Hệ thống, mỗi hàng là một lượt (các bước của tác nhân đặt cạnh phản hồi của hệ thống), giữ nguyên số thứ tự bước.
  - `build_report.py` đặt `tblLayout fixed` cho bảng đặc tả (tỉ lệ cột 22/39/39) để Word không tự co cột nhãn.
  - Bảng dài hơn 20 hàng được phép ngắt trang và lặp lại dòng đầu "Use case …". Hiện chỉ có UC05 và UC10 bị ngắt.

### Đối chiếu với code (điểm mới)

| Nội dung | Ghi chú |
|---|---|
| Vai trò | Có thêm `public`, đã ghi vào **kế hoạch mục 11, điểm 21**. `admin` không bao giờ được tạo qua đăng ký |
| Đăng ký | Trả HTTP 201 kèm token, nghĩa là đăng nhập ngay. Mật khẩu 8–72 byte, có cả chữ và số, không quá phổ biến, không trùng email hoặc MSSV. Họ tên 2–100 ký tự. Trùng email hoặc MSSV trả HTTP 409 |
| Đăng nhập | Bằng email hoặc MSSV. Khóa 15 phút sau 5 lần sai theo (IP, tài khoản) hoặc 30 lần sai theo tài khoản. Luôn so khớp bcrypt (dùng chuỗi băm giả khi không có tài khoản) để chống dò tài khoản |
| Thu hồi token | `logout` và `change-password` tăng `token_version`; `change-password` trả token mới |
| Hạn mức sinh từ vựng | admin 50, student 10, public 3 lượt mỗi ngày. Lần sinh lỗi được hoàn lượt (`vocab_quota.refund`) |
| Lưu từ từ trang dịch | Không chọn sổ thì lưu vào sổ mặc định "Từ vựng <tên ngôn ngữ>". Tiếng Việt là ngôn ngữ giải nghĩa nên bị từ chối. Sổ khác ngôn ngữ hoặc từ trùng trả HTTP 409 (hoặc cập nhật thẻ cũ, tùy `on_duplicate`) |
| Phân tích từ | Lesk lỗi thì dùng nghĩa đầu tiên của WordNet. Nguồn không phải tiếng Anh hoặc WordNet lỗi thì chỉ dịch từ bằng NLLB |
| OCR khi nạp tri thức | Gemini; nếu API lỗi thì dùng Tesseract (`pdf_extractor.py`) |
| Từ điển chuyên ngành | Thêm mục trùng trả HTTP 400; nhập tệp chỉ nhận `.csv` hoặc `.json` với các cột `domain`, `word`, `translation` |
| Phiên hội thoại | Đổi tên: bỏ khoảng trắng hai đầu, cắt còn 100 ký tự, tên rỗng thì báo lỗi. Danh sách phiên được tải theo trang |

### Cần nhóm xem lại

- Cách chia use case: 18 use case được gộp chức năng theo màn hình. Chức năng xóa bộ nhớ đệm (YC23) của admin chỉ xuất hiện trên H3-04, không có bảng đặc tả riêng.
- Bảng 3.3 chưa có số liệu đáp ứng. Ở Chương 5 cần đo và đối chiếu lại các yêu cầu này.
- Chương 3 sẽ dài hơn kế hoạch nếu Phiên 5b vẽ thêm 14 sơ đồ tuần tự và 3 sơ đồ hoạt động. Nếu cần rút gọn, có thể chuyển một phần bảng đặc tả (ví dụ UC11, UC14, UC15, UC17) sang Phụ lục.

## Phiên 5b – Mục 3.2 Sơ đồ tuần tự và sơ đồ hoạt động (30/10/2026)

### Đã làm

- **18 hình mới**, tất cả bằng PlantUML. Trong `03_1_yeu_cau_usecase.md`, mỗi hình đặt ngay sau bảng đặc tả tương ứng, có một câu dẫn nêu điểm đáng chú ý của luồng:
  - **15 sơ đồ tuần tự:** H3-08a (UC01), H3-08b (UC02), H3-09 (UC03), H3-10 (UC04), H3-11 (UC05, mức tổng quan; chi tiết ở H4-11a/b), H3-12 (UC06), H3-13 (UC07–UC08 chung), H3-14 (UC09), H3-15 (UC10), H3-16 (UC11), H3-17 (UC12), H3-18 (UC13), H3-19 (UC14), H3-20 (UC16), H3-21 (UC17–UC18 chung). H3-08 trong kế hoạch được tách thành a/b vì cao gần 30 cm.
  - **3 sơ đồ hoạt động:** H3-22 (UC12, gồm nhánh dự phòng khi không nạp được FSRS), H3-23 (UC16, xử lý theo từng loại nguồn), H3-24 (UC15, chấm điểm và cập nhật lịch ôn phía máy chủ).
- Các hình của Chương 3 được đánh lại số theo thứ tự xuất hiện (Hình 3.1–3.25); câu dẫn và `FIGURES.md` đã đồng bộ.
- **Công cụ:**
  - thêm `figures/src/_theme/seq.iuml`, chứa các thiết lập chung của sơ đồ tuần tự (màu participant theo phân hệ, tự đánh số bước);
  - `build_report.py` có thêm giới hạn **cao tối đa 20 cm** (`MAX_FIGURE_HEIGHT`), trước đây chỉ giới hạn chiều rộng. Hình quá cao được thu nhỏ theo tỉ lệ; cỡ chữ in nhỏ nhất ở Chương 3 khoảng 9 pt (Hình 3.12).
- Phần 3.1–3.2 hiện dài khoảng **49 trang** (trang 86–134).

### Sửa lại đặc tả của Phiên 5a sau khi đối chiếu sâu hơn

| Use case | Nội dung sửa |
|---|---|
| UC03, UC04 | Thu hồi token chỉ có hiệu lực ở Auth Service (kế hoạch mục 11, điểm 22) |
| UC07 | Luồng chính dùng `/stream`, nhánh này không có bộ nhớ đệm; chuyển `/text` (ô dịch nhanh, có bộ nhớ đệm) xuống luồng phụ (điểm 25) |
| UC13, YC16, YC19 | Thêm nguồn sinh từ ảnh (JPG, PNG, WEBP, tối đa 5 MB). Kong giới hạn thêm 60 yêu cầu/giờ. VERIFY là một lượt LLM kiểm duyệt. Lưu sổ AI sinh **không** phát sự kiện sinh âm thanh (điểm 23) |
| UC14 | Bản sao bộ từ mẫu đã có thì mở lại, không tạo trùng; nhập nhận cả CSV; từ trùng được bỏ qua |
| UC15 | Trò chơi chạy theo **sổ thẻ**, không theo ngôn ngữ. Máy chủ tính điểm, sao, XP; có thể ghi lượt ôn FSRS (Again/Hard/Good) cho thẻ đến hạn. Gửi lại cùng mã yêu cầu thì không chấm lần hai |
| UC16 | Thêm luồng phụ khi đang có tiến trình nạp khác; ghi rõ cách loại đoạn trùng và cách thay đoạn cũ theo URL nguồn |
| UC18 | Import là upsert (ghi đè bản dịch cũ); sinh âm thanh cho mục mới ở nền; không ghi mã lỗi (điểm 24) |

### Phát hiện mới (đã ghi vào kế hoạch mục 11, điểm 22–25)

1. **Phạm vi thu hồi token:** sau khi đăng xuất, token cũ vẫn gọi được các service khác tối đa 60 phút.
2. **Âm thanh thẻ học:** giao diện phát âm theo văn bản qua `/translate/tts`; tệp CAS do sự kiện `flashcard.created` sinh ra gần như không được dùng khi phát.
3. **Lỗi mã HTTP ở từ điển chuyên ngành:** lỗi 400 bị đổi thành 500.
4. **Bộ nhớ đệm dịch:** trang Dịch thuật (nhánh thông thường) không dùng bộ nhớ đệm.

Điểm 1, 3 sẽ đưa vào phần hạn chế ở Chương 6. Điểm 2, 4 ảnh hưởng cách viết mục 4.3, 4.4 và cách đo ở Chương 5.

### Cần nhóm xem lại

- Chương 3 sẽ còn dài thêm khi viết 3.3–3.7 (Phiên 6). Nếu cần rút gọn, có thể chuyển các cặp bảng và hình của UC11, UC14, UC17–UC18 sang Phụ lục.
- Giới hạn chiều cao 20 cm áp dụng cho mọi hình. Đã kiểm tra: hiện chỉ các hình của Chương 3 bị thu nhỏ theo giới hạn này.

## Phiên 6 – Mục 3.3–3.7 và tiểu kết Chương 3 (31/10/2026)

### Đã làm

- **Bản thảo** `drafts/03_2_kien_truc_csdl_api.md`. Khoảng 44 trang khi ghép (trang 135–178). Gồm các phần:
  - 3.3 Kiến trúc: thành phần (Bảng 3.22), route Kong (Bảng 3.23), ba kiểu giao tiếp, RabbitMQ, phân lớp service, triển khai và tài nguyên (Bảng 3.24);
  - 3.4 CSDL: phân chia theo service, ERD tổng thể, 4 nhóm bảng với 10 bảng thuộc tính (Bảng 3.25–3.34), khóa Redis (Bảng 3.35);
  - 3.5 API: quy ước và định dạng lỗi, mã HTTP (Bảng 3.36), nhóm endpoint (Bảng 3.37), sự kiện SSE (Bảng 3.38);
  - 3.6 Bảo mật: hai lớp kiểm tra JWT, vòng đời phiên, mô hình đe dọa đối chiếu OWASP Top 10:2021 (Bảng 3.39);
  - 3.7 Giao diện: route (Bảng 3.40), hệ thống thiết kế;
  - tiểu kết Chương 3.
- **20 hình (Hình 3.26–3.45):**
  - H3-25 vẽ từ Phiên 0b, sửa lại mũi tên: Chatbot dùng SSE, Flashcard không dùng SSE.
  - H3-26…H3-44 mới. PlantUML cho sơ đồ tuần tự, ERD, trạng thái, sitemap. SVG cho H3-30 (triển khai), H3-38 (định dạng phản hồi), H3-41 (lớp phòng thủ).
  - Python cho H3-43 (hệ thống thiết kế, dùng logo thật trong `frontend/src/assets/brand/`) và H3-44 (ghép ba ảnh `login-360/768/1280.png` có sẵn trong repo; trang đăng nhập không chứa dữ liệu người dùng).
- **Tài liệu tham khảo:** thêm `owasp_top10`. Danh mục còn 71 mục, 70 mục được trích dẫn.
- **Công cụ:**
  - thêm `figures/src/_theme/erd.iuml`;
  - ERD chuyển từ Mermaid sang PlantUML, vì bản Mermaid rộng 40 cm (đã ghi vào kế hoạch mục 3.2).

### Sửa thêm ở các phần trước

- Bản thảo 03_1: tên bốn trò chơi theo đúng giao diện (Ghép cặp, Đua 60 giây, Xếp chữ, Bắn bóng nghĩa); UC05 thêm giới hạn câu hỏi 2 000 ký tự.
- H3-11: bước tra bộ nhớ đệm ghi rõ "sau khi tra Redis khớp chính xác".

### Phát hiện mới (kế hoạch mục 11, điểm 26–28)

1. **Giới hạn tần suất của Kong gộp theo consumer:** cấu hình không đặt `limit_by`, mọi JWT chung consumer `auth-issuer`. Theo tài liệu của Kong, giới hạn trên route có JWT (kể cả 6 lượt/phút sinh từ vựng) có thể dùng chung cho **mọi** người dùng. Cần kiểm chứng ở Chương 5.
2. **RabbitMQ không thử lại** sự kiện xử lý lỗi: lỗi chỉ được ghi log, tin nhắn vẫn được ack.
3. **Định dạng lỗi API chưa thống nhất** giữa các service; client của Chatbot ở giao diện chỉ báo lỗi chung kèm mã HTTP.

Ngoài ra, đã xác nhận ba điểm:
- Hàm RRF được gọi với `match_count = 50`, nên mỗi nhánh lấy 100 ứng viên (khớp điểm 20).
- Cột `messages.feedback` có trong schema nhưng chưa có endpoint ghi.
- Bộ đếm chống dò mật khẩu nằm trong bộ nhớ của tiến trình Auth.

### Cần nhóm quyết định

- **Độ dài Chương 3:** hiện khoảng **93 trang** (86–178), kế hoạch là 30–35 trang. Các phương án rút gọn:
  1. Chuyển 10 bảng thuộc tính (Bảng 3.25–3.34) sang Phụ lục, chỉ giữ ERD trong chương. Giảm khoảng 10 trang.
  2. Chuyển bảng đặc tả và sơ đồ của các use case phụ (UC03, UC04, UC06, UC11, UC14, UC17, UC18) sang Phụ lục. Giảm khoảng 15–18 trang.
  3. Bỏ Hình 3.28 (ba kiểu giao tiếp), vì nội dung đã có ở các sơ đồ tuần tự Hình 3.9, 3.12, 3.14. Bỏ Hình 3.32 (phân chia bảng), vì ERD tổng thể Hình 3.33 đã tô màu theo service.
- Hình 3.45 dùng ảnh chụp có sẵn trong repo, không cần chạy Docker. Nhóm xem có muốn thay bằng ảnh chụp mới không.

## Phiên 6b – Rút gọn Chương 3 (31/10/2026)

Nhóm yêu cầu rút Chương 3 về độ dài theo kế hoạch (khoảng 45 trang). Kết quả: **47 trang** (trang 86–132), trước đó là 93 trang. Toàn bộ báo cáo hiện có 184 trang.

### Đã làm

- **Mục 3.2:** giữ toàn bộ sơ đồ use case, và chỉ giữ đặc tả cùng sơ đồ của **một use case tiêu biểu cho mỗi phân hệ**: UC02, UC05, UC08, UC12, UC16. Đặc tả và sơ đồ của 13 use case còn lại chuyển sang **Phụ lục B**. Sơ đồ hoạt động của UC12 và UC16 cũng ở Phụ lục B.
- **Mục 3.3–3.7:**
  - Bỏ ba hình trùng ý: ba kiểu giao tiếp, phân chia bảng theo service (ERD tổng thể đã tô màu theo service), các lớp phòng thủ (đã có bảng mô hình đe dọa).
  - Bỏ bảng các thành phần, vì hình kiến trúc đã thể hiện.
  - Bỏ bảng route của giao diện, vì sơ đồ điều hướng đã thể hiện.
  - Chuyển sang **Phụ lục C:** luồng qua Kong, định dạng phản hồi, mã HTTP, nhóm endpoint, sự kiện SSE. Trong chương chỉ giữ phần tóm tắt bằng lời.
  - Chuyển sang **Phụ lục E:** 10 bảng thuộc tính và luồng hàm RRF.
  - Chuyển sang **Phụ lục A:** bảng giới hạn tài nguyên.
- **Tệp mới:** `drafts/91_phu_luc.md` có khung đủ Phụ lục A–F. B, C (trừ danh sách endpoint đầy đủ) và E đã có nội dung; A, D, F còn ghi chú TODO cho Phiên 15.
- **Công cụ:**
  - `filters.lua`: hình và bảng trong phụ lục được đánh số theo chữ cái (Hình B.1, Bảng E.3) và vẫn vào danh mục hình, danh mục bảng (trường `SEQ` đặt lại ở đầu mỗi phụ lục).
  - **`build/renumber.py` (mới):** đánh số lại toàn bộ Hình/Bảng viết tay trong các bản thảo sau khi thêm, bớt hoặc chuyển. Hình nhận theo mã ảnh, bảng nhận theo chú thích; mọi câu nhắc cũng được đổi theo. Chạy `python build/renumber.py --dry-run` để xem trước.
- Kế hoạch: cập nhật danh sách phụ lục (A–F) và mục 3.5.2. `FIGURES.md`: cột "Mục" của các hình đã chuyển ghi `PL B`, `PL C`, `PL E`; ba hình bị bỏ ghi `bỏ (Phiên 6b)`.

### Cấu trúc Chương 3 hiện tại

| Mục | Nội dung | Trang |
|---|---|---|
| 3.1 | Tác nhân, 23 yêu cầu chức năng, yêu cầu phi chức năng | 86–90 |
| 3.2 | 6 sơ đồ use case; 5 đặc tả và sơ đồ tiêu biểu | 91–108 |
| 3.3 | Kiến trúc, route Kong, RabbitMQ, phân lớp, triển khai | 109–116 |
| 3.4 | 5 ERD, chỉ mục, khóa Redis | 117–123 |
| 3.5–3.7 | Quy ước API, SSE, bảo mật, điều hướng, hệ thống thiết kế, tiểu kết | 124–132 |

Bản sao các bản thảo trước khi rút gọn được lưu trong scratchpad của phiên làm việc (`backup_p6/`).

## Phiên R1 – Công cụ ngân sách trang và rút gọn Chương 1 (31/10/2026)

### Công cụ

- **Báo cáo ngân sách trang:** `build_report.py --word --pdf` giờ in số trang thực tế của từng chương, tài liệu tham khảo và cả phần chính, so với `page_budget` trong `report_config.json`. Chương nào vượt quá 10% ngân sách được đánh dấu `VƯỢT`. Trang bắt đầu của mỗi chương được nhận theo dòng tiêu đề "CHƯƠNG n" trong PDF (bỏ qua dòng mục lục).
- **`renumber.py` đánh số lại cả công thức:** `	ag{c-k}` được đánh lại theo thứ tự trong từng chương (một chương có thể nằm trong nhiều tệp), và các câu nhắc dạng "(c-k)" đổi theo. Đã chạy thử: khi chưa sửa bản thảo, công cụ không đổi gì.
- **`report_config.json`:** danh sách tệp Chương 4 đổi theo dàn ý V2: `04_1_ingestion.md`, `04_2_chatbot.md`, `04_3_phan_he_ho_tro.md`.

### Chương 1 (13 → 8 trang)

- **1.1:** chatbot học vụ là lý do chính. Nhu cầu dịch và học từ vựng còn một đoạn ngắn. Phần chọn đề tài ghi rõ trọng tâm và tiện ích hỗ trợ. Bỏ hình "Ba nhu cầu" (H1-02).
- **1.2:** gộp bốn tiểu mục thành ba. Bỏ tiểu mục "Công cụ dịch và học từ vựng". Bảng 1.1 còn 3 cột (website, chatbot LLM tổng quát, hệ thống của đề tài) và 5 tiêu chí xoay quanh chatbot, thêm hai tiêu chí: cập nhật khi văn bản thay đổi, từ chối câu hỏi ngoài phạm vi.
- **1.3:** mục tiêu cụ thể chia thành nhóm chính (chatbot, 5 mục) và nhóm hỗ trợ (4 mục). Bỏ hình giao diện bốn phân hệ (H1-04).
- **1.4:** viết gọn; người dùng gồm thêm vai trò `public`, khớp với Chương 3. Phạm vi đánh giá chuyên sâu là chatbot.
- **1.5:** viết thành danh sách 6 bước ngắn. Bỏ hình quy trình (H1-05).
- **1.6:** còn 5 đóng góp, các đóng góp về RAG lên trước.
- **1.7, tiểu kết:** viết thành đoạn văn.
- Bỏ ghi chú TODO về tệp `tb-892` (đã có trong mục Phiên 1 của tệp này); còn 2 ghi chú TODO cho nhóm.
- Hình còn lại: H1-01 (Hình 1.1), H1-03 (Hình 1.2), thu nhỏ còn 12,5–13 cm.

### Số trang sau phiên

| Chương 1 | Chương 2 | Chương 3 | TLTK | Phần chính |
|---|---|---|---|---|
| **8** / 8 | 72 / 24 | 47 / 22 | 8 / 4 | 136 / 130 |

Chương 2, 3 và tài liệu tham khảo sẽ được rút ở Phiên R2, R3.

## Phiên R2 – Rút gọn Chương 2 (31/10/2026)

Chương 2 từ **72 xuống 24 trang**, đúng ngân sách. Giữ ba tệp bản thảo, phân bố lại nội dung.

### Cấu trúc mới

| Mục | Nội dung | Từ bản cũ |
|---|---|---|
| 2.1 Mô hình ngôn ngữ lớn (3 tiểu mục) | Transformer và attention; sinh văn bản (nhiệt độ, top-p) và kỹ thuật prompt; ba hạn chế của LLM | 2.1.1–2.1.4 cũ, bỏ mã hóa vị trí, MoE, mục tiêu tự hồi quy dạng công thức |
| 2.2 RAG (7 tiểu mục) | Giữ đủ 7 tiểu mục cũ: kiến trúc, Bi/Cross-Encoder, HNSW, FTS và RRF, kỹ thuật nâng cao, phân đoạn, độ đo | Rút ví dụ (còn Ví dụ 2.1 về RRF), bỏ công thức mean pooling, InfoNCE, Cross-Encoder, HNSW, TF-IDF, BM25, ts_rank_cd, multi-query, P@K, nDCG; bỏ Bảng 2.2 (chiến lược phân đoạn, đã có Hình 2.10) |
| 2.3 Nền tảng cho các phân hệ hỗ trợ | 2.3.1 Dịch máy nơ-ron và xử lý ngôn ngữ (NLLB, CTranslate2, nhận diện ngôn ngữ, chuyên ngành, Lesk, TTS) · 2.3.2 Lặp lại ngắt quãng và FSRS (giữ R(t,S), I(r,S)) | 2.3 + 2.4 cũ (20 trang → khoảng 3 trang); bỏ BLEU, chrF, SM-2, lượng tử hóa, Bảng 2.3 |
| 2.4 Kiến trúc và công nghệ | 2.4.1 Microservices và cổng API · 2.4.2 Giao tiếp, lưu trữ và xác thực · 2.4.3 Công nghệ và mô hình | 2.5 + 2.6 cũ; Bảng 2.1 và 2.4 cũ gộp thành Bảng 2.1 |
| 2.5 Nghiên cứu liên quan | Hai đoạn văn | 2.7 cũ, bỏ Bảng 2.5 và hình dòng thời gian |

### Số liệu

- **Công thức:** 55 → **10**: attention, nhiệt độ, cosine, RRF, sandwich, điều kiện trùng cache, Hit Rate, MRR, R(t,S), I(r,S). Ký hiệu được giải thích trong câu văn.
- **Hình:** 39 → **13**. 30 hình còn lại (gồm cả hình giữ chỗ) đánh dấu `bỏ (V2)` trong `FIGURES.md`; tệp vẫn giữ.
- **Bảng:** 5 → 1.
- **Tài liệu tham khảo:** bỏ 16 tài liệu không còn được trích dẫn (bahdanau2015, fielding2000, jacob2018, krawczyk1997hmac, lesk1986, miller1995, oord2018, papineni2002, popovic2015, post2018, quinlan2002, redis_docs, shazeer2017moe, su2024rope, sutskever2014, wozniak1994). Còn 55 mục, 54 được trích dẫn; `iuh_quyche` giữ lại chờ nhóm bổ sung.
- **Ghi chú TODO:** bỏ TODO về chế độ gộp của Bi-Encoder (văn bản không còn khẳng định cách gộp). Còn 2 TODO: `ef_search` của HNSW và cấu hình LLM khi chạy demo.
- Sửa tham chiếu chéo trong Chương 3 và Phụ lục E theo số mục mới (2.5.1 → 2.4.1; 2.5.5 → 2.4.2; 2.4.3 → 2.3.2).

### Cần nhóm quyết định

- **Tài liệu tham khảo:** hiện **6 trang** với 55 mục; ngân sách 4 trang tương ứng khoảng 40 mục. Đề xuất nâng ngân sách tài liệu tham khảo lên 6 trang, lấy từ 8 trang dự phòng (phần chính vẫn ≤ 130). Nếu giữ 4 trang thì phải bỏ thêm khoảng 15 tài liệu, chủ yếu các tài liệu kỹ thuật (tài liệu hướng dẫn của Kong, Docker, React…).

### Số trang sau phiên

| Chương 1 | Chương 2 | Chương 3 | TLTK | Phần chính |
|---|---|---|---|---|
| 8 / 8 | **24** / 24 | 47 / 22 | 6 / 4 | 85 / 130 |

## Phiên R3 – Rút gọn Chương 3 và sắp lại phụ lục (31/10/2026)

Ngân sách tài liệu tham khảo được nâng lên 6 trang theo đề xuất ở Phiên R2 (dự phòng còn 6 trang); đã cập nhật `report_config.json` và `KE_HOACH_V2.md`.

Chương 3 từ **47 xuống 22 trang**, đúng ngân sách.

### Chương 3

| Mục | Thay đổi |
|---|---|
| 3.1 | Bỏ sơ đồ ngữ cảnh (trùng với sơ đồ use case tổng quát). Bảng 3.2 yêu cầu chức năng còn 12 dòng: chatbot và quản trị tri thức tách chi tiết (YC01–YC07), mỗi phân hệ hỗ trợ gộp 1–2 dòng. Bảng 3.3 còn 7 dòng. |
| 3.2 | Chỉ đặc tả hai use case trọng tâm: UC05 Hỏi đáp học vụ (kèm sơ đồ tuần tự) và UC16 Nạp tri thức (kèm sơ đồ tuần tự). Use case của các phân hệ hỗ trợ là Bảng 3.6, mỗi use case một dòng. |
| 3.3 | Bảng route Kong còn 6 nhóm. Phân lớp bên trong service, thứ tự plugin, luồng giao tiếp viết thành đoạn văn. Bỏ hình RabbitMQ và hình phân lớp. |
| 3.4 | Giữ ERD tổng thể và ERD nhóm RAG. Người dùng/hội thoại, Flashcard, Dịch thuật mỗi nhóm một đoạn; ERD của hai nhóm đầu chuyển sang Phụ lục E. Bỏ hình lưu trữ dịch thuật và bảng khóa Redis. |
| 3.5 | Quy ước API và ba luồng SSE viết thành đoạn văn. |
| 3.6 | Bỏ hình vòng đời token. Bảng mô hình đe dọa còn 6 dòng. |
| 3.7 | Giữ sơ đồ điều hướng; hệ thống thiết kế còn một câu. Bỏ hình hệ thống thiết kế; hình đăng nhập ba độ rộng (H3-44) để dành cho mục 4.4. |

Chương 3 còn **9 hình, 8 bảng**.

### Phụ lục (21 trang, A, D, F còn TODO)

- **B. Use case bổ sung:** sơ đồ use case phân hệ Quản trị, Xác thực, Dịch thuật, Flashcard; 5 đặc tả (UC06, UC17, UC02, UC08, UC12). Đặc tả UC08 được sửa để không còn nhắc tới UC07. Bỏ 8 đặc tả và toàn bộ sơ đồ tuần tự, sơ đồ hoạt động của phân hệ hỗ trợ.
- **C. Thiết kế API:** bảng nhóm endpoint, định dạng phản hồi (Hình C.1), mã HTTP, sự kiện SSE (bảng và Hình C.2). Bỏ hình luồng qua Kong.
- **E. Lược đồ CSDL:** luồng hàm RRF, 6 bảng thuộc tính (nhóm RAG, người dùng, hội thoại), ERD người dùng và hội thoại, ERD Flashcard. Bỏ 4 bảng thuộc tính của Flashcard và từ điển.

### Hình

- Trong `FIGURES.md`, cột "Mục" của mọi hình Chương 3 đã cập nhật: 9 hình trong chương, 9 hình trong phụ lục, H3-23 và H3-44 để dùng lại ở 4.1 và 4.4, 25 hình còn lại đánh dấu `bỏ (V2)` (vẫn giữ tệp).
- Cách làm: viết khung cho từng tệp (lưu trong scratchpad, thư mục `r3/`), script trích nguyên văn các bảng và đặc tả cần giữ từ bản cũ rồi đánh số lại. Bản sao trước khi rút gọn lưu ở `backup_r3/`.

### Số trang sau phiên

| Chương 1 | Chương 2 | Chương 3 | TLTK | Phần chính | Phụ lục |
|---|---|---|---|---|---|
| 8 / 8 | 24 / 24 | **22** / 22 | 6 / 6 | 60 / 130 | 21 |

Ba phiên rút gọn đã xong. Phần chính còn 70 trang ngân sách cho Chương 4 (42), Chương 5 (18), Chương 6 (4) và 6 trang dự phòng.

## Phiên 7 – Mục 4.1 Pipeline thu thập và xử lý tri thức (31/10/2026)

Tệp mới `drafts/04_1_ingestion.md`, gồm tiêu đề và lời dẫn Chương 4 cùng mục 4.1. Chiếm **8 trang** (ngân sách 9).

| Mục | Nội dung | Đối chiếu mã nguồn |
|---|---|---|
| 4.1 (mở đầu) | Hai cách chạy: CLI và API quản trị | `run_pipeline.py`, `routers/admin_ingest.py` |
| 4.1.1 | Bảng 4.1: nguồn (sitemap, danh mục ≤ 10 trang, BFS độ sâu 2/5/4/3, 4 URL tuyển sinh, quản trị viên); lọc 5 tên miền | `sources.py`, `extractors/url_extractor.py`, `utils/url_helpers.py` |
| 4.1.2 | Crawler 5 luồng, trafilatura, PDF đính kèm, frontmatter, bỏ qua theo MD5; PDF dưới 50 ký tự → OCR 150 DPI ≤ 30 trang, Gemini (bỏ model lỗi 429, chờ 10 giây khi gặp lỗi 503) → Tesseract | `crawlers/content_crawler.py`, `html_utils.py`, `pdf_extractor.py`, `ocr_service.py` |
| 4.1.3 | `clean_noise`; đoạn cha theo tiêu đề ≤ 1 200 token (ước lượng max(từ, ký tự/4)); đoạn con 600/100, bảng lặp hàng tiêu đề; loại trùng MD5. Hình 4.2 là kết quả chạy chunker thật | `chunkers/hybrid_chunker.py`, `utils/text_cleaner.py` |
| 4.1.4 | `inject_meta` (ví dụ thật), `injected_content`, Bi-Encoder 768 chiều; upsert `documents`, xóa cũ, lô 25, thử lại 3 lần | `embedders/supabase_embedder.py` |
| 4.1.5 | 3 cách nạp, SSE `/status`, các trạng thái; 3 hạn chế (trạng thái trong bộ nhớ, phân đoạn lại cả thư mục tạm, `verify=False`) | `routers/admin_ingest.py` |
| 4.1.6 | Bảng 4.2 thống kê theo tên miền: **[CHỜ SỐ LIỆU]**, kèm câu SQL | Máy hiện tại không có dữ liệu nạp, cần chạy trên Supabase |

**Hình:** 3 hình.
- H4-01 là sơ đồ hoạt động PlantUML của toàn pipeline.
- H4-06 là đoạn cha thật tách thành 10 đoạn con. Script `figures/src/ch4/_data/H4-06_run_chunk.py` gọi chính `HybridChunker` của dự án (chỉ đọc) trên đoạn cha lấy từ log truy vấn, Chunk 1 của tệp `logs/academic_chatbot/2026-10-29/142502-quy-trinh-ang-ky-hoc.md`.
- H4-08 là ảnh giữ chỗ, nhóm sẽ chụp ở Phiên S.

Trong `FIGURES.md`, H4-02/03/04/05/07 và H3-23 được đánh dấu `bỏ (V2)`; H4-01 thay cho H3-23.

**Nhận xét rút ra từ mã nguồn, đã ghi trong báo cáo:**
- Phần chồng lấn của đoạn con bắt đầu giữa câu.
- Tên mục xuất hiện hai lần trong văn bản được sinh vector: tiền tố `[###### …]` của chunker và `[Mục: …]` của `inject_meta`.
- Ảnh nhúng trong trang web không được OCR (`extract_image_text` trả về chuỗi rỗng).

**Việc nhóm cần làm:** chạy câu SQL ở mục 4.1.6 trên Supabase rồi điền Bảng 4.2.

### Số trang sau phiên

| Ch.1 | Ch.2 | Ch.3 | Ch.4 | TLTK | Phần chính |
|---|---|---|---|---|---|
| 8 | 24 | 22 | 8 / 42 | 6 | 68 / 130 |

## Phiên 8a – Mục 4.2.1 đến 4.2.5 Chatbot (31/10/2026)

Tệp mới `drafts/04_2_chatbot.md`: phần mở đầu mục 4.2 và 4.2.1–4.2.5. Chiếm **12 trang** (ngân sách 12). Chương 4 hiện 19 trang.

| Mục | Nội dung | Đối chiếu mã nguồn |
|---|---|---|
| 4.2 (mở đầu) | Cấu trúc thư mục, nạp sẵn mô hình khi khởi động (ONNX nếu có) | `main.py`, `rag_service.preload_models` |
| 4.2.1 | Hai endpoint, 7 bước của `/stream`, Bảng 4.3 (5 nhánh: số lời gọi LLM, sự kiện SSE), lưu trữ | `routers/chat.py`, `llm_generation_service.py`, `chat_service.py` |
| 4.2.2 | Hai lớp guardrail: 35 mẫu regex (13 + 22) và nhãn `REJECTED_QUERY`; Bảng 4.4 chạy thật trên 7 câu mẫu | `guardrails/query_filter.py` |
| 4.2.3 | Router: JSON 3 trường, 7 intent, quy tắc giữ từ khóa, nhà cung cấp riêng, xử lý lỗi; Hình 4.6 là ví dụ thật | `rag_service.generate_standalone_query`, `llm_providers.py` |
| 4.2.4 | Cache hai tầng (0,60 / 0,80 / so khớp số), cổng chất lượng 4 điều kiện, TTL 24 giờ và 7 ngày, làm mới thủ công | `rag_service.check_semantic_cache`, `async_cache_writeback`, `match_semantic_cache` (SQL) |
| 4.2.5 | RPC RRF 50 ứng viên, rerank, ngưỡng 0,20 và 0,65, hạn mức (Bảng 4.5), trộn xen kẽ, Small-to-Big; Bảng 4.6 là kết quả thật | `rag_service.retrieve_relevant_chunks_multi`, `match_chunks_hybrid_rrf` (SQL) |

**Hình:** Hình 4.4 (H4-11a, đã vẽ lại tách hai nhánh từ chối và gọn hơn), Hình 4.5 (H4-11b), Hình 4.6 (H4-13), Hình 4.7 (H4-14, đổi dấu thập phân sang dấu phẩy), Hình 4.8 (H4-16, mới vẽ). **Bảng:** 4.3 đến 4.6.

**Số liệu có script đo:** Bảng 4.4 do `figures/src/ch4/_data/guardrail_check.py` sinh ra (kết quả trong `guardrail_check.json`; script nạp hàm của dự án bằng importlib, chỉ đọc). Bảng 4.6 và độ trễ truy xuất 2 374 ms lấy từ log `logs/academic_chatbot/2026-10-29/142502-quy-trinh-ang-ky-hoc.md` (cùng log dùng cho Hình 4.2 và Hình 4.6).

**Phát hiện khi đối chiếu mã** (đã thêm vào KE_HOACH_VIET_BAO_CAO.md §11, điểm 29–33): guardrail chặn nhầm hai câu hợp lệ; ngưỡng 0,92 của cache vô hiệu; cache lưu theo truy vấn đầu tiên và không tự xóa sau khi nạp lại; `get_adaptive_candidate_count` không được gọi; endpoint không streaming lưu tin nhắn người dùng hai lần; giới hạn 20/phút của slowapi cần kiểm chứng ở Chương 5 (điểm 33).

**Thay đổi công cụ:**
- `render_figures.py` không còn ghi đè trạng thái `bỏ (V2)` trong `FIGURES.md` (trước đó mỗi lần vẽ lại sẽ đưa các hình đã bỏ về "giữ chỗ").
- `build_report.py` đặt `cantSplit` cho mọi dòng bảng, không để một dòng bị cắt đôi giữa hai trang.

**Thay đổi so với kế hoạch:** bỏ H4-09, H4-10, H4-12, H4-15, H4-17 (đánh dấu `bỏ (V2)`): H4-11a/b đã thể hiện vòng đời nên không vẽ H4-10; guardrail và ví dụ truy xuất trình bày bằng Bảng 4.4 và 4.6.

### Số trang sau phiên

| Ch.1 | Ch.2 | Ch.3 | Ch.4 | TLTK | Phần chính |
|---|---|---|---|---|---|
| 8 | 24 | 22 | 19 / 42 | 6 | 80 / 130 |

Khoảng trống còn lại trong Chương 4: 23 trang (4.2.6–4.2.9 dự kiến 12, 4.3 là 6, 4.4 là 3, còn dư khoảng 2).

## Phiên 8b – Mục 4.2.6 đến 4.2.9 Chatbot (31/10/2026)

Nối thêm vào `drafts/04_2_chatbot.md`: 4.2.6–4.2.9, chiếm khoảng **10 trang** (ngân sách 12). Mục 4.2 hiện dài khoảng 22 trang (ngân sách 24); Chương 4 hiện 29/42 trang.

| Mục | Nội dung | Đối chiếu mã nguồn |
|---|---|---|
| 4.2.6 | Hình 4.9 khung prompt; Small-to-Big (`parent_content`); Sandwich theo công thức (2-5); thẻ cách ly; hai giới hạn (không thoát ký tự, thiếu `created_at`); bộ nhớ ngắn hạn 6 tin và dài hạn (`match_past_messages`, 0,8, 3 tin) | `guardrails/query_filter.py`, `rag_service.build_rag_payload`, `build_dynamic_system_instruction` |
| 4.2.7 | 9 quy tắc persona; Bảng 4.7 (7 intent); điểm yếu: niên khóa ghi cứng, few-shot chưa đối chiếu; lớp nhà cung cấp (hai cài đặt, nhiệt độ 0,2, tắt `enable_thinking`, thứ tự dự phòng); hai lưu ý (nối tiếp khi chuyển giữa chừng, chuỗi lỗi có thể vào cache) | `prompts/prompt_templates.py`, `services/llm_providers.py` |
| 4.2.8 | Self-RAG ở mức prompt (3 thẻ, chỉ dùng cho log và cổng cache); Bảng 4.8 (6 log); máy trạng thái lọc `<thinking>`; Hình 4.10 ví dụ thật; trích dẫn (cách chọn vị trí, snippet từ đoạn cha, danh sách là "đã đưa vào ngữ cảnh"); Hình 4.11 là ảnh giữ chỗ | `llm_generation_service.py`, `rag_service.build_rag_payload`, `frontend/.../ChatMessageBubble.tsx` |
| 4.2.9 | Lưu phiên, 4 endpoint quản lý phiên, 4 điểm thiếu kiểm soát quyền, nhật ký Markdown 3 loại | `routers/sessions.py`, `chat_service.py`, `log_utils.py` |

**Hình:** Hình 4.9 (H4-19, SVG mới), Hình 4.10 (H4-21, SVG mới, văn bản chép từ log 29/10/2026), Hình 4.11 (H4-24, ảnh giữ chỗ, Phiên S). **Bảng:** 4.7 và 4.8. Đã đánh dấu `bỏ (V2)`: H4-18, H4-20, H4-22, H4-23, H4-25.

**Số liệu có script đo:** Bảng 4.8 do `figures/src/ch4/_data/log_metrics.py` trích từ sáu log đầy đủ của ngày 29/10/2026 (kết quả trong `log_metrics.json`). Nội dung đã ghi rõ đây là sáu lượt riêng lẻ, không phải thống kê.

**Phát hiện khi đối chiếu mã** (KE_HOACH_VIET_BAO_CAO.md §11, điểm 34–38): chuyển nhà cung cấp giữa chừng nối đôi văn bản và chuỗi lỗi có thể vào cache; metadata thiếu `created_at`/`upload_time` nên luật CF-RAG không dùng được ngày cập nhật; phân quyền phiên thiếu ở 4 điểm; luật niên khóa ghi cứng và few-shot chưa đối chiếu; `match_past_messages` mới chỉ suy ra.

**Việc nhóm cần làm:**
- Chạy `SELECT pg_get_functiondef('match_past_messages'::regproc);` trên Supabase để kiểm tra mục 4.2.6.
- Kiểm tra vị trí "Phòng Tài chính – Kế toán tầng trệt nhà E" và "Trung tâm Quản trị Hệ thống tầng 1 nhà A" trong ví dụ mẫu của prompt.
- Chụp ảnh giao diện câu trả lời có trích dẫn cho Hình 4.11 (Phiên S).

**Lưu ý trang:** Chương 3 hiện 23 trang (ngân sách 22, vượt 4,5%, còn trong ngưỡng 10%) do thay đổi `cantSplit` ở bảng làm đổi chỗ ngắt trang; sẽ rà lại ở Phiên 13.

### Số trang sau phiên

| Ch.1 | Ch.2 | Ch.3 | Ch.4 | TLTK | Phần chính |
|---|---|---|---|---|---|
| 8 | 24 | 23 | 29 / 42 | 6 | 90 / 130 |

Chương 4 còn 13 trang ngân sách cho 4.3 (6), 4.4 (3) và tiểu kết (khoảng 1).

## Phiên 9 – Mục 4.3, 4.4 và tiểu kết Chương 4 (31/10/2026)

Tệp mới `drafts/04_3_phan_he_ho_tro.md`, chiếm khoảng **11 trang** (ngân sách 10: 4.3 khoảng 7,5 trang so với 6, 4.4 khoảng 3,3 trang, tiểu kết khoảng 0,5 trang). Chương 4 hiện **40/42 trang**, nằm trong ngân sách chung nên không cắt.

| Mục | Nội dung | Đối chiếu mã nguồn |
|---|---|---|
| 4.3.1 | 10 ngôn ngữ, `/text` ≤ 1 000 và `/stream` ≤ 3 000 ký tự; NLLB-200 600M qua CTranslate2 (INT8/float16), dự phòng Groq → Gemini; nhận diện ngôn ngữ (fastText + Lingua, chỉ `detected` mới dịch); dịch chuyên ngành (6 lĩnh vực, từ điển, `decide_domain`); phân tích từ; TTS và MinIO CAS. Hình 4.12 (H4-28), Hình 4.13 (ảnh giữ chỗ H4-33) | `routers/translation.py`, `services/translation_service.py`, `llm_service.py`, `domain_*.py`, `language_detection.py` |
| 4.3.2 | Sổ là đơn vị ngôn ngữ; FSRS (không bước học, New → Review); hàng đợi và kiểu ôn (tỉ lệ đã đối chiếu với `choose_study_mode`); pipeline sinh từ vựng (Hình 4.14 = H4-40); bộ từ mẫu clone-on-start; trò chơi (Bảng 4.9); Hình 4.15 (ảnh giữ chỗ H4-45) | `fsrs_algorithm.py`, `flashcard_service.py`, `vocab_pipeline.py`, `vocab_quota.py`, `catalog_service.py`, `game_logic.py` |
| 4.3.3 | Điểm cài đặt của Auth Service (bcrypt luôn chạy, bộ đếm trong bộ nhớ, từ chối khởi động khi khóa yếu), không lặp lại mục 3.6 | `auth_service.py`, `config.py`, `utils/throttle.py` |
| 4.3.4 | Dịch tài liệu: chưa triển khai (3 lớp khóa), ngoài phạm vi đánh giá | `docker-compose.yml`, `gateway/kong.template.yml`, `DEPLOY.md` |
| 4.4.1 | Kiến trúc 4 tầng frontend, luồng SSE bằng `fetch` + `ReadableStream`, thích ứng màn hình (Hình 4.16 dùng lại H3-44), giới hạn đã biết | `frontend/README.md`, `chatService.ts`, `package.json` |
| 4.4.2 | 9 container, Bảng 4.10 (3 tệp Compose xếp chồng), Funnel, nginx, CI (3 nhóm job, job RAG chỉ kiểm thử hàm độ đo), các điểm chưa kiểm chứng | `docker-compose*.yml`, `.github/workflows/ci.yml`, `DEPLOY.md` |
| Tiểu kết | Tóm tắt Chương 4 và các hạn chế sẽ chuyển sang Chương 6 | |

**Chỉnh sửa ngoài phạm vi phiên:** Bảng 3.8 (Chương 3) trước đó ghi "mọi thao tác trên sổ, thẻ, phiên đều kiểm tra chủ sở hữu"; đã sửa cho khớp phát hiện ở 4.2.9 (phiên hội thoại chatbot chưa kiểm tra) và bổ sung vào đoạn hạn chế ở cuối mục 3.6.

**Phát hiện mới** (KE_HOACH_VIET_BAO_CAO.md §11, điểm 39–41): nút thích/không thích gọi route chưa tồn tại; job CI "đánh giá RAG" chỉ kiểm thử các hàm độ đo; các kết quả kiểm chứng triển khai lấy từ ghi chép của nhóm (`DEPLOY.md`).

**Hình:** Hình 4.12 (H4-28) và Hình 4.14 (H4-40) vẽ mới bằng PlantUML; Hình 4.13 (H4-33) và Hình 4.15 (H4-45) là ảnh giữ chỗ; Hình 4.16 dùng lại H3-44. Đã đánh dấu `bỏ (V2)` cho 36 hình H4 còn lại ở trạng thái giữ chỗ.

**Việc nhóm cần làm (Phiên S):** chụp 4 ảnh còn lại: H4-08 (nạp tri thức), H4-24 (câu trả lời có trích dẫn), H4-33 (Translation Studio) và H4-45 (phiên ôn tập).

### Số trang sau phiên

| Ch.1 | Ch.2 | Ch.3 | Ch.4 | TLTK | Phần chính |
|---|---|---|---|---|---|
| 8 | 24 | 23 | 40 / 42 | 6 | 101 / 130 |

Còn lại: Chương 5 (18), Chương 6 (4) và phần đầu; tổng dự kiến khoảng 123 + dự phòng.

## Phiên 10 – Khung Chương 5 (31/10/2026)

Tệp mới `drafts/05_kiem_thu_danh_gia.md`, hiện **15 trang** (ngân sách 18; sau khi điền số liệu và viết mục 5.4 dự kiến khoảng 17–18). Phần chính hiện 116/130.

Danh sách việc nhóm cần làm (ảnh chụp, số liệu, thông tin) nay nằm trong tệp riêng **`VIEC_NHOM_CAN_LAM.md`**, có ô đánh dấu để theo dõi.

| Mục | Nội dung | Trạng thái số liệu |
|---|---|---|
| 5.1 | Môi trường (Bảng 5.1, do `eval/env_info.py` ghi), bộ dữ liệu và độ đo (công thức 5-1 Cohen's kappa, 5-2 khoảng Wilson), Bảng 5.2 kế hoạch 9 thí nghiệm E1–E9 | Đã có |
| 5.2.1 E1 | 5 cấu hình truy xuất (C1–C5), Bảng 5.3, Hình 5.1 | Chờ số liệu |
| 5.2.2 E2 | LLM không tài liệu so với RAG, Bảng 5.4 và 5.5 (độ tin cậy tự khai so với nhãn chấm tay) | Chờ số liệu |
| 5.2.3 E3 | Cache: 20 cặp diễn đạt lại và 10 cặp khác số, Bảng 5.6, Hình 5.2 | Chờ số liệu |
| 5.2.4 E4 | Bộ lọc an toàn: 19/32 câu tấn công bị chặn (59,4%), 6/60 câu hợp lệ bị chặn nhầm (10%); 0/50 câu thường, 6/10 câu chứa từ dễ nhầm | **Đã đo** (`eval/run_guardrail_eval.py`) |
| 5.2.5 E5 | Độ trễ và TTFT, Bảng 5.8, Hình 5.3; số sơ bộ lấy từ Bảng 4.8 | Chờ số liệu |
| 5.3.1 E6 | 1 642 kiểm thử: 1 634 đạt, 1 không đạt, 7 bỏ qua | **Đã đo** (`eval/run_test_suites.py`) |
| 5.3.2 E7 | Sinh từ vựng A và B (Bảng 5.10), thử chèn lệnh 19/20 | Lấy từ `flashcard_service/evaluation/results/REPORT.md` |
| 5.3.3 E8 | Nhận diện ngôn ngữ và chuyên ngành (Bảng 5.11) | Lấy từ báo cáo benchmark 10/10/2026 |
| 5.3.4 E9 | Kiểm chứng giới hạn tần suất với hai tài khoản (Bảng 5.12) | Chờ số liệu |
| 5.4 | Thảo luận | TODO, viết sau khi có số liệu |

**Script mới** trong `eval/` (chỉ đọc mã dự án): `env_info.py`, `run_test_suites.py` (kết quả `results/test_suites.json` và `junit_*.xml`), `run_guardrail_eval.py` (dữ liệu `data/guardrail_attacks.jsonl`, 32 câu, và `guardrail_benign.jsonl`, 60 câu).

**Lưu ý trung thực về số liệu:**
- Bộ câu mẫu của E4 do tôi soạn theo yêu cầu đề tài, cố ý có biến thể nằm ngoài mẫu của bộ lọc (diễn đạt khác, ngụy trang), nên tỉ lệ 59,4% là phạm vi bao phủ chứ không phải tần suất tấn công thực. Nhóm cần đọc lại hai tệp dữ liệu trước khi nộp.
- Bảng 5.10 và 5.11 trích từ báo cáo có sẵn của nhóm, không chạy lại (không có khóa Groq; thiếu mô hình `lid.176.ftz` trong `models/`). Đã ghi rõ trong văn bản.
- Các thư mục `.pytest_cache` không được tạo trong mã dự án (dùng `-p no:cacheprovider`).

**Phát hiện mới:**
- Kiểm thử `test_login_failure_is_logged_without_password` của Auth Service không đạt vì `logger.propagate = False` nên `caplog` không bắt được dòng nhật ký (chức năng ghi log vẫn đúng).
- Kết quả trên máy nhóm (Translation Service: 447 đạt, 0 lỗi) khác CI trên `main` (4 test lỗi), vì thiếu mô hình trong CI.
- Thử chèn lệnh ở Flashcard: ca I04 (in biến môi trường) bị script gắn cờ vì chuỗi tên khóa, nhóm chưa phân biệt rò rỉ thật hay lặp lại tải trọng.

**Cần bạn quyết định:** E1, E2, E3, E5 cần script chạy trên hệ thống thật. Tôi đề nghị một phiên **10b** để viết bốn script này (và mẫu Phụ lục F), vì không có script thì không điền được bảng nào. Phiên 11 (Chương 6 và phần đầu) có thể làm song song.

### Số trang sau phiên

| Ch.1 | Ch.2 | Ch.3 | Ch.4 | Ch.5 | TLTK | Phần chính |
|---|---|---|---|---|---|---|
| 8 | 24 | 23 | 40 | 15 / 18 | 6 | 116 / 130 |

Dự kiến cuối cùng: Ch.5 khoảng 18 và Ch.6 khoảng 4, tổng khoảng 123–124, còn khoảng 6 trang dự phòng.

## Phiên 11 – Chương 6 và phần đầu (31/10/2026)

Tệp mới `drafts/06_ket_luan.md` (**4 trang**, đúng ngân sách) và `drafts/00_phan_dau.md` (phần đầu, trang số La Mã i đến xxi trong bản dựng; chưa tính bìa và phụ bìa). Phần chính hiện **120/130 trang**; khi Chương 5 đủ 18 trang sẽ là khoảng 123.

| Thành phần | Nội dung |
|---|---|
| Chương 6.1 | Bảng 6.1 đối chiếu 9 mục tiêu ở 1.3.2 với mức đạt (Đạt, đạt một phần, đang hoàn thiện) và căn cứ; các số đã đo (1 642 kiểm thử, 100% thẻ đúng lược đồ, 97,8% nhận diện ngôn ngữ); chỗ trống `[CHỜ SỐ LIỆU]` cho kết quả Chương 5 |
| Chương 6.2 | Hạn chế theo bốn nhóm: chatbot (7 mục, chi tiết), pipeline tri thức, phân hệ hỗ trợ và bảo mật (ngắn), đánh giá. Dùng các điểm 18–41 của kế hoạch cũ mục 11 |
| Chương 6.3 | 7 hướng phát triển, chatbot trước |
| ABSTRACT và Tóm tắt | Mỗi bản một trang, từ khóa; còn một chỗ `[CHỜ SỐ LIỆU]` cho kết quả chính |
| Lời cảm ơn | Dùng "nhóm chúng em" (khác phần thân báo cáo dùng "nhóm/chúng tôi", vì là lời cảm ơn thầy cô); còn `[TODO]` tên giáo viên hướng dẫn |
| Nhận xét GVHD, GVPB 1, GVPB 2 | Ba trang có dòng chấm và chỗ ký |
| Mục lục, danh mục hình, bảng | Tạo tự động bằng `[[TOC]]`, `[[LOF]]`, `[[LOT]]` |
| Danh mục từ viết tắt | 51 mục (A–Z), chỉ gồm từ thật sự xuất hiện trong các chương, xác định bằng cách đếm trong bản thảo |

**Còn lại cho Phiên 13:** bìa, phụ bìa tiếng Việt và tiếng Anh, họ tên và mã số sinh viên, nhật ký làm việc (bảng 15 tuần), cập nhật danh mục viết tắt nếu thêm từ mới, rà soát toàn bộ.

### Số trang sau phiên

| Ch.1 | Ch.2 | Ch.3 | Ch.4 | Ch.5 | Ch.6 | TLTK | Phần chính |
|---|---|---|---|---|---|---|---|
| 8 | 24 | 23 | 40 | 15 / 18 | 4 / 4 | 6 | 120 / 130 |

## Phiên 10b – Script đo và số liệu Chương 5 (31/10/2026)

Kết quả: máy này **kết nối được Supabase** của dự án (kho tri thức 415 tài liệu), nên E1, E3, E5 và Bảng 4.2 được đo thật thay vì để trống. Chương 5 hiện **18/18 trang**, Chương 6 4/4, phần chính **124/130**.

**Script mới trong `eval/`** (xem `eval/README.md`; chỉ đọc Supabase, không ghi CSDL): `common.py`, `kb_stats.py`, `run_retrieval_ablation.py` (E1), `run_cache_eval.py` (E3, mô phỏng quy tắc trong bộ nhớ), `run_answer_eval.py` (E2 và E5, gọi Gemini), `run_latency_eval.py`, `analyze_pipeline.py`, `rating_tools.py` (tạo phiếu chấm, gộp, báo cáo; đã thử bằng nhãn giả rồi tạo lại phiếu trống). Dữ liệu: `eval/data/questions.jsonl` (45 câu, nhãn nguồn đúng, đáp án tham chiếu), `key_phrases.json`, `cache_pairs.jsonl` (23 cặp). Hình 5.1–5.3 vẽ bằng `figures/src/ch5/H5-02.py`, `H5-03.py`, `H5-04.py`.

**Số liệu đã đo và đã đưa vào báo cáo**
- **Bảng 4.2:** 415 tài liệu, 1 092 đoạn cha, 3 181 đoạn con (ctsv 222, iuh 87, camnang 60, csm 35, tuyensinh 4, pdt 3, tệp tải lên 4).
- **E1 (Bảng 5.3):** 35 câu có đáp án. C1 = C3 (nhánh toàn văn chỉ có kết quả ở 2/35 câu vì phép AND); xếp hạng lại: Hit@3 80,0% → 94,3%, MRR@5 0,687 → 0,762; Hit@1 chặt 60,0% và nới lỏng 85,7%; 7/10 câu không đáp án bị trả danh sách rỗng.
- **E3 (Bảng 5.6):** trúng 9/15 cặp diễn đạt lại; 0/8 trúng nhầm cặp khác con số (4/8 nếu bỏ bước so khớp số); loại do ngưỡng cosine 0,60 là chính.
- **E5 (Bảng 5.8, 37 lượt RAG, Gemini):** tổng trung vị 3,3 giây, p95 17,2 giây; TTFT trung vị 2,8 giây; đuôi dài do API.
- **E2 (chỉ báo tự động):** Hit@1 đầu cuối 77,1%, Hit@3 91,4%; 10/10 câu ngoài kho/ngoài phạm vi có câu từ chối; 1/37 lượt đóng khối `<thinking>` sai.
- **Phụ lục F:** bảng 45 câu hỏi.

**Phát hiện mới** (KE_HOACH_VIET_BAO_CAO.md §11, điểm 42–45): nhánh toàn văn gần như không đóng góp; bộ xếp hạng lại không phân biệt thực thể (câu về trường khác); khối `<thinking>` đóng sai làm mất câu trả lời; `pdt.iuh.edu.vn` nằm trong kho dù ngoài danh sách tên miền.

**Chi phí và an toàn:** `run_answer_eval.py` gọi Gemini khoảng 135 lần (45 câu × V1 một lần, V2 hai lần); các lời gọi chạy trên khóa trong `.env` của dự án. Không có thao tác ghi vào Supabase, Redis hay mã dự án. Một số lời gọi tự chuyển sang `gemini-3.1-flash-lite` hoặc `gemini-3.5-flash`.

**Còn lại cho nhóm:** hai người chấm tay `eval/results/rating_r1.csv`, `rating_r2.csv` (90 câu trả lời, mù A/B) rồi chạy `rating_tools.py merge` và `report` để điền Bảng 5.4 và 5.5; đọc lại bộ câu hỏi và nhãn (tôi soạn); E9 (hai tài khoản, cần Docker). Chi tiết ở `VIEC_NHOM_CAN_LAM.md`.

### Số trang sau phiên

| Ch.1 | Ch.2 | Ch.3 | Ch.4 | Ch.5 | Ch.6 | TLTK | Phần chính |
|---|---|---|---|---|---|---|---|
| 8 | 24 | 23 | 41 | 18 / 18 | 4 / 4 | 6 | 124 / 130 |

## Phiên 12 – Phụ lục A, C, D và tài liệu tham khảo (31/10/2026)

Phụ lục hiện **35 trang** (A 3, B ~8, C ~8, D 4, E ~5, F ~3 và trang tiêu đề); toàn tài liệu 176 trang, phần chính vẫn **124/130**. Không còn `[TODO]` trong phụ lục.

| Phụ lục | Nội dung | Nguồn |
|---|---|---|
| A | Yêu cầu, 4 bước cài đặt (`download_models.py`, `.env.prod`, `docker compose … up -d --build`, `deploy_smoke.py`), tạo admin (gán `users.role` trong CSDL), nạp kho tri thức (trang `/admin` và `run_pipeline`), bộ từ mẫu (`seed_catalog`), vận hành, Funnel; Bảng A.1 giữ nguyên | `DEPLOY_QUICKSTART.md`, `README.md` mục 7 |
| C | Bảng C.4: 14 endpoint của Chatbot Service (kèm quyền); Bảng C.5: endpoint rút gọn của Auth, Translation, Flashcard. Danh sách rút ra bằng cách đọc decorator trong `routers/*.py` | `app/routers/*.py`, `main.py` |
| D | Prompt của bộ định tuyến, persona và 9 quy tắc, luật và ví dụ mẫu của `REGULATION`, cách ghép prompt; **trích tự động từ mã nguồn** (nhập `prompt_templates.py` và chạy đoạn gán `rewrite_prompt` của `rag_service.py`) nên đúng nguyên văn | `prompts/prompt_templates.py`, `rag_service.py` |
| F | Đã có từ Phiên 10b (bảng 45 câu hỏi) | `eval/data/questions.jsonl` |

**Tài liệu tham khảo:** 17 trang web đã kiểm tra liên kết còn truy cập được ngày 31/10/2026, ghi ngày truy cập 31/10/2026; OWASP LLM ghi rõ bản 2025; 7 mã arXiv đối chiếu tiêu đề với arxiv.org, sửa tiêu đề mục `chen2024bgem3` cho đúng ("M3-Embedding: Multi-Linguality, …"). Còn một `[TODO]`: số hiệu và năm ban hành của Quy chế đào tạo (trang Cẩm nang không ghi), nhóm cần cung cấp.

**Chưa kiểm tra:** thông tin xuất bản (tập, số, trang) của các bài báo ngoài mã arXiv, vì không truy cập được cơ sở dữ liệu của nhà xuất bản; nhóm nên đối chiếu nếu GVHD yêu cầu.

## Phiên 13 – Bìa, nhật ký, rà soát tổng thể (31/10/2026)

**Bìa và phụ bìa:** công cụ build có thêm phần `cover` (bìa, phụ bìa tiếng Việt, phụ bìa tiếng Anh; không số trang, không đầu và chân trang), dựng từ `drafts/00_bia.md`, logo `build/assets/logo_iuh.png` (tách từ cuốn mẫu QuyLong, đã xử lý lớp trong suốt) và thông tin ở mục `cover` của `build/report_config.json`. Ba kiểu chữ `Cover Text`, `Cover Bold`, `Cover Title` thêm vào `make_reference.py` (đã sinh lại `reference.docx`). Bố cục theo mẫu của Khoa (PDF mẫu), vì file mẫu `.docx` của Khoa là bản của viện khác nên không dùng trực tiếp.

**Chưa có thông tin nên đang hiện chỗ trống ở bìa:** họ tên hai sinh viên (hiện "Họ tên Sinh viên 1/2" trong `students`), ngành, giáo viên hướng dẫn, tháng nộp. **Tên đề tài là tên tạm do trợ lý đề xuất**, nhóm thay bằng tên chính thức ở `title_vi` và `title_en`. Lịch sử git có hai tác giả chính là "Trần Anh Hào" (AnhHao0107) và Baovr125/BaoHocHoi; nhóm tự xác nhận họ tên đầy đủ.

**Nhật ký làm việc:** `drafts/92_nhat_ky.md`, bảng 15 tuần để trống (cuối phụ lục, có trong mục lục). `eval/git_weekly.py` tạo `eval/results/git_weekly.md` tóm tắt 191 commit theo 17 tuần để nhóm nhớ lại công việc; nội dung từng tuần và chữ ký giáo viên do nhóm điền, tôi không tự viết vì không có căn cứ.

**Rà soát:**
- Mọi tham chiếu "mục x.y.z" và "Phụ lục X" trong bản thảo đều có tiêu đề tương ứng; build không còn cảnh báo (hình, bảng, trích dẫn).
- Danh mục viết tắt thêm 12 từ đang dùng trong chương nhưng chưa có (ANN, CRAG, CSS, FK, GIN, HS256, HTTPS, IP, JSONB, MB, PK, UC); không từ nào thừa. Tổng 63 mục.
- Tài liệu tham khảo: thêm `luyenty.com` theo yêu cầu của nhóm; số lượng 56 mục, 55 được trích dẫn (còn `iuh_quyche` chưa trích dẫn).

**Số trang:** tổng 181 (phần đầu 21 trang La Mã gồm cả bìa không đánh số, phần chính 125, phụ lục 35). Phần chính 125/130: Ch.3 23/22 và Ch.4 42/42, các chương còn lại đúng ngân sách.

## Cách dùng bộ công cụ

```powershell
cd B:\KhoaLuan\Report
python build\make_reference.py                         # chỉ chạy lại khi sửa style
python build\render_figures.py                         # vẽ hình mới/đổi + tạo ảnh giữ chỗ
python build\render_figures.py H4-14                   # vẽ lại một hình
python build\renumber.py --dry-run                     # xem trước việc đánh số lại Hình/Bảng
python build\renumber.py                               # đánh số lại sau khi thêm, bớt, chuyển hình/bảng
python build\build_report.py --sample --word --pdf     # ghép bản mẫu
python build\build_report.py --word --pdf              # ghép báo cáo thật từ drafts\ (bỏ qua file chưa có)
```

Quy ước viết bản thảo (bổ sung cho mục 3.2 của kế hoạch):

- **Heading:** viết kèm số cho dễ đọc, ví dụ `# CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI`, `## 1.1 Lý do chọn đề tài`. Script tự bỏ số viết tay; nếu số viết tay lệch với số thực tế thì in cảnh báo.
- **Heading không đánh số:**
  - `## Tiểu kết chương {.unnumbered}`: không số, vẫn vào mục lục;
  - `# Lời cảm ơn {.unnumbered .unlisted}`: không số, không vào mục lục.
- **Hình:** `![Hình 4.3. Chú thích](../figures/ten_hinh.png){width=14cm}`. Thêm `(Nguồn: [n])` vào chú thích nếu hình lấy từ nguồn ngoài.
- **Bảng:** một dòng `Bảng 3.5. Chú thích` ngay trên bảng pipe.
- **Công thức đánh số:** `$$ ... \tag{2-12} $$` (đặt thành một đoạn riêng).
- **Tài liệu tham khảo:** đặt trong khối `::: {custom-style="Reference"}` … `:::`. Mỗi mục mở đầu bằng `[@khóa]`.
- **Trích dẫn:** dùng `[@khóa]` hoặc `[@a; @b]`, đặt trước dấu chấm câu. Không mở đầu đoạn văn bằng một trích dẫn.
- **Hình có cùng chú thích ở bản thảo và `FIGURES.md`:** sau khi sửa chú thích trong bản thảo, chạy lại đoạn đồng bộ chú thích (Phiên 6) hoặc sửa tay cột "Nội dung" trong `FIGURES.md`.
- **Hộp ví dụ:** dùng khối `::: {custom-style="Example Box"}` … `:::`.
- **Bảng đặc tả use case:** dùng khối mã ```` ```{.usecase caption="Bảng 3.x. Đặc tả use case UCxx …"} ````. Trong khối, mỗi dòng có dạng `Trường: giá trị` với các trường Use case, Mục đích, Mô tả, Tác nhân, Điều kiện trước, Điều kiện sau. Sau dòng `Luồng sự kiện chính:` là các bước `A: 1. …` (tác nhân) và `H: 2. …` (hệ thống). Sau dòng `Luồng sự kiện phụ:`, mỗi dòng là một luồng, ví dụ `3a. …`.


## Phiên 14 – Rà soát cuối và ghi chú hoàn thiện (31/10/2026)

**Đã làm:**
- Điền câu kết quả đo thật vào ABSTRACT và Tóm tắt (Hit@3 94,3% so với 80,0%, trung vị 3,3 giây); rút gọn cả hai để mỗi phần vừa một trang (trước đó tràn một dòng từ khóa sang trang sau).
- Quét bản PDF: không còn `??`, `{{`, trích dẫn chưa giải; phát hiện trang 42 gần trống do Bảng 3.5 (UC16) bị đẩy sang trang sau nên rút gọn bảng (gộp bước 5 và 6, rút gọn mô tả); hiện chỉ còn trang cuối Chương 5 ngắn vì còn ghi chú `[TODO]` chờ chấm tay E2.
- Gắn trích dẫn Quy chế đào tạo vào mục 1.1 (mục `iuh_quyche` trước đó chưa được trích dẫn; nay 56/56 mục được trích dẫn).
- Tạo `GHI_CHU_CUOI.md`: vị trí cần điền sau E2 và E9, thông tin chỉ nhóm biết, việc kiểm tra kỹ thuật, quy trình hoàn thiện, bảng điểm cần nắm khi bảo vệ và những câu không nên nói.

**Số trang:** 181 (phần chính 125/130). Còn 12 `[TODO]` và 4 `[CHỜ SỐ LIỆU]`, đều cần nhóm.
