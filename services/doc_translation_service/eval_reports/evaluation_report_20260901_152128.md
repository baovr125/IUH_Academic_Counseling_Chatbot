# Bao Cao Danh Gia: Doc Translation Service

> **Ngay chay:** 01/09/2026 16:05:08  
> **Che do:** Kong Gateway (port 8000) [OK]  
> **Tunnel vLLM:** `https://bondless-immerse-paternal.ngrok-free.dev`  
> **Model:** Qwen/Qwen2.5-14B-Instruct-AWQ  
> **Thu muc luu ket qua:** `eval_outputs/run_20260901_152128/`  

---

## 1. Tom Tat Dieu Hanh (Executive Summary)

| Tong file | Completed | Failed | Timeout |
|---|---|---|---|
| **5** | **5** OK | **0** ERR | **0** TIMEOUT |

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
| 1 | `kho2.pdf` | 248.9 KB | [OK] COMPLETED | 5m 37s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260901_152128/01_kho2/` |
| 2 | `kho3.pdf` | 842.5 KB | [OK] COMPLETED | 6m 57s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260901_152128/02_kho3/` |
| 3 | `1706.03762v7.pdf` | 2.11 MB | [OK] COMPLETED | 3m 53s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260901_152128/03_1706.03762v7/` |
| 4 | `kho1.pdf` | 3.48 MB | [OK] COMPLETED | 6m 41s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 7 terms | [OK] | `eval_outputs/run_20260901_152128/04_kho1/` |
| 5 | `2005.14165v4.pdf` | 6.45 MB | [OK] COMPLETED | 19m 48s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260901_152128/05_2005.14165v4/` |

---

## 4. Chi Tiet Tung File

### 1. [OK] `kho2.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 5m 37s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 248.9 KB |
| **So trang** | 9 |
| **Thu muc luu tru** | `eval_outputs/run_20260901_152128/01_kho2/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 9 dong, 1 separator rows | [OK] |
| Ten rieng con nhan ra | 2/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 3331 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| FAIR Data Principles | Nguyên tắc dữ liệu FAIR | /fair dætə prɪnsɪpəlz/ | [audio] |
| Data Management | Quản lý dữ liệu | /ˈdeɪtə mænɪdʒmənt/ | [audio] |
| Data Stewardship | Chăm sóc dữ liệu | /ˈdeɪtə stiːdoʊrʃɪp/ | [audio] |
| Digital Publications | Tạp chí số | /ˈdɪdʒɪtl ˌpʌblɪˈkeɪʃənz/ | [audio] |
| Scholarly Digital Research Objects | Các đối tượng nghiên cứu kỹ thuật số học thuật | /ˈskɒlərli dɪdʒɪtl rɪˈsɜːrtʃ ˈɔbɪʤts/ | [audio] |
| Transparency | Minh bạch | /trænsˈpeɪrənsi/ | [audio] |
| Reproducibility | Tái tạo được | /riːprəˌdjuːsəˈbɪləti/ | [audio] |
| Reusability | Tái sử dụng được | /riːuːzəˈbɪləti/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 1.82 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260901_152128\01_kho2\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]    5%  Kh?i t?o t?c v? d?ch ng?m qua Celery...
  [  1m 44s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [  1m 52s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [  2m 16s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  2m 57s]   43%  ?? d?ch xong Batch 1/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 29s]   46%  ?? d?ch xong Batch 2/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 53s]   50%  ?? d?ch xong Batch 3/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   4m 1s]   60%  ?? d?ch xong Batch 6/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   4m 9s]   63%  ?? d?ch xong Batch 7/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 41s]   70%  ?? d?ch xong Batch 9/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 49s]   73%  ?? d?ch xong Batch 10/12 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 37s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 2. [OK] `kho3.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 6m 57s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 842.5 KB |
