# CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

## 6.1 Kết quả đạt được

Đề tài đã xây dựng một hệ thống web theo kiến trúc microservices, trong đó chatbot tư vấn học vụ dựa trên RAG trả lời câu hỏi của sinh viên IUH từ kho tri thức được thu thập từ các website và văn bản của trường, có trích dẫn nguồn và trả lời theo luồng. Bảng 6.1 đối chiếu từng mục tiêu cụ thể ở mục 1.3.2 với kết quả.

Bảng 6.1. Đối chiếu mục tiêu và kết quả

| Mục tiêu | Mức đạt | Căn cứ |
|----------------------------------------------|------------------|--------------------------------------------|
| Pipeline kho tri thức | Đạt | Mục 4.1; Bảng 4.2: 415 tài liệu, 3 181 đoạn con |
| Trả lời có trích dẫn, dạng luồng | Đạt | Mục 4.2.1, 4.2.8; trích dẫn là các nguồn đã đưa vào ngữ cảnh |
| Kỹ thuật RAG nâng cao | Đã cài đặt; xếp hạng lại cải thiện Hit@3 từ 80,0% lên 94,3% | Mục 4.2.3 đến 4.2.6, 5.2.1, 5.2.3 |
| Từ chối câu ngoài phạm vi, chặn chèn lệnh | Đạt một phần | Mục 5.2.4: chặn 19/32 câu tấn công, chặn nhầm 6/60 câu hợp lệ |
| Đánh giá thực nghiệm chatbot | Đạt, còn chờ chấm tay chất lượng câu trả lời | Mục 5.2 |
| Dịch 10 ngôn ngữ, 6 chuyên ngành | Đạt | Mục 4.3.1, 5.3.3 |
| Flashcard lập lịch FSRS, sinh từ vựng bằng AI | Đạt | Mục 4.3.2, 5.3.2 |
| Xác thực JWT qua cổng API có giới hạn tần suất | Đạt, còn hạn chế | Mục 3.6, 4.3.3 |
| Đóng gói Docker Compose, kiểm thử tự động | Đạt | Mục 4.4.2; 1 634 trên 1 642 kiểm thử đạt (Bảng 5.9) |

Về kết quả định lượng đã đo được: bộ kiểm thử tự động của năm service gồm 1 642 kiểm thử, trong đó 1 634 đạt, 1 không đạt do lỗi của kiểm thử và 7 bị bỏ qua; pipeline sinh từ vựng ba bước cho 100% thẻ đúng lược đồ trên 20 chủ đề (Bảng 5.10); bộ nhận diện ngôn ngữ đạt độ chính xác 97,8% trên 2 000 câu của tập Tatoeba (Bảng 5.11).

Với chatbot, trên 35 câu hỏi có đáp án, tài liệu đúng nằm trong 3 hạng đầu ở 94,3% (cấu hình đầy đủ, nguyên văn câu hỏi) và 91,4% (qua bộ định tuyến); bộ nhớ đệm không trúng nhầm cặp câu khác con số nào nhưng chỉ trúng 60% cặp diễn đạt lại; một lượt hỏi đáp có trung vị 3,3 giây và p95 17,2 giây.

> [CHỜ SỐ LIỆU: Thêm tỉ lệ câu trả lời đúng của hệ thống so với LLM không có tài liệu sau khi chấm tay (mục 5.2.2).]

## 6.2 Hạn chế

Các hạn chế dưới đây được phát hiện khi đối chiếu với mã nguồn và qua các phép đo ở Chương 5.

**Chatbot học vụ**
- **Bộ lọc an toàn:** lớp biểu thức chính quy chặn nhầm các câu hợp lệ có từ như "quên hướng dẫn" hay "cập nhật hệ thống" và bỏ lọt các cách diễn đạt khác mẫu hoặc ngụy trang (Bảng 5.7). Lớp thứ hai dựa vào LLM chưa được đo.
- **Bộ nhớ đệm ngữ nghĩa:** câu trả lời cho câu hỏi nhiều ý được lưu dưới khóa là truy vấn đầu tiên; bộ nhớ đệm không tự xóa sau khi nạp lại kho tri thức; tham số ngưỡng 0,92 trong mã không có tác dụng. Chuỗi thông báo lỗi của lớp nhà cung cấp LLM có thể lọt qua cổng chất lượng và bị lưu.
- **Truy xuất và ngữ cảnh:** nhánh toàn văn nối các từ truy vấn bằng phép AND nên chỉ có kết quả với 2 trong 35 câu hỏi đo được (mục 5.2.1), khiến tìm kiếm lai chưa hơn tìm kiếm vector; hàm chọn số ứng viên thích ứng không được gọi; ngày cập nhật không đến được prompt vì metadata thiếu, nên luật xử lý mâu thuẫn theo thời gian chưa dùng được; chưa kiểm tra giá trị `hnsw.ef_search` của cơ sở dữ liệu; Self-RAG mới ở mức prompt, chưa kích hoạt truy xuất lại.
- **Trích dẫn:** danh sách trích dẫn là các đoạn đã đưa vào ngữ cảnh chứ không phải các đoạn mô hình thực sự dùng; đoạn trích lấy từ đầu đoạn cha nên có thể chỉ là tiêu đề.
- **Prompt:** luật niên khóa ghi cứng; một số ví dụ mẫu nêu chi tiết chưa đối chiếu với tài liệu của trường; bộ định tuyến gán loại câu hỏi chưa ổn định.
- **Độ trễ:** hai lời gọi LLM tuần tự (bộ định tuyến và sinh) chiếm phần lớn thời gian, và bộ định tuyến luôn chạy trước bộ nhớ đệm.
- **Phiên hội thoại:** các endpoint đọc, đổi tên, xóa phiên không kiểm tra chủ sở hữu; yêu cầu hỏi đáp với mã phiên đã có ghi đè chủ phiên; danh sách phiên của người đăng nhập gồm cả phiên không có chủ; mã phiên do service sinh chỉ có 32 bit ngẫu nhiên.

