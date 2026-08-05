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
| **19** | Backend Audit Fix (18 lỗi) | Kiểm tra toàn diện backend và sửa 18 lỗi từ CRITICAL → LOW (xem bảng chi tiết bên dưới). |
| **20** | Tái Cấu Trúc Chat Backend (Modular Architecture) | Tách file `chat.py` (710 dòng) thành kiến trúc đa tầng Clean Architecture: `app/schemas/chat.py` (Pydantic models), `app/services/chat_service.py` (Supabase DB CRUD & Session), `app/services/rag_service.py` (ML Models, Hybrid RRF, Cross-Encoder, Rewriter), giữ `app/routers/chat.py` thuần túy (~200 dòng) xử lý HTTP/SSE Endpoints. |
| **21** | Tái Cấu Trúc Auth Backend (Modular Architecture) | Tách file `routes/auth.py` (502 dòng) thành `services/auth_service.py` chứa 100% logic xác thực (đăng ký, đăng nhập, Google OAuth token check, OTP reset password), rút gọn `routes/auth.py` về ~100 dòng chỉ làm nhiệm vụ route handler. |
| **22** | Hợp Nhất Thư Mục Backend (Unified App Package) | Xóa bỏ sự trùng lặp thư mục giữa `backend/` gốc và `backend/app/`. Gom 100% routers, schemas, services, utils về gói thống nhất `backend/app/` (`app/routers/`, `app/schemas/`, `app/services/`, `app/utils/`). Cập nhật tất cả các đường dẫn import chuẩn hóa (`from app.schemas...`, `from app.utils...`). |
| **23** | Khắc phục lỗi Phase 0 (Roadmap) | Sửa 3 lỗi nghiêm trọng: 1) Sửa UI hiển thị nội dung stream (không bị kẹt ở typing dots), 2) Thêm Auth Headers cho `sendMessage` & `sendMessageStream`, 3) Cập nhật database hỗ trợ FTS tiếng Việt (thêm extension `unaccent` và `pg_trgm`). |
| **24** | Khắc phục lỗi Phase 1 (Roadmap) - Task 1.4 | Cập nhật Schema Hardening và Input Validation. Thêm `max_length=2000` và validator loại bỏ khoảng trắng cho `SendMessagePayload` trong `backend/app/schemas/chat.py`. Kiểm tra nghiêm ngặt `role: Literal['user', 'assistant']`. Bổ sung hiển thị số lượng ký tự (`{value.length}/2000`) và vô hiệu hóa nút gửi trên frontend UI (`frontend1/src/components/chat/ChatComposer.tsx`). |

---

## 🔧 Chi Tiết Sửa Lỗi Backend Audit (Mục #19)

> **Ngày thực hiện**: 04/08/2026  
> **Tổng số lỗi**: 18 (3 CRITICAL · 3 HIGH · 7 MEDIUM · 5 LOW)

### 🔴 CRITICAL (3 lỗi)

| Mã | Tên lỗi | File | Mô tả vấn đề | Cách sửa |
|---|---|---|---|---|
| C1 | Blocking SSE Stream | `backend/app/routers/chat.py` | Vòng lặp `for chunk in stream_iter` là đồng bộ (synchronous), chặn toàn bộ event loop asyncio → server đứng khi có nhiều request đồng thời. | Thay bằng `while True: chunk = await asyncio.to_thread(lambda: next(stream_iter, None))` để đọc từng chunk trong thread pool. |
| C2 | Mock Auth Bypass | `backend/utils/security.py` | Token bắt đầu bằng `mock_`/`test_`/`dev_` bỏ qua xác thực JWT **ở mọi môi trường**, kể cả production. | Thêm điều kiện `os.getenv("ENVIRONMENT") in ("development", "dev", "test")` trước khi cho phép bypass. Thêm `ENVIRONMENT=development` vào `.env`. |
| C3 | ENV Crash khi thiếu biến | `backend/utils/security.py` | `int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))` crash với `TypeError` nếu biến môi trường không tồn tại. | Thêm giá trị mặc định: `int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "180"))`. |

### 🟠 HIGH (3 lỗi)

| Mã | Tên lỗi | File | Mô tả vấn đề | Cách sửa |
|---|---|---|---|---|
| H1 | Query Rewriter bị bỏ qua | `backend/app/routers/chat.py` | Ở streaming mode, `save_user_msg_to_db` lưu tin nhắn vào DB **trước** khi `build_rag_payload` đọc history → query rewriter thấy tin nhắn hiện tại là "last user msg" và bỏ qua rewrite. | Tạo `filtered_history` loại trừ tin nhắn hiện tại (`msg["content"] == content`) trước khi truyền vào `generate_standalone_query`. |
| H2 | Duplicate User Message | `backend/app/routers/chat.py` | Tin nhắn người dùng xuất hiện **2 lần** trong payload gửi Gemini API: 1 lần từ `history[-6:]` và 1 lần từ `contents.append(current_query)`. | Sử dụng `filtered_history[-6:]` (đã loại trừ msg hiện tại) để build `contents`, tránh trùng lặp. |
| H3 | Thiếu Auth ở `/messages` | `backend/app/routers/chat.py` | Endpoint `POST /messages` (non-streaming) không có dependency `get_optional_current_user_id` → không gắn `user_id` vào conversation. | Thêm `current_user_id: Optional[str] = Depends(get_optional_current_user_id)` và truyền vào `save_turn_to_db`. |

