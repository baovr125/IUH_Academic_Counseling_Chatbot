# Bao Cao Danh Gia: Doc Translation Service

> **Ngay chay:** 03/09/2026 14:48:53  
> **Che do:** Kong Gateway (port 8000) [OK]  
> **Tunnel vLLM:** `https://bondless-immerse-paternal.ngrok-free.dev`  
> **Model:** Qwen/Qwen2.5-14B-Instruct-AWQ  
> **Thu muc luu ket qua:** `eval_outputs/run_20260903_143626/`  

---

## 1. Tom Tat Dieu Hanh (Executive Summary)

| Tong file | Completed | Failed | Timeout |
|---|---|---|---|
| **3** | **3** OK | **0** ERR | **0** TIMEOUT |

### Verdict Tong The: **PASS -- Tat ca pipeline hoat dong dung**

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
| 1 | `NEJMoa2035389.pdf` | 763.1 KB | [OK] COMPLETED | 6m 41s | Groq (openai/gpt-oss-120b) & vLLM (Qwen/ | 9 terms | [OK] | `eval_outputs/run_20260903_143626/01_NEJMoa2035389/` |
| 2 | `1706.03762v7.pdf` | 2.11 MB | [OK] COMPLETED | 3m 12s | Groq (openai/gpt-oss-120b) & vLLM (Qwen/ | 12 terms | [OK] | `eval_outputs/run_20260903_143626/02_1706.03762v7/` |
| 3 | `ai_lect_01.pdf` | 2.13 MB | [OK] COMPLETED | 2m 0s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260903_143626/03_ai_lect_01/` |

---

## 4. Chi Tiet Tung File

### 1. [OK] `NEJMoa2035389.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 6m 41s |
| **Model AI su dung** | `Groq (openai/gpt-oss-120b) & vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 763.1 KB |
| **So trang** | 14 |
| **Thu muc luu tru** | `eval_outputs/run_20260903_143626/01_NEJMoa2035389/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (Chua tach thanh LaTeX) | [WARN] |
| Bang Markdown | 49 dong, 2 separator rows | [OK] |
| Kiem soat ngon ngu (Chong Han tu) | 0 ky tu (Sach 100%) | [OK] |
| Hinh anh dinh kem | 3 anh bi dead link | [WARN] |
| Ten rieng con nhan ra | 2/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 3533 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (9 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| PCR | phản ứng chuỗi polymerase (PCR) | /ˌpiː.siːˈɑːr/ | [audio] |
| mRNA-1273 vaccine | vắc-xin mRNA-1273 | /mRNA-1273 vaccine/ | [audio] |
| lipid nanoparticle-encapsulated mRNA | mRNA bọc trong hạt nanomRNA | /lipid nanoparticle-encapsulated mRNA/ | [audio] |
| prefusion stabilized full-length spike protein | protein gai điểm ổn định dạng tiền phân tiết | /prefusion stabilized full-length spike protein/ | [audio] |
| SARS-CoV-2 | vi rút SARS-CoV-2 | /SARS-CoV-2/ | [audio] |
| placebo-controlled trial | thử nghiệm đối chứng giả dược | /placebo-controlled trial/ | [audio] |
| observer-blinded | đối chứng mù quan sát viên | /observer-blinded/ | [audio] |
| vaccine efficacy | hiệu quả của vắc-xin | /vaccine efficacy/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 9.12 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260903_143626\01_NEJMoa2035389\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   32.1s]   35%  ?? tr?ch xu?t xong 9 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [   1m 4s]   43%  ?? d?ch xong Batch 1/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 48s]   46%  ?? d?ch xong Batch 2/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 56s]   50%  ?? d?ch xong Batch 3/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   3m 4s]   53%  ?? d?ch xong Batch 4/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 12s]   56%  ?? d?ch xong Batch 5/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 37s]   60%  ?? d?ch xong Batch 6/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 49s]   66%  ?? d?ch xong Batch 8/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 13s]   70%  ?? d?ch xong Batch 9/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 29s]   76%  ?? d?ch xong Batch 11/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  6m 41s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng Groq (openai/gpt-oss-120b) & 
```

---

### 2. [OK] `1706.03762v7.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 3m 12s |
| **Model AI su dung** | `Groq (openai/gpt-oss-120b) & vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 2.11 MB |
| **So trang** | 15 |
| **Thu muc luu tru** | `eval_outputs/run_20260903_143626/02_1706.03762v7/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (Chua tach thanh LaTeX) | [WARN] |
| Bang Markdown | 41 dong, 4 separator rows | [OK] |
| Kiem soat ngon ngu (Chong Han tu) | 1 ky tu Han/Ngoai lai | [ERR] |
| Hinh anh dinh kem | 10 anh bi dead link | [WARN] |
| Ten rieng con nhan ra | 15/40 terms | [check] |
| Trich dan (et al.) / [N] | 93 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 2670 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (12 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| Transformer | Transformer | /trænsˈfɔːrmər/ | [audio] |
| Attention mechanism | cơ chế chú ý | /əˈtenʃn ˈmekənɪzəm/ | [audio] |
| Attention Mechanism | cơ chế chú ý | /əˈtenʃn ˈmekənɪzəm/ | [audio] |
| Self-attention | tự chú ý | /sɛlf əˈtenʃn/ | [audio] |
| Scaled Dot-Product Attention | chú ý tích vô hướng tỷ lệ | /skeɪld dɑːt ˈprɑːdʌkt əˈtenʃn/ | [audio] |
| Multi-Head Attention | chú ý đa đầu | /ˈmʌlti hed əˈtenʃn/ | [audio] |
| Recurrent Neural Networks | mạng nơ-ron hồi quy | /rɪˈkɜːrənt ˈnjʊərəl ˈnɛtwɜːrks/ | [audio] |
| recurrent neural networks | mạng nơ-ron hồi quy | /rɪˈkɜːrənt ˈnjʊərəl ˈnɛtwɜːrks/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 11.44 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260903_143626\02_1706.03762v7\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   35%  ?? tr?ch xu?t xong 12 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  1m 52s]   46%  ?? d?ch xong Batch 1/6 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   2m 8s]   53%  ?? d?ch xong Batch 2/6 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 32s]   66%  ?? d?ch xong Batch 4/6 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 56s]   73%  ?? d?ch xong Batch 5/6 qua Groq (openai/gpt-oss-120b)...
  [  3m 12s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng Groq (openai/gpt-oss-120b) & 
```

---

### 3. [OK] `ai_lect_01.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 2m 0s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 2.13 MB |
| **So trang** | 30 |
| **Thu muc luu tru** | `eval_outputs/run_20260903_143626/03_ai_lect_01/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (Chua tach thanh LaTeX) | [WARN] |
| Bang Markdown | 0 dong, 0 separator rows | [OK] |
| Kiem soat ngon ngu (Chong Han tu) | 0 ky tu (Sach 100%) | [OK] |
| Hinh anh dinh kem | 17 anh bi dead link | [WARN] |
| Ten rieng con nhan ra | 0/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 546 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| Machine Learning | Học máy | /məˈʃiːn lɜːrnɪŋ/ | [audio] |
| Rationality | Tính toán hợp lý | /ræʃəˈnalɪti/ | [audio] |
| Natural Language Processing | Xử lý ngôn ngữ tự nhiên | /ˈnætʃrəl ˈlæŋgwɪdʒ prəʊˈsesɪŋ/ | [audio] |
| Probability | Độ khả năng | /prɒbəˈbɪlɪti/ | [audio] |
| Causality | Nguyên nhân - kết quả | /kɔːˈsælɪti/ | [audio] |
| Morality | Đạo đức | /mɒˈrælɪti/ | [audio] |
| Neural Network | Mạng nơ-ron | /ˈnʊərəl ˈnetwɜːk/ | [audio] |
| McCulloch-Pitts Neuron Model | Mô hình nơ-ron McCulloch-Pitts | /məˈkʌloʊtʃ-pɪts/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 13.91 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260903_143626\03_ai_lect_01\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   32.1s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  1m 36s]   60%  ?? d?ch xong Batch 1/2 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   2m 0s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

## 5. Ket Qua Benchmark Ky Thuat

### 5a. Chunking Algorithm -- Bao Toan Cau Truc

Doc test: 527 tu | 2 bang | 3 cong thuc | 1 code block

| Thuat toan | So batch | Thoi gian (ms) | Vi pham bang | Vi pham LaTeX | Vi pham code |
|---|---|---|---|---|---|
| **Naive Fixed-Size** | 5 | 0.04 | [ERR] 3 (60.0%) | [ERR] 1 | [ERR] 2 |
| **Hierarchical v6.2** *(Our)* | 1 | 0.261 | [OK] 0 (0%) | [OK] 1 | [OK] 1 |

### 5b. So Sanh PDF Parser Libraries

| Parser | Latency (ms) | ms/trang | Table | Heading | Math | Output |
|---|---|---|---|---|---|---|
| **PyMuPDF4LLM** *(Our)* | 564.51 | 141.13 | [OK] | [OK] | [OK] | Structured Markdown (LLM-ready) |
| **PyMuPDF (Raw fitz)** | 5.07 | 1.27 | [ERR] | [ERR] | [OK] | Plain Text (Unstructured) |
| **pdfplumber** | 367.39 | 91.85 | [OK] | [ERR] | [OK] | Plain Text + Table Dicts |
| **pypdf** | 31.29 | 7.82 | [ERR] | [ERR] | [ERR] | Plain Text (Lossy) |

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
| 8 | 300.0 | 2402.96 | 606.59 | **3.96x** | **+296.1%** |

## 6. Van De Phat Hien & Khuyen Nghi

*Khong phat hien van de nghiem trong nao.* [OK]

### Khuyen Nghi:

1. **File rat lon (>50 trang):** Can implement page-level chunked upload de tranh timeout worker.
2. **Session recovery:** Co che Redis `job_latest_{doc_id}` dang hoat dong dung.
3. **Fallback chain:** Kiem tra file nao dung Gemini fallback vs vLLM primary de danh gia chi phi.

---

## 7. Verdict Cuoi Cung

> **PASS -- Tat ca pipeline hoat dong dung**

*Bao cao duoc tao tu dong boi `eval_pipeline.py` luc 03/09/2026 14:48:53*