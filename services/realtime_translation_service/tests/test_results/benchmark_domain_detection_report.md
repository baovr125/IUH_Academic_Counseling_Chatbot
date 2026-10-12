# Benchmark — Domain Detection (Phase 2.2)

## A. Thông tin chung

| Mục | Nội dung |
|---|---|
| Benchmark | Nhận diện lĩnh vực ở chế độ `auto` (một lời gọi LLM nhận diện + dịch) và đường tra từ điển cho từ/cụm ngắn |
| Thời gian chạy | DD-01 16:25:58–16:30:55; DD-02 16:30:55–16:37:41; DD-03 16:37:41–16:46:11; DD-05 16:40 (ngày 2026-10-10, +07) |
| Mã nguồn | Git HEAD `7e846214` + thay đổi chưa commit; vân tay `app/**/*.py` = `5ac072ebfd20` |
| Môi trường | Windows 11, Python 3.11.8, groq 0.33.0; Groq `qwen/qwen3.8-27b` (`reasoning_effort=none`, temperature 0,2), chỉ Groq (`DOMAIN_LLM_PROVIDERS=groq`, không dự phòng Gemini để đo đúng một model); từ điển thật từ Supabase: 246 mục, 6 lĩnh vực |
| Đối tượng | Chuỗi production: `build_auto_system_prompt` → `domain_llm.stream_llm` → `JointStreamParser` → `decide_domain` (ngưỡng mặc định `AUTO_DOMAIN_MIN_CONFIDENCE=0.75`, biên xung đột +2); đường ngắn `DomainIndex.exact` |
| Dataset | `domain_val.jsonl` 57 mẫu (36 in-domain, 12 ngoài domain, 3 thuật ngữ lạc ngữ cảnh, 6 cụm ngắn) — bộ val, không dùng để chỉnh. `domain_holdout.jsonl` 60 mẫu (48 in-domain = 8 bài/lĩnh vực, 12 ngoài domain) — phần mở đầu bài Wikipedia tiếng Anh, chưa từng dùng để chỉnh. DD-03: 12 mẫu in-domain (2/lĩnh vực) + 6 ngoài domain của bộ val, lặp 5 lần |
| Lệnh chạy | `bash test_artifacts/run_llm_benchmarks.sh` (các bước DD-01/02/03): `python evaluation/run_domain_raw.py --split {val,holdout} --model qwen/qwen3.8-27b --out test_artifacts/dd0{1,2}_*.jsonl --gap 5.0`; `python evaluation/run_domain_consistency.py --split val --per-domain 2 --ood 6 --repeats 5 ...`; phân tích offline: `python evaluation/analyze_domain_raw.py test_artifacts/dd01_val_qwen.jsonl test_artifacts/dd02_holdout_qwen.jsonl --show-errors` (và `--rule raw`); DD-05: `python evaluation/benchmarks/run_domain_local_bench.py --out test_artifacts/dd05_lt02_domain_local.json` |
| Định nghĩa metric | *macro-F1*: trung bình F1 của 6 lĩnh vực trên mẫu in-domain; *abstain đúng*: mẫu ngoài domain được trả "không xác định"; *sai-mà-tự-tin*: mẫu (in-domain + ngoài domain) bị gán một lĩnh vực sai; *ECE*: 10 bin trên confidence LLM của các lần LLM **chọn** một lĩnh vực; *token đầu*: thời gian tới chunk đầu tiên (dòng `DOMAIN:` đến cùng/ngay sau) |
| Tiêu chí | `evaluation.md` mục 2.4 (ghi "đề xuất" trong tài liệu đó) |

## B. Kết quả test case

| Test Case ID | Test Case Description | Test Data | Expected Result | Actual Result | Metric/Measurement | Status | Evidence/Log | Notes |
|---|---|---|---|---|---|---|---|---|
| DD-01 | Phân loại lĩnh vực + abstain trên bộ val | 57 mẫu (52 lời gọi LLM; 5 cụm ngắn đi đường từ điển) | macro-F1 ≥ 0,85; accuracy ≥ 90%; abstain ≥ 90%; sai-mà-tự-tin ≤ 5%; ECE ≤ 0,10 | 36/36 in-domain đúng; 12/12 ngoài domain abstain; 3/3 thuật ngữ lạc ngữ cảnh abstain; 6/6 cụm ngắn đúng; 0 lỗi API; 0 vi phạm định dạng; 0 bản dịch hỏng | macro-F1 1,000; accuracy 1,000; abstain 1,000; sai-mà-tự-tin 0/48; ECE 0,040 | PASS | `test_artifacts/dd01_val_qwen.jsonl`, `dd01_02_analysis.log` | ECE tính cả câu trả lời `unknown` = 0,149 (xem mục D) |
| DD-02 | Phân loại lĩnh vực + abstain trên hold-out độc lập (Wikipedia) | 60 mẫu, 60 lời gọi LLM | như DD-01 | 48/48 in-domain đúng; 12/12 ngoài domain abstain; 0 lỗi API; 0 vi phạm định dạng; 0 bản dịch hỏng | macro-F1 1,000; accuracy 1,000; abstain 1,000; sai-mà-tự-tin 0/60; ECE 0,031 | PASS | `test_artifacts/dd02_holdout_qwen.jsonl`, `dd01_02_analysis.log` | ECE tính cả `unknown` = 0,178 |
| DD-03 | Nhất quán khi gọi lại cùng đầu vào | 18 mẫu × 5 lần = 90 lời gọi | ≥ 98% lời gọi cho cùng quyết định | 90/90 cùng quyết định với đa số; 18/18 mẫu nhất quán tuyệt đối; đa số đúng nhãn 18/18 | 100% | PASS | `test_artifacts/dd03_consistency_val_qwen.json` | Bản dịch giống hệt nhau chỉ 6/18 mẫu (33%) — nhất quán về *lĩnh vực*, không về *câu chữ* |
| DD-04 | Độ trễ phân loại (domain nằm ở dòng đầu stream) | Các lời gọi DD-01 (52) và DD-02 (60) | P95 ≤ ~1,5 s; timeout < 20 s | token đầu p50 0,46 s / p95 0,82 s (val); p50 0,48 s / p95 0,73 s (hold-out). Timeout token đầu cấu hình 10 s | p95 lớn nhất 0,82 s | PASS | `dd01_02_analysis.log` | Đo từ máy khách tới Groq qua Internet; chưa gồm debounce 1,5 s phía UI |
| DD-05 | Tra từ điển chính xác cho từ/cụm ngắn (không LLM) | 246 thuật ngữ thật × 4 dạng (nguyên dạng, VIẾT HOA, có "the", số nhiều) + 50 cụm không có trong từ điển | *(đề xuất, chờ duyệt)* nguyên dạng 100%; false-hit 0 | nguyên dạng 246/246; viết hoa 246/246; có mạo từ 246/246; số nhiều 245/246; false-hit 0/50 | hit-rate 100% / 100% / 100% / 99,6% | PASS | `test_artifacts/dd05_lt02_domain_local.json` (`exact`, `exact_misses`) | Ca trượt duy nhất "negligence per ses" do bộ sinh số nhiều tạo dạng không có thật (cụm Latinh) — giới hạn của dữ liệu thử, không phải lỗi tra cứu |

