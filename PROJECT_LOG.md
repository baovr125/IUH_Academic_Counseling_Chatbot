# 📝 Nhật Ký Dự Án (PROJECT LOG)

**Tên dự án**: IUH Academic Counseling Chatbot & Language Portal  
**Cập nhật lần cuối**: 06/08/2026  

---

## 🎯 Tổng Quan
Hệ thống Trợ lý Học vụ Thông minh IUH tích hợp RAG 4 Giai đoạn, đồng bộ dữ liệu PostgreSQL (Supabase) và cổng học tập đa ngôn ngữ.

---

## 🚀 Tính Năng Nổi Bật
- **RAG & ML**: Rút trích pgvector, rerank `bge-reranker-v2-m3` tối ưu OOM, nạp trước model.
- **Tối ưu LLM**: Tắt thinking budget Gemini 2.5 (TTFT 0.63s), auto failover.
- **Quản lý phiên (Supabase)**: Phân vùng `user_id`, UUID v5, tự động đồng bộ sidebar, bảo toàn lịch sử.
- **Giao diện (UI/UX)**: Gợi ý câu hỏi tự động, soft-delete, validation chống spam.

---

## 📅 Lịch Sử Cập Nhật

### Mới Nhất (06/08/2026)
- Hoàn thành Frontend Infinite Scroll (Phase 4.4): Thêm phân trang và tải vô hạn cho cả danh sách Session (ở Sidebar) và danh sách Message (khi cuộn lên trên) dựa trên hệ thống API mới.
- Hoàn thành (N+1 Session Loading Optimization): Thay đổi API `GET /api/chat/sessions` để áp dụng Lazy Loading cho tin nhắn (chỉ trả về metadata của hội thoại). Đã thêm endpoint mới `GET /api/chat/sessions/{session_id}/messages` để tải chi tiết tin nhắn của một phiên.
- Hoàn thiện xử lý ngoại lệ toàn hệ thống: Thay thế toàn bộ các khối `except Exception:` trong thư mục `backend/app/` bằng `logger.exception()` từ `app.utils.logger` để ghi log chi tiết kèm theo stack trace.
- Hoàn thành (Structured Logging & Error Monitoring): Triển khai `python-json-logger` để log dạng JSON, thêm UUID middleware theo dõi `request_id`, và bắt lỗi toàn cục bằng `logger.exception()` kèm phản hồi HTTP 500 sạch sẽ.
- Hoàn thành Giai đoạn 4.2 (Backend Rate Limiting): Triển khai giới hạn tần suất API bằng `slowapi` (`20/minute`) cho các endpoint chat, xử lý ngoại lệ `RateLimitExceeded`, và siết chặt cấu hình CORS origin.
- Đổi tên thư mục `frontend1` thành `frontend`.
- Sửa lỗi mất lịch sử sidebar bằng cách tạo tài khoản dev hợp lệ trong CSDL, khắc phục lỗi khoá ngoại `user_id`.
- Sửa lỗi UI hiển thị sai text "Gợi ý câu hỏi" trên mọi tin nhắn bằng cách chặn AI sinh text dẫn dắt ngoài thẻ `[follow_up]`.

### Các Bản Cập Nhật Trước
- **Hiệu Năng & Ổn Định**: Sửa lỗi OOM của Cross-Encoder, tối ưu streaming Gemini, failover tự động.
- **Bảo Mật & Guardrails**: Chống Jailbreak, ẩn System Prompt, lọc truy vấn ngoài lề (Stage 0).
- **Tái Cấu Trúc**: Phân chia Clean Architecture (routers, schemas, services, utils).
- **Tính năng RAG**: Mở rộng ngữ cảnh (Neighbor Chunk), giới hạn ký tự, API đánh giá phản hồi.

---

## 🧪 Lệnh Hữu Ích
- **Chạy Frontend**: `cd frontend && pnpm run dev`
- **Chạy Backend**: `cd backend && uvicorn main:app --reload`
