# Bao Cao Danh Gia: Doc Translation Service

> **Ngay chay:** 07/09/2026 14:00:13  
> **Che do:** Kong Gateway (port 8000) [OK]  
> **Tunnel vLLM:** `https://bondless-immerse-paternal.ngrok-free.dev`  
> **Model:** Qwen/Qwen2.5-14B-Instruct-AWQ  
> **Thu muc luu ket qua:** `eval_outputs/run_20260907_135826/`  

---

## 1. Tom Tat Dieu Hanh (Executive Summary)

| Tong file | Completed | Failed | Timeout |
|---|---|---|---|
| **3** | **0** OK | **3** ERR | **0** TIMEOUT |

### Verdict Tong The: **FAIL -- Pipeline gap loi nghiem trong**

---

## 2. Trang Thai Ha Tang

| Thanh phan | Trang thai |
|---|---|
| Kong API Gateway (port 8000) | Kong Gateway (port 8000) [OK] |
| Kaggle vLLM Tunnel | [OK] Alive -- Qwen/Qwen2.5-14B-Instruct-AWQ |
| Tunnel URL | `https://bondless-immerse-paternal.ngrok-free.dev` |

---

## 3. Ket Qua Kiem Thu E2E -- Bang Tong Hop

| # | File | Kich thuoc | Ket qua | Thoi gian | Mo hinh AI | Glossary | PDF tai ve | Thu muc luu |
|---|---|---|---|---|---|---|---|---|
| 1 | `NEJMoa2035389.pdf` | 763.1 KB | [ERR] FAILED | 24.1s |  | 0 terms | [skip] | `eval_outputs/run_20260907_135826/01_NEJMoa2035389/` |
| 2 | `1706.03762v7.pdf` | 2.11 MB | [ERR] FAILED | 24.1s |  | 0 terms | [skip] | `eval_outputs/run_20260907_135826/02_1706.03762v7/` |
| 3 | `ai_lect_01.pdf` | 2.13 MB | [ERR] FAILED | 32.1s |  | 0 terms | [skip] | `eval_outputs/run_20260907_135826/03_ai_lect_01/` |

---

## 4. Chi Tiet Tung File

### 1. [ERR] `NEJMoa2035389.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [ERR] **FAILED** |
| **Thoi gian xu ly** | 24.1s |
| **Model AI su dung** | `` |
| **Kich thuoc file** | 763.1 KB |
| **So trang** | 0 |
| **Thu muc luu tru** | `eval_outputs/run_20260907_135826/01_NEJMoa2035389/` |

*Pipeline that bai: `Lỗi Marker Tunnel: HTTP 500 - Internal Server Error`*

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [   24.1s]    0%  Th?t b?i: L?i Marker Tunnel: HTTP 500 - Internal Server Error
```

---

### 2. [ERR] `1706.03762v7.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [ERR] **FAILED** |
| **Thoi gian xu ly** | 24.1s |
| **Model AI su dung** | `` |
| **Kich thuoc file** | 2.11 MB |
| **So trang** | 0 |
| **Thu muc luu tru** | `eval_outputs/run_20260907_135826/02_1706.03762v7/` |

*Pipeline that bai: `Lỗi Marker Tunnel: HTTP 500 - Internal Server Error`*

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [   24.1s]    0%  Th?t b?i: L?i Marker Tunnel: HTTP 500 - Internal Server Error
```

---

### 3. [ERR] `ai_lect_01.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [ERR] **FAILED** |
| **Thoi gian xu ly** | 32.1s |
| **Model AI su dung** | `` |
| **Kich thuoc file** | 2.13 MB |
| **So trang** | 0 |
| **Thu muc luu tru** | `eval_outputs/run_20260907_135826/03_ai_lect_01/` |

