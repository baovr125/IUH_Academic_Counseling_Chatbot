# Deploy nhanh: đọc file này trước

> **Dành cho:** bất kỳ ai (hoặc trợ lý AI) vừa lấy mã nguồn về và cần chạy được bản demo của dự án này trên máy mình mà
> chưa biết gì về ngữ cảnh. File tự đủ: đọc từ trên xuống, làm từng bước, mỗi bước có **kết quả mong đợi** và **cách xử lý khi sai**.
> Trạng thái ghi trong file đúng vào ngày **2026-10-28**. Muốn hiểu sâu hơn, đọc thêm [DEPLOY.md](DEPLOY.md).

## 0. Quy tắc cho trợ lý AI (và người) trước khi làm bất cứ điều gì

1. **Không in, không commit, không gửi** nội dung `.env.prod` hay bất kỳ khóa/mật khẩu nào. Nếu cần kiểm tra file, chỉ nói tên biến và độ dài.
2. **Hỏi người dùng trước khi** chạy: `git push`, `tailscale funnel` (đưa dịch vụ ra internet công khai), `docker compose down`, hoặc bất kỳ lệnh xóa nào.
3. **Không** dùng `docker compose down -v` (xóa dữ liệu MinIO) và **không** dùng `docker system prune`.
4. Lệnh trong file viết cho **PowerShell trên Windows**. Trên Linux/macOS các lệnh `docker`, `git`, `python` giống hệt; chỉ phần Tailscale và kiểm tra cổng/ổ đĩa khác.
5. Gặp lỗi thì **dừng lại ở bước đó**, đọc mục "Nếu không đạt", đừng nhảy sang bước sau.
6. Chỉ khẳng định điều đã kiểm tra. Những điều chưa kiểm chứng được liệt kê ở [mục 8](#8-những-điều-chưa-được-kiểm-chứng).

## 1. Bối cảnh trong 1 phút

**Dự án:** hệ sinh thái AI cho sinh viên IUH gồm chatbot tư vấn học vụ (RAG), dịch thuật thời gian thực, thẻ ghi nhớ
(flashcard) và xác thực. Mã nguồn: https://github.com/baovr125/IUH_Academic_Counseling_Chatbot

**Đã làm gì (tóm tắt):** đóng gói để chạy demo trên **một máy** bằng Docker Compose và đưa ra internet qua **Tailscale Funnel**
(một link HTTPS duy nhất). LLM gọi qua **API key (Gemini)**. Tính năng **Dịch tài liệu đã bị khóa** vì service đó không được triển khai.

```
Người dùng ──HTTPS──> Tailscale Funnel ──> nginx (127.0.0.1:5173) ──/api──> Kong ──> auth | chatbot | realtime | flashcard
                                                                                   (Supabase, Redis, RabbitMQ, MinIO, Gemini/Groq)
```

**Từ khóa cần biết**

| Từ | Nghĩa |
|---|---|
| **Kong** | Cổng API: kiểm JWT, giới hạn tốc độ, CORS. Mọi `/api/...` đều đi qua đây |
| **`.env.prod`** | File cấu hình/bí mật của lần triển khai này. Tự tạo, **không có trong git** |
| **`docker-compose.prod.yml`** | Lớp phủ đặt lên `docker-compose.yml`: dùng `.env.prod`, không mount mã nguồn, chỉ mở `127.0.0.1:5173` |
| **Chế độ API / GPU** | Chatbot gọi Gemini (mặc định) hay gọi vLLM/Ollama ở máy GPU khác (tuỳ chọn). File này chỉ dùng chế độ API |
| **Funnel** | Tính năng của Tailscale để đưa một cổng cục bộ ra internet công khai (bước tuỳ chọn) |

**Nhánh và PR (quan trọng khi lấy code)**

| Thứ | Có gì | Ghi chú |
|---|---|---|
| `main` | Toàn bộ phần deploy (PR #21): `docker-compose.prod.yml`, `.env.prod.example`, khóa doc-translation | Đã merge |
| Nhánh `docs/deploy-guide` (PR #22) | Thêm `DEPLOY.md`, file này, `scripts/deploy_smoke.py` | **Lấy nhánh này nếu PR #22 chưa merge** |

## 2. Trước khi bắt đầu: máy của bạn có đủ điều kiện không?

| Yêu cầu | Cách kiểm tra | Cần |
|---|---|---|
| Docker Desktop (hoặc Docker Engine) | `docker version` | Chạy được |
| Docker Compose | `docker compose version` | **>= 2.24** |
| GPU NVIDIA chạy được trong Docker | `docker run --rm --gpus all ubuntu nvidia-smi` | Thấy tên card |
| VRAM | `nvidia-smi` | **8 GB:** chạy bình thường (cả stack ~7,0 GB gồm Windows, rất sát). **6 GB:** chỉ chạy được với [chế độ tiết kiệm VRAM](#card-6-gb-chế-độ-tiết-kiệm-vram). Dưới 6 GB: không khuyến nghị |
| RAM | Task Manager | >= 16 GB |
| Ổ đĩa trống (ổ chứa dữ liệu Docker) | `Get-PSDrive` | >= 40 GB |
| Cổng trống | `Get-NetTCPConnection -State Listen -LocalPort 5173,5672,15672,6379,9000,9001 -ErrorAction SilentlyContinue` | Không in ra gì |
| Python 3.11+ và git | `python --version`, `git --version` | Có |
| Internet | | Cần lúc build và tải model |

**Nếu máy không có GPU NVIDIA: DỪNG.** Hướng triển khai này chưa được kiểm chứng trên CPU (xem mục 8). Bạn vẫn đóng góp được bằng cách
test trên link demo của chủ máy, chuẩn bị dữ liệu demo và sửa CI.

### Card 6 GB: chế độ tiết kiệm VRAM

Mức VRAM đo trên máy chủ dự án (RTX 4060 Laptop 8 GB), tính xấp xỉ:

| Thành phần | VRAM |
|---|---|
| Windows và các ứng dụng đang mở (explorer, trình duyệt, Zalo...) | ~0,9 GB |
| `realtime-translation-service` (dịch, NLLB float16) | ~1,8 GB |
| `academic-chatbot-service` (embedder + reranker ONNX) | ~4,3 GB |
| **Tổng khi cả hai trên GPU** | **~7,0 GB, không vừa card 6 GB** |
| Tổng khi realtime chuyển sang CPU | ~5,25 GB, còn ~0,75 GB trống (rất sát) |

Nếu card của bạn là 6 GB, ở **Bước 4** (và mọi lệnh `docker compose` sau đó) thêm `-f docker-compose.lowvram.yml` vào **cuối** danh sách file:

```powershell
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.lowvram.yml up -d --build
```

Cách này đưa model dịch NLLB sang CPU (int8) để giải phóng ~1,8 GB. Đánh đổi và giới hạn:
- Dịch realtime **chậm hơn** (chưa đo độ trễ). Chatbot vẫn dùng GPU ~4,3 GB.
- Vẫn **rất sát**: đóng trình duyệt tăng tốc phần cứng, game và mọi ứng dụng dùng GPU khác. Nếu bị `CUDA out of memory`, thử giảm ứng dụng nền trước khi nghĩ đến lỗi khác.
- **Đừng thử ẩn GPU khỏi chatbot** bằng `CUDA_VISIBLE_DEVICES`: container chatbot sẽ crash (`free(): double free detected`) và khởi động lại liên tục. Muốn chatbot chạy CPU phải sửa mã, chưa làm.
- Chưa chạy thật trên máy 6 GB; số liệu ở trên là suy ra từ máy 8 GB.

## 3. Các bước

### Bước 1. Lấy đúng nhánh

```powershell
git clone https://github.com/baovr125/IUH_Academic_Counseling_Chatbot.git
cd IUH_Academic_Counseling_Chatbot
git fetch origin
git switch docs/deploy-guide      # nếu PR #22 đã merge thì dùng: git switch main
```

**Mong đợi:** các lệnh sau đều trả `True`
```powershell
Test-Path docker-compose.prod.yml, .env.prod.example, scripts/deploy_smoke.py, scripts/download_models.py, DEPLOY_QUICKSTART.md
```
**Nếu không:** bạn đang sai nhánh. Chạy `git branch --show-current` và `git log --oneline -3` (commit mới nhất phải bắt đầu bằng `docs:` hoặc `Merge pull request`).

### Bước 2. Tải model cho chatbot (không nằm trong git)

```powershell
python scripts/download_models.py
```
**Mong đợi:** có hai thư mục `hf_models/vietnamese-bi-encoder-onnx` và `hf_models/bge-reranker-v2-m3-onnx` (~2,7 GB tổng).
**Nếu không:** báo không thấy `huggingface-cli` thì thử `hf download AnhHao0107/vietnamese-bi-encoder-onnx --local-dir hf_models/vietnamese-bi-encoder-onnx`
(và tương tự cho `AnhHao0107/bge-reranker-v2-m3-onnx`). Model NLLB/fastText của realtime tự tải lúc build, không cần làm gì.

### Bước 3. Tạo `.env.prod`

```powershell
Copy-Item .env.prod.example .env.prod
```
Sinh ba bí mật mới (in ra màn hình, chép vào `.env.prod`, **đừng gửi cho ai**):
```powershell
python -c "import secrets; [print(k, secrets.token_urlsafe(n)) for k,n in (('JWT_SECRET_KEY',48),('RABBITMQ_DEFAULT_PASS',18),('MINIO_ROOT_PASSWORD',24))]"
```

Mở `.env.prod` và điền:

| Biến | Giá trị |
|---|---|
| `JWT_SECRET_KEY`, `RABBITMQ_DEFAULT_PASS`, `MINIO_ROOT_PASSWORD` | Ba giá trị vừa sinh |
| `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` | **Xin chủ dự án Supabase (baovr125)** qua kênh an toàn, không dùng tin nhắn thường |
| `GEMINI_API_KEY` | Khóa của bạn (Google AI Studio) |
| `GROQ_API_KEY` | Khóa của bạn (Groq) |
| `PUBLIC_ORIGIN`, `CORS_ALLOW_ORIGINS` | Chạy trên chính máy này: `http://localhost:5173` (cả hai biến). Dùng Funnel thì đổi ở bước 6 |
| Các biến còn lại | Giữ nguyên. Chế độ API (`LLM_PROVIDER=gemini`) đã đặt sẵn |

**Mong đợi:** không còn giá trị mẫu (`CHANGE-ME`, `YOUR_...`, `[...]`). Kiểm tra bằng lệnh sau, kết quả phải là **0** (lệnh chỉ đếm, không in nội dung; dòng chú thích bắt đầu bằng `#` được bỏ qua):
```powershell
(Select-String -Path .env.prod -Pattern '^[^#\s].*(CHANGE|YOUR_|GENERATE|\[[A-Z_]+\])' | Measure-Object).Count
```
**Nếu không:** thiếu giá trị nào thì điền nốt. `JWT_SECRET_KEY` phải >= 32 ký tự, nếu không Kong từ chối khởi động.

### Bước 4. Build và chạy

```powershell
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
**Mong đợi:** lần đầu **lâu** (build các image nặng như torch/CUDA, ~17 GB, tuỳ mạng có thể vài chục phút); kết thúc không có chữ `error`, các container ở trạng thái `Started`/`Healthy`.
**Nếu không:** xem [mục 5](#5-sự-cố-thường-gặp). Lỗi `could not select device driver "nvidia"` nghĩa là Docker chưa dùng được GPU.

### Bước 5. Kiểm tra

Đợi khoảng **2 phút** (chatbot nạp model nên chưa trả lời ngay), rồi:

```powershell
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml ps
python scripts/deploy_smoke.py
```
**Mong đợi:**
- `ps`: **9 container** đang chạy; `iuh_auth_service`, `iuh_kong_gateway`, `iuh_rabbitmq` hiện `healthy`.
- `deploy_smoke.py`: `TẤT CẢ ĐẠT (8 ca)`.
- Mở trình duyệt `http://localhost:5173`, đăng nhập thử.

**Nếu không:** `ps` thiếu container thì xem `docker logs <tên container>` (tên: `iuh_academic_chatbot_service`, `iuh_realtime_translation_service`, `iuh_flashcard_service`, `iuh_auth_service`, `iuh_kong_gateway`, `iuh_frontend`).
Smoke thất bại toàn bộ với `http=0` thì stack chưa lên xong, đợi thêm rồi chạy lại.

> **Đừng hoảng:** gọi `/api/v1/chat/health` hoặc `/api/v1/translate/health` mà **không có token** trả `401` là **đúng thiết kế**. Smoke test đã tính điều này.

### Bước 6 (tuỳ chọn). Đưa ra internet bằng Tailscale Funnel

**Hỏi chủ máy trước:** bước này làm dịch vụ **công khai**, ai có link đều vào được và tự đăng ký tài khoản (dùng quota LLM của bạn).

1. Cài [Tailscale](https://tailscale.com/download), đăng nhập.
2. Trang https://login.tailscale.com/admin/dns → **Enable HTTPS** (tên máy sẽ được ghi vào sổ chứng chỉ công khai và **không xóa được**; đặt tên trung tính trước: `tailscale set --hostname=<tên>`).
3. Bật Funnel (tài khoản chưa cho phép thì lệnh in link để bật):
   ```powershell
   & "C:\Program Files\Tailscale\tailscale.exe" funnel --bg 5173
   ```
4. Sửa `.env.prod`: `PUBLIC_ORIGIN` và `CORS_ALLOW_ORIGINS` = `https://<tên-máy>.<tailnet>.ts.net` (không có `/` cuối), rồi tạo lại container:
   ```powershell
   docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate
   ```
5. Kiểm tra từ điện thoại bằng **4G**, và: `python scripts/deploy_smoke.py --base https://<link-của-bạn>`.

**Tắt Funnel khi xong:** `& "C:\Program Files\Tailscale\tailscale.exe" funnel reset`.

## 4. Vận hành cơ bản

Đặt biến cho gọn: `$dc = "docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml"`

| Việc | Lệnh |
|---|---|
| Xem trạng thái | `Invoke-Expression "$dc ps"` |
| Xem log | `docker logs -f iuh_academic_chatbot_service` |
| Dừng (giữ dữ liệu) | `Invoke-Expression "$dc down"` (**không** thêm `-v`) |
| Chạy lại | `Invoke-Expression "$dc up -d"` |
| Áp dụng thay đổi `.env.prod` | `Invoke-Expression "$dc up -d --force-recreate <service>"` (**`docker restart` không nạp lại env**) |
| Cập nhật mã | `git pull` rồi `Invoke-Expression "$dc up -d --build"` |
| Xem VRAM | `nvidia-smi` |

## 5. Sự cố thường gặp

| Triệu chứng | Cách xử lý |
|---|---|
| `kong-gateway` thoát ngay, log nói về `JWT_SECRET_KEY` | Khóa < 32 ký tự, là giá trị mẫu, hoặc có ký tự `\| & \ "`. Sinh lại ở bước 3 |
| `could not select device driver "nvidia"` | Cài driver NVIDIA, bật WSL2 GPU cho Docker Desktop, thử lại `docker run --rm --gpus all ubuntu nvidia-smi` |
| Lỗi cú pháp `!override`/`!reset` | `docker compose version` < 2.24. Cập nhật Docker Desktop |
| `port is already allocated` | Cổng 5173/6379/9000... đang bị chương trình khác dùng. Dừng nó |
| Trình duyệt báo lỗi CORS | `PUBLIC_ORIGIN` không khớp địa chỉ trên thanh địa chỉ. Sửa rồi `up -d --force-recreate` |
| Chat chậm; log có `Falling back to Gemini` | `LLM_PROVIDER`/`REWRITER_PROVIDER` chưa là `gemini` trong `.env.prod` |
| Lỗi `429` / hết quota Gemini | Đợi một lúc, hoặc bật billing cho key, hoặc đặt `VOCAB_VERIFY_ENABLED=0` |
| Micro không hoạt động | Trình duyệt chỉ cho micro trên `localhost` hoặc HTTPS, không dùng được với `http://<IP-LAN>` |
| Hết ổ đĩa | `docker builder prune` (chỉ xóa cache build) |
| `CUDA out of memory`, hoặc container chatbot/realtime khởi động lại liên tục (card 6 GB) | Thêm `-f docker-compose.lowvram.yml` (xem phần "Card 6 GB"), rồi đóng ứng dụng dùng GPU khác |
| Chatbot crash `free(): double free detected` | Bạn đã ẩn GPU bằng `CUDA_VISIBLE_DEVICES`. Xóa biến đó, tạo lại container |

Bảng sự cố đầy đủ hơn nằm ở mục 8 của [DEPLOY.md](DEPLOY.md).

### Hai máy chạy song song (bản đầy đủ và bản tiết kiệm)

Dự án hiện có hai máy cùng chạy bản demo: một máy **8 GB** chạy bản đầy đủ (máy chính) và một máy **6 GB** chạy bản tiết kiệm (dự phòng, hoặc để thử).

| | Máy 8 GB (bản đầy đủ) | Máy 6 GB (bản tiết kiệm) |
|---|---|---|
| Lệnh chạy | `... -f docker-compose.yml -f docker-compose.prod.yml up -d` | thêm `-f docker-compose.lowvram.yml` **ở cuối** |
| Dịch realtime (NLLB) | GPU | CPU (chậm hơn) |
| Vai trò trong demo | **Máy chính**, và là máy dùng để test tải | Dự phòng; đo VRAM và độ trễ dịch trên CPU |

- **Chung:** dự án Supabase (cùng tài khoản và dữ liệu). **Riêng:** `JWT_SECRET_KEY`, mật khẩu RabbitMQ/MinIO, Redis, key LLM và link Funnel. Token đăng nhập của máy này không dùng được ở máy kia, người dùng chỉ cần đăng nhập lại.
- **Không** đặt `NLLB_DEVICE=cpu` trong `.env.prod`: Compose gốc đặt `NLLB_DEVICE: cuda` trong `environment` và nó thắng `env_file`. Chỉ có `-f docker-compose.lowvram.yml` mới có tác dụng. Máy 8 GB **không** được thêm file lowvram.
- Trước demo, cả hai máy chạy **cùng một commit hoặc tag** (`git pull` rồi so `git log --oneline -1`).
- Đừng để hai link Funnel cùng công khai cho người xem một lúc; chỉ bật link của máy dự phòng khi máy chính gặp sự cố.

## 6. Những điều KHÔNG được làm

- Không commit hay chia sẻ `.env.prod`; không dán nó vào chat, issue hay PR.
- Không `docker compose down -v` hay `docker system prune`.
- Không mở thêm cổng ra internet (RabbitMQ, Redis, MinIO đều chỉ nghe `127.0.0.1` và phải giữ như vậy).
- Không bật Funnel khi chưa hỏi chủ máy; không chạy test tải vào giờ demo (chung quota Gemini).
- Không đẩy thẳng lên `main`; thay đổi đi qua Pull Request.

## 7. Báo kết quả cho chủ dự án

Sau khi làm xong (hoặc kẹt), gửi đúng những thứ này (**không** gửi `.env.prod`):

```
1. Máy: hệ điều hành, GPU + VRAM, RAM
2. Nhánh đang dùng: (kết quả `git branch --show-current` và `git log --oneline -1`)
3. Bước đang làm / bước bị kẹt:
4. Kết quả `docker compose ... ps`:
5. Kết quả `python scripts/deploy_smoke.py`:
6. Nếu lỗi: ~30 dòng log cuối của container lỗi (đã xóa bí mật nếu có)
```

## 8. Những điều chưa được kiểm chứng

- Máy **không có GPU NVIDIA**; máy **6 GB VRAM thật** (mới đo mức dùng trên máy 8 GB, chưa chạy trên máy 6 GB, chưa đo độ trễ dịch khi NLLB chạy CPU); chatbot chạy CPU (sẽ crash nếu ẩn GPU).
- **Streaming (SSE)** và **IP thật của client** qua Funnel với nhiều người dùng cùng lúc.
- **Tải đồng thời**: cả stack đã dùng ~6,9/8,2 GB VRAM khi rảnh, chưa đo khi nhiều người dùng.
- Dùng **dự án Supabase riêng** (thứ tự chạy file SQL trong `db/` chưa được kiểm chứng).
- **Bật lại Dịch tài liệu** và **chế độ GPU** (vLLM/Ollama ở máy khác) sau khi merge.
- **CI trên `main` đang đỏ sẵn** ở job `realtime_translation_service` (4 test thiếu NLLB/Redis/NLTK trong môi trường CI), không do việc deploy.

## 9. Bản đồ file quan trọng

| File | Dùng để |
|---|---|
| `docker-compose.yml` | Định nghĩa chung các service (dùng cho dev) |
| `docker-compose.prod.yml` | Lớp phủ triển khai (dùng `.env.prod`, không mount mã nguồn, chỉ mở `127.0.0.1:5173`) |
| `docker-compose.lowvram.yml` | Lớp phủ tuỳ chọn cho card ~6 GB: chạy NLLB (dịch) trên CPU để tiết kiệm ~1,8 GB VRAM |
| `.env.prod.example` | Mẫu cấu hình; chép thành `.env.prod` |
| `gateway/kong.template.yml` | Cấu hình Kong (route, JWT, CORS, khóa doc-translation bằng 503) |
| `frontend/nginx.conf` | nginx của frontend: phục vụ giao diện, chuyển `/api` sang Kong, hỗ trợ streaming |
| `scripts/download_models.py` | Tải model ONNX vào `hf_models/` |
| `scripts/deploy_smoke.py` | Kiểm tra nhanh sau triển khai (8 ca, chỉ đọc) |
| `DEPLOY.md` | Tài liệu chi tiết: lý do thiết kế, kiến trúc, bảng sự cố đầy đủ |
| `README.md` mục 8.5 | Tóm tắt triển khai demo |
