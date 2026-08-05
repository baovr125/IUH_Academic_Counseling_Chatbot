# 📝 Nhật Ký Dự Án (PROJECT LOG)

**Tên dự án**: IUH Academic Counseling Chatbot & Language Portal  
**Thư mục gốc**: `/home/anhhao/workSpace/IUH_Academic_Counseling_Chatbot`  
**Cập nhật lần cuối**: 04/08/2026  

---

## 🎯 Tổng Quan Hệ Thống

Hệ thống Trợ lý Học vụ Thông minh IUH tích hợp RAG 4 Giai đoạn, đồng bộ dữ liệu qua Supabase PostgreSQL và cung cấp cổng học tập đa ngôn ngữ (Flashcard, Translation Studio).

---

## 🚀 Các Tính Năng Kỹ Thuật Chính

- **RAG 4 Giai đoạn & Tối ưu ML**: Rút trích ứng viên bằng pgvector, rerank bằng `bge-reranker-v2-m3` (đã tối ưu `batch_size=2` tránh OOM), nạp trước model khi khởi động để giảm độ trễ, chặn prompt injection.
- **Tối ưu Stream & LLM**: Tắt thinking budget của Gemini 2.5 giúp giảm độ trễ TTFT xuống 0.63s, tự động chuyển model dự phòng khi lỗi dưới 0.1s.
- **Quản Lý Lịch Sử Chat (Supabase)**: Phân vùng theo `user_id`, định danh UUID v5, tự động đồng bộ sidebar, bảo toàn lịch sử chat kể cả khi ngắt kết nối đột ngột.
- **UI/UX Chat**: Hỗ trợ soft-delete (giữ nguyên dữ liệu huấn luyện model), tự động lưu tiêu đề, có cảnh báo khi xoá, validation chống spam ký tự.

---

## 📅 Lịch Sử Nâng Cấp (Changelog)

- **Hạ Tầng & Khởi Tạo**: Thiết lập cấu trúc cơ bản, RAG, Docker và Auth cơ bản.
- **Hiệu Năng & Ổn Định**: Tối ưu streaming Gemini, khắc phục mất history khi switch tab, nạp sẵn AI Models, failover tự động.
- **Bảo Mật & Guardrails**: Chống Jailbreak, chống rò rỉ System Prompt, ngăn chặn truy vấn ngoài lề (Guardrails Stage 0), vá 18 lỗ hổng hệ thống nghiêm trọng.
- **Tái Cấu Trúc (Clean Architecture)**: Tách file lớn (chat.py, auth.py) thành các thư mục độc lập (routers, schemas, services, utils) hợp nhất dưới package `backend/app/`.
- **Hoàn thiện Phase 1 & 2**: Bổ sung validation (giới hạn 2000 ký tự), theo dõi độ trễ, API đánh giá phản hồi, Mở rộng ngữ cảnh RAG (Neighbor Chunk), cache TTL và fallback "Không biết" với ngưỡng tin cậy.
- **Cập Nhật Gần Nhất**: 
  - Fix crash tràn RAM (OOM) của Cross-Encoder.
  - Sửa lỗi API 404 và treo stream process.
  - Xóa bypass Auth tạm bợ và thiết lập User phát triển chuẩn (`dev@iuh.edu.vn`) có liên kết an toàn tới Database.

---

## 🧪 Chạy Test Tự Động

**Frontend** (Vitest/Jest, React Testing Library):
```bash
cd frontend1
npx vitest run
```

**Backend** (Pytest, SQLAlchemy):
```bash
cd backend
python3 -m pytest tests/
```
