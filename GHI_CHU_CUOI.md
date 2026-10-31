# Ghi chú cuối: các điểm cần chú ý và cần bổ sung vào báo cáo

Tệp này viết ở Phiên 14 (rà soát cuối, 31/10/2026). Nó bổ sung cho `VIEC_NHOM_CAN_LAM.md` (danh sách việc) bằng ba phần: vị trí chính xác cần điền, những điểm dễ sai khi hoàn thiện, và những điểm hội đồng có thể hỏi. Khi xong một mục, đánh dấu `[x]`.

**Tình trạng:** 181 trang cả cuốn, phần chính 125/130 (Ch.3 23/22, Ch.4 42/42, Ch.5 18/18, Ch.6 4/4). Build không còn cảnh báo. Còn 12 ghi chú `[TODO]` và 4 ghi chú `[CHỜ SỐ LIỆU]` trong bản thảo, đều cần thông tin của nhóm.

---

## 1. Việc bắt buộc trước khi nộp (theo thứ tự nên làm)

1. **Thông tin bìa** (`build/report_config.json`): `students`, `cover.title_vi`, `title_en`, `major_vi`, `major_en`, `supervisor_vi`, `supervisor_en`, `date_vi`, `date_en`. Tên đề tài hiện là **tên tạm do trợ lý đề xuất**; chân trang tự lấy họ tên sinh viên. Đổi tên đề tài thì kiểm tra lại cả Tóm tắt và ABSTRACT cho khớp.
2. **Lời cảm ơn** (`drafts/00_phan_dau.md`, dòng có `[TODO: Họ tên và học vị…]`): tên GVHD.
3. **Chấm tay E2** rồi điền kết quả (mục 2.1 dưới đây).
4. **E9 giới hạn tần suất của Kong** (mục 2.2).
5. **4 ảnh giao diện:** `figures/ch4/H4-08.png`, `H4-24.png`, `H4-33.png`, `H4-45.png` (yêu cầu chi tiết ở `VIEC_NHOM_CAN_LAM.md` mục 1). Chạy `build/render_figures.py` rồi build lại. Không để lộ email, MSSV thật; không chụp trang Dashboard có dữ liệu mẫu.
6. **Nhật ký làm việc** (`drafts/92_nhat_ky.md`) và chữ ký GVHD.
7. **Thông tin còn thiếu ở Chương 1, 2, 4 và tài liệu tham khảo** (mục 2.3).
8. **Cập nhật mục lục, danh mục hình và bảng trong Word** (mục 4).

---

## 2. Điểm cần bổ sung vào báo cáo, theo từng vị trí

### 2.1 Sau khi chấm tay E2

| Vị trí | Việc cần làm |
|---|---|
| Bảng 5.4 (mục 5.2.2) | Điền tỉ lệ đúng / một phần / sai của V1 (có tài liệu) và V2 (không tài liệu), kèm khoảng tin cậy Wilson; điền hệ số kappa giữa hai người chấm (công thức 5-1). Số liệu lấy từ `rating_tools.py report`. |
| Bảng 5.5 (mục 5.2.2) | Điền các cột nhãn theo mức tin cậy `HIGH`/`MEDIUM`/`LOW`. Viết riêng một đoạn phân tích các câu `HIGH` nhưng chấm là sai (đã có chỗ giữ trong `[CHỜ SỐ LIỆU]`). |
| Mục 5.4 (đoạn `[TODO: Sau khi hoàn thành chấm tay…]`) | Thêm một đoạn về chất lượng câu trả lời V1 so với V2 và về các câu trả lời bám sát tài liệu (faithful). Nói rõ cả điểm bất lợi nếu có (ví dụ V1 sai ở câu mà V2 đúng). |
| Mục 6.1 (`drafts/06_ket_luan.md`, `[CHỜ SỐ LIỆU]`) | Một câu về tỉ lệ câu trả lời đúng của hệ thống so với LLM không có tài liệu. |
| ABSTRACT và Tóm tắt | Có thể thêm một mệnh đề về tỉ lệ đúng sau chấm tay, **nhưng mỗi phần phải còn vừa đúng một trang** (hiện đã gần kín; đã phải rút gọn ở Phiên 14). |

Chú ý khi chấm: hai người chấm **độc lập**, không biết phương án nào là V1 hay V2 (hai cột A/B đã được trộn ngẫu nhiên, bản đối chiếu nằm ở `eval/results/rating_mapping.json`; đừng mở tệp này trước khi chấm xong). Với câu ngoài kho, từ chối hợp lý được tính là `dung`. Tính kappa trên hai bản chấm độc lập **trước khi** thống nhất các ô khác nhau, nếu không kappa sẽ vô nghĩa.

