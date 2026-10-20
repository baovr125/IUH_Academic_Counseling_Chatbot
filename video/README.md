# 🎬 IUH Academic Counseling & Microservices AI - Remotion Explainer Video

Dự án Remotion chuyên biệt để tạo video đồ họa động (Motion Graphics) giải thích kiến trúc hệ thống, luồng dữ liệu tương tác giữa các microservices và highlight các file mã nguồn cốt lõi dựa trên kịch bản [video-script.md](../video-script.md).

---

## 🎙️ Mô Hình TTS Tiếng Việt Chuyên Dụng (VieNeu-TTS v3)

- **Mô hình**: `pnnbao-ump/VieNeu-TTS-v3` từ HuggingFace (hơn 1.2 triệu lượt tải), chạy hoàn toàn **offline / local** trên máy có GPU NVIDIA RTX 3050 (6GB VRAM) hoặc CPU thông qua engine `vieneu`.
- **Giọng đọc**: **`Minh Quân`** (giọng nam truyền cảm, tự nhiên, chuẩn phát thanh viên, ngắt nghỉ đúng ngữ điệu và phát âm chuẩn các thuật ngữ kỹ thuật tiếng Anh như *Kong API Gateway*, *Redis*, *PostgreSQL*, *Celery*, *Parent-Child*).
- **Độ phân giải âm thanh**: 24kHz / 48kHz WAV chuyển đổi sang 192kbps MP3 chất lượng cao tại [`public/audio/`](./public/audio/).
- **Kịch bản sinh âm thanh**: [`scripts/generate_vieneu_audio.py`](../scripts/generate_vieneu_audio.py).

---

## 🏛️ Các Thành Phần Component & Đồng Bộ Trực Quan (Speech-to-Visual Sync)

1. **`ArchitectureDiagram` (`src/components/ArchitectureDiagram.tsx`)**:
   - Hiển thị sơ đồ kiến trúc 5 phân tầng (Web Client, Kong Gateway, 5 Microservices, Celery Worker, PostgreSQL/pgvector + Redis 7 + RabbitMQ + MinIO).
   - **Đồng bộ thời gian thực theo giọng đọc**:
     - *5.5s - 14.5s*: Nói về **Web Client (React 18)** ➔ Node `client-web` sáng rực rỡ, các node khác mờ đi.
     - *14.5s - 27.5s*: Nói về **Kong API Gateway** (bác bảo vệ kiểm tra thẻ JWT, Rate Limit) ➔ Node `gateway-kong` sáng rực rỡ kèm huy hiệu `🎯 ĐANG GIẢI THÍCH`.
     - *27.5s - 38.5s*: Nói về **Academic Chatbot Service** ➔ Node `svc-chatbot` sáng rực rỡ.
     - *38.5s - 47.5s*: Nói về **Redis 7 & PostgreSQL pgvector** ➔ Node `cache-redis` và `db-postgres` sáng.
     - *47.5s - 55.4s*: Nói về **Worker Celery, RabbitMQ & MinIO** ➔ Node `worker-doc` sáng.
2. **`DataFlowOverlay` (`src/components/DataFlowOverlay.tsx`)**:
   - Mô phỏng gói tin dữ liệu di chuyển từng bước dọc theo đường cong Bezier, minh họa bằng ví dụ thực tế của sinh viên K21 hỏi về điểm C môn Triết và học vượt.
3. **`FolderTree` (`src/components/FolderTree.tsx`)**:
   - Cây thư mục tương tác hiển thị cấu trúc mã nguồn thực tế của repository, tự động chuyển focus vào đúng file khi thuyết minh đang giải thích.
4. **`FileHighlightCard` (`src/components/FileHighlightCard.tsx`)**:
   - Thẻ IDE hiển thị code snippet thực tế, số dòng và các đóng góp kỹ thuật then chốt của 4 file: `hybrid_chunker.py`, `rag_service.py`, `prompt_templates.py`, và `query_filter.py`.
5. **`SubtitlesBar` (`src/components/SubtitlesBar.tsx`)**:
   - Thanh phụ đề nổi ở dưới màn hình kèm bộ hiển thị sóng âm thanh Equalizer động chạy theo thời gian thực.
6. **`MainVideo` (`src/MainVideo.tsx`)**:
   - Điều phối 5 phân cảnh chính nối tiếp nhau qua `<Series>` (Tổng thời lượng: **7264 frames @ 30fps = ~4 phút 02 giây**).

---

## 📺 Danh Sách Các Composition Đã Đăng Ký Trong Remotion

| Composition ID | Độ Phân Giải | FPS | Thời Lượng | Nội Dung Chi Tiết |
| :--- | :--- | :--- | :--- | :--- |
| **`MainExplainerVideo`** | 1920x1080 | 30 | 7264 frames (~4m 02s) | **Toàn bộ video thuyết trình hợp nhất đồng bộ âm thanh** |
| `SceneArchitecture` | 1920x1080 | 30 | 1660 frames (55.4s) | Sơ đồ kiến trúc động & spotlight chính xác từng Node theo giọng nói |
| `SceneDataFlow` | 1920x1080 | 30 | 1821 frames (60.7s) | Mô phỏng luồng dữ liệu 6 bước với ví dụ thực tế K21 |
| `SceneFileHighlights` | 1920x1080 | 30 | 1653 frames (55.1s) | Cây thư mục + Highlight 4 file code cốt lõi (`hybrid_chunker`, `rag_service`...) |
| `SceneMetrics` | 1920x1080 | 30 | 1008 frames (33.6s) | Bảng chỉ số thực nghiệm & 126/126 Unit Tests đạt 100% |

---

## 🚀 Hướng Dẫn Vận Hành

### 1. Khởi Chạy Remotion Studio (Xem & Nghe Trực Tiếp Trên Trình Duyệt)
```bash
cd video
npm run dev
```
Trình duyệt sẽ tự động mở giao diện Remotion Studio tại `http://localhost:3000`, cho phép bạn tua timeline, nghe giọng thuyết minh tự nhiên của `Minh Quân` và kiểm tra sự đồng bộ từng frame.

### 2. Tạo Lại Giọng Đọc Khi Cần Chỉnh Sửa Kịch Bản
```bash
/home/anhhao/miniconda3/envs/py311/bin/python scripts/generate_vieneu_audio.py
```

### 3. Kiểm Tra Linter & Typecheck
```bash
npm run lint
```

### 4. Build Bundle
```bash
npm run build
```
