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

### 🌟 Tổng hợp nhánh `chatbot` (từ khi tách khỏi `main`)
**1. Hệ thống RAG & Backend**
- **Tái Cấu Trúc**: Áp dụng Clean Architecture (routers, schemas, services, utils).
- **Bảo Mật & Guardrails**: Tích hợp Context Sandbox (chống Indirect Prompt Injection), thêm Input Validation, và chặn Jailbreak prompt.
- **Hiệu Năng & Ổn Định**: Sửa lỗi OOM của Cross-Encoder (`bge-reranker-v2-m3`), tối ưu streaming LLM (giảm độ trễ), sửa lỗi API 404.
- **Giám Sát & Logging**: Đo lường độ trễ (latency) và token usage; triển khai Structured Logging (`python-json-logger`), UUID tracking; cấu hình API Rate Limiting (`slowapi`) và CORS chặt chẽ.

**2. Giao diện (Frontend) & UI/UX**
- **Cải tiến Cấu trúc**: Đổi tên thư mục `frontend1` thành `frontend`.
- **Quản lý Phiên (Sessions)**: Sửa lỗi khóa ngoại `user_id` qua tự động đăng nhập (dev user); cập nhật logic tạo tiêu đề chat; sửa lỗi tự xóa lịch sử.
- **Tối ưu N+1 & Infinite Scroll (Phase 4.4)**: Áp dụng Lazy Loading (chỉ tải metadata ban đầu), thêm phân trang và tải vô hạn cho danh sách Session ("Load More") và Message (cuộn lên trên).
- **Tương tác người dùng**: Thêm UI gợi ý câu hỏi chính xác (chặn AI sinh text dẫn dắt sai), tích hợp User Feedback UI (Like/Dislike/Comment) và trang Analytics Dashboard.

**3. Kiểm Thử & Tài Liệu**
- Viết test cases và tích hợp Automation Testing cho cả frontend và backend.
- Tạo mới và liên tục cập nhật lộ trình cải tiến (RAG Roadmap) cũng như `PROJECT_LOG.md`.

---

## 🧪 Lệnh Hữu Ích
- **Chạy Frontend**: `cd frontend && pnpm run dev`
- **Chạy Backend**: `cd backend && uvicorn main:app --reload`
