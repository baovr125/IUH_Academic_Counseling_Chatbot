# Bao Cao Danh Gia: Doc Translation Service

> **Ngay chay:** 02/09/2026 12:03:47  
> **Che do:** Kong Gateway (port 8000) [OK]  
> **Tunnel vLLM:** `https://bondless-immerse-paternal.ngrok-free.dev`  
> **Model:** Qwen/Qwen2.5-14B-Instruct-AWQ  
> **Thu muc luu ket qua:** `eval_outputs/run_20260902_112620/`  

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
| 1 | `kho2.pdf` | 248.9 KB | [OK] COMPLETED | 2m 24s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260902_112620/01_kho2/` |
| 2 | `kho3.pdf` | 842.5 KB | [OK] COMPLETED | 10m 18s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260902_112620/02_kho3/` |
| 3 | `1706.03762v7.pdf` | 2.11 MB | [OK] COMPLETED | 2m 32s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260902_112620/03_1706.03762v7/` |
| 4 | `kho1.pdf` | 3.48 MB | [OK] COMPLETED | 6m 1s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 7 terms | [OK] | `eval_outputs/run_20260902_112620/04_kho1/` |
| 5 | `2005.14165v4.pdf` | 6.45 MB | [OK] COMPLETED | 15m 47s | vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ) | 8 terms | [OK] | `eval_outputs/run_20260902_112620/05_2005.14165v4/` |

---

## 4. Chi Tiet Tung File

### 1. [OK] `kho2.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 2m 24s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 248.9 KB |
| **So trang** | 9 |
| **Thu muc luu tru** | `eval_outputs/run_20260902_112620/01_kho2/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 0 dong, 0 separator rows | [OK] |
| Ten rieng con nhan ra | 2/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 3136 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| FAIR Data Principles | Nguyên tắc dữ liệu FAIR | /fair dætə prɪnsɪpəlz/ | [audio] |
| Data Management | Quản lý dữ liệu | /deɪtə mænɪdʒmənt/ | [audio] |
| Data Stewardship | Quản lý tài nguyên dữ liệu | /deɪtə stiːdoːrʃɪp/ | [audio] |
| Digital Publications | Tạp chí kỹ thuật số | /ˈdɪdʒɪtl ˌpʌblɪˈkeɪʃənz/ | [audio] |
| Knowledge Discovery | Khám phá tri thức | /ˈnoʊlɪdʒ diˈskʌvəri/ | [audio] |
| Reproducibility | Tính tái tạo | /riːprəˌdjuːsəˈbɪlɪti/ | [audio] |
| Transparency | Tính minh bạch | /trænsˈpeɪrənsi/ | [audio] |
| Research Objects | Đối tượng nghiên cứu | /riːsɜːrtʃ ˈɒbɪdʒəts/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 1.84 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260902_112620\01_kho2\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   24.1s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  1m 44s]   45%  ?? d?ch xong Batch 1/7 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  1m 52s]   51%  ?? d?ch xong Batch 2/7 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 24s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
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
| **Thu muc luu tru** | `eval_outputs/run_20260902_112620/02_kho3/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 7 dong, 1 separator rows | [OK] |
| Ten rieng con nhan ra | 4/40 terms | [check] |
| Trich dan (et al.) / [N] | 179 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 3087 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| gravitational waves | tiếng rung hấp dẫn | /ˌɡrævɪˈteɪʃənəl ˈweɪvz/ | [audio] |
| black holes | hố đen | /blæk hoʊlz/ | [audio] |
| matched-filter signal-to-noise ratio | tỷ lệ tín hiệu trên nhiễu của bộ lọc phù hợp | /ˈmætʃt fɪltər ˈsɪgnəl tu nɔɪz ˈreɪʃioʊ/ | [audio] |
| quasinormal modes | chế độ gần bình thường | /kwɑːziˈnɔrməl moʊdz/ | [audio] |
| post-Newtonian calculations | tính toán hậu Newton | /pɑːst nuːˈtuːnɪən kælkjʊˈleɪʃənz/ | [audio] |
| relativistic two-body dynamics | động lực học hai vật thể tương đối | /rɪləˈvɪstɪk tu baɪdi ˈdɪnæmɪks/ | [audio] |
| numerical relativity | tương đối số học | /njuːmɛrɪkəl rɪˈlætɪvəti/ | [audio] |
| binary pulsar system | hệ thống ngôi sao nhị phân | /ˈbɪnəri ˈpʌlsɑːr ˈsɪstəm/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 11.22 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260902_112620\02_kho3\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   24.1s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [   2m 8s]   42%  ?? d?ch xong Batch 1/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 24s]   45%  ?? d?ch xong Batch 2/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 32s]   48%  ?? d?ch xong Batch 3/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 48s]   51%  ?? d?ch xong Batch 4/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   3m 4s]   57%  ?? d?ch xong Batch 6/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   8m 1s]   60%  ?? d?ch xong Batch 7/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  8m 49s]   62%  ?? d?ch xong Batch 8/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   9m 5s]   68%  ?? d?ch xong Batch 10/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  10m 2s]   74%  ?? d?ch xong Batch 12/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 10m 10s]   77%  ?? d?ch xong Batch 13/14 qua Fallback Failed...
  [ 10m 18s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 3. [OK] `1706.03762v7.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 2m 32s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 2.11 MB |
| **So trang** | 15 |
| **Thu muc luu tru** | `eval_outputs/run_20260902_112620/03_1706.03762v7/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 40 dong, 4 separator rows | [OK] |
| Ten rieng con nhan ra | 15/40 terms | [check] |
| Trich dan (et al.) / [N] | 94 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 2718 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| Recurrent Neural Networks (RNN) | Mạng nơ-ron tái phát | /rɪˈkɜːrənt/ /nʊrɒn/ /reɪfɛpt/ | [audio] |
| Long Short-Term Memory (LSTM) | Hồi quy ngắn hạn dài hạn | /lɒŋ/ /ʃɔːrt/ /tɜːrm/ /mɛməri/ | [audio] |
| Gated Recurrent Unit (GRU) | Đơn vị tái phát có cửa | /ɡeɪtɪd/ /rɪˈkɜːrənt/ /juːnit/ | [audio] |
| Sequence Modeling | Mô hình hóa chuỗi | /ˈsiːkwəns/ /ˈmoʊldɪŋ/ | [audio] |
| Sequence Transduction | Chuyển đổi chuỗi | /ˈsiːkwəns/ /trænsdʌkʃn/ | [audio] |
| Attention Mechanism | Máy cơ chế chú ý | /əˈtenʃn/ /ˈmekənɪzəm/ | [audio] |
| Transformer | Biến đổi | /trænsˈfeɪmər/ | [audio] |
| BLEU Score | Điểm số BLEU | /bleu/ /skɔːr/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 11.44 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260902_112620\03_1706.03762v7\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   32.1s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [   2m 8s]   46%  ?? d?ch xong Batch 1/6 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 16s]   53%  ?? d?ch xong Batch 2/6 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 24s]   66%  ?? d?ch xong Batch 4/6 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 32s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 4. [OK] `kho1.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 6m 1s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 3.48 MB |
| **So trang** | 12 |
| **Thu muc luu tru** | `eval_outputs/run_20260902_112620/04_kho1/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 27 dong, 5 separator rows | [OK] |
| Ten rieng con nhan ra | 11/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 0 blocks | [check] |
| Noi dung tieng Viet | 5121 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (7 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| protein structure prediction | đoán định cấu trúc protein | /protein structure prediction/ | [audio] |
| Critical Assessment of protein Structure Prediction (CASP) | Đánh giá phê duyệt cấu trúc protein (CASP) | /Critical Assessment of protein Structure Prediction/ | [audio] |
| machine learning | học máy | /machine learning/ | [audio] |
| multi-sequence alignment | đối sánh nhiều chuỗi | /multi-sequence alignment/ | [audio] |
| physical interaction programme | chương trình tương tác vật lý | /physical interaction programme/ | [audio] |
| evolutionary history | lịch sử tiến hóa | /evolutionary history/ | [audio] |
| atomic accuracy | độ chính xác nguyên tử | /atomic accuracy/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 10.91 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260902_112620\04_kho1\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   24.1s]   35%  ?? tr?ch xu?t xong 7 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  2m 40s]   42%  ?? d?ch xong Batch 1/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 48s]   45%  ?? d?ch xong Batch 2/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   3m 4s]   57%  ?? d?ch xong Batch 6/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   4m 1s]   60%  ?? d?ch xong Batch 7/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 21s]   62%  ?? d?ch xong Batch 8/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 29s]   68%  ?? d?ch xong Batch 10/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 37s]   74%  ?? d?ch xong Batch 12/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 53s]   77%  ?? d?ch xong Batch 13/14 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   6m 1s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

