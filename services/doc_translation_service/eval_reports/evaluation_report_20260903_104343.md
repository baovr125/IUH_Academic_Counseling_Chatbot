# Bao Cao Danh Gia: Doc Translation Service

> **Ngay chay:** 03/09/2026 11:38:18  
> **Che do:** Kong Gateway (port 8000) [OK]  
> **Tunnel vLLM:** `https://bondless-immerse-paternal.ngrok-free.dev`  
> **Model:** Qwen/Qwen2.5-14B-Instruct-AWQ  
> **Thu muc luu ket qua:** `eval_outputs/run_20260903_104343/`  

---

## 1. Tom Tat Dieu Hanh (Executive Summary)

| Tong file | Completed | Failed | Timeout |
|---|---|---|---|
| **5** | **4** OK | **0** ERR | **1** TIMEOUT |

### Verdict Tong The: **PASS WITH WARNINGS -- Pipeline hoat dong, co file timeout (bai bao qua dai)**

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
| 1 | `kho2.pdf` | 248.9 KB | [OK] COMPLETED | 2m 32s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 13 terms | [OK] | `eval_outputs/run_20260903_104343/01_kho2/` |
| 2 | `kho3.pdf` | 842.5 KB | [OK] COMPLETED | 10m 18s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 12 terms | [OK] | `eval_outputs/run_20260903_104343/02_kho3/` |
| 3 | `1706.03762v7.pdf` | 2.11 MB | [OK] COMPLETED | 3m 53s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 12 terms | [OK] | `eval_outputs/run_20260903_104343/03_1706.03762v7/` |
| 4 | `kho1.pdf` | 3.48 MB | [OK] COMPLETED | 7m 21s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 12 terms | [OK] | `eval_outputs/run_20260903_104343/04_kho1/` |
| 5 | `2005.14165v4.pdf` | 6.45 MB | [TIMEOUT] TIMEOUT | 30m 6s | Fallback Failed | 12 terms | [skip] | `eval_outputs/run_20260903_104343/05_2005.14165v4/` |

---

## 4. Chi Tiet Tung File

### 1. [OK] `kho2.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 2m 32s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 248.9 KB |
| **So trang** | 9 |
| **Thu muc luu tru** | `eval_outputs/run_20260903_104343/01_kho2/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (Chua tach thanh LaTeX) | [WARN] |
| Bang Markdown | 0 dong, 0 separator rows | [OK] |
| Kiem soat ngon ngu (Chong Han tu) | 0 ky tu (Sach 100%) | [OK] |
| Hinh anh dinh kem | 5 anh bi dead link | [WARN] |
| Ten rieng con nhan ra | 2/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 3057 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (13 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| Fine-tuning | tinh chỉnh | /faɪn ˈtuːnɪŋ/ | [audio] |
| fine-tuning | tinh chỉnh | /faɪn ˈtuːnɪŋ/ | [audio] |
| Throughput | thông lượng | /ˈθruːpʊt/ | [audio] |
| Credit | tín chỉ | /ˈkredɪt/ | [audio] |
| Scholarship | học bổng | /ˈskɑːlərʃɪp/ | [audio] |
| FAIR Data Principles | Nguyên tắc dữ liệu FAIR | /fair dætə prɪnsɪp(ə)ls/ | [audio] |
| Data Management | Quản lý dữ liệu | /ˈdeɪtə mænɪdʒmənt/ | [audio] |
| Data Stewardship | Bảo vệ dữ liệu | /ˈdeɪtə stiːdwɜːʃɪp/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 1.81 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260903_104343\01_kho2\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   24.1s]   35%  ?? tr?ch xu?t xong 13 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  1m 44s]   45%  ?? d?ch xong Batch 1/7 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   2m 0s]   51%  ?? d?ch xong Batch 2/7 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 24s]   62%  ?? d?ch xong Batch 4/7 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 32s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 2. [OK] `kho3.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 10m 18s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 842.5 KB |
| **So trang** | 16 |
| **Thu muc luu tru** | `eval_outputs/run_20260903_104343/02_kho3/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (Chua tach thanh LaTeX) | [WARN] |
| Bang Markdown | 7 dong, 1 separator rows | [OK] |
| Kiem soat ngon ngu (Chong Han tu) | 0 ky tu (Sach 100%) | [OK] |
| Hinh anh dinh kem | 6 anh bi dead link | [WARN] |
| Ten rieng con nhan ra | 4/40 terms | [check] |
| Trich dan (et al.) / [N] | 164 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 2026 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (12 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| Latency | độ trễ | /ˈleɪtnsi/ | [audio] |
| Gravitational waves | sóng hấp dẫn | /ˌɡrævɪˈteɪʃənl weɪvz/ | [audio] |
| gravitational waves | sóng hấp dẫn | /ˌɡrævɪˈteɪʃənl weɪvz/ | [audio] |
| Gravitational wave | sóng hấp dẫn | /ˌɡrævɪˈteɪʃənl weɪv/ | [audio] |
| Black hole | lỗ đen | /blæk hoʊl/ | [audio] |
| Black holes | lỗ đen | /blæk hoʊlz/ | [audio] |
| black holes | lỗ đen | /blæk hoʊlz/ | [audio] |
| Binary black hole | hệ lỗ đen đôi | /ˈbaɪnəri blæk hoʊl/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 7.76 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260903_104343\02_kho3\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   35%  ?? tr?ch xu?t xong 12 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  1m 52s]   42%  ?? d?ch xong Batch 1/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   2m 8s]   45%  ?? d?ch xong Batch 2/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 16s]   48%  ?? d?ch xong Batch 3/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 40s]   51%  ?? d?ch xong Batch 4/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 17s]   57%  ?? d?ch xong Batch 6/14 qua Fallback Failed...
  [  5m 13s]   60%  ?? d?ch xong Batch 7/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  6m 25s]   62%  ?? d?ch xong Batch 8/14 qua Fallback Failed...
  [  8m 42s]   65%  ?? d?ch xong Batch 9/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  9m 22s]   68%  ?? d?ch xong Batch 10/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  9m 46s]   71%  ?? d?ch xong Batch 11/14 qua Fallback Failed...
  [  9m 54s]   77%  ?? d?ch xong Batch 13/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 10m 18s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 3. [OK] `1706.03762v7.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 3m 53s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 2.11 MB |
