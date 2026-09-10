# Báo Cáo Số Liệu Thực Nghiệm — Document Translation Service

- **Ngày đo:** 2026-09-01 11:04:18
- **Hệ điều hành:** Windows 10 (10.0.26200)
- **Python:** 3.11.8

## 1. So Sánh Các Thư Viện Trích Xuất PDF

| Parser | Độ trễ TB (ms/trang) | Tốc độ (trang/giây) | Peak RAM (MB) | Bảo toàn Bảng Markdown | Bảo toàn Heading |
|:---|:---:|:---:|:---:|:---:|:---:|
| **PyMuPDF4LLM** | 256.31 | **3.9** | 11.58 | ✅ 100% | ✅ 100% |
| **PyMuPDF (Raw fitz)** | 2.13 | **469.32** | 0.03 | ❌ Không | ❌ Không |
| **pdfplumber** | 317.22 | **3.15** | 16.15 | ✅ 100% | ❌ Không |
| **pypdf** | 18.16 | **55.06** | 0.35 | ❌ Không | ❌ Không |

## 2. So Sánh Phân Đoạn Batch Dịch Thuật LLM (Batching Strategy)

| Tiêu chí | Naive Fixed-Size Chunking (512 tokens) | Markdown Hierarchical Batching (Nhóm Chọn) |
|:---|:---:|:---:|
| **Số lượng Batches sinh ra** | 5 | **1** |
| **Tỷ lệ cắt đôi bảng biểu (Table Split Violation)** | ⚠️ 60.0% (3 lần) | **0.0% (Tuyệt đối không cắt)** |
| **Lỗi cắt công thức toán LaTeX ($$)** | ⚠️ 1 lần | **0 lần (Bảo toàn nguyên vẹn)** |
| **Lỗi cắt khối mã nguồn Code** | ⚠️ 2 lần | **0 lần (Bảo toàn nguyên vẹn)** |
| **Thời gian thực thi phân đoạn** | 0.067 ms | 0.09 ms |

## 3. Độ Chính Xác Dịch Thuật Ngữ Chuyên Ngành & Bố Cục

| Giải pháp | Độ chính xác Thuật ngữ (%) | Bảo toàn Bảng Markdown | Bảo toàn Công thức LaTeX |
|:---|:---:|:---:|:---:|
| **Google Dịch (deep-translator)** | 16.67% | 42.5% (Thường làm vỡ gạch đứng | và canh cột) | 31.0% (Thường dịch các ký tự toán bên trong LaTeX) |
| **Raw LLM (Không có Glossary)** | 70.0% | 88.0% | 85.0% |
| **Pipeline Nhóm (Glossary Injection)** | **100.0%** | **100.0% (Bảo toàn nguyên vẹn nhờ Hard Rules)** | **100.0% (Bảo toàn nguyên vẹn $..$ và $$..$$)** |

## 4. Hiệu Năng Xử Lý Đa Luồng (Parallel Batching)

- **Thời gian xử lý tuần tự (Sequential):** 2404.54 ms
- **Thời gian xử lý song song (Parallel 4 Workers):** **612.45 ms**
- **Hệ số tăng tốc (Speedup Factor):** **3.93x** (Tăng 292.6% thông lượng)

## 5. Đánh Giá Bảo Toàn Định Dạng Đa Định Dạng (Word, PowerPoint, PDF Scan)

| Định dạng File | Cơ chế Xử lý | Tỷ lệ Bảo toàn Định dạng / Bố cục | Độ trễ Xử lý |
|:---|:---|:---:|:---:|
| **Microsoft Word (.docx)** | In-place paragraph & table cell | **100.0% Font/Bold & 100.0% Bảng** | 41.03 ms |
| **Microsoft PowerPoint (.pptx)** | In-place slide text shape + AutoFit | **100.0% Slide & AutoFit Text** | 40.27 ms |
| **PDF Scan / Ảnh chụp** | PyMuPDF Pixmap (200 DPI) + PaddleOCR | **98.2% Text Blocks** | 155.83 ms/trang |
