# 🎙️ LỜI THOẠI THUYẾT MINH VIDEO CHUYÊN SÂU (VOICEOVER SCRIPT)
# CHUYÊN ĐỀ: KIẾN TRÚC DỊCH VỤ ACADEMIC CHATBOT SERVICE & 2-STAGE HYBRID RAG
> **Thời lượng mục tiêu**: **~14 phút** (khoảng 2.100 - 2.250 từ tiếng Việt)  
> **Tốc độ đọc**: ~150 từ/phút (trầm tĩnh, tự tin, chuẩn xác từng thuật ngữ kỹ thuật)  
> **Đối tượng người nghe**: Kỹ sư AI chuyên sâu và Giảng viên / Sinh viên Non-IT  

---

## PHẦN 1: MỞ ĐẦU & TỬ HUYỆT CỦA NAIVE RAG TRONG TƯ VẤN HỌC VỤ (~1 phút 20 giây - 200 từ)

Chào các bạn! Trong giáo dục đại học, quy chế đào tạo và văn bản học vụ là cơ sở pháp lý quyết định đến quyền lợi và lộ trình của hàng chục nghìn sinh viên. Tại Trường Đại học Công nghiệp TP.HCM (IUH), hệ thống quy chế bao gồm hàng trăm trang tài liệu phức tạp và liên tục thay đổi theo từng khóa tuyển sinh.

Khi áp dụng AI vào tư vấn, giải pháp thông thường là Naive RAG — lấy văn bản cắt thành đoạn nhỏ cố định, nhúng vector rồi ném vào mô hình ngôn ngữ. Nhưng trong thực tế học vụ, Naive RAG đã thất bại thảm hại!

Có bốn tử huyệt chết người: 
Thứ nhất, cắt vụn văn bản làm mất ngữ cảnh: mệnh đề 'Sinh viên bị cảnh báo học vụ' nằm ở mảnh A, nhưng điều kiện then chốt 'điểm tích lũy dưới 1.20' lại văng sang mảnh B, khiến AI bịa đặt điều kiện.
Thứ hai, vector đơn thuần không thể bắt chính xác mã môn học như 4203001 hay từ viết tắt GPA, trong khi tìm kiếm từ khóa lại mù trước cách diễn đạt tự nhiên của sinh viên.
Thứ ba, Naive RAG không có bộ thẩm định tài liệu, ép mô hình đọc văn bản rác và khuếch đại ảo giác.
Và thứ tư, sinh viên thường hỏi câu phức hợp hai ý, nhưng Naive RAG chỉ tìm kiếm một lần, dẫn đến trả lời thiếu sót.

Để giải quyết triệt để, chúng tôi đã phát triển dịch vụ Academic Chatbot Service — một kiến trúc RAG chuyên sâu được bảo chứng bởi các nghiên cứu khoa học tiên tiến trên thế giới.

---

## PHẦN 2: CƠ SỞ KHOA HỌC & LỰA CHỌN: ADVANCED RAG HAY MODULAR RAG? (~1 phút 30 giây - 230 từ)

Để giải quyết bài toán, chúng tôi dựa trên công trình tổng quan năm 2023 của Gao và các cộng sự từ Đại học Đồng Tế và Đại học Phúc Đán mang tên *Retrieval-Augmented Generation for Large Language Models: A Survey*. Nhóm tác giả đã phân chia sự tiến hóa của RAG thành ba thế hệ: Naive RAG, Advanced RAG và Modular RAG.

Nhiều người sẽ hỏi: Tại sao dự án không áp dụng toàn bộ kiến trúc Modular RAG thuần túy, mà lại chọn nền tảng là Advanced RAG kết hợp có chọn lọc với một số module?

Từ góc nhìn của kỹ sư AI, đây là bài toán đánh đổi giữa tính linh hoạt lý thuyết và hiệu năng thực tế. Modular RAG thuần túy biến mọi khâu thành các Agent phi tập trung giao tiếp qua mạng đồ thị phức tạp. Nó cho điểm cao trong phòng thí nghiệm, nhưng khi đưa vào thực tế phục vụ 5.000 sinh viên cùng tra cứu mùa đăng ký học phần, Modular RAG gây ra độ trễ khủng khiếp từ 5 đến 10 giây mỗi lượt chat, chi phí token tăng vọt và nguy cơ trôi dạt trạng thái ngoài tầm kiểm soát.