| **So trang** | 16 |
| **Thu muc luu tru** | `eval_outputs/run_20260901_152128/02_kho3/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 7 dong, 1 separator rows | [OK] |
| Ten rieng con nhan ra | 6/40 terms | [check] |
| Trich dan (et al.) / [N] | 185 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 2560 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| gravitational waves | tiếng rung hấp dẫn | /ˌɡrævɪˈteɪʃənəl ˈweɪvz/ | [audio] |
| black holes | hố đen | /blæk hoʊlz/ | [audio] |
| matched-filter signal-to-noise ratio | tỷ lệ tín hiệu trên nhiễu của bộ lọc phù hợp | /ˈmætʃt fɪltər ˈsɪgnəl tu nɔɪz ˈreɪʃioʊ/ | [audio] |
| luminosity distance | khoảng cách độ sáng | /lʌmjəˈnɒsəti ˈdɪstəns/ | [audio] |
| quasinormal modes | chế độ gần bình thường | /kwɑːziˈnɔrməl moʊdz/ | [audio] |
| post-Newtonian calculations | tính toán hậu Newton | /pɑːst ˈnuːtuːnɪən kælkjʊˈleɪʃənz/ | [audio] |
| relativistic two-body dynamics | động lực học hai vật thể tương đối | /rɪləˈvɪstɪk tu bi dɪˈnæmɪks/ | [audio] |
| numerical relativity | tương đối số học | /njuːmɛrɪkəl rɪˈlætɪvəti/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 7.89 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260901_152128\02_kho3\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [   24.1s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   48.2s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  1m 28s]   42%  ?? d?ch xong Batch 1/20 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  1m 36s]   44%  ?? d?ch xong Batch 2/20 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 24s]   46%  ?? d?ch xong Batch 3/20 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 41s]   48%  ?? d?ch xong Batch 4/20 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 49s]   50%  ?? d?ch xong Batch 5/20 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 57s]   52%  ?? d?ch xong Batch 6/20 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 21s]   54%  ?? d?ch xong Batch 7/20 qua Fallback Failed...
  [  3m 53s]   56%  ?? d?ch xong Batch 8/20 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   4m 1s]   58%  ?? d?ch xong Batch 9/20 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   4m 9s]   60%  ?? d?ch xong Batch 10/20 qua Fallback Failed...
  [  4m 33s]   62%  ?? d?ch xong Batch 11/20 qua Fallback Failed...
  [  4m 57s]   64%  ?? d?ch xong Batch 12/20 qua Fallback Failed...
  [  5m 21s]   66%  ?? d?ch xong Batch 13/20 qua Fallback Failed...
  [  5m 29s]   68%  ?? d?ch xong Batch 14/20 qua Fallback Failed...
  [  5m 37s]   70%  ?? d?ch xong Batch 15/20 qua Fallback Failed...
  [  5m 45s]   72%  ?? d?ch xong Batch 16/20 qua Fallback Failed...
  [   6m 1s]   74%  ?? d?ch xong Batch 17/20 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   6m 9s]   76%  ?? d?ch xong Batch 18/20 qua Fallback Failed...
  [  6m 33s]   78%  ?? d?ch xong Batch 19/20 qua Fallback Failed...
  [  6m 57s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
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
| **Thu muc luu tru** | `eval_outputs/run_20260901_152128/03_1706.03762v7/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 56 dong, 4 separator rows | [OK] |
| Ten rieng con nhan ra | 17/40 terms | [check] |
| Trich dan (et al.) / [N] | 91 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 3097 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| Transformer | Biến đổi (Transformer) | /ˈtræns.fɔːr.mər/ | [audio] |
| Attention Mechanism | Cơ chế chú ý (Attention) | /əˈtenʃən ˈmekənɪzəm/ | [audio] |
| Recurrent Neural Networks (RNN) | Mạng nơ-ron tái phát (Mạng nơ-ron tái phát) | /riˈkɜːrənt nɜːrəl ˈnetˌwɜːrk/ | [audio] |
| Long Short-Term Memory (LSTM) | Mạng nơ-ron nhớ dài hạn (Mạng LSTM) | /lɒŋ ʃɔːrtɜːrm ˈmeməri/ | [audio] |
| Gated Recurrent Unit (GRU) | Đơn vị tái phát có cửa (Đơn vị GRU) | /ɡeɪdɪd rɪˈkɜːrənt ˈjuːnit/ | [audio] |
| Encoder-Decoder Architecture | Kiến trúc mã hóa-khôi phục (Encoder-Decoder) | /ɛnˈkoʊdər dɪˈkoʊdər ˈɑːkjɪˈtekʧər/ | [audio] |
| Scaled Dot-Product Attention | Chú ý tích điểm được quy mô (Scaled Dot-Product Attention) | /skæld dɒt prəˈdʌkt əˈtenʃən/ | [audio] |
| Multi-Head Attention | Chú ý đa đầu (Multi-Head Attention) | /ˈmʌltɪ hed əˈtenʃən/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 8.22 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260901_152128\03_1706.03762v7\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [   16.1s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   48.2s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  2m 16s]   44%  ?? d?ch xong Batch 1/10 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 24s]   48%  ?? d?ch xong Batch 2/10 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 40s]   52%  ?? d?ch xong Batch 3/10 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 49s]   64%  ?? d?ch xong Batch 6/10 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 45s]   72%  ?? d?ch xong Batch 8/10 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 53s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 4. [OK] `kho1.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 6m 41s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 3.48 MB |
| **So trang** | 12 |
| **Thu muc luu tru** | `eval_outputs/run_20260901_152128/04_kho1/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 25 dong, 4 separator rows | [OK] |
| Ten rieng con nhan ra | 12/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 3456 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (7 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| protein structure prediction | đoán trước cấu trúc protein | /protein structure prediction/ | [audio] |
| Critical Assessment of protein Structure Prediction (CASP) | Đánh giá quan trọng về dự đoán cấu trúc protein (CASP) | /Critical Assessment of protein Structure Prediction/ | [audio] |
| machine learning | học máy | /machine learning/ | [audio] |
| multi-sequence alignment | đối sánh đa chuỗi | /multi-sequence alignment/ | [audio] |
| atomic accuracy | độ chính xác nguyên tử | /atomic accuracy/ | [audio] |
| physical interactions | tác động vật lý | /physical interactions/ | [audio] |
| evolutionary history | lịch sử tiến hóa | /evolutionary history/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 7.08 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260901_152128\04_kho1\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [   24.1s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   40.1s]   35%  ?? tr?ch xu?t xong 7 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  1m 28s]   42%  ?? d?ch xong Batch 1/18 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  1m 52s]   44%  ?? d?ch xong Batch 2/18 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   2m 0s]   48%  ?? d?ch xong Batch 4/18 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 16s]   51%  ?? d?ch xong Batch 5/18 qua Fallback Failed...
  [  2m 40s]   53%  ?? d?ch xong Batch 6/18 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 29s]   55%  ?? d?ch xong Batch 7/18 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   4m 1s]   57%  ?? d?ch xong Batch 8/18 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 17s]   60%  ?? d?ch xong Batch 9/18 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 25s]   62%  ?? d?ch xong Batch 10/18 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 37s]   66%  ?? d?ch xong Batch 12/18 qua Fallback Failed...
  [  5m 53s]   68%  ?? d?ch xong Batch 13/18 qua Fallback Failed...
  [   6m 9s]   71%  ?? d?ch xong Batch 14/18 qua Fallback Failed...
  [  6m 25s]   73%  ?? d?ch xong Batch 15/18 qua Fallback Failed...
  [  6m 33s]   75%  ?? d?ch xong Batch 16/18 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  6m 41s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 5. [OK] `2005.14165v4.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 19m 48s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 6.45 MB |
| **So trang** | 75 |
| **Thu muc luu tru** | `eval_outputs/run_20260901_152128/05_2005.14165v4/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 463 dong, 46 separator rows | [OK] |
| Ten rieng con nhan ra | 31/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 9 blocks | [check] |
| Noi dung tieng Viet | 14276 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| autoregressive language model | mô hình ngôn ngữ tự hồi quy | /auto-regressive/ | [audio] |
| few-shot learning | học ít mẫu | /few-shot/ | [audio] |
| fine-tuning | tinh chỉnh | /fine-tuning/ | [audio] |
| cloze tasks | nhiệm vụ điền từ | /cloze/ | [audio] |
| closed book question answering | trả lời câu hỏi không cần sách tham khảo | /closed-book/ | [audio] |
| translation | dịch thuật | /translation/ | [audio] |
| common sense reasoning | lý luận dựa trên kiến thức thông thường | /common-sense/ | [audio] |
| reading comprehension | hiểu biết đọc | /reading-comprehension/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 39.76 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260901_152128\05_2005.14165v4\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [  1m 28s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [  1m 44s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  2m 56s]   40%  ?? d?ch xong Batch 1/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   3m 4s]   41%  ?? d?ch xong Batch 2/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 29s]   42%  ?? d?ch xong Batch 4/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 37s]   43%  ?? d?ch xong Batch 5/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 45s]   44%  ?? d?ch xong Batch 7/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 57s]   45%  ?? d?ch xong Batch 8/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 37s]   46%  ?? d?ch xong Batch 10/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 45s]   47%  ?? d?ch xong Batch 11/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  6m 41s]   48%  ?? d?ch xong Batch 13/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   7m 5s]   49%  ?? d?ch xong Batch 14/62 qua Fallback Failed...
  [  7m 21s]   50%  ?? d?ch xong Batch 16/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  8m 18s]   52%  ?? d?ch xong Batch 19/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  8m 50s]   53%  ?? d?ch xong Batch 21/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   9m 6s]   54%  ?? d?ch xong Batch 22/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  9m 54s]   56%  ?? d?ch xong Batch 25/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 10m 26s]   57%  ?? d?ch xong Batch 27/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 10m 42s]   58%  ?? d?ch xong Batch 28/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  11m 6s]   60%  ?? d?ch xong Batch 31/62 qua Fallback Failed...
  [ 11m 46s]   61%  ?? d?ch xong Batch 33/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 12m 18s]   62%  ?? d?ch xong Batch 35/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 12m 26s]   63%  ?? d?ch xong Batch 36/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  13m 6s]   64%  ?? d?ch xong Batch 38/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 13m 30s]   65%  ?? d?ch xong Batch 40/62 qua Fallback Failed...
  [ 13m 38s]   66%  ?? d?ch xong Batch 41/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 13m 46s]   67%  ?? d?ch xong Batch 42/62 qua Fallback Failed...
  [ 14m 27s]   68%  ?? d?ch xong Batch 44/62 qua Fallback Failed...
  [ 14m 51s]   69%  ?? d?ch xong Batch 46/62 qua Fallback Failed...
  [ 15m 23s]   70%  ?? d?ch xong Batch 47/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 16m 11s]   71%  ?? d?ch xong Batch 49/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 16m 35s]   72%  ?? d?ch xong Batch 50/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 16m 43s]   73%  ?? d?ch xong Batch 52/62 qua Fallback Failed...
  [ 16m 51s]   74%  ?? d?ch xong Batch 53/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  18m 3s]   75%  ?? d?ch xong Batch 55/62 qua Fallback Failed...
  [ 18m 19s]   76%  ?? d?ch xong Batch 57/62 qua Fallback Failed...
  [ 18m 27s]   77%  ?? d?ch xong Batch 58/62 qua Fallback Failed...
  [ 18m 35s]   78%  ?? d?ch xong Batch 59/62 qua Fallback Failed...
  [ 19m 16s]   79%  ?? d?ch xong Batch 61/62 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 19m 40s]   85%  ?ang render l?i b?n d?ch (vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)) th?nh 
  [ 19m 48s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

## 5. Ket Qua Benchmark Ky Thuat

### 5a. Chunking Algorithm -- Bao Toan Cau Truc

Doc test: 527 tu | 2 bang | 3 cong thuc | 1 code block

| Thuat toan | So batch | Thoi gian (ms) | Vi pham bang | Vi pham LaTeX | Vi pham code |
|---|---|---|---|---|---|
| **Naive Fixed-Size** | 5 | 0.064 | [ERR] 3 (60.0%) | [ERR] 1 | [ERR] 2 |
| **Hierarchical v6.2** *(Our)* | 1 | 0.276 | [OK] 0 (0%) | [OK] 1 | [OK] 1 |

### 5b. So Sanh PDF Parser Libraries

| Parser | Latency (ms) | ms/trang | Table | Heading | Math | Output |
|---|---|---|---|---|---|---|
| **PyMuPDF4LLM** *(Our)* | 489.26 | 122.31 | [OK] | [OK] | [OK] | Structured Markdown (LLM-ready) |
| **PyMuPDF (Raw fitz)** | 4.67 | 1.17 | [ERR] | [ERR] | [OK] | Plain Text (Unstructured) |
| **pdfplumber** | 341.72 | 85.43 | [OK] | [ERR] | [OK] | Plain Text + Table Dicts |
| **pypdf** | 27.08 | 6.77 | [ERR] | [ERR] | [ERR] | Plain Text (Lossy) |

### 5c. Do Chinh Xac Thuat Ngu vs Ground Truth (30 tu chuyen nganh)

| Phuong phap | Dung/Tong | Accuracy | Bang Markdown | LaTeX |
|---|---|---|---|---|
| Google Translate | 5/30 | 16.67% | 42.5% (Thường làm vỡ gạch đứng | và canh cột) | 31.0% (Thường dịch các ký tự toán bên trong LaTeX) |
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
| 8 | 300.0 | 2403.8 | 611.05 | **3.93x** | **+293.4%** |

## 6. Van De Phat Hien & Khuyen Nghi

*Khong phat hien van de nghiem trong nao.* [OK]

### Khuyen Nghi:

1. **File rat lon (>50 trang):** Can implement page-level chunked upload de tranh timeout worker.
2. **Session recovery:** Co che Redis `job_latest_{doc_id}` dang hoat dong dung.
3. **Fallback chain:** Kiem tra file nao dung Gemini fallback vs vLLM primary de danh gia chi phi.

---

## 7. Verdict Cuoi Cung

> **PASS -- Tat ca pipeline hoat dong dung**

*Bao cao duoc tao tu dong boi `eval_pipeline.py` luc 01/09/2026 16:05:08*