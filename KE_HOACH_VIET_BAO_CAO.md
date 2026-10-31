# KẾ HOẠCH CHI TIẾT VIẾT BÁO CÁO KHÓA LUẬN TỐT NGHIỆP

> **Cập nhật 31/10/2026:** nhóm quyết định giới hạn phần chính của báo cáo trong 130 trang và lấy Academic Chatbot Service làm trọng tâm. Dàn ý chương, danh mục hình và các phiên làm việc được thay bằng **`KE_HOACH_V2.md`**. Các mục 0, 1, 2, 6.1–6.2, 7, 8, 10, 11, 12 của tài liệu này vẫn áp dụng.


**Đề tài:** IUH_Academic_Counseling_Chatbot (IUH EduBot)
**Đơn vị:** Khoa Công nghệ Thông tin – Trường Đại học Công nghiệp TP. Hồ Chí Minh
**Số sinh viên thực hiện:** 2 (trong báo cáo xưng "nhóm" / "chúng tôi")
**Mã nguồn:** `B:\KhoaLuan\IUH_Academic_Counseling_Chatbot` (gọi tắt là *repo*)
**Thư mục báo cáo:** `B:\KhoaLuan\Report`
**Ngày lập:** 30/10/2026. Bố cục đã được duyệt.

---

## Mục lục kế hoạch