Do đó, chúng tôi chọn **Advanced RAG làm bộ khung xương sống vững chắc**, tối ưu sâu ở hai giai đoạn Pre-retrieval và Post-retrieval với độ trễ dưới 1.5 giây, đồng thời tích hợp có chọn lọc **5 module thực dụng nhất từ Modular RAG**:
1. *Module Semantic Cache*: Xóa bỏ độ trễ và chi phí cho các câu hỏi lặp lại.
2. *Module Fusion Search*: Kết hợp sức mạnh đa nguồn giữa Vector và Từ khóa qua thuật toán RRF.
3. *Module Dynamic Routing*: Phân loại câu hỏi theo ý định chuyên biệt SpatioRoute.
4. *Module Semantic Memory*: Lưu vết ngữ cảnh hội thoại cá nhân hóa.
5. *Module Quality Gate*: Chốt chặn tự phản tư Self-RAG kiểm duyệt câu trả lời.

---

## PHẦN 3: BẢN ĐỒ NGHIÊN CỨU: ÁP DỤNG ĐIỂM NÀO, LOẠI BỎ ĐIỂM NÀO? (~2 phút 10 giây - 320 từ)

Mọi kỹ thuật trong dự án đều xuất phát từ các nghiên cứu khoa học đã được kiểm chứng:

**Thứ nhất là nghiên cứu *Rewrite-Retrieve-Read* của Ma và cộng sự từ Microsoft Research và Đại học Giao thông Thượng Hải.**
Nghiên cứu chứng minh việc viết lại câu hỏi trước khi tìm kiếm sẽ gia tăng vượt bậc độ chính xác của tài liệu thu hồi. Chúng tôi áp dụng mô hình cục bộ Qwen-2.5 để phân rã câu hỏi kép thành tối đa 3 truy vấn con độc lập và chuẩn hóa từ lóng sinh viên. Điểm loại bỏ: Chúng tôi bỏ thuật toán học tăng cường PPO vì dễ overfit dữ liệu đóng, thay bằng Dynamic Few-shot Prompting có Guardrail an toàn.

**Thứ hai là nghiên cứu *Lost in the Middle* của Nelson Liu và cộng sự tại Đại học Stanford và UC Berkeley.**
Thực nghiệm chứng minh khả năng chú ý của kiến trúc Transformer tuân theo đường cong hình chữ U: nhận thức rất mạnh ở đầu và cuối ngữ cảnh, nhưng tụt dốc nghiêm trọng ở khu vực chính giữa. Chúng tôi áp dụng thuật toán `_sandwich_reorder`: hoán vị tài liệu rank 1 lên đầu, rank 2 xuống cuối, các tài liệu còn lại xen kẽ ở giữa, đồng thời đính kèm thẻ nhắc nhở câu hỏi `<query_reminder>` ở sát đáy ngữ cảnh. Điểm loại bỏ: Bỏ kỹ thuật brute-force hoán vị nhiều lần vì gây tốn kém chi phí gọi mô hình.

**Thứ ba là nghiên cứu *Corrective RAG (CRAG)* của Đại học Khoa học Kỹ thuật Trung Quốc và Google DeepMind.**
CRAG đề xuất bộ đánh giá chất lượng tài liệu trước khi sinh câu trả lời. Chúng tôi áp dụng bộ lọc ngưỡng điểm rerank 0.25 để kiên quyết loại bỏ tài liệu rác. Điểm loại bỏ: Trong CRAG, khi thiếu tài liệu, hệ thống tự động tìm kiếm trên mạng Internet. Chúng tôi **loại bỏ hoàn toàn Web Search** vì Internet chứa nhiều tin rác và quy chế trường khác; hệ thống chỉ sử dụng CSDL nội bộ chính thống IUH.

**Thứ tư là nghiên cứu *Self-RAG* của Asai và cộng sự tại Đại học Washington.**
Chúng tôi đưa các thẻ phản tư `<thinking>`, `<doc_relevance>`, `<conflict_detected>` và `<answer_confidence>` vào quy trình suy luận của LLM, dùng làm điều kiện khóa cổng ghi cache.

Và cuối cùng, chúng tôi đã thử nghiệm nghiên cứu **HyDE** của Gao và Callan từ CMU — sinh câu trả lời giả định rồi mới tìm kiếm. Tuy nhiên, chúng tôi **loại bỏ hoàn toàn HyDE** vì quy chế chứa các con số chế tài cố định, câu trả lời giả định thường bịa sai số điểm, khiến vector tìm sai điều luật.