### 2.2 Sau khi chạy E9 (Kong)

- Điền Bảng 5.12 (mục 5.3.4) theo kết quả hai tài khoản.
- Phát hiện 26 trong `KE_HOACH_VIET_BAO_CAO.md` mục 11: `kong.template.yml` không đặt `limit_by`, mặc định là `consumer`. Nếu hai tài khoản dùng **chung** bộ đếm, nêu ở Chương 6 (hạn chế) và hướng phát triển đặt `limit_by` rõ ràng; nếu mỗi tài khoản có bộ đếm riêng, sửa câu mô tả về Kong ở Chương 3 cho khớp.
- Nếu không chạy được Docker trước hạn, chuyển Bảng 5.12 thành "chưa kiểm chứng", ghi lý do, đừng để ô trống.

### 2.3 Thông tin chỉ nhóm biết

| Vị trí | Cần điền |
|---|---|
| Mục 1.1 | Vai trò của `ctsv.iuh.edu.vn` và `csm.iuh.edu.vn` (đơn vị nào quản lý, nội dung gì). |
| Mục 1.1 | Kết quả khảo sát sinh viên, nếu có. Không có thì **xóa dòng TODO**, đừng viết số giả. |
| Mục 1.2 (Bảng 1.1) | Kiểm tra lại các sản phẩm bên ngoài và ghi ngày kiểm tra. |
| Mục 2.2.3 | Giá trị `hnsw.ef_search` thực tế trên Supabase (xem mục 3 dưới đây). |
| Mục 2.4.3 | Cấu hình LLM dùng khi demo (biến môi trường `LLM_PROVIDER`, mô hình). Cấu hình khi đo ở Chương 5 đã ghi sẵn (Gemini). |
| Mục 4.2.7 | Hai chi tiết địa điểm trong ví dụ mẫu của prompt (Phòng Tài chính – Kế toán tầng trệt nhà E; Trung tâm Quản trị Hệ thống tầng 1 nhà A) có đúng không. |
| Mục 4.3.2 và tài liệu tham khảo | Nội dung đã tham khảo từ luyenty.com và ngày truy cập. Máy dùng để viết không truy cập được trang này nên **báo cáo chưa mô tả tính năng nào của nó**; thay câu chung chung bằng một câu cụ thể (ví dụ cách tổ chức sổ thẻ, kiểu ôn tập, giao diện). |
| Tài liệu tham khảo (Quy chế) | Số hiệu và năm ban hành Quy chế đào tạo theo hệ thống tín chỉ (đã được trích dẫn ở mục 1.1). |
| Phụ lục (Nhật ký) | Công việc từng tuần. Gợi ý nhớ lại: `eval/results/git_weekly.md` (191 commit theo tuần). Không chép nguyên commit message; viết lại theo việc đã làm. |

---

## 3. Việc kiểm tra kỹ thuật nhóm nên tự chạy (không làm được từ máy viết báo cáo)

1. `SELECT pg_get_functiondef('match_past_messages'::regproc);` trên Supabase, đối chiếu với mô tả ở mục 4.2.6. Trong `db/schema_complete.sql` hàm này chỉ được suy ra và có chú thích "GIẢ ĐỊNH CẦN XÁC NHẬN". Nếu khác, sửa mục 4.2.6 và Phụ lục E.
2. `SHOW hnsw.ef_search;` (và kiểm tra số hàng thực tế mà nhánh vector trả về). Mã nguồn không đặt tham số này nên mặc định là 40, trong khi RPC xin 50 ứng viên; nếu đúng thì nhánh vector có thể chỉ trả tối đa 40. Nêu đúng giá trị ở mục 2.2.3 và 4.2.5.
3. Đọc lại `eval/data/questions.jsonl` (45 câu, Phụ lục F), `guardrail_attacks.jsonl` (32), `guardrail_benign.jsonl` (60) và `cache_pairs.jsonl` (23 cặp). **Các bộ này do trợ lý soạn từ tài liệu trong kho**, chưa có người khác duyệt. Nếu GVHD hỏi về tính độc lập của bộ kiểm thử, câu trả lời trung thực là: bộ câu hỏi do nhóm soạn, cỡ nhỏ, nhãn nguồn do nhóm gán. Có thể thêm vài câu do người ngoài nhóm tự đặt để giảm thiên lệch.
4. Kiểm thử Auth `test_login_failure_is_logged_without_password` đang không đạt (1 trong 1.642). Lỗi ở kiểm thử (logger đặt `propagate = False` nên `caplog` không bắt được), không ở chức năng. Báo cáo đã ghi đúng 1.634/1.642 và nêu nguyên nhân. Nếu nhóm sửa kiểm thử, **phải chạy lại `eval/run_test_suites.py` và cập nhật mọi chỗ ghi 1.634** (ABSTRACT, Tóm tắt, mục 5.3.1, mục 6.1).