0. [Các quyết định đã chốt](#0-các-quyết-định-đã-chốt)
1. [Quy ước định dạng theo mẫu của Khoa](#1-quy-ước-định-dạng-theo-mẫu-của-khoa)
2. [Quy ước viết nội dung](#2-quy-ước-viết-nội-dung)
3. [Quy trình và công cụ](#3-quy-trình-và-công-cụ)
4. [Bố cục chi tiết từng mục, kèm nguồn lấy thông tin](#4-bố-cục-chi-tiết-từng-mục-kèm-nguồn-lấy-thông-tin)
5. [Danh mục công thức của Chương 2](#5-danh-mục-công-thức-của-chương-2)
6. [Kế hoạch hình minh họa và sơ đồ](#6-kế-hoạch-hình-minh-họa-và-sơ-đồ)
7. [Danh mục từ viết tắt dự kiến](#7-danh-mục-từ-viết-tắt-dự-kiến)
8. [Tài liệu tham khảo dự kiến](#8-tài-liệu-tham-khảo-dự-kiến)
9. [Phân chia các phiên viết](#9-phân-chia-các-phiên-viết)
10. [Thông tin nhóm cần cung cấp](#10-thông-tin-nhóm-cần-cung-cấp)
11. [Những điểm phải đối chiếu với mã nguồn](#11-những-điểm-phải-đối-chiếu-với-mã-nguồn)
12. [Checklist rà soát cuối](#12-checklist-rà-soát-cuối)

---

## 0. Các quyết định đã chốt

| # | Vấn đề | Quyết định |
|---|---|---|
| 1 | Document Translation Service (đang tắt trong `docker-compose.yml`) | **Phương án (b).** Mô tả ngắn ở mục 4.6 như một phân hệ thử nghiệm. Ở mục 6.3 trình bày kỹ hướng phát triển để đưa phân hệ này vào vận hành. |
| 2 | Số sinh viên | 2 người. Bìa, phụ bìa và footer ghi tên cả hai. Trong bài xưng "nhóm" / "chúng tôi". |
| 3 | Tên đề tài | **IUH_Academic_Counseling_Chatbot**. Header mỗi trang ghi tên này. |
| 4 | Chương 2 | Viết sâu, có **đầy đủ công thức**, kèm giải thích từng ký hiệu (danh sách ở mục 5). |
| 5 | Chương 5 (Kiểm thử và đánh giá) | Hiện chỉ dựng khung và ghi chú nguồn số liệu. Nhóm bổ sung kết quả sau. |
| 6 | Định dạng | Quy tắc định dạng lấy theo mẫu PDF của Khoa CNTT. Bìa có logo mới, lấy theo cuốn QuyLong (tạm chưa làm phần đóng cuốn). |
| 7 | Nguồn ánh xạ báo cáo ↔ repo | README gốc §11 "Bản đồ tài liệu ↔ báo cáo khóa luận". Mục 4 của kế hoạch này mở rộng bảng đó đến cấp tiểu mục. |
| 8 | Chi tiết định dạng (chốt 30/10/2026, sau Phiên 0) | Heading 1 **một dòng, căn trái** (`CHƯƠNG 1 ⇥ TÊN CHƯƠNG`); caption dạng **`Hình 2.1: …`**; phần đầu đánh số **La Mã**; header căn phải, nghiêng; footer: tên 2 SV bên trái, số trang bên phải. Các mục 1.1–1.3 bên dưới đã sửa theo. |
| 9 | Hình minh họa (bổ sung 30/10/2026) | Báo cáo phải **nhiều sơ đồ và hình minh họa** để dễ đọc: khoảng **130 hình**, có ví dụ thật lấy từ log và dữ liệu của hệ thống, ảnh giao diện chụp khi hệ thống chạy thật. Chi tiết ở **mục 6**. |

---

## 1. Quy ước định dạng theo mẫu của Khoa

### 1.1. Trang giấy, phông chữ và style

| Thuộc tính | Giá trị |
|---|---|
| Khổ giấy | A4, đứng |
| Lề | Trên 3 cm, dưới 3 cm, trái 3,5 cm, phải 2 cm |
| Phông nội dung | Times New Roman 13, giãn dòng 1,5 |
| Heading 1 (Chương) | TNR 14, đậm, IN HOA, **căn trái**, trước 24 pt / sau 24 pt, giãn dòng 1,15, sang trang mới. Một dòng: "CHƯƠNG 1 ⇥ TỔNG QUAN ĐỀ TÀI" (theo PDF của Khoa tr.17) |
| Heading 2 (x.y) | TNR 13, đậm, trước 6 pt / sau 12 pt |
| Heading 3 (x.y.z) | TNR 13, đậm nghiêng |
| Heading 4 (x.y.z.t) | TNR 13, nghiêng. Không đưa vào mục lục |
| Content | TNR 13, trước 10 pt / sau 0, giãn dòng 1,5, căn đều hai bên, không thụt đầu dòng |
| Bullet | TNR 13, trước 0 / sau 0, giãn dòng 1,5 |
| Caption | TNR 13, trước 6 pt / sau 12 pt, căn giữa |
| Danh mục (mục lục, danh mục hình/bảng) | TNR 13, trước 0 / sau 0, giãn dòng 1,15 |
| Bảng | Chỉ kẻ đường ngang. Chữ trong bảng TNR 11–13 |
| Mã nguồn trích dẫn | Consolas hoặc Courier New 10–11, đặt trong khung. Chỉ trích đoạn ngắn; đoạn dài chuyển sang phụ lục |

### 1.2. Đánh số và chú thích

- Tối đa 4 cấp số (`4.2.5.1`). Mục lục chỉ hiển thị đến cấp 3.
- Mục nào đã chia thì phải có **ít nhất 2 tiểu mục**.
- Hình: chú thích **dưới** hình, dạng `Hình 4.3: Luồng xử lý semantic cache hai tầng`.
- Bảng: chú thích **trên** bảng, dạng `Bảng 3.5: Đặc tả use case Hỏi đáp chatbot`.
- (Trong bản thảo Markdown viết `Hình 4.3.` hay `Hình 4.3:` đều được; script ghép tự chuẩn hóa thành dấu `:`.)
- Công thức: căn giữa, số `(2-7)` căn phải. Đánh số lại từ đầu ở mỗi chương.
- Hình và bảng phải dùng **Insert Caption** (trường SEQ) để Word tự sinh danh mục hình và danh mục bảng.
- Mọi hình và bảng phải được nhắc đến trong đoạn văn trước khi xuất hiện, ví dụ "như Hình 4.3 cho thấy…".
- Hình lấy từ nguồn ngoài phải ghi nguồn ở chú thích, ví dụ `(Nguồn: [12])`.

### 1.3. Header, footer và số trang

- Header: `IUH_Academic_Counseling_Chatbot`, căn phải, TNR 12, nghiêng.
- Footer: tên 2 sinh viên ở bên trái, số trang ở góc dưới bên phải.
- Phần đầu (Abstract → Tóm tắt) đánh số La Mã (i, ii, …), giống mục lục mẫu của Khoa. Bìa và phụ bìa không đánh số.
- Số trang Ả Rập bắt đầu từ **1 tại Chương 1**, đánh liên tục đến hết Tài liệu tham khảo.
- Phụ lục **không** đánh số trang.

### 1.4. Thứ tự toàn cuốn

| # | Thành phần | Ghi chú |
|---|---|---|
| 1 | Bìa | Logo mới, theo cuốn QuyLong |
| 2 | Phụ bìa tiếng Việt | |
| 3 | Phụ bìa tiếng Anh | |
| 4 | ABSTRACT (tiếng Anh) + Keywords | Khoảng 1 trang |
| 5 | Lời cảm ơn | |
| 6 | Nhận xét của GVHD | Trang trống có tiêu đề và dòng chấm |
| 7 | Nhận xét của GVPB 1 | |
| 8 | Nhận xét của GVPB 2 | |
| 9 | Mục lục | Trường TOC, cấp 1–3 |
| 10 | Danh mục hình ảnh | Trường TOC theo caption "Hình" |
| 11 | Danh mục bảng biểu | Trường TOC theo caption "Bảng" |
| 12 | Danh mục từ viết tắt | Bảng 3 cột: Từ viết tắt / Từ đầy đủ / Nghĩa. Xếp theo A–Z |
| 13 | Tóm tắt (tiếng Việt) + Từ khóa | Khoảng 1 trang |
| 14 | Chương 1 → Chương 6 | |
| 15 | Tài liệu tham khảo | |
| 16 | Phụ lục A–F | |
| 17 | Nhật ký làm việc | Bảng 15 tuần |

---

## 2. Quy ước viết nội dung

### 2.1. Nguyên tắc trung thực với mã nguồn (quan trọng nhất)

1. **Mọi mô tả kỹ thuật phải truy được đến file trong repo.** README §11 có ghi chú: "Mọi mô tả trong README được đối chiếu với mã nguồn; tính năng và số liệu không truy được nguồn trong repo đã bị loại". Báo cáo giữ đúng nguyên tắc này.
2. **Không dùng số liệu không có script đo đi kèm.** Một số tài liệu cũ (`system-architechture-report.md`, README của doc_translation) có các câu như "100%" hay "giảm tải >60%". Những con số này chỉ được đưa vào báo cáo khi chạy lại được script đo.
3. **Phân biệt rõ ba trạng thái**, không viết lẫn:
   - **Đã cài đặt và đang chạy**: mô tả ở Chương 4.
   - **Đã cài đặt nhưng đang tắt hoặc chưa được gọi**: nói rõ trạng thái.
   - **Chưa làm**: chỉ đưa vào mục 6.2 Hạn chế hoặc 6.3 Hướng phát triển.
4. Khi lý thuyết khác với cách cài đặt thực tế thì **nói rõ sự khác nhau**. Ví dụ: Chương 2 trình bày BM25, nhưng hệ thống dùng `ts_rank_cd` của PostgreSQL FTS (xem mục 11).

### 2.2. Văn phong

- Viết ở ngôi thứ nhất số nhiều ("nhóm", "chúng tôi"), câu khoa học, khách quan.
- Không dùng emoji. Không dùng giọng quảng cáo ("vượt trội", "hoàn hảo", "cực kỳ").
- Lần đầu gặp thuật ngữ tiếng Anh thì ghi dạng *Tiếng Việt (English, viết tắt)*, ví dụ "sinh tăng cường truy xuất (Retrieval-Augmented Generation – RAG)". Từ lần sau dùng viết tắt.
- Tên hàm, file, biến đặt trong định dạng code, ví dụ `retrieve_relevant_chunks_multi`. Không lạm dụng: mỗi đoạn văn tối đa vài tên.
- Mỗi chương mở đầu bằng 1 đoạn giới thiệu chương và kết thúc bằng mục "Tiểu kết chương" dài khoảng ½ trang. (Mục tiểu kết không cần đánh số tiểu mục.)

### 2.3. Trích dẫn

- Trích dẫn dạng số trong ngoặc vuông `[n]`, đặt trước dấu chấm câu.
- Nhiều nguồn ghi `[3], [7]` hoặc `[3]–[5]`.
- Danh sách Tài liệu tham khảo: nhóm tiếng Việt trước, tiếng Anh sau. Trong mỗi nhóm xếp theo alphabet (tác giả Việt theo **tên**, tác giả nước ngoài theo **họ**). Đánh số `[1].` liên tục, thụt treo 1 cm.
- Định dạng:
  - Bài báo: `Tác giả (năm), "Tên bài", *Tên tạp chí/hội nghị*, Tập (số), tr. x–y.`
  - Sách: `Tác giả (năm), *Tên sách*, NXB, Nơi XB.`
  - Website: `Tên tổ chức (năm), "Tiêu đề trang", URL, truy cập ngày dd/mm/yyyy.`

### 2.4. Mẫu bảng dùng lại (theo cuốn QuyLong)

**Bảng đặc tả use case** (cột trái in đậm):

| Trường | Nội dung |
|---|---|
| Use case | UC-xx Tên use case |
| Mục đích | … |
| Mô tả | … |
| Tác nhân | … |
| Điều kiện trước | … |
| Điều kiện sau | … |
| Luồng sự kiện chính | Bảng con 2 cột: **Tác nhân** \| **Hệ thống**, đánh số bước |
| Luồng sự kiện phụ / ngoại lệ | Các nhánh 3a, 4a, … |

**Bảng mô tả CSDL:**

| Thuộc tính | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|

Cột "Ràng buộc" (PK, FK, NOT NULL, UNIQUE, DEFAULT) là phần thêm so với QuyLong.

**Bảng endpoint API:**

| Phương thức | Đường dẫn (qua Kong) | Quyền | Mô tả |
|---|---|---|---|

---

## 3. Quy trình và công cụ

### 3.1. Cấu trúc thư mục báo cáo

```text
B:\KhoaLuan\Report\
├── KE_HOACH_VIET_BAO_CAO.md      ← file này
├── TIEN_DO.md                    ← nhật ký tiến độ các phiên (tạo ở Phiên 0)
├── drafts\                       ← bản thảo Markdown, mỗi mục lớn một file
│   ├── 00_phan_dau.md            (abstract, lời cảm ơn, tóm tắt, viết tắt)
│   ├── 01_tong_quan.md
│   ├── 02_1_llm_rag.md
│   ├── 02_2_dich_may_srs.md
│   ├── 02_3_microservices_congnghe.md
│   ├── 03_1_yeu_cau_usecase.md
│   ├── 03_2_kien_truc_csdl_api.md
│   ├── 04_1_ingestion.md … 04_8_trien_khai.md
│   ├── 05_kiem_thu_danh_gia.md
│   ├── 06_ket_luan.md
│   ├── 90_tai_lieu_tham_khao.md
│   └── 91_phu_luc.md
├── figures\                      ← hình đã xuất (PNG ≥ 200 dpi), chia theo chương: ch1\ … ch6\
│   ├── FIGURES.md                ← danh mục hình: mã hình, file, chú thích, nguồn, trạng thái (mục 6.4)
│   ├── src\                      ← mã nguồn hình để vẽ lại được: .mmd, .puml, .svg, .py (biểu đồ)
│   └── screenshots\              ← ảnh chụp giao diện gốc (chưa chú thích) và bản có chú thích
├── build\
│   ├── reference.docx            ← file style dựng từ mẫu 2021, chỉnh theo PDF của Khoa
│   ├── build_report.py           ← script ghép Markdown → DOCX và hậu xử lý
│   ├── render_figures.py         ← (Phiên 0b) xuất mọi hình trong figures\src\ thành PNG
│   ├── screenshots.py            ← (Phiên 0b) chụp giao diện bằng Playwright + đánh số chú thích
│   └── IUH_EduBot_BaoCao.docx    ← sản phẩm cuối
└── (các file mẫu hiện có)
```

### 3.2. Viết bằng Markdown trước, ghép thành Word sau

**Lý do chọn cách này:**
- Báo cáo dài (ước tính khoảng 220 trang) và viết qua nhiều phiên.
- Markdown dễ duyệt, dễ so sánh thay đổi, dễ sửa từng phần.
- Công thức viết bằng LaTeX (`$$ ... $$`), sau đó chuyển thành công thức Word (OMML) để sửa được trong Word.

**Quy ước trong bản thảo:**
- Tiêu đề dùng `#` cho chương, `##` cho x.y, `###` cho x.y.z, `####` cho cấp 4.
- Hình: `![Hình 4.3. Luồng semantic cache hai tầng](../figures/4_3_semantic_cache.png)`.
- Bảng: ngay trên bảng có một dòng `Bảng 3.5. …`, bảng viết theo cú pháp pipe table.
- Công thức: `$$ RRF(d)=\sum_{r\in R}\frac{1}{k+r(d)} \tag{2-12} $$`.
- Chỗ cần bổ sung: `> [TODO: …]`. Riêng Chương 5 dùng `> [CHỜ SỐ LIỆU: …]`.

**Công cụ** (khảo sát máy ngày 30/10/2026):

| Việc | Công cụ | Trạng thái |
|---|---|---|
| Markdown → DOCX | `pypandoc_binary` (pandoc 3.9) + `build/reference.docx` + `build/filters.lua` | **đã có** (Phiên 0) |
| Hậu xử lý DOCX | `python-docx` trong `build_report.py` | **đã có** (Phiên 0) |
| Cập nhật mục lục, caption, xuất PDF | Word 16 qua COM (`build_report.py --word --pdf`) | **đã có** |
| **Lưu đồ, sơ đồ tuần tự**, use case, hoạt động, triển khai | **PlantUML** 1.2026.9 (`build/tools/plantuml.jar` + Java 25). Lưu đồ vẽ bằng sơ đồ hoạt động của PlantUML. *Rút ra ở Phiên 0b:* cùng nội dung, Mermaid cho hình quá khổ (lưu đồ semantic cache cao gấp 3 lần chiều rộng; sơ đồ tuần tự rộng 37 cm), còn PlantUML gọn và đọc được ở cỡ chữ 9 pt | **đã có** |
| ERD, sơ đồ trạng thái, lưu đồ nhỏ | **Mermaid** 11.4.1 (`build/tools/mermaid.min.js`) chạy trong Chromium có sẵn của Playwright. 23 sơ đồ ♻ trong README được dùng làm nội dung gốc rồi vẽ lại bằng công cụ phù hợp. *Rút ra ở Phiên 6:* ERD 14 bảng bằng Mermaid rộng 40 cm, nên ERD và sơ đồ trạng thái cũng chuyển sang **PlantUML** (theme `_theme/erd.iuml`, thực thể tô màu theo service) | **đã có** |
| Sơ đồ kiến trúc, sơ đồ khái niệm, hình ví dụ thực tế | **SVG viết tay theo khuôn mẫu chung** (bảng màu ở mục 6.2), xuất PNG bằng Playwright. Không cần tải gì thêm; thay cho draw.io vì máy chưa cài draw.io | có sẵn |
| Biểu đồ số liệu, minh họa toán học | **matplotlib** 3.10 (có sẵn), dùng một file style chung. Riêng FSRS tính bằng gói `fsrs` 6.3.2 đã cài trên máy (cùng phiên bản dải `>=6,<7` của repo) | có sẵn |
| Ảnh chụp giao diện | **Playwright** (Python, Chromium có sẵn) chạy kịch bản điều hướng cố định khi hệ thống chạy thật (`docker compose up`). **Pillow** 11 đánh số chú thích ①②③ lên ảnh | có sẵn; cần hệ thống chạy được (mục 10) |
| Trang bìa và phụ bìa | dựng một lần bằng Word theo cuốn QuyLong, lưu `build/cover.docx`, script ghép vào đầu file. Logo đã trích sẵn ở `figures/iuh_logo_new.png` | Phiên 16 |

Khi chạy `build_report.py --word`, mục lục, danh mục hình/bảng và số caption được cập nhật tự động. Nếu ghép không có `--word` thì mở file bằng Word → `Ctrl+A` → `F9`.

### 3.3. Quy trình mỗi phiên viết

1. Đọc `TIEN_DO.md` và mục tương ứng trong kế hoạch này.
2. Đọc README nguồn và **mã nguồn** được ghi trong mục 4. Ghi lại những chỗ README khác với code.
3. Viết bản thảo vào `drafts/…md`, kèm danh sách hình/bảng cần vẽ.
4. Vẽ sơ đồ, lưu `figures/src` và xuất PNG.
5. Tự kiểm theo checklist cuối phiên: số tiểu mục ≥ 2, có caption, có trích dẫn, không có số liệu thiếu nguồn.
6. Cập nhật `TIEN_DO.md`: đã viết gì, còn TODO gì, số trang ước tính.
7. Nhóm duyệt bản thảo → sửa → đánh dấu "đã duyệt".

---

## 4. Bố cục chi tiết từng mục, kèm nguồn lấy thông tin

**Ký hiệu:**
- 📄 README cần đọc
- 🧩 mã nguồn cần đối chiếu
- 🖼 hình hoặc bảng dự kiến. Số hình ghi trong các bảng dưới đây là số tạm lúc lập kế hoạch ban đầu. **Danh mục hình chính thức nằm ở mục 6.3** (mã `H<chương>-<số>`).
- ∑ công thức (chi tiết ở mục 5)
- ⚠ lưu ý đối chiếu

Các đường dẫn đều tính từ thư mục gốc repo.

---

### PHẦN ĐẦU (viết ở Phiên 14, sau khi xong nội dung chính)

| Thành phần | Nội dung | Độ dài |
|---|---|---|
| ABSTRACT | Bối cảnh → bài toán → giải pháp (microservices, Advanced RAG, NMT, FSRS) → kết quả chính (điền sau khi có Chương 5) → đóng góp. Keywords: *Retrieval-Augmented Generation, Hybrid Search, Cross-Encoder Reranking, Microservices, Neural Machine Translation, Spaced Repetition, FSRS* | 250–350 từ |
| Lời cảm ơn | Cảm ơn Khoa, GVHD, gia đình, bạn bè | ½–1 trang |
| Tóm tắt (tiếng Việt) | Nội dung tương đương ABSTRACT, kèm từ khóa | 1 trang |
| Danh mục viết tắt | Theo mục 7 của kế hoạch | 2 trang |

---

### CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI (~10–12 trang, Phiên 1)

| Mục | Nội dung cần viết | Nguồn |
|---|---|---|
| **1.1 Lý do chọn đề tài** | Ba khó khăn chính của sinh viên IUH:<br>(1) thông tin học vụ (quy chế, học phí, học bổng, thủ tục) rải rác trên nhiều website (iuh.edu.vn, camnang, ctsv, tuyensinh) và nhiều văn bản PDF;<br>(2) cần đọc hiểu tài liệu tiếng nước ngoài theo chuyên ngành;<br>(3) cần học từ vựng có phương pháp.<br>Kết luận: cần một hệ thống hợp nhất ba nhu cầu này. | 🧩 `data_ingestion/sources.py` (danh sách nguồn thực tế); ⚠ khảo sát thực tế: **ngoài repo** |
| **1.2 Khảo sát hiện trạng** | | |
| 1.2.1 Kênh tra cứu học vụ hiện tại | Sổ tay sinh viên (camnang.iuh.edu.vn), cổng thông báo, phòng ban. Ưu và nhược điểm của từng kênh. | ngoài repo (website IUH) |
| 1.2.2 Chatbot và trợ lý AI trong giáo dục | Chatbot dùng LLM thuần (ChatGPT, Gemini) và vấn đề ảo giác; chatbot dựa luật (rule-based); một số hệ thống RAG trong giáo dục. | 📄 `paper/check_2312.10997v5.pdf` (RAG survey) + tìm thêm |
| 1.2.3 Công cụ dịch và học từ vựng | Google Translate, DeepL; Anki, Quizlet. Nhận xét: tách rời nhau, không có ngữ cảnh chuyên ngành của IUH. | ngoài repo |
| 1.2.4 Khoảng trống đề tài giải quyết | Bảng so sánh tính năng: các giải pháp hiện có và IUH EduBot. | 🖼 **Bảng 1.1** so sánh giải pháp |
| **1.3 Mục tiêu** | | |
| 1.3.1 Mục tiêu tổng quát | Một câu. | |
| 1.3.2 Mục tiêu cụ thể | Danh sách gạch đầu dòng theo 5 phân hệ (Chatbot, Dịch, Flashcard, Xác thực/Gateway, Quản trị) cộng mục tiêu triển khai và kiểm thử. | 📄 README §1, §3 |
| **1.4 Đối tượng và phạm vi** | | |
| 1.4.1 Đối tượng nghiên cứu | Công nghệ: LLM, RAG, tìm kiếm lai, reranker, NMT, FSRS, microservices. Người dùng: sinh viên IUH, quản trị viên. | |
| 1.4.2 Phạm vi | Dữ liệu tri thức công khai của IUH. 10 ngôn ngữ dịch, 6 chuyên ngành. Flashcard 10 ngôn ngữ. Ứng dụng web. **Không bao gồm:** kết nối hệ thống đào tạo nội bộ (điểm, lịch học), ứng dụng di động. Dịch tài liệu ở mức thử nghiệm. | 📄 README §1; 🧩 `realtime_translation_service` (danh sách ngôn ngữ, chuyên ngành) |
| **1.5 Phương pháp nghiên cứu** | Nghiên cứu tài liệu → phân tích yêu cầu → thiết kế → cài đặt lặp → kiểm thử tự động (pytest, Vitest, CI) → đánh giá thực nghiệm (các bộ `evaluation/`). | 📄 README §8; 🧩 `*/evaluation/`, `.github/workflows/ci.yml` |
| **1.6 Đóng góp chính** | 5–7 gạch đầu dòng: pipeline Advanced RAG đầy đủ cho tiếng Việt; semantic cache hai tầng có cross-encoder kiểm tra lại; dịch chuyên ngành kết hợp từ điển và LLM; kho âm thanh CAS dùng qua sự kiện; pipeline sinh từ vựng AI 3 bước có kiểm tra tự động; kiến trúc microservices có gateway bảo mật. | 📄 README §1 |
| **1.7 Bố cục báo cáo** | Mỗi chương 2–3 câu. | |

---

### CHƯƠNG 2. CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ SỬ DỤNG (~40–45 trang, Phiên 2–4)

**Cách viết thống nhất cho mỗi lý thuyết:** khái niệm → **hình minh họa trực quan** (đặt trước công thức để người đọc nắm ý trước) → công thức (∑) → **ví dụ số nhỏ tính tay** (hộp "Ví dụ", mục 6.1) → ưu và nhược điểm → **"Áp dụng trong đề tài"**. Đoạn cuối này dài 2–4 câu, trỏ sang mục tương ứng ở Chương 4 để giữ mạch liên kết, giống cách viết của cuốn QuyLong. Danh sách hình của chương ở mục 6.3.

#### 2.1 Mô hình ngôn ngữ lớn (Phiên 2)

| Mục | Nội dung | Nguồn | Công thức / hình |
|---|---|---|---|
| 2.1.1 Kiến trúc Transformer và LLM | Self-attention, multi-head, positional encoding; mô hình decoder-only; tiền huấn luyện theo next-token; MoE (Qwen3 A3B là mô hình MoE). | Vaswani 2017 [EN]; báo cáo kỹ thuật Qwen | ∑ (2-1)…(2-5); 🖼 Hình 2.1 kiến trúc Transformer, Hình 2.2 Scaled Dot-Product Attention |
| 2.1.2 Sinh văn bản và tham số giải mã | Temperature, top-p, greedy; độ dài ngữ cảnh. | | ∑ (2-6), (2-7) |
| 2.1.3 Kỹ thuật prompt | System prompt và persona, few-shot, Chain-of-Thought (CoT số học), đầu ra có cấu trúc (JSON schema). | 📄 Chatbot README §4.5–4.6; 🧩 `academic_chatbot_service/app/prompts/prompt_templates.py`, `flashcard_service/.../vocab_pipeline.py` | |
| 2.1.4 Hạn chế của LLM | Ảo giác (hallucination), kiến thức có ngày cắt, prompt injection và jailbreak. Đây là cơ sở để dẫn sang RAG và guardrail. | RAG survey [EN], OWASP LLM Top 10 | |
| 2.1.5 Các mô hình dùng trong đề tài | Qwen (chạy cục bộ qua vLLM/Ollama, API tương thích OpenAI), Google Gemini (bản demo, có chuỗi dự phòng), Groq (`gpt-oss-120b`/`qwen`, dùng cho dịch và flashcard). | 📄 Chatbot README §4.7, Flashcard README §3.4; 🧩 `llm_providers.py`, `llm_client.py` | 🖼 Bảng 2.1 mô hình và vai trò |

#### 2.2 Retrieval-Augmented Generation (Phiên 2, trọng tâm của chương)

| Mục | Nội dung | Nguồn | Công thức / hình |
|---|---|---|---|
| 2.2.1 Kiến trúc RAG cơ bản | Retriever và generator; Naive → Advanced → Modular RAG. | RAG survey (`paper/check_2312.10997v5.pdf`), Lewis 2020 | ∑ (2-8); 🖼 Hình 2.3 Naive RAG, Hình 2.4 Advanced RAG |
| 2.2.2 Biểu diễn văn bản: Bi-Encoder và Cross-Encoder | Embedding câu, huấn luyện tương phản; cross-encoder chấm cặp (q, d). So sánh chi phí O(1) truy vấn với O(n) cặp. Giới thiệu `vietnamese-bi-encoder` (768 chiều, PhoBERT) và `bge-reranker-v2-m3`. | 📄 Chatbot README §4.3, §4.4, §4.8; Reimers 2019; Nogueira 2019 | ∑ (2-9)…(2-12); 🖼 Hình 2.5 so sánh Bi-Encoder và Cross-Encoder |
| 2.2.3 Tìm kiếm vector và HNSW | Các độ đo tương tự; tìm kiếm láng giềng gần đúng (ANN); HNSW (đồ thị nhiều tầng, tham số `m`, `ef_construction`, `ef_search`); pgvector. | 📄 db README §5.1; 🧩 `db/schema_complete.sql` (HNSW `m=16, ef_construction=64`, cosine); Malkov 2018 | ∑ (2-13)…(2-15); 🖼 Hình 2.6 cấu trúc HNSW |
| 2.2.4 Tìm kiếm toàn văn và tìm kiếm lai | TF-IDF → BM25 (lý thuyết). **PostgreSQL FTS:** `tsvector`, `websearch_to_tsquery`, `ts_rank_cd` (cover density), `unaccent` cho tiếng Việt. RRF hợp nhất thứ hạng. | 📄 db README §5.2; 🧩 `db/schema_complete.sql`; Robertson 2009; Cormack 2009 | ∑ (2-16)…(2-20); 🖼 Hình 2.7 minh họa RRF; ⚠ **nói rõ hệ thống dùng `ts_rank_cd`, không phải BM25 chuẩn** |
| 2.2.5 Kỹ thuật RAG nâng cao | (a) Query rewriting, multi-query, decomposition; (b) HyDE (giới thiệu, đề tài **không dùng**); (c) Small-to-Big / Parent–Child; (d) Lost in the Middle và sắp xếp lại ngữ cảnh; (e) Self-RAG, CRAG; (f) Semantic cache. | `paper/` (2305.14283, 2212.10496, 2307.03172, 2310.11511, 2401.15884) | ∑ (2-21)…(2-23); 🖼 Hình 2.8 đường cong U của Lost in the Middle (vẽ lại, ghi nguồn), Hình 2.9 Parent–Child |
| 2.2.6 Phân đoạn văn bản và trích xuất dữ liệu | Fixed-size, recursive, theo cấu trúc; xử lý bảng; trích xuất HTML (trafilatura), PDF (PyMuPDF), OCR (Gemini, Tesseract). | 📄 Ingestion README §3.3–3.4 | 🖼 Bảng 2.2 so sánh chiến lược chunking |
| 2.2.7 Độ đo đánh giá truy xuất và sinh | Hit Rate@K, MRR, Precision@K, nDCG; faithfulness và answer relevance. **Viết ở đây để Chương 5 chỉ cần dẫn lại.** | 🧩 `scripts/eval/retrieval_eval.py`, `test_rag_benchmark.py` | ∑ (2-24)…(2-27) |

#### 2.3 Dịch máy và xử lý ngôn ngữ (Phiên 3)

| Mục | Nội dung | Nguồn | Công thức / hình |
|---|---|---|---|
| 2.3.1 Dịch máy nơ-ron và NLLB-200 | Mô hình encoder–decoder; beam search; NLLB-200 (200 ngôn ngữ, bản distilled 600M); mã ngôn ngữ `vie_Latn`, …. | 📄 Realtime README §3.1; NLLB Team 2022 | ∑ (2-28)…(2-30); 🖼 Hình 2.10 encoder–decoder |
| 2.3.2 Lượng tử hóa với CTranslate2 | float16 / INT8, `translate_batch`. Đánh đổi giữa tốc độ, bộ nhớ và chất lượng. | 🧩 `services/translation_service.py`; `docker-compose.lowvram.yml` | ∑ (2-31), (2-32) |
| 2.3.3 Nhận diện ngôn ngữ | fastText `lid.176` (n-gram ký tự + softmax); Lingua (mô hình n-gram); **fusion có hiệu chỉnh** và dev-gate. | 📄 `LANGUAGE_DETECTION.md` §1–4; Joulin 2017 | ∑ (2-33)…(2-35) (công thức fusion lấy đúng theo §2, §4) |
| 2.3.4 Nhận diện chuyên ngành | LLM tự đánh giá độ tin cậy, kết hợp bằng chứng từ từ điển thuật ngữ → `decide_domain`. | 📄 `DOMAIN_DETECTION.md` §1, §3 | ∑ (2-36) (quy tắc quyết định) |
| 2.3.5 Khử nhập nhằng nghĩa từ | Thuật toán Lesk, WordNet, spaCy (dùng cho phân tích từ). | 📄 Realtime README §3.5; Lesk 1986; Miller 1995 | ∑ (2-37) |
| 2.3.6 Tổng hợp tiếng nói | Neural TTS; Microsoft Edge TTS. | 📄 Realtime README §3.6 | |
| 2.3.7 Độ đo chất lượng dịch | BLEU, chrF. | 🧩 `realtime_translation_service/evaluation/run_bleu_chrf.py` | ∑ (2-38), (2-39) |

#### 2.4 Lặp lại ngắt quãng (Phiên 3)

| Mục | Nội dung | Nguồn | Công thức / hình |
|---|---|---|---|
| 2.4.1 Đường cong lãng quên và hiệu ứng ngắt quãng | Ebbinghaus; active recall. | Ebbinghaus 1885; Cepeda 2006 | ∑ (2-40); 🖼 Hình 2.11 đường cong lãng quên |
| 2.4.2 Thuật toán SM-2 | Hệ số dễ (EF), khoảng cách ôn. ⚠ **Chỉ là lý thuyết để so sánh, đề tài không cài SM-2.** | Wozniak 1990 | ∑ (2-41), (2-42) |
| 2.4.3 Mô hình DSR và FSRS | Difficulty – Stability – Retrievability; đường quên dạng hàm lũy thừa; cập nhật S và D sau mỗi lần ôn; tính khoảng ôn theo retention mong muốn. Đề tài dùng gói `fsrs` ≥ 6. | 📄 Flashcard README §3.1; 🧩 `fsrs_algorithm.py`, `requirements.txt` (`fsrs>=6.0.0,<7.0.0`); Ye 2022/2023 | ∑ (2-43)…(2-49); 🖼 Bảng 2.3 so sánh SM-2 và FSRS |

#### 2.5 Kiến trúc Microservices và hạ tầng (Phiên 4)

| Mục | Nội dung | Nguồn | Công thức / hình |
|---|---|---|---|
| 2.5.1 Microservices và Database-per-service | So sánh với kiến trúc nguyên khối; nguyên tắc Database-per-service (đề tài áp dụng **ở mức quy ước** trên cùng một Supabase). | 📄 README §2; db README §2–3; Newman 2021 | 🖼 Hình 2.12 Monolith và Microservices |
| 2.5.2 API Gateway | Định tuyến, xác thực tập trung, rate limiting (fixed window), CORS, correlation-id. | 📄 gateway README §3–4; tài liệu Kong | ∑ (2-50) rate limit |
| 2.5.3 Giao tiếp đồng bộ, streaming và bất đồng bộ | REST, Server-Sent Events, message broker (RabbitMQ topic exchange, queue, routing key). | 📄 README §2.2–2.3 | 🖼 Hình 2.13 mô hình topic exchange |
| 2.5.4 Bộ nhớ đệm và lưu trữ đối tượng | Redis (LRU, TTL); object storage S3 và MinIO; **Content-Addressable Storage** (băm nội dung → khóa). | 📄 Realtime README §3.6 | ∑ (2-51) khóa CAS |
| 2.5.5 Xác thực với JWT | Cấu trúc JWT, HS256, claims, access và refresh token, thu hồi token; băm mật khẩu bằng bcrypt. | 📄 Auth README §4; RFC 7519 | ∑ (2-52), (2-53); 🖼 Hình 2.14 cấu trúc JWT |

#### 2.6 Công nghệ triển khai (Phiên 4)

Mỗi công nghệ gồm: giới thiệu ngắn + vai trò trong đề tài. Mở đầu mục bằng **bản đồ công nghệ theo tầng** (H2-42), thay cho việc chèn từng logo riêng lẻ.

| Mục | Công nghệ | Nguồn |
|---|---|---|
| 2.6.1 Backend | Python 3.11, FastAPI, Pydantic v2, Uvicorn, ONNX Runtime | 📄 README §4; 🧩 `requirements*.txt` |
| 2.6.2 Frontend | React 18, TypeScript 5, Vite 5, Tailwind 3, TanStack Query 5, React Router 6 | 📄 frontend README §1; 🧩 `frontend/package.json` |
| 2.6.3 Dữ liệu | Supabase PostgreSQL, pgvector, RLS, Redis 7, MinIO, RabbitMQ 3 | 📄 README §4, db README |
| 2.6.4 Hạ tầng | Kong 3.9.3 (DB-less), Docker / Docker Compose, GitHub Actions, Tailscale Funnel | 📄 README §4, §7; `DEPLOY.md` |
| 2.6.5 Mô hình AI | Bảng tổng hợp: tên mô hình, kích thước, định dạng (ONNX / CT2), nơi dùng | 🖼 Bảng 2.4 |

#### 2.7 Các nghiên cứu liên quan (Phiên 4)

Trình bày 6–8 công trình (RAG survey, Self-RAG, CRAG, Query Rewriting, Lost in the Middle, HyDE; các chatbot giáo dục tiếng Việt nếu tìm được), sau đó lập **Bảng 2.5** đối chiếu kỹ thuật nào được áp dụng trong đề tài.

⚠ `paper/check2605.18209v1.pdf` là bài *SpatioRoute: Dynamic Prompt Routing for Zero-Shot Spatial Reasoning*. Bài này chỉ nên trích khi nói về **định tuyến prompt theo intent**; không trích như một bài về RAG.

**Tiểu kết Chương 2.**

---

### CHƯƠNG 3. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG (~45 trang, Phiên 5–6)

#### 3.1 Phân tích yêu cầu (Phiên 5)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.1.1 Tác nhân | **Khách** (chưa đăng nhập), **Người dùng** gồm hai vai trò: `student` (sinh viên, giảng viên IUH) và `public` (người dùng công cộng; xem mục 11 điểm 21), **Quản trị viên** (`admin`, gán thủ công trong DB). Hệ thống ngoài: LLM API, Edge TTS. | 📄 README §6, §7.3; Auth README §3.2; 🧩 `frontend/src/router/AppRouter.tsx`, `gateway/kong.template.yml` (route công khai) |
| 3.1.2 Yêu cầu chức năng | Bảng mã YC-xx theo phân hệ. | 📄 README §1; các mục "API" của từng README |
| 3.1.3 Yêu cầu phi chức năng | Hiệu năng (streaming, cache), bảo mật (JWT, rate limit, chống injection), khả dụng, khả năng mở rộng, tài nguyên (GPU ~6–8 GB VRAM, giới hạn RAM theo container). | 📄 README §6, §7.1 |

🖼 Bảng 3.1 Tác nhân · Bảng 3.2 Yêu cầu chức năng · Bảng 3.3 Yêu cầu phi chức năng

#### 3.2 Mô hình hóa chức năng (Phiên 5)

Mỗi use case chi tiết gồm: **bảng đặc tả** (mẫu ở 2.4) + **sơ đồ tuần tự** (hoặc sơ đồ hoạt động khi luồng có nhiều nhánh), đặt ở cấp 4.

| Mục | Sơ đồ use case | Use case viết đặc tả chi tiết |
|---|---|---|
| 3.2.1 Use case tổng quát | 🖼 Hình 3.1 | — |
| 3.2.2 Phân hệ Xác thực | 🖼 Hình 3.2 | UC01 Đăng ký · UC02 Đăng nhập (email hoặc MSSV) · UC03 Làm mới / đăng xuất · UC04 Cập nhật hồ sơ, đổi mật khẩu, cài đặt |
| 3.2.3 Phân hệ Chatbot | 🖼 Hình 3.3 | UC05 Hỏi đáp học vụ (streaming, trích dẫn) · UC06 Quản lý phiên hội thoại |
| 3.2.4 Phân hệ Dịch thuật | 🖼 Hình 3.4 | UC07 Dịch văn bản (thường / streaming) · UC08 Dịch theo chuyên ngành · UC09 Phân tích từ và nghe phát âm · UC10 Lưu từ thành thẻ |
| 3.2.5 Phân hệ Flashcard | 🖼 Hình 3.5 | UC11 Quản lý sổ thẻ và thẻ · UC12 Ôn tập theo FSRS · UC13 Sinh từ vựng bằng AI · UC14 Dùng bộ từ mẫu và nhập Excel · UC15 Chơi trò chơi ôn từ |
| 3.2.6 Phân hệ Quản trị | 🖼 Hình 3.6 | UC16 Nạp tri thức (file / URL / quét website, theo dõi tiến độ) · UC17 Quản lý tài liệu tri thức · UC18 Quản lý từ điển chuyên ngành |

- 📄 Mục "API" của từng README.
- 🧩 `routers/*.py` của từng service: luồng chính phải khớp endpoint thật.
- ⚠ **Dịch tài liệu**: chỉ ghi trong sơ đồ tổng quát với nhãn «thử nghiệm», không viết đặc tả chi tiết.
- ⚠ **Không có** use case quên mật khẩu / OTP (chưa cài đặt).

#### 3.3 Thiết kế kiến trúc tổng thể (Phiên 6)

| Mục | Nội dung | Nguồn | Hình |
|---|---|---|---|
| 3.3.1 Sơ đồ kiến trúc | Trình duyệt → nginx → Kong → 4 service → hạ tầng → LLM / TTS bên ngoài | 📄 README §2.1 (mermaid) | 🖼 Hình 3.7 (vẽ lại đẹp bằng draw.io) |
| 3.3.2 Định tuyến qua Gateway | Bảng route, plugin, timeout, upstream | 📄 gateway README §2–5 | 🖼 Hình 3.8 luồng một request qua Kong; Bảng 3.x route |
| 3.3.3 Luồng giao tiếp | REST / SSE / sự kiện; luồng `flashcard.created` → TTS → `flashcard.audio_ready` | 📄 README §2.2–2.3 | 🖼 Hình 3.9 sơ đồ tuần tự sự kiện sinh âm thanh |
| 3.3.4 Kiến trúc phân lớp bên trong service | `routers` → `schemas` → `services` → `utils` (+ `guardrails`, `prompts`, `data_ingestion`) | 📄 README §9; cây thư mục từng README | 🖼 Hình 3.10 |
| 3.3.5 Sơ đồ triển khai | Container, cổng, mạng, giới hạn CPU / RAM / GPU | 📄 README §7.1; 🧩 `docker-compose*.yml` | 🖼 Hình 3.11 Deployment diagram; Bảng 3.x tài nguyên |

#### 3.4 Thiết kế cơ sở dữ liệu (Phiên 6)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.4.1 Phân chia dữ liệu theo service | Bảng ánh xạ service ↔ bảng | 📄 db README §3 |
| 3.4.2 CSDL tri thức RAG | `documents`, `document_chunks`, `document_parents`, `semantic_cache`… Chỉ mục HNSW, GIN, `tsvector`. Hàm RPC `match_chunks_hybrid_rrf`. | 📄 db README §4–5; 🧩 `db/schema_complete.sql` |
| 3.4.3 CSDL người dùng và hội thoại | `users` (role, token_version, settings), `chat_sessions`, `messages` | 📄 db README §4; Auth README §5 |
| 3.4.4 CSDL Flashcard | decks, flashcards (trạng thái FSRS), review_logs, catalog, game sessions, streak, quota | 📄 db README §4; Flashcard README §5; 🧩 `db/migrations/003–007` |
| 3.4.5 CSDL Dịch thuật | Từ điển chuyên ngành và chỉ mục | 📄 Realtime README §5 |

- 🖼 Hình 3.12 ERD tổng thể (vẽ lại từ db README §4).
- 🖼 Mỗi bảng chính có một bảng mô tả thuộc tính, tổng khoảng 12–15 bảng.
- ⚠ db README §6: một số đối tượng DB trước đây chưa có SQL và DB đang chạy có thể đang theo file cũ. Trong báo cáo, mô tả theo `schema_complete.sql` và ghi chú điều này.

#### 3.5 Thiết kế API (Phiên 6)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.5.1 Quy ước | Tiền tố `/api/v1`, envelope `{ok, data, error}`, mã lỗi, phân quyền | 📄 README §9; Auth README §3.1 |
| 3.5.2 Danh sách endpoint | Chỉ nêu cách nhóm endpoint. Bảng tóm tắt và bản đầy đủ đặt ở Phụ lục C (rút gọn ở Phiên 6b). | 📄 mục "API" từng README; 🧩 `routers/*.py` |
| 3.5.3 Giao thức SSE | Các sự kiện `metadata` / `delta` / `done` / `error` của chat; hợp đồng SSE của `/translate/stream`; tiến độ nạp tri thức | 📄 Chatbot README §3; `DOMAIN_DETECTION.md` §2; frontend README §4.2 |

#### 3.6 Thiết kế bảo mật (Phiên 6)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.6.1 Xác thực, phân quyền và vòng đời token | Kong kiểm tra chữ ký, `iss`, `exp`; service giải mã lại; `token_version`; Kong xóa header `X-User-*` | 📄 README §6; Auth README §4.2; 🖼 Hình 3.13 vòng đời phiên |
| 3.6.2 Mô hình đe dọa và biện pháp | Bảng đối chiếu OWASP: dò mật khẩu, timing attack, IDOR, prompt injection, rate limit, RLS, không commit bí mật | 📄 Auth README §9 (bảng OWASP); README §6; 🧩 `guardrails/query_filter.py` |

#### 3.7 Thiết kế giao diện (Phiên 6)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.7.1 Sơ đồ điều hướng | Route, trang, phân quyền route | 📄 frontend README §3; 🖼 Hình 3.14 sitemap |
| 3.7.2 Hệ thống thiết kế | Màu thương hiệu IUH, logo, theme sáng / tối, responsive, trợ năng (tương phản) | 📄 frontend README §5; 🧩 `tests/e2e/theme_audit/`, `frontend/src/assets/brand/` |

**Tiểu kết Chương 3.**

---

### CHƯƠNG 4. XÂY DỰNG HỆ THỐNG (~70 trang, Phiên 7–12)

**Cách viết thống nhất cho mỗi service:**
1. Vai trò và vị trí trong hệ thống, **mở đầu bằng sơ đồ kiến trúc của service** (vị trí trong hệ thống được tô màu).
2. Cấu trúc thư mục (cây rút gọn trong khung mã).
3. Từng kỹ thuật: vấn đề → **lưu đồ** → giải pháp → cài đặt (trích code ngắn, tham số thật) → **ví dụ thực tế** lấy từ log hoặc dữ liệu thật (mục 6.1) → nhận xét.
4. Bảng cấu hình chính.
5. **Kết quả trên giao diện**: 1–3 ảnh chụp màn hình của chức năng vừa trình bày.
6. Hạn chế đã biết (ghi ngắn, phần chi tiết để ở 6.2).

#### 4.1 Pipeline thu thập và xử lý tri thức (Phiên 7)

| Mục | Nội dung | Nguồn | Hình / bảng |
|---|---|---|---|
| 4.1.1 Nguồn dữ liệu và thu thập URL | Sitemap camnang; danh mục thông báo; BFS theo độ sâu cho từng domain; URL cố định tuyensinh | 📄 Ingestion README §3.1; 🧩 `data_ingestion/sources.py`, `crawlers/` | 🖼 Bảng 4.1 nguồn và độ sâu; Hình 4.1 sơ đồ pipeline tổng thể (Ingestion README §1) |
| 4.1.2 Trích xuất nội dung | trafilatura / BeautifulSoup; PDF bằng PyMuPDF; OCR PDF scan bằng Gemini, Tesseract dự phòng | 📄 Ingestion README §3.2–3.3; 🧩 `crawlers/*`, `extractors/*` | |
| 4.1.3 Hybrid Chunker và Parent–Child | Child khoảng 600 ký tự, parent khoảng 1200 token; tách bảng (`split_table`); siêu dữ liệu | 📄 Ingestion README §3.4; 🧩 `chunkers/hybrid_chunker.py`; `db/schema_v3_parent_child_rag.sql` | 🖼 Hình 4.2 ví dụ một văn bản được tách thành parent / child |
| 4.1.4 Sinh embedding và ghi CSDL | ONNX bi-encoder, theo lô, upsert, `tsvector` | 📄 Ingestion README §3.5; 🧩 `embedders/` | |
| 4.1.5 API quản trị và chạy CLI | `/api/admin/ingest/*`, SSE tiến độ, `run_pipeline.py` | 📄 Ingestion README §4–5; 🧩 `routers/admin_ingest.py` | |
| 4.1.6 Thống kê kho tri thức | Số tài liệu, số chunk / parent, phân bố theo nguồn và loại | ⚠ **truy vấn Supabase** (db README §7) | 🖼 Bảng 4.2 |

#### 4.2 Academic Chatbot Service (Phiên 8, phần dài nhất)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 4.2.1 Tổng quan vòng đời một câu hỏi | Từ `POST /messages/stream` đến sự kiện `done` | 📄 Chatbot README §3; 🖼 **Hình 4.3 pipeline đầy đủ**, **Hình 4.4 sơ đồ tuần tự** |
| 4.2.2 Guardrail an toàn | Nhóm regex, chặn thẻ cấu trúc; ví dụ câu bị chặn | 📄 §4.1; 🧩 `guardrails/query_filter.py` |
| 4.2.3 Router / Query Rewriter | Câu hỏi độc lập; `need_retrieval`; 7 intent; tách 1–4 sub-query; xử lý xã giao | 📄 §4.2; 🧩 `rag_service.generate_standalone_query`; 🖼 Bảng 4.3 các intent |
| 4.2.4 Semantic cache hai tầng | L1 Redis khớp chính xác → L2 pgvector (≥ 0.60) → cross-encoder (≥ 0.80) → kiểm tra số học; ghi lại sau khi trả lời (Quality Gate: chỉ ghi khi confidence = HIGH) | 📄 §4.3; 🧩 `check_semantic_cache`, `async_cache_writeback`; 🖼 Hình 4.5 |
| 4.2.5 Truy xuất lai và rerank đa truy vấn | RPC RRF k = 60 cho mỗi sub-query; gộp; cross-encoder; ngưỡng 0.20 / 0.65; quota động; top_k = 8, candidate = 50 | 📄 §4.4; 🧩 `retrieve_relevant_chunks_multi`, `db/schema_complete.sql`; 🖼 Hình 4.6; ⚠ `get_adaptive_candidate_count` **chưa được pipeline gọi** |
| 4.2.6 Small-to-Big, sắp xếp Sandwich và cách ly ngữ cảnh | Lấy parent; sắp xếp để chống Lost in the Middle; các thẻ `<retrieved_context>`, `<source id>`, `<query_reminder>` | 📄 §4.5; 🧩 `llm_generation_service.py`; 🖼 Hình 4.7 ví dụ khung prompt |
| 4.2.7 Prompt theo intent và lớp nhà cung cấp LLM | Template theo intent; few-shot; CoT số học; OpenAI-compatible (vLLM / Ollama) và Gemini có chuỗi dự phòng; cấu hình `LLM_PROVIDER` | 📄 §4.5, §4.7; 🧩 `prompts/prompt_templates.py`, `llm_providers.py`; ⚠ mặc định trong code khác nhau giữa các file (mục 11) |
| 4.2.8 Self-RAG, streaming SSE và trích dẫn | Thẻ `<thinking>` (`doc_relevance`, `conflict_detected`, `answer_confidence`) được lọc khỏi luồng; sự kiện `metadata` mang citations | 📄 §4.6, §3 |
| 4.2.9 Mô hình ML cục bộ và log truy vấn | ONNX CUDA / CPU, tải mô hình bằng `download_models.py`; log Markdown (độ trễ, token) | 📄 §4.8–4.9; 🧩 `log_utils.py` |
| 4.2.10 Quản lý phiên hội thoại | API sessions, lưu messages | 📄 §5–6 |

🖼 Bảng 4.4 tổng hợp tham số cấu hình chatbot (Chatbot README §7).

#### 4.3 Realtime Translation Service (Phiên 9)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 4.3.1 Dịch thường và dịch streaming | `POST /text`; `/stream` (SSE, tối đa 3000 ký tự); cache Redis theo SHA-256; NLLB float16 (GPU) / INT8 (low-VRAM); dự phòng bằng LLM | 📄 Realtime README §3.1–3.2; 🧩 `translation_service.py`, `llm_service.py`, `cache_service.py`; 🖼 Hình 4.8 luồng dịch |
| 4.3.2 Nhận diện ngôn ngữ | fastText + Lingua + fusion, hiệu chỉnh, dev-gate, văn bản trộn nhiều ngôn ngữ | 📄 `LANGUAGE_DETECTION.md` §1–4, §7; 🧩 `language_detection.py` |
| 4.3.3 Dịch theo chuyên ngành | 6 chuyên ngành; tra từ điển → chèn thuật ngữ vào prompt LLM; `decide_domain`; thông báo cho người dùng | 📄 Realtime README §3.3; `DOMAIN_DETECTION.md` §1–3, §5; 🧩 `domain_detection.py`; 🖼 Hình 4.9 |
| 4.3.4 Phân tích từ | `/analyze_word`: spaCy, WordNet, Lesk; `/lookup`, `/flashcard` | 📄 §3.5, §3.8 |
| 4.3.5 TTS và kho âm thanh CAS | Edge TTS 10 giọng; khóa `terms/{lang}_{md5}.mp3`; bucket `flashcard-audios`, `dictionary-audio`; consumer RabbitMQ | 📄 §3.6–3.7; 🧩 `tts_service.py`, `rabbitmq_consumer.py`; 🖼 Hình 4.10 |
| 4.3.6 Quản trị từ điển chuyên ngành | CRUD, import, xóa hàng loạt | 📄 §4 |

#### 4.4 Flashcard Service (Phiên 10)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 4.4.1 Sổ thẻ và thẻ | Sổ là đơn vị ngôn ngữ; chống IDOR | 📄 Flashcard README §3.6, §4 |
| 4.4.2 Cài đặt FSRS và hàng đợi học | Cách gọi gói `fsrs`; ánh xạ nút Again / Hard / Good / Easy; `get_study_queue`; chế độ ôn; streak; thống kê | 📄 §3.1–3.2; 🧩 `fsrs_algorithm.py`; 🖼 Hình 4.11 vòng đời trạng thái thẻ (New → Learning → Review → Relearning) |
| 4.4.3 Chấm chính tả | `verify_spelling` | 📄 §3.3 |
| 4.4.4 Pipeline sinh từ vựng AI | SELECT → ENRICH → VERIFY; kiểm tra bằng code (schema, hệ chữ, IPA / pinyin / kana / romaja / RTGS); `<user_input>` fence; quota 6/phút; sinh ảnh | 📄 §3.4; 🧩 `vocab_pipeline.py`; 🖼 Hình 4.12 |
| 4.4.5 Thư viện bộ từ, nhập Excel, lưu từ trang dịch | Clone-on-start; `excel_importer.py`; `cards/from-translation` | 📄 §3.5, §3.8 |
| 4.4.6 Trò chơi ôn từ | 4 trò (MatchPairs, SpeedRound, WordBuilder, Shooter); chấm điểm phía máy chủ | 📄 §3.7; 🧩 `game_logic.py`, `game_service.py` |
| 4.4.7 Tích hợp sự kiện | Publish `flashcard.created`, consume `flashcard.audio_ready` | 📄 §3.9 |

#### 4.5 Auth Service và Kong API Gateway (Phiên 11)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 4.5.1 Đăng ký, đăng nhập, chính sách mật khẩu | Đăng nhập bằng email hoặc MSSV; bcrypt cost 12; luôn chạy bcrypt (chống timing attack); throttle (5 lần sai theo IP + tài khoản, 30 lần sai theo tài khoản) | 📄 Auth README §3.2, §4.3; 🧩 `auth_service/app/services/auth_service.py` |
| 4.5.2 Cấp phát, làm mới và thu hồi JWT | Claims `sub`, `role`, `tv`, `iat`, `exp`, `iss`; access 60 phút; refresh tối đa 7 ngày; `token_version`; fail-closed khi thiếu `JWT_SECRET_KEY` | 📄 §4.1–4.2; 🧩 `utils/security.py` (giống nhau ở 3 service) |
| 4.5.3 Cấu hình Kong | DB-less, entrypoint kiểm tra cấu hình, route, plugin JWT / rate limit / CORS / correlation-id / request-transformer, timeout | 📄 gateway README §1–6; 🧩 `gateway/kong.template.yml`, `kong-entrypoint.sh` |

#### 4.6 Document Translation Service – phân hệ thử nghiệm (Phiên 11, ~4–5 trang)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 4.6.1 Mục tiêu và kiến trúc | Dịch PDF, DOCX, PPTX, PDF scan; xử lý bất đồng bộ (FastAPI :8004 + Celery worker + RabbitMQ + MinIO + Redis); trích glossary; phát sự kiện `doc.translated` | 📄 `services/doc_translation_service/README.md` §1–2; `notes_for_thesis.md` §1–2; 🖼 Hình 4.13 (sơ đồ tuần tự rút gọn) |
| 4.6.2 Trạng thái hiện tại | Đang tắt trong `docker-compose.yml` (khối bị comment); frontend khóa trang bằng cờ `VITE_FEATURE_DOC_TRANSLATION`. Lý do tắt: tài nguyên GPU / RAM, phụ thuộc nặng (PaddleOCR, babeldoc). | 🧩 `docker-compose.yml` (dòng ~153–178), `frontend/src/config.ts`, `frontend/tests/DocTranslationLock.test.tsx` |

⚠ Các benchmark trong README của phân hệ này (0% cắt bảng, thuật ngữ 100%, nhanh 3,97 lần…) **chỉ được nêu nếu chạy lại được script**. Nếu không, ghi là "số liệu sơ bộ của nhóm, chưa kiểm chứng lại" hoặc bỏ hẳn.

#### 4.7 Ứng dụng Web (Phiên 12)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 4.7.1 Cấu trúc dự án, tầng dịch vụ và quản lý trạng thái | `src/services/`, TanStack Query, xác thực phía client, luồng chat SSE | 📄 frontend README §2, §4–5 |
| 4.7.2 Đăng nhập và Dashboard | Ảnh chụp + mô tả; ⚠ một số khối Dashboard dùng dữ liệu mẫu, phải ghi rõ | 📄 §7 |
| 4.7.3 Giao diện Chatbot | Streaming, CitationBadge, FormattedMarkdown, danh sách phiên | |
| 4.7.4 Giao diện Dịch thuật | Chọn ngôn ngữ / chuyên ngành, WordAnalysisPopup, SaveFlashcardModal, phát âm | |
| 4.7.5 Giao diện Flashcard và trò chơi | Sổ thẻ, ôn tập, sinh từ AI, bộ từ mẫu, 4 trò chơi, thống kê | |
| 4.7.6 Giao diện Quản trị, Hồ sơ, Cài đặt | Nạp tri thức, DictionaryAdmin, Profile, Settings | |

Ảnh giao diện được phân về đúng mục chức năng ở 4.1–4.5 (mục "Kết quả trên giao diện"). Mục 4.7 chỉ giữ phần kiến trúc frontend, các trang tổng hợp (Dashboard, Hồ sơ, Cài đặt) và phần responsive / giao diện sáng–tối. Danh sách ảnh cần chụp ở mục 6.5.

#### 4.8 Triển khai hệ thống (Phiên 12)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 4.8.1 Đóng gói bằng Docker Compose | Dockerfile từng service; compose gốc, lớp phủ prod, low-VRAM; mạng; cổng | 📄 README §7; 🧩 `docker-compose*.yml`, `*/Dockerfile` |
| 4.8.2 Quy hoạch tài nguyên | Bảng CPU / RAM / GPU; số đo VRAM (ghi chú trong `docker-compose.lowvram.yml`); máy phát triển RTX 4060 8 GB, RAM 24 GB | 📄 README §7.1 |
| 4.8.3 CI/CD và kiểm soát chất lượng | GitHub Actions (ma trận pytest, `rag-eval-benchmark`, Vitest), pre-commit | 📄 README §8; 🧩 `.github/workflows/ci.yml`, `.pre-commit-config.yaml` |
| 4.8.4 Triển khai demo công khai | nginx, Tailscale Funnel, `deploy_smoke.py` | 📄 `DEPLOY.md`, `DEPLOY_QUICKSTART.md`, `run_mod.md`; 🧩 `frontend/nginx.conf` |

**Tiểu kết Chương 4.**

---

### CHƯƠNG 5. KIỂM THỬ VÀ ĐÁNH GIÁ (~30–40 trang, Phiên 13 dựng khung, nhóm bổ sung sau)

Phiên 13 chỉ viết phần **phương pháp** và **thiết kế thí nghiệm**, chèn bảng trống, và ghi rõ script hoặc tài liệu để lấy số liệu.

| Mục | Nội dung khung | Nguồn số liệu (README §11, Chương 5) | Trạng thái |
|---|---|---|---|
| 5.1 Môi trường và phương pháp đánh giá | Cấu hình máy, phiên bản mô hình, bộ dữ liệu, độ đo (dẫn lại 2.2.7, 2.3.7) | — | viết được ngay |
| 5.2 Kiểm thử phần mềm | Chiến lược (unit, integration, frontend, e2e thủ công); bảng số test theo service; kết quả pass/fail và coverage | 📄 README §8; 🧩 `run_tests.sh all`, `ci.yml`, `scripts/e2e_flashcard/` | **cần chạy lại** |
| 5.3 Đánh giá Chatbot | (a) Truy xuất: Hit Rate@K, MRR trên bộ câu hỏi có nhãn; (b) Chất lượng trả lời: chấm thủ công hoặc LLM-as-judge; (c) Ablation: dense / FTS / hybrid / +rerank / +small-to-big; (d) Semantic cache: tỷ lệ hit, độ trễ; (e) Guardrail: tỷ lệ chặn trên bộ câu jailbreak; (f) Độ trễ đầu-cuối, TTFT | 🧩 `scripts/eval/retrieval_eval.py`, `logs/academic_chatbot/` | **ngoài repo, cần xây bộ câu hỏi có nhãn** |
| 5.4 Đánh giá Dịch thuật | Nhận diện ngôn ngữ (accuracy, F1, độ trễ); nhận diện chuyên ngành; BLEU / chrF; độ trễ NLLB và LLM; tải bằng Locust | 📄 `LANGUAGE_DETECTION.md` §5, `DOMAIN_DETECTION.md` §6, `tests/test_results/*.md`, `services/realtime_qa_report.md`; 🧩 `evaluation/*` | một phần |
| 5.5 Đánh giá Flashcard | So sánh 1 lời gọi với pipeline 3 bước; kiểm tra IPA; thử prompt injection; đúng đắn của FSRS (unit test) | 📄 `flashcard_service/evaluation/results/REPORT.md` | một phần (một người chấm, mẫu nhỏ) |
| 5.6 Đánh giá bảo mật | Smoke test bảo mật; rate limit; JWT hết hạn hoặc bị thu hồi; IDOR | 🧩 `scripts/security_smoke_test.py`, test của auth | cần chạy |
| 5.7 Đánh giá hiệu năng và tài nguyên | RAM / VRAM thực tế, thời gian khởi động, thông lượng | `docker stats`, Locust | cần đo |
| 5.8 Thảo luận | So với mục tiêu ở 1.3; giải thích kết quả; các mối đe dọa đến tính hợp lệ (bộ dữ liệu nhỏ, một người chấm…) | — | viết sau |

---

### CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN (~6–8 trang, Phiên 14)

| Mục | Nội dung | Nguồn |
|---|---|---|
| 6.1 Kết quả đạt được | Đối chiếu từng mục tiêu cụ thể ở 1.3.2: đạt, đạt một phần, chưa đạt | 📄 README §1 |
| 6.2 Hạn chế | Viết trung thực, chia theo phân hệ:<br>• **CSDL**: một số đối tượng cần chạy lại `schema_complete.sql`.<br>• **Chatbot**: chưa kiểm tra quyền sở hữu phiên ở `GET messages` / `PATCH` / `DELETE`; chưa có feedback; `get_adaptive_candidate_count` chưa dùng; cache theo sub-query đầu; chưa có đánh giá RAG đầy đủ.<br>• **Dịch**: model Groq dự phòng bị lỗi 404; consumer RabbitMQ không thử lại; `/tts` và `/audio` công khai.<br>• **Flashcard**: chất lượng AI chưa đo cho 8 ngôn ngữ; bộ từ chưa được biên tập viên duyệt.<br>• **Frontend**: lịch sử dịch chỉ nằm trong bộ nhớ; Dashboard có dữ liệu mẫu.<br>• **Bảo mật**: HS256 dùng chung bí mật; thu hồi token chưa lan sang Kong; chưa xác minh email / MSSV; chưa có CSP.<br>• **Triển khai**: container chatbot chạy root, thiếu HEALTHCHECK; rate limit của Kong dùng bộ đếm cục bộ.<br>• **Dịch tài liệu**: chưa đưa vào vận hành. | 📄 README §10; mục "Ghi chú kỹ thuật và giới hạn" của từng README; Auth README §9 |
| 6.3 Hướng phát triển | Gồm 5 tiểu mục, mỗi tiểu mục nêu **vấn đề → giải pháp đề xuất → công nghệ hoặc cách làm**. Danh sách chi tiết ở bảng ngay dưới. | 📄 README §11 (hàng "Hướng phát triển") |

**Năm tiểu mục của 6.3 Hướng phát triển:**

| Tiểu mục | Nội dung |
|---|---|
| **6.3.1 Đưa Document Translation Service vào vận hành** (theo quyết định 1, khoảng 1–1,5 trang) | • Tách worker OCR / dịch thành container riêng, có thể chạy trên GPU rời hoặc dịch vụ đám mây.<br>• Dùng hàng đợi Celery có giới hạn đồng thời theo VRAM.<br>• Lưu trạng thái job vào Redis kèm TTL; tiến độ đẩy qua SSE.<br>• Chạy lại và kiểm chứng benchmark: parser PDF, cắt bảng, độ chính xác glossary, tăng tốc song song.<br>• Glossary trích từ tài liệu tự động tạo flashcard qua sự kiện `doc.translated`.<br>• Ephemeral RAG: hỏi đáp trên chính tài liệu vừa tải lên.<br>• Mở lại cờ `VITE_FEATURE_DOC_TRANSLATION` và viết test e2e. |
| 6.3.2 Chatbot | • Bộ đánh giá RAG có nhãn và chạy trong CI.<br>• Endpoint feedback và vòng học từ phản hồi.<br>• Kiểm tra quyền sở hữu phiên.<br>• Bật quota ứng viên thích ứng.<br>• Tự động cập nhật tri thức theo lịch (crawl định kỳ, phát hiện thay đổi).<br>• Cân nhắc CRAG hoặc HyDE.<br>• Kết nối dữ liệu cá nhân hóa (điểm, lịch học) nếu được trường cấp quyền. |
| 6.3.3 Dịch và Flashcard | • Thử lại khi consumer lỗi, kèm dead-letter queue.<br>• Bảo vệ `/tts`.<br>• Đánh giá chất lượng sinh từ cho 10 ngôn ngữ, có nhiều người chấm.<br>• Quy trình biên tập bộ từ.<br>• Ứng dụng di động / PWA, ôn tập offline. |
| 6.3.4 Bảo mật | • Chuyển sang RS256 / JWKS.<br>• Lan truyền thu hồi token.<br>• Dùng Redis cho bộ đếm rate limit dùng chung.<br>• Xác minh email / MSSV, quên mật khẩu bằng OTP.<br>• Thêm CSP. |
| 6.3.5 Hạ tầng | • Healthcheck, chạy container bằng user không phải root.<br>• Giám sát bằng Prometheus / Grafana, tracing theo correlation-id.<br>• Chuyển sang Kubernetes để mở rộng theo chiều ngang. |

---

### TÀI LIỆU THAM KHẢO (Phiên 15)

Theo mục 2.3 và mục 8 của kế hoạch này. Mục tiêu khoảng 35–50 tài liệu.

### PHỤ LỤC (Phiên 15, không đánh số trang)

| Phụ lục | Nội dung | Nguồn |
|---|---|---|
| A. Hướng dẫn cài đặt và vận hành | Yêu cầu, `.env`, tải mô hình, chạy compose, tạo admin, nạp tri thức, seed catalog. **Đã có:** bảng giới hạn tài nguyên container (A.1) | 📄 README §7, `DEPLOY_QUICKSTART.md` |
| B. Đặc tả chi tiết use case | **Đã viết ở Phiên 6b:** đặc tả và sơ đồ của 13 use case không trình bày trong mục 3.2 (UC01, 03, 04, 06, 07, 09, 10, 11, 13, 14, 15, 17, 18), cùng sơ đồ hoạt động của UC12 và UC16 | 🧩 `routers/*.py`, `services/*.py` |
| C. Thiết kế API chi tiết | **Đã có:** luồng qua Kong (C.1), định dạng phản hồi (C.2), mã HTTP (Bảng C.1), nhóm endpoint (Bảng C.2), sự kiện SSE (Bảng C.3, Hình C.3). **Còn thiếu:** danh sách endpoint đầy đủ (Phiên 15) | 📄 mục "API" từng README; 🧩 `routers/*.py` |
| D. Prompt template chính | Router, prompt theo intent, Self-RAG, vocab pipeline (rút gọn) | 🧩 `prompts/prompt_templates.py`, `vocab_pipeline.py` |
| E. Lược đồ cơ sở dữ liệu | **Đã có:** luồng hàm `match_chunks_hybrid_rrf` (Hình E.1), 10 bảng thuộc tính (E.1–E.10) | 🧩 `db/schema_complete.sql` |
| F. Bộ câu hỏi đánh giá chatbot | Điền sau khi có Chương 5 | — |

### NHẬT KÝ LÀM VIỆC

Bảng 15 tuần theo mẫu của Khoa. Có thể dựng sơ bộ từ lịch sử git (191 commit, từ 10/06/2026 đến 29/10/2026) và **nhóm cần xác nhận lại**.

---

## 5. Danh mục công thức của Chương 2

Mỗi công thức phải có: công thức LaTeX + "trong đó: …" giải thích **mọi** ký hiệu + 1–2 câu ý nghĩa. Với công thức có tham số dùng trong hệ thống, ghi **giá trị thực tế**.

| Số | Mục | Công thức | Giá trị thực tế trong hệ thống |
|---|---|---|---|
| (2-1) | 2.1.1 | Scaled dot-product attention: $\text{Attention}(Q,K,V)=\text{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right)V$ | |
| (2-2) | 2.1.1 | Multi-head: $\text{MultiHead}=\text{Concat}(\text{head}_1..\text{head}_h)W^O$, $\text{head}_i=\text{Attention}(QW_i^Q,KW_i^K,VW_i^V)$ | |
| (2-3) | 2.1.1 | Positional encoding sin/cos (giới thiệu thêm RoPE) | |
| (2-4) | 2.1.1 | Mô hình ngôn ngữ tự hồi quy: $P(x)=\prod_t P(x_t\mid x_{<t})$; loss cross-entropy | |
| (2-5) | 2.1.1 | Định tuyến MoE: $y=\sum_{i\in \text{TopK}} g_i(x)E_i(x)$ | Qwen3 A3B |
| (2-6) | 2.1.2 | Softmax có temperature: $p_i=\frac{e^{z_i/T}}{\sum_j e^{z_j/T}}$ | lấy `temperature` từ cấu hình |
| (2-7) | 2.1.2 | Lấy mẫu nucleus (top-p): tập nhỏ nhất $V_p$ thỏa $\sum_{x\in V_p}p(x)\ge p$ | |
| (2-8) | 2.2.1 | RAG: $P(y\mid q)\approx\sum_{d\in \text{top-}k}P(d\mid q)\,P(y\mid q,d)$ | top_k = 8 |
| (2-9) | 2.2.2 | Cosine similarity | ngưỡng L2 cache 0.60 |
| (2-10) | 2.2.2 | Mean pooling embedding | 768 chiều |
| (2-11) | 2.2.2 | Loss tương phản (MultipleNegativesRanking / InfoNCE) | |
| (2-12) | 2.2.2 | Điểm cross-encoder: $s=\sigma(W\cdot h_{[CLS]}(q\oplus d))$ | ngưỡng 0.20 / 0.65 / 0.80 |
| (2-13) | 2.2.3 | Khoảng cách cosine và L2, tích vô hướng | toán tử `<=>` của pgvector |
| (2-14) | 2.2.3 | Phân phối tầng của HNSW: $l=\lfloor -\ln(U)\cdot m_L\rfloor$, $m_L=1/\ln M$ | m = 16, ef_construction = 64 |
| (2-15) | 2.2.3 | Độ phức tạp tìm kiếm $O(\log N)$ | |
| (2-16) | 2.2.4 | TF-IDF | |
| (2-17) | 2.2.4 | BM25: $\sum_{t\in q}\text{IDF}(t)\frac{f(t,d)(k_1+1)}{f(t,d)+k_1(1-b+b\frac{|d|}{avgdl})}$ | (lý thuyết) |
| (2-18) | 2.2.4 | IDF của BM25 | |
| (2-19) | 2.2.4 | Ý tưởng cover density của `ts_rank_cd` (mô tả theo tài liệu PostgreSQL) | hệ thống dùng hàm này |
| (2-20) | 2.2.4 | RRF: $\text{RRF}(d)=\sum_{r\in R}\frac{1}{k+\text{rank}_r(d)}$ | k = 60 |
| (2-21) | 2.2.5 | Multi-query: hợp kết quả của các sub-query $\{q_1..q_n\}$ | n ≤ 4 |
| (2-22) | 2.2.5 | Hàm thứ tự sandwich (đặt tài liệu tốt nhất ở đầu và cuối) | |
| (2-23) | 2.2.5 | Quy tắc ghi cache / Quality Gate: ghi khi confidence = HIGH, cache hit khi $s_{bi}\ge0.60 \wedge s_{ce}\ge0.80 \wedge$ số học khớp | |
| (2-24) | 2.2.7 | Hit Rate@K | |
| (2-25) | 2.2.7 | MRR $=\frac{1}{|Q|}\sum_i \frac{1}{\text{rank}_i}$ | |
| (2-26) | 2.2.7 | Precision@K, Recall@K | |
| (2-27) | 2.2.7 | nDCG@K | |
| (2-28) | 2.3.1 | NMT: $P(y\mid x)=\prod_t P(y_t\mid y_{<t},x)$ | |
| (2-29) | 2.3.1 | Điểm beam search có chuẩn hóa độ dài | beam_size lấy từ code |
| (2-30) | 2.3.1 | Cross-attention encoder–decoder | |
| (2-31) | 2.3.2 | Lượng tử hóa affine: $q=\text{round}(x/s)+z$, $\hat x=s(q-z)$ | INT8 |
| (2-32) | 2.3.2 | Hệ số tỉ lệ $s=\frac{\max|x|}{127}$ (lượng tử hóa đối xứng) | |
| (2-33) | 2.3.3 | Phân loại fastText: $P(y\mid x)=\text{softmax}(B\cdot\frac{1}{N}\sum A x_n)$ | `lid.176` |
| (2-34) | 2.3.3 | Mô hình n-gram ký tự của Lingua | |
| (2-35) | 2.3.3 | Công thức fusion có hiệu chỉnh | **lấy đúng từ `LANGUAGE_DETECTION.md` / `language_detection.py`** |
| (2-36) | 2.3.4 | Quy tắc `decide_domain` | **lấy từ `DOMAIN_DETECTION.md` §3** |
| (2-37) | 2.3.5 | Simplified Lesk: $\arg\max_{s}|\text{gloss}(s)\cap \text{context}|$ | |
| (2-38) | 2.3.7 | BLEU $=BP\cdot\exp\left(\sum_n w_n\log p_n\right)$, kèm BP | |
| (2-39) | 2.3.7 | chrF$_\beta$ | β = 2 |
| (2-40) | 2.4.1 | Ebbinghaus: $R=e^{-t/S}$ | |
| (2-41) | 2.4.2 | SM-2: cập nhật EF | |
| (2-42) | 2.4.2 | SM-2: khoảng ôn $I(n)$ | |
| (2-43) | 2.4.3 | FSRS: retrievability theo hàm lũy thừa $R(t,S)=\left(1+F\frac{t}{S}\right)^{-w_{20}}$ | **đối chiếu mã nguồn gói `fsrs` v6** |
| (2-44) | 2.4.3 | Khoảng ôn theo retention mong muốn $I(r,S)$ | desired_retention lấy từ code |
| (2-45) | 2.4.3 | Stability ban đầu $S_0(G)$ | |
| (2-46) | 2.4.3 | Difficulty ban đầu và cập nhật (mean reversion) | |
| (2-47) | 2.4.3 | Stability sau khi nhớ được $S'_r$ | |
| (2-48) | 2.4.3 | Stability sau khi quên $S'_f$ | |
| (2-49) | 2.4.3 | Stability ôn trong ngày (short-term, FSRS-6) | |
| (2-50) | 2.5.2 | Rate limit fixed window: cho qua nếu $\text{count}(ip,\lfloor t/W\rfloor)<L$ | L = 1000/phút; 10/phút cho login |
| (2-51) | 2.5.4 | Khóa CAS: `terms/{lang[:2]}_{MD5(lower(term))}.mp3`; khóa cache SHA-256 | |
| (2-52) | 2.5.5 | Chữ ký JWT HS256: $\text{HMAC-SHA256}(K,\ \text{b64url}(H)\Vert"."\Vert\text{b64url}(P))$ | |
| (2-53) | 2.5.5 | Chi phí bcrypt: số vòng $2^{\text{cost}}$ | cost = 12 |

⚠ Các công thức FSRS (2-43)…(2-49) phải đối chiếu với **phiên bản gói `fsrs` thực tế** đang cài (`pip show fsrs`, đọc mã nguồn), không chép từ blog.

**Số thực tế sau Phiên 3.** Thứ tự công thức trong bản thảo khác bảng trên một chút:
- (2-29) là cross-attention, (2-30) là beam search.
- Nhận diện ngôn ngữ tách thành fusion (2-35) và meta-confidence (2-36).
- `decide_domain` tách thành điểm từ vựng (2-37) và quy tắc quyết định (2-38).
- Vì vậy các công thức từ Lesk trở đi lùi 2 số: Lesk (2-39), BLEU (2-40), chrF (2-41), Ebbinghaus (2-42), SM-2 (2-43)–(2-44), FSRS (2-45)–(2-51).
- **Phiên 4 bắt đầu từ (2-52)**: rate limit (2-52), khóa CAS (2-53), chữ ký JWT (2-54), bcrypt (2-55).

Các công thức FSRS đã được đối chiếu với `fsrs` 6.3.2 (`scheduler.py`).

---

## 6. Kế hoạch hình minh họa và sơ đồ

*Bổ sung ngày 30/10/2026 theo yêu cầu của nhóm: tăng sơ đồ và hình minh họa để báo cáo dễ đọc hơn.* Số thứ tự cuối cùng do Word sinh. Mã `H<chương>-<số>` dưới đây chỉ dùng để lên kế hoạch và theo dõi trong `figures/FIGURES.md`.

### 6.1. Nguyên tắc

**Mật độ.**
- Khoảng **130 hình bắt buộc** (mức A), tối đa khoảng 170 hình nếu làm thêm mức B, C. Báo cáo khoảng 220 trang chữ, nên trung bình cứ 1,5–2 trang có một hình.
- Không để quá **2 trang liên tiếp chỉ có chữ**. Ngoại lệ: tài liệu tham khảo, phụ lục, bảng đặc tả dài.
- Hình làm báo cáo dày thêm khoảng 25–35 trang. Cần hỏi GVHD nếu Khoa có giới hạn số trang.

**Các loại hình** (ký hiệu dùng ở mục 6.3):

| Mã | Loại | Dùng khi | Công cụ |
|---|---|---|---|
| KT | Sơ đồ kiến trúc, sơ đồ khối | Thành phần và quan hệ giữa các thành phần | SVG theo khuôn mẫu chung |
| LĐ | Lưu đồ (flowchart) | Thuật toán, pipeline, rẽ nhánh | PlantUML (sơ đồ hoạt động) |
| TT | Sơ đồ tuần tự | Tương tác theo thời gian giữa các thành phần. Quá 12–15 bước thì tách thành hai hình (a, b), ví dụ H4-11a, H4-11b | PlantUML |
| UC | Sơ đồ use case | Chức năng theo tác nhân (Chương 3) | PlantUML |
| HĐ | Sơ đồ hoạt động | Use case có nhiều nhánh | PlantUML |
| TTh | Sơ đồ trạng thái | Vòng đời thẻ FSRS, trạng thái job | PlantUML (đổi ở Phiên 6) |
| ERD | Sơ đồ thực thể – quan hệ | CSDL | PlantUML (đổi ở Phiên 6) |
| MH | Minh họa khái niệm | Lý thuyết Chương 2, ví dụ đồ chơi | SVG hoặc matplotlib |
| BĐ | Biểu đồ số liệu | Đường cong, phân bố, kết quả đo | matplotlib |
| VD | **Ví dụ thực tế** | Đầu vào/đầu ra thật của hệ thống, lấy từ log, dữ liệu hoặc lần chạy thật | SVG/HTML dựng từ dữ liệu |
| AC | Ảnh chụp giao diện (có thể đánh số chú thích ①②③) | Kết quả trên giao diện | Playwright + Pillow |

**Hộp "Ví dụ"** (không phải hình, không đánh số caption):
- khung nền nhạt, dùng style mới `Example Box` (thêm vào `reference.docx` ở Phiên 0b);
- dùng cho ví dụ tính tay ở Chương 2 (ví dụ: tính RRF cho 3 tài liệu với k = 60) và ví dụ dữ liệu ngắn ở Chương 4.

**Trung thực khi dùng hình.** Mở rộng nguyên tắc ở mục 2.1:
- Hình dùng số liệu đồ chơi: cuối caption ghi "(số liệu minh họa)".
- Hình vẽ lại từ tài liệu: ghi "(Vẽ lại theo [n])". Nếu lấy số liệu từ bài báo: ghi "(Số liệu: [n])".
- Hình **VD** ghi rõ nguồn: tên file log hoặc dữ liệu và ngày chạy. Một lượt chạy đơn lẻ chỉ là minh họa, **không** trình bày như kết quả đánh giá (kết quả đánh giá để ở Chương 5).
- **Không dùng ảnh trong `frontend/screenshots-responsive/` có nội dung chat, dịch hoặc thống kê.** Các ảnh này chứa dữ liệu giả của `src/mock/mockData.ts`: khi không gọi được backend, `services/chatService.ts`, `translationService.ts`, `dashboardService.ts` tự chuyển sang dữ liệu giả (ví dụ câu "Ghi chú dài để kiểm tra bảng cuộn ngang"). Chỉ dùng được các ảnh không chứa dữ liệu, như trang đăng nhập, để minh họa bố cục responsive.
- Ảnh e2e trong `services/realtime_translation_service/tests/e2e/screenshots/terminology/` chụp **giao diện phiên bản cũ** (logo "E", màu cam). Chỉ dùng ở Chương 5 làm minh chứng kiểm thử, có ghi rõ là giao diện cũ.
- Sơ đồ Mermaid lấy lại từ README (♻) phải được **đối chiếu với code trước khi vẽ lại**, vì README có thể sai so với code (mục 11).

### 6.2. Quy chuẩn hình (để cả cuốn trông thống nhất)

**Kích thước.**
- Rộng tối đa 15,5 cm. Hình nhỏ rộng 8–12 cm.
- Xuất PNG ≥ 200 dpi.
- Ảnh chụp: cửa sổ 1440×900, hệ số thu phóng 2.

**Chữ trong hình.**
- Phông Arial. Khi in cỡ chữ ≥ 9 pt. Riêng sơ đồ tuần tự dày cho phép tối thiểu 8 pt.
- Cao tối đa khoảng 20 cm để còn chỗ cho chú thích trong một trang. Hình cao hơn thì gộp bớt nút hoặc tách đôi.
- Tên hàm dài (ví dụ `generate_standalone_query`) không xuống dòng được và làm sơ đồ phình ra. Trên hình dùng nhãn tiếng Việt ngắn; tên hàm nêu trong phần văn bản.
- Tiếng Việt có dấu đầy đủ.
- Tên hàm, endpoint, bảng CSDL dùng Consolas.

**Bảng màu cố định theo thành phần.** Dùng cho mọi sơ đồ KT, LĐ, TT, ERD. Màu chủ đạo của frontend là thang `blue` của Tailwind (`frontend/tailwind.config.*`).

| Thành phần | Viền / nền | Ghi chú |
|---|---|---|
| Người dùng, trình duyệt, frontend | `#2563EB` / `#EFF6FF` | xanh IUH |
| nginx, Kong Gateway | `#475569` / `#F1F5F9` | xám đậm |
| Auth Service | `#7C3AED` / `#F5F3FF` | tím |
| Academic Chatbot Service | `#0D9488` / `#F0FDFA` | xanh ngọc |
| Realtime Translation Service | `#16A34A` / `#F0FDF4` | xanh lá |
| Flashcard Service | `#EA580C` / `#FFF7ED` | cam |
| Document Translation (thử nghiệm) | `#DB2777` / `#FDF2F8`, **viền nét đứt** | |
| Hạ tầng dữ liệu (Supabase/PostgreSQL, Redis, MinIO, RabbitMQ) | `#B45309` / `#FFFBEB` | nâu vàng |
| Dịch vụ bên ngoài (LLM API, Edge TTS) | `#6B7280` / trắng, **viền nét đứt** | |

**Đọc được khi in đen trắng.**
- Mỗi khối luôn có nhãn chữ.
- Đường gọi REST: nét liền. SSE: nét liền đậm. Sự kiện RabbitMQ: nét đứt.

**Mermaid và PlantUML.** Dùng chung một theme đặt trong `figures/src/_theme/`, nền trắng:
- `palette.json`: bảng màu gốc;
- `plantuml.iuml`: theme PlantUML, có stereotype màu theo phân hệ;
- `mermaid.json`, `classes.mmd`: theme Mermaid;
- `svg.css`: style cho SVG viết tay;
- `figstyle.py`: style matplotlib.

**Biểu đồ matplotlib.**
- Một style chung, lưới nhạt.
- **Không đặt tiêu đề trong hình** (tiêu đề nằm ở caption).
- Trục có ghi đơn vị.

**Ảnh chụp giao diện.**
- Dùng tài khoản demo tên trung tính ("Sinh viên Demo"), không để lộ email hay MSSV thật.
- Chụp ở chế độ sáng, trừ hình so sánh sáng–tối.
- Mọi ảnh cùng kích thước cửa sổ, có viền xám mảnh.
- Khi cần chú thích: đánh số ①②③ màu đỏ lên ảnh, giải thích bằng danh sách ngay dưới hình.

### 6.3. Danh mục hình theo chương

**Mức ưu tiên:**
- **A**: bắt buộc.
- **B**: nên có.
- **C**: làm nếu còn thời gian.

Ký hiệu ♻ là sơ đồ Mermaid có sẵn trong README. Repo có 23 sơ đồ như vậy; chúng được vẽ lại theo quy chuẩn 6.2 sau khi đối chiếu với code.

#### Chương 1 (5 hình)

| Mã | Mục | Nội dung | Loại | Nguồn | Ưu tiên |
|---|---|---|---|---|---|
| H1-01 | 1.1 | Thông tin học vụ phân tán: sinh viên phải tra cứu nhiều website (camnang, ctsv, tuyensinh, iuh.edu.vn) và nhiều file PDF | KT | `data_ingestion/sources.py` | A |
| H1-02 | 1.1 | Ba nhu cầu của sinh viên (tra cứu học vụ, đọc tài liệu ngoại ngữ, học từ vựng) và hệ thống hợp nhất | MH | — | A |
| H1-03 | 1.3 | Tổng quan giải pháp: 5 phân hệ và liên kết giữa chúng (dịch → lưu từ → flashcard → âm thanh) | KT | README §1, §2.3 | A |
| H1-04 | 1.3 | Ghép ảnh giao diện 4 phân hệ chính (chatbot, dịch, flashcard, quản trị) | AC | Phiên S | B |
| H1-05 | 1.5 | Quy trình nghiên cứu và phát triển lặp: tài liệu → yêu cầu → thiết kế → cài đặt → kiểm thử, CI → đánh giá | LĐ | README §8, `ci.yml` | A |

#### Chương 2 (43 hình)

| Mã | Mục | Nội dung | Loại | Nguồn | Ưu tiên |
|---|---|---|---|---|---|
| H2-01 | 2.1.1 | Kiến trúc Transformer (vẽ lại theo Vaswani 2017) | MH | [EN] | A |
| H2-02 | 2.1.1 | Scaled dot-product attention và multi-head attention | MH | [EN] | A |
| H2-03 | 2.1.1 | Mô hình decoder-only sinh từng token (tự hồi quy) | MH | — | B |
| H2-04 | 2.1.1 | Mixture-of-Experts: router chọn top-k chuyên gia | MH | Shazeer 2017 | B |
| H2-05 | 2.1.2 | Phân phối xác suất token ở 3 giá trị temperature (số liệu minh họa) | BĐ | — | A |
| H2-06 | 2.1.2 | Top-p: tập nucleus trên phân phối đã sắp xếp (số liệu minh họa) | BĐ | — | B |
| H2-07 | 2.1.3 | Cấu trúc một prompt: system/persona, few-shot, ngữ cảnh, câu hỏi | MH | `prompt_templates.py` | B |
| H2-08 | 2.1.4 | Các hạn chế của LLM (ảo giác, ngày cắt kiến thức, prompt injection) và cách giải quyết (RAG, guardrail) | MH | — | A |
| H2-09 | 2.2.1 | Naive RAG: lập chỉ mục – truy xuất – sinh | MH | Lewis 2020 | A |
| H2-10 | 2.2.1 | So sánh Naive, Advanced, Modular RAG (vẽ lại theo Gao 2023) | MH | `paper/check_2312.10997v5.pdf` | A |
| H2-11 | 2.2.2 | Bi-Encoder và Cross-Encoder | MH | Reimers 2019 | A |
| H2-12 | 2.2.2 | Không gian embedding: câu hỏi học vụ thật chiếu xuống 2 chiều (PCA), câu cùng chủ đề nằm gần nhau | VD | câu hỏi trong `logs/academic_chatbot/`; mô hình bi-encoder cục bộ | B (cần chạy được mô hình) |
| H2-13 | 2.2.3 | Đồ thị nhiều tầng của HNSW và đường tìm kiếm tham lam | MH | Malkov 2018 | A |
| H2-14 | 2.2.4 | Hai danh sách xếp hạng (vector, FTS) hợp nhất bằng RRF, k = 60; kèm hộp ví dụ tính tay | MH | `schema_complete.sql` | A |
| H2-15 | 2.2.4 | PostgreSQL FTS: văn bản → `unaccent` → `tsvector` → `websearch_to_tsquery` → `ts_rank_cd` | LĐ | `schema_complete.sql` | B |
| H2-16 | 2.2.5 | Kỹ thuật trước truy xuất: viết lại câu hỏi, tách nhiều truy vấn, HyDE | MH | `paper/` | B |
| H2-17 | 2.2.5 | Lost in the Middle: độ chính xác theo vị trí của tài liệu đúng (vẽ lại, số liệu từ bài báo) | BĐ | `paper/check2307.03172v3.pdf` | A |
| H2-18 | 2.2.5 | Parent–Child (Small-to-Big): tìm bằng child nhỏ, đưa parent lớn vào ngữ cảnh | MH | — | A |
| H2-19 | 2.2.5 | Luồng Self-RAG và CRAG | MH | `paper/` | B |
| H2-20 | 2.2.5 | Ý tưởng semantic cache: so khớp theo nghĩa thay vì theo chuỗi | MH | — | B |
| H2-21 | 2.2.6 | Ba chiến lược chunking trên **cùng một đoạn quy chế thật** | VD | văn bản trong kho tri thức | A |
| H2-22 | 2.2.7 | Ví dụ tính Hit@K, MRR, nDCG trên 3 câu hỏi (số liệu minh họa) | MH | — | B |
| H2-23 | 2.3.1 | Encoder–decoder có cross-attention cho dịch máy | MH | NLLB 2022 | A |
| H2-24 | 2.3.1 | Cây beam search (beam = 2) cho một câu ngắn (số liệu minh họa) | MH | — | B |
| H2-25 | 2.3.1 | NLLB-200: một mô hình cho nhiều cặp ngôn ngữ; mã `eng_Latn`, `vie_Latn`… | MH | Realtime README §3.1 | C |
| H2-26 | 2.3.2 | Lượng tử hóa FP16 → INT8 và sai số làm tròn | BĐ | — | B |
| H2-27 | 2.3.3 | Nhận diện ngôn ngữ: fastText + Lingua + fusion | LĐ ♻ | Realtime README §3.4, `LANGUAGE_DETECTION.md` | A |
| H2-28 | 2.3.4 | Quy tắc quyết định chuyên ngành `decide_domain` | LĐ | `DOMAIN_DETECTION.md` §3 | A |
| H2-29 | 2.3.5 | Ví dụ Lesk chọn nghĩa của một từ đa nghĩa | VD | WordNet | B |
| H2-30 | 2.3.7 | Ví dụ so khớp n-gram khi tính BLEU | MH | Papineni 2002 | B |
| H2-31 | 2.4.1 | Đường cong lãng quên và tác dụng của các lần ôn ngắt quãng | BĐ | tính bằng gói `fsrs` 6.3.2 | A |
| H2-32 | 2.4.3 | Mô hình DSR: quan hệ giữa độ khó, độ ổn định và khả năng nhớ | MH | Ye 2022 | A |
| H2-33 | 2.4.3 | Đường R(t) của FSRS với các độ ổn định S khác nhau | BĐ | `fsrs` 6.3.2 | A |
| H2-34 | 2.4.3 | Lịch ôn mô phỏng: khoảng ôn thay đổi theo chuỗi đánh giá Again/Hard/Good/Easy | BĐ | `fsrs` 6.3.2, tham số mặc định | A |
| H2-35 | 2.5.1 | Kiến trúc nguyên khối và microservices | MH | Newman 2021 | A |
| H2-36 | 2.5.2 | Mẫu API Gateway: một cửa vào, định tuyến, xác thực tập trung | MH | — | A |
| H2-37 | 2.5.2 | Rate limit cửa sổ cố định theo thời gian (số liệu minh họa) | BĐ | — | B |
| H2-38 | 2.5.3 | REST, SSE và message broker trên trục thời gian | TT | — | A |
| H2-39 | 2.5.3 | Topic exchange của RabbitMQ: routing key → queue | MH | — | A |
| H2-40 | 2.5.4 | Content-Addressable Storage: cùng nội dung → cùng khóa → không lưu trùng | MH | — | B |
| H2-41 | 2.5.5 | Cấu trúc JWT header.payload.signature, dùng claim thật của hệ thống | MH | `utils/security.py` | A |
| H2-42 | 2.6 | Bản đồ công nghệ theo tầng (giao diện – gateway – dịch vụ – dữ liệu – AI – hạ tầng). Thay cho việc chèn từng logo riêng lẻ | KT | README §4 | A |
| H2-43 | 2.7 | Dòng thời gian các kỹ thuật RAG nâng cao 2020–2024, đánh dấu kỹ thuật đề tài áp dụng | MH | `paper/` | B |

#### Chương 3 (44 hình)

| Mã | Mục | Nội dung | Loại | Nguồn | Ưu tiên |
|---|---|---|---|---|---|
| H3-01 | 3.1.1 | Sơ đồ ngữ cảnh: tác nhân, hệ thống và các dịch vụ bên ngoài | KT | `AppRouter.tsx`, `kong.template.yml` | A |
| H3-02 | 3.2.1 | Use case tổng quát (dịch tài liệu gắn nhãn «thử nghiệm») | UC | — | A |
| H3-03 → H3-07 | 3.2.2–3.2.6 | Use case của 5 phân hệ: Xác thực, Chatbot, Dịch, Flashcard, Quản trị (5 hình) | UC | `routers/*.py` | A |
| H3-08 → H3-21 | 3.2.2–3.2.6 | Sơ đồ tuần tự cho UC01–UC18 (14 hình; gộp các UC có luồng giống nhau) | TT | `routers/*.py`, `services/*.py` | A |
| H3-22 | 3.2.5 | Sơ đồ hoạt động UC12 Ôn tập theo FSRS | HĐ | `fsrs_algorithm.py`, `StudyMode.tsx` | A |
| H3-23 | 3.2.6 | Sơ đồ hoạt động UC16 Nạp tri thức | HĐ | `routers/admin_ingest.py` | A |
| H3-24 | 3.2.5 | Sơ đồ hoạt động UC15 Trò chơi ôn từ (chấm điểm phía máy chủ) | HĐ | `game_service.py`, `game_logic.py` | B |
| H3-25 | 3.3.1 | Kiến trúc tổng thể, mức container | KT ♻ | README §2.1 | A |
| H3-26 | 3.3.2 | Một request đi qua Kong | TT ♻ | gateway README §2 | A |
| H3-27 | 3.3.3 | Ba kiểu giao tiếp trong hệ thống (REST, SSE, sự kiện) | KT | README §2.2 | A |
| H3-28 | 3.3.3 | Luồng sự kiện sinh âm thanh cho thẻ mới | TT ♻ | README §2.3 | A |
| H3-29 | 3.3.4 | Kiến trúc phân lớp bên trong một service | KT | README §9 | A |
| H3-30 | 3.3.5 | Sơ đồ triển khai: container, cổng, mạng, GPU | Triển khai (PlantUML) | `docker-compose*.yml` | A |
| H3-31 | 3.4.1 | Phân chia bảng theo service (tô màu theo 6.2) | KT | db README §3 | A |
| H3-32 | 3.4 | ERD tổng thể | ERD ♻ | db README §4 | A |
| H3-33 → H3-36 | 3.4.2–3.4.5 | ERD theo nhóm: tri thức RAG, người dùng – hội thoại, flashcard, dịch thuật (4 hình, đủ lớn để đọc được) | ERD | `schema_complete.sql`, `migrations/003–007` | A |
| H3-37 | 3.4.2 | Chỉ mục HNSW, GIN và luồng hàm `match_chunks_hybrid_rrf` | LĐ | `schema_complete.sql` | B |
| H3-38 | 3.5.1 | Cấu trúc envelope `{ok, data, error}` và mã lỗi | MH | README §9 | B |
| H3-39 | 3.5.3 | Dòng sự kiện SSE của chat: `metadata` → `delta`… → `done` / `error` | TT | Chatbot README §3 | A |
| H3-40 | 3.6.1 | Vòng đời phiên đăng nhập và token | TT ♻ | Auth README §4.2 | A |
| H3-41 | 3.6.2 | Các lớp phòng thủ: trình duyệt → Kong → service → CSDL (RLS) | KT | README §6, Auth README §9 | A |
| H3-42 | 3.7.1 | Sơ đồ điều hướng (sitemap) và phân quyền route | LĐ | `AppRouter.tsx` | A |
| H3-43 | 3.7.2 | Hệ thống thiết kế: logo, bảng màu, chữ, sáng/tối | MH | `assets/brand/`, `tailwind.config.*` | B |
| H3-44 | 3.7.2 | Trang đăng nhập ở 360 / 768 / 1280 px (trang không chứa dữ liệu nên dùng được ảnh có sẵn) | AC | `screenshots-responsive/theme-after/light/login-*.png` | B |

#### Chương 4 (65 hình)

| Mã | Mục | Nội dung | Loại | Nguồn | Ưu tiên |
|---|---|---|---|---|---|
| H4-01 | 4.1 | Pipeline thu thập tri thức tổng quát | LĐ ♻ | Ingestion README §1 | A |
| H4-02 | 4.1.1 | Thu thập URL: sitemap, danh mục, BFS theo độ sâu cho từng domain | MH | `sources.py`, `crawlers/` | A |
| H4-03 | 4.1.2 | Trang HTML gốc và văn bản sạch sau trafilatura, đặt cạnh nhau | VD | một trang camnang thật | A |
| H4-04 | 4.1.2 | Nhánh PDF: PyMuPDF → OCR (Gemini, Tesseract dự phòng) | LĐ | `extractors/` | B |
| H4-05 | 4.1.3 | HybridChunker | LĐ ♻ | Ingestion README §3.4 | A |
| H4-06 | 4.1.3 | Một văn bản thật được tách thành parent / child (tô màu từng đoạn) | VD | kho tri thức | A |
| H4-07 | 4.1.6 | Thống kê kho tri thức theo nguồn và loại tài liệu | BĐ | truy vấn Supabase | A (cần quyền DB) |
| H4-08 | 4.1.5 | Giao diện nạp tri thức và tiến độ SSE (có đánh số chú thích) | AC | Phiên S | A |
| H4-09 | 4.2 | Kiến trúc Academic Chatbot Service | KT ♻ | Chatbot README §2 | A |
| H4-10 | 4.2.1 | **Pipeline đầy đủ của một câu hỏi** (hình lớn, cả trang) | KT | Chatbot README §3–4 | A |
| H4-11a, H4-11b | 4.2.1 | Sơ đồ tuần tự `POST /messages/stream`, tách hai phần: (a) tiếp nhận, định tuyến, tra cache; (b) truy xuất, sinh, lưu kết quả. Đã vẽ ở Phiên 0b | TT ♻ | Chatbot README §3, `llm_generation_service.py` | A |
| H4-12 | 4.2.2 | Guardrail: các nhóm luật và ví dụ câu bị chặn | LĐ + VD | `guardrails/query_filter.py` và test | A |
| H4-13 | 4.2.3 | Ví dụ thật: câu hỏi → câu độc lập → 2 sub-query → intent `PROCEDURE` | VD | `logs/academic_chatbot/2026-10-29/142502-quy-trinh-ang-ky-hoc.md` | A |
| H4-14 | 4.2.4 | Semantic cache hai tầng | LĐ ♻ | Chatbot README §4.3 | A |
| H4-15 | 4.2.4 | Ví dụ một lượt cache hit thật | VD | log `…-CACHE-HIT-…md` | B |
| H4-16 | 4.2.5 | Truy xuất lai + rerank đa truy vấn | LĐ ♻ | Chatbot README §4.4 | A |
| H4-17 | 4.2.5 | Ví dụ thật: các chunk được chọn, điểm rerank, sub-query và nguồn | VD | log 29/10/2026 | A |
| H4-18 | 4.2.6 | Sắp xếp Sandwich: thứ tự chunk trước và sau | MH | `llm_generation_service.py` | A |
| H4-19 | 4.2.6 | Khung prompt với các thẻ cách ly `<retrieved_context>`, `<source id>`, `<query_reminder>` | VD | `prompt_templates.py` | A |
| H4-20 | 4.2.7 | Lớp nhà cung cấp LLM và chuỗi dự phòng | LĐ ♻ | Chatbot README §4.7 | A |
| H4-21 | 4.2.8 | Ví dụ khối `<thinking>` của Self-RAG và phần bị lọc khỏi luồng trả về | VD | log 29/10/2026 | A |
| H4-22 | 4.2.8 | Phân rã độ trễ của **một lượt hỏi** (router, truy xuất, sinh), ghi rõ là một lượt chạy | BĐ | log 29/10/2026 | B |
| H4-23 → H4-25 | 4.2 | Giao diện: chat đang streaming; trích dẫn nguồn (CitationBadge, có đánh số chú thích); danh sách phiên | AC | Phiên S | A |
| H4-26 | 4.3 | Kiến trúc Realtime Translation Service | KT ♻ | Realtime README §2 | A |
| H4-27 | 4.3.1 | Luồng dịch thường `POST /text` | LĐ ♻ | Realtime README §3.1 | A |
| H4-28 | 4.3.1 | Dịch streaming qua SSE | TT | router dịch, `DOMAIN_DETECTION.md` §2 | A |
| H4-29 | 4.3.2 | Ví dụ nhận diện văn bản trộn nhiều ngôn ngữ | VD | `LANGUAGE_DETECTION.md` §7 | B |
| H4-30 | 4.3.3 | Dịch theo chuyên ngành | LĐ ♻ | Realtime README §3.3 | A |
| H4-31 | 4.3.3 | Ví dụ: thuật ngữ từ điển được chèn vào prompt và kết quả dịch | VD | gọi API thật | A |
| H4-32 | 4.3.5 | TTS và kho âm thanh CAS | LĐ ♻ | Realtime README §3.6 | A |
| H4-33 → H4-36 | 4.3 | Giao diện: Translation Studio; chọn chuyên ngành và thông báo; WordAnalysisPopup; DictionaryAdmin | AC | Phiên S | A |
| H4-37 | 4.4 | Kiến trúc Flashcard Service | KT ♻ | Flashcard README §2 | A |
| H4-38 | 4.4.2 | Trạng thái thẻ **thực tế** trong hệ thống: New → Review; Again giữ ở Review và tăng `lapses`. Đặt cạnh mô hình 4 trạng thái của FSRS để so sánh (xem mục 11, điểm 16) | TTh | gói `fsrs` 6.3.2, `fsrs_algorithm.py` | A |
| H4-39 | 4.4.2 | Một thẻ cụ thể: 4 nút đánh giá cho ra 4 ngày ôn kế tiếp khác nhau | VD | tính bằng `fsrs` | B |
| H4-40 | 4.4.4 | Pipeline sinh từ vựng SELECT → ENRICH → VERIFY | LĐ ♻ | Flashcard README §3.4 | A |
| H4-41 | 4.4.4 | Ví dụ đầu ra thật của pipeline: một thẻ JSON đã qua kiểm tra | VD | `evaluation/results/topics_A.jsonl` | A |
| H4-42 | 4.4.5 | Clone-on-start bộ từ mẫu và nhập Excel | LĐ | `excel_importer.py`, service catalog | B |
| H4-43 | 4.4.6 | Chấm điểm trò chơi phía máy chủ | TT | `game_service.py` | B |
| H4-44 → H4-49 | 4.4 | Giao diện: sổ thẻ; phiên ôn (mặt trước/sau, 4 nút); sinh từ bằng AI; thư viện bộ từ; 4 trò chơi (ghép 2×2); thống kê và streak | AC | Phiên S | A |
| H4-50 | 4.5.1 | Lưu đồ đăng nhập: bcrypt luôn chạy, throttle hai tầng | LĐ | `auth_service.py` | A |
| H4-51 | 4.5.2 | Cấp, làm mới, thu hồi token với `token_version` | TT | `utils/security.py` | A |
| H4-52 | 4.5.3 | Chuỗi plugin của Kong theo thứ tự xử lý | KT | `kong.template.yml` | A |
| H4-53 | 4.5 | Giao diện đăng nhập / đăng ký | AC | Phiên S | A |
| H4-54 | 4.6.1 | Kiến trúc Document Translation (thử nghiệm, viền nét đứt) | KT ♻ | doc_translation README §1 | A |
| H4-55 | 4.6.2 | Giao diện thể hiện chức năng dịch tài liệu đang khóa bằng cờ tính năng (xem mục 11, điểm 17) | AC | Phiên S | B |
| H4-56 | 4.7.1 | Kiến trúc frontend: pages → components → hooks/context → services → API | KT | frontend README §2 | A |
| H4-57 | 4.7.1 | Luồng chat SSE phía client | TT ♻ | frontend README §4.2 | A |
| H4-58 | 4.7.2 | Dashboard (đánh dấu khối dữ liệu mẫu có `SampleDataBadge`) | AC | Phiên S | A |
| H4-59 | 4.7.6 | Hồ sơ và Cài đặt | AC | Phiên S | B |
| H4-60 | 4.7 | Responsive: cùng một trang ở 360 / 768 / 1280 px | AC | Phiên S | A |
| H4-61 | 4.7 | Giao diện sáng và tối | AC | Phiên S | B |
| H4-62 | 4.8.1 | Triển khai bằng Docker Compose: mạng, cổng, volume | KT | `docker-compose*.yml` | A |
| H4-63 | 4.8.2 | Giới hạn RAM / CPU / GPU theo container (là cấu hình, không phải số đo) | BĐ | các file compose | B |
| H4-64 | 4.8.3 | Pipeline CI trên GitHub Actions | LĐ | `.github/workflows/ci.yml` | A |
| H4-65 | 4.8.4 | Demo công khai qua Tailscale Funnel | KT ♻ | DEPLOY.md §2 | A |

#### Chương 5 (10 hình, vẽ khi có số liệu)

| Mã | Mục | Nội dung | Loại | Nguồn số liệu | Ưu tiên |
|---|---|---|---|---|---|
| H5-01 | 5.2 | Số test và kết quả theo service | BĐ | lần chạy `run_tests.sh all` | A |
| H5-02 | 5.3 | Hit@K / MRR theo cấu hình ablation | BĐ | `scripts/eval/retrieval_eval.py` | A |
| H5-03 | 5.3 | Tỷ lệ cache hit, độ trễ khi có và không có cache | BĐ | log chatbot | B |
| H5-04 | 5.3 | Phân bố độ trễ đầu–cuối và TTFT (box plot) | BĐ | log chatbot | B |
| H5-05 | 5.4 | Ma trận nhầm lẫn nhận diện ngôn ngữ | BĐ | `tests/test_results/benchmark_language_detection_report.md` (**đã có**) | A |
| H5-06 | 5.4 | Kết quả nhận diện chuyên ngành | BĐ | `benchmark_domain_detection_report.md` (**đã có**) | A |
| H5-07 | 5.4 | BLEU / chrF theo cặp ngôn ngữ | BĐ | `evaluation/run_bleu_chrf.py` | A |
| H5-08 | 5.5 | Một lời gọi và pipeline 3 bước khi sinh từ vựng | BĐ | `flashcard_service/evaluation/results/REPORT.md` (**đã có**) | A |
| H5-09 | 5.4 | Minh chứng e2e dịch chuyên ngành (ghi rõ là giao diện cũ) | AC | `tests/e2e/screenshots/terminology/` | C |
| H5-10 | 5.7 | RAM / VRAM đo thực tế theo container | BĐ | `docker stats` | B |

#### Chương 6 (3 hình)

| Mã | Mục | Nội dung | Loại | Ưu tiên |
|---|---|---|---|---|
| H6-01 | 6.1 | Mức hoàn thành mục tiêu theo phân hệ | MH | B |
| H6-02 | 6.3.1 | Kiến trúc đề xuất để đưa Document Translation vào vận hành | KT | A |
| H6-03 | 6.3 | Lộ trình phát triển theo giai đoạn | MH | B |

#### Tổng hợp

| Chương | Mức A | Mức B | Mức C | Tổng | Trong đó: ảnh giao diện | Trong đó: ví dụ thực tế (VD) |
|---|---|---|---|---|---|---|
| 1 | 4 | 1 | 0 | 5 | 1 | 0 |
| 2 | 25 | 17 | 1 | 43 | 0 | 3 |
| 3 | 39 | 5 | 0 | 44 | 1 | 0 |
| 4 | 54 | 11 | 0 | 65 | 20 | 12 |
| 5 | 6 | 3 | 1 | 10 | 1 | 0 |
| 6 | 1 | 2 | 0 | 3 | 0 | 0 |
| **Tổng** | **129** | **39** | **2** | **170** | **23** | **15** |

*Sau Phiên 0b:* H4-11 được tách thành H4-11a và H4-11b, nên danh mục có 171 hình (mức A: 130).

Số bảng vẫn như ước tính cũ (~60–70).

### 6.4. Quản lý hình

- `figures/FIGURES.md` liệt kê từng hình với các cột: mã, file PNG, file nguồn, chú thích, ghi chú nguồn, trạng thái (*chưa vẽ / đã vẽ / đã duyệt*). Đây là nơi duy nhất ghi chú thích chuẩn của hình.
- `build/render_figures.py` xuất lại các hình có file nguồn thay đổi trong `figures/src/`:
  - `.mmd` → Mermaid;
  - `.puml` → PlantUML;
  - `.svg` → PNG qua Playwright;
  - `.py` → matplotlib.
- `build_report.py` (đã có) báo khi ảnh không tồn tại và khi hình chưa được nhắc trong văn bản. Phiên 0b bổ sung thêm cảnh báo khi caption trong bản thảo khác caption trong `FIGURES.md`.
- Hình chưa vẽ kịp: trong bản thảo vẫn đặt ảnh giữ chỗ (khung xám ghi mã hình), để thấy trước bố cục trang.

### 6.5. Danh sách ảnh giao diện cần chụp (Phiên S)

**Chuẩn bị:**
- Hệ thống chạy đầy đủ bằng `docker compose up`.
- Một tài khoản sinh viên demo và một tài khoản admin.
- 4–5 phiên chat hỏi câu thật.
- Hai sổ thẻ (tiếng Anh, tiếng Nhật) có thẻ đến hạn ôn.
- Một bộ từ mẫu lấy từ catalog.
- Từ điển chuyên ngành có dữ liệu.

`build/screenshots.py` chạy kịch bản cố định nên chụp lại được mỗi khi giao diện thay đổi.

| # | Trang / trạng thái | Dùng cho |
|---|---|---|
| S01–S02 | `/login`: tab đăng nhập, tab đăng ký | H4-53 |
| S03 | `/dashboard` | H4-58 |
| S04–S07 | `/chat`: màn hình chào; đang streaming; câu trả lời có trích dẫn và popover nguồn; danh sách phiên | H4-23 → H4-25, H1-04 |
| S08–S11 | `/translation`: kết quả dịch theo chuyên ngành; thông báo chuyên ngành (DomainStatus); WordAnalysisPopup; SaveFlashcardModal | H4-33 → H4-35 |
| S12–S20 | `/flashcards`: chọn ngôn ngữ; DeckDashboard; danh sách thẻ; StudyMode mặt trước; mặt sau và 4 nút; SessionSummary; GenerateVocabModal và kết quả; thư viện bộ từ; ImportExcelModal | H4-44 → H4-49 |
| S21–S24 | 4 trò chơi: MatchPairs, SpeedRound, WordBuilder, Shooter | H4-48 |
| S25 | Thống kê học tập và streak (LearningStreakHeatmap) | H4-49 |
| S26–S29 | `/admin`: nạp tri thức; tiến độ SSE; danh sách tài liệu; DictionaryAdmin | H4-08, H4-36 |
| S30 | `/translation-doc` đang bị khóa | H4-55 |
| S31–S32 | `/profile`, `/settings` | H4-59 |
| S33–S36 | `/chat` ở 360 và 768 px; `/chat` ở chế độ tối; `/flashcards` ở 360 px | H4-60, H4-61 |

---

## 7. Danh mục từ viết tắt dự kiến

Có nhiều hơn 10 từ nên **bắt buộc có danh mục**. Xếp A–Z. Bảng 3 cột: Từ viết tắt | Từ đầy đủ | Nghĩa.

ANN, API, BFS, BLEU, BM25, CAS, CI/CD, CoT, CORS, CRUD, CSDL, DSR, ERD, FSRS, FTS, GPU, HNSW, HTTP, IDOR, IPA, JSON, JWT, LLM, LRU, MoE, MRR, MSSV, NLP, NMT, OCR, ONNX, ORM, OWASP, RAG, REST, RLS, RPC, RRF, S3, SM-2, SPA, SSE, TTL, TTS, UC, UI, URL, VRAM, YC.

Trong bảng, "CSDL", "MSSV" là viết tắt tiếng Việt; vẫn xếp chung theo A–Z. Danh sách được cập nhật dần trong quá trình viết. Khi tổng hợp, chỉ giữ những từ thật sự xuất hiện trong bài.

---

## 8. Tài liệu tham khảo dự kiến

⚠ Thông tin xuất bản (tập, số, trang) **phải kiểm tra lại** từ nguồn gốc khi viết Phiên 15. Danh sách dưới đây chỉ là danh sách cần thu thập.

### 8.1. Tiếng Việt

- Trường ĐH Công nghiệp TP.HCM, *Quy chế đào tạo trình độ đại học* (văn bản hiện hành). **Nhóm cung cấp số hiệu và năm.**
- Trường ĐH Công nghiệp TP.HCM, *Sổ tay sinh viên* (camnang.iuh.edu.vn).
- ~~Trường ĐH Công nghiệp TP.HCM (2025), *Thông báo 892 – Quy định về học tiếng Anh*~~. ⚠ *Phát hiện ở Phiên 1:* file `B:\KhoaLuan\tb-892-2025-Quy dinh ve hoc tieng Anh.pdf` thực chất là bản sao cuốn khóa luận QuyLong (92 trang), không phải Thông báo 892. **Nhóm cần cung cấp lại văn bản đúng** nếu muốn trích dẫn.
- Khoa CNTT – IUH, *Mẫu báo cáo khóa luận tốt nghiệp*.
- (Tùy chọn) Các khóa luận hoặc bài báo tiếng Việt về chatbot, RAG, PhoBERT.

### 8.2. Tiếng Anh: đã có trong `paper/`

| File | Công trình |
|---|---|
| `check_2312.10997v5.pdf` | Gao Y. và cs., *Retrieval-Augmented Generation for Large Language Models: A Survey* |
| `check2310.11511v1.pdf` | Asai A. và cs., *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection* |
| `2401.15884v3.pdf` | Yan S.-Q. và cs., *Corrective Retrieval Augmented Generation* |
| `check2305.14283v3.pdf` | Ma X. và cs., *Query Rewriting for Retrieval-Augmented Large Language Models* |
| `check2307.03172v3.pdf` | Liu N. F. và cs., *Lost in the Middle: How Language Models Use Long Contexts* |
| `processing2212.10496v1.pdf` | Gao L. và cs., *Precise Zero-Shot Dense Retrieval without Relevance Labels* (HyDE) |
| `check2605.18209v1.pdf` | Chunhachatrachai P. và cs., *SpatioRoute: Dynamic Prompt Routing for Zero-Shot Spatial Reasoning* (chỉ dùng cho ý định tuyến prompt) |

### 8.3. Tiếng Anh: cần bổ sung

**LLM**
- Vaswani A. và cs. (2017), *Attention Is All You Need*.
- Brown T. và cs. (2020), *Language Models are Few-Shot Learners*.
- Wei J. và cs. (2022), *Chain-of-Thought Prompting*.
- Holtzman A. và cs. (2020), *The Curious Case of Neural Text Degeneration* (top-p).
- Báo cáo kỹ thuật Qwen3.
- Shazeer N. và cs. (2017), *Outrageously Large Neural Networks* (MoE).

**RAG và truy xuất**
- Lewis P. và cs. (2020), *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*.
- Karpukhin V. và cs. (2020), *Dense Passage Retrieval*.
- Reimers N., Gurevych I. (2019), *Sentence-BERT*.
- Nogueira R., Cho K. (2019), *Passage Re-ranking with BERT*.
- Chen J. và cs. (2024), *BGE M3-Embedding*.
- Nguyen D. Q., Nguyen A. T. (2020), *PhoBERT*.
- Malkov Y., Yashunin D. (2018), *HNSW*.
- Robertson S., Zaragoza H. (2009), *The Probabilistic Relevance Framework: BM25 and Beyond*.
- Cormack G. và cs. (2009), *Reciprocal Rank Fusion*.
- Järvelin K., Kekäläinen J. (2002), *nDCG*.

**Dịch máy và xử lý ngôn ngữ**
- NLLB Team (2022), *No Language Left Behind*.
- Joulin A. và cs. (2017), *Bag of Tricks for Efficient Text Classification* (fastText).
- Papineni K. và cs. (2002), *BLEU*.
- Popović M. (2015), *chrF*.
- Lesk M. (1986).
- Miller G. (1995), *WordNet*.
- Jacob B. và cs. (2018), *Quantization … Integer-Arithmetic-Only Inference*.

**Lặp lại ngắt quãng**
- Ebbinghaus H. (1885/1913), *Memory*.
- Wozniak P., Gorzelanczyk E. (1994), SM-2.
- Cepeda N. và cs. (2006).
- Ye J. và cs. (2022), *A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling* (KDD).
- Ye J. và cs. (2023), *Optimizing Spaced Repetition Schedule by Capturing the Dynamics of Memory* (IEEE TKDE).
- Tài liệu thuật toán FSRS (wiki open-spaced-repetition).

**Kiến trúc và bảo mật**
- Newman S. (2021), *Building Microservices*, 2nd ed.
- Richardson C. (2018), *Microservices Patterns*.
- Jones M. và cs. (2015), RFC 7519 *JSON Web Token*.
- Provos N., Mazières D. (1999), *bcrypt*.
- OWASP Top 10 (2021) và OWASP Top 10 for LLM Applications.
- Tài liệu chính thức: Kong, FastAPI, React, PostgreSQL FTS (`ts_rank_cd`), pgvector, RabbitMQ, Redis, MinIO, Docker.

---

## 9. Phân chia các phiên viết

Mỗi phiên tương ứng khoảng **một lượt làm việc dài**. Sau mỗi phiên nhóm duyệt rồi mới sang phiên tiếp theo. Có thể gộp hoặc tách phiên tùy độ dài thực tế.

*Cập nhật 30/10/2026:*
- Thêm Phiên **0b** (dựng công cụ vẽ hình) và Phiên **S** (chụp giao diện).
- Tách Phiên 5 thành **5a/5b**, vì số sơ đồ của Chương 3 tăng.
- Cột "Hình" ghi số hình mức A/B phải xong trong phiên đó (mã hình ở mục 6.3).

| Phiên | Nội dung | Đầu vào chính | Đầu ra | Hình (A/B) | Trang |
|---|---|---|---|---|---|
| **0** ✅ | Dựng công cụ ghép DOCX, file mẫu định dạng | File mẫu 2021, PDF mẫu, QuyLong | `build/*`, `MAU_DINH_DANG.docx/.pdf` | — | — |
| **0b** ✅ | **Dựng công cụ vẽ hình**: `render_figures.py` (Mermaid, PlantUML, SVG, matplotlib); theme chung và bảng màu 6.2; khuôn SVG cho sơ đồ kiến trúc; style matplotlib; khung `screenshots.py` + đánh số chú thích; style `Example Box`; `figures/FIGURES.md`; **vẽ thử 6 hình mẫu, mỗi loại một hình** (H3-25 KT, H4-14 LĐ, H4-11 TT, H3-02 UC, H2-33 BĐ, H4-13 VD) để nhóm duyệt phong cách | 23 sơ đồ ♻ trong README, log chatbot, gói `fsrs` | Bộ công cụ hình + 6 hình mẫu | 6 | — |
| **1** | Chương 1 | README §1, §3; `sources.py`; khảo sát ngoài repo | `01_tong_quan.md` | 4 / 1 | 10–12 |
| **2** | 2.1 LLM + 2.2 RAG (kèm công thức 2-1…2-27) | `paper/`, Chatbot README §4, db README §5 | `02_1_llm_rag.md` | 12 / 10 | 20–22 |
| **3** | 2.3 Dịch máy + 2.4 Lặp lại ngắt quãng (2-28…2-49) | Realtime README, LANGUAGE / DOMAIN_DETECTION, mã gói `fsrs` | `02_2_dich_may_srs.md` | 7 / 4 (+1 C) | 14–16 |
| **4** | 2.5 Microservices + 2.6 Công nghệ + 2.7 Nghiên cứu liên quan + tiểu kết | README §2, §4, gateway, Auth README §4 | `02_3_microservices_congnghe.md` | 6 / 3 | 10–12 |
| **5a** | 3.1 Yêu cầu + 3.2 Use case: 6 sơ đồ use case, 18 bảng đặc tả | `routers/*.py`, `AppRouter.tsx`, `kong.template.yml` | `03_1_yeu_cau_usecase.md` | 7 / 0 | 18–20 |
| **5b** | 3.2 (tiếp): 14 sơ đồ tuần tự, 3 sơ đồ hoạt động | `routers/*.py`, `services/*.py` | bổ sung vào `03_1_…md` | 16 / 1 | 10–12 |
| **6** | 3.3 Kiến trúc + 3.4 CSDL + 3.5 API + 3.6 Bảo mật + 3.7 Giao diện | db README, `schema_complete.sql`, gateway README, frontend README | `03_2_kien_truc_csdl_api.md` | 16 / 4 | 20–22 |
| **S** | **Chụp giao diện** theo danh sách 6.5 (36 ảnh). *Quyết định 30/10/2026:* tạm chưa chạy Docker. Các phiên viết đặt **ảnh giữ chỗ** đúng mã hình (đã tạo sẵn trong `figures/chN/`); **nhóm tự chụp sau** và lưu đè đúng tên file, rồi chạy lại `render_figures.py` và `build_report.py` | Hệ thống chạy bằng `docker compose up`, tài khoản demo | `figures/screenshots/*` | 17 / 4 (ảnh dùng ở Phiên 1, 7–12; đã tính trong số hình của các phiên đó) | — |
| **7** | 4.1 Pipeline tri thức (cần **truy vấn thống kê kho tri thức**) | Ingestion README, `data_ingestion/*` | `04_1_ingestion.md` | 7 / 1 | 10–12 |
| **8** | 4.2 Chatbot (phần nhiều hình nhất: 17 hình) | Chatbot README, `rag_service.py`, `llm_generation_service.py`, `prompt_templates.py`, `query_filter.py`, `logs/academic_chatbot/` | `04_2_chatbot.md` | 15 / 2 | 18–22 |
| **9** | 4.3 Realtime Translation | Realtime README, `app/services/*` | `04_3_realtime.md` | 10 / 1 | 12–14 |
| **10** | 4.4 Flashcard | Flashcard README, `fsrs_algorithm.py`, `vocab_pipeline.py`, `game_*.py`, `evaluation/results/` | `04_4_flashcard.md` | 10 / 3 | 12–14 |
| **11** | 4.5 Auth + Kong; 4.6 Doc Translation (thử nghiệm) | Auth / gateway README, doc_translation README + `notes_for_thesis.md` | `04_5_auth_gateway.md`, `04_6_doc_translation.md` | 5 / 1 | 10–12 |
| **12** | 4.7 Frontend + 4.8 Triển khai | frontend README, ảnh Phiên S, compose, DEPLOY, `ci.yml` | `04_7_frontend.md`, `04_8_trien_khai.md` | 7 / 3 | 14–16 |
| **13** | Khung Chương 5: phương pháp, thiết kế thí nghiệm, bảng trống, `[CHỜ SỐ LIỆU]`. **Vẽ luôn H5-05, H5-06, H5-08** vì đã có số liệu trong repo | README §8, §11, các tài liệu `evaluation/`, `tests/test_results/` | `05_kiem_thu_danh_gia.md` | 3 (+3 chờ số liệu) | 10–12 (khung) |
| **14** | Chương 6 + phần đầu (Abstract, Tóm tắt, Lời cảm ơn, Danh mục viết tắt) | Toàn bộ bản thảo | `06_ket_luan.md`, `00_phan_dau.md` | 1 / 2 | 8–10 |
| **15** | Tài liệu tham khảo (kiểm tra từng nguồn) + hoàn thiện Phụ lục A, C, D (B, E đã viết ở Phiên 6b) | `paper/`, README, `schema_complete.sql`, prompts | `90_…md`, `91_…md` | — | — |
| **16** | **Tổng hợp**: ghép trang bìa, phụ bìa, các trang nhận xét, toàn bộ bản thảo → DOCX; chuẩn hóa caption, TOC, header/footer, số trang | Mọi file `drafts/`, `figures/` | `build/IUH_EduBot_BaoCao.docx` | — | — |
| **17** | Rà soát: chính tả, nhất quán thuật ngữ, trích dẫn ↔ danh mục, **hình ↔ chú thích ↔ FIGURES.md**, mật độ hình (không quá 2 trang chỉ có chữ), checklist ở mục 12 | DOCX | Bản hoàn chỉnh (chưa có Chương 5) | — | — |
| **18+** | (Sau này) Nhóm bổ sung số liệu Chương 5 → vẽ các biểu đồ còn lại → cập nhật Abstract, Tóm tắt, 6.1 → build lại | Kết quả đo | Bản cuối | 3 / 3 + 1 C | +20–30 |

**Thứ tự ưu tiên** nếu cần thay đổi:
- Phiên 0b phải làm trước mọi phiên viết, vì mọi phiên đều có hình.
- Phiên S nên làm sớm, ngay khi hệ thống chạy được.
- Chương 4 có thể viết trước Chương 2 và 3, vì nó bám sát code nhất.
- Phần đầu và Chương 6 viết cuối.

**Mỗi phiên viết, hình được làm cùng lúc với chữ.** Phiên chỉ được coi là xong khi các hình mức A của phiên đã có trong `figures/` và được ghép thử vào DOCX.

---

## 10. Thông tin nhóm cần cung cấp

| # | Thông tin | Dùng ở | Cần trước phiên |
|---|---|---|---|
| 1 | Họ tên, MSSV, lớp, khóa của 2 sinh viên | Bìa, phụ bìa, footer | 16 (càng sớm càng tốt) |
| 2 | Họ tên, học hàm / học vị GVHD; ngành; tháng / năm bảo vệ | Bìa, lời cảm ơn | 14 |
| 3 | Tên đề tài tiếng Anh cho phụ bìa EN (mặc định giữ `IUH_Academic_Counseling_Chatbot`) | Phụ bìa EN | 14 |
| 4 | Phân công công việc giữa 2 thành viên | Nhật ký, có thể thêm một bảng phân công | 15 |
| 5 | Nhật ký 15 tuần (có thể dựa trên lịch sử git) | Nhật ký làm việc | 15 |
| 6 | Truy cập Supabase để chạy truy vấn thống kê kho tri thức; xác nhận bản RPC `match_chunks_hybrid_rrf` đang chạy trên DB | 4.1.6, 3.4 | 7 |
| 7 | Hệ thống chạy được (`docker compose up`) để chụp giao diện, kèm tài khoản demo (sinh viên, admin) và dữ liệu demo theo mục 6.5. Nếu không, nhóm tự chụp theo danh sách 6.5 | Chương 1, 4 | S |
| 7b | **Cấp quyền tải 2 công cụ vẽ:** `plantuml.jar` (GitHub release) và `mermaid.min.js` (bản cố định từ cdn.jsdelivr.net). Hoặc nhóm tự tải về `build/tools/` | Mọi sơ đồ UC, HĐ, LĐ, TT, ERD | 0b |
| 7c | Mô hình bi-encoder cục bộ chạy được trên máy, để vẽ H2-12 (không gian embedding). Không có thì bỏ hình này (mức B) | 2.2.2 | 2 |
| 8 | Số hiệu và năm của Quy chế đào tạo IUH hiện hành và các văn bản trong kho tri thức | 1.1, TLTK | 1 |
| 9 | (Nếu có) kết quả khảo sát sinh viên về nhu cầu | 1.1 | 1 |
| 10 | Kết quả đo Chương 5 | Chương 5 | 18 |

---

## 11. Những điểm phải đối chiếu với mã nguồn

Danh sách các chỗ đã phát hiện tài liệu khác với code, hoặc dễ viết sai.

| # | Vấn đề | Cách viết đúng trong báo cáo |
|---|---|---|
| 1 | **BM25 và `ts_rank_cd`**: tài liệu cũ gọi là BM25 | Chương 2 trình bày BM25 như nền tảng lý thuyết. Chương 3 và 4 ghi rõ hệ thống dùng PostgreSQL FTS (`websearch_to_tsquery` + `ts_rank_cd`, có `unaccent`) |
| 2 | **LLM mặc định**: `llm_providers.py` mặc định `openai` (vLLM / Ollama, Qwen), `rag_service.py` mặc định `gemini`; bản demo dùng Gemini | Trình bày là **lớp LLM cấu hình được** qua `LLM_PROVIDER`, có chuỗi dự phòng Gemini. Nêu rõ cấu hình dùng khi demo và khi đo |
| 3 | **Số ứng viên thích ứng 30 / 50 / 70**: hàm `get_adaptive_candidate_count` tồn tại nhưng **pipeline không gọi** | Mô tả cấu hình thực tế (`candidate_count=50`). Phần thích ứng đưa vào hạn chế hoặc hướng phát triển |
| 4 | **OTP / quên mật khẩu**: `system-architechture-report.md` có nhắc, nhưng code không có | Không mô tả như tính năng. Đưa vào 6.3.4 |
| 5 | **SM-2**: không được cài đặt | Chỉ trình bày ở lý thuyết để so sánh |
| 6 | **Database-per-service**: chỉ ở mức quy ước, dùng chung một Supabase | Nói rõ đây là ranh giới logic, không phải tách vật lý |
| 7 | **Schema DB**: DB đang chạy có thể được nạp từ file cũ | Mô tả theo `schema_complete.sql` và ghi chú (db README §6) |
| 8 | **Dashboard** có khối dữ liệu mẫu | Ghi rõ dưới ảnh chụp, hoặc chụp phần dùng dữ liệu thật |
| 9 | **Số liệu "quảng cáo"** (100% thuật ngữ, 99,9%, >60%…) | Không dùng nếu không có script đo chạy lại được |
| 10 | **`routers/cache.py`** không được include vào app | Không mô tả như endpoint đang hoạt động |
| 11 | **Benchmark `test_rag_benchmark.py`** chỉ kiểm tra **công thức** trên dữ liệu viết cứng | Không gọi là kết quả đánh giá RAG |
| 12 | Số test trong README là **đếm bằng grep, chưa chạy** | Chương 5 phải dùng số liệu từ lần chạy thật |
| 13 | Quyền sở hữu phiên chat chưa được kiểm tra ở một số endpoint | Thiết kế ở 3.6 không được tuyên bố "chống IDOR toàn diện" cho chatbot. Ghi vào 6.2 |
| 14 | Số ngôn ngữ: dịch 10 ngôn ngữ, flashcard 10 ngôn ngữ (frontend hoặc tài liệu cũ có chỗ ghi 9) | Đếm lại trong code (`languages` router, cấu hình NLLB) trước khi viết |
| 15 | `paper/check2605.18209v1.pdf` không phải bài về RAG | Chỉ trích khi nói về định tuyến prompt |
| 16 | **Trạng thái thẻ FSRS** (phát hiện ở Phiên 0b). `fsrs_algorithm.py` tạo `Scheduler(learning_steps=(), relearning_steps=(), enable_fuzzing=True)`. Khi chạy thử gói `fsrs` 6.3.2 với đúng cấu hình này: thẻ mới chuyển **thẳng sang Review** sau lần ôn đầu, và chọn Again vẫn ở Review (chỉ tăng `lapses`). Learning (1) và Relearning (3) có trong quy ước cột `state` nhưng không bao giờ xuất hiện. Ngoài ra, khi không nạp được `fsrs`, module dùng **bộ lập lịch dự phòng không phải FSRS** | Chương 2 trình bày đủ 4 trạng thái của FSRS (lý thuyết). Chương 4 vẽ đúng hai trạng thái thực tế New → Review và giải thích lý do: DB không lưu `step`. Nêu bộ lập lịch dự phòng ở 4.4.2 |
| 17 | `/translation-doc` khi tắt cờ `VITE_FEATURE_DOC_TRANSLATION` **chuyển hướng về `/translation`** (`AppRouter.tsx` dòng 47–50), không hiển thị trang khóa | Hình H4-55 phải chụp đúng cách giao diện thể hiện trạng thái khóa (đối chiếu `frontend/tests/DocTranslationLock.test.tsx` ở Phiên 11) |
| 19 | **Số đoạn đưa vào prompt** (phát hiện ở Phiên 2). Tham số `top_k=8` của `retrieve_relevant_chunks_multi` **không được dùng** trong thân hàm (`rag_service.py` dòng 367–555). Số đoạn cha cuối cùng do quota quyết định: 1–2 sub-query lấy tối đa 5 đoạn, 3–4 sub-query lấy tối đa 8 đoạn. Thêm vào đó, mỗi sub-query được giữ 2–3 đoạn cha "tốt" (điểm ≥ 0,65), hoặc tối thiểu 2–3 đoạn khi không đủ đoạn tốt | Mục 4.2.5 mô tả theo quota thực tế, không ghi "top_k = 8". Nêu tham số thừa này ở 6.2 |
| 20 | **`hnsw.ef_search`** (phát hiện ở Phiên 2). Mã nguồn không đặt tham số này, nên pgvector dùng giá trị mặc định 40. Theo tài liệu pgvector, quét chỉ mục HNSW trả về tối đa `ef_search` hàng, trong khi `match_chunks_hybrid_rrf` lấy `LIMIT max(2·match_count, 60)` = 100 ứng viên ở nhánh vector | Cần kiểm tra trên CSDL thật (số hàng nhánh vector trả về). Nếu đúng như dự đoán, nêu ở 6.2 và đề xuất `SET hnsw.ef_search` ở 6.3.2 |
| 21 | **Vai trò `public`** (phát hiện ở Phiên 5a). Ngoài `student`, đăng ký còn nhận vai trò `public` (bí danh public/guest/parent/highschool), không bắt buộc email IUH, khoa, ngành. Hạn mức sinh từ vựng AI mỗi ngày: admin 50, student 10, public 3 (`vocab_quota.py`) | Đã đưa vào Bảng 3.1, UC01, UC13. Kế hoạch cũ chỉ có `student` và `admin` |
| 22 | **Phạm vi thu hồi token** (phát hiện ở Phiên 5b). Chỉ Auth Service so `tv` với `token_version` trong CSDL. Các service khác (`utils/security.py`, giống nhau ở 4 service) chỉ kiểm tra chữ ký, `iss`, `exp` và lấy vai trò từ claim. Vì vậy sau khi đăng xuất hoặc đổi mật khẩu, token cũ vẫn gọi được chatbot, dịch, flashcard đến khi hết hạn (tối đa 60 phút); đổi vai trò admin cũng chỉ có hiệu lực khi token cũ hết hạn | Đã ghi đúng phạm vi ở UC03, UC04 và Hình 3.6. Nêu ở 4.5 (cơ chế) và Chương 6 (hạn chế, hướng khắc phục: kiểm tra `tv` qua Redis hoặc rút ngắn hạn token) |
| 23 | **Âm thanh thẻ học** (phát hiện ở Phiên 5b). Chỉ `POST /cards` và `cards/from-translation` phát `flashcard.created`; `decks/from-generated`, nhập Excel và sao chép bộ từ mẫu không phát. Khi phát âm, giao diện (`useFlashcardAudio.ts`) gọi `/translate/tts` theo văn bản (khóa `tts/{MD5(text_voice)}.mp3`), lỗi thì gọi `/flashcards/tts`, cuối cùng dùng giọng đọc của trình duyệt; `audio_url` (tệp CAS `terms/…`) chỉ dùng khi thẻ không có văn bản | Đã sửa YC19, UC13. Khi viết 4.3 và 4.4: mô tả CAS là cơ chế sinh trước cho thẻ tạo tay và thẻ lưu từ trang dịch, không nói mọi thẻ đều phát từ tệp CAS |
| 24 | **Mã lỗi từ điển chuyên ngành** (phát hiện ở Phiên 5b). Trong `admin_dictionary.py`, `HTTPException(400)` (mục trùng, tệp sai định dạng) nằm trong `try … except Exception` nên bị đổi thành HTTP 500 với thông báo chung | Đặc tả UC18 chỉ ghi "báo lỗi", không ghi mã. Nêu ở Chương 6 (hạn chế) |
| 25 | **Bộ nhớ đệm dịch** (phát hiện ở Phiên 5b). Trang Dịch thuật dùng `/translate/stream`; nhánh dịch thông thường của endpoint này không tra và không ghi bộ nhớ đệm. Bộ nhớ đệm Redis chỉ có ở `/translate/text` (ô dịch nhanh trên Dashboard) và ở nhánh dịch theo chuyên ngành | Đã sửa UC07. Khi đo ở Chương 5, phân biệt rõ endpoint nào có bộ nhớ đệm |
| 26 | **Giới hạn tần suất của Kong gộp theo consumer** (phát hiện ở Phiên 6). `kong.template.yml` không đặt `limit_by`, nên Kong dùng mặc định `consumer`, chỉ quay về IP khi không xác định được consumer. Mọi JWT được ký dưới một consumer chung `auth-issuer`, nên trên route có JWT, giới hạn chung 1 000/phút và giới hạn sinh từ vựng 6/phút, 60/giờ có thể bị **dùng chung cho mọi người dùng** | Mục 3.3.2 đã ghi "theo tài liệu của Kong". **Chương 5 phải kiểm chứng** (hai tài khoản cùng gọi `/vocabulary/generate`, xem lượt thứ 7 có bị 429 không). Nếu đúng, nêu ở Chương 6 và đề xuất `limit_by: header` hoặc `ip` |
| 27 | **Sự kiện RabbitMQ không được thử lại** (phát hiện ở Phiên 6). Hai consumer bắt mọi ngoại lệ bên trong `async with message.process()`, nên khi xử lý lỗi (ví dụ Edge TTS lỗi) tin nhắn vẫn được ack, không vào hàng đợi lỗi, không thử lại | Đã ghi ở 3.3.3. Nêu ở Chương 6 (hướng: requeue có giới hạn hoặc dead-letter queue) |
| 28 | **Định dạng lỗi API chưa thống nhất** (phát hiện ở Phiên 6). Auth và Flashcard trả `{ok:false, error}`, Chatbot và Translation trả `{detail}`, Kong trả `{message}`. Client của Chatbot ở giao diện chỉ báo lỗi chung kèm mã HTTP. README của frontend ghi phát âm "ưu tiên URL âm thanh đã sinh sẵn", trái với `useFlashcardAudio.ts` (xem điểm 23) | Đã ghi ở 3.5.1 và Hình 3.39. Nêu ở Chương 6 |
| 18 | Sơ đồ tuần tự `POST /messages/stream` trong Chatbot README §3 thiếu bước: sau Router, hệ thống tính embedding của `queries[0]` và lưu embedding của tin nhắn người dùng ở nền (`llm_generation_service.py` dòng 319–325). Lệnh ghi cache trong khối `finally` cũng được gọi ở nhánh cache HIT, nhưng bị Quality Gate chặn vì `top_doc_score = 0` | Hình H4-11 vẽ theo code, có bước này |
| 29 | **Guardrail chặn nhầm** (phát hiện ở Phiên 8a). Chạy `check_safety_and_jailbreak` trên câu "Em quên hướng dẫn đăng ký học phần…" và "Khi nào nhà trường cập nhật hệ thống đăng ký học phần?" cho kết quả **bị chặn** (khớp mẫu "quên … hướng dẫn" và "cập nhật hệ thống"). Số mẫu: 13 + 22 = 35 | Đã ghi ở Bảng 4.4 (kết quả do `figures/src/ch4/_data/guardrail_check.py` sinh ra). Nêu ở Chương 6 (hạn chế, hướng: giới hạn mẫu theo ngữ cảnh) |
| 30 | **Ngưỡng cache** (Phiên 8a). `check_semantic_cache(threshold=0.92)` luôn dùng `min(threshold, 0.60)`, nên 0,92 không có tác dụng; Cross-Encoder (0,80) và so khớp số quyết định. Cache lưu câu trả lời dưới khóa là **truy vấn đầu tiên** dù câu hỏi được tách nhiều sub-query. Pipeline nạp tri thức **không tự xóa cache** (chỉ có `DELETE /messages/cache` thủ công) | Đã ghi ở 4.2.4. Nêu ở Chương 6; Chương 5 nên đo tỉ lệ trúng cache có tính tới điểm này |
| 31 | **Mã chưa nối vào luồng chạy** (Phiên 8a). `get_adaptive_candidate_count` (30/50/70 ứng viên) có unit test nhưng không được gọi, số ứng viên luôn 50. Trường `reason` của bộ định tuyến không được prompt yêu cầu nên thường rỗng. Với nhà cung cấp tương thích OpenAI, `temperature=0` bị đổi thành 0,2 (`generate_text`) | Đã ghi ở 4.2.3 và 4.2.5. Không mô tả thành "đã dùng" ở các chương khác |
| 32 | **Lưu tin nhắn** (Phiên 8a). Endpoint `POST /messages` (không streaming) gọi `save_user_msg_to_db` lúc nhận rồi gọi lại trong `save_turn_to_db`, nên **lưu tin nhắn người dùng hai lần**; giao diện chỉ dùng `/stream` nên chưa thấy lỗi. Endpoint `/stream` không lưu `latency_ms` và số token vào bảng `messages` (chỉ có trong log Markdown) | Đã ghi ở 4.2.1. Khi đo độ trễ ở Chương 5, lấy từ log Markdown chứ không từ bảng `messages` |
| 33 | **Giới hạn 20 yêu cầu/phút của slowapi** (Phiên 8a) dùng `get_remote_address`; `Dockerfile` chạy `uvicorn` không đặt `--forwarded-allow-ips`. Đứng sau Kong, địa chỉ nguồn có thể là địa chỉ của Kong, khi đó mọi người dùng chung một bộ đếm | **Chưa kiểm chứng** (cần chạy Docker). Chương 5 kiểm chứng cùng điểm 26; chưa khẳng định trong báo cáo |
| 34 | **Lớp nhà cung cấp LLM** (Phiên 8b). `OpenAICompatibleProvider.generate_stream` chuyển sang Gemini khi có ngoại lệ, kể cả giữa chừng: phần Gemini được **nối vào sau** phần đã gửi. Khi mọi mô hình lỗi, `GeminiProvider` trả chuỗi "⚠️ Lỗi AI: …" như văn bản thường; cổng chất lượng cache chỉ kiểm tra thẻ khi có mặt nên chuỗi này **có thể được ghi vào cache** | Đã ghi ở 4.2.7, ghi rõ "đọc từ mã, chưa tái hiện". Nếu có điều kiện, tái hiện ở Chương 5 (tắt cả Qwen lẫn Gemini). Nêu ở Chương 6 |
| 35 | **Metadata thiếu `created_at`/`upload_time`** (Phiên 8b). `wrap_context_sandbox` chỉ thêm dòng "Ngày cập nhật lên CSDL" khi metadata có hai khóa này; pipeline nạp tri thức không ghi (metadata chỉ có `title`, `source_url`, `breadcrumbs`, `published_date`, `headers`, đối chiếu log 29/10/2026). Luật `REGULATION` (CF-RAG) nêu "ngày cập nhật CSDL" là tiêu chí thứ 3 nên chưa có dữ liệu | Đã ghi ở 4.2.6. Nêu ở Chương 6 (hướng: truyền `published_date` hoặc cột `created_at` vào prompt) |
| 36 | **Phân quyền phiên hội thoại** (Phiên 8b). `GET /sessions/{id}/messages`, `PATCH`, `DELETE` nhận `current_user_id` nhưng không dùng; `save_user_msg_to_db` ghi đè `user_id` của phiên đã tồn tại; `GET /sessions` của người đăng nhập gồm cả phiên có `user_id` rỗng; mã phiên server sinh là `s_` + 8 hex rồi `uuid5` (32 bit). Kong yêu cầu JWT trên `/api/chat` nên chỉ người đã đăng nhập tới được | Đã ghi ở 4.2.9. Nêu ở Chương 6 (hạn chế bảo mật, hướng: kiểm tra `conversations.user_id` ở mọi endpoint, dùng `uuid4` đầy đủ) |
| 37 | **Prompt** (Phiên 8b). Luật niên khóa ghi cứng ("khóa + 2004", K21+ = khóa mới 2025, K23+ chưa tuyển sinh). Các few-shot nêu chi tiết cụ thể (Phòng Tài chính tầng trệt nhà E, Trung tâm Quản trị Hệ thống tầng 1 nhà A) chưa đối chiếu với tài liệu trường. Router gán `ADVISING` cho "điểm ưu tiên đối tượng chính sách" nhưng `REGULATION` cho "điểm ưu tiên khu vực" (log 29/10/2026) | **Nhóm cần kiểm tra** hai chi tiết địa điểm trong few-shot. Đã ghi ở 4.2.7 và 4.2.8 |
| 38 | **`match_past_messages` chỉ được suy ra** trong `db/schema_complete.sql` (chú thích "GIẢ ĐỊNH CẦN XÁC NHẬN"); định nghĩa thật nằm trong Supabase đang chạy | **Nhóm cần chạy** `SELECT pg_get_functiondef('match_past_messages'::regproc);` trên Supabase và đối chiếu với mục 4.2.6 (cùng phiên, ngưỡng 0,8, tối đa 3 tin) |
| 42 | **Nhánh toàn văn gần như không đóng góp** (Phiên 10b). `match_chunks_hybrid_rrf` dùng `websearch_to_tsquery('simple', unaccent(q))`, nối mọi từ bằng AND; với 35 câu hỏi đo, chỉ 2 câu có kết quả toàn văn (trung vị 0 đoạn khớp), nên tìm kiếm lai cho kết quả giống hệt chỉ vector (C1 = C3, `eval/results/retrieval_ablation.json`) | Đã ghi ở 5.2.1, 4.2.5, 6.2, 6.3. Đề xuất nới AND (khớp một phần số từ khóa) |
| 43 | **Bộ xếp hạng lại không phân biệt thực thể** (Phiên 10b). Câu hỏi về đồng phục của trường khác nhận điểm 0,52 từ nội quy IUH; ngưỡng 0,20 không chặn. Bộ định tuyến chặn được câu này ở E2 | Đã ghi ở 5.2.1 |
| 44 | **Khối `<thinking>` đóng sai** (Phiên 10b). Ở Q43 mô hình đóng bằng `</doc_relevance>`; bộ lọc streaming sẽ nuốt cả câu trả lời. Xảy ra 1/37 lượt RAG | Đã ghi ở 5.2.2. Hướng khắc phục: lọc theo thẻ đóng hợp lệ đầu tiên hoặc đặt giới hạn độ dài khối |
| 45 | **Kho có miền ngoài danh sách** (Phiên 10b). `pdt.iuh.edu.vn` có 3 tài liệu dù không nằm trong `ALLOWED_DOMAINS`, vì URL do quản trị viên nhập tay không qua bộ lọc tên miền | Đã ghi ở 4.1.1 và 4.1.6 |
| 39 | **Giao diện và máy chủ lệch nhau** (Phiên 9). Nút thích/không thích gọi `POST /api/chat/messages/{id}/feedback` (`chatService.ts` dòng 265–267) nhưng `routers/chat.py` không có route này. Dashboard vẫn dùng `mock/mockData.ts` (có `SampleDataBadge`). Lịch sử dịch chỉ nằm trong bộ nhớ trình duyệt | Đã ghi ở 4.4.1 và tiểu kết Chương 4. Nêu ở Chương 6 |
| 40 | **CI** (Phiên 9). Job `rag-eval-benchmark` chỉ chạy `scripts/eval/test_rag_benchmark.py`, kiểm thử các hàm Hit Rate@K, MRR, Precision@K trên dữ liệu mẫu, không truy xuất kho thật. DEPLOY.md ghi CI trên `main` đỏ ở 4 test của `realtime_translation_service` (thiếu NLLB, Redis, NLTK trong môi trường CI) | Đã ghi ở 4.4.2, nói rõ job này không thay thế Chương 5 |
| 41 | **Phụ thuộc vào ghi chép triển khai** (Phiên 9). Các điều "đã kiểm chứng" và "chưa kiểm chứng" ở 4.4.2 lấy từ `DEPLOY.md` (nhóm tự ghi), báo cáo chỉ trích phần "chưa kiểm chứng" và không lặp lại các con số vitest, `deploy_smoke.py` | Nếu nhóm muốn trích kết quả kiểm chứng, cần chạy lại và đưa vào Chương 5 |

---

## 12. Checklist rà soát cuối

**Định dạng**
- [ ] Lề 3 / 3 / 3,5 / 2 cm; TNR 13; giãn dòng 1,5; đúng style Heading 1–4, Content, Caption, Bullet.
- [ ] Chương bắt đầu ở trang mới; heading "CHƯƠNG x" + tên chương in hoa.
- [ ] Mục lục cấp 1–3; danh mục hình và danh mục bảng sinh tự động; đã cập nhật trường (F9).
- [ ] Số trang bắt đầu từ 1 tại Chương 1; phụ lục không đánh số; header và footer đúng.
- [ ] Bảng chỉ kẻ ngang; chú thích bảng ở trên, chú thích hình ở dưới; công thức đánh số (x-y) căn phải.

**Hình**
- [ ] Đủ các hình mức A ở mục 6.3. `FIGURES.md` không còn hình nào ở trạng thái "chưa vẽ".
- [ ] Hình đúng quy chuẩn 6.2: bảng màu theo thành phần, chữ ≥ 9 pt khi in, rộng ≤ 15,5 cm, đọc được khi in đen trắng.
- [ ] Không có 2 trang liên tiếp chỉ có chữ, trừ các ngoại lệ ở 6.1.
- [ ] Hình số liệu minh họa ghi "(số liệu minh họa)"; hình vẽ lại ghi "(Vẽ lại theo [n])"; hình VD ghi nguồn log hoặc dữ liệu.
- [ ] Không có ảnh giao diện chứa dữ liệu giả từ `src/mock/`; không lộ email hay MSSV thật.
- [ ] Sơ đồ ♻ đã được đối chiếu với code.

**Nội dung**
- [ ] Mọi mục đã chia có ≥ 2 tiểu mục.
- [ ] Mọi hình và bảng được nhắc đến trong văn bản trước khi xuất hiện.
- [ ] Mọi công thức giải thích đủ ký hiệu.
- [ ] Mọi trích dẫn `[n]` có trong danh mục và ngược lại; danh mục đúng thứ tự (Việt → Anh, alphabet).
- [ ] Mọi từ viết tắt có trong danh mục, được định nghĩa ở lần đầu xuất hiện.
- [ ] Không còn `[TODO]` (trừ `[CHỜ SỐ LIỆU]` ở Chương 5 cho đến khi bổ sung).
- [ ] Không có số liệu thiếu nguồn; đã kiểm tra lần lượt 28 điểm ở mục 11.
- [ ] Thuật ngữ nhất quán (ví dụ luôn dùng "truy xuất lai", không lẫn với "tìm kiếm kết hợp").
- [ ] Chính tả tiếng Việt có dấu đầy đủ; không có emoji.
- [ ] Tên 2 sinh viên và GVHD đúng ở mọi nơi.
