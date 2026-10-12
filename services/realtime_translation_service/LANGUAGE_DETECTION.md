# Language Detection — thiết kế, vận hành, hiệu chỉnh

Phạm vi: nhận diện ngôn ngữ nguồn khi `source_lang="auto"` (`/translate/text`, `/translate/stream`, `/translate/detect`).
Domain Detection **không** thuộc tài liệu này.

## 1. Chính sách

Chỉ trạng thái `detected` mới được dịch. Mọi trạng thái khác **dừng** và yêu cầu người dùng chọn ngôn ngữ nguồn.

| status | Ý nghĩa | `/text` | `/stream` | UI |
|---|---|---|---|---|
| `detected` | đủ tin cậy | dịch | `detection` → `resolved_source_lang` → `text` | nhãn ngôn ngữ |
| `uncertain` | ngắn/mơ hồ/hai engine bất đồng | 400 `LANG_UNCERTAIN` | `detection` → `error` (`code`) | hộp chọn ngôn ngữ + nút ứng viên |
| `unsupported` | nhận ra ngôn ngữ ngoài 10 ngôn ngữ hỗ trợ | 400 `LANG_UNSUPPORTED` | như trên | thông báo + chọn tay |
| `unknown` | chỉ có URL/email | 400 `LANG_UNKNOWN` | như trên | thông báo |
| `invalid_input` | không có chữ cái (số, emoji, ký hiệu) | 400 `INVALID_INPUT` | như trên | thông báo |
| `system_error` | lỗi engine | 503 `LANG_SYSTEM_ERROR` | như trên | lỗi chung |

Lỗi `/text` có dạng `{"ok": false, "detail": "<message>", "error": {"code", "message", "detection": {...}}}`
(`detail` giữ để tương thích ngược). `/detect` luôn trả HTTP 200 với chi tiết, trừ `invalid_input` (400) và `system_error` (503).
Ngôn ngữ chọn tay luôn thắng và bỏ qua nhận diện (`engine="manual"`).

`LanguageDetectionDetails`: `status`, `resolved_source_lang` (chỉ khi `detected`), `confidence`, `margin`, `engine`
(`fusion|fasttext|lingua|script|hint|manual|none`), `candidates` (≤3 ngôn ngữ **được hỗ trợ**), `reason`
(`short_input|low_confidence|engines_disagree|out_of_scope|script_mismatch|mixed_language`), `detected_language`
(với `unsupported`), `is_multilingual`, `message`.

`source_lang_hint` (tùy chọn, chỉ khi `auto`): ngôn ngữ đã nhận diện ở lần gõ trước. Chỉ được nhận khi nằm trong top-2
ngôn ngữ hỗ trợ và xác suất ≥ `DETECT_HINT_MIN_PROB`, và **chỉ khi kết luận chắc chắn đã không xảy ra** — không bao giờ ghi
đè bằng chứng mạnh (Ý vẫn là `unsupported` dù hint là `en`).

## 2. Đường xử lý (`app/services/language_detection.py`)

```
text ─► (cap 60k) ─► bóc HTML (bỏ script/style/code/pre) ─► bỏ URL/email/@mention ─► NFC ─► cap 2.000 ký tự
     ─► script profile (Latin/Han/Kana/Hangul/Thai/Cyrillic/Arabic/…) và độ dài hiệu dụng
          └─ luật chắc chắn theo hệ chữ: Hangul→ko, Kana(+Hán)→ja, Thai→th, Arabic/Hebrew/Greek/Indic→unsupported
     ─► fastText top-5 (nhãn gốc; nhãn lạ gộp thành "?")
     ─► Lingua (35 ngôn ngữ: 10 hỗ trợ + 25 họ hàng/dễ nhầm) — chạy khi fastText chưa đủ chắc / text ngắn / nhãn ngoài phạm vi
     ─► fusion có trọng số + bằng chứng độc lập (tiếng Việt có dấu/không dấu, marker de/fr/es ≥2 từ, Hán thuần → zh)
     ─► meta-confidence = sigmoid(bias + Σ coef·feature)  (models/detect_calibration.json)
     ─► quyết định theo bucket độ dài (short/medium/long) + các lớp bảo vệ
```

