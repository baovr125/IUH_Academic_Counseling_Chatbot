# Việc nhóm cần làm để hoàn thiện báo cáo

Tệp này gom mọi việc cần người thật thực hiện (chụp ảnh, chạy hệ thống, điền thông tin). Phần viết đã xong đều để chỗ trống đánh dấu trong bản thảo bằng `[TODO: …]` hoặc `[CHỜ SỐ LIỆU: …]`. Cập nhật lần cuối: sau Phiên 14 (31/10/2026). Xem thêm `GHI_CHU_CUOI.md` (vị trí điền chi tiết, quy trình hoàn thiện, điểm cần nắm khi bảo vệ). Khi làm xong một mục, đánh dấu `[x]` ở đầu dòng.

## 1. Ảnh giao diện cần chụp (Phiên S)

Lưu đúng tên và đúng thư mục dưới đây (ghi đè ảnh giữ chỗ), rồi chạy `python -B -X utf8 build/render_figures.py` và `python -B -X utf8 build/build_report.py --word --pdf`. Khổ ngang khoảng 16:9 (ảnh giữ chỗ là 1220×685), chữ trên giao diện đọc được, không lộ email hoặc thông tin cá nhân.

- [ ] `figures/ch4/H4-08.png`: Trang Quản trị, mục nạp tri thức, khi đang nạp (thấy thanh tiến độ). Hình 4.3, mục 4.1.5.
- [ ] `figures/ch4/H4-24.png`: Chatbot trả lời một câu hỏi về quy chế hoặc học phí, hiện các huy hiệu nguồn trích dẫn và các nút câu hỏi gợi ý. Hình 4.11, mục 4.2.8.
- [ ] `figures/ch4/H4-33.png`: Trang Dịch thuật (Translation Studio) ở chế độ chuyên ngành, có kết quả. Hình 4.13, mục 4.3.1.
- [ ] `figures/ch4/H4-45.png`: Phiên ôn tập flashcard ở mặt sau thẻ, thấy bốn nút đánh giá. Hình 4.15, mục 4.3.2.

## 2. Số liệu và đánh giá cần người thật

Đã xong (Phiên 10b): Bảng 4.2, E1 (truy xuất), E3 (bộ nhớ đệm), E4 (bộ lọc), E5 (độ trễ), E6 (kiểm thử), thu câu trả lời V1 và V2. Còn lại:

- [ ] **Chấm tay E2** (Bảng 5.4 và 5.5): hai người mở riêng `eval/results/rating_r1.csv` và `rating_r2.csv` (Excel, UTF-8). Với mỗi câu có hai câu trả lời A và B (không biết phương án nào). Điền `label_A`, `label_B` là `dung`, `mot_phan` hoặc `sai` (xem mục 5.1.2 và đáp án tham chiếu trong cột `reference`) và `faithful_A`, `faithful_B` là 1 hoặc 0 (mọi khẳng định có trong tài liệu, chỉ cần với phương án có tài liệu). Với câu ngoài kho hoặc ngoài phạm vi, `dung` nghĩa là từ chối hợp lý. Xong thì chạy `python -B -X utf8 eval/rating_tools.py merge`, thống nhất các ô khác nhau trong `rating_final.csv` (cột `final_A`, `final_B`), rồi `rating_tools.py report`; điền kết quả vào Bảng 5.4 và 5.5 và viết thêm một đoạn ở mục 5.4.
- [ ] **E9** giới hạn tần suất của Kong với hai tài khoản (mục 5.3.4, Bảng 5.12); cần Docker Compose.
- [ ] **Đọc lại bộ câu hỏi và nhãn** (`eval/data/questions.jsonl`, Phụ lục F) do tôi soạn từ tài liệu trong kho: kiểm tra đáp án tham chiếu và nhãn nguồn, thêm câu hỏi nếu muốn bộ lớn hơn (script chạy lại được bằng `eval/README.md`).
- [ ] **Kiểm tra `match_past_messages`** (mục 4.2.6): `SELECT pg_get_functiondef('match_past_messages'::regproc);` trên Supabase, đối chiếu với mô tả.
- [ ] **Kiểm tra `hnsw.ef_search`** (mục 2.2.3).
- [ ] Bộ lọc an toàn (mục 5.2.4): đọc lại hai tệp `guardrail_attacks.jsonl`, `guardrail_benign.jsonl` do tôi soạn.

