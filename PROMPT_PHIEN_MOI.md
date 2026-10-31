Tôi là sinh viên Khoa CNTT, Trường ĐH Công nghiệp TP.HCM (IUH). Nhóm tôi có 2 người và đang hoàn thiện báo cáo khóa luận tốt nghiệp. Hãy trả lời bằng tiếng Việt có dấu đầy đủ; trong báo cáo xưng "nhóm" / "chúng tôi".

## Bối cảnh
- **Đề tài:** IUH_Academic_Counseling_Chatbot (IUH EduBot): hệ thống hỗ trợ sinh viên IUH theo kiến trúc microservices. Trọng tâm báo cáo là **Academic Chatbot Service** (pipeline nạp tri thức và Advanced RAG). Dịch thuật, Flashcard (FSRS), Auth, Kong, Frontend chỉ nói sơ qua; Document Translation Service chỉ một đoạn.
- **Mã nguồn:** `B:\KhoaLuan\IUH_Academic_Counseling_Chatbot` (không được sửa).
- **Thư mục báo cáo:** `B:\KhoaLuan\Report`. Mẫu của Khoa (`Mau bao cao KLTN.docx.pdf`, `04.-MAU-KHOA-LUAN-TOT-NGHIEP-2021.docx`) và báo cáo khóa trước (`Mau bao cao KLTN_QuyLong.pdf`) chỉ để tham khảo, không ghi đè.

## Tình trạng hiện tại (31/10/2026)
Mọi phiên viết (R1–R3, 7–13, 10b, 14) **đã xong**. Báo cáo dài 181 trang, **phần chính (Chương 1 → Tài liệu tham khảo) 125/130 trang** (ngân sách: Ch1 8, Ch2 24, Ch3 22 (đang 23), Ch4 42, Ch5 18, Ch6 4, TLTK 6). Build không còn cảnh báo. Còn 12 ghi chú `[TODO]` và 4 `[CHỜ SỐ LIỆU]` trong `drafts/`, đều cần thông tin hoặc số liệu của nhóm. Việc còn lại chủ yếu là **nhóm điền thông tin, rồi tôi (Claude) build lại và rà soát**.

## Đọc trước khi làm bất cứ việc gì
1. `Report/GHI_CHU_CUOI.md`: vị trí cần điền sau khi có số liệu, quy trình hoàn thiện, điểm cần nắm khi bảo vệ.
2. `Report/VIEC_NHOM_CAN_LAM.md`: checklist việc của nhóm.
3. `Report/TIEN_DO.md` (cuối tệp là Phiên 13 và 14) và `Report/KE_HOACH_V2.md` (dàn ý, ngân sách trang, danh sách hình).
4. `Report/KE_HOACH_VIET_BAO_CAO.md` khi cần quy định định dạng, phong cách hình, quy tắc tài liệu tham khảo và **mục 11: 45 điểm tài liệu lệch với mã nguồn**.
5. `Report/eval/README.md` khi cần chạy lại thí nghiệm.

## Quy tắc làm việc (bắt buộc)
- Mọi mô tả kỹ thuật phải **khớp mã nguồn**. Không dùng số liệu không có script đo đi kèm. Không bịa số liệu, tên người, số hiệu văn bản.
- Làm **từng phiên**, tôi duyệt rồi mới làm tiếp; xong phiên thì cập nhật `TIEN_DO.md`.
- Không ghi đè file mẫu, không sửa mã nguồn dự án. Không chạy Docker (tôi sẽ tự chạy khi cần E9).
- Số liệu Chương 5 phải do script trong `Report/eval/` sinh ra; script chỉ đọc, không ghi CSDL.
- Nhóm 2 sinh viên; chỗ chưa biết thông tin thì để `[TODO: …]`, không đoán.

