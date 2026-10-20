# Báo cáo đánh giá sinh từ vựng bằng AI

> Số liệu từ `evaluation/results/`. Mọi tỷ lệ kèm khoảng tin cậy Wilson 95% `[thấp-cao] (đạt/tổng)`. Mẫu nhỏ nên khoảng tin cậy rộng; xem README để biết các hạn chế.

## 1. Chủ đề: phương án B (3 bước) so với đối chứng A (1 lời gọi)

| Chỉ số | A: một lần gọi | B: SELECT→ENRICH→VERIFY |
|---|---|---|
| Số lần chạy | 20 | 20 |
| Chạy thành công | 20 | 20 |
| Lỗi do provider (429/timeout) | 0 | 0 |
| Lỗi hệ thống | 0 | 0 |
| Tổng số thẻ | 200 | 199 |
| Đạt ≥ 90% số lượng | 100.0% [84-100] (20/20) | 100.0% [84-100] (20/20) |
| Lần chạy có từ trùng | 0 | 0 |
| Thẻ đúng schema / ứng viên | 97.3% [94-99] (214/220) | 100.0% [98-100] (214/214) |
| Tỷ lệ bị reviewer loại | 0.0% [0-2] (0/214) | 0.0% [0-2] (0/214) |
| Tỷ lệ reviewer sửa | 0.0% [0-2] (0/200) | 18.6% [14-25] (37/199) |
| Ví dụ chứa từ khóa | 98.5% [96-99] (197/200) | 98.0% [95-99] (195/199) |
| IPA hợp lệ (có) | 100.0% [98-100] (200/200) | 97.5% [94-99] (194/199) |
| Có dịch câu ví dụ | 100.0% [98-100] (200/200) | 100.0% [98-100] (199/199) |
| Thẻ đã qua kiểm duyệt | 0.0% [0-2] (0/200) | 95.5% [92-98] (190/199) |
| Độ trễ (s) | p50: 2.2, p95: 2.8, mean: 2.3 | p50: 5.2, p95: 6.1, mean: 5.1 |
| Token / lần chạy | prompt: 313, completion: 798 | prompt: 2103, completion: 1669 |
| Token / thẻ | 111.1 | 379.1 |
| Lời gọi LLM / lần chạy | 1.0 | 3.0 |
| Provider | groq:openai/gpt-oss-120b: 20 | groq:openai/gpt-oss-120b: 20 |
| Mã lỗi | — | — |

### Phương án B theo trình độ

| Trình độ | Lần chạy | Thẻ | Ví dụ chứa từ khóa | IPA hợp lệ | Có dịch ví dụ |
|---|---|---|---|---|---|
| A1 | 1/1 | 9 | 100.0% [70-100] (9/9) | 100.0% [70-100] (9/9) | 100.0% [70-100] (9/9) |
| A2 | 5/5 | 50 | 92.0% [81-97] (46/50) | 100.0% [93-100] (50/50) | 100.0% [93-100] (50/50) |
| B1 | 6/6 | 60 | 100.0% [94-100] (60/60) | 100.0% [94-100] (60/60) | 100.0% [94-100] (60/60) |
| B2 | 5/5 | 50 | 100.0% [93-100] (50/50) | 90.0% [79-96] (45/50) | 100.0% [93-100] (50/50) |
| C1 | 3/3 | 30 | 100.0% [89-100] (30/30) | 100.0% [89-100] (30/30) | 100.0% [89-100] (30/30) |

Số chủ đề chạy thành công ở cả hai biến thể: 20.

## 2. Đoạn văn (trích từ)

| Chỉ số | B: đoạn văn |
|---|---|
| Số lần chạy | 8 |
| Chạy thành công | 8 |
| Lỗi do provider (429/timeout) | 0 |
| Lỗi hệ thống | 0 |
| Tổng số thẻ | 79 |
| Đạt ≥ 90% số lượng | 100.0% [68-100] (8/8) |
| Lần chạy có từ trùng | 0 |
| Thẻ đúng schema / ứng viên | 100.0% [96-100] (86/86) |
| Tỷ lệ bị reviewer loại | 2.3% [1-8] (2/86) |
| Tỷ lệ reviewer sửa | 13.9% [8-23] (11/79) |
| Ví dụ chứa từ khóa | 100.0% [95-100] (79/79) |
| IPA hợp lệ (có) | 100.0% [95-100] (79/79) |
| Có dịch câu ví dụ | 100.0% [95-100] (79/79) |
| Thẻ đã qua kiểm duyệt | 88.6% [80-94] (70/79) |
| Độ trễ (s) | p50: 6.2, p95: 7.0, mean: 6.1 |
| Token / lần chạy | prompt: 2299, completion: 2121 |
| Token / thẻ | 447.5 |
| Lời gọi LLM / lần chạy | 3.0 |
| Provider | groq:openai/gpt-oss-120b: 8 |
| Mã lỗi | — |

## 3. IPA so với từ điển

```json
{
  "sampled_words": 100,
  "dictionary_coverage": "34.0% [25-44] (34/100)",
  "exact_match_among_covered": "76.5% [60-88] (26/34)",
  "close_match_among_covered(>=0.8)": "100.0% [90-100] (34/34)",
  "note": "Cận dưới: từ điển trộn giọng Anh/Mỹ; chỉ tính các từ đơn có mục từ điển."
}
```

## 4. Prompt injection

```json
{
  "payloads": 20,
  "attempts": 20,
  "passed": 19,
  "failed_ids": [
    "I04"
  ]
}
```
