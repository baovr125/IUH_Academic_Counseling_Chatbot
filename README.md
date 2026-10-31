# Báo cáo khóa luận: IUH Academic Counseling Chatbot (IUH EduBot)

Thư mục này chứa toàn bộ phần báo cáo khóa luận tốt nghiệp (bản thảo, công cụ dựng Word/PDF, hình, script đo thí nghiệm). Mã nguồn dự án nằm ở repo chính, không nằm ở đây. Nhánh `report/thesis` chỉ dùng để hai thành viên làm chung phần báo cáo; khi khóa luận xong sẽ xóa nhánh và chỉ giữ lại tệp báo cáo.

## 1. Tình trạng hiện tại (31/10/2026)

| Mục | Kết quả |
|---|---|
| Phần viết | Đã xong toàn bộ 6 chương, phụ lục A–F, tài liệu tham khảo, bìa, nhật ký (bản trống) |
| Số trang | 181 trang cả cuốn; phần chính 125/130 trang (Chương 3: 23/22, các chương còn lại đúng ngân sách) |
| Build | Không còn cảnh báo (hình, bảng, trích dẫn) |
| Tài liệu tham khảo | 56 mục, đều được trích dẫn |
| Chỗ còn trống | 12 ghi chú `[TODO]` và 4 ghi chú `[CHỜ SỐ LIỆU]` trong `drafts/`, đều cần thông tin hoặc số liệu của nhóm |

Số liệu Chương 5 đã đo bằng script trong `eval/` (kho tri thức ngày 31/10/2026, LLM Gemini):

- **Kho tri thức:** 415 tài liệu, 1.092 đoạn cha, 3.181 đoạn con.
- **E1 truy xuất (35 câu):** không xếp hạng lại Hit@3 80,0%; có cross-encoder Hit@3 94,3%. Toàn pipeline Hit@1 77,1%, Hit@3 91,4%. 10/10 câu ngoài kho bị từ chối.
- **E3 bộ nhớ đệm (mô phỏng):** 9/15 cặp diễn đạt lại trúng, 0/8 trúng nhầm.
- **E4 bộ lọc an toàn:** chặn 19/32 câu tấn công, chặn nhầm 6/60 câu hợp lệ.
- **E5 độ trễ (37 lượt RAG):** trung vị 3.338 ms, p95 17.155 ms.
- **E6 kiểm thử:** 1.642 kiểm thử, 1.634 đạt, 1 không đạt (lỗi của kiểm thử Auth, không phải lỗi chức năng), 7 bỏ qua.

Chưa có: **E2** (chấm tay chất lượng câu trả lời) và **E9** (giới hạn tần suất của Kong). Bảng 5.4, 5.5, 5.12 còn trống vì hai mục này.

## 2. Những việc đã làm

- Viết lại toàn bộ báo cáo theo kế hoạch phiên bản 2: phần chính ≤ 130 trang, trọng tâm là Academic Chatbot Service (pipeline nạp tri thức và Advanced RAG). Các phân hệ phụ (Dịch thuật, Flashcard, Auth, Kong, Frontend) chỉ trình bày ngắn.
- Đối chiếu tài liệu với mã nguồn: 45 điểm tài liệu lệch với mã đã được ghi lại (mục 11 của `KE_HOACH_VIET_BAO_CAO.md`) và các điểm yếu thật của mã nguồn được nêu trung thực ở Chương 4, 5, 6.
- Viết công cụ dựng báo cáo tự động: Markdown → Word → PDF, có in ngân sách trang từng chương, tự đánh số hình, bảng, công thức.
- Viết script đo thí nghiệm E1–E6 (chỉ đọc mã dự án và Supabase, không ghi CSDL) và tạo bộ dữ liệu đánh giá (45 câu hỏi có nhãn, 32 câu tấn công, 60 câu hợp lệ, 23 cặp cho bộ nhớ đệm).
- Dựng bìa, phụ bìa (tiếng Việt và tiếng Anh), danh mục viết tắt, lời cảm ơn, nhật ký làm việc (bảng trống).
- Soạn sẵn tệp chuẩn bị bảo vệ: các điểm yếu hội đồng có thể hỏi và những câu không nên nói (trong `GHI_CHU_CUOI.md`, mục 5).

## 3. Việc cần làm tiếp (chia theo người làm; đánh dấu ở `VIEC_NHOM_CAN_LAM.md`)

### 3.1 Bắt buộc trước khi nộp