---

## 4. Quy trình hoàn thiện sau khi điền xong

1. Đóng Word nếu đang mở tệp đầu ra (nếu không, build báo `PermissionError`).
2. `cd B:\KhoaLuan\Report` rồi chạy `python -B -X utf8 build/render_figures.py` (khi có ảnh mới), `python -B -X utf8 build/renumber.py` (khi thêm/bớt hình bảng), rồi `python -B -X utf8 build/build_report.py --word --pdf`.
3. Kiểm tra dòng `Phần chính ... / 130` (vượt quá 10% là phải cắt), không có cảnh báo, và `ghi chú TODO: 0`.
4. Quét trang gần trắng: trang chỉ có hình thì bình thường; trang gần trống vì bảng bị đẩy sang trang sau thì rút bảng hoặc đổi chỗ đoạn văn (đã gặp ở Bảng 3.5, đã rút gọn).
5. **Tóm tắt** và **ABSTRACT** mỗi phần đúng một trang; ba trang "Nhận xét" mỗi trang một tờ.
6. Mở `.docx` trong Word, kiểm tra mục lục, danh mục hình, danh mục bảng (script đã cập nhật qua Word COM; nếu cần, Ctrl+A rồi F9). Chỉ sửa tay trong Word khi thật cần, vì lần build sau sẽ ghi đè; hãy sửa ở `drafts/`.
7. In thử vài trang (bìa, một trang có hình, một trang có bảng) để kiểm tra chữ trong hình đọc được và đúng lề đóng gáy.

---

## 5. Điểm cần chú ý khi bảo vệ (hội đồng có thể hỏi)

Các điểm yếu dưới đây đều **đã được ghi trung thực trong báo cáo**; nhóm nên nắm số liệu để trả lời.

| Chủ đề | Số liệu và vị trí trong báo cáo | Cách trả lời gợi ý |
|---|---|---|
| Truy xuất | E1 trên 35 câu: không xếp hạng lại Hit@1 60,0%, Hit@3 80,0%, MRR@5 0,687; có cross-encoder Hit@3 94,3%, MRR@5 0,762 (mục 5.2.1). Toàn pipeline Hit@1 77,1%, Hit@3 91,4% (mục 5.2.2). | Mẫu nhỏ nên nêu khoảng tin cậy; xếp hạng lại cải thiện rõ nhất ở Hit@3. |
| Nhánh toàn văn gần như không đóng góp | Chỉ 2/35 câu có kết quả từ FTS vì `websearch_to_tsquery` nối các từ bằng AND (mục 4.2.5, phát hiện 42). | Nhánh vector gánh phần lớn kết quả. Hướng khắc phục: dùng OR hoặc `plainto_tsquery` kèm xếp hạng. |
| Bộ lọc an toàn | Chặn 19/32 câu tấn công (59,4%), chặn nhầm 6/60 câu hợp lệ (10%) (mục 5.2.4). | Guardrail chỉ là một lớp biểu thức chính quy; lớp thứ hai là prompt và bộ định tuyến. Chưa phải biện pháp an ninh hoàn chỉnh. |
| Bộ nhớ đệm ngữ nghĩa | Mô phỏng: 9/15 cặp diễn đạt lại trúng, 0/8 cặp khác số bị trúng nhầm (4/8 nếu bỏ luật so khớp chữ số) (mục 5.2.3). Tham số `threshold=0.92` thực tế không có tác dụng (bị chặn bởi `min(threshold, 0.60)`); cache khóa theo truy vấn đầu tiên, không tự vô hiệu khi kho đổi (mục 4.2.4). | Thiết kế hai tầng có chủ ý (0,60 cosine rồi cross-encoder 0,80 và so khớp số); các hạn chế đã nêu. |
| Độ trễ | 37 lượt RAG với Gemini: trung vị 3.338 ms, phân vị 95 là 17.155 ms; TTFT trung vị 2.801 ms (mục 5.2.5). | Đuôi dài chủ yếu do mô hình sinh và lần gọi bộ định tuyến; số đo phụ thuộc đường truyền và Gemini tại thời điểm đo. |
| Từ chối câu ngoài kho | 10/10 câu ngoài kho bị từ chối (mục 5.2.2). | Mẫu nhỏ. Câu về "đồng phục của trường khác" nhận điểm 0,52 từ bộ xếp hạng lại (không bị ngưỡng 0,20 chặn) và chỉ bị chặn ở bộ định tuyến (phát hiện 43). |
| Thẻ `<thinking>` đóng sai | 1/37 lượt có thẻ đóng sai (`</doc_relevance>`); bộ lọc streaming có thể nuốt cả câu trả lời (phát hiện 44, mục 5.2.2). | Hạn chế của việc lọc theo trạng thái; hướng khắc phục: lọc theo thẻ đang mở. |
| Bảo mật phiên hội thoại | Một số endpoint phiên chat không kiểm tra chủ sở hữu (mục 4.2.9, 3.6, 6.2); token chỉ bị thu hồi ở Auth Service (phát hiện 22); Kong gộp giới hạn theo consumer (phát hiện 26). | Kiến trúc có JWT và Kong ở lớp ngoài; các lỗ hổng ở lớp service đã được liệt kê và đưa vào hướng phát triển. |
| Kiểm thử | 1.642 kiểm thử, 1.634 đạt, 1 không đạt (lỗi của kiểm thử), 7 bỏ qua (mục 5.3.1). Benchmark RAG trong CI chỉ kiểm thử công thức Hit/MRR trên dữ liệu mẫu, **không** đo truy xuất thật (phát hiện 40). | Đừng nói "đã đánh giá RAG bằng CI". Kết quả đánh giá thật là E1–E5 ở Chương 5. |
| Quy mô kho tri thức | 415 tài liệu, 1.092 đoạn cha, 3.181 đoạn con; ctsv 222, iuh 87, camnang 60, csm 35 (Bảng 4.2). | Kho phản ánh các nguồn đã nạp tại ngày 31/10/2026, không phải toàn bộ thông tin của trường. |
| Miền ngoài danh sách | `pdt.iuh.edu.vn` có 3 tài liệu dù không nằm trong `ALLOWED_DOMAINS` vì URL do quản trị viên nhập tay không qua bộ lọc tên miền (mục 4.1.1). | Đây là ngoại lệ của quy trình quản trị, không phải lỗi thu thập. |

