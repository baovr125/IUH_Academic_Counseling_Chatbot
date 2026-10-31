# ABSTRACT {.unnumbered}

Students of the Industrial University of Ho Chi Minh City (IUH) have to look up academic regulations, tuition, scholarships and administrative procedures that are scattered over several websites and many PDF documents. General-purpose chatbots based on large language models (LLMs) can answer in natural language but may produce wrong answers without any official source. This thesis builds IUH_Academic_Counseling_Chatbot, a web system with a microservices architecture whose core is an academic advising chatbot based on Retrieval-Augmented Generation (RAG).

A knowledge-base pipeline collects IUH web pages and PDF files (with OCR for scanned files), cleans the text, splits it into parent–child chunks and stores 768-dimensional embeddings in PostgreSQL with pgvector. Each question passes through a regular-expression safety filter, an LLM router, a two-tier semantic cache, hybrid retrieval fusing vector and full-text search with Reciprocal Rank Fusion, cross-encoder reranking, parent–child context building, and streamed generation with source citations. Supporting services provide translation, FSRS-scheduled flashcards and JWT authentication behind a Kong API gateway.

The evaluation covers 1,642 automated tests (1,634 passed) and a safety-filter experiment. On 35 labelled questions, the correct document is among the top three retrieved for 94.3% of the questions with cross-encoder reranking (80.0% without), and the median response time of one question is 3.3 seconds. Limitations and future work are also reported.

**Keywords:** Retrieval-Augmented Generation, Hybrid Search, Cross-Encoder Reranking, Semantic Cache, Microservices, Academic Advising Chatbot.

# Lời cảm ơn {.unnumbered .unlisted}

Để hoàn thành khóa luận này, nhóm chúng em đã nhận được sự giúp đỡ của nhiều người, và xin được gửi lời cảm ơn chân thành đến:

Quý thầy cô Khoa Công nghệ Thông tin, Trường Đại học Công nghiệp Thành phố Hồ Chí Minh, đã truyền đạt kiến thức nền tảng trong suốt quá trình học tập.

[TODO: Họ tên và học vị của giáo viên hướng dẫn] đã tận tình hướng dẫn, góp ý về định hướng và cách trình bày để nhóm hoàn thành đề tài.

Gia đình và bạn bè đã động viên và hỗ trợ nhóm trong những lúc khó khăn.

Do hạn chế về thời gian và kiến thức, khóa luận khó tránh khỏi thiếu sót. Nhóm chúng em rất mong nhận được ý kiến đóng góp của quý thầy cô để đề tài được hoàn thiện hơn.

Nhóm chúng em xin chân thành cảm ơn.

# Nhận xét của giáo viên hướng dẫn {.unnumbered .unlisted}

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

Tp. Hồ Chí Minh, ngày …… tháng …… năm 2026

Giáo viên hướng dẫn

(Ký và ghi rõ họ tên)

# Nhận xét của giáo viên phản biện 1 {.unnumbered .unlisted}

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

Tp. Hồ Chí Minh, ngày …… tháng …… năm 2026

Giáo viên phản biện 1

(Ký và ghi rõ họ tên)

# Nhận xét của giáo viên phản biện 2 {.unnumbered .unlisted}

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

.........................................................................................................

Tp. Hồ Chí Minh, ngày …… tháng …… năm 2026

Giáo viên phản biện 2

(Ký và ghi rõ họ tên)

# Mục lục {.unnumbered .unlisted}

[[TOC]]

# Danh mục hình ảnh {.unnumbered}

[[LOF]]

# Danh mục bảng biểu {.unnumbered}

[[LOT]]

# Danh mục từ viết tắt {.unnumbered}