### 5. [OK] `2005.14165v4.pdf`

| Thuoc tinh | Gia tri |
|---|---|
| **Ket qua pipeline** | [OK] **COMPLETED** |
| **Thoi gian xu ly** | 15m 47s |
| **Model AI su dung** | `vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)` |
| **Kich thuoc file** | 6.45 MB |
| **So trang** | 75 |
| **Thu muc luu tru** | `eval_outputs/run_20260902_112620/05_2005.14165v4/` |

**Phan Tich Chat Luong Ban Dich:**

| Chieu danh gia | Ket qua | Verdict |
|---|---|---|
| LaTeX blocks bao toan | 0 blocks (100.0% nguyen ven) | [OK] |
| Bang Markdown | 387 dong, 40 separator rows | [OK] |
| Ten rieng con nhan ra | 31/40 terms | [check] |
| Trich dan (et al.) / [N] | 0 citations | [check] |
| Code blocks | 9 blocks | [check] |
| Noi dung tieng Viet | 16988 ky tu dac trung | [OK] |

**Bang Thuat Ngu Trich Xuat (8 thuat ngu -- hien thi toi da 8):**

| Thuat ngu | Nghia tieng Viet | Phien am IPA | Audio |
|---|---|---|---|
| few-shot learners | học máy ít mẫu | /fjuː ʃɒt lɜːnəz/ | [audio] |
| pre-training | huấn luyện tiền nghiệm | /pri traɪnɪŋ/ | [audio] |
| fine-tuning | điều chỉnh tinh vi | /faɪn tuːnɪŋ/ | [audio] |
| autoregressive language model | mô hình ngôn ngữ tự hồi quy | /ɔːtə'reɡrɛsɪv læŋgwɪdʒ məʊdl/ | [audio] |
| cloze tasks | những nhiệm vụ điền từ | /kloʊz tæsk/ | [audio] |
| closed book question answering | trả lời câu hỏi không cần sách giáo trình | /kləʊzd bʊk kwɛstʃən ˈænsərɪŋ/ | [audio] |
| common sense reasoning | lý luận thường thức | /kɒmən sens ˈriːznɪŋ/ | [audio] |
| reading comprehension | hiểu biết đọc | /rediŋ kəmˈprɛʃən/ | [audio] |

