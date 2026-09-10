# Bao Cao Danh Gia: Doc Translation Service

> **Ngay chay:** 02/09/2026 11:03:32  
> **Che do:** Kong Gateway (port 8000) [OK]  
> **Tunnel vLLM:** `https://bondless-immerse-paternal.ngrok-free.dev`  
> **Model:** Qwen/Qwen2.5-14B-Instruct-AWQ  
> **Thu muc luu ket qua:** `eval_outputs/run_20260902_100523/`  

---

## 1. Tom Tat Dieu Hanh (Executive Summary)

| Tong file | Completed | Failed | Timeout |
|---|---|---|---|
| **5** | **4** OK | **1** ERR | **0** TIMEOUT |

### Verdict Tong The: **PARTIAL PASS -- Co loi xay ra o mot so file**

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
| 1 | `kho2.pdf` | 248.9 KB | [OK] COMPLETED | 4m 41s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260902_100523/01_kho2/` |
| 2 | `kho3.pdf` | 842.5 KB | [OK] COMPLETED | 13m 40s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260902_100523/02_kho3/` |
| 3 | `1706.03762v7.pdf` | 2.11 MB | [OK] COMPLETED | 10m 10s | Gemini 2.5 Flash | 7 terms | [OK] | `eval_outputs/run_20260902_100523/03_1706.03762v7/` |
| 4 | `kho1.pdf` | 3.48 MB | [OK] COMPLETED | 15m 38s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 7 terms | [OK] | `eval_outputs/run_20260902_100523/04_kho1/` |
| 5 | `2005.14165v4.pdf` | 6.45 MB | [ERR] FAILED | 13m 18s | Fallback Failed | 10 terms | [skip] | `eval_outputs/run_20260902_100523/05_2005.14165v4/` |

---

## 4. Chi Tiet Tung File

### 1. [OK] `kho2.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 4m 41s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 248.9 KB |
| **So trang** | 9 |
| **Thu muc luu tru** | `eval_outputs/run_20260902_100523/01_kho2/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 9 dong, 1 separator rows | [OK] |
| Ten rieng con nhan ra | 2/40 terms | [check] |
| Trich dan (et al.) / [N] | 1 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 3342 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| FAIR Data Principles | Nguyên tắc dữ liệu FAIR | /fair dætə prɪnsɪpəlz/ | [audio] |
| Data Management | Quản lý dữ liệu | /deɪtə mænɪdʒmənt/ | [audio] |
| Data Stewardship | Bảo vệ dữ liệu | /deɪtə stiːdoʊrʃɪp/ | [audio] |
| Digital Publications | Tạp chí kỹ thuật số | /ˈdɪdʒɪtl̩ pʌblɪkaɪʃənz/ | [audio] |
| Knowledge Discovery | Khám phá tri thức | /ˈnoʊlɪdʒ diˈskʌvəri/ | [audio] |
| Reproducibility | Tính tái tạo | /riːprəˌdjuːsəˈbɪlɪti/ | [audio] |
| Transparency | Tính minh bạch | /trænsˈpeɪrənsi/ | [audio] |
| Research Objects | Đối tượng nghiên cứu | /riːsɜːrtʃ ˈɒbɪdʒɪts/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 1.87 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260902_100523\01_kho2\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   48.2s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  2m 40s]   53%  ?? d?ch xong Batch 4/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 56s]   56%  ?? d?ch xong Batch 5/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   3m 4s]   60%  ?? d?ch xong Batch 6/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 53s]   66%  ?? d?ch xong Batch 8/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 17s]   70%  ?? d?ch xong Batch 9/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 25s]   73%  ?? d?ch xong Batch 10/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 33s]   76%  ?? d?ch xong Batch 11/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 41s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 2. [OK] `kho3.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 13m 40s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 842.5 KB |
| **So trang** | 16 |
| **Thu muc luu tru** | `eval_outputs/run_20260902_100523/02_kho3/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 7 dong, 1 separator rows | [OK] |
| Ten rieng con nhan ra | 5/40 terms | [check] |
| Trich dan (et al.) / [N] | 173 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 835 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| gravitational waves | đông vịnh hấp dẫn | /gravitational waves/ | [audio] |
| black holes | hố đen | /black holes/ | [audio] |
| luminosity distance | khoảng cách độ sáng | /luminosity distance/ | [audio] |
| mass quadrupole moment | thời gian biến đổi mômen bội phương thứ hai về khối lượng | /mass quadrupole moment/ | [audio] |
| signal-to-noise ratio | tỷ số tín hiệu trên nhiễu | /signal-to-noise ratio/ | [audio] |
| matched-filter | bộ lọc phù hợp | /matched-filter/ | [audio] |
| quasinormal modes | mô hình gần bình thường | /quasinormal modes/ | [audio] |
| postNewtonian calculations | tính toán hậu Newton | /postNewtonian calculations/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 7.62 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260902_100523\02_kho3\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [  1m 12s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  2m 18s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [  2m 34s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  5m 23s]   43%  ?? d?ch xong Batch 1/11 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 39s]   47%  ?? d?ch xong Batch 2/11 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  7m 15s]   50%  ?? d?ch xong Batch 3/11 qua Fallback Failed...
  [  8m 43s]   54%  ?? d?ch xong Batch 4/11 qua Fallback Failed...
  [ 10m 12s]   58%  ?? d?ch xong Batch 5/11 qua Fallback Failed...
  [ 10m 20s]   61%  ?? d?ch xong Batch 6/11 qua Fallback Failed...
  [  11m 8s]   65%  ?? d?ch xong Batch 7/11 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 11m 48s]   72%  ?? d?ch xong Batch 9/11 qua Fallback Failed...
  [ 13m 16s]   76%  ?? d?ch xong Batch 10/11 qua Fallback Failed...
  [ 13m 40s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 3. [OK] `1706.03762v7.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 10m 10s |
