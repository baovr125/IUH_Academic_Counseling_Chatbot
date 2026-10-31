# CHƯƠNG 1. MẪU KIỂM TRA ĐỊNH DẠNG

Chương này chỉ dùng để kiểm tra bộ công cụ ghép báo cáo: heading nhiều cấp, đoạn văn, danh sách, hình, bảng, công thức, mã nguồn và ghi chú cần bổ sung. Nội dung không phải bản thảo chính thức.

## 1.1 Đoạn văn, danh sách và trích dẫn

Đoạn nội dung dùng style Content: Times New Roman 13, cách trên 10 pt, giãn dòng 1,5, căn đều hai bên và không thụt đầu dòng. Thuật ngữ lần đầu xuất hiện được ghi đầy đủ, ví dụ sinh tăng cường truy xuất (Retrieval-Augmented Generation – RAG) [3]. Từ lần sau chỉ dùng viết tắt RAG. Văn bản có thể có **chữ đậm**, *chữ nghiêng* và tên hàm trong định dạng mã như `retrieve_relevant_chunks_multi`. Trích dẫn nhiều nguồn ghi dạng [1], [3] hoặc [2]–[4].

Danh sách gạch đầu dòng dùng style Bullet:

- truy xuất dày (dense retrieval) dựa trên vector nhúng;
- truy xuất thưa (sparse retrieval) dựa trên từ khóa;
    - mục con cấp hai để kiểm tra thụt lề;
- hợp nhất kết quả bằng RRF.

Danh sách đánh số:

1. Viết lại câu hỏi thành câu độc lập.
2. Truy xuất ứng viên và xếp hạng lại.
3. Sinh câu trả lời kèm trích dẫn.

### 1.1.1 Tiểu mục cấp ba thứ nhất

Heading 3 in đậm và nghiêng, cách trên 6 pt, cách dưới 12 pt.

#### 1.1.1.1 Tiểu mục cấp bốn thứ nhất

Heading 4 in nghiêng, không vào mục lục.

#### 1.1.1.2 Tiểu mục cấp bốn thứ hai

Mỗi mục đã chia phải có ít nhất hai tiểu mục.

### 1.1.2 Tiểu mục cấp ba thứ hai

Đoạn văn của tiểu mục cấp ba thứ hai.

## 1.2 Hình, bảng và công thức

Như Hình 1.1 cho thấy, hình được căn giữa và chú thích nằm dưới hình. Số hiệu "1.1" là trường STYLEREF và SEQ nên Word tự đánh lại khi thêm hoặc bớt hình.

![Hình 1.1. Logo mới của Trường Đại học Công nghiệp TP. Hồ Chí Minh (Nguồn: [1])](../../figures/iuh_logo_new.png){width=9cm}

Bảng 1.1 tóm tắt các style chính theo mẫu của Khoa. Chú thích bảng nằm trên bảng, bảng chỉ kẻ đường ngang.

Bảng 1.1. Tóm tắt các style chính theo mẫu của Khoa

| Style | Phông và cỡ chữ | Cách trên / dưới | Giãn dòng |
|---|---|---|---|
| Heading 1 | TNR 14, đậm, in hoa | 24 pt / 24 pt | 1,15 |
| Heading 2 | TNR 13, đậm | 6 pt / 12 pt | 1,15 |
| Heading 3 | TNR 13, đậm nghiêng | 6 pt / 12 pt | 1,15 |
| Heading 4 | TNR 13, nghiêng | 6 pt / 12 pt | 1,15 |
| Content | TNR 13 | 10 pt / 0 pt | 1,5 |
| Caption | TNR 13 | 6 pt / 12 pt | 1,15 |

Độ tương tự cosine giữa vector truy vấn và vector tài liệu được tính theo công thức (1-1):

$$ \cos(\mathbf{q},\mathbf{d})=\frac{\mathbf{q}\cdot\mathbf{d}}{\lVert\mathbf{q}\rVert\,\lVert\mathbf{d}\rVert}=\frac{\sum_{i=1}^{n} q_i d_i}{\sqrt{\sum_{i=1}^{n} q_i^2}\,\sqrt{\sum_{i=1}^{n} d_i^2}} \tag{1-1} $$

trong đó: $\mathbf{q}$ là vector nhúng của câu truy vấn; $\mathbf{d}$ là vector nhúng của đoạn tài liệu; $n$ là số chiều của vector; $\lVert\cdot\rVert$ là chuẩn Euclid.

Hợp nhất thứ hạng nghịch đảo [2] cộng điểm của một tài liệu qua nhiều danh sách xếp hạng, như công thức (1-2):

$$ \operatorname{RRF}(d)=\sum_{r\in R}\frac{1}{k+\operatorname{rank}_r(d)} \tag{1-2} $$

trong đó: $R$ là tập các danh sách xếp hạng; $\operatorname{rank}_r(d)$ là vị trí của tài liệu $d$ trong danh sách $r$; $k$ là hằng số làm mượt.

Công thức dài có phân số lồng nhau, như BM25 ở công thức (1-3):

$$ \operatorname{BM25}(q,d)=\sum_{t\in q}\operatorname{IDF}(t)\cdot\frac{f(t,d)\,(k_1+1)}{f(t,d)+k_1\left(1-b+b\,\frac{|d|}{\mathrm{avgdl}}\right)} \tag{1-3} $$

## 1.3 Mã nguồn và ghi chú cần bổ sung

Đoạn mã ngắn đặt trong khung, phông Consolas 10:

```python
def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return scores
```

> [TODO: ví dụ ghi chú cần bổ sung — style TODO có nền vàng để dễ thấy khi duyệt bản thảo.]

## Tiểu kết chương {.unnumbered}

Mục tiểu kết dùng Heading 2 không đánh số nhưng vẫn có trong mục lục.