---

## PHẦN 4: KỸ NGHỆ DỮ LIỆU ĐẦU VÀO: HYBRID PARENT-CHILD & TABLE-AWARE (~1 phút 50 giây - 280 từ)

Một hệ thống AI chuyên nghiệp bắt đầu từ sự chỉn chu của tầng dữ liệu. Trong module `hybrid_chunker.py`, chúng tôi xây dựng quy trình phân đoạn đa cấp độ:

**Bước 1: Trích xuất siêu dữ liệu Frontmatter**: Bóc tách chính xác URL nguồn, tiêu đề quy chế, ngày ban hành và sơ đồ phân cấp breadcrumbs từ các tài liệu Cẩm nang người học và Sổ tay sinh viên.

**Bước 2: Phân tách khối cha Parent Chunks**: Phân tích cây tiêu đề Markdown từ H1 đến H6. Mỗi điều khoản được giữ trọn vẹn thành một Parent Chunk tối đa 1.200 token. Nếu một điều khoản quá dài vượt 1.200 token, thuật toán tự động kích hoạt Secondary Regex để bóc tách theo mục La Mã như 'I. Nguyên tắc chung' hoặc rơi vào cơ chế ngắt đoạn văn bảo toàn câu, đảm bảo không có câu văn nào bị cắt đứt đoạn.

**Bước 3: Phân mảnh khối con Child Chunks**: Mỗi khối cha sinh ra các khối con tối đa 600 ký tự với 100 ký tự gối đầu overlap, phục vụ tạo vector ngữ nghĩa sắc bén.

**Bước 4: Cơ chế Table-Aware Splitter**: Khi gặp bảng biểu học phí hay biểu điểm, thuật toán tự động nhận diện hàng tiêu đề Markdown. Khi cắt bảng dài thành nhiều mảnh nhỏ, dòng tiêu đề cột được nhân bản vào đầu mỗi mảnh con! Nhờ đó, dòng dữ liệu ở đáy bảng vẫn giữ nguyên bối cảnh tên cột, không bao giờ bị mất ý nghĩa.

**Bước 5: Augmented Context**: Đường dẫn phân cấp như 'Tuyển sinh > Xét học bạ' được nhúng trực tiếp vào văn bản chunk con trước khi đưa vào mô hình `bkai-foundation-models/vietnamese-bi-encoder` để sinh vector 768 chiều.

---

## PHẦN 5: TỐC ĐỘ VÀ AN TOÀN: BỘ ĐỆM NGỮ NGHĨA 2 GIAI ĐOẠN (~1 phút 40 giây - 260 từ)

Trong đợt cao điểm nộp học phí hay kỳ thi, hàng nghìn sinh viên gửi câu hỏi có cùng nội dung. Hệ thống triển khai Bộ đệm Ngữ nghĩa hai giai đoạn trong `rag_service.py`:

**Giai đoạn 1 — Quét diện rộng High Recall**: Kiểm tra Redis O(1) theo chuỗi ký tự chuẩn hóa. Nếu không khớp tuyệt đối, vector 768 chiều được so khớp Cosine trên PostgreSQL pgvector với ngưỡng gợi mở 0.60 để không bỏ sót ứng viên tiềm năng.

**Giai đoạn 2 — Thẩm định chuyên sâu High Precision**: Nếu chỉ dựa vào vector của Bi-Encoder, hai câu hỏi 'Hạn nộp học phí học kỳ 1' và 'Hạn nộp học phí học kỳ 2' có thể đạt độ tương đồng lên tới 0.93 vì chỉ khác một chữ số! Để ngăn chặn thảm họa này, cặp câu hỏi được đưa qua mô hình Cross-Encoder `BAAI/bge-reranker-v2-m3` với ngưỡng khắt khe 0.80. Đồng thời, thuật toán kiểm tra tính nhất quán của thực thể số: tập hợp các chữ số trong câu hỏi sinh viên phải trùng khớp hoàn toàn với câu hỏi trong cache. Nếu sinh viên hỏi về 'kỳ 2' mà cache lưu 'kỳ 1', hệ thống đánh dấu Cache MISS ngay lập tức.