1. **Thông tin bìa**: sửa `build/report_config.json` (mục `students` và `cover`): họ tên hai sinh viên, ngành (VN/EN), tên đề tài chính thức (VN/EN), học vị và họ tên GVHD (VN/EN), tháng nộp. Tên đề tài hiện tại chỉ là tên tạm. Điền thêm tên GVHD trong lời cảm ơn (`drafts/00_phan_dau.md`).
2. **Chấm tay E2** (xem lưu ý ở mục 5): hai người chấm độc lập `eval/results/rating_r1.csv` và `rating_r2.csv`. Bước `rating_tools.py merge` và `report` cần `rating_mapping.json` (không có trên nhánh, chỉ nằm trên máy người đã sinh các tệp chấm), nên người đó chạy hai lệnh này.
3. **E9 giới hạn tần suất của Kong** với hai tài khoản, cần Docker Compose. Nếu không kịp thì ghi "chưa kiểm chứng" kèm lý do vào Bảng 5.12, không để ô trống.
4. **Chụp 4 ảnh giao diện** (khổ ngang khoảng 16:9, chữ đọc được, không lộ email hay MSSV thật), lưu đúng tên vào `figures/ch4/`:
   - `H4-08.png`: trang Quản trị, đang nạp tri thức (thấy thanh tiến độ).
   - `H4-24.png`: chatbot trả lời một câu về quy chế hoặc học phí, hiện huy hiệu nguồn và nút gợi ý.
   - `H4-33.png`: trang Dịch thuật, chế độ chuyên ngành, có kết quả.
   - `H4-45.png`: phiên ôn tập flashcard, mặt sau thẻ, thấy bốn nút đánh giá.
5. **Nhật ký làm việc** (`drafts/92_nhat_ky.md`): công việc từng tuần và chữ ký GVHD. Gợi ý nhớ lại trong `eval/results/git_weekly.md`; viết lại theo việc đã làm, không chép nguyên commit.
6. Chạy lại build (mục 4) và cập nhật mục lục, danh mục hình, danh mục bảng trong Word.

### 3.2 Thông tin chỉ nhóm biết

- Vai trò của `ctsv.iuh.edu.vn` và `csm.iuh.edu.vn` (mục 1.1).
- Kết quả khảo sát sinh viên nếu có (mục 1.1). Không có thì xóa dòng TODO, không viết số giả.
- Kiểm tra lại các sản phẩm bên ngoài ở Bảng 1.1 và ghi ngày kiểm tra (mục 1.2).
- Số hiệu và năm ban hành Quy chế đào tạo theo hệ thống tín chỉ (tài liệu tham khảo).
- Nội dung đã tham khảo từ luyenty.com và ngày truy cập (mục 4.3.2).
- Cấu hình LLM khi demo (mục 2.4.3).
- Hai chi tiết địa điểm trong ví dụ mẫu của prompt có đúng không: "Phòng Tài chính – Kế toán tầng trệt nhà E", "Trung tâm Quản trị Hệ thống tầng 1 nhà A" (mục 4.2.7).

### 3.3 Kiểm tra kỹ thuật (làm trên máy có Supabase)

- Chạy `SELECT pg_get_functiondef('match_past_messages'::regproc);` rồi đối chiếu với mục 4.2.6 và Phụ lục E.
- Chạy `SHOW hnsw.ef_search;` rồi ghi đúng giá trị ở mục 2.2.3 và 4.2.5.
- Đọc lại các bộ dữ liệu đánh giá trong `eval/data/` (do trợ lý soạn, chưa ai duyệt): `questions.jsonl`, `guardrail_attacks.jsonl`, `guardrail_benign.jsonl`, `cache_pairs.jsonl`.
- Nếu sửa kiểm thử Auth `test_login_failure_is_logged_without_password`: chạy lại `eval/run_test_suites.py` và sửa số 1.634 ở mọi nơi (ABSTRACT, Tóm tắt, mục 5.3.1, mục 6.1).

### 3.4 Sau khi có số liệu E2 và E9

Điền Bảng 5.4, 5.5, 5.12; thêm một đoạn ở mục 5.4; sửa câu kết quả ở mục 6.1, ABSTRACT và Tóm tắt (mỗi phần phải còn đúng một trang). Vị trí điền chi tiết ở `GHI_CHU_CUOI.md`, mục 2.

## 4. Cách dựng báo cáo

### 4.1 Yêu cầu môi trường

