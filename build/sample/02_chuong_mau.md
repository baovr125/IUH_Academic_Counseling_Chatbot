# CHƯƠNG 2. MẪU BẢNG ĐẶC TẢ VÀ ĐÁNH SỐ LẠI THEO CHƯƠNG

Chương này kiểm tra việc số hình, bảng và công thức được đánh lại từ đầu ở mỗi chương, đồng thời thử mẫu bảng đặc tả use case.

## 2.1 Bảng đặc tả use case

Bảng 2.1 là mẫu bảng đặc tả use case theo bố cục đã duyệt. Luồng sự kiện chính được trình bày bằng bảng con hai cột ở Bảng 2.2.

Bảng 2.1. Đặc tả use case UC-xx (mẫu)

| Trường | Nội dung |
|---|---|
| **Use case** | UC-xx Tên use case |
| **Mục đích** | Mô tả ngắn mục đích |
| **Tác nhân** | Người dùng |
| **Điều kiện trước** | Người dùng đã đăng nhập |
| **Điều kiện sau** | Hệ thống lưu kết quả |
| **Luồng sự kiện phụ** | 3a. Dữ liệu không hợp lệ: hệ thống báo lỗi và quay lại bước 2. |

Bảng 2.2. Luồng sự kiện chính của UC-xx (mẫu)

| Tác nhân | Hệ thống |
|---|---|
| 1. Người dùng mở chức năng. | |
| | 2. Hệ thống hiển thị biểu mẫu. |
| 3. Người dùng nhập dữ liệu và gửi. | |
| | 4. Hệ thống kiểm tra và lưu dữ liệu. |

## 2.2 Hình và công thức của chương 2

Hình 2.1 dùng lại logo để kiểm tra số hình bắt đầu lại từ 1 ở chương mới.

![Hình 2.1. Hình thứ nhất của Chương 2](../../figures/iuh_logo_new.png){width=6cm}

Công thức (2-1) là độ đo Mean Reciprocal Rank:

$$ \mathrm{MRR}=\frac{1}{|Q|}\sum_{i=1}^{|Q|}\frac{1}{\mathrm{rank}_i} \tag{2-1} $$

trong đó: $Q$ là tập câu hỏi đánh giá; $\mathrm{rank}_i$ là vị trí của tài liệu đúng đầu tiên với câu hỏi thứ $i$.

## Tiểu kết chương {.unnumbered}

Chương 2 mẫu kết thúc tại đây.
