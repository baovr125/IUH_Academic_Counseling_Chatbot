# 🎓 IUH Academic Counseling & Microservices AI Ecosystem

Hệ sinh thái Microservices AI phục vụ **Tư vấn Học tập IUH, Dịch thuật Tài liệu & Thẻ Ghi nhớ (Flashcards)** được thiết kế theo kiến trúc **Clean Architecture 4 Lớp**, cô lập CSDL (Database-per-service), quản lý tập trung qua **Kong API Gateway** và giao tiếp bất đồng bộ qua **RabbitMQ / Redis**.

---

## 🏛️ 1. Cấu Trúc Mã Nguồn Dự Án (Project Folder Structure)

Dự án được phân chia thành 5 Microservices riêng biệt dưới thư mục `services/`, kết hợp với các thư mục tài nguyên chung (`db/`, `scripts/`, `gateway/`, `frontend/`):

```text
IUH_Academic_Counseling_Chatbot/
├── .env / .env.example                  # Cấu hình biến môi trường chung
├── docker-compose.yml                   # Orchestration 5 Microservices + Kong Gateway + Redis + RabbitMQ
├── AGENTS.md / PROJECT_LOG.md / README.md
│
├── gateway/                             # Cấu hình Kong API Gateway
│   └── kong.yml                         # Router điều hướng cổng 8000 -> Ports 8001..8005
│
├── frontend/                            # Web UI App (React 18 + TypeScript + Vite + Tailwind CSS)
│
├── db/                                  # Quản lý Schemas & Migrations SQL (PostgreSQL / Supabase)
│   ├── schema_v2_hybrid_rag.sql
│   ├── migration_v3_decks_and_docs.sql
│   └── migration_v6_doc_vectors.sql     # Schema doc_vectors (embedding vector 1024d)
│
├── scripts/                             # Scripts nạp dữ liệu & Data Pipeline chung
│   ├── data_pipeline/
│   │   └── step2_chunk_embed_v2.py      # Script Hierarchical Chunking & Embedding BGE-M3
│   └── eval/                            # Scripts đánh giá RAG Benchmark (Hit Rate@K, MRR)
│
└── services/                            # 5 STANDALONE MICROSERVICES (CÔ LẬP 100%)
    ├── 1. auth_service/                 # Port 8001: Đăng ký, Đăng nhập & Xác thực Token JWT
    ├── 2. academic_chatbot_service/    # Port 8002: Chatbot Hỏi đáp Học vụ RAG 2-Stage (Hybrid RRF + BGE)
    ├── 3. realtime_translation_service/ # Port 8003: Dịch nhanh từ/cụm từ & Redis Semantic Cache
    ├── 4. doc_translation_service/      # Port 8004: Dịch file PDF & Truy vấn RAG (BGE-M3 1024d + Hierarchical)
    └── 5. flashcard_service/            # Port 8005: Quản lý Thẻ ghi nhớ & Thuật toán SM-2
```

---

## 📐 2. Kiến Trúc Sơ Đồ Hệ Thống (System Architecture Diagram)

```mermaid
flowchart TD
    Client["💻 Client Browser (React 18 + Vite)\nhttp://localhost:5173"] -->|HTTP / SSE Stream| Gateway["🚪 Kong API Gateway\nhttp://localhost:8000"]
    
    subgraph Core_Microservices ["Hệ Sinh Thái Microservices AI (FastAPI / Python 3.11+)"]
        Gateway -->|/api/v1/auth| AuthSvc["🔑 Auth Service\n(Port 8001)"]
        Gateway -->|/api/v1/chat| ChatSvc["🤖 Academic Chatbot Service\n(Port 8002)"]
        Gateway -->|/api/v1/translate| TransSvc["🌐 Real-time Translation Service\n(Port 8003)"]
        Gateway -->|/api/v1/documents| DocSvc["📄 Doc Translation & RAG Service\n(Port 8004)"]
        Gateway -->|/api/v1/flashcards| FlashSvc["🃏 Flashcard SM-2 Service\n(Port 8005)"]
    end

    subgraph Infrastructure ["Hạ Tầng Dữ Liệu & Event Bus"]
        AuthSvc --> Supabase[("🗄️ Auth DB\n(Supabase Postgres)")]
        ChatSvc --> VectorDB[("🔍 Vector DB / FTS\n(pgvector 1024d)")]
        TransSvc --> RedisCache[("⚡ Redis Semantic Cache\n(Port 6379)")]
        DocSvc --> RabbitMQ["🐇 RabbitMQ Event Bus\n(Port 5672)"]
        DocSvc --> CeleryWorker["⚙️ Async PDF Worker"]
    end
```