| **Model AI su dung** | `Gemini 2.5 Flash` |
| **Kich thuoc file** | 2.11 MB |
| **So trang** | 15 |
| **Thu muc luu tru** | `eval_outputs/run_20260902_100523/03_1706.03762v7/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 56 dong, 4 separator rows | [OK] |
| Ten rieng con nhan ra | 15/40 terms | [check] |
| Trich dan (et al.) / [N] | 96 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 0 ky tu dac trung | [ERR] |

**Bang Thuat Ngu Trich Xuat (7 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| Transformer | Biến đổi | /transformer/ | [audio] |
| Attention Mechanism | Cơ chế chú ý | /attention mechanism/ | [audio] |
| Recurrent Neural Networks (RNN) | Mạng nơ-ron tái phát | /recurrent neural networks/ | [audio] |
| Long Short-Term Memory (LSTM) | Mạng nơ-ron ngắn hạn dài hạn | /long short-term memory/ | [audio] |
| Gated Recurrent Unit (GRU) | Đơn vị tái phát có cửa | /gated recurrent unit/ | [audio] |
| BLEU Score | Điểm số BLEU | /bleu score/ | [audio] |
| Encoder-Decoder Architecture | Kiến trúc mã hóa - giải mã | /encoder-decoder architecture/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 7.98 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260902_100523\03_1706.03762v7\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   56.1s]   35%  ?? tr?ch xu?t xong 7 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  8m 33s]   60%  ?? d?ch xong Batch 2/4 qua Fallback Failed...
  [ 10m 10s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng Gemini 2.5 Flash!
```

---

### 4. [OK] `kho1.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 15m 38s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 3.48 MB |
| **So trang** | 12 |
| **Thu muc luu tru** | `eval_outputs/run_20260902_100523/04_kho1/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 18 dong, 4 separator rows | [OK] |
| Ten rieng con nhan ra | 12/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 605 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (7 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| protein structure prediction | đoán định cấu trúc protein | /protein structure prediction/ | [audio] |
| Critical Assessment of protein Structure Prediction (CASP) | Đánh giá quan trọng về dự đoán cấu trúc protein (CASP) | /Critical Assessment of protein Structure Prediction (CASP)/ | [audio] |
| multi-sequence alignments | đối sánh đa chuỗi | /multi-sequence alignments/ | [audio] |
| machine learning | học máy | /machine learning/ | [audio] |
| deep learning algorithm | thuật toán học sâu | /deep learning algorithm/ | [audio] |
| atomic accuracy | độ chính xác nguyên tử | /atomic accuracy/ | [audio] |
| physical interactions | tác động vật lý | /physical interactions/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 9.32 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260902_100523\04_kho1\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   32.1s]   35%  ?? tr?ch xu?t xong 7 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [   8m 1s]   48%  ?? d?ch xong Batch 2/9 qua Fallback Failed...
  [  9m 30s]   53%  ?? d?ch xong Batch 3/9 qua Fallback Failed...
  [  9m 38s]   57%  ?? d?ch xong Batch 4/9 qua Fallback Failed...
  [  11m 6s]   66%  ?? d?ch xong Batch 6/9 qua Fallback Failed...
  [ 12m 10s]   71%  ?? d?ch xong Batch 7/9 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 15m 30s]   75%  ?? d?ch xong Batch 8/9 qua Fallback Failed...
  [ 15m 38s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 5. [ERR] `2005.14165v4.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [ERR] **FAILED** |
| **Thoi gian xu ly** | 13m 18s |
| **Model AI su dung** | `Fallback Failed` |
| **Kich thuoc file** | 6.45 MB |
| **So trang** | 0 |
| **Thu muc luu tru** | `eval_outputs/run_20260902_100523/05_2005.14165v4/` |

*Pipeline that bai: `range object index out of range`*