### 🟡 MEDIUM (7 lỗi)

| Mã | Tên lỗi | File | Mô tả vấn đề | Cách sửa |
|---|---|---|---|---|
| M1 | Domain Filter Bypass | `backend/app/guardrails/query_filter.py` | Từ khóa generic (`hỏi`, `tư vấn`, `hỗ trợ`) trong `ACADEMIC_DOMAIN_KEYWORDS` được kiểm tra **TRƯỚC** `OFF_TOPIC_TRIGGERS` → câu hỏi như "tư vấn nấu phở" bị coi là hợp lệ. | Đảo thứ tự: kiểm tra `OFF_TOPIC_TRIGGERS` trước, xóa 3 từ generic ra khỏi danh sách. |
| M2 | Double Normalization | `backend/app/routers/chat.py` | `normalize_academic_query()` gọi **2 lần**: ở endpoint và lại ở `build_rag_payload()`. | Xóa lần gọi trong `build_rag_payload()`, chỉ giữ ở endpoint (caller). |
| M3 | Thiếu `__init__.py` | `backend/app/guardrails/` | Thư mục `guardrails/` thiếu file `__init__.py` → có thể gây lỗi import trong một số cấu hình Python. | Tạo file `__init__.py` với comment mô tả package. |
| M4 | Unsafe Dict Access | `backend/app/routers/chat.py` | `c['content']` gây `KeyError` nếu chunk không có key `content`. | Đổi thành `c.get('content', '')`. |
| M5 | Guardrail Refusals không lưu DB | `backend/app/routers/chat.py` | Khi guardrail chặn (jailbreak/off-topic) ở endpoint non-streaming, câu trả lời **không được lưu vào DB** → mất dữ liệu audit. | Thêm `save_user_msg_to_db()` + `save_assistant_msg_to_db()` trước khi return refusal. |
| M6 | Thiếu Metadata SSE Event | `backend/app/routers/chat.py` | Khi guardrail chặn ở streaming mode, chỉ gửi `delta` + `done` mà **không gửi `metadata`** → frontend có thể không cập nhật `sessionId`. | Thêm `yield metadata event` với `sessionId` và `citations: []` trước khi gửi refusal text. |
| M7 | CORS Wildcard | `backend/main.py` | `allow_origin_regex=".*"` cho phép **mọi origin** bất kể danh sách `allow_origins`, vô hiệu hóa bảo mật CORS. | Xóa dòng `allow_origin_regex=".*"`. |

### 🟢 LOW (5 lỗi)

| Mã | Tên lỗi | File | Mô tả vấn đề | Cách sửa |
|---|---|---|---|---|
| L1 | Trả về title chưa sanitize | `backend/app/routers/chat.py` | `rename_session` trả về `payload.title` gốc (chưa strip/truncate) thay vì `new_title` đã xử lý. | Trả về `new_title` (đã `.strip()[:100]`). |
| L2 | Tiêu đề chỉ có khoảng trắng | `backend/app/routers/chat.py` | Title toàn whitespace qua `.strip()` thành chuỗi rỗng → lưu title trống vào DB. | Kiểm tra `if not new_title:` → trả lỗi "Tiêu đề không được để trống". |
| L3 | Silent Exception Swallowing | `backend/app/routers/chat.py` | 8+ khối `except: pass` nuốt mọi lỗi → không thể debug khi gặp sự cố production. | Thay tất cả bằng `except Exception as e: logger.warning(f"...")`. |
| L4 | passlib + bcrypt xung đột | `backend/requirements.txt` | `passlib[bcrypt]` chưa tương thích `bcrypt>=4.1` (đổi API internal) → crash khi hash password. | Pin `bcrypt>=3.2.0,<4.0.0` trong requirements.txt. |
| L5 | `datetime.utcnow()` deprecated | `backend/utils/security.py` | `datetime.utcnow()` deprecated từ Python 3.12, trả về naive datetime không có timezone info. | Thay bằng `datetime.now(timezone.utc)`, import thêm `timezone`. |

---

## 🧪 Hướng Dẫn Chạy Test Tự Động (Automated Tests)

Các test case tự động cho Phase 0 đã được tạo. Dưới đây là cách chạy test (Yêu cầu phải cài đặt các thư viện test trước):

### 1. Frontend Tests (React Testing Library + Jest)
File test: `frontend1/tests/ChatMessageBubble.test.tsx` và `frontend1/tests/chatService.test.ts`

**Cách cài đặt & chạy:**
```bash
cd frontend1
# Cài đặt thư viện test (Vitest/Jest, Testing Library)
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom
# Chạy test
npx vitest run
```

### 2. Backend Tests (Pytest + SQLAlchemy)
File test: `backend/tests/test_fts_vietnamese.py`

**Cách cài đặt & chạy:**
```bash
cd backend
# Kích hoạt môi trường ảo (ví dụ: source .venv/bin/activate)
# Cài đặt pytest
pip install pytest pytest-asyncio
# Chạy test
python3 -m pytest tests/test_fts_vietnamese.py
```