## C. Tổng hợp

| Tổng test case | PASS | FAIL | PENDING | BLOCKED | SKIPPED |
|---:|---:|---:|---:|---:|---:|
| 5 | 5 | 0 | 0 | 0 | 0 |

| Metric | val | hold-out | Tiêu chí (`evaluation.md` 2.4) |
|---|---|---|---|
| Macro-F1 in-domain | 1,000 (n=36) | 1,000 (n=48) | ≥ 0,85 |
| Accuracy in-domain | 100% | 100% | ≥ 90% |
| Abstain đúng ngoài domain | 12/12 | 12/12 | ≥ 90% |
| Sai-mà-tự-tin | 0/48 | 0/60 | ≤ 5% |
| ECE (chỉ lần chọn lĩnh vực) | 0,040 | 0,031 | ≤ 0,10 |
| Lặp 5 lần giống nhau | 100% (90 lời gọi) | — | ≥ 98% |
| Token đầu p95 | 0,82 s | 0,73 s | ≤ ~1,5 s |

**Baseline** (quy tắc chỉ tin LLM, không ngưỡng/không đối chiếu từ điển — `--rule raw`): cho kết quả **y hệt** trên cả val và hold-out (log `dd01_02_analysis_rawrule.log`). Ở lượt chạy giai đoạn 9 trước đó, quy tắc có ngưỡng từng abstain đúng thêm 1 ca thuật ngữ lạc ngữ cảnh; lượt này không có khác biệt.

## D. Phân tích

- **Đạt:** cả 5 test case đạt tiêu chí theo ước lượng điểm.
- **Độ tin cậy thống kê (đo được, không phải giả thuyết):** với 0 lỗi trên n mẫu, cận trên 95% của tỉ lệ lỗi ≈ 3/n: in-domain gộp 84 mẫu ⇒ lỗi phân loại có thể tới ~3,6%; ngoài domain gộp 24 mẫu ⇒ abstain thật có thể thấp tới ~87,5% (dưới ngưỡng 90%). Nghĩa là số mẫu **chưa đủ để khẳng định** tiêu chí abstain ở độ tin cậy 95%, dù không có lỗi nào.
- **ECE:** khi LLM trả `unknown` đúng, confidence kèm theo thường thấp (0,1); nếu tính cả các câu này vào ECE (coi confidence là xác suất "đúng") thì ECE tăng lên 0,15–0,18 dù quyết định đúng. Chỉ số có ý nghĩa với tiêu chí là ECE trên các lần LLM chọn một lĩnh vực (0,03–0,04). Confidence của LLM tập trung ở 0,95 (48/60 mẫu hold-out) nên không phân biệt tốt.
- **Ngưỡng chưa được kiểm tra:** do không có lỗi nào, ngưỡng 0,75 và biên +2 không ảnh hưởng kết quả; không kết luận được giá trị ngưỡng nào tốt hơn.
- **Hạn chế dataset:** val do nhóm tự viết (câu rõ chủ đề); hold-out lấy phần mở đầu bài Wikipedia (văn phong định nghĩa, rất dễ nhận lĩnh vực), nhãn theo chủ đề bài; không có câu trộn nhiều lĩnh vực, câu mơ hồ, từ đa nghĩa — nhóm khó mà `evaluation.md` 2.1 yêu cầu (≥ 600 đoạn) **chưa được xây dựng**, nên kết quả trên chỉ đại diện cho văn bản rõ chủ đề.
- **Độ trễ** phụ thuộc mạng và tải Groq tại thời điểm chạy (16:25–16:46); lượt giai đoạn 9 trước đó cho p95 0,69–0,88 s — cùng mức.
