# Probe và kiểm chứng ad-hoc cho Realtime Translation

Các script nhỏ dùng khi phát triển nhận diện ngôn ngữ / domain (2026-10-10 → 12), trước đây nằm ngoài dự án.
Bổ sung cho bộ kiểm thử chính thức (`tests/`, `evaluation/run_*.py`, `evaluation/benchmarks/`). Chạy từ **thư mục gốc dự án**:

```
python -X utf8 services/realtime_translation_service/evaluation/probes/<script>.py
```
Mọi script tự tìm service qua đường dẫn tương đối; chạy trong chế độ `TESTING=1` (không cần Redis/Supabase thật).

## E2E qua API
| Script | Làm gì |
|---|---|
| `smoke_api.py` | Dựng app bằng `TestClient`, gọi `/translate/detect`, `/translate/text`, `/translate/stream` với 4 câu mẫu (Việt, Ý ngoài phạm vi, từ quá ngắn, chỉ có số) và in mã trạng thái + trạng thái nhận diện. Token ký bằng khóa **ngẫu nhiên mỗi lần chạy** (issuer `iuh-auth-service`), không dùng secret thật. |

## Hành vi nhận diện ngôn ngữ (in kết quả từng câu)
| Script | Làm gì |
|---|---|
| `probe_new.py` / `probe_old.py` | Chạy cùng bộ câu mẫu qua bộ nhận diện hiện tại (`language_detection`) và qua đường cũ (`translation_service` + fastText) để so sánh |
| `mixed_probe.py` | Câu pha nhiều ngôn ngữ (Việt + Nhật, Việt + Pháp…) |
| `hostile_timing.py` | Đầu vào xấu (chuỗi 3000 ký tự, chữ Hebrew, toán học in đậm…): thời gian xử lý + trạng thái |
| `margin_check.py` | Độ tin cậy/biên độ của các ca đúng theo nhóm (teencode, không dấu, sai dấu…) so với ngưỡng |
| `wrong_high.py` | Liệt kê các ca nhận sai nhưng tự tin cao (kiểm tra rủi ro "sai mà chắc") |

## Hiệu năng và bộ nhớ (nặng, tải mô hình)
`perf_check.py` (độ trễ/đồng thời, tắt cache), `total_rss.py` (RSS khi nạp NLLB + bộ nhận diện), `mem_variants.py` (RSS theo từng cấu hình Lingua).

## Cần dữ liệu Tatoeba ngoài
`p1_analysis.py`, `oos_mass_analysis.py`, `mem_variants.py` đọc `evaluation/dataset/external/tatoeba/external_sanity.jsonl` (đổi thư mục bằng biến `TATOEBA_DIR`).
Dữ liệu này **không có trong repo** (giấy phép CC BY 2.0 FR, đã `.gitignore`): tải bằng `fetch_tatoeba.py` (cần mạng). Thư mục `external/` hiện chưa có dữ liệu.

## Dựng dữ liệu / tài liệu / đối chiếu số liệu
| Script | Làm gì |
|---|---|
| `fetch_tatoeba.py` | Tải mẫu ngẫu nhiên Tatoeba để kiểm tra độc lập |
| `fetch_holdout.py` | Dựng bộ hold-out từ phần mở đầu bài Wikipedia tiếng Anh |
| `gen_messages.py <file_ra>` | Sinh `MESSAGES_REVIEW.md` (liệt kê mọi cảnh báo/thông báo). **Chạy từ thư mục service**; chú ý không ghi đè bản đang dùng |
| `check_artifacts.py`, `check_more.py <thư_mục_artifact> <thư_mục_service>` | Chỉ đọc: đối chiếu số liệu trong `tests/test_results/test_artifacts` với các báo cáo (thiếu file thì bỏ qua) |

## Đã kiểm chứng sau khi chuyển (2026-10-19)
Đã chạy từ vị trí mới, exit 0: `smoke_api`, `probe_new`, `probe_old`, `hostile_timing`, `mixed_probe`, `margin_check`, `wrong_high`, `check_artifacts`, `check_more`.
**Chưa chạy lại:** `perf_check`, `total_rss`, `mem_variants` (nặng), `p1_analysis`, `oos_mass_analysis`, `fetch_*` (cần dữ liệu/mạng), `gen_messages` (tránh ghi đè tài liệu). Các script này đã được kiểm tra cú pháp và đổi đường dẫn.

## Lưu ý
* `smoke_api.py` từng trả 401 vì sau đợt hardening xác thực, service bắt buộc `iss = iuh-auth-service` và `exp`: nếu viết script gọi API mới, hãy ký token theo đúng quy tắc trong `app/utils/security.py`.
* Không đưa secret vào script: bản cũ của `smoke_api.py` ghi cứng một khóa JWT thử (đã bỏ).