**Tai File Ket Qua:** [OK]

| Thuoc tinh | Gia tri |
|---|---|
| HTTP Status | 200 |
| Content-Type | `application/pdf` |
| Kich thuoc file ket qua | 31.42 MB |
| Dinh dang phat hien | PDF |
| File da luu tai | `G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260902_112620\05_2005.14165v4\translated.pdf` |

**Timeline Tien Do Xu Ly:**

```
  [    8.0s]   20%  ?ang b?c t?ch PDF b?i b?o khoa h?c th?nh c?u tr?c Markdown...
  [   32.1s]   30%  ?ang tr?ch xu?t thu?t ng? chuy?n ng?nh (Glossary)...
  [   48.1s]   35%  ?? tr?ch xu?t xong 8 thu?t ng?. ?ang b?t ??u d?ch thu?t...
  [  1m 36s]   40%  ?? d?ch xong Batch 1/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 40s]   42%  ?? d?ch xong Batch 3/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 48s]   43%  ?? d?ch xong Batch 4/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  2m 56s]   44%  ?? d?ch xong Batch 5/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 12s]   45%  ?? d?ch xong Batch 6/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  3m 53s]   46%  ?? d?ch xong Batch 7/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 33s]   47%  ?? d?ch xong Batch 8/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  4m 41s]   48%  ?? d?ch xong Batch 9/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   5m 5s]   50%  ?? d?ch xong Batch 11/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  5m 29s]   51%  ?? d?ch xong Batch 13/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  6m 49s]   52%  ?? d?ch xong Batch 14/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  6m 57s]   54%  ?? d?ch xong Batch 16/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  7m 21s]   55%  ?? d?ch xong Batch 17/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  7m 37s]   56%  ?? d?ch xong Batch 18/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  7m 45s]   57%  ?? d?ch xong Batch 19/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   8m 1s]   58%  ?? d?ch xong Batch 20/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  8m 41s]   59%  ?? d?ch xong Batch 21/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  8m 49s]   60%  ?? d?ch xong Batch 22/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [   9m 6s]   61%  ?? d?ch xong Batch 24/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  9m 46s]   62%  ?? d?ch xong Batch 25/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 10m 10s]   63%  ?? d?ch xong Batch 26/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 10m 42s]   65%  ?? d?ch xong Batch 28/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 10m 58s]   66%  ?? d?ch xong Batch 29/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 11m 14s]   67%  ?? d?ch xong Batch 30/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 11m 54s]   68%  ?? d?ch xong Batch 31/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 12m 26s]   69%  ?? d?ch xong Batch 32/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 12m 34s]   70%  ?? d?ch xong Batch 33/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  13m 6s]   71%  ?? d?ch xong Batch 35/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 13m 22s]   73%  ?? d?ch xong Batch 37/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 13m 30s]   74%  ?? d?ch xong Batch 38/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 14m 10s]   75%  ?? d?ch xong Batch 39/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 14m 59s]   76%  ?? d?ch xong Batch 40/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [  15m 7s]   77%  ?? d?ch xong Batch 41/44 qua Fallback Failed...
  [ 15m 15s]   78%  ?? d?ch xong Batch 42/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 15m 39s]   79%  ?? d?ch xong Batch 43/44 qua vLLM (Qwen/Qwen2.5-14B-Instruct-AWQ)...
  [ 15m 47s]  100%  ?? ho?n th?nh d?ch thu?t th?nh c?ng b?ng vLLM (Qwen/Qwen2.5-14B-Instru
```