Lớp bảo vệ: `p1 ≥ DETECT_MIN_CONFIDENCE`, `margin ≥ DETECT_MIN_MARGIN`; `unsupported` yêu cầu khối ngoài-phạm-vi vượt ngôn
ngữ hỗ trợ tốt nhất ≥ `DETECT_OOS_MIN_MARGIN`; nếu ≥ `DETECT_OUTSIDE_MASS_BLOCK` xác suất nằm ngoài tập hỗ trợ mà top-1 chưa
tới `DETECT_OUTSIDE_P1_CAP` thì chỉ `uncertain` (trừ khi có bằng chứng độc lập, vd tiếng Việt không dấu).

Độ dài hiệu dụng: **số từ** với hệ chữ có dấu cách; **số ký tự** với CJK/Thai (không dùng `split()`).
Kết quả được cache LRU trong RAM (`DETECT_CACHE_SIZE`), khóa gồm cả `hint`.

## 3. Cấu hình (biến môi trường)

Xem `.env.example` (mục 5). Quan trọng nhất:

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `FASTTEXT_LID_MODEL` | `models/lid.176.ftz` | có thể dùng `lid.176.bin` (+~0,1 điểm chính xác, nặng 131 MB) |
| `DETECT_LINGUA_OOS` | 25 mã ISO | danh sách ngôn ngữ họ hàng đưa vào Lingua để nhận ra "ngoài phạm vi" |
| `DETECT_LINGUA_LOW_ACCURACY` | `1` | Lingua chế độ tiết kiệm RAM (~60 MB). Đặt `0` để dùng độ chính xác cao (~730 MB), chất lượng nhỉnh hơn nhẹ (xem §5) |
| `DETECT_CALIBRATION_FILE` | `models/detect_calibration.json` | hệ số + ngưỡng theo bucket |
| `DETECT_USE_MARKERS` | `1` | `0` để ablation luật marker |

Khởi động: `main.py` gọi `warm_up()` (nạp fastText + Lingua, chạy vài lượt nhận diện) trước khi nhận request;
`/health/ready` báo `lingua_model: loaded|missing` và `degraded` nếu thiếu.

## 4. Hiệu chỉnh & dev-gate

```bash
python evaluation/dataset/build_lang_dev_set.py            # sinh lang_dev.jsonl / lang_val.jsonl (UTF-8)
python scripts/build_vi_lexicon.py                          # sinh app/resources/vi_toneless_syllables.txt từ vocab PhoBERT
python scripts/fit_detection_calibrator.py                  # fit chỉ trên DEV → models/detect_calibration.json
python evaluation/dev_gate.py --split val --show-errors     # kiểm chứng trên VAL (hoặc --file <jsonl> bất kỳ)
```

`dev_gate.py` gọi đúng `detect_language_detailed` (cùng hàm của `/text`, `/stream`, `/detect`). Bộ dev/val do nhóm tự viết nên
**dễ hơn thực tế**; nó chỉ để hiệu chỉnh và chặn hồi quy, không phải bộ test của `word/Report/realtime_translation/evaluation.md`.
Không dùng bộ test đóng băng để tinh chỉnh ngưỡng.

Lưu ý khi fit lại: ngưỡng được đặt ngay trên mẫu sai có meta cao nhất (out-of-fold) và bị chặn ở 0,95; **một nhãn nhiễu trong dữ liệu
có thể đẩy ngưỡng lên cao và làm sập độ phủ** — luôn chạy lại dev-gate trên dữ liệu độc lập sau khi fit, và đừng thêm dữ liệu
chưa được kiểm tra nhãn qua `--extra`.

## 5. Số đo đã có (chạy trên máy phát triển, CPU)

Mọi số dưới đây là **tín hiệu phát triển**, không thay cho kết quả của bài test chính thức.

