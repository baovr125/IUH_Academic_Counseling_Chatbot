# 📝 Nhật Ký Dự Án (PROJECT LOG)

**Tên dự án**: IUH Academic Counseling Chatbot & Language Portal  
**Thư mục gốc**: `/home/anhhao/workSpace/IUH_Academic_Counseling_Chatbot`  
**Cập nhật lần cuối**: 04/08/2026  

---

## 🎯 Tổng Quan Hệ Thống

Hệ thống Trợ lý Học vụ Thông minh IUH tích hợp RAG 4 Giai đoạn (HyDE/Rewriter -> Vector & Full-Text Search -> Cross-Encoder Reranker -> Gemini 2.5 Flash), đồng bộ dữ liệu người dùng qua Supabase PostgreSQL và cung cấp cổng học tập đa ngôn ngữ (Flashcard, Translation Studio).

---

## 🚀 Các Tính Năng Kỹ Thuật & Tối Ưu Chính

### 1. Kiến Trúc RAG & Tối Ưu Hiệu Năng
- **RAG 4 Giai đoạn**: Rút 35 ứng viên từ CSDL vector pgvector (HNSW) & FTS qua RPC `match_chunks_hybrid_rrf`, dùng `bge-reranker-v2-m3` chọn top 5 đoạn trích dẫn chuẩn nhất.
- **Tối ưu Tốc độ Reranker**: Đưa `batch_size=16` vào `CrossEncoder.predict()`, giảm thời gian rerank từ **32.2 giây xuống còn 1.74 giây**.
- **Nạp Trước Models (Preload)**: Nạp sẵn `SentenceTransformer` & `CrossEncoder` vào RAM ngay khi server FastAPI khởi động, loại bỏ trễ Lazy Loading.
- **Tối ưu Stream Real-time**: Tắt thinking budget (`thinking_budget=0`) đối với Gemini 2.5, giảm thời gian phản hồi token đầu tiên (TTFT) từ **6.25 giây xuống 0.63 giây**.
- **Failover Tự Động 503**: Rút thử token đầu tiên trong `try...except` để phát hiện nhanh lỗi `503 UNAVAILABLE` và tự động chuyển đổi model dự phòng trong <0.1s.

### 2. Quản Lý Lịch Sử Chat & Phân Vùng Người Dùng (Supabase PostgreSQL)
- **Lưu Trữ Bền Vững**: Chuẩn hóa `session_id` thành UUID v5, lưu 100% câu hỏi và câu trả lời vào các bảng `conversations` và `messages`.
- **An Toàn Ngắt Kết Nối**: Lưu câu hỏi người dùng ngay khi gửi và dùng khối `finally:` cho câu trả lời của AI, đảm bảo không mất lịch sử khi chuyển tab hay chuyển trang.
- **Phân Vùng Người Dùng & Tải Tức Thì**: Phân vùng lịch sử theo `user_id`, tự động tải lịch sử khi mở trang và tạo item chat mới trên sidebar ngay khi gửi câu hỏi đầu tiên.

### 3. Tối Ưu UI/UX Đổi Tên & Xóa Cuộc Trò Chuyện
- **Soft Delete Bảo Lưu CSDL**: Khi xóa chat (`DELETE /api/chat/sessions/{id}`), backend cập nhật `is_deleted = true`. Cuộc trò chuyện ẩn khỏi sidebar người dùng nhưng dữ liệu được **bảo lưu 100% trong PostgreSQL** cho RAG.
- **Tự Động Lưu Tiêu Đề (`onBlur`)**: Nhập tiêu đề mới và click ra ngoài (`onBlur`) hoặc ấn `Enter` để lưu ngay lập tức.
- **Modal Pop-up Cảnh Báo Xóa**: Bấm icon Xóa (🗑️ Trash) mở cửa sổ Pop-up xác nhận trước khi thực hiện soft delete.
- **Cố Định Tiêu Đề Ban Đầu (Preserve Chat Title)**: Sửa hàm `save_user_msg_to_db` trong `backend/app/routers/chat.py`. Tiêu đề chỉ tự động tạo 1 lần duy nhất ở tin nhắn đầu tiên; các tin nhắn sau chỉ cập nhật `updated_at`, giữ nguyên tiêu đề ban đầu (hoặc tiêu đề người dùng đã sửa).

---

## 📅 Tóm Tắt Lịch Sử Nâng Cấp (Changelog)

| STT | Hạng mục | Chi tiết nâng cấp |
|---|---|---|
| **1-5** | Hạ tầng & RAG Base | Dọn dẹp codebase, viết tài liệu backend, thiết lập RAG 4 giai đoạn, bypass auth test mode (`MSSV: SV2026001`), Docker setup. |
| **6-8** | Gemini API & Persistence | Khắc phục trễ stream Gemini 2.5, sửa lỗi 400 INVALID_ARGUMENT, chuẩn hóa UUID v5 lưu PostgreSQL. |
| **9-11** | Robustness & Performance | Khắc phục mất history khi switch tab (`finally:` block), preload ML models ở lifespan, failover tự động lỗi 503 trong 0.05s. |
| **12-14** | Auth & Session Sync | Sửa Pydantic schema `ApiResult`, phân vùng session theo User ID, thêm header Auth Bearer token cho SSE stream. |
| **15-17** | UI/UX & Title Preservation | Thêm cột `is_deleted` bảo lưu CSDL, đổi tên `onBlur`, Pop-up modal xác nhận xóa, giữ nguyên tiêu đề ban đầu không ghi đè. |
| **18** | Pre-Retrieval Guardrails | Triển khai Stage 0 Guardrails (`backend/app/guardrails/query_filter.py`): Chống Jailbreak & System Prompt Exfiltration (0ms), chuẩn hóa từ viết tắt học vụ (`dkhp`, `gpa`), lọc câu hỏi ngoài phạm vi học vụ, đóng gói XML `<retrieved_context>` chống Indirect Prompt Injection, cập nhật JWT expire 180 phút trong `.env`. |

