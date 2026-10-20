# 🎬 KỊCH BẢN PHÂN CẢNH MASTERCLASS (FULL STORYBOARD & TECHNICAL SPECIFICATION)
# CHUYÊN ĐỀ: KIẾN TRÚC DỊCH VỤ ACADEMIC CHATBOT SERVICE & 2-STAGE HYBRID RAG
> **Dự án**: IUH Academic Counseling Chatbot  
> **Thời lượng video**: ~13 - 15 phút (800 - 900 giây, 60fps = 48.000 - 54.000 khung hình)  
> **Định dạng sản xuất**: Remotion (React Framework), 1920x1080 Full HD, 60 FPS  
> **Tài liệu lời thoại đính kèm**: [`video/voiceover-script.md`](file:///home/anhhao/workSpace/IUH_Academic_Counseling_Chatbot/video/voiceover-script.md)  
> **Thư mục tài liệu nghiên cứu**: [`paper/`](file:///home/anhhao/workSpace/IUH_Academic_Counseling_Chatbot/paper/)

---

## 🔬 PHẦN I: MA TRẬN SO SÁNH KIẾN TRÚC & CƠ SỞ KHOA HỌC (THEORETICAL FOUNDATION)

### 1. Bảng So Sánh Toàn Diện: Naive RAG vs. Advanced RAG (với các Module chọn lọc của Dự án)

| Tiêu chí kỹ thuật | Kiến trúc Naive RAG (Cơ bản) | Kiến trúc Dự án (Advanced RAG + Selected Modular Elements) | Giải thích cho Giảng viên / Sinh viên (Non-IT) |
| :--- | :--- | :--- | :--- |
| **Chiến lược phân mảnh (Chunking)** | Cắt cố định (Fixed-size: 500 ký tự). Cắt đứt đôi câu văn hoặc bảng biểu. | **Hybrid Parent-Child Chunking**: Parent (max 1200 tokens theo header Markdown), Child (max 600 ký tự, overlap 100). | Giống như việc đọc trọn vẹn một điều luật có tiêu đề rõ ràng, thay vì nhặt từng mẩu giấy vụn bị xé rách giữa chừng. |
| **Bảo tồn Bảng biểu (Tables)** | Mù bảng (Table-blind): Cắt ngang các hàng, mất liên kết giữa dòng và cột. | **Table-Aware Splitter**: Tự động nhận diện bảng và nhân bản dòng tiêu đề cột vào mọi mảnh con. | Khi tra bảng học phí hoặc thang điểm rèn luyện, mọi con số đều có tên cột tương ứng, không bị nhầm lẫn giữa điểm môn học và điểm rèn luyện. |
| **Không gian nhúng (Embedding)** | Thường dùng model đa ngôn ngữ chung chung, không hiểu sâu tiếng Việt và thuật ngữ đào tạo. | `bkai-foundation-models/vietnamese-bi-encoder` (**768 chiều**), nhúng kèm phân cấp danh mục `[Tuyển sinh > Xét học bạ]`. | Vector hiểu được ngữ cảnh chuyên biệt của tiếng Việt và cấu trúc văn bản hành chính Việt Nam. |
| **Phương thức tìm kiếm (Retrieval)** | Chỉ dùng Vector đơn lẻ (Dense only). Hay bỏ sót mã môn học (`4203001`), từ viết tắt (`GPA`). | **Hybrid Search kết hợp Reciprocal Rank Fusion ($k=60$)**: Chạy song song Dense HNSW Cosine (768d) và Sparse FTS simple `tsvector`. | Kết hợp cả trí nhớ ngữ nghĩa tự nhiên của AI lẫn khả năng tra cứu chính xác từng chữ của mục lục máy tính. |
| **Xếp hạng lại (Reranking)** | Không có reranking. Phụ thuộc hoàn toàn vào top-k tương đồng vector ban đầu. | **Cross-Encoder Reranker**: `BAAI/bge-reranker-v2-m3` đọc chéo cặp (Query, Doc), loại bỏ tài liệu rác dưới ngưỡng 0.20. | Như một vị giám khảo thứ hai đọc kỹ lại từng câu để đảm bảo tài liệu thực sự trả lời đúng thắc mắc của sinh viên. |
| **Tình trạng chen chúc tài liệu** | Các câu vụn của cùng 1 điều dài chiếm sạch top-k, làm mất các điều luật khác. | **Parent-Aware Quota Deduplication**: Gom nhóm theo `parent_id`, chỉ giữ 1 câu con điểm cao nhất cho mỗi Điều khoản. | Đảm bảo mỗi điều luật quan trọng đều có đại diện trong danh sách, không để một điều luật dài chiếm sóng toàn bộ. |
| **Mở rộng ngữ cảnh (Context)** | Gửi nguyên mảnh con vụn về cho LLM đọc, dẫn đến suy diễn thiếu căn cứ. | **Small-to-Big Retrieval Collapse**: Tìm kiếm bằng mảnh con nhạy bén, nhưng nạp toàn bộ điều khoản cha cho LLM đọc. | Tìm kiếm nhanh như tra từ điển, nhưng khi trả lời thì đọc cả trang sách để hiểu trọn vẹn quyền lợi sinh viên. |
| **Hiện tượng "Lost in the Middle"** | Nối chuỗi văn bản ngẫu nhiên. LLM bị "đãng trí" ở giữa ngữ cảnh (Liu et al., 2023). | **Sandwich Reordering**: Hoán vị `[#1, #3, #5, ..., #4, #2]`, đưa tài liệu quan trọng nhất ra 2 đầu Prompt + `<query_reminder>`. | Đặt những thông tin quan trọng nhất vào ngay trước mắt và ngay dòng cuối cùng để AI luôn ghi nhớ, không bị quên. |
| **Bộ đệm Ngữ nghĩa (Caching)** | Không có cache hoặc chỉ cache chuỗi ký tự thô. Tốn chi phí API và độ trễ cao. | **2-Stage Semantic Cache**: Redis O(1) + pgvector Bi-Encoder 768d ($\ge 0.60$) $\rightarrow$ Cross-Encoder ($\ge 0.80$) + Kiểm tra thực thể số. | Sinh viên hỏi câu quen thuộc nhận được phản hồi tức thì dưới 50ms, đồng thời tuyệt đối không bao giờ nhầm lẫn giữa "Học kỳ 1" và "Học kỳ 2". |
| **Cổng an toàn kiểm soát Cache** | Không có. Câu trả lời lỗi hoặc bị ảo giác vẫn bị lưu vào cache, lây lan cho sinh viên khác. | **Gated Write-Back**: Chỉ lưu khi điểm tài liệu $\ge 0.25$, Self-RAG `<doc_relevance> != NO` và `<answer_confidence> == HIGH`. | Cổng kiểm duyệt chất lượng nghiêm ngặt: chỉ những câu trả lời chuẩn xác 100% và được kiểm chứng mới được ghi vào sổ nhớ chung. |
| **Bảo vệ Prompt Injection** | Dễ bị người dùng lừa đảo chèn mã bẻ khóa (Jailbreak) vào câu hỏi. | **XML Sandboxing & Tag Blocker**: Bọc tài liệu trong `<retrieved_context>`, chặn đứng mọi thẻ hệ thống (`<thinking>`, `<|im_start|>`). | Như một buồng cách ly vô trùng, sinh viên có cố tình gõ lệnh bẻ khóa thì hệ thống cũng nhận diện và chặn đứng từ ngoài cửa. |

---

### 2. Danh Mục Các Công Trình Nghiên Cứu Khoa Học Đã Tham Khảo & Đối Soát (Literature Mapping)

Toàn bộ các tài liệu gốc được lưu trữ tại thư mục [`/paper/`](file:///home/anhhao/workSpace/IUH_Academic_Counseling_Chatbot/paper/):

```
IUH_Academic_Counseling_Chatbot/paper/
├── check_2312.10997v5.pdf     # 1. RAG Survey (Gao et al., 2023 - Tongji/Fudan)
├── check2307.03172v3.pdf     # 2. Lost in the Middle (Liu et al., 2023 - Stanford/Berkeley)
├── 2401.15884v3.pdf          # 3. Corrective RAG - CRAG (Yan et al., 2024 - USTC/DeepMind)
├── check2310.11511v1.pdf     # 4. Self-RAG (Asai et al., 2023 - Univ. of Washington/Allen AI)
├── check2305.14283v3.pdf     # 5. Rewrite-Retrieve-Read (Ma et al., 2023 - SJTU/Microsoft)
├── processing2212.10496v1.pdf # 6. HyDE (Gao et al., 2022 - CMU/Waterloo)
└── check2605.18209v1.pdf     # 7. SpatioRoute (Chunhachatrachai et al., 2024 - NTU)
```

#### Phân tích chi tiết từng nghiên cứu:

1. **Gao et al. (2023) — *Retrieval-Augmented Generation for Large Language Models: A Survey***:
   * *Nội dung chứng minh*: Phân loại quá trình tiến hóa: Naive RAG $\rightarrow$ Advanced RAG $\rightarrow$ Modular RAG. Advanced RAG giải quyết các điểm nghẽn bằng Pre-retrieval (phân rã câu hỏi, chunking hạt mịn) và Post-retrieval (reranking, sandwich reordering).
   * *Lý do chọn Advanced RAG + Selected Modular RAG thay vì Modular RAG toàn phần*: Modular RAG phân rã toàn bộ hệ thống thành các Agent phi tập trung giao tiếp qua mạng. Trong môi trường trường đại học phục vụ hàng nghìn sinh viên đồng thời vào mùa thi và mùa học phí, kiến trúc Modular RAG thuần túy tạo ra độ trễ quá lớn (5-10 giây/request), chi phí hạ tầng tăng vọt và nguy cơ trôi dạt trạng thái (state drift). Do đó, dự án chọn **Advanced RAG làm bộ khung vững chắc**, chỉ tích hợp 5 module thực dụng nhất của Modular RAG (Semantic Cache, Fusion Search, Dynamic Routing, Semantic Memory, Quality Gate).

2. **Liu et al. (Stanford / UC Berkeley, 2023) — *Lost in the Middle: How Language Models Use Long Contexts***:
   * *Nội dung chứng minh*: Đường cong nhận thức của Transformer có hình chữ U (U-curve): Chú ý cực mạnh ở đầu và cuối ngữ cảnh, suy giảm nghiêm trọng ở khu vực chính giữa.
   * *Điểm áp dụng trong dự án*: Thuật toán `_sandwich_reorder` trong `query_filter.py` hoán vị danh sách tài liệu từ `[#1, #2, #3, #4, #5]` sang `[#1, #3, #5, #4, #2]`. Thêm thẻ `<query_reminder>` ở cuối prompt để tận dụng tối đa hiệu ứng Recency.
   * *Điểm loại bỏ*: Bài báo đề xuất kỹ thuật chạy thử nhiều hoán vị khác nhau (exhaustive permutation) rồi lấy trung bình. Chúng tôi loại bỏ cách này vì làm tăng chi phí và thời gian gọi LLM lên gấp N lần; thay vào đó, chúng tôi dùng hoán vị xác định O(N) duy nhất.

3. **Yan et al. (USTC / Google DeepMind, 2024) — *Corrective Retrieval Augmented Generation (CRAG)***:
   * *Nội dung chứng minh*: Đưa thêm bộ thẩm định tài liệu (Retrieval Evaluator) để chấm điểm mức độ liên quan trước khi cho phép LLM tổng hợp câu trả lời.
   * *Điểm áp dụng trong dự án*: Áp dụng bộ lọc ngưỡng điểm rerank `top_doc_score >= 0.25` và thẻ phản tư `<doc_relevance>`.
   * *Điểm loại bỏ*: Trong bài báo CRAG, khi tài liệu nội bộ không đạt chất lượng, hệ thống tự động kích hoạt Web Search (Google/Bing). Trong dự án IUH, chúng tôi **kiên quyết loại bỏ Web Search**. Lý do: Quy chế đào tạo đại học là văn bản pháp lý nội bộ mang tính quy chuẩn. Tìm kiếm Internet mở sẽ kéo về các bài viết blog rác, diễn đàn sinh viên cũ kỹ hoặc quy chế của các trường khác, gây nguy hiểm khôn lường cho quyền lợi sinh viên. Thay vào đó, hệ thống từ chối an toàn và hướng dẫn sinh viên đến đúng Phòng Đào tạo.

4. **Asai et al. (Univ. of Washington / Allen AI, 2023) — *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection***:
   * *Nội dung chứng minh*: Dùng các token phản tư đặc biệt (`[IsRel]`, `[IsSup]`, `[IsUse]`) để mô hình tự phê bình độ chính xác của câu trả lời.
   * *Điểm áp dụng trong dự án*: Tích hợp thẻ `<thinking>` chứa `<doc_relevance>`, `<conflict_detected>` và `<answer_confidence>` vào cấu trúc suy luận của LLM. Dùng các thẻ này làm điều kiện khóa cổng Gated Cache Write-Back.
   * *Điểm điều chỉnh*: Bài báo gốc phải fine-tune lại trọng số mô hình với các token đặc biệt. Chúng tôi chuyển hóa thành dạng XML-prompting có kiểm soát, tương thích hoàn hảo với mọi LLM thương mại và mã nguồn mở (Gemini 3.5 Flash, Qwen-2.5) mà không cần tốn hàng nghìn USD huấn luyện lại.

5. **Ma et al. (Microsoft Research / SJTU, 2023) — *Query Rewriting for Retrieval-Augmented Large Language Models***:
   * *Nội dung chứng minh*: Mô hình Rewrite-Retrieve-Read khắc phục khoảng cách giữa cách hỏi của người dùng và từ ngữ trong cơ sở dữ liệu tri thức.
   * *Điểm áp dụng trong dự án*: Xây dựng module `Adaptive Query Rewriter & Router` chạy mô hình Qwen-2.5 cục bộ để phân rã câu hỏi kép thành 1-3 truy vấn con độc lập và chuẩn hóa tiếng lóng sinh viên về từ ngữ quy chế.
   * *Điểm điều chỉnh*: Bài báo dùng thuật toán PPO học tăng cường. Chúng tôi dùng Dynamic Few-shot Prompting với schema JSON và Guardrails, giúp hệ thống không bị overfit và dễ dàng cập nhật quy tắc nghiệp vụ mới mà không cần train lại.

6. **Gao & Callan (Carnegie Mellon University, 2022) — *Precise Zero-Shot Dense Retrieval without Relevance Labels (HyDE)***:
   * *Nội dung phân tích & Lý do loại bỏ*: HyDE sinh ra một câu trả lời giả định rồi dùng vector của câu giả định đó để tìm tài liệu thật. Nhóm phát triển đã thử nghiệm HyDE nhưng **chủ động loại bỏ**. Nguyên nhân: Trong văn bản pháp lý, các con số chế tài (ví dụ điểm GPA cảnh báo học vụ, số tín chỉ bắt buộc, phần trăm hoàn tiền học phí) là bất biến. HyDE thường khiến LLM "đoán mò" ra các con số sai, và vector của con số sai đó lại kéo về các điều khoản không phù hợp, làm trầm trọng thêm tình trạng ảo giác. Thay vào đó, chúng tôi dùng **Hierarchical Augmented Context** để giải bài toán zero-shot một cách chính xác tuyệt đối.

7. **Chunhachatrachai et al. (National Taiwan University, 2024) — *SPATIOROUTE: Dynamic Prompt Routing***:
   * *Nội dung chứng minh*: Việc định tuyến câu hỏi động sang các mẫu Prompt chuyên biệt tốt hơn rất nhiều so với việc dùng một siêu Prompt (Monolithic Prompt) ôm đồm mọi thứ.
   * *Điểm áp dụng trong dự án*: Xây dựng bộ định tuyến 7 ý định (`REGULATION`, `PROCEDURE`, `CRISIS`, `ADVISING`, `COMPLAINT`, `TECH_SUPPORT`, `GENERAL`). Tinh giản Prompt tuyến `REGULATION` giảm 64% token, bổ sung Chuỗi tư duy số học (Arithmetic CoT) và nguyên tắc phân định quyền lợi ("Được phép / Không được phép").

---

### 3. Bảng Ánh Xạ & Tích Hợp Assets Hình Ảnh Thực Tế (Image Assets Integration Matrix)

Toàn bộ các tệp hình ảnh được lưu trữ tại thư mục [`video/public/images/`](file:///home/anhhao/workSpace/IUH_Academic_Counseling_Chatbot/video/public/images/):

| Tên File Asset | Độ phân giải / Loại | Mô tả Nội dung Thực tế | Phân Cảnh Sử Dụng (Scene) | Mục đích & Vai trò Truyền đạt |
| :--- | :--- | :--- | :--- | :--- |
| **`anh-nha-E-iuh.jpg`** | 739x415 (JPEG) | Ảnh chụp thực tế Nhà E - Cơ sở chính Trường ĐH Công nghiệp TP.HCM (trụ sở Ban Giám hiệu, Phòng Đào tạo). | **Scene 1** (Mở đầu) & **Scene 9** (Tổng kết) | **Thiết lập bối cảnh thực tế (Establishing shot)**: Khẳng định tính ứng dụng của Chatbot tại chính ngôi trường IUH, tạo sự gần gũi cho sinh viên và thầy cô. |
| **`banner_camnang.png`** | 5000x2296 (PNG 4K) | Banner chính thức góc rộng: *"CẨM NANG NGƯỜI HỌC - student guideline"*, logo IUH sắc nét và 2 sinh viên cầm cẩm nang học vụ. | **Scene 1** (0:10) & **Scene 4** (Tiền xử lý dữ liệu) | **Nguồn tri thức cốt lõi**: Minh họa văn bản quy chế chính thức mà hệ thống RAG cần xử lý, đối lập giữa tài liệu quy chuẩn và nguy cơ cắt vụn của Naive RAG. |
| **`sotaysinhvien.jpg`** | 447x447 (JPEG) | Bìa tài liệu thực tế *"SỔ TAY SINH VIÊN 2021"* của IUH. | **Scene 1** & **Scene 4** (Chunking) | **Minh họa bài toán xung đột niên khóa (CF-RAG)**: Thể hiện quy chế thay đổi qua các năm (2021, 2023, 2026), giải thích vì sao cần ưu tiên Khóa tuyển sinh > Năm ban hành. |
| **`naive-advance-modular-RAG.jpg`** | 739x415 (JPEG) | Sơ đồ 3 cột chuẩn mực trích từ nghiên cứu khoa học Gao et al. (2023, Tongji/Fudan) phân biệt: Naive RAG, Advanced RAG, Modular RAG. | **Scene 2** (Cơ sở khoa học & So sánh kiến trúc) | **Cột mốc lý thuyết trung tâm**: Dùng làm hình ảnh tham chiếu khi kỹ sư AI giải thích lý do chọn Advanced RAG + 5 module thay vì Full Modular RAG. |
| **`lost-in-the-middle-U-shaped performance curve.png`** | 831x780 (PNG) | Đồ thị thực nghiệm hình chữ U trích từ công trình Nelson Liu et al. (Stanford / Berkeley) đo lường độ chính xác suy giảm ở giữa context. | **Scene 3** (Bản đồ nghiên cứu) & **Scene 7** (Sandwich Reordering) | **Bằng chứng thực nghiệm đắt giá**: Chứng minh hiện tượng mất tập trung của Transformer, tạo cơ sở toán học thuyết phục cho thuật toán `_sandwich_reorder`. |
| **`tuvantuyensinhbanner.jpg`** | 1953x1277 (JPEG) | Poster chương trình *"Tư vấn tuyển sinh liên thông đại học, đại học từ xa"*. | *Đã loại bỏ (Không sử dụng)* | **Không phù hợp**: Nội dung tuyển sinh liên thông / từ xa không khớp với phạm vi tư vấn quy chế học vụ sinh viên chính quy. |

---

## 🎬 PHẦN II: CHI TIẾT 9 PHÂN CẢNH SẢN XUẤT (DETAILED REMOTION STORYBOARD)


---

### SCENE 1: MỞ ĐẦU & TỬ HUYỆT CỦA NAIVE RAG TRONG TƯ VẤN HỌC VỤ (0:00 - 1:15) — 75 GIÂY

* **Khung hình**: Frame 0 đến 4.500 (60 fps).
* **Mục tiêu**: Nêu bật bối cảnh đại học IUH, đặt vấn đề về sự phức tạp của quy chế học vụ, và phân tích sâu sắc tại sao cách làm Naive RAG (RAG ngây thơ) lại hoàn toàn thất bại.
* **Âm thanh & Hiệu ứng**:
  * Nhạc mở đầu công nghệ hiện đại, tự tin, tiết tấu vừa phải.
  * Âm thanh gõ bàn phím (typing SFX), tiếng "buzz" báo lỗi khi Naive RAG đưa thông tin sai lệch.
* **Mô tả thị giác (Visual & Animation)**:
  1. *0:00 - 0:25*: 
     - **Establishing shot**: Hiển thị ảnh thực tế Nhà E IUH (`public/images/anh-nha-E-iuh.jpg`) với hiệu ứng slow pan cinematic sang trọng, góc nhìn hướng lên tòa nhà biểu tượng của Phòng Đào tạo & Văn phòng Trường.
     - **Knowledge Source Showcase**: Hiện banner chính thức *"CẨM NANG NGƯỜI HỌC"* (`public/images/banner_camnang.png`) góc rộng với 2 sinh viên IUH, bên cạnh là bìa cuốn *"SỔ TAY SINH VIÊN"* (`public/images/sotaysinhvien.jpg`). Thể hiện nguồn dữ liệu học vụ đồ sộ hàng trăm trang.
     - Một sinh viên K19 gửi câu hỏi: *"Em bị cảnh báo học vụ lần 1 thì học kỳ tới được đăng ký tối đa bao nhiêu tín chỉ?"*.
  2. *0:25 - 0:50*: Đồ họa mô phỏng Naive RAG: 
     - Lưỡi kéo cơ học cắt ngang dòng chữ: `[Sinh viên bị cảnh báo học vụ... (Hết Chunk 1)]` $\rightarrow$ Mảnh tiếp theo: `[...chỉ được đăng ký tối đa 14 tín chỉ (Chunk 2)]`.
     - Bộ thu hồi chỉ nhặt được Chunk 1. Mô hình AI hiển thị bong bóng chat bịa đặt: *"Bạn được đăng ký thoải mái không giới hạn!"* $\rightarrow$ Biển báo nguy hiểm màu đỏ: **ẢO GIÁC HỌC VỤ NGUY HIỂM!**
  3. *0:50 - 1:15*: 4 biểu tượng tử huyệt của Naive RAG hiện lên:
     - ✂️ *Cắt vụn mất ngữ cảnh (Context Truncation)*.
     - 🔤 *Xung đột Từ khóa - Vector (Vocabulary Mismatch)*.
     - 📢 *Khuếch đại Ảo giác (Hallucination Amplification)*.
     - 🧩 *Bất lực trước câu hỏi kép (Compound Query Blindness)*.

---

### SCENE 2: CƠ SỞ KHOA HỌC & LỰA CHỌN: ADVANCED RAG HAY MODULAR RAG? (1:15 - 3:00) — 105 GIÂY

* **Khung hình**: Frame 4.500 đến 10.800.
* **Mục tiêu**: Đưa người xem đến chiều sâu học thuật: Phân tích báo cáo tổng quan của Gao et al. (2023). Trả lời thuyết phục câu hỏi: "Vì sao chọn Advanced RAG + Selected Modules mà không phải toàn bộ Modular RAG?".
* **Âm thanh & Hiệu ứng**:
  * Tiếng lật trang tài liệu nghiên cứu khoa học, âm thanh "ding" công nghệ khi các thẻ nghiên cứu hiện lên.
* **Mô tả thị giác (Visual & Animation)**:
  1. *1:15 - 1:45*: 
     - Hiển thị bìa bài báo khoa học `check_2312.10997v5.pdf` (*Retrieval-Augmented Generation for Large Language Models: A Survey* - Gao et al., Tongji & Fudan Univ).
     - **Tâm điểm thị giác**: Phóng to bức ảnh sơ đồ 3 thế hệ kiến trúc RAG chính thức từ paper (`public/images/naive-advance-modular-RAG.jpg`):
       - Cột 1: *Naive RAG* (Retrieve $\rightarrow$ Read).
       - Cột 2: *Advanced RAG* (Pre-Retrieval [Rewrite, Route, Expand] $\rightarrow$ Retrieval $\rightarrow$ Post-Retrieval [Rerank, Reorder, Fuse]).
       - Cột 3: *Modular RAG* (Mạng lưới đa Module linh hoạt).
  2. *1:45 - 2:30*: **Bảng phân tích đánh đổi của Kỹ sư AI (Engineering Trade-off)**:
     - Mô hình Modular RAG thuần túy: Hiện đồ thị mạng nhện phức tạp, đồng hồ đếm độ trễ tăng vọt lên **8.5 giây**, chi phí token đỏ rực. Kèm nhãn cảnh báo: *Quá tải hệ thống khi 5.000 sinh viên cùng tra cứu mùa thi!*
     - Mô hình Advanced RAG + Selected Modules của dự án: Tinh gọn, luồng đi thẳng tắp, đồng hồ độ trễ xanh mướt **0.8 giây - 1.2 giây**, phản hồi tức thì.
  3. *2:30 - 3:00*: Hiển thị 5 Module được chắt lọc từ Modular RAG tích hợp vào bộ khung:
     - ⚡ Module 1: *2-Stage Semantic Cache*.
     - 🔍 Module 2: *Hybrid Fusion Search (RRF)*.
     - 🧭 Module 3: *Dynamic SpatioRoute*.
     - 🧠 Module 4: *Semantic Past-Chat Memory*.
     - 🛡️ Module 5: *Self-RAG Quality Gate*.

```mermaid
flowchart LR
    subgraph Modular_RAG_Tradeoff ["Đánh đổi: Modular RAG thuần túy vs Advanced RAG chọn lọc"]
        direction TB
        ModRAG["🕸️ Full Modular RAG\n(Decoupled Multi-Agent DAG)\n• Độ trễ cao: 5 - 10s\n• Nguy cơ trôi dạt trạng thái\n• Khó bảo trì trong giáo dục"]
        AdvRAG["⚡ Advanced RAG + 5 Selected Modules (IUH Chatbot)\n• Xương sống: Pre-retrieval + Post-retrieval\n• Độ trễ thấp: < 1.5s\n• Tính tất định cao, kiểm soát tuyệt đối"]
    end
```

---

### SCENE 3: BẢN ĐỒ NGHIÊN CỨU: ÁP DỤNG ĐIỂM NÀO, LOẠI BỎ ĐIỂM NÀO? (3:00 - 5:15) — 135 GIÂY

* **Khung hình**: Frame 10.800 đến 18.900.
* **Mục tiêu**: Trích dẫn danh chính ngôn thuận 5 bài báo khoa học trong thư mục `/paper/`, nêu rõ cơ chế nào được đưa vào code, cơ chế nào bị chủ động loại bỏ vì không phù hợp với văn bản pháp lý IUH.
* **Âm thanh & Hiệu ứng**:
  * Âm thanh con dấu đóng "ADOPTED" màu xanh lá và "DISCARDED" màu đỏ gạch.
* **Mô tả thị giác (Visual & Animation)**:
  * Carousel chuyển động mượt mà qua từng bài báo:
    1. **Paper 1: Ma et al. (Microsoft / SJTU) — *Rewrite-Retrieve-Read***:
       - *ADOPTED*: Viết lại câu hỏi đa ý thành 1-3 subqueries độc lập bằng Qwen-2.5 local.
       - *DISCARDED*: Bỏ Reinforcement Learning (PPO) vì dễ overfit; thay bằng Few-Shot Prompting có Guardrail.
    2. **Paper 2: Liu et al. (Stanford / Berkeley) — *Lost in the Middle***:
       - **Hiển thị đồ thị thực nghiệm**: Phóng to hình ảnh gốc từ paper (`public/images/lost-in-the-middle-U-shaped performance curve.png`) biểu diễn độ chính xác tụt dốc hình chữ U từ 76% xuống dưới 54% ở vị trí giữa ngữ cảnh (dưới cả mức closed-book baseline đường đỏ đứt đoạn).
       - *ADOPTED*: Thuật toán hoán vị `_sandwich_reorder` `[#1, #3, ..., #2]` và thẻ `<query_reminder>`.
       - *DISCARDED*: Bỏ exhaustive brute-force permutation vì gây bùng nổ chi phí gọi LLM.
    3. **Paper 3: Yan et al. (USTC / DeepMind) — *Corrective RAG (CRAG)***:
       - *ADOPTED*: Bộ đánh giá chất lượng tài liệu Cross-Encoder (threshold 0.25).
       - *DISCARDED*: **Loại bỏ hoàn toàn Web Search** vì mạng Internet chứa tin rác, quy chế cũ hoặc sai lệch trường khác; hệ thống chỉ dùng CSDL chính thống IUH.
    4. **Paper 4: Asai et al. (Univ. of Washington / Allen AI) — *Self-RAG***:
       - *ADOPTED*: Thẻ phản tư `<thinking>`, `<doc_relevance>`, `<answer_confidence>` làm chốt chặn ghi đệm Cache.
       - *DISCARDED*: Bỏ việc custom token fine-tuning phức tạp; thay bằng XML-prompting đa nền tảng.
    5. **Paper 5: Gao & Callan (CMU) — *HyDE (Hypothetical Document Embeddings)***:
       - *EVALUATED & DISCARDED*: **Loại bỏ HyDE**! Hiển thị đồ họa trực quan: AI đoán bừa một con số GPA giả định $\rightarrow$ Vector của con số sai kéo về toàn tài liệu sai $\rightarrow$ Thay bằng Augmented Context phân cấp chính xác.

---

### SCENE 4: KỸ NGHỆ DỮ LIỆU ĐẦU VÀO: HYBRID PARENT-CHILD & TABLE-AWARE (5:15 - 7:30) — 135 GIÂY

* **Khung hình**: Frame 18.900 đến 27.000.
* **Mục tiêu**: Đi sâu vào file mã nguồn `app/data_ingestion/chunkers/hybrid_chunker.py`. Chứng minh cách phân mảnh giữ nguyên cấu trúc bảng và phả hệ điều khoản.
* **Âm thanh & Hiệu ứng**:
  * Âm thanh phóng to kính hiển vi dữ liệu (zoom SFX), tiếng quét laser cấu trúc văn bản.
* **Mô tả thị giác (Visual & Animation)**:
  1. *Bước 1: Frontmatter Extraction*: 
     - Hiển thị bìa tài liệu thực tế *"CẨM NANG NGƯỜI HỌC"* (`public/images/banner_camnang.png`) và *"SỔ TAY SINH VIÊN"* (`public/images/sotaysinhvien.jpg`) đang được nạp vào luồng xử lý.
     - Trích xuất siêu dữ liệu `source_url`, `title`, `published_date`, `breadcrumbs`.
  2. *Bước 2: Parent Chunks Creation*:
     - Tách theo header `#` đến `######`, giới hạn trần **1.200 tokens**.
     - Nếu một điều quá 1.200 tokens: Tự động kích hoạt Secondary Regex (`**I. ...**`, `**1. ...**`) hoặc phân đoạn Fallback `\n\n`.
  3. *Bước 3: Child Chunks Creation*:
     - Kích thước tối đa 600 ký tự, overlap 100 ký tự.
  4. *Bước 4: Table-Aware Splitter (Điểm sáng kỹ thuật)*:
     - Hoạt họa một bảng học phí Markdown dài 50 dòng: Hàng Header `| Ngành | Số tín chỉ | Học phí / tín chỉ |` được sao chép tự động vào đầu từng chunk con cắt nhỏ!
  5. *Bước 5: Augmented Context*:
     - Ghép chuỗi phân cấp `[Quy chế đào tạo > Chương 3 > Điều 15]` vào đầu chunk con trước khi mã hóa thành vector 768 chiều bởi `bkai-foundation-models/vietnamese-bi-encoder`.

```mermaid
flowchart TD
    Raw["📄 Quy chế Đào tạo (.md)"] --> Front["🏷️ Trích xuất Frontmatter & Breadcrumbs"]
    Front --> Parent["📑 Parent Chunks (Max 1200 tokens theo H1-H6)"]
    
    Parent --> OverCheck{"Section > 1200 tokens?"}
    OverCheck -- "Có" --> SecRegex["✂️ Secondary Regex (**I.** / **1.**) + Paragraph Fallback (\n\n)"]
    OverCheck -- "Không" --> CleanParent["✅ Parent Chunk Chuẩn mực"]
    SecRegex --> CleanParent
    
    CleanParent --> ChildBranch{"Nội dung có Bảng biểu không?"}
    ChildBranch -- "Có Bảng Markdown" --> TableSplit["📊 Table-Aware Splitter:\nNhân bản Table Header vào từng mảnh row con"]
    ChildBranch -- "Văn bản thường" --> TextSplit["📝 Recursive Window Splitter (Max 600 chars, Overlap 100)"]
    
    TableSplit --> Augmented["🏷️ Augmented Text: '[Header Path]\n' + Nội dung con"]
    TextSplit --> Augmented
    
    Augmented --> Vector768["🧬 Bi-Encoder (bkai 768d) -> Lưu pgvector"]
    CleanParent --> DocStore["🗄️ Lưu Document Store nguyên bản cho LLM đọc"]
```

---

### SCENE 5: TỐC ĐỘ VÀ AN TOÀN: BỘ ĐỆM NGỮ NGHĨA 2 GIAI ĐOẠN (2-STAGE SEMANTIC CACHE) (7:30 - 9:30) — 120 GIÂY

* **Khung hình**: Frame 27.000 đến 34.200.
* **Mục tiêu**: Giải thích kiến trúc Semantic Cache trong `rag_service.py`: Tại sao Bi-Encoder Cosine thôi là chưa đủ? Sự cần thiết của Cross-Encoder và Bộ kiểm tra thực thể số.
* **Âm thanh & Hiệu ứng**:
  * Tiếng đồng hồ đếm tốc độ cao (5ms response), tiếng còi từ chối sắc nét khi thực thể số không khớp.
* **Mô tả thị giác (Visual & Animation)**:
  1. *Giai đoạn 1 (High Recall)*:
     - Redis tra cứu O(1) hash key.
     - Supabase pgvector so khớp vector 768 chiều với ngưỡng rộng $\ge 0.60$.
  2. *Giai đoạn 2 (High Precision)*:
     - Đưa cặp `(User Query, Cached Canonical Query)` vào `BAAI/bge-reranker-v2-m3` Cross-Encoder với ngưỡng khắt khe $\ge 0.80$.
     - **Minh họa Entity Numbers Guard**:
       - Câu hỏi mới: *"Hạn nộp học phí học kỳ **1** năm 2026"*
       - Câu hỏi trong Cache: *"Hạn nộp học phí học kỳ **2** năm 2026"*
       - Bi-Encoder Cosine Score: 0.93 (Rất cao do chỉ khác 1 từ!).
       - Bộ lọc thực thể số so sánh: `set(['1', '2026']) != set(['2', '2026'])` $\rightarrow$ **TỪ CHỐI CACHE HIT LẬP TỨC (REJECTED)**! Chuyển sang tìm kiếm CSDL.
  3. *Gated Write-Back (Cổng an toàn)*:
     - 3 điều kiện đồng thời: `top_doc_score >= 0.25`, độ dài $10 \le \text{len} \le 3000$, và reflection `<doc_relevance> != NO` & `<answer_confidence> == HIGH`.

---

### SCENE 6: TRUY XUẤT LAI HỢP HYBRID RRF, QUOTA DEDUPLICATION & BGE-RERANKER (9:30 - 11:30) — 120 GIÂY

* **Khung hình**: Frame 34.200 đến 41.400.
* **Mục tiêu**: Mổ xẻ chi tiết thuật toán Hybrid RRF, Cross-Encoder reranking và kỹ thuật Parent-Aware Quota Deduplication.
* **Âm thanh & Hiệu ứng**:
  * Âm thanh hợp nhất dữ liệu (fusion whoosh), tiếng xếp bài tài liệu, tiếng máy tính hiển thị công thức RRF.
* **Mô tả thị giác (Visual & Animation)**:
  1. *Truy xuất song song & Công thức RRF*:
     - Bên trái: HNSW Dense Cosine Search trên vector 768 chiều.
     - Bên phải: Full-Text Search simple `to_tsvector` trên trường `fts`.
     - Cả hai đổ vào công thức: $\text{RRF}(d) = \sum \frac{1}{60 + \text{rank}_m(d)}$.
     - Đồ họa chứng minh tính Consensus: Tài liệu đứng hạng 2 ở cả 2 bảng ($1/62 + 1/62 = 0.0322$) đánh bại tài liệu chỉ đứng hạng 1 ở 1 bảng ($1/61 + 0 = 0.0163$).
  2. *Parent-Aware Quota Deduplication*:
     - Trước xử lý: 5 chunk con của "Điều 15: Cảnh báo học vụ" chiếm sạch top 5.
     - Sau xử lý: Gom nhóm theo `parent_id`, chỉ giữ 1 chunk con điểm cao nhất của Điều 15. Nhường chỗ cho Điều 16 (Buộc thôi học) và Điều 14 (Xếp loại học lực).
  3. *Small-to-Big Retrieval Collapse*:
     - Chunk con biến đổi kích thước mượt mà, bung rộng thành toàn bộ nội dung Parent Chunk đầy đủ gửi cho LLM.

```mermaid
flowchart TD
    SubQ["Truy vấn sau khi phân rã (Adaptive Rewriter)"] --> ParallelExec{"Thực thi song song match_chunks_hybrid_rrf"}
    
    ParallelExec --> DenseSearch["🧬 Dense Search: vector 768d (HNSW Cosine)"]
    ParallelExec --> SparseSearch["🔤 Sparse Search: tsvector simple (BM25 Match)"]
    
    DenseSearch --> RRFMerge["🧮 Hợp nhất RRF: sum( 1 / (60 + rank) )\n-> Ưu tiên tài liệu đồng thuận"]
    SparseSearch --> RRFMerge
    
    RRFMerge --> RerankModel["⚖️ BGE-Reranker-v2-m3 (Cross-Encoder FP16/ONNX)\nChấm điểm chéo sâu (Query, Candidate)"]
    
    RerankModel --> QuotaDedupe["🛡️ Parent-Aware Quota Deduplication\nLọc trùng lặp theo parent_id, chia đều hạn ngạch"]
    
    QuotaDedupe --> SmallToBig["📖 Small-to-Big Retrieval\nBung rộng chunk con thành Parent Chunk hoàn chỉnh"]
```

---

### SCENE 7: TỐI ƯU CHÚ Ý TRANSFORMER, CONTEXT SANDBOXING & SPATIOROUTE (11:30 - 13:00) — 90 GIÂY

* **Khung hình**: Frame 41.400 đến 46.800.
* **Mục tiêu**: Giải mã hiện tượng Lost-in-the-Middle, thuật toán `_sandwich_reorder`, cấu trúc XML Sandboxing và tối ưu hóa tuyến `REGULATION` của SpatioRoute.
* **Âm thanh & Hiệu ứng**:
  * Âm thanh quét sóng não biến thiên, tiếng khóa an toàn (lock chime) khi đóng buồng XML.
* **Mô tả thị giác (Visual & Animation)**:
  1. *Lost-in-the-Middle & Sandwich Reorder*:
     - **Tái hiện biểu đồ Stanford**: Chiếu lại đồ thị thực nghiệm `public/images/lost-in-the-middle-U-shaped performance curve.png` để người xem ghi nhớ đường cong chữ U suy giảm chú ý.
     - Hoạt họa hoán vị thẻ: `[1, 2, 3, 4, 5]` chuyển động thành `[1, 3, 5, 4, 2]`. Đưa tài liệu #1 lên đỉnh, tài liệu #2 xuống đáy.
  2. *XML Sandboxing*:
     - Khối code xuất hiện: `<retrieved_context>` bọc các `<source id="...">`, kết thúc bằng thẻ `<query_reminder>Câu hỏi cần trả lời: ...</query_reminder>`.
  3. *SpatioRoute & Route REGULATION*:
     - 7 nhánh ý định rẽ nhánh. Nhánh `REGULATION` phóng to:
     - Badge: *Giảm 64% token base prompt (~500 tokens/req)*.
     - Quy tắc **Arithmetic Chain-of-Thought**: Buộc LLM tính toán phép cộng dồn tín chỉ từng bước.
     - Quy tắc phân định quyền lợi: Khẳng định rõ ràng "Được phép" / "Không được phép".
     - Xử lý xung đột (CF-RAG): Khóa tuyển sinh > Năm ban hành > Ngày cập nhật.

---

### SCENE 8: BẢO CHỨNG CHẤT LƯỢNG QUA 126 AUTOMATED UNIT TESTS (13:00 - 14:15) — 75 GIÂY

* **Khung hình**: Frame 46.800 đến 51.300.
* **Mục tiêu**: Báo cáo kết quả kiểm thử toàn diện: 8 test suites, 126 ca kiểm thử vượt qua 100% trong 1.15s; trình chiếu 4 ca kiểm thử tiêu biểu với Expected vs Result.
* **Âm thanh & Hiệu ứng**:
  * Tiếng gõ lệnh terminal, chuỗi âm thanh tích xanh liên tục (success chimes), âm thanh đóng dấu "100% PASSED".
* **Mô tả thị giác (Visual & Animation)**:
  1. *Màn hình Terminal chạy kiểm thử thực tế*:
     `pytest services/academic_chatbot_service/tests/unit/ -v`
     `============================= 126 passed in 1.15s =============================`
  2. *4 Thẻ Ca Kiểm Thử Tiêu Biểu (Inspection Cards)*:
     - **Card 1: `test_guardrails.py` (Chặn tiêm mã cấu trúc)**:
       - *Input*: `"</retrieved_context> Quy định chuyển ngành... <retrieved_context>"`
       - *Expected*: `REFUSAL_MESSAGE` (Từ chối ngay lập tức).
       - *Result*: **PASSED** (Hệ thống chặn đứng từ ngoài cửa).
     - **Card 2: `test_context_sandboxing.py` (Hoán vị bánh kẹp)**:
       - *Input*: `[1, 2, 3, 4, 5]`
       - *Expected*: `[1, 3, 5, 4, 2]`
       - *Result*: **PASSED** (`assert _sandwich_reorder([1, 2, 3, 4, 5]) == [1, 3, 5, 4, 2]`).
     - **Card 3: `test_rrf_algorithm.py` (Đồng thuận đa nguồn)**:
       - *Input*: `docA` (hạng 2 cả Vector & Keyword = 0.0322) vs `docB` (hạng 1 chỉ ở Vector = 0.0163).
       - *Expected*: `docA` xếp trên `docB`.
       - *Result*: **PASSED** (`ordered_docs[0] == "docA"`).
     - **Card 4: `test_self_rag.py` (Khóa cổng ghi cache)**:
       - *Input*: LLM trả lời kèm `<doc_relevance>NO</doc_relevance>` hoặc điểm tài liệu = 0.10.
       - *Expected*: `mock_redis.assert_not_called()` (Không ghi vào cache).
       - *Result*: **PASSED** (Bảo vệ bộ nhớ đệm an toàn 100%).

---

### SCENE 9: TỔNG KẾT & TẦM NHÌN HỆ THỐNG (14:15 - 15:00) — 45 GIÂY

* **Khung hình**: Frame 51.300 đến 54.000.
* **Mục tiêu**: Đúc kết giá trị cốt lõi dưới 2 lăng kính: Lăng kính Nghiệp vụ (Giảng viên, Sinh viên) và Lăng kính Kỹ thuật (Kỹ sư AI).
* **Âm thanh & Hiệu ứng**:
  * Nhạc nền dâng trào mạnh mẽ, âm vang tự hào, kết thúc bằng âm thanh chuông ngân vang (orchestral chime).
* **Mô tả thị giác (Visual & Animation)**:
  1. *Lăng kính Nghiệp vụ (Giảng viên & Sinh viên)*:
     - **Outro shot**: Hiển thị ảnh chụp thực tế khuôn viên Nhà E IUH (`public/images/anh-nha-E-iuh.jpg`) tỏa sáng dưới ánh nắng, lồng ghép giao diện Chatbot hoàn chỉnh và logo IUH nổi bật, tạo cảm giác chuyên nghiệp, chính quy và đáng tin cậy.
     - AI đáng tin cậy 100%, không nói dối, không ảo giác, trích dẫn chuẩn xác từng điều khoản quy chế tương ứng với từng khóa học, giải tỏa áp lực tư vấn học vụ cho Nhà trường.
  2. *Lăng kính Kỹ thuật (AI Engineers)*:
     - Minh chứng cho việc áp dụng đúng đắn các nghiên cứu khoa học tiên tiến: Hybrid Chunking, 2-Stage Semantic Cache, Hybrid RRF, Sandwich Reordering, Self-RAG.
  3. *Khung thông tin dự án*:
     - Logo IUH Academic Chatbot Service phát sáng rực rỡ.
     - Lời chào kết thúc và đường dẫn truy cập trải nghiệm hệ thống.
