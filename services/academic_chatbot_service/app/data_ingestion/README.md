# Data Pipeline - Chatbot Tư Vấn Học Vụ IUH

Thư mục này chứa quy trình xử lý dữ liệu (data pipeline) cho Chatbot Tư vấn Học vụ IUH. Pipeline chịu trách nhiệm thu thập dữ liệu từ các trang web của trường, xử lý thành định dạng thân thiện với LLM (Markdown), chia nhỏ dữ liệu thành các đoạn (chunk), và nhúng (embed) vào cơ sở dữ liệu vector (Supabase) để phục vụ cho hệ thống RAG (Retrieval-Augmented Generation).

## 📂 Cấu Trúc Thư Mục

- `extractors/`: Chứa logic để tìm kiếm và trích xuất URL từ nhiều nguồn khác nhau (Sitemaps, Breadth-First Search, Trang danh mục).
- `crawlers/`: Chứa logic để tải nội dung từ các URL và chuyển đổi sang định dạng Markdown. Xử lý cả trang HTML và tài liệu PDF, bao gồm cả khả năng nhận dạng ký tự quang học (OCR) cho hình ảnh.
- `chunkers/`: Triển khai các chiến lược chia nhỏ văn bản (ví dụ: Parent-Child Chunking) để cắt các tài liệu Markdown dài thành các đoạn nhỏ hơn, có ngữ nghĩa liên quan để phục vụ tìm kiếm vector.
- `embedders/`: Đảm nhiệm việc tạo các vector nhúng (sử dụng mô hình `bkai-foundation-models/vietnamese-bi-encoder`) và lưu chúng vào cơ sở dữ liệu Supabase.
- `utils/`: Các script tiện ích như ghi log (logger) và các hàm hỗ trợ khác.
- `run_pipeline.py`: File script chính để điều phối và chạy toàn bộ pipeline hoặc từng bước cụ thể.
- `requirements.txt`: Các thư viện Python cần thiết để chạy pipeline.

## ⚙️ Logic & Quy Trình Hoạt Động

Pipeline được chia thành 4 bước chạy tuần tự:

### 1. Trích xuất URL (Bước 0)
- **Mục tiêu:** Thu thập toàn bộ các URL liên quan cần cào dữ liệu.
- **Phương pháp:** Sử dụng phương pháp kết hợp (hybrid):
  - Phân tích XML Sitemaps (vd: `camnang.iuh.edu.vn`).
  - Lấy các link từ trang danh mục (vd: `iuh.edu.vn/vi/thong-bao.html`).
  - Sử dụng thuật toán BFS (Breadth-First Search) để duyệt các link theo chiều sâu nhất định.
  - Bổ sung một số URL cụ thể (vd: các trang quy chế tuyển sinh).
- **Đầu ra:** Lưu danh sách các URL vào `data/urls.json` và biểu đồ liên kết website vào `data/web_structure_graph.json`.

### 2. Cào Dữ Liệu (Bước 1)
- **Mục tiêu:** Tải nội dung từ danh sách URL đã trích xuất và chuyển đổi thành Markdown.
- **Phương pháp:**
  - Sử dụng đa luồng (multithreading) để tăng tốc độ cào dữ liệu.
  - Làm sạch mã HTML và lấy nội dung chính (sử dụng `trafilatura` và `beautifulsoup4`).
  - Trích xuất văn bản từ file PDF (dùng `PyMuPDF`) và xử lý hình ảnh qua OCR (`pytesseract`).
- **Đầu ra:** Lưu các file Markdown vào thư mục `data/crawled_markdown/`.

### 3. Chia Nhỏ Dữ Liệu - Chunking (Bước 2)
- **Mục tiêu:** Cắt các tài liệu Markdown lớn thành các đoạn (chunk) nhỏ hơn để tối ưu hóa việc truy xuất tìm kiếm vector.
- **Phương pháp:**
  - Triển khai **Hybrid Chunker** sử dụng chiến lược Parent-Child.
  - Tạo các đoạn Parent lớn để giữ ngữ cảnh, và các đoạn Child nhỏ (vd: max_size 600, overlap 100) để tìm kiếm ngữ nghĩa chính xác.
- **Đầu ra:** Lưu kết quả vào `data/parents.json` và `data/children.json`.

### 4. Nhúng Dữ Liệu - Embedding (Bước 3)
- **Mục tiêu:** Chuyển đổi các đoạn văn bản (chunk) thành các biểu diễn vector và lưu trữ vào database.
- **Phương pháp:**
  - Sử dụng mô hình `bkai-foundation-models/vietnamese-bi-encoder` để tạo embeddings.
  - Tải các vector và siêu dữ liệu (metadata) của chunk lên cơ sở dữ liệu PostgreSQL của Supabase có hỗ trợ `pgvector`.

## 🚀 Hướng Dẫn Chạy Pipeline

Trước khi chạy, hãy đảm bảo bạn đã cài đặt đầy đủ các thư viện yêu cầu:

```bash
pip install -r data_pipeline/requirements.txt
```

Bạn có thể chạy pipeline bằng file script `run_pipeline.py`. Script này hỗ trợ tham số `--step` để chạy toàn bộ pipeline hoặc một bước cụ thể.

Chạy các lệnh sau từ thư mục gốc (root) của project:

```bash
# Chạy toàn bộ pipeline tuần tự
python -m data_pipeline.run_pipeline --step all

# 1. Chỉ chạy bước Trích xuất URL
python -m data_pipeline.run_pipeline --step extract

# 2. Chỉ chạy bước Cào dữ liệu & Parse (cần có file urls.json)
python -m data_pipeline.run_pipeline --step crawl

# 3. Chỉ chạy bước Chia nhỏ Chunk (cần có thư mục crawled_markdown/)
python -m data_pipeline.run_pipeline --step chunk

# 4. Chỉ chạy bước Nhúng Vector (cần có file children.json)
python -m data_pipeline.run_pipeline --step embed
```

*Lưu ý: Hãy đảm bảo các biến môi trường cấu hình cho Supabase (ví dụ: URL và Key) đã được thiết lập đầy đủ trước khi chạy bước Embedding.*