Các mục dưới đây lấy từ mã trong `build/` và `figures/src/`, đối chiếu với máy đã dựng báo cáo (Windows 11, Python 3.11.8). Repo chưa có tệp `requirements.txt`.

| Thành phần | Dùng cho | Ghi chú |
|---|---|---|
| Windows + Microsoft Word | Cờ `--word` (cập nhật mục lục, danh mục hình/bảng, số trang, xuất PDF) | `build/word_update.ps1` điều khiển Word qua COM bằng PowerShell, nên **không chạy được trên macOS/Linux**. Máy viết dùng Word 2016 trở lên (Office16). Không có `--word` thì vẫn ra tệp `.docx` nhưng mục lục và số trang chưa được cập nhật, và không xuất được PDF (`--pdf` cần `--word`). |
| Python 3.11 | Mọi script | Máy viết dùng 3.11.8. |
| `python-docx`, `pypandoc_binary`, `pillow`, `pymupdf` | `build_report.py` | `pypandoc_binary` đã kèm sẵn pandoc (máy viết: pandoc 3.9), **không cần cài pandoc riêng**. `pymupdf` dùng để đếm trang và in ngân sách trang; thiếu thì build vẫn chạy nhưng báo "cần gói pymupdf để đếm trang". |
| `matplotlib`, `numpy` | Hình vẽ bằng `.py` trong `figures/src/` | |
| `fsrs` | 3 hình Chương 2: `H2-31.py`, `H2-33.py`, `H2-34.py` | Thư viện FSRS (máy viết: 6.3.2). Chỉ cần khi vẽ lại 3 hình này. |
| `playwright` + Chromium | Hình Mermaid (`.mmd`) và SVG (`.svg`) | Chạy `python -m playwright install chromium` nếu chưa có. `render_figures.py` tự dùng bản Chromium bất kỳ trong `%LOCALAPPDATA%\ms-playwright\chromium-*\`, không có thì dùng bản mặc định của Playwright. Máy viết: playwright 1.49.1. |
| Java | Hình PlantUML (`.puml`, 49 hình) | Lệnh `java -jar build/tools/plantuml.jar`. Máy viết: Java 25; `plantuml.jar` bản 1.2026.9. **Không cần cài Graphviz** (máy viết không có `dot` mà vẫn vẽ được). |
| Phông Times New Roman và Arial | Chữ trong báo cáo (Times New Roman cỡ 13, `reference.docx`) và trong hình, ảnh giữ chỗ (Arial) | Có sẵn trên Windows. |
| `build/tools/plantuml.jar`, `build/tools/mermaid.min.js` | Vẽ lại hình | **Không có trên nhánh** (đã bị `.gitignore`). Xin bản từ người đang giữ hoặc tải về. Dựng Word/PDF từ các PNG có sẵn trong `figures/` thì không cần. |

Cài nhanh các gói Python (phiên bản ghim trong `requirements.txt` là bản đã dùng trên máy viết, chưa thử trên máy trắng):

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

**Không phải máy nào cũng chạy được `eval/`.** Các script đo (`eval/`, và vài tệp trong `figures/src/ch4/_data/`) đang ghi cứng đường dẫn `B:\KhoaLuan\IUH_Academic_Counseling_Chatbot` (xem `eval/common.py`, `run_guardrail_eval.py`, `run_test_suites.py`), cần mã nguồn dự án ở đúng đường dẫn đó, tệp `.env` của dự án (Supabase, khóa Gemini) và các thư viện của dự án. Nếu cần chạy trên máy khác, đổi các đường dẫn này trước. Dựng báo cáo (`build/`) không phụ thuộc vào các điều kiện này.

### 4.2 Lệnh dựng

```powershell
cd Report
python -B -X utf8 build/render_figures.py [ID...]      # vẽ hình mới hoặc hình đổi
python -B -X utf8 build/renumber.py                    # sau khi thêm/bớt/chuyển hình, bảng, công thức
python -B -X utf8 build/build_report.py --word --pdf   # dựng báo cáo, in ngân sách trang
```

Kết quả ở `build/IUH_EduBot_BaoCao.docx` và `.pdf`. Sau khi build, kiểm tra: dòng `Phần chính ... / 130` không "VƯỢT", không có cảnh báo, số ghi chú TODO giảm theo.

Nếu `--word` báo lỗi: kiểm tra Word đã cài và không đang mở tệp docx; chạy được tay bằng `powershell -NoProfile -ExecutionPolicy Bypass -File build/word_update.ps1 -Docx <đường dẫn docx>`.

## 5. Quy tắc làm việc (bắt buộc)

- **Sửa ở `drafts/`, không sửa tay trong Word.** Lần build sau sẽ ghi đè bản Word.
- **Mô tả kỹ thuật phải khớp mã nguồn** của dự án. Không sửa mã nguồn dự án từ phần báo cáo.
- **Không bịa số liệu, tên người, số hiệu văn bản.** Chưa biết thì để `[TODO: …]`. Số liệu Chương 5 phải do script trong `eval/` sinh ra.
- **Không dùng số liệu "quảng cáo" của tài liệu cũ** (100% thuật ngữ, 99,9%…): không có script đo.
- **Chấm E2 phải độc lập.** Hai người chấm riêng, không biết cột A/B là phương án nào. Tệp đối chiếu `eval/results/rating_mapping.json` **không có trên nhánh này**; ai đang giữ thì không mở trước khi chấm xong. Tính kappa trên hai bản chấm độc lập trước khi thống nhất các ô khác nhau.
- **Tóm tắt và ABSTRACT** mỗi phần đúng một trang; ba trang "Nhận xét" mỗi trang một tờ.
- Nếu build báo `PermissionError` ở tệp docx: Word đang mở tệp, hãy đóng Word.

## 6. Làm việc chung trên nhánh này

Thư mục `Report` nằm ngoài cây mã dự án, nên clone repo rồi lấy nhánh này ra một thư mục riêng:

```
git clone https://github.com/baovr125/IUH_Academic_Counseling_Chatbot.git
cd IUH_Academic_Counseling_Chatbot
git worktree add ../Report report/thesis
```

- Mỗi lần làm: `git pull` trước, commit nhỏ, push sau. Hai người tránh cùng sửa một tệp `drafts/` một lúc.
- Đừng commit `build/IUH_EduBot_BaoCao.docx` và `.pdf` nếu chưa cần (mỗi bản khoảng 10–20 MB, repo là công khai và kho sẽ phình).
- Không đưa lên: tệp mẫu của Khoa, báo cáo khóa trước, khóa API, tệp `.env`. Đã có `.gitignore` chặn một số mục.
- Khi xong khóa luận: xóa nhánh, chỉ giữ lại tệp báo cáo.

## 7. Bản đồ thư mục và tệp

| Đường dẫn | Nội dung |
|---|---|
| `drafts/` | Bản thảo Markdown: bìa, phần đầu, Chương 1–6, tài liệu tham khảo, phụ lục, nhật ký |
| `build/` | Công cụ dựng báo cáo (`build_report.py`, `render_figures.py`, `renumber.py`, `report_config.json`, `reference.docx`) và bản dựng mới nhất |
| `figures/` | Hình theo chương, mã nguồn hình trong `figures/src/`, danh mục `FIGURES.md`, ảnh giữ chỗ cho 4 ảnh giao diện |
| `eval/` | Script đo thí nghiệm, dữ liệu vào (`data/`), kết quả (`results/`); cách chạy ở `eval/README.md` |
| `KE_HOACH_V2.md` | Dàn ý và ngân sách trang hiện hành |
| `KE_HOACH_VIET_BAO_CAO.md` | Quy định định dạng, quy tắc tài liệu tham khảo, mục 11 là 45 điểm đối chiếu với mã nguồn |
| `TIEN_DO.md` | Nhật ký tiến độ từng phiên |
| `VIEC_NHOM_CAN_LAM.md` | Danh sách việc dạng checklist (đánh dấu `[x]` khi xong) |
| `GHI_CHU_CUOI.md` | Vị trí điền chi tiết, quy trình hoàn thiện, điểm cần nắm khi bảo vệ |
| `PROMPT_PHIEN_MOI.md` | Bối cảnh và quy tắc để mở một phiên làm việc mới với trợ lý |

## 8. Nên đọc trước khi bảo vệ

`GHI_CHU_CUOI.md` mục 5: bảng các điểm yếu hội đồng có thể hỏi (truy xuất, nhánh toàn văn, bộ lọc an toàn, bộ nhớ đệm, độ trễ, bảo mật phiên) kèm số liệu và cách trả lời, cùng danh sách những câu không nên nói (ví dụ: không nói "chống tấn công toàn diện", không nói "độ chính xác X%" khi chưa có kết quả chấm tay).