| Từ viết tắt | Từ đầy đủ | Nghĩa |
|---|---|---|
| AI | Artificial Intelligence | Trí tuệ nhân tạo |
| ANN | Approximate Nearest Neighbor | Tìm láng giềng gần đúng |
| API | Application Programming Interface | Giao diện lập trình ứng dụng |
| AWQ | Activation-aware Weight Quantization | Lượng tử hóa trọng số có xét kích hoạt |
| BFS | Breadth-First Search | Duyệt theo chiều rộng |
| BM25 | Best Matching 25 | Hàm xếp hạng văn bản theo tần suất từ |
| CEFR | Common European Framework of Reference for Languages | Khung tham chiếu trình độ ngôn ngữ châu Âu |
| CI | Continuous Integration | Tích hợp liên tục |
| CORS | Cross-Origin Resource Sharing | Chia sẻ tài nguyên giữa các nguồn gốc khác nhau |
| CPU | Central Processing Unit | Bộ xử lý trung tâm |
| CRAG | Corrective Retrieval Augmented Generation | RAG có hiệu chỉnh truy xuất |
| CSDL | — | Cơ sở dữ liệu |
| CSS | Cascading Style Sheets | Ngôn ngữ định kiểu trang web |
| CSV | Comma-Separated Values | Tệp giá trị phân tách bằng dấu phẩy |
| DPI | Dots Per Inch | Số điểm ảnh trên mỗi inch |
| ECE | Expected Calibration Error | Sai số hiệu chỉnh kỳ vọng |
| ERD | Entity Relationship Diagram | Sơ đồ thực thể liên kết |
| FK | Foreign Key | Khóa ngoại |
| FSRS | Free Spaced Repetition Scheduler | Bộ lập lịch lặp lại ngắt quãng |
| GB | Gigabyte | Đơn vị dung lượng |
| GIN | Generalized Inverted Index | Chỉ mục đảo ngược tổng quát |
| GPU | Graphics Processing Unit | Bộ xử lý đồ họa |
| HNSW | Hierarchical Navigable Small World | Đồ thị phân cấp tìm láng giềng gần đúng |
| HS256 | HMAC using SHA-256 | Thuật toán ký JWT dùng khóa chung |
| HTML | HyperText Markup Language | Ngôn ngữ đánh dấu siêu văn bản |
| HTTP | HyperText Transfer Protocol | Giao thức truyền siêu văn bản |
| HTTPS | HyperText Transfer Protocol Secure | HTTP có mã hóa |
| INT8 | 8-bit Integer | Số nguyên 8 bit (dùng khi lượng tử hóa) |
| IP | Internet Protocol | Địa chỉ giao thức Internet |
| IPA | International Phonetic Alphabet | Bảng phiên âm quốc tế |
| IUH | — | Trường Đại học Công nghiệp Thành phố Hồ Chí Minh |
| JSON | JavaScript Object Notation | Định dạng dữ liệu văn bản |
| JSONB | JSON Binary | Kiểu dữ liệu JSON nhị phân của PostgreSQL |
| JWT | JSON Web Token | Mã thông báo xác thực dạng JSON |
| LLM | Large Language Model | Mô hình ngôn ngữ lớn |
| MB | Megabyte | Đơn vị dung lượng |
| MD5 | Message-Digest Algorithm 5 | Hàm băm dùng làm mã định danh nội dung |
| MRR | Mean Reciprocal Rank | Hạng nghịch đảo trung bình |
| MSSV | — | Mã số sinh viên |
| NFKC | Normalization Form KC | Dạng chuẩn hóa Unicode tương thích |
| NLLB | No Language Left Behind | Mô hình dịch máy đa ngôn ngữ của Meta |
| OCR | Optical Character Recognition | Nhận dạng ký tự quang học |
| ONNX | Open Neural Network Exchange | Định dạng trao đổi mô hình nơ-ron |
| OWASP | Open Worldwide Application Security Project | Tổ chức về an toàn ứng dụng |
| PDF | Portable Document Format | Định dạng tài liệu di động |
| PK | Primary Key | Khóa chính |
| RAG | Retrieval-Augmented Generation | Sinh tăng cường truy xuất |
| RAM | Random Access Memory | Bộ nhớ truy cập ngẫu nhiên |
| REST | Representational State Transfer | Phong cách thiết kế API qua HTTP |
| RLS | Row Level Security | Bảo mật mức dòng trong cơ sở dữ liệu |
| RPC | Remote Procedure Call | Lời gọi hàm từ xa (hàm trong cơ sở dữ liệu) |
| RRF | Reciprocal Rank Fusion | Hợp nhất thứ hạng nghịch đảo |
| SSE | Server-Sent Events | Sự kiện đẩy từ máy chủ |
| SSL | Secure Sockets Layer | Giao thức mã hóa kết nối |
| TTFT | Time To First Token | Thời gian đến chữ đầu tiên |
| TTS | Text-to-Speech | Chuyển văn bản thành giọng nói |
| UC | Use Case | Ca sử dụng (use case) |
| URL | Uniform Resource Locator | Địa chỉ tài nguyên |
| UUID | Universally Unique Identifier | Mã định danh duy nhất toàn cục |
| VRAM | Video Random Access Memory | Bộ nhớ của GPU |
| XML | Extensible Markup Language | Ngôn ngữ đánh dấu mở rộng |
| XP | Experience Points | Điểm kinh nghiệm (trong trò chơi) |
| XSS | Cross-Site Scripting | Tấn công chèn mã vào trang web |