## Cách dựng báo cáo
Bản thảo Markdown ở `Report/drafts/` (00_bia, 00_phan_dau, 01…06, 90_tai_lieu_tham_khao, 91_phu_luc, 92_nhat_ky) → pandoc + `build/filters.lua` → python-docx → Word COM (`word_update.ps1`) → PDF.
```powershell
cd B:\KhoaLuan\Report
python -B -X utf8 build/render_figures.py [ID...]      # vẽ hình mới/đổi (PlantUML, SVG, matplotlib); danh mục figures/FIGURES.md
python -B -X utf8 build/renumber.py                    # sau khi thêm/bớt/chuyển hình, bảng, công thức
python -B -X utf8 build/build_report.py --word --pdf   # in ngân sách trang; "VƯỢT" nếu quá 10%
```
- Thông tin bìa, danh sách phần dựng: `build/report_config.json` (cover, front, main, appendix; mục `students`, `cover`).
- Nếu build báo `PermissionError` ở docx: Word đang mở tệp, nhờ tôi đóng.
- Sửa ở `drafts/`, không sửa tay trong Word (lần build sau ghi đè). Chú thích hình trong bản thảo phải khớp `figures/FIGURES.md`.
- Tóm tắt, ABSTRACT mỗi phần phải đúng một trang; ba trang "Nhận xét" mỗi trang một tờ.

## Số liệu thật đã có (script ở `Report/eval/`, kho tri thức ngày 31/10/2026, LLM Gemini)
- Kho: 415 tài liệu, 1.092 đoạn cha, 3.181 đoạn con.
- **E1 truy xuất (35 câu):** không xếp hạng lại Hit@1 60,0%, Hit@3 80,0%, MRR@5 0,687; có cross-encoder Hit@3 94,3%, MRR@5 0,762. Toàn pipeline Hit@1 77,1%, Hit@3 91,4%. 10/10 câu ngoài kho bị từ chối.
- **E3 cache (mô phỏng):** 9/15 cặp diễn đạt lại trúng, 0/8 trúng nhầm (4/8 nếu bỏ luật so khớp số).
- **E4 guardrail:** chặn 19/32 câu tấn công (59,4%), chặn nhầm 6/60 câu hợp lệ (10%).
- **E5 độ trễ (37 lượt RAG):** tổng trung vị 3.338 ms, p95 17.155 ms, TTFT trung vị 2.801 ms.
- **E6 kiểm thử:** 1.642, đạt 1.634, 1 không đạt (kiểm thử Auth `test_login_failure_is_logged_without_password`, lỗi do `propagate = False`, không phải lỗi chức năng), 7 bỏ qua.
- E7, E8 trích từ báo cáo sẵn có của repo. **E2 (chấm tay) và E9 (Kong) chưa có** nên Bảng 5.4, 5.5, 5.12 còn trống.
- Các phát hiện quan trọng về mã nguồn (đã ghi trong báo cáo): nhánh toàn văn dùng `websearch_to_tsquery` (AND) nên chỉ 2/35 câu có kết quả FTS; ngưỡng cache `threshold=0.92` không có tác dụng; endpoint phiên chat thiếu kiểm tra chủ sở hữu; `hnsw.ef_search` mặc định 40; 1/37 lượt có thẻ `</doc_relevance>` đóng sai.

## Việc nhóm đang/sẽ làm (tôi sẽ báo khi xong để bạn tích hợp)
Chi tiết ở `VIEC_NHOM_CAN_LAM.md`: thông tin bìa (họ tên 2 sinh viên, ngành, GVHD, tên đề tài chính thức, ngày nộp; tên đề tài hiện là tên tạm), Lời cảm ơn (tên GVHD), nhật ký làm việc, chấm tay E2 (`eval/results/rating_r1.csv`, `rating_r2.csv`, rồi `rating_tools.py merge` và `report`), E9, 4 ảnh giao diện (`figures/ch4/H4-08.png`, `H4-24.png`, `H4-33.png`, `H4-45.png`), mô tả phần tham khảo từ luyenty.com, số hiệu Quy chế đào tạo, vai trò ctsv/csm, kiểm tra `match_past_messages` và `hnsw.ef_search` trên Supabase.

## Việc tiếp theo
Hỏi tôi hiện đã điền được những mục nào, rồi:
1. Tích hợp thông tin/số liệu vào đúng vị trí (xem bảng ở mục 2 của `GHI_CHU_CUOI.md`), cập nhật các câu kết quả ở ABSTRACT, Tóm tắt, mục 5.4, mục 6.1.
2. Nếu số kiểm thử hoặc số liệu nào đổi thì sửa **mọi nơi** có số đó.
3. Build lại, kiểm tra ngân sách trang, trang gần trống, cảnh báo, `ghi chú TODO`, rồi báo cáo kết quả và chờ tôi duyệt.
