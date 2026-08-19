# Hướng Dẫn Triển Khai & Mở Rộng Hệ Thống Máy Chủ (Deployment & Scaling Guide)

Tài liệu này hướng dẫn chi tiết quy trình triển khai (Deploy) toàn bộ hệ sinh thái **IUH Academic Counseling Chatbot & Language Portal** lên máy chủ chuyên dụng (Production Server) với cấu hình phần cứng lớn và hỗ trợ tăng tốc đồ họa (GPU Acceleration).

---

## 1. Yêu cầu Cấu hình Máy chủ Khuyến nghị (Recommended Production Specs)

| Thành phần | Cấu hình Tiêu chuẩn (Standard Server) | Cấu hình Chuyên sâu (High-Performance Server) |
| :--- | :--- | :--- |
| **Hệ điều hành** | Ubuntu Server 22.04 / 24.04 LTS | Ubuntu Server 22.04 LTS (Hỗ trợ CUDA tốt nhất) |
| **CPU** | 8 - 16 Cores (Intel Xeon / AMD EPYC) | 16 - 32 Cores (AMD EPYC / Intel Xeon Platinum) |
| **RAM** | **32 GB DDR4/DDR5 ECC** | **64 GB - 128 GB DDR5 ECC** |
| **GPU / VRAM** | **1x NVIDIA RTX 3090 / 4090 (24GB VRAM)** | **1x - 2x NVIDIA A100 / A6000 (40GB - 80GB VRAM)** |
| **Ổ cứng (Storage)** | 500 GB - 1 TB NVMe SSD (Gen 4) | 2 TB NVMe SSD (RAID 10) |
| **Băng thông mạng** | 1 Gbps Dedicated Port | 10 Gbps Port |

---

## 2. Cài đặt Driver NVIDIA & NVIDIA Container Toolkit trên Ubuntu Server

Để Docker Container có thể nhận diện và sử dụng Card đồ họa (GPU) phục vụ mô hình AI, OCR và Local LLM:

```bash
# 1. Cập nhật hệ thống & cài đặt NVIDIA Driver
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y nvidia-driver-550 nvidia-utils-550

# 2. Cài đặt NVIDIA Container Toolkit cho Docker
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 3. Cấu hình Docker daemon và khởi động lại Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 4. Kiểm tra Docker đã nhận GPU thành công
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

---

## 3. Chiến lược Tối ưu Hạn mức Tài nguyên (Resource Allocation) trên Server 64GB RAM

Khi deploy trên máy chủ 64GB RAM, bạn nâng hạn mức trong `docker-compose.yml` như sau:

```yaml
services:
  # Kong Gateway: Xử lý hàng chục nghìn request đồng thời
  kong-gateway:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G

  # Chatbot Service: Load Bi-Encoder + Cross-Encoder lên GPU
  academic-chatbot-service:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Celery Worker Dịch thuật: Tăng tốc OCR và xử lý đa luồng
  doc-translation-worker:
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Real-time Translation & TTS
  realtime-translation-service:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
```

---

## 4. Mở rộng Quy mô Ngang (Horizontal Scaling)

### 4.1. Scale số lượng Worker Dịch tài liệu (Celery Worker Replication)
Khi có hàng trăm sinh viên cùng upload tài liệu PDF/DOCX, bạn chỉ cần scale số lượng container worker mà không cần sửa code:

```bash
# Khởi chạy 4 Worker chạy song song
docker compose up -d --scale doc-translation-worker=4
```
*Hệ thống RabbitMQ sẽ tự động phân phối đều từng file tài liệu vào hàng đợi cho 4 worker xử lý đồng thời.*

### 4.2. Scale Stateless Web Services
Với các service nhẹ (`auth_service`, `flashcard_service`, `realtime_translation_service`):
* Cấu hình Kong Gateway Upstream làm bộ cân bằng tải (Load Balancer - Round Robin).

---

## 5. Tách Kiến trúc Model-as-a-Service (vLLM / Triton Inference Server)

Khi lượng người dùng lớn, thay vì mỗi microservice tự import `sentence-transformers`, nên tách một Inference Cluster độc lập:

1. **Text Embeddings & Reranking**: Sử dụng **HuggingFace TEI (Text Embeddings Inference)** chạy trực tiếp trên GPU.
   ```bash
   docker run --gpus all -p 8080:80 ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id BAAI/bge-reranker-v2-m3
   ```
2. **Local LLM Server (Ollama / vLLM)**: Sử dụng **vLLM** với cơ chế PagedAttention để phục vụ suy luận LLM với độ trễ dưới 20ms.
3. Các microservice chỉ cần gửi request HTTP/gRPC siêu nhẹ đến cụm Inference này, giải phóng $100\%$ RAM cho container nghiệp vụ.

---

## 6. Bảo mật & SSL/TLS Production
1. **Tên miền & SSL (HTTPS)**: Sử dụng Cloudflare hoặc Nginx Reverse Proxy phía trước Kong Gateway để cài đặt chứng chỉ Let's Encrypt SSL/TLS miễn phí.
2. **MinIO Production**: Đổi mật khẩu `MINIO_ROOT_USER` và `MINIO_ROOT_PASSWORD` trong file `.env`, bật SSL cho MinIO Console.
3. **Database Supabase/PostgreSQL**: Đặt Connection Pooling (PgBouncer) với max connection $\ge 100$.
