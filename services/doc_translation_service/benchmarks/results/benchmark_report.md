# Báo Cáo Số Liệu Thực Nghiệm — Document Translation Service

- **Ngày đo:** 2026-08-29 21:00:17
- **Hệ điều hành:** Windows 10 (10.0.26200)
- **Python:** 3.11.8

## 1. So Sánh Các Thư Viện Trích Xuất PDF

| Parser | Độ trễ TB (ms/trang) | Tốc độ (trang/giây) | Peak RAM (MB) | Bảo toàn Bảng Markdown | Bảo toàn Heading |
|:---|:---:|:---:|:---:|:---:|:---:|
| **PyMuPDF4LLM** | 124.79 | **8.01** | 11.59 | ✅ 100% | ✅ 100% |
| **PyMuPDF (Raw fitz)** | 0.93 | **1071.07** | 0.04 | ❌ Không | ❌ Không |
| **pdfplumber** | 85.1 | **11.75** | 16.15 | ✅ 100% | ❌ Không |
| **pypdf** | 6.65 | **150.36** | 0.35 | ❌ Không | ❌ Không |

## 2. So Sánh Phân Đoạn Batch Dịch Thuật LLM (Batching Strategy)

| Tiêu chí | Naive Fixed-Size Chunking (512 tokens) | Markdown Hierarchical Batching (Nhóm Chọn) |
|:---|:---:|:---:|
| **Số lượng Batches sinh ra** | 5 | **1** |
| **Tỷ lệ cắt đôi bảng biểu (Table Split Violation)** | ⚠️ 60.0% (3 lần) | **0.0% (Tuyệt đối không cắt)** |
| **Lỗi cắt công thức toán LaTeX ($$)** | ⚠️ 1 lần | **0 lần (Bảo toàn nguyên vẹn)** |
| **Lỗi cắt khối mã nguồn Code** | ⚠️ 2 lần | **0 lần (Bảo toàn nguyên vẹn)** |
| **Thời gian thực thi phân đoạn** | 0.037 ms | 0.049 ms |

## 3. Độ Chính Xác Dịch Thuật Ngữ Chuyên Ngành & Bố Cục

| Giải pháp | Độ chính xác Thuật ngữ (%) | Bảo toàn Bảng Markdown | Bảo toàn Công thức LaTeX |
|:---|:---:|:---:|:---:|
| **Google Dịch (deep-translator)** | 16.67% | 42.5% (Thường làm vỡ gạch đứng | và canh cột) | 31.0% (Thường dịch các ký tự toán bên trong LaTeX) |
| **Raw LLM (Không có Glossary)** | 70.0% | 88.0% | 85.0% |
| **Pipeline Nhóm (Glossary Injection)** | **100.0%** | **100.0% (Bảo toàn nguyên vẹn nhờ Hard Rules)** | **100.0% (Bảo toàn nguyên vẹn $..$ và $$..$$)** |

## 4. Hiệu Năng Xử Lý Đa Luồng (Parallel Batching)

- **Thời gian xử lý tuần tự (Sequential):** 2402.66 ms
- **Thời gian xử lý song song (Parallel 4 Workers):** **604.47 ms**
- **Hệ số tăng tốc (Speedup Factor):** **3.97x** (Tăng 297.5% thông lượng)

## 5. Đánh Giá Bảo Toàn Định Dạng Đa Định Dạng (Word, PowerPoint, PDF Scan)

| Định dạng File | Cơ chế Xử lý | Tỷ lệ Bảo toàn Định dạng / Bố cục | Độ trễ Xử lý |
|:---|:---|:---:|:---:|
| **Microsoft Word (.docx)** | In-place paragraph & table cell | **100.0% Font/Bold & 100.0% Bảng** | 15.25 ms |
| **Microsoft PowerPoint (.pptx)** | In-place slide text shape + AutoFit | **100.0% Slide & AutoFit Text** | 22.35 ms |
| **PDF Scan / Ảnh chụp** | PyMuPDF Pixmap (200 DPI) + PaddleOCR | **98.2% Text Blocks** | 47.42 ms/trang |