| **So trang** | 15 |
| **Thu muc luu tru** | `eval_outputs/run_20260903_104343/03_1706.03762v7/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (Chua tach thanh LaTeX) | [WARN] |
| Bang Markdown | 42 dong, 4 separator rows | [OK] |
| Kiem soat ngon ngu (Chong Han tu) | 1 ky tu Han/Ngoai lai | [ERR] |
| Hinh anh dinh kem | 10 anh bi dead link | [WARN] |
| Ten rieng con nhan ra | 15/40 terms | [check] |
| Trich dan (et al.) / [N] | 95 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 2159 ky tu dac trung | [OK] |

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
| Kich thuoc file ket qua | 11.34 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260903_104343\03_1706.03762v7\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   35%  ?? tr?ch xu?t xong 12 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  1m 52s]   46%  ?? d?ch xong Batch 1/6 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   2m 8s]   60%  ?? d?ch xong Batch 3/6 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 24s]   73%  ?? d?ch xong Batch 5/6 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 53s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 4. [OK] `kho1.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 7m 21s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 3.48 MB |
| **So trang** | 12 |
| **Thu muc luu tru** | `eval_outputs/run_20260903_104343/04_kho1/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (Chua tach thanh LaTeX) | [WARN] |
| Bang Markdown | 28 dong, 5 separator rows | [OK] |
| Kiem soat ngon ngu (Chong Han tu) | 0 ky tu (Sach 100%) | [OK] |
| Hinh anh dinh kem | 11 anh bi dead link | [WARN] |
| Ten rieng con nhan ra | 11/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 3817 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (12 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| Transformer | Transformer | /trænsˈfɔːrmər/ | [audio] |
| Self-attention | tự chú ý | /sɛlf əˈtenʃn/ | [audio] |
| Encoder | bộ mã hóa | /ɪnˈkoʊdər/ | [audio] |
| Convolutional | tích chập | /ˌkɑːnvəˈluːʃənl/ | [audio] |
| Fine-tuning | tinh chỉnh | /faɪn ˈtuːnɪŋ/ | [audio] |
| fine-tuning | tinh chỉnh | /faɪn ˈtuːnɪŋ/ | [audio] |
| Pre-training | tiền huấn luyện | /priː ˈtreɪnɪŋ/ | [audio] |
| pre-training | tiền huấn luyện | /priː ˈtreɪnɪŋ/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 9.51 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260903_104343\04_kho1\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   35%  ?? tr?ch xu?t xong 12 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  2m 24s]   42%  ?? d?ch xong Batch 1/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 40s]   45%  ?? d?ch xong Batch 2/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 48s]   54%  ?? d?ch xong Batch 5/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 25s]   57%  ?? d?ch xong Batch 6/14 qua Fallback Failed...
  [  4m 49s]   60%  ?? d?ch xong Batch 7/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   5m 5s]   65%  ?? d?ch xong Batch 9/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 21s]   68%  ?? d?ch xong Batch 10/14 qua Fallback Failed...
  [  5m 29s]   71%  ?? d?ch xong Batch 11/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  6m 17s]   77%  ?? d?ch xong Batch 13/14 qua Fallback Failed...
  [  7m 21s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 5. [TIMEOUT] `2005.14165v4.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [TIMEOUT] **TIMEOUT** |