**Cổng kiểm soát ghi đệm Gated Write-back**: Câu trả lời của LLM chỉ được lưu vào cache khi thỏa mãn cả ba điều kiện: điểm tài liệu trích xuất đạt từ 0.25 trở lên, độ dài từ 10 đến 3.000 ký tự, và các thẻ Self-RAG của chính LLM xác nhận độ liên quan tài liệu là YES cùng độ tự tin ở mức HIGH. Không một câu trả lời lỗi nào có cơ hội lọt vào bộ đệm!

---

## PHẦN 6: TRUY XUẤT LAI HỢP HYBRID RRF, QUOTA DEDUPLICATION & BGE-RERANKER (~1 phút 50 giây - 280 từ)

Khi không có trong cache, hệ thống kích hoạt quy trình Truy xuất Lai hợp qua bốn bước:

**Bước 1: Viết lại và phân rã truy vấn**: Mô hình cục bộ Qwen-2.5 phân tích câu hỏi kép và tách thành 1 đến 3 truy vấn con độc lập.

**Bước 2: Tìm kiếm song song và Hợp nhất thứ hạng RRF**: Mỗi truy vấn con thực thi song song trên PostgreSQL qua hàm `match_chunks_hybrid_rrf`. Hệ thống chạy đồng thời:
- Tìm kiếm vector dày đặc Dense Search trên vector 768 chiều với chỉ mục HNSW Cosine.
- Tìm kiếm từ khóa Sparse Search trên trường fts bằng từ điển simple, bắt trọn từng mã học phần và thuật ngữ học vụ.
Hai bảng xếp hạng được hợp nhất bằng công thức **Reciprocal Rank Fusion (RRF)** với hằng số k bằng 60. Điểm RRF cực kỳ ưu ái sự đồng thuận: tài liệu đứng thứ hai ở cả hai bảng sẽ đạt điểm cao hơn tài liệu chỉ đứng nhất ở bảng vector nhưng biến mất ở bảng từ khóa.

**Bước 3: Chấm điểm chéo với BGE-Reranker v2-m3**: Mô hình Cross-Encoder đọc đồng thời từng truy vấn con với nội dung tài liệu để chấm điểm mức độ liên quan thực sự.

**Bước 4: Gom nhóm hạn ngạch Parent-Aware Quota Selection & Small-to-Big Retrieval**: Để tránh tình trạng các câu vụn vặt của một điều khoản dài chiếm hết danh sách kết quả, thuật toán gom nhóm theo `parent_id` và chỉ giữ lại một chunk con điểm cao nhất cho mỗi Điều khoản. Sau đó, cơ chế Small-to-Big tự động hoán đổi từ chunk con sang toàn bộ nội dung khối cha hoàn chỉnh để nạp vào LLM. Sinh viên tìm kiếm bằng mảnh ghép nhỏ nhạy bén, nhưng LLM đọc và suy luận trên toàn bộ văn bản điều khoản pháp lý đầy đủ!

---

## PHẦN 7: TỐI ƯU CHÚ Ý TRANSFORMER, CONTEXT SANDBOXING & SPATIOROUTE (~1 phút 40 giây - 250 từ)

Sau khi có tài liệu chuẩn xác, hệ thống đưa vào Prompt thông qua ba tầng công nghệ:

**Tầng 1: Thuật toán hoán vị Sandwich Reordering**: Giải quyết hiện tượng Lost-in-the-Middle bằng cách đưa tài liệu quan trọng nhất lên vị trí đầu tiên, tài liệu quan trọng thứ hai xuống vị trí cuối cùng, các tài liệu còn lại nằm ở giữa theo công thức `[#1, #3, #5, ..., #4, #2]`. Dù mô hình có giảm chú ý ở đoạn giữa, hai điều khoản quan trọng nhất vẫn nằm ở hai vùng nhận thức mạnh nhất của Transformer.

**Tầng 2: Cách ly an toàn bằng XML Sandboxing**: Toàn bộ tài liệu được bọc cách ly trong thẻ `<retrieved_context>`, mỗi tài liệu đánh số trong `<source id="...">`, kết thúc bằng thẻ `<query_reminder>`. Cấu trúc này vô hiệu hóa hoàn toàn mã độc prompt injection ẩn giấu trong dữ liệu.