**Pipeline tri thức:** trạng thái tiến trình nằm trong bộ nhớ nên chỉ chạy được một lần nạp mỗi lúc và mất khi khởi động lại; mỗi lần nạp qua API phân đoạn lại cả thư mục tạm; crawler tắt kiểm tra chứng chỉ SSL; ảnh nhúng trong trang web không được OCR; tên mục bị lặp hai lần trong văn bản sinh vector; phần chồng lấn của đoạn con bắt đầu giữa câu.

**Phân hệ hỗ trợ và bảo mật**
- Thu hồi token chỉ có hiệu lực tại Auth Service; các service khác chấp nhận token cũ đến khi hết hạn.
- Giới hạn tần suất của Kong có thể đang dùng chung giữa các người dùng vì không đặt `limit_by` (cần kiểm chứng ở mục 5.3.4); bộ đếm đăng nhập sai nằm trong bộ nhớ tiến trình.
- Sự kiện RabbitMQ không được thử lại; định dạng lỗi API chưa thống nhất giữa các service.
- Chưa xác minh email và khôi phục mật khẩu; chưa có Content-Security-Policy. Giao diện còn khối dữ liệu mẫu, lịch sử dịch chỉ lưu trong trình duyệt và nút thích hoặc không thích gọi route chưa tồn tại; dịch tài liệu chưa triển khai.

**Đánh giá:** các bộ câu hỏi tự soạn nên có thể thiên lệch; kho tri thức lấy tại một thời điểm; phần lớn kiểm thử dùng đối tượng giả; việc đo chạy trên một máy cá nhân.

## 6.3 Hướng phát triển

Hướng phát triển trước hết nhắm vào chatbot, sau đó là các phân hệ còn lại.

1. **Khắc phục các lỗi đã biết của chatbot:** kiểm tra chủ sở hữu ở mọi endpoint phiên và sinh mã phiên đủ ngẫu nhiên; lưu bộ nhớ đệm theo toàn bộ tập truy vấn con, tự xóa khi nạp lại tri thức và không lưu câu trả lời lỗi; sửa các mẫu của bộ lọc và bổ sung lớp phân loại bằng mô hình để giảm chặn nhầm.
2. **Nâng chất lượng truy xuất và trích dẫn:** nới phép AND của nhánh toàn văn (ví dụ yêu cầu khớp một phần số từ khóa); hiệu chỉnh `hnsw.ef_search` và số ứng viên; đánh dấu các đoạn được dùng thật khi sinh câu trả lời và trích đoạn con khớp nhất; ghi ngày ban hành và ngày cập nhật vào metadata để xử lý mâu thuẫn giữa các văn bản; OCR ảnh nhúng và trích xuất bảng tốt hơn.
3. **Giảm độ trễ:** dùng mô hình nhỏ hơn cho bộ định tuyến, chạy truy xuất song song với một số bước khác, tra bộ nhớ đệm bằng câu hỏi gốc trước khi gọi bộ định tuyến, rút ngắn khối suy luận.
4. **Đánh giá liên tục:** đưa bộ câu hỏi chuẩn vào quy trình tích hợp liên tục để phát hiện hồi quy chất lượng; nối chức năng thích hoặc không thích với một route lưu phản hồi; xem xét dữ liệu phản hồi để mở rộng bộ câu hỏi.
5. **Hạ tầng và bảo mật:** chuyển bộ đếm đăng nhập sai và trạng thái nạp tri thức sang Redis; kiểm tra phiên bản token ở mọi service; đặt `limit_by` theo người dùng; thêm hàng đợi lỗi cho RabbitMQ; thêm Content-Security-Policy và cookie `HttpOnly`.
6. **Các phân hệ khác:** đưa chức năng dịch tài liệu vào vận hành, thay dữ liệu mẫu của Dashboard bằng dữ liệu thật, thêm xác minh email và khôi phục mật khẩu.