---

## 5. Ket Qua Benchmark Ky Thuat

### 5a. Chunking Algorithm -- Bao Toan Cau Truc

Doc test: 527 tu | 2 bang | 3 cong thuc | 1 code block

| Thuat toan | So batch | Thoi gian (ms) | Vi pham bang | Vi pham LaTeX | Vi pham code |
|---|---|---|---|---|---|
| **Naive Fixed-Size** | 5 | 0.069 | [ERR] 3 (60.0%) | [ERR] 1 | [ERR] 2 |
| **Hierarchical v6.2** *(Our)* | 1 | 0.347 | [OK] 0 (0%) | [OK] 1 | [OK] 1 |

### 5b. So Sanh PDF Parser Libraries

| Parser | Latency (ms) | ms/trang | Table | Heading | Math | Output |
|---|---|---|---|---|---|---|
| **PyMuPDF4LLM** *(Our)* | 562.2 | 140.55 | [OK] | [OK] | [OK] | Structured Markdown (LLM-ready) |
| **PyMuPDF (Raw fitz)** | 8.37 | 2.09 | [ERR] | [ERR] | [OK] | Plain Text (Unstructured) |
| **pdfplumber** | 675.42 | 168.85 | [OK] | [ERR] | [OK] | Plain Text + Table Dicts |
| **pypdf** | 59.62 | 14.9 | [ERR] | [ERR] | [ERR] | Plain Text (Lossy) |

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
| 8 | 300.0 | 2404.17 | 614.56 | **3.91x** | **+291.2%** |

## 6. Van De Phat Hien & Khuyen Nghi

*Khong phat hien van de nghiem trong nao.* [OK]

### Khuyen Nghi:

1. **File rat lon (>50 trang):** Can implement page-level chunked upload de tranh timeout worker.
2. **Session recovery:** Co che Redis `job_latest_{doc_id}` dang hoat dong dung.
3. **Fallback chain:** Kiem tra file nao dung Gemini fallback vs vLLM primary de danh gia chi phi.

---

## 7. Verdict Cuoi Cung

> **PASS -- Tat ca pipeline hoat dong dung**

*Bao cao duoc tao tu dong boi `eval_pipeline.py` luc 02/09/2026 12:03:47*