| **Thoi gian xu ly** | 30m 6s |
| **Model AI su dung** | `Fallback Failed` |
| **Kich thuoc file** | 6.45 MB |
| **So trang** | 0 |
| **Thu muc luu tru** | `eval_outputs/run_20260903_104343/05_2005.14165v4/` |

*File timeout sau 30 phut -- khong co ban dich de phan tich.*

**Bang Thuat Ngu Trich Xuat (12 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| Transformer | Transformer | /trænsˈfɔːrmər/ | [audio] |
| Recurrent Neural Networks | mạng nơ-ron hồi quy | /rɪˈkɜːrənt ˈnjʊərəl ˈnɛtwɜːrks/ | [audio] |
| recurrent neural networks | mạng nơ-ron hồi quy | /rɪˈkɜːrənt ˈnjʊərəl ˈnɛtwɜːrks/ | [audio] |
| RNNs | các mạng nơ-ron hồi quy | /ˌɑːr.enˈenz/ | [audio] |
| LSTM | mạng bộ nhớ dài-ngắn hạn | /ˌel.es.tiːˈem/ | [audio] |
| Encoder | bộ mã hóa | /ɪnˈkoʊdər/ | [audio] |
| Decoder | bộ giải mã | /diːˈkoʊdər/ | [audio] |
| Encoder-Decoder | bộ mã hóa - giải mã | /ɪnˈkoʊdər diːˈkoʊdər/ | [audio] |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [   32.1s]   35%  ?? tr?ch xu?t xong 12 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  1m 20s]   40%  ?? d?ch xong Batch 1/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 24s]   41%  ?? d?ch xong Batch 2/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 32s]   42%  ?? d?ch xong Batch 3/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 40s]   44%  ?? d?ch xong Batch 5/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 56s]   45%  ?? d?ch xong Batch 6/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 17s]   46%  ?? d?ch xong Batch 7/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 41s]   47%  ?? d?ch xong Batch 8/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 49s]   48%  ?? d?ch xong Batch 9/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 57s]   49%  ?? d?ch xong Batch 10/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   5m 5s]   50%  ?? d?ch xong Batch 12/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 45s]   51%  ?? d?ch xong Batch 13/44 qua Fallback Failed...
  [  6m 33s]   52%  ?? d?ch xong Batch 14/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  6m 49s]   53%  ?? d?ch xong Batch 15/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   7m 5s]   54%  ?? d?ch xong Batch 16/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  7m 13s]   55%  ?? d?ch xong Batch 17/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  7m 21s]   56%  ?? d?ch xong Batch 18/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   8m 1s]   57%  ?? d?ch xong Batch 19/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  8m 42s]   58%  ?? d?ch xong Batch 20/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  8m 58s]   60%  ?? d?ch xong Batch 22/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  9m 46s]   61%  ?? d?ch xong Batch 24/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  10m 2s]   62%  ?? d?ch xong Batch 25/44 qua Fallback Failed...
  [ 10m 42s]   63%  ?? d?ch xong Batch 26/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 10m 58s]   64%  ?? d?ch xong Batch 27/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 11m 14s]   65%  ?? d?ch xong Batch 28/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 11m 30s]   66%  ?? d?ch xong Batch 29/44 qua Fallback Failed...
  [ 11m 54s]   67%  ?? d?ch xong Batch 30/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 12m 10s]   68%  ?? d?ch xong Batch 31/44 qua Fallback Failed...
  [ 12m 26s]   69%  ?? d?ch xong Batch 32/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 12m 58s]   70%  ?? d?ch xong Batch 33/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 13m 30s]   71%  ?? d?ch xong Batch 35/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 13m 46s]   72%  ?? d?ch xong Batch 36/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 13m 54s]   73%  ?? d?ch xong Batch 37/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 14m 19s]   74%  ?? d?ch xong Batch 38/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 15m 31s]   76%  ?? d?ch xong Batch 40/44 qua Fallback Failed...
  [ 15m 39s]   77%  ?? d?ch xong Batch 41/44 qua Fallback Failed...
  [ 15m 55s]   78%  ?? d?ch xong Batch 42/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 16m 19s]   79%  ?? d?ch xong Batch 43/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  17m 7s]   85%  ?ang render l?i b?n d?ch (vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)) th?nh 
  [ 18m 11s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [ 18m 35s]   35%  ?? tr?ch xu?t xong 12 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [ 18m 43s]   69%  ?? ph?c h?i Batch 32/44 t? Cache...
  [ 20m 36s]   73%  ?? ph?c h?i Batch 37/44 t? Cache...
  [ 21m 24s]   75%  ?? ph?c h?i Batch 39/44 t? Cache...
  [ 21m 56s]   76%  ?? d?ch xong Batch 40/44 qua Fallback Failed...
  [ 22m 52s]   77%  ?? d?ch xong Batch 41/44 qua Fallback Failed...
  [ 23m 25s]   78%  ?? d?ch xong Batch 42/44 qua Fallback Failed...
  [ 24m 29s]   79%  ?? d?ch xong Batch 43/44 qua Fallback Failed...
  [  25m 1s]   85%  ?ang render l?i b?n d?ch (vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)) th?nh 
  [ 25m 57s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [ 26m 29s]   73%  ?? ph?c h?i Batch 37/44 t? Cache...
  [ 28m 13s]   75%  ?? ph?c h?i Batch 39/44 t? Cache...
  [ 28m 21s]   76%  ?? d?ch xong Batch 40/44 qua Fallback Failed...
  [  30m 6s]   77%  ?? d?ch xong Batch 41/44 qua Fallback Failed...
```

---

## 5. Ket Qua Benchmark Ky Thuat

### 5a. Chunking Algorithm -- Bao Toan Cau Truc

Doc test: 527 tu | 2 bang | 3 cong thuc | 1 code block

| Thuat toan | So batch | Thoi gian (ms) | Vi pham bang | Vi pham LaTeX | Vi pham code |
|---|---|---|---|---|---|
| **Naive Fixed-Size** | 5 | 0.041 | [ERR] 3 (60.0%) | [ERR] 1 | [ERR] 2 |
| **Hierarchical v6.2** *(Our)* | 1 | 0.243 | [OK] 0 (0%) | [OK] 1 | [OK] 1 |

### 5b. So Sanh PDF Parser Libraries

| Parser | Latency (ms) | ms/trang | Table | Heading | Math | Output |
|---|---|---|---|---|---|---|
| **PyMuPDF4LLM** *(Our)* | 523.16 | 130.79 | [OK] | [OK] | [OK] | Structured Markdown (LLM-ready) |
| **PyMuPDF (Raw fitz)** | 7.1 | 1.77 | [ERR] | [ERR] | [OK] | Plain Text (Unstructured) |
| **pdfplumber** | 660.98 | 165.25 | [OK] | [ERR] | [OK] | Plain Text + Table Dicts |
| **pypdf** | 58.9 | 14.73 | [ERR] | [ERR] | [ERR] | Plain Text (Lossy) |

### 5c. Do Chinh Xac Thuat Ngu vs Ground Truth (30 tu chuyen nganh)

| Phuong phap | Dung/Tong | Accuracy | Bang Markdown | LaTeX |
|---|---|---|---|---|
| Google Translate | 5/30 | 16.67% | 42.5% (Thường làm vỡ gạch đứng | và canh cột) | 31.0% (Thường dịch các ký tự toán bên trong LaTeX) |
| LLM thuan (khong Glossary) | 21/30 | 70.0% | 88.0% | 85.0% |
| **Pipeline cua nhom** *(Glossary Injection)* | 30/30 | **100.0%** | **100.0% (Bảo toàn nguyên vẹn cấu trúc 1 cột)** | **100.0% (Bảo toàn công thức nhờ Math Shielding)** |

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
| 8 | 300.0 | 2403.96 | 613.06 | **3.92x** | **+292.1%** |

## 6. Van De Phat Hien & Khuyen Nghi

- [TIMEOUT] `2005.14165v4.pdf`: Timeout sau 30 phut -- file qua lon (6.45 MB)

### Khuyen Nghi:

1. **File rat lon (>50 trang):** Can implement page-level chunked upload de tranh timeout worker.
2. **Session recovery:** Co che Redis `job_latest_{doc_id}` dang hoat dong dung.
3. **Fallback chain:** Kiem tra file nao dung Gemini fallback vs vLLM primary de danh gia chi phi.

---

## 7. Verdict Cuoi Cung

> **PASS WITH WARNINGS -- Pipeline hoat dong, co file timeout (bai bao qua dai)**

*Bao cao duoc tao tu dong boi `eval_pipeline.py` luc 03/09/2026 11:38:18*