**Tầng 3: Điều hướng chuyên biệt SpatioRoute**: Hệ thống phân loại câu hỏi vào một trong 7 nhóm ý định. Tuyến `REGULATION` về quy chế đào tạo được tối ưu cắt giảm 64% token rườm rà, tiết kiệm hơn 500 token mỗi lượt gọi. Tuyến này áp dụng **Arithmetic Chain-of-Thought**: buộc mô hình tính toán số học từng bước khi cộng dồn tín chỉ hoặc tính điểm trung bình trước khi kết luận, tuân thủ nghiêm ngặt nguyên tắc khẳng định rõ ràng 'Được phép' hay 'Không được phép' dựa trên thứ tự ưu tiên CF-RAG: Khóa tuyển sinh của sinh viên luôn được ưu tiên cao hơn năm ban hành văn bản.

---

## PHẦN 8: BẢO CHỨNG CHẤT LƯỢNG QUA 126 AUTOMATED UNIT TESTS (~1 phút 30 giây - 240 từ)

Chất lượng và độ ổn định của toàn bộ kiến trúc được bảo chứng qua **126 ca kiểm thử đơn vị tự động (Unit Tests)** trên 8 bộ suite chuyên biệt trong thư mục `tests/unit/`, vượt qua 100% chỉ trong 1.15 giây:

**Ca 1 — Chặn tiêm mã cấu trúc (`test_guardrails.py`)**: Người dùng gửi câu hỏi chứa thẻ đóng giả mạo `</retrieved_context>` kèm quy định giả. Kết quả kỳ vọng: Trả về thông báo từ chối an toàn `REFUSAL_MESSAGE`. Kết quả thực tế: **PASS 100%**, hệ thống chặn đứng cuộc tấn công ngay tại tầng lọc ngoài cùng.

**Ca 2 — Hoán vị bánh kẹp Sandwich (`test_context_sandboxing.py`)**: Truyền vào 5 tài liệu xếp hạng từ 1 đến 5. Kết quả kỳ vọng: Hoán vị chính xác thành `[1, 3, 5, 4, 2]`. Kết quả thực tế: **PASS 100%**, đưa tài liệu 1 và 2 ra hai đầu ngữ cảnh.

**Ca 3 — Đồng thuận đa nguồn RRF (`test_rrf_algorithm.py`)**: Tài liệu A đứng hạng 2 ở cả hai bảng đạt 0.0322 điểm, tài liệu B đứng hạng 1 chỉ ở bảng Vector đạt 0.0163 điểm. Kết quả kỳ vọng: Tài liệu A xếp trên tài liệu B. Kết quả thực tế: **PASS 100%**, chứng minh thuật toán luôn ưu tiên sự đồng thuận đa chiều.

**Ca 4 — Khóa cổng ghi cache Self-RAG (`test_self_rag.py`)**: Khi LLM sinh câu trả lời với thẻ `<doc_relevance>NO</doc_relevance>` hoặc điểm tài liệu chỉ đạt 0.10. Kết quả kỳ vọng: Tiến trình ghi cache Redis bị hủy bỏ. Kết quả thực tế: **PASS 100%**, bảo vệ bộ đệm an toàn tuyệt đối.

---

## PHẦN 9: TỔNG KẾT & TẦM NHÌN HỆ THỐNG (~1 phút 00 giây - 160 từ)

Nhìn lại toàn bộ hành trình, dịch vụ Academic Chatbot của IUH là sự kết hợp hoàn hảo giữa kỹ nghệ phần mềm và trí tuệ nhân tạo hiện đại:

Đối với thầy cô và sinh viên, đây là người trợ lý học vụ đáng tin cậy: không ảo giác, không nói dối, trích dẫn chuẩn xác từng điều khoản quy chế tương ứng với đúng khóa học của mình và phản hồi gần như ngay lập tức.

Đối với cộng đồng kỹ sư AI, dự án là minh chứng cho thấy việc áp dụng đúng đắn các nghiên cứu khoa học tiên tiến — từ Hybrid Chunking, 2-Stage Semantic Cache, Hybrid RRF, Sandwich Reordering đến Self-RAG — hoàn toàn có thể giải quyết triệt để những điểm yếu cố hữu của mô hình ngôn ngữ lớn trong các bài toán pháp lý chuyên biệt.

Toàn bộ hệ thống hiện đã sẵn sàng phục vụ thực tế cho sinh viên Trường Đại học Công nghiệp TP.HCM. Cảm ơn quý thầy cô và các bạn đã theo dõi!
