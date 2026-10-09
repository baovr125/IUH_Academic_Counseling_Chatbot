# 📊 Realtime Translation Service - Tự Đánh Giá (Manual Review Report)
Thời gian chạy: 2026-09-29 17:05:15

## 1. Tổng Quan (Executive Summary)
- Tổng số Testcase: 10
- Tỷ lệ bảo toàn cấu trúc HTML: 80.0%

## 2. Hiệu Năng Tốc Độ (Latency Benchmarks)
| Luồng Dịch | P50 (ms) | P90 (ms) | P99 (ms) | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| **NLLB (Default)** | 66.37ms | 464.89ms | 464.89ms | Dịch tốc độ cao |
| **Gemini Bypass (IT/Econ)** | 642.97ms | 1390.6ms| 1390.6ms | Ép từ điển chuyên ngành |

## 3. Lỗi Kỹ Thuật (HTML/Timeout Errors)
- **ID:** `html_broken`
  - **Lỗi:** Cấu trúc HTML Bị Hỏng
  - **Câu gốc:** `<div>Unclosed div <p>Paragraph with missing closing tag`
  - **Bản dịch:** `<div>Không đóng div<p>Phần có thẻ đóng cửa bị thiếu</p></div>`

## 4. Đối Chiếu Kết Quả Dịch Thuật (Translation Review)
| Thể Loại | Tốc độ | Cấu trúc HTML | Câu Gốc (Original Text) | Bản Dịch Thực Tế (Actual Translation) |
| :--- | :--- | :--- | :--- | :--- |
| text | 464.89ms | ✅ Giữ nguyên | `This is a simple sentence to test the latency of the translation model.` | `Đây là một câu đơn giản để kiểm tra độ trễ của mô hình dịch.` |
| text | 179.8ms | ✅ Giữ nguyên | `Welcome to the Academic Counseling Chatbot. How can I help you today?` | `Chào mừng bạn đến với Chatbot tư vấn học thuật. Tôi có thể giúp bạn như thế nào?` |
| IT | 1390.6ms | ✅ Giữ nguyên | `The prerequisite for this new course is Data Structures.` | `Điều kiện tiên quyết cho khóa học mới này là cấu trúc dữ liệu.` |
| IT | 336.01ms | ✅ Giữ nguyên | `We need to optimize the database query to reduce latency.` | `Chúng ta cần tối ưu hóa truy vấn cơ sở dữ liệu để giảm độ trễ.` |
| Kinh tế | 642.97ms | ✅ Giữ nguyên | `The inflation rate has a direct impact on the stock market.` | `Tỷ lệ lạm phát có tác động trực tiếp đến thị trường chứng khoán.` |
| html | 57.08ms | ✅ Giữ nguyên | `<p>Hello <strong>world</strong>!</p>` | `<p>Xin chào.<strong>thế giới</strong>!</p>` |
| html | 49.72ms | ✅ Giữ nguyên | `<a href="/courses/123" class="course-link" data-id="123">View Course</a>` | `<a class="course-link" data-id="123" href="/courses/123">Xem khóa học</a>` |
| html | 66.37ms | ✅ Giữ nguyên | `<div class="wrapper">
  <h1>Course Syllabus</h1>
  <p>Please read the <a href="/syllabus">syllabus</a> carefully.</p>
  <script>alert('test');</script>
  <style>.wrapper { color: red; }</style>
</div>` | `<div class="wrapper">
<h1>Khóa học Syllabus</h1>
<p>Vui lòng đọc<a href="/syllabus">chương trình học</a>cẩn thận.</p>
<script>alert('test');</script>
<style>.wrapper { color: red; }</style>
</div>` |
| html | 65.42ms | ❌ Rách tag | `<div>Unclosed div <p>Paragraph with missing closing tag` | `<div>Không đóng div<p>Phần có thẻ đóng cửa bị thiếu</p></div>` |
| IT | 277.8ms | ✅ Giữ nguyên | `<div class="alert">Warning: The <strong>prerequisite</strong> for this module is <a href="/ds">Data Structures</a>.</div>` | `<div class="alert">Cảnh báo:<strong>điều kiện tiên quyết</strong>cho mô-đun này là<a href="/ds">Các cấu trúc dữ liệu</a>.</div>` |