---

## 🔬 3. Chi Tiết Từng Microservice Trong Hệ Thống

### 🚪 3.0. Kong API Gateway (Port 8000)
- **Vai trò**: Reverse Proxy & Central Router tập trung.
- **Header CORS**: Tự động xử lý Preflight `OPTIONS`, cấu hình `Access-Control-Allow-Origin: *`.
- **Định tuyến (Routing)**: Chuyển tiếp các request từ Frontend (`http://localhost:8000`) đến 5 microservices tương ứng.

---

### 🔑 3.1. Authentication Service (`services/auth_service` - Port 8001)
- **Tính năng**: Đăng ký, đăng nhập, xác thực sinh viên IUH và cấp mã JWT Access Token.
- **Cấu trúc**:
  - `routers/auth.py`: Direct endpoints (`/login`, `/register`, `/verify-student`, `/me`).
  - `schemas/auth.py`: Pydantic Models tự động tương thích cả camelCase và snake_case.
  - `services/auth_service.py`: Mã hóa mật khẩu Bcrypt và ký JWT Token.

---

### 🤖 3.2. Academic Counseling Chatbot Service (`services/academic_chatbot_service` - Port 8002)
- **Tính năng**: Chatbot Tư vấn Học tập IUH dựa trên **Kiến trúc 2-Stage Hybrid RAG & Streaming SSE**.
- **Nguyên lý**:
  1. **Stage 1 (Hybrid RRF)**: Kết hợp Cosine Similarity (pgvector) + Full-Text Search (FTS) qua thuật toán Reciprocal Rank Fusion (RRF).
  2. **Stage 2 (Cross-Encoder Reranking)**: Dùng model `BAAI/bge-reranker-v2-m3` lọc Top-K ngữ cảnh chính xác nhất.
  3. **Context Sandboxing**: Bọc ngữ cảnh trong thẻ XML `<retrieved_context>` chống Prompt Injection.
  4. **Streaming SSE**: Trả về từng token và trích dẫn số trang/điều khoản quy chế thời gian thực.

---

### 🌐 3.3. Real-time Translation Service (`services/realtime_translation_service` - Port 8003)
- **Tính năng**: Dịch thuật Từ & Đoạn văn ngắn nhanh lập tức.
- **Tối ưu**: Tra cứu Redis Semantic Cache (Port 6379) qua mã SHA-256 Hash. Nếu đã từng dịch (**Cache Hit**), trả kết quả trong **< 5ms**.

---

### 📄 3.4. Document Translation & RAG Service (`services/doc_translation_service` - Port 8004)
- **Tính năng**: Dịch file PDF/DOCX tài liệu bài báo khoa học & Hỏi đáp RAG trên nội dung file (Document-Bounded Q&A).
- **Thuật toán cốt lõi**:
  1. **PyMuPDF Extraction**: Trích xuất văn bản và chỉ số trang chính xác.
  2. **Hierarchical Chunking v6.2 (Parent-Child)**: Nhận diện tiêu đề H1/H2 (`Parent`), phân tách câu an toàn qua `nltk.tokenize.sent_tokenize` (`Child` 5-350 từ).
  3. **Metadata Injection (`inject_meta`)**: Bơm tiền tố mục `[Mục: Section > Subsection > Title]` trước khi tạo Vector Embedding.
  4. **BAAI/bge-m3 Embedding (1024d)**: Nhúng vector 1024 chiều lưu vào bảng `doc_vectors` trên Supabase.
  5. **Gemini Terminology-Aware Translation**: Dịch giữ nguyên thuật ngữ chuyên ngành học vụ IUH (*Credit system*, *Cumulative GPA*, *Academic Advisor*...).
  6. **Hard Payload Filtering**: Tìm kiếm vector cô lập theo `doc_id` + `user_id` và trả về câu trả lời kèm trích dẫn số trang (`[Trang X]`).

---