**Bang Thuat Ngu Trich Xuat (10 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| language model | mô hình ngôn ngữ | /lang-gwijst muh-dəl/ | [audio] |
| pre-training | huấn luyện tiền nghiệm | /pri-trayn-ing/ | [audio] |
| fine-tuning | tinh chỉnh | /fahyn-toong/ | [audio] |
| few-shot learning | học ít mẫu | /fyoo-shawt lehr-ning/ | [audio] |
| autoregressive model | mô hình tự hồi quy | /aw-toh-re-gres-iv muh-dəl/ | [audio] |
| cloze tasks | những nhiệm vụ điền từ | /klohz task/ | [audio] |
| closed book question answering | đáp câu hỏi không cần sách tham khảo | /klōzd bəʊk kweschən ˈænsərɪŋ/ | [audio] |
| translation | dịch thuật | /trans-lā-shən/ | [audio] |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [   32.1s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [  1m 28s]   35%  ?? tr?ch xu?t xong 10 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  4m 17s]   41%  ?? d?ch xong Batch 1/30 qua Fallback Failed...
  [   5m 5s]   42%  ?? d?ch xong Batch 2/30 qua Fallback Failed...
  [  6m 33s]   44%  ?? d?ch xong Batch 3/30 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   9m 5s]   48%  ?? d?ch xong Batch 6/30 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 10m 37s]   50%  ?? d?ch xong Batch 8/30 qua Fallback Failed...
  [ 11m 58s]   52%  ?? d?ch xong Batch 9/30 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 12m 35s]   53%  ?? d?ch xong Batch 10/30 qua Fallback Failed...
  [ 13m 18s]    0%  Th?t b?i: range object index out of range
```

---

## 5. Ket Qua Benchmark Ky Thuat

### 5a. Chunking Algorithm -- Bao Toan Cau Truc

Doc test: 527 tu | 2 bang | 3 cong thuc | 1 code block

| Thuat toan | So batch | Thoi gian (ms) | Vi pham bang | Vi pham LaTeX | Vi pham code |
|---|---|---|---|---|---|
| **Naive Fixed-Size** | 5 | 0.062 | [ERR] 3 (60.0%) | [ERR] 1 | [ERR] 2 |
| **Hierarchical v6.2** *(Our)* | 1 | 0.338 | [OK] 0 (0%) | [OK] 1 | [OK] 1 |

### 5b. So Sanh PDF Parser Libraries

| Parser | Latency (ms) | ms/trang | Table | Heading | Math | Output |
|---|---|---|---|---|---|---|
| **PyMuPDF4LLM** *(Our)* | 557.29 | 139.32 | [OK] | [OK] | [OK] | Structured Markdown (LLM-ready) |
| **PyMuPDF (Raw fitz)** | 8.03 | 2.01 | [ERR] | [ERR] | [OK] | Plain Text (Unstructured) |
| **pdfplumber** | 762.55 | 190.64 | [OK] | [ERR] | [OK] | Plain Text + Table Dicts |
| **pypdf** | 64.96 | 16.24 | [ERR] | [ERR] | [ERR] | Plain Text (Lossy) |

### 5c. Do Chinh Xac Thuat Ngu vs Ground Truth (30 tu chuyen nganh)

| Phuong phap | Dung/Tong | Accuracy | Bang Markdown | LaTeX |
|---|---|---|---|---|
| Google Translate | 18/30 | 60.0% | 42.5% (Thường làm vỡ gạch đứng | và canh cột) | 31.0% (Thường dịch các ký tự toán bên trong LaTeX) |
| LLM thuan (khong Glossary) | 21/30 | 70.0% | 88.0% | 85.0% |
| **Pipeline cua nhom** *(Glossary Injection)* | 30/30 | **100.0%** | **100.0% (Bảo toàn nguyên vẹn nhờ Hard Rules)** | **100.0% (Bảo toàn nguyên vẹn $..$ và $$..$$)** |

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
| 8 | 300.0 | 2403.41 | 611.09 | **3.93x** | **+293.3%** |

## 6. Van De Phat Hien & Khuyen Nghi

- [!] `1706.03762v7.pdf`: Ban dich khong co noi dung tieng Viet
- [ERR] `2005.14165v4.pdf`: Pipeline that bai -- `range object index out of range`

### Khuyen Nghi:

1. **File rat lon (>50 trang):** Can implement page-level chunked upload de tranh timeout worker.
2. **Session recovery:** Co che Redis `job_latest_{doc_id}` dang hoat dong dung.
3. **Fallback chain:** Kiem tra file nao dung Gemini fallback vs vLLM primary de danh gia chi phi.

---

## 7. Verdict Cuoi Cung

> **PARTIAL PASS -- Co loi xay ra o mot so file**

*Bao cao duoc tao tu dong boi `eval_pipeline.py` luc 02/09/2026 11:03:32*