| Bộ dữ liệu | Mẫu | Accuracy chặt | Sai-mà-tự-tin | OOS false-accept |
|---|---:|---:|---:|---:|
| dev (tự viết, dùng để fit) | 425 | 93,0%¹ | 0% | 0% |
| val (tự viết, không dùng để fit) | 144 | 87,1%¹ | 0% | 0% |
| Tatoeba mẫu 1 (dùng để chọn vài luật tổng quát) | 2.075 | 98,4% | 0,10% | 0,35% |
| Tatoeba hold-out (seed khác, không tinh chỉnh) — Lingua high-accuracy | 2.690 | 98,2% (98,6% nếu tính abstain) | 0,15% | 0,43% |
| Tatoeba hold-out — **Lingua low-accuracy (mặc định)** | 2.690 | 97,95% (98,3% nếu tính abstain) | 0,30% | 0,87% |

¹ Có nhiều mẫu cố ý rất ngắn/mơ hồ (tiền tố gõ dở) được phép abstain; accuracy "chấp nhận abstain" là 99,7–100%.

Tatoeba là câu sạch, nhiều câu ngắn, có nhãn nhiễu (ví dụ câu tiếng Anh nằm trong file tiếng Mã Lai); không đại diện cho nhập liệu thực
của người dùng (typo, slang, code-switching nặng).

| Chi phí | Giá trị |
|---|---|
| Độ trễ warm (1 / 10 / 50 luồng) | p50 ≈ 0,12 ms, p95 ≈ 1 ms, p99 ≤ 18 ms |
| Warm-up khi khởi động | ~0,06 s (low accuracy, mặc định), ~0,6 s (high accuracy) |
| RAM Lingua (35 ngôn ngữ) | +~60 MB (low, mặc định), +~730 MB (high). Tổng RSS service khi nạp đủ model: ~1,7 GB (low) / ~2,3 GB (high); giới hạn container hiện tại 3,5 GB |
| `lid.176.bin` so với `.ftz` | sai-mà-tự-tin 0,10% so với 0,19%; accuracy +0,13 điểm; +130 MB |

## 6. Giới hạn đã biết

- Ngôn ngữ họ hàng ngắn (sv/da/nb, bg/uk↔ru, es↔pt↔it) vẫn có thể bị gán nhầm hoặc abstain; chỉ tốt khi câu đủ dài.
- Chữ Nôm / ký tự hiếm: không có luật riêng.
- `is_multilingual` chỉ là cờ dựa trên tỉ lệ hệ chữ: câu Việt–Anh (cùng chữ Latin) luôn có `is_multilingual=false`. Câu trộn ngôn ngữ được xử lý như một ngôn ngữ chủ đạo (xem §7).
- Calibration hiện tại được fit khi Lingua ở chế độ high-accuracy; fit lại cho low-accuracy làm tiếng Việt không dấu kém đi nên chưa đổi.
- Calibration fit trên ~330 mẫu dev; hệ số nhỏ nên quyết định thực tế dựa nhiều vào các lớp bảo vệ. Cần fit lại khi có dữ liệu gán nhãn thật lớn hơn.
- Bộ dữ liệu `evaluation/dataset/lang_detection_*.jsonl` (bộ của giai đoạn trước) vẫn bị lỗi encoding (mojibake); sửa ở bước chuẩn bị của `evaluation.md`.

## 7. Văn bản trộn nhiều ngôn ngữ

Service nhận diện **một ngôn ngữ chủ đạo** cho cả đoạn, không tách từng đoạn con. Đã thử trên code thật (chỉ đo nhận diện, chưa đo chất lượng dịch):

| Loại | Kết quả |
|---|---|
| Việt có dấu + thuật ngữ Anh (5 câu, 10–25% từ Anh) | 5/5 `vi`, confidence ≥ 0,99 |
| Việt có dấu, Anh chiếm ~40% | 2/2 `vi` |
| Việt không dấu + Anh | 2/2 `vi` (xác suất `vi` 0,42–0,64) |
| Anh chủ đạo + từ Việt (`phở`, `xin chào`) | 2/2 `en` |
| Việt + chuỗi tiếng Nhật/Pháp trong dấu ngoặc | 2/2 `vi` |
| Cụm rất ngắn gần 50–50 (`Hôm nay meeting`) | `uncertain` → hỏi người dùng |

Khuyến nghị: giữ nguyên cách này. Nếu cần giữ nguyên thuật ngữ tiếng Anh trong bản dịch, dùng từ điển thuật ngữ/domain thay vì nhận diện đa ngôn ngữ.