## 3. Thông tin cần điền hoặc xác nhận

- [ ] Vai trò của hai trang `ctsv.iuh.edu.vn` và `csm.iuh.edu.vn` (mục 1.1).
- [ ] Số liệu khảo sát sinh viên, nếu có (mục 1.1).
- [ ] Kiểm tra các ô đánh giá sản phẩm bên ngoài ở Bảng 1.1 và ghi ngày kiểm tra (mục 1.2).
- [ ] Số hiệu, năm ban hành của Quy chế đào tạo (tài liệu tham khảo [3]).
- [x] Ngày truy cập tài liệu tham khảo: đã ghi 31/10/2026 sau khi kiểm tra liên kết (Phiên 12). Còn thiếu số hiệu Quy chế (dòng trên).
- [ ] Cấu hình LLM dùng khi chạy demo (mục 2.4.3). Cấu hình khi đo ở Chương 5 đã ghi (Gemini, kho ngày 31/10/2026).
- [ ] Hai chi tiết địa điểm trong ví dụ mẫu của prompt: "Phòng Tài chính – Kế toán tầng trệt nhà E", "Trung tâm Quản trị Hệ thống tầng 1 nhà A" (`prompts/prompt_templates.py`, mục 4.2.7). Nếu sai, sửa ví dụ mẫu hoặc báo để ghi vào báo cáo.
- [ ] **Bìa và phụ bìa** (sửa `build/report_config.json`): `students` (họ tên hai sinh viên), mục `cover`: `title_vi`, `title_en` (tên đề tài chính thức; hiện là tên tạm), `major_vi`, `major_en` (ngành), `supervisor_vi`, `supervisor_en` (học vị và họ tên GVHD), `date_vi` (tháng nộp). Chân trang tự lấy họ tên sinh viên. Đồng thời điền tên GVHD trong lời cảm ơn (`drafts/00_phan_dau.md`).
- [ ] **Nhật ký làm việc** (`drafts/92_nhat_ky.md`): điền thời gian, công việc từng tuần và xin chữ ký GVHD; gợi ý trong `eval/results/git_weekly.md`.
- [ ] **Luyenty.com** (mục 4.3.2 và tài liệu tham khảo [4]): ghi cụ thể đã tham khảo gì (tổ chức sổ thẻ, kiểu ôn, giao diện…) và ngày truy cập; tôi không truy cập được trang từ máy hiện tại.
- [ ] Sau Chương 5: điền một câu kết quả chính vào ABSTRACT và Tóm tắt (`drafts/00_phan_dau.md`, tìm `[CHỜ SỐ LIỆU`) và một đoạn tóm tắt ở mục 6.1 (`drafts/06_ket_luan.md`).
- [ ] Đọc lại lời cảm ơn và chỉnh theo ý nhóm (dùng "chúng em"; nếu muốn cảm ơn thêm người hoặc đơn vị nào).

## 4. Phát hiện cần nhóm biết

- Một kiểm thử của Auth Service không đạt trên máy bạn: `test_login_failure_is_logged_without_password`. Lỗi nằm ở kiểm thử (logger đặt `propagate = False` nên `caplog` không bắt được), không ở chức năng. Có thể sửa kiểm thử, nhưng đó là sửa mã dự án nên tôi không tự làm.
- Các điểm yếu của mã nguồn đã ghi trong báo cáo và sẽ tổng hợp ở Chương 6: xem `KE_HOACH_VIET_BAO_CAO.md` mục 11, điểm 18 đến 41.