*Pipeline that bai: `Lỗi Marker Tunnel: HTTP 500 - Internal Server Error`*

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [   32.1s]    0%  Th?t b?i: L?i Marker Tunnel: HTTP 500 - Internal Server Error
```

---

## 5. Ket Qua Benchmark Ky Thuat

### 5a. Chunking Algorithm -- Bao Toan Cau Truc

Doc test: 527 tu | 2 bang | 3 cong thuc | 1 code block

| Thuat toan | So batch | Thoi gian (ms) | Vi pham bang | Vi pham LaTeX | Vi pham code |
|---|---|---|---|---|---|
| **Naive Fixed-Size** | 5 | 0.046 | [ERR] 3 (60.0%) | [ERR] 1 | [ERR] 2 |
| **Hierarchical v6.2** *(Our)* | 1 | 0.219 | [OK] 0 (0%) | [OK] 1 | [OK] 1 |

### 5b. So Sanh PDF Parser Libraries

| Parser | Latency (ms) | ms/trang | Table | Heading | Math | Output |
|---|---|---|---|---|---|---|
| **PyMuPDF4LLM** *(Our)* | 1215.83 | 303.96 | [OK] | [OK] | [OK] | Structured Markdown (LLM-ready) |
| **PyMuPDF (Raw fitz)** | 8.25 | 2.06 | [ERR] | [ERR] | [OK] | Plain Text (Unstructured) |
| **pdfplumber** | 713.9 | 178.48 | [OK] | [ERR] | [OK] | Plain Text + Table Dicts |
| **pypdf** | 71.66 | 17.92 | [ERR] | [ERR] | [ERR] | Plain Text (Lossy) |

### 5c. Do Chinh Xac Thuat Ngu vs Ground Truth (30 tu chuyen nganh)

| Phuong phap | Dung/Tong | Accuracy | Bang Markdown | LaTeX |
|---|---|---|---|---|
| Google Translate | 5/30 | 16.67% | 42.5% (Thường làm vỡ gạch đứng | và canh cột) | 31.0% (Thường dịch các ký tự toán bên trong LaTeX) |
| LLM thuan (khong Glossary) | 21/30 | 70.0% | 88.0% | 85.0% |
| **Pipeline cua nhom** *(Glossary Injection)* | 29/30 | **96.67%** | **100.0% (Bảo toàn nguyên vẹn cấu trúc 1 cột)** | **100.0% (Bảo toàn công thức nhờ Math Shielding)** |

**Vi du cu the:**

| Thuat ngu | Google Translate | Pipeline cua nhom |
|---|---|---|
| `Credits` | Tín dụng | Tín chỉ (Chuẩn IUH) |
| `Prerequisite course` | Điều kiện tiên quyết | Môn học tiên quyết |
| `Transcript` | Bản ghi âm / Tập lệnh | Bảng điểm |
| `Feature map` | Bản đồ tính năng | Bản đồ đặc trưng |
| `Pooling layer` | Lớp tổng hợp | Lớp gộp |
| `Deadlock` | Bế tắc / Đình trệ | Khóa chết luồng |
| `Attention mechanism` | Cơ chế tập trung | Cơ chế chú ý |

### 5d. Parallel vs Sequential Batch Translation

| So batch | Latency/batch (ms) | Sequential (ms) | Parallel (ms) | Speedup | Cai thien |
|---|---|---|---|---|---|
| 8 | 300.0 | 2402.24 | 612.84 | **3.92x** | **+292.0%** |

## 6. Van De Phat Hien & Khuyen Nghi

- [ERR] `NEJMoa2035389.pdf`: Pipeline that bai -- `Lỗi Marker Tunnel: HTTP 500 - Internal Server Error`
- [ERR] `1706.03762v7.pdf`: Pipeline that bai -- `Lỗi Marker Tunnel: HTTP 500 - Internal Server Error`
- [ERR] `ai_lect_01.pdf`: Pipeline that bai -- `Lỗi Marker Tunnel: HTTP 500 - Internal Server Error`

### Khuyen Nghi:

1. **File rat lon (>50 trang):** Can implement page-level chunked upload de tranh timeout worker.
2. **Session recovery:** Co che Redis `job_latest_{doc_id}` dang hoat dong dung.
3. **Fallback chain:** Kiem tra file nao dung Gemini fallback vs vLLM primary de danh gia chi phi.

---

## 7. Verdict Cuoi Cung

> **FAIL -- Pipeline gap loi nghiem trong**

*Bao cao duoc tao tu dong boi `eval_pipeline.py` luc 07/09/2026 14:00:13*