### 🃏 3.5. Flashcard Service (`services/flashcard_service` - Port 8005)
- **Tính năng**: Quản lý bộ thẻ ghi nhớ & Thuật toán lặp lại ngắt quãng Anki SuperMemo 2 (SM-2).
- **Thuật toán SM-2**: Tự động tính toán Ease Factor ($EF'$) và khoảng cách ngày ôn tập tiếp theo dựa trên phản hồi mức độ thuộc bài của sinh viên.

---

## 📌 4. Bảng Cổng Kết Nối & Tài Liệu API Swagger UI

| Dịch Vụ (Microservice) | Cổng Container | Cổng Gateway (Exposed) | Link Swagger UI API Docs |
| :--- | :--- | :--- | :--- |
| **Kong API Gateway** | `8000` | `8000` | - |
| **Auth Service** | `8001` | `8000/api/v1/auth` | [http://localhost:8001/docs](http://localhost:8001/docs) |
| **Academic Chatbot Service** | `8002` | `8000/api/v1/chat` | [http://localhost:8002/docs](http://localhost:8002/docs) |
| **Realtime Translation Service** | `8003` | `8000/api/v1/translate` | [http://localhost:8003/docs](http://localhost:8003/docs) |
| **Doc Translation Service** | `8004` | `8000/api/v1/documents` | [http://localhost:8004/docs](http://localhost:8004/docs) |
| **Flashcard Service** | `8005` | `8000/api/v1/flashcards` | [http://localhost:8005/docs](http://localhost:8005/docs) |
| **Frontend Web App** | `80` | `5173` | [http://localhost:5173](http://localhost:5173) |
| **RabbitMQ Management** | `15672` | `15672` | [http://localhost:15672](http://localhost:15672) |

---

## 🚀 5. Hướng Dẫn Chạy Dự Án Dành Cho Thành Viên Nhóm

### ⚡ Cách 1: Khởi chạy toàn bộ hệ thống bằng Docker Compose (Khuyên dùng)

1. **Khởi tạo file cấu hình `.env`**:
   ```bash
   cp .env.example .env
   ```
   *Điền các thông tin `SUPABASE_URL`, `SUPABASE_KEY` và `GEMINI_API_KEY` vào file `.env` vừa tạo.*

2. **Chạy Docker Compose**:
   ```bash
   docker-compose up -d --build
   ```

3. **Truy cập ứng dụng**:
   - Giao diện Web Client: [http://localhost:5173](http://localhost:5173)
   - Cổng API Gateway: [http://localhost:8000](http://localhost:8000)

4. **Xem Log của các Microservices**:
   ```bash
   # Xem log của tất cả services
   docker-compose logs -f

   # Xem log của service cụ thể (VD: Doc Translation Service)
   docker logs -f iuh_doc_translation_service
   ```

---

### 💻 Cách 2: Chạy độc lập từng Microservice dưới Local (Phục vụ Debug & Chỉnh sửa Code)

Nếu bạn muốn chỉnh sửa hoặc debug riêng 1 service (ví dụ `doc_translation_service`) mà không cần bật lại toàn bộ Docker:

1. Di chuyển vào thư mục dịch vụ:
   ```bash
   cd services/doc_translation_service
   ```
2. Khởi tạo môi trường ảo Python và cài đặt dependencies:
   ```bash
   python -m venv venv
   # Trên Windows:
   .\venv\Scripts\activate
   # Trên Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   ```
3. Chạy service với Uvicorn:
   ```bash
   uvicorn app.main:app --port 8004 --reload
   ```
4. Mở Swagger UI kiểm tra API: [http://localhost:8004/docs](http://localhost:8004/docs)

---

### 🧪 Cách 3: Chạy Script Hierarchical Chunking & Vector Embedding

Khi muốn nạp thêm dữ liệu bài báo hoặc quy chế học vụ vào Supabase PostgreSQL:

```bash
python scripts/data_pipeline/step2_chunk_embed_v2.py
```

---

## 🛡️ 6. Quy Tắc Phát Triển & Viết Mã Nguồn (Guidelines)

1. **Clean Architecture 4 Lớp**: Mọi code mới viết cho Microservice phải nằm đúng các thư mục `routers/`, `schemas/`, `services/`, `utils/`.
2. **Không Dùng Type `any` Trên Frontend**: Tất cả API Contract và Props phải được định nghĩa rõ ràng trong `frontend/src/types/`.
3. **Structured API Response**: Mọi API trả về đúng chuẩn JSON format:
   ```json
   {
     "ok": true,
     "data": { ... },
     "error": null
   }
   ```

---
*Dự án Khóa Luận Tốt Nghiệp — IUH AI Microservices Ecosystem.*