### Những câu **không nên** nói khi bảo vệ

- Không nói hệ thống "chống tấn công toàn diện" hay "chống IDOR" cho chatbot (phiên hội thoại còn thiếu kiểm tra chủ sở hữu).
- Không nói "độ chính xác X%" khi chưa có kết quả chấm tay E2; chỉ nói Hit@K của truy xuất và tỉ lệ từ chối câu ngoài kho.
- Không dùng số liệu "quảng cáo" trong tài liệu cũ của dự án (100% thuật ngữ, 99,9%, >60%…): không có script đo đi kèm (phát hiện 9).
- Không mô tả OTP/quên mật khẩu, SM-2, số ứng viên thích ứng 30/50/70, `routers/cache.py` như tính năng đang chạy (phát hiện 3, 4, 5, 10).
- Không khẳng định hệ thống đã kiểm chứng trên hạ tầng triển khai thật khi `DEPLOY.md` ghi "chưa kiểm chứng" (mục 4.4.2).
- Số liệu Chương 5 gắn với kho ngày 31/10/2026 và mô hình Gemini lúc đo; nếu kho hoặc mô hình thay đổi thì phải đo lại bằng script trong `eval/`.

---

## 6. Nên cân nhắc nếu còn thời gian (không bắt buộc)

- **Thêm câu hỏi vào bộ đánh giá** do người ngoài nhóm đặt, để giảm thiên lệch (mục 3.3).
- **Đo lại E1 sau khi đổi FTS sang OR** (nếu nhóm sửa mã dự án): đây là cải tiến dễ đo nhất trong các phát hiện. Khi đó cập nhật mục 5.2.1 và 6.3.
- **Sửa kiểm thử Auth** (propagate) rồi cập nhật số ở mọi nơi (xem mục 3.4).
- **Số trang:** Chương 3 hơi vượt (23/22). Nếu GVHD yêu cầu cắt, ứng viên đầu tiên là mục 3.6 và 3.7.

---

## 7. Tệp liên quan

| Tệp | Nội dung |
|---|---|
| `KE_HOACH_V2.md`, `TIEN_DO.md` | Kế hoạch và tiến độ từng phiên. |
| `VIEC_NHOM_CAN_LAM.md` | Danh sách việc dạng checklist (ảnh, số liệu, thông tin). |
| `KE_HOACH_VIET_BAO_CAO.md` mục 11 | 45 điểm đối chiếu giữa tài liệu và mã nguồn (điểm 29–45 phát hiện khi viết Chương 4 và 5). |
| `eval/README.md` | Cách chạy lại mọi thí nghiệm; kết quả ở `eval/results/`. |
| `figures/FIGURES.md` | Danh mục hình, trạng thái, chú thích. |
| `build/report_config.json` | Thông tin bìa, danh sách phần dựng. |