# Tóm tắt {.unnumbered}

Sinh viên Trường Đại học Công nghiệp Thành phố Hồ Chí Minh (IUH) phải tra cứu quy chế, học phí, học bổng và thủ tục học vụ nằm rải rác trên nhiều website và nhiều văn bản PDF. Các chatbot dựa trên mô hình ngôn ngữ lớn (LLM) có thể trả lời bằng ngôn ngữ tự nhiên nhưng dễ trả lời sai và không dẫn nguồn chính thức. Khóa luận xây dựng IUH_Academic_Counseling_Chatbot, một hệ thống web theo kiến trúc microservices, có lõi là chatbot tư vấn học vụ dựa trên sinh tăng cường truy xuất (RAG).

Pipeline kho tri thức thu thập các trang web và tệp PDF của IUH (có OCR cho bản scan), làm sạch văn bản, phân đoạn theo cặp đoạn cha–con và lưu vector nhúng 768 chiều trong PostgreSQL với pgvector. Mỗi câu hỏi đi qua bộ lọc an toàn dùng biểu thức chính quy, bộ định tuyến LLM viết lại và tách câu hỏi, bộ nhớ đệm ngữ nghĩa hai tầng, truy xuất lai hợp nhất tìm kiếm vector và toàn văn bằng Reciprocal Rank Fusion, xếp hạng lại bằng cross-encoder, dựng ngữ cảnh theo cặp đoạn cha–con, rồi sinh câu trả lời theo luồng kèm thẻ tự đánh giá và trích dẫn nguồn. Các service hỗ trợ gồm dịch thuật, flashcard lập lịch bằng thuật toán FSRS và xác thực JWT sau cổng API Kong.

Việc đánh giá gồm 1 642 kiểm thử tự động (1 634 đạt), thí nghiệm về bộ lọc an toàn. Trên 35 câu hỏi có đáp án, tài liệu đúng nằm trong ba hạng đầu ở 94,3% câu khi có xếp hạng lại bằng cross-encoder (80,0% khi không có), và trung vị thời gian của một lượt hỏi đáp là 3,3 giây. Quá trình đối chiếu với mã nguồn cũng chỉ ra các hạn chế, như bộ lọc an toàn chặn nhầm câu hợp lệ và phiên hội thoại chưa kiểm tra chủ sở hữu, được bàn cùng các hướng phát triển.

**Từ khóa:** sinh tăng cường truy xuất, tìm kiếm lai, xếp hạng lại bằng cross-encoder, bộ nhớ đệm ngữ nghĩa, microservices, chatbot tư vấn học vụ.
