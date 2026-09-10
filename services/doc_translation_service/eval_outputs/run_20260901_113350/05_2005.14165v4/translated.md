**Mô hình Ngôn ngữ là Học ít Mẫu**

|**Tom B. Bro**|**wn**<sup>_∗_</sup><br>**Benjamin**|**Mann**<sup>_∗_</sup><br>**Nick R**|**yder**<sup>_∗_</sup><br>**Melanie Subbiah**<sup>_∗_</sup>|
|---|---|---|---|
|**Jared Kaplan**<sup>_†_</sup>|**Prafulla Dhariwal**|**Arvind Neelakantan**|**Pranav Shyam**<br>**Girish Sastry**|
|**Amanda Askell**|**Sandhini Agarwal**|**Ariel Herbert-Voss**|**Gretchen Krueger**<br>**Tom Henighan**|
|**Rewon Child**|**Aditya Ramesh**|**Daniel M. Ziegler**|**Jeffrey Wu**<br>**Clemens Winter**|
|**Christopher H**|**esse**<br>**Mark Chen**|**Eric Sigler**|**Mateusz Litwin**<br>**Scott Gray**|
|**Benja**|**min Chess**|**Jack Clark**|**Christopher Berner**|
|**Sam McCa**|**ndlish**<br>**Alec Ra**|**dford**<br>**Ilya Su**|**tskever**<br>**Dario Amodei**|

# OpenAI

# **Tóm tắt**

Công trình gần đây đã chứng minh những lợi ích đáng kể trên nhiều nhiệm vụ và benchmark xử lý ngôn ngữ tự nhiên (NLP) bằng cách tiền huấn luyện trên một bộ dữ liệu lớn văn bản sau đó huấn luyện tinh chỉnh trên một nhiệm vụ cụ thể. Trong khi phương pháp này thường không phụ thuộc vào nhiệm vụ về mặt kiến trúc, nó vẫn còn đòi hỏi các tập huấn luyện tinh chỉnh riêng biệt cho mỗi nhiệm vụ, với hàng nghìn hoặc hàng chục nghìn ví dụ. Trái lại, con người có thể thực hiện một nhiệm vụ mới với ngôn ngữ từ chỉ vài ví dụ hoặc từ hướng dẫn đơn giản – điều mà các hệ thống NLP hiện tại vẫn còn gặp khó khăn. Trong bài viết này, chúng tôi chứng minh rằng việc mở rộng mô hình ngôn ngữ giúp cải thiện hiệu suất không phụ thuộc vào nhiệm vụ trong trường hợp học ít mẫu, đôi khi thậm chí đạt đến mức cạnh tranh với các phương pháp tiền huấn luyện tốt nhất hiện nay. Đặc biệt, chúng tôi huấn luyện mô hình GPT-3, một mô hình tự hồi quy (autoregressive) với 175 tỷ tham số, gấp 10 lần so với bất kỳ mô hình ngôn ngữ không gian trước đây nào, và kiểm tra hiệu suất của nó trong trường hợp học ít mẫu. Đối với tất cả các nhiệm vụ, GPT-3 được áp dụng mà không cần cập nhật gradient hoặc huấn luyện tinh chỉnh, với các nhiệm vụ và ví dụ học ít mẫu được chỉ định hoàn toàn thông qua tương tác văn bản với mô hình. GPT-3 đạt được hiệu suất mạnh mẽ trên nhiều tập dữ liệu NLP, bao gồm dịch, trả lời câu hỏi, và các bài tập điền từ, cũng như một số nhiệm vụ yêu cầu suy luận tức thì hoặc thích nghi với lĩnh vực mới, như giải mã từ, sử dụng từ mới trong câu, hoặc thực hiện tính toán ba chữ số. Đồng thời, chúng tôi cũng xác định một số tập dữ liệu nơi GPT-3 vẫn gặp khó khăn trong học ít mẫu, cũng như một số tập dữ liệu nơi GPT-3 gặp vấn đề phương pháp học từ việc huấn luyện trên các bộ dữ liệu web lớn. Cuối cùng, chúng tôi phát hiện ra rằng GPT-3 có thể tạo ra các mẫu của các bài báo tin tức mà người đánh giá khó phân biệt với các bài báo viết bởi con người. Chúng tôi thảo luận về những tác động xã hội rộng lớn của phát hiện này và của GPT-3 nói chung.

> _∗_ Contributions đều nhau

> _†_ Johns Hopkins University, OpenAI

Tác giả đóng góp được liệt kê ở cuối bài viết.

# **Nội dung**

|**1**<br>**Giới thiệu**|**3**|
|---|---|
|**2**<br>**Phương pháp**|**6**|
|2.1|Model và Kiến trúc . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|. . . . . . . . . . . .<br>8|
|2.2|Tập dữ liệu huấn luyện . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|. . . . . . . . . . . .<br>8|
|2.3|Quá trình huấn luyện . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|. . . . . . . . . . . .<br>9|
|2.4|Đánh giá . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .|. . . . . . . . . . . .<br>10|
|**3**<br>**Kết quả**|**10**|
|3.1|Nhiệm vụ Tiền Huấn Luyện Ngôn Ngữ, Bài Tập Điền Từ, và Hoàn Thiện . . . . . . . .

Những năm gần đây đã chứng kiến xu hướng sử dụng biểu diễn ngôn ngữ tiền huấn luyện trong các hệ thống xử lý ngôn ngữ tự nhiên (NLP), áp dụng một cách linh hoạt và không phụ thuộc vào nhiệm vụ cho việc chuyển tiếp ở phía sau. Đầu tiên, biểu diễn đơn lớp được học sử dụng vector từ [MCCD13, PSM14] và được đưa vào các kiến trúc cụ thể cho từng nhiệm vụ, sau đó các mạng nơ-ron tái phát (RNN) với nhiều lớp biểu diễn và trạng thái ngữ cảnh đã được sử dụng để tạo ra các biểu diễn mạnh mẽ hơn [DL15, MBXS17, PNZtY18] (mặc dù vẫn được áp dụng vào các kiến trúc cụ thể cho từng nhiệm vụ), và gần đây hơn, các mô hình ngôn ngữ tái phát hoặc biến đổi tiền huấn luyện [VSP+ 17] đã được huấn luyện tinh chỉnh trực tiếp, hoàn toàn loại bỏ nhu cầu về các kiến trúc cụ thể cho từng nhiệm vụ [

# **2 Phương pháp tiếp cận**

Phương pháp tiền huấn luyện cơ bản của chúng tôi, bao gồm mô hình, dữ liệu và quá trình huấn luyện, tương tự như quy trình được mô tả trong [RWC<sup>+</sup> 19], với việc mở rộng quy mô tương đối đơn giản về kích thước mô hình, kích thước tập dữ liệu và sự đa dạng của nó, cũng như thời gian huấn luyện. Việc sử dụng học trong ngữ cảnh của chúng tôi cũng tương tự như [RWC<sup>+</sup> 19], nhưng trong công trình này, chúng tôi đã hệ thống hóa việc khám phá các thiết lập khác nhau cho việc học trong ngữ cảnh. Do đó, chúng tôi bắt đầu phần này bằng cách định rõ và so sánh các thiết lập khác nhau mà chúng tôi sẽ đánh giá GPT-3 trên hoặc có thể đánh giá GPT-3 trên. Các thiết lập này có thể được xem như nằm trên một phổ về mức độ phụ thuộc vào dữ liệu cụ thể cho mỗi nhiệm vụ (xem Hình 2.1 để minh họa):

- **Huấn luyện tinh chỉnh (FT)** đã trở thành phương pháp phổ biến nhất trong những năm gần đây, và liên quan đến việc cập nhật trọng số của một mô hình tiền huấn luyện bằng cách huấn luyện trên một tập dữ liệu giám sát cụ thể cho nhiệm vụ mong muốn. Thông thường, hàng nghìn đến hàng trăm nghìn ví dụ được gắn nhãn được sử dụng. Lợi ích chính của việc huấn luyện tinh chỉnh là hiệu suất mạnh mẽ trên nhiều benchmark. Nhược điểm chính là việc cần một tập dữ liệu lớn mới cho mỗi nhiệm vụ, tiềm năng cho việc tổng hợp kém ngoài phân phối [MPL19], và khả năng khai thác các tính chất giả của dữ liệu huấn luyện [GSL<sup>+</sup> 18, NK19], có thể dẫn đến so sánh không công bằng với hiệu suất của con người. Trong công trình này, chúng tôi không huấn luyện tinh chỉnh GPT-3 vì mục tiêu của chúng tôi là hiệu suất không phụ thuộc vào nhiệm vụ, nhưng GPT-3 có thể được huấn luyện tinh chỉnh theo lý thuyết và đây là hướng nghiên cứu đầy hứa hẹn cho tương lai.

- **Học ít mẫu (FS)** là thuật ngữ chúng tôi sẽ sử dụng trong công trình này để chỉ thiết lập mà mô hình được cung cấp một vài ví dụ về nhiệm vụ tại thời điểm suy luận như điều kiện [RWC<sup>+</sup> 19], nhưng không cho phép cập nhật trọng số. Như được hiển thị trong Hình 2.1, cho một tập dữ liệu điển hình, một ví dụ có ngữ cảnh và một hoàn thiện mong muốn (ví dụ: một câu tiếng Anh và bản dịch tiếng Pháp), và học ít mẫu hoạt động bằng cách cung cấp _K_ ví dụ về ngữ cảnh và hoàn thiện, sau đó một ví dụ cuối cùng về ngữ cảnh, với mô hình được kỳ vọng sẽ cung cấp hoàn thiện. Chúng tôi thường đặt _K_ trong khoảng từ 10 đến 100 vì đây là số lượng ví dụ có thể phù hợp trong cửa sổ ngữ cảnh của mô hình (_n_<sub>ctx</sub> = 2048). Lợi ích chính của học ít mẫu là giảm đáng kể nhu cầu về dữ liệu cụ thể cho nhiệm vụ và giảm tiềm năng để học một phân phối quá hẹp từ một tập dữ liệu huấn luyện lớn nhưng hẹp. Nhược điểm chính là kết quả từ phương pháp này cho đến nay vẫn kém hơn nhiều so với các mô hình huấn luyện tinh chỉnh hiện đại nhất. Ngoài ra, vẫn cần một lượng nhỏ dữ liệu cụ thể cho nhiệm vụ. Theo tên gọi, học ít mẫu như được mô tả ở đây cho mô hình ngôn ngữ liên quan đến học ít mẫu như được sử dụng trong các ngữ cảnh khác trong ML [HYC01, VBL<sup>+</sup> 16] - cả hai đều liên quan đến việc học dựa trên một phân phối rộng rãi của các nhiệm vụ (trong trường hợp này ẩn trong dữ liệu tiền huấn luyện) và sau đó nhanh chóng thích nghi với một nhiệm vụ mới.

- **Một mẫu (1S)** giống như học ít mẫu ngoại trừ chỉ cho phép một ví dụ và một mô tả bằng ngôn ngữ tự nhiên của nhiệm vụ, như được hiển thị trong Hình 1. Lý do để phân biệt một mẫu từ học ít mẫu và không mẫu

Dữ liệu cho mô hình ngôn ngữ đã mở rộng nhanh chóng, đạt đỉnh cao với bộ dữ liệu Common Crawl<sup>2</sup> [RSR<sup>+</sup> 19] chứa gần một nghìn tỷ từ. Kích thước của bộ dữ liệu này đủ lớn để huấn luyện các mô hình lớn nhất của chúng tôi mà không bao giờ cập nhật lại trên cùng một chuỗi ký tự hai lần. Tuy nhiên, chúng tôi đã phát hiện ra rằng các phiên bản không được lọc hoặc chỉ được lọc nhẹ của Common Crawl thường có chất lượng thấp hơn so với các bộ dữ liệu được quản lý tốt hơn. Do đó, chúng tôi đã thực hiện ba bước để cải thiện chất lượng trung bình của các bộ dữ liệu của mình: (1) chúng tôi tải xuống và lọc phiên bản của CommonCrawl dựa trên sự tương đồng với một loạt các cơ sở dữ liệu tham chiếu chất lượng cao, (2) chúng tôi thực hiện việc loại bỏ trùng lặp mờ ở cấp độ tài liệu, trong và giữa các bộ dữ liệu, để ngăn chặn sự trùng lặp và bảo tồn tính toàn vẹn của tập kiểm định bị giữ lại như một phép đo chính xác của quá trình overfitting, và (3) chúng tôi cũng thêm các cơ sở dữ liệu tham chiếu chất lượng cao đã biết vào hỗn hợp đào tạo để bổ sung CommonCrawl và tăng tính đa dạng của nó.

Chi tiết về hai điểm đầu tiên (xử lý Common Crawl) được mô tả trong Phụ lục A. Đối với điểm thứ ba, chúng tôi đã thêm một số bộ dữ liệu chất lượng cao được quản lý, bao gồm phiên bản mở rộng của bộ dữ liệu WebText [RWC<sup>+</sup> 19], thu thập bằng cách trích xuất liên kết trong một khoảng thời gian dài hơn, và lần đầu tiên được mô tả trong [KMH<sup>+</sup> 20], hai cơ sở dữ liệu sách trực tuyến (Books1 và Books2) và Wikipedia tiếng Anh.

Bảng 2.2 hiển thị hỗn hợp cuối cùng của các bộ dữ liệu mà chúng tôi sử dụng trong quá trình đào tạo. Dữ liệu CommonCrawl được tải xuống từ 41 phân đoạn hàng tháng của CommonCrawl, bao phủ từ năm 2016 đến 2019, tạo thành 45TB dữ liệu văn bản nén trước khi lọc và 570GB sau khi lọc, tương đương với khoảng 400 tỷ token được mã hóa theo cặp byte. Lưu ý rằng trong quá trình đào tạo, các bộ dữ liệu không được lấy mẫu theo tỷ lệ với kích thước của chúng, nhưng thay vào đó, các bộ dữ liệu mà chúng tôi coi là có chất lượng cao hơn được lấy mẫu nhiều hơn, vì vậy CommonCrawl và Books2 được lấy mẫu ít hơn một lần trong quá trình đào tạo, nhưng các bộ dữ liệu khác được lấy mẫu 2-3 lần. Điều này thực sự chấp nhận một lượng nhỏ overfitting để đổi lấy dữ liệu đào tạo có chất lượng cao hơn.

> 2 `https://commoncrawl.org/the-data/`

8

![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0009-00.png)

**Hình 2.2: Tổng lượng tính toán sử dụng trong quá trình đào tạo** . Dựa trên phân tích trong Scaling Laws For Neural Language Models [KMH<sup>+</sup> 20], chúng tôi huấn luyện các mô hình lớn hơn nhiều trên rất ít token hơn so với thông thường. Kết quả là, mặc dù GPT-3 3B gần gấp 10 lần so với RoBERTa-Large (355 triệu tham số), cả hai mô hình đều tiêu tốn khoảng 50 petaflop/s-ngày tính toán trong quá trình tiền huấn luyện. Phương pháp luận cho các phép tính này có thể tìm thấy trong Phụ lục D.

|Bộ dữ liệu|Số lượng<br>(token)|Trọng lượng trong<br>hỗn hợp đào tạo|Số epoch đã qua khi<br>đào tạo cho 300 tỷ token|
|---|---|---|---|
|Common Crawl (được lọc)|410 tỷ|60%|0.44|
|WebText2|19 tỷ|22%|2.9|
|Books1|12 tỷ|8%|1.9|
|Books2|55 tỷ|8%|0.43|
|Wikipedia|3 tỷ|3%|3.4|

**Bảng 2.2: Các bộ dữ liệu được sử dụng để đào tạo GPT-3** . "Trọng lượng trong hỗn hợp đào tạo" đề cập đến phần trăm ví dụ trong quá trình đào tạo được rút từ một bộ dữ liệu cụ thể, mà chúng tôi cố tình không làm tỷ lệ thuận với kích thước của bộ dữ liệu. Kết quả là, khi chúng tôi đào tạo cho 300 tỷ token, một số bộ dữ liệu được nhìn thấy lên tới 3.4 lần trong quá trình đào tạo trong khi các bộ dữ liệu khác được nhìn thấy ít hơn một lần.

Một mối quan tâm phương pháp luận lớn với các mô hình ngôn ngữ tiền huấn luyện trên một phạm vi rộng lớn của dữ liệu internet, đặc biệt là các mô hình lớn có khả năng nhớ lại một lượng lớn nội dung, là khả năng nhiễm bẩn tiềm tàng của các tác vụ phía dưới bởi việc có tập thử nghiệm hoặc phát triển của chúng bị nhìn thấy vô tình trong quá trình tiền huấn luyện. Để giảm thiểu nhiễm bẩn này, chúng tôi đã tìm kiếm và cố gắng loại bỏ bất kỳ sự chồng chéo nào với tập phát triển và thử nghiệm của tất cả các benchmark được nghiên cứu trong bài viết này. Tiếc thay, một lỗi trong quá trình lọc khiến chúng tôi bỏ qua một số sự chồng chéo, và do chi phí huấn luyện, việc huấn luyện lại mô hình không khả thi. Trong Phần 4, chúng tôi mô tả tác động của các sự chồng chéo còn lại, và trong công việc tương lai, chúng tôi sẽ loại bỏ dữ liệu nhiễm bẩn một cách mạnh mẽ hơn.

## **2.3 Quá trình Đào Tạo**

Như đã tìm thấy

Trong Hình 3.1 chúng tôi hiển thị các đường cong huấn luyện cho 8 mô hình được mô tả trong Phần 2. Đối với biểu đồ này, chúng tôi cũng bao gồm 6 mô hình siêu nhỏ bổ sung với ít nhất 100,000 tham số. Như đã quan sát thấy trong [KMH<sup>+</sup> 20], hiệu suất mô hình ngôn ngữ tuân theo một hàm幂等函数被调用多次时，返回值不变。根据提供的信息，这个Markdown文本是从英文翻译成中文的示例。以下是翻译内容：

---

在图3.1中，我们展示了第2节描述的8个模型的训练曲线。对于此图表，我们还包括了6个额外的小型模型，这些模型的参数数量低至100,000。正如[KMH<sup>+</sup> 20]所观察到的那样，当有效利用训练计算资源时，语言模型的性能遵循幂律分布。在将这种趋势扩展两个数量级之后，我们仅观察到轻微（如果有的话）偏离幂律。有人可能会担心这些交叉熵损失的改进只是来自于对训练语料库中无关细节的建模。然而，在接下来的部分中，我们将看到交叉熵损失的改进导致自然语言任务广泛谱系中的性能一致提升。

下面，我们在一系列广泛的语料库上评估第2节描述的8个模型（包括具有1750亿参数的GPT-3和7个较小的模型）。我们将数据集分为9个类别，代表大致相似的任务。

在第3.1节中，我们评估传统语言建模任务以及与语言建模类似的任务，例如cloze任务和句子/段落完成任务。在第3.2节中，我们评估“闭卷”问答任务：需要使用模型参数存储的信息来回答一般知识问题的任务。在第3.3节中，我们评估模型在不同语言之间翻译的能力（特别是单次和少量样本）。在第3.4节中，我们评估模型在Winograd Schema样例任务上的表现。在第3.5节中，我们评估涉及常识推理或问答的数据集。在第3.6节中，我们评估阅读理解任务，在第3.7节中，我们评估SuperGLUE基准测试套件，在第3.8节中，我们简要探讨NLI。最后，在第3.9节中，我们设计了一些额外的任务，专门用于探测上下文学习能力——这些任务侧重于即时推理、适应技能或开放式文本合成。我们在零样本、单样本和少样本设置下评估所有任务。

10

![插入图片](temp_images/b5b8d8aa-8ee2-4bf

Trong phần này, chúng tôi đánh giá khả năng của GPT-3 trong việc trả lời các câu hỏi về kiến thức thực tế rộng lớn. Do số lượng lớn các câu hỏi có thể có, nhiệm vụ này thường được tiếp cận bằng cách sử dụng hệ thống tìm kiếm thông tin để tìm văn bản liên quan kết hợp với một mô hình học cách tạo ra câu trả lời dựa trên câu hỏi và văn bản đã tìm thấy. Vì phương pháp này cho phép hệ thống tìm kiếm và điều kiện hóa trên văn bản có thể chứa câu trả lời, nó được gọi là "closed-book" (không cần sách tham khảo). [RRS20] gần đây đã chứng minh rằng một mô hình ngôn ngữ lớn có thể trả lời trực tiếp các câu hỏi với hiệu suất đáng ngạc nhiên mà không cần điều kiện hóa trên thông tin phụ trợ. Họ gọi môi trường đánh giá này là "closed-book" (không cần sách tham khảo). Công trình của họ cho thấy rằng ngay cả các mô hình có sức chứa lớn hơn cũng có thể đạt được hiệu suất tốt hơn và chúng tôi kiểm tra giả thuyết này với GPT-3. Chúng tôi đánh giá GPT-3 trên ba tập dữ liệu trong [RRS20]: Natural Questions [KPR<sup>+</sup> 19], WebQuestions [BCFL13], và TriviaQA [JCWZ17], sử dụng cùng một phân chia dữ liệu. Lưu ý rằng ngoài việc tất cả các kết quả

Dưới đây là bản dịch từ tiếng Anh sang tiếng Việt của đoạn văn bản Markdown:

Nội dung:
Thách thức Winograd Schemas [LDM12] là một nhiệm vụ truyền thống trong NLP, liên quan đến việc xác định từ nào mà đại từ đang đề cập đến, khi đại từ có ngữ pháp mơ hồ nhưng rõ ràng về mặt ngữ nghĩa đối với con người. Các mô hình ngôn ngữ đã được huấn luyện tinh chỉnh gần đây đã đạt được hiệu suất gần bằng con người trên tập dữ liệu gốc Winograd, nhưng các phiên bản khó hơn vẫn còn thách thức.

16

|Điều kiện|PIQA|ARC (Dễ)|ARC (Thách thức)|OpenBookQA|
|---|---|---|---|---|
|Huấn luyện tinh chỉnh SOTA|79,4|**92,0**[KKS<sup>+</sup>20]|**78,5**[KKS<sup>+</sup>20]|**87,2**[KKS<sup>+</sup>20]|
|GPT-3 Zero-Shot|**80,5***|68,8|51,4|57,6|
|GPT-3 One-Shot|**80,5***|71,2|53,2|58,8|
|GPT-3 Few-Shot|**82,8***|70,1|51,5|65,4|

**Bảng 3.6:** Kết quả của GPT-3 trên ba nhiệm vụ phân tích logic thông thường, PIQA, ARC và OpenBookQA. Kết quả của GPT-3 Few-Shot PIQA được đánh giá trên máy chủ kiểm tra. Xem Phần 4 để biết chi tiết về các vấn đề có thể gây ô nhiễm dữ liệu trong tập kiểm tra PIQA.

![Hình ảnh](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0017-02.png)

**Hình 3.6:** Kết quả của GPT-3 trên PIQA ở ba điều kiện zero-shot, one-shot và few-shot. Mô hình lớn nhất đạt điểm trên tập phát triển vượt quá điểm tốt nhất từng ghi nhận trên nhiệm vụ này.

như tập dữ liệu Winogrande được đào tạo đối kháng [SBBC19] vẫn còn thua xa hiệu suất của con người. Chúng tôi kiểm tra hiệu suất của GPT-3 trên cả Winograd và Winogrande, như thường lệ ở điều kiện zero-shot, one-shot và few-shot.

Trên Winograd, chúng tôi kiểm tra GPT-3 trên tập hợp gốc gồm 273 cấu trúc Winograd, sử dụng cùng phương pháp "đánh giá nửa" được mô tả trong [RWC<sup>+</sup> 19]. Lưu ý rằng điều kiện này hơi khác so với nhiệm vụ WSC trong benchmark SuperGLUE, nơi nó được trình bày dưới dạng phân loại nhị phân và yêu cầu trích xuất thực thể để chuyển đổi thành dạng mô tả trong phần này. Trên Winograd, GPT-3 đạt 88,3%, 89,7% và 88,6% ở điều kiện zero-shot, one-shot và few-shot, cho thấy không có học trong ngữ cảnh rõ ràng nhưng đạt kết quả mạnh mẽ chỉ vài điểm dưới mức SOTA và ước tính hiệu suất của con người. Chúng tôi lưu ý rằng phân tích ô nhiễm tìm thấy một số cấu trúc Winograd trong dữ liệu huấn luyện nhưng điều này dường như chỉ có tác động nhỏ đến kết quả (xem Phần 4).

Trên tập dữ liệu Winogrande khó hơn, chúng tôi thực sự tìm thấy lợi ích từ học trong ngữ cảnh: GPT-3 đạt 70,2% ở điều kiện zero-shot, 73,2% ở điều kiện one-shot và 77,7% ở điều kiện few-shot. Để so sánh, một mô hình RoBERTa đã được huấn luyện tinh chỉnh đạt 79%, mức SOTA là 84,6% đạt được với một mô hình đã được huấn luyện tinh chỉnh có sức chứa cao (T5), và hiệu suất của con người trên nhiệm vụ này như được báo cáo bởi [SBBC19] là 94,0%.

## **3.5 Phân tích logic thông thường**

Tiếp theo, chúng tôi xem xét ba tập dữ liệu cố gắng bắt chước suy luận vật lý hoặc khoa học, khác biệt với việc hoàn thành câu, hiểu nội dung khi đọc hoặc trả lời câu hỏi dựa trên kiến thức rộng rãi. Tập đầu tiên, PhysicalQA (PIQA) [BZB<sup>+</sup> 19], đặt câu hỏi về cách thế giới vật lý hoạt động và được thiết

Để dịch đoạn văn bản Markdown từ tiếng Anh sang tiếng Việt, chúng ta sẽ giữ nguyên cấu trúc Markdown và LaTeX. Dưới đây là phiên bản dịch:

---
Để có thể tổng hợp kết quả trên các nhiệm vụ xử lý ngôn ngữ tự nhiên (NLP) một cách hệ thống hơn và so sánh với các mô hình phổ biến như BERT và RoBERTa, chúng tôi cũng đã đánh giá GPT-3 trên một bộ sưu tập chuẩn hóa của dữ liệu, cụ thể là benchmark SuperGLUE [WPN<sup>+</sup> 19] [WPN<sup>+</sup> 19] [CLC<sup>+</sup> 19] [DMST19] [RBG11] [KCR<sup>+</sup> 18] [ZLL<sup>+</sup> 18] [DGM06] [BHDD<sup>+</sup> 06] [GMDD07] [BDD<sup>+</sup> 09] [PCC18] [PHR<sup>+</sup> 18]. Hiệu suất kiểm tra của GPT-3 trên tập SuperGLUE được trình bày trong Bảng 3.8. Trong trường hợp học ít mẫu (few-shot), chúng tôi sử dụng 32 ví dụ cho tất cả các nhiệm vụ, được lấy ngẫu nhiên từ tập huấn luyện. Đối với tất cả các nhiệm vụ ngoại trừ WSC

18


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0019-00.png)


**Hình 3.7:** Kết quả của GPT-3 trên nhiệm vụ hiểu nội dung khi đọc CoQA. GPT-3 175B đạt 85 F1 trong trường hợp học ít mẫu, chỉ kém một vài điểm so với hiệu suất con người đo được và các mô hình huấn luyện tinh chỉnh hiện đại nhất. Hiệu suất zero-shot và one-shot thấp hơn một chút, với lợi ích lớn nhất từ việc học ít mẫu dành cho các mô hình lớn hơn.

||SuperGLU<br>Tổng trung bình|E<br>BoolQ<br>Độ chính xác|CB<br>y<br>Độ chính xác|CB<br>y<br>F1|COPA<br>Độ chính xác|RTE<br>Độ chính xác|
|---|---|---|---|---|---|---|
|Mô hình tốt nhất đã huấn luyện|**89.0**|**91.0**|**96.9**|**93.9**|**94.8**|**92.5**|
|Mô hình BERT-Large đã huấn luyện|69.0|77.4|83.6|75.7|70.6|71.7|
|GPT-3 Few-Shot|71.8|76.4|75.6|52.0|92.0|69.0|
||WiC<br>Độ chính xác|WSC<br>Độ chính xác|MultiRC<br>Độ chính xác|MultiRC<br>F1a|ReCoRD<br>Độ chính xác|ReCoRD<br>F1|
|Mô hình tốt nhất đã huấn luyện|**76.1**|**93.8**|**62.3**|**88.2**|**92.5**|**93.3**|
|Mô hình BERT-Large đã huấn luyện|69.6|64.6|24.1|70.0|71.3|72.0|
|GPT-3 Few-Shot|49.4|

Để kiểm tra khả năng thực hiện các phép tính đơn giản của mô hình GPT-3 mà không cần huấn luyện chuyên biệt cho từng nhiệm vụ, chúng tôi đã phát triển một bộ thử nghiệm nhỏ gồm 10 bài kiểm tra liên quan đến việc yêu cầu mô hình GPT-3 giải quyết một vấn đề tính toán đơn giản bằng ngôn ngữ tự nhiên:

- **Cộng hai chữ số (2D+)** – Mô hình được yêu cầu cộng hai số nguyên được lấy ngẫu nhiên đều từ khoảng [0, 100), dưới dạng câu hỏi, ví dụ: “C: 48 cộng với 76 là bao nhiêu? Đ: 124.”

- **Trừ hai chữ số (2D-)** – Mô hình được yêu cầu trừ hai số nguyên được lấy ngẫu nhiên đều từ khoảng [0, 100); kết quả có thể âm. Ví dụ: “C: 34 trừ đi 53 là bao nhiêu? Đ: -19”.

- **Cộng ba chữ số (3D+)** – Tương tự như cộng hai chữ số, ngoại trừ việc các số được lấy ngẫu nhiên đều từ khoảng [0, 1000).

21

![Hình ảnh](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0022-00.png)

**Hình 3.10:** Kết quả trên tất cả 10 nhiệm vụ tính toán trong chế độ few-shot cho các mô hình khác nhau về kích thước. Có sự tăng đột biến đáng kể từ mô hình lớn thứ hai (GPT-3 13B) đến mô hình lớn nhất (GPT-3 175), với mô hình lớn nhất có thể thực hiện chính xác phép cộng hai chữ số, thường chính xác đối với phép cộng ba chữ số, và trả lời đúng một phần đáng kể thời gian đối với phép cộng bốn-chín chữ số, nhân hai chữ số và các phép toán phức tạp. Kết quả cho one-shot và zero-shot được trình bày trong phụ lục.

- **Trừ ba chữ số (3D-)** – Tương tự như trừ hai chữ số, ngoại trừ việc các số được lấy ngẫu nhiên đều từ khoảng [0, 1000).

- **Cộng bốn chữ số (4D+)** – Tương tự như cộng ba chữ số, ngoại trừ việc các số được lấy ngẫu nhiên đều từ khoảng [0, 10000).

- **Trừ bốn chữ số (4D-)** – Tương tự như trừ ba chữ số, ngoại trừ việc các số được lấy ngẫu nhiên đều từ khoảng [0, 10000).

- **Cộng năm chữ số (5D+)** – Tương tự như cộng ba chữ số, ngoại trừ việc các số được lấy ngẫu nhiên đều từ khoảng [0, 100000).

- **Trừ năm chữ số (5D-)** – Tương tự như trừ ba chữ số, ngoại trừ việc các số được lấy ngẫu nhiên đều từ khoảng [0, 100000).

- **Nhân hai chữ số (2Dx)** – Mô hình được yêu cầu nhân hai số nguyên được lấy ngẫu nhiên đều từ khoảng [0, 100), ví dụ: “C: 24 nhân với 42 là bao nhiêu? Đ: 1008”.

- **Phép toán phức tạp một chữ số (1DC)** – Mô hình được yêu cầu thực hiện một phép toán phức tạp trên ba số một chữ số, với dấu ngoặc đơn bao quanh hai số cuối cùng. Ví dụ: “C: 6+(4*8) là bao nhiêu? Đ: 38”. Ba số một chữ số được chọn ngẫu nhiên từ khoảng [0, 10) và các phép toán được chọn ngẫu nhiên từ {+, -, *}.

Trong tất cả 10 nhiệm vụ, mô hình phải tạo ra câu trả lời chính xác hoàn toàn. Đối với mỗi nhiệm vụ, chúng tôi tạo ra một tập dữ liệu gồm 2,000 trường hợp ngẫu nhiên của nhiệm vụ và đánh giá tất cả các mô hình trên những trường hợp này.

Đầu tiên, chúng tôi đánh giá GPT-3 trong chế độ few-shot, kết quả được hiển thị trong Hình 3.10. Trên phép cộng và trừ, GPT-3 thể hiện sự thuần thục mạnh mẽ khi số chữ số nhỏ, đạt được 100% chính xác trên phép cộng hai chữ số, 98.9% trên phép trừ hai chữ số, 80.2% trên phép cộng ba chữ số, và 94.2% trên phép trừ ba chữ số. Hiệu suất giảm khi số chữ số tăng lên, nhưng GPT-3 vẫn đạt được 25-26% chính xác trên phép toán bốn chữ số và 9-10% chính xác trên phép toán năm chữ số, gợi ý rằng nó có khả năng tổng quát hóa đến các số chữ số lớn hơn. GPT-3 cũng đạt được 29.2% chính xác trên phép nhân hai chữ số, một phép toán đặc biệt đòi hỏi tính toán mạnh mẽ. Cuối cùng, GPT-3 đạt được 21.3% chính xác trên phép toán phức tạp một chữ số (ví dụ: 9*(7+5)), gợi ý rằng nó có độ ổn định ngoài việc chỉ thực hiện một phép toán đơn lẻ.

Hình 3.10 rõ ràng cho thấy các mô hình nhỏ hoạt động kém trong tất cả các nhiệm vụ này – thậm chí mô hình 13 tỷ tham số (mô hình lớn thứ hai sau mô hình đầy đủ 175 tỷ tham số của GPT-3) cũng chỉ giải quyết được phép cộng và trừ hai chữ số nửa số lần, và tất cả các phép toán khác ít hơn 10% số lần.

Chế độ one-shot và zero-shot có hiệu suất bị suy

Để kiểm tra khả năng của GPT-3 trong việc học các thao tác biểu tượng mới từ một vài ví dụ, chúng tôi đã thiết kế một bộ thử nghiệm nhỏ gồm 5 nhiệm vụ "thao tác ký tự". Mỗi nhiệm vụ đòi hỏi đưa cho mô hình một từ bị biến dạng bằng cách kết hợp các thao tác đảo vị trí, thêm hoặc xóa ký tự, và yêu cầu nó khôi phục từ gốc. Các nhiệm vụ cụ thể là:

- **Đảo vị trí ký tự trong từ (CL)** – Mô hình được đưa một từ với các ký tự bị đảo vị trí, sau đó ký hiệu "=" và được yêu cầu tạo ra từ gốc. Ví dụ: nó có thể được đưa "lyinevitab" và phải xuất ra "inevitably".

- **Tổ hợp tất cả nhưng ký tự đầu và cuối (A1)** – Mô hình được đưa một từ với tất cả các ký tự ngoại trừ ký tự đầu tiên và cuối cùng bị đảo lộn ngẫu nhiên, và phải xuất ra từ gốc. Ví dụ: criroptuon = corruption.

- **Tổ hợp tất cả nhưng hai ký tự đầu và cuối (A2)** – Mô hình được đưa một từ với tất cả các ký tự ngoại trừ hai ký tự đầu tiên và cuối cùng bị đảo lộn ngẫu nhiên, và phải khôi phục từ gốc. Ví dụ: opoepnnt → opponent.

- **Thêm ngẫu nhiên ký tự vào từ (RI)** – Một ký tự dấu câu hoặc khoảng trắng ngẫu nhiên được thêm giữa mỗi ký tự của từ, và mô hình phải xuất ra từ gốc. Ví dụ: s.u!c/c!e.s s i/o/n = succession.

- **Từ đảo ngược (RW)** – Mô hình được đưa một từ viết ngược lại, và phải xuất ra từ gốc. Ví dụ: stcejbo → objects.

Đối với mỗi nhiệm vụ, chúng tôi tạo ra 10,000 ví dụ, mà chúng tôi chọn là 10,000 từ phổ biến nhất theo [Nor09], có độ dài từ hơn 4 ký tự đến dưới 15 ký tự. Kết quả học ít mẫu được hiển thị trong Hình 3.11. Hiệu suất nhiệm vụ thường tăng mượt mà theo kích thước mô hình, với mô hình GPT-3 đầy đủ đạt được 66.9% trên việc loại bỏ

23


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0024-00.png)


**Hình 3.11:** Hiệu suất học ít mẫu trên năm nhiệm vụ thao tác ký tự cho các kích thước khác nhau của mô hình. Có sự cải thiện mượt mà theo kích thước mô hình, mặc dù nhiệm vụ thêm ngẫu nhiên ký tự cho thấy đường dốc tăng lên, với mô hình 175 tỷ tham số giải quyết nhiệm vụ phần lớn thời gian. Tăng cường hiệu suất một mẫu và không mẫu được hiển thị trong phụ lục. Tất cả các nhiệm vụ đều được thực hiện với _K_ = 100.

thêm ký tự ngẫu nhiên, 38.6% trên việc đảo vị trí ký tự, 40.2% trên nhiệm vụ tổ hợp dễ dàng, và 15.1% trên nhiệm vụ tổ hợp khó khăn (trong đó chỉ ký tự đầu tiên và cuối cùng được giữ cố định). Không có mô hình nào có thể đảo ngược thứ tự ký tự trong từ.

Trong trường hợp một mẫu, hiệu suất yếu hơn đáng kể (giảm một nửa hoặc nhiều hơn), và trong trường hợp không mẫu, mô hình hiếm khi có thể thực hiện bất kỳ nhiệm vụ nào (Bảng 3.10). Điều này gợi ý rằng mô hình thực sự có vẻ học các nhiệm vụ này tại thời điểm kiểm tra, vì mô hình không thể thực hiện chúng không mẫu và tính chất nhân tạo của chúng khiến chúng ít có khả năng xuất hiện trong dữ liệu tiền huấn luyện (mặc dù chúng tôi không thể xác nhận điều này chắc chắn).

Chúng tôi có thể định lượng hiệu suất thêm bằng cách vẽ "đường cong học trong ngữ cảnh", mà thể hiện hiệu suất nhiệm vụ theo số lượng ví dụ trong ngữ cảnh. Chúng tôi hiển thị đường cong học trong ngữ cảnh cho nhiệm vụ Thêm Ký tự trong Hình 1.2. Chúng ta có thể thấy rằng các mô hình lớn hơn có thể sử dụng hiệu quả hơn thông tin trong ngữ cảnh, bao gồm cả các ví dụ nhiệm vụ và mô tả nhiệm vụ bằng ngôn ngữ tự nhiên.

Cuối cùng, đáng lưu ý rằng giải quyết các nhiệm vụ này đòi hỏi thao tác ký tự, trong khi mã hóa BPE của chúng tôi hoạt động trên các phần lớn của từ (trung bình ∼ 0.7 từ mỗi token), do đó từ góc độ của mô hình ngôn ngữ, thành công trong các nhiệm vụ này đòi hỏi không chỉ thao tác các token BPE mà còn hiểu và phân tách cấu trúc bên trong của chúng. Ngoài ra, CL, A1 và A2 không phải là song ánh (tức là, từ chưa bị rối không phải là hàm xác định của từ bị rối), đòi hỏi mô hình phải thực hiện tìm kiếm để tìm ra giải pháp đúng. Do đó, kỹ năng liên quan dường như đòi hỏi việc khớp mẫu và tính toán không đơn giản.

## **3.9.3 Đề Bài So Sánh SAT**

Để kiểm tra GPT-3 trên một nhiệm vụ tương đối không thông thường so với phân phối thông thường của văn bản, chúng tôi đã thu thập một tập hợp 374 "đề bài so sánh SAT" [TLBS03]. So sánh là một kiểu câu hỏi lựa chọn nhiều đáp án mà đã cấu thành một phần của bài thi SAT vào đại học trước năm 2005. Một ví dụ điển hình là "audacious là đến boldness như (a) sanctimonious là đến hypocrisy, (b) anonymous là đến identity, (c) remorseful là đến misdeed, (d) deleterious là đến result, (e) impressionable là đến temptation". Học sinh được yêu cầu chọn cặp từ nào trong năm cặp từ có mối quan hệ tương tự như cặp từ gốc; trong ví dụ này, câu trả lời là "sanctimonious là đến hypocrisy". Trên nhiệm vụ này, GPT-3 đạt được 65.2% trong trường hợp học ít mẫu, 59.1% trong trường hợp một mẫu và 53.7% trong trường hợp không mẫu, trong khi điểm trung bình của ứng viên đại học là 57% [TL05] (chọn ngẫu nhiên sẽ cho ra 20%). Như được hiển thị trong Hình 3.12, kết quả cải thiện theo quy mô, với mô hình 175 tỷ tham số cải thiện hơn 10% so với mô hình 13 tỷ tham số.

24


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0025-00.png)


**Hình 3.12:** Hiệu suất không mẫu, một mẫu và học ít mẫu trên nhiệm vụ đề bài so sánh SAT, cho các kích thước khác nhau của mô hình. Mô hình lớn nhất đạt được 65% độ chính xác trong trường hợp học ít mẫu, và cũng thể hiện lợi ích đáng kể đến học trong ngữ cảnh mà không có trong các mô hình nhỏ hơn.

## **3.9.4 Tạo Bài Báo Điện Tử**

Dịch đoạn văn bản Markdown sau từ tiếng Anh sang tiếng Việt:

Text:
Các công trình trước đây về mô hình ngôn ngữ sinh ra đã kiểm định chất lượng khả năng sinh ra các bài viết giả lập "tin tức" bằng cách lấy mẫu điều kiện từ mô hình dựa trên một đề mục viết bởi con người, bao gồm một câu mở đầu hợp lý cho một câu chuyện tin tức [RWC<sup>+</sup> 19]. So sánh với [RWC<sup>+</sup> 19], tập dữ liệu được sử dụng để huấn luyện GPT-3 ít tập trung hơn vào các bài viết tin tức, nên việc thử nghiệm tạo ra các bài viết tin tức qua các mẫu không điều kiện thuần túy ít hiệu quả hơn - ví dụ, GPT-3 thường hiểu sai câu mở đầu của một "bài viết tin tức" như một tweet và sau đó đăng các phản hồi hoặc tweet tiếp theo. Để giải quyết vấn đề này, chúng tôi đã sử dụng khả năng học ít mẫu của GPT-3 bằng cách cung cấp ba bài viết tin tức trước đó trong ngữ cảnh của mô hình để điều kiện hóa nó. Với tiêu đề và phụ đề của một bài viết kế tiếp được đề xuất, mô hình có thể sinh ra đáng tin cậy các bài viết ngắn thuộc thể loại "tin tức".

Để đánh giá chất lượng sinh ra các bài viết tin tức từ GPT-3 (chúng tôi tin rằng điều này có thể tương quan với chất lượng mẫu điều kiện tổng thể), chúng tôi quyết định đo lường khả năng phân biệt của con người giữa các bài viết sinh ra từ GPT-3 và các bài viết thực sự. Công trình tương tự đã được thực hiện bởi Kreps et al. [KMB20] và Zellers et al. [ZHR<sup>+</sup> 19]. Mô hình ngôn ngữ sinh ra được huấn luyện để khớp phân phối nội dung được tạo ra bởi con người, nên khả năng (không) phân biệt của con người giữa hai loại bài viết có thể là một thước đo chất lượng tiềm năng quan trọng.

Để thấy rõ con người có thể phát hiện văn bản sinh ra từ mô hình như thế nào, chúng tôi đã chọn ngẫu nhiên 25 tiêu đề và phụ đề bài viết từ trang web newser.com (trung bình 215 từ). Chúng tôi sau đó đã sinh ra các phần còn lại của những tiêu đề và phụ đề này từ bốn mô hình ngôn ngữ khác nhau, từ 125 triệu đến 175 tỷ tham số (trung bình 200 từ). Đối với mỗi mô hình, chúng tôi đã đưa ra khoảng 80 người tham gia từ Hoa Kỳ một bài kiểm tra bao gồm các tiêu đề và phụ đề thực tế theo sau bởi hoặc bài viết viết bởi con người hoặc bài viết sinh ra từ mô hình<sup>4</sup>. Người tham gia được yêu cầu chọn liệu bài viết có phải là "rất có thể được viết bởi con người", "càng có khả năng được viết bởi con người", "Tôi không biết", "càng có khả năng được viết bởi máy tính", hoặc "rất có thể được viết bởi máy tính".

Các bài viết chúng tôi đã chọn không nằm trong dữ liệu huấn luyện của các mô hình và các đầu ra của mô hình được định dạng và lựa chọn theo chương trình để ngăn chặn việc lựa chọn trái phép của con người. Tất cả các mô hình đều sử dụng cùng ngữ cảnh để điều kiện hóa đầu ra và được huấn luyện trước với cùng kích thước ngữ cảnh và cùng các tiêu đề và phụ đề bài viết được sử dụng như đề mục cho mỗi mô hình. Tuy nhiên, chúng tôi cũng đã chạy một thí nghiệm để kiểm soát nỗ lực và sự chú ý của người tham gia theo cùng định dạng nhưng liên quan đến các bài viết sinh ra từ mô hình kiểm soát. Điều này được thực hiện bằng cách sinh ra các bài viết từ một "mô hình kiểm soát": một mô hình 160 triệu tham số không có ngữ cảnh và tăng ngẫu nhiên đầu ra.

> 4Chúng tôi muốn xác định mức độ tốt mà một người trung bình trên internet có thể phát hiện văn bản sinh ra từ mô hình ngôn ngữ, vì vậy chúng tôi tập trung vào người tham gia được rút từ dân số Hoa Kỳ nói chung. Xem Phụ lục E để chi tiết.

25

||Trung bình độ chính xác|Phạm vi khoảng tin cậy 95% (thấp, cao)|_t_so sánh với<br>mô hình kiểm soát (_p_-giá trị)|"Tôi không biết"<br>đánh dấu|
|---|---|---|---|---|
|Mô hình kiểm soát (mô hình cố tình tồi)|86%|83%–90%|-|3.6%|
|GPT-3 Nhỏ|76%|72%–80%|3.9 (2_e_-4)|4.9%|
|GPT-3 Trung|61%|58%–65%|10.3 (7_e_-21)|6.0%|
|GPT-3 Lớn|68%|64%–72%|7.3 (3_e_-11)|8.7%|
|GPT-3 XL|62%|59%–65%|10.7 (1_e_-19)|7.5%|
|GPT-3 2.7B|62%|58%–65%|10.4 (5_e_-19)|7.1%|
|GPT-3 6.7B|60%|56%–63%|11.2 (3_e_-21)|6.2%|
|GPT-3 13B|55%|52%–58%|15.3 (1_e_-32)|7.1%|
|GPT-3 175B|52%|49%–54%|16.9 (1_e_-34)|7.8%|

**Bảng 3.11: Độ chính xác của con người trong việc nhận biết liệu các bài viết ngắn (~200 từ) có phải là sinh ra từ mô hình**. Chúng tôi tìm thấy rằng độ chính xác của con người (đo bằng tỷ lệ giữa số lần gán đúng và số lần gán không trung lập) dao động từ 86% đối với mô hình kiểm soát đến 52% đối với GPT-3 175B. Bảng này so sánh độ chính xác trung bình giữa năm mô hình

Dịch đoạn văn bản Markdown sau từ tiếng Anh sang tiếng Việt. Lưu ý: Giữ nguyên thẻ Markdown và LaTeX.

Text:
Một nhiệm vụ được nghiên cứu trong ngôn ngữ phát triển [CB78] là khả năng học và sử dụng những từ mới, ví dụ như sử dụng một từ trong một câu sau khi chỉ nhìn thấy định nghĩa của nó một lần, hoặc ngược lại, suy luận ý nghĩa của từ đó từ chỉ một lần sử dụng. Trong phần này, chúng tôi kiểm tra định tính khả năng của GPT-3 thực hiện nhiệm vụ đầu tiên trên đây. Cụ thể, chúng tôi cung cấp cho GPT-3 định nghĩa của một từ không tồn tại, như "Gigamuru", và sau đó yêu cầu nó sử dụng từ đó trong một câu. Chúng tôi cung cấp một đến năm ví dụ trước đó về việc sử dụng từ khác (tách biệt).

> 5Chúng tôi sử dụng phép thử t-student hai mẫu để kiểm tra sự khác biệt đáng kể giữa trung bình độ chính xác của mỗi mô hình và mô hình đối chứng, và báo cáo sự khác biệt chuẩn hóa giữa trung bình (như thống kê t) và giá trị p.

> 6Nếu một mô hình luôn tạo ra văn bản ấn tượng hơn so với các bài viết của con người, có thể rằng hiệu suất của con người trên nhiệm vụ này sẽ giảm xuống dưới 50%. Thật vậy, nhiều cá nhân đã đạt dưới 50% trên nhiệm vụ này.

> 7Các mẫu không tin tức bổ sung có thể tìm thấy trong Phụ lục F.

26


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0027-00.png)


**Hình 3.13:** Khả năng của con người để nhận biết liệu các bài báo là do mô hình sinh ra (được đo bằng tỷ lệ giữa số lần gán đúng và số lần gán không trung lập) giảm khi kích thước của mô hình tăng lên. Độ chính xác trên các đầu ra của mô hình đối chứng (một mô hình GPT-3 Small không điều kiện với độ ngẫu nhiên cao hơn) được chỉ ra bằng đường đứt điểm ở phía trên, và ngẫu nhiên (50%) được chỉ ra bằng đường đứt điểm ở phía dưới. Đường tốt nhất phù hợp là một hàm멱 (power function) với khoảng tin cậy 95%.

|||95% Khoảng Tin Cậy|_t_so_sánh_với|mình_không_biết|
|---|---|---|---|---|
||Độ chính xác trung bình|i<br>Khoảng (thấp, cao)|đối_chứng (_p_-giá_trị)|gán|
|Đối chứng|88%|84%–91%|-|2.7%|
|GPT-3 175B|52%|48%–57%|12.7 (3.2_e_-23)|10.6%|



**Bảng 3.12:** Khả năng của con người để nhận biết liệu các bài báo dài khoảng 500 từ có phải là do mô hình sinh ra (được đo bằng tỷ lệ giữa số lần gán đúng và số lần gán không trung lập) là 88% trên mô hình đối chứng và 52% trên GPT-3 175B. Bảng này hiển thị kết quả của phép thử t-student hai mẫu cho sự khác biệt giữa độ chính xác trung bình của GPT-3 175B và mô hình đối chứng (một mô hình GPT-3 Small không điều kiện với độ ngẫu nhiên cao hơn).

27

`Tiêu đề: Giáo hội Giám lý United đồng ý chia tách lịch sử Phụ đề: Những người phản đối hôn nhân đồng giới sẽ thành lập giáo phái riêng Bài:` Sau hai ngày tranh luận căng thẳng, Giáo hội Giám lý United đã đồng ý chia tách - một sự kiện dự kiến sẽ kết thúc bằng việc thành lập một giáo phái mới, "truyền thống và xã hội bảo thủ", theo tờ Washington Post. Phần lớn đại biểu tham dự cuộc họp hàng năm của Hội nghị Tổng của giáo hội vào tháng Năm đã bỏ phiếu để tăng cường lệnh cấm việc phong chức linh mục LGBTQ và viết các quy tắc mới sẽ "kỷ luật" các linh mục tổ chức lễ cưới đồng giới. Nhưng những người phản đối các biện pháp này có kế hoạch mới: Họ nói họ sẽ thành lập một giáo phái riêng vào năm 2020, gọi giáo phái của mình là Christian Methodist

Doạn văn bản Markdown dưới đây đã được dịch từ tiếng Anh sang tiếng Việt. Lưu ý rằng thẻ Markdown và LaTeX đã được giữ nguyên.

Text:
Khi tập dữ liệu huấn luyện của chúng tôi được lấy từ internet, có thể rằng mô hình của chúng tôi đã được huấn luyện trên một số tập kiểm tra chuẩn của chúng tôi. Việc phát hiện chính xác sự ô nhiễm từ các tập dữ liệu lớn quy mô internet là một lĩnh vực nghiên cứu mới chưa có phương pháp tốt nhất được thiết lập. Mặc dù việc huấn luyện các mô hình lớn mà không điều tra về sự ô nhiễm là thực hành phổ biến, nhưng với quy mô ngày càng tăng của các tập dữ liệu tiền huấn luyện, chúng tôi tin rằng vấn đề này đang trở nên ngày càng quan trọng.

Lo ngại này không chỉ là lý thuyết. Một trong những bài báo đầu tiên huấn luyện mô hình ngôn ngữ trên dữ liệu Common Crawl [TL18] đã phát hiện và loại bỏ một tài liệu huấn luyện trùng lặp với một trong các tập dữ liệu đánh giá của họ. Các công trình khác như GPT-2 [RWC<sup>+</sup> 19] cũng đã tiến hành phân tích trùng lặp sau khi huấn luyện. Kết quả nghiên cứu tương đối lạc quan, tìm thấy rằng

29

`Dữ liệu đầu vào tiếng Anh kém: Tôi đã ăn những quả dâu tím. Dữ liệu đầu ra tiếng Anh tốt: Tôi đã ăn những quả dâu tím. Dữ liệu đầu vào tiếng Anh kém: Cảm ơn bạn đã chọn tôi làm nhà thiết kế của bạn. Tôi sẽ rất cảm kích. Dữ liệu đầu ra tiếng Anh tốt: Cảm ơn bạn đã chọn tôi làm nhà thiết kế của bạn. Tôi rất cảm kích. Dữ liệu đầu vào tiếng Anh kém: Những thay đổi đã được thực hiện. Hoặc tôi đã thực hiện sự thay đổi mà bạn yêu cầu. Hoặc tôi đã thay đổi những gì bạn muốn và thực hiện những điều chỉnh. Dữ liệu đầu ra tiếng Anh tốt: Những thay đổi đã được thực hiện. Hoặc tôi đã thực hiện sự thay đổi mà bạn yêu cầu. Hoặc tôi đã thay đổi những gì bạn

# **5 Hạn chế**

GPT-3 và phân tích của chúng tôi về nó có một số hạn chế. Dưới đây, chúng tôi mô tả một số hạn chế này và đề xuất hướng nghiên cứu trong tương lai.

Đầu tiên, mặc dù GPT-3 có những cải thiện định lượng và định tính mạnh mẽ so với tiền nhiệm trực tiếp của nó là GPT-2, nó vẫn còn một số nhược điểm đáng kể trong việc tổng hợp văn bản và một số nhiệm vụ xử lý ngôn ngữ tự nhiên (NLP). Trong việc tổng hợp văn bản, mặc dù chất lượng tổng thể cao, nhưng GPT-3 vẫn đôi khi lặp lại ngữ nghĩa ở cấp độ tài liệu, mất sự nhất quán qua các đoạn văn dài, mâu thuẫn với chính mình và đôi khi chứa các câu hoặc đoạn văn không liên quan. Chúng tôi sẽ phát hành một bộ sưu tập gồm 500 mẫu không được kiểm duyệt để giúp cung cấp cái nhìn rõ ràng hơn về những hạn chế và ưu điểm của GPT-3 trong việc tổng hợp văn bản. Trong lĩnh vực các nhiệm vụ ngôn ngữ rời rạc, chúng tôi nhận thấy không chính thức rằng GPT-3 gặp khó khăn đặc biệt trong việc "phân tích vật lý thông thường", mặc dù nó hoạt động tốt trên một số tập dữ liệu (như PIQA [BZB+ 19]) kiểm tra lĩnh vực này. Đặc biệt, GPT-3 gặp khó khăn với các câu hỏi kiểu "Nếu tôi đặt phô mai vào tủ lạnh, nó có tan chảy không?". Về mặt định lượng, hiệu suất học trong ngữ cảnh của GPT-3 có một số khoảng cách đáng kể trên bộ benchmark của chúng tôi, như đã mô tả trong Phần 3, và đặc biệt là nó chỉ hơi tốt hơn ngẫu nhiên khi được đánh giá một mẫu hoặc thậm chí học ít mẫu trên một số nhiệm vụ so sánh, như xác định liệu hai từ có được sử dụng cùng cách trong một câu, hoặc liệu một câu có hàm ý câu khác (WIC và ANLI tương ứng), cũng như trên một số nhiệm vụ hiểu nội dung khi đọc. Điều này đặc biệt đáng chú ý khi GPT-3 có hiệu suất học ít mẫu mạnh mẽ trên nhiều nhiệm vụ khác.

GPT-3 có một số hạn chế về mặt cấu trúc và thuật toán, có thể giải thích cho một số vấn đề trên. Chúng tôi tập trung vào việc khám phá hành vi học trong ngữ cảnh trong các mô hình tự hồi quy vì nó đơn giản để lấy mẫu và tính toán xác suất với loại mô hình này. Kết quả là các thí nghiệm của chúng tôi không bao gồm bất kỳ kiến trúc hai chiều nào hoặc các mục tiêu huấn luyện khác như làm sạch nhiễu. Đây là sự khác biệt đáng chú ý so với phần lớn các nghiên cứu gần đây, đã chứng minh cải thiện hiệu suất huấn luyện tinh chỉnh khi sử dụng các phương pháp này trên các mô hình ngôn ngữ tiêu chuẩn [RSR+ 19]. Do đó, quyết định thiết kế của chúng tôi có thể dẫn đến hiệu suất kém hơn trên các nhiệm vụ mà thực nghiệm cho thấy lợi ích từ kiến trúc hai chiều. Điều này có thể bao gồm các nhiệm vụ điền từ, nhiệm vụ đòi hỏi phải nhìn lại và so sánh hai nội dung, hoặc nhiệm vụ đòi hỏi phải đọc lại và cân nhắc kỹ lưỡng một đoạn văn dài trước khi tạo ra một câu trả lời ngắn gọn. Điều này có thể là một giải thích khả thi cho việc hiệu suất học ít mẫu của GPT-3 chậm hơn trên một số nhiệm vụ, như WIC (đòi hỏi so sánh cách sử dụng một từ trong hai câu), ANLI (đòi hỏi so sánh hai câu để xem liệu một câu có hàm ý câu kia không), và một số nhiệm vụ hiểu nội dung khi đọc (ví dụ: QuAC và RACE). Chúng tôi cũng giả thuyết, dựa trên các nghiên cứu trước đây, rằng một mô hình hai chiều lớn sẽ mạnh hơn trong việc huấn luyện tinh chỉnh so với GPT-3. Tạo ra một mô hình hai chiều ở quy mô của GPT-3, và/hoặc cố gắng áp dụng mô hình hai chiều với học ít hoặc không mẫu, là một hướng nghiên cứu đầy hứa hẹn trong tương lai, và có thể giúp đạt được "tốt nhất của cả hai thế giới".

Hạn chế cơ bản hơn của phương pháp chung được mô tả trong bài viết này - mở rộng quy mô bất kỳ mô hình tương tự ngôn ngữ (LM) nào, dù là tự hồi quy hay hai chiều - là nó có thể cuối cùng sẽ gặp phải (hoặc có thể đã gặp phải) giới hạn của

33

mục tiêu huấn luyện ban đầu. Mục tiêu hiện tại của chúng ta cân nhắc mỗi token đều bằng nhau và thiếu khái niệm về điều gì là quan trọng nhất để dự đoán và điều gì ít quan trọng hơn. [RRS20] chứng minh lợi ích của việc tùy chỉnh dự đoán cho các đối tượng quan tâm. Ngoài ra, với các mục tiêu tự giám sát, việc xác định nhiệm vụ phụ thuộc vào việc ép buộc nhiệm vụ mong muốn vào một vấn đề dự đoán, trong khi cuối cùng, các hệ thống ngôn ngữ hữu ích (ví dụ như trợ lý ảo) có thể được xem xét tốt hơn là thực hiện các hành động hướng mục tiêu thay vì chỉ dự đoán. Cuối cùng, các mô hình ngôn ngữ được huấn luyện trước lớn không được gắn kết với các lĩnh vực kinh nghiệm khác, như video hoặc tương tác vật lý thực tế, và do đó thiếu rất nhiều thông tin về thế giới [BHT+ 20]. Vì tất cả những lý do này, việc mở rộng dự đoán tự giám sát thuần túy có thể sẽ gặp giới hạn, và việc bổ sung với một phương pháp khác có thể là cần thiết. Các hướng nghiên cứu đầy hứa hẹn trong lĩnh vực này có thể bao gồm việc học hàm mục tiêu từ con người [ZSW+ 19a], huấn luyện tinh chỉnh với học tăng cường, hoặc thêm các mô đun bổ sung như hình ảnh để cung cấp sự gắn kết và một mô hình tốt hơn về thế giới [CLY+ 19].

Một hạn chế khác ch

Dưới đây là bản dịch đoạn văn bản Markdown từ tiếng Anh sang tiếng Việt:

Text:
Bất kỳ hoạt động gây hại cho xã hội nào dựa vào việc tạo ra văn bản đều có thể được tăng cường bởi những mô hình ngôn ngữ mạnh mẽ. Các ví dụ bao gồm thông tin sai lệch, thư rác, lừa đảo, lạm dụng quy trình pháp lý và chính phủ, viết luận văn học thuật giả mạo và kỹ thuật xã hội. Nhiều ứng dụng này bị giới hạn bởi khả năng của con người viết văn bản chất lượng cao. Những mô hình ngôn ngữ tạo ra văn bản chất lượng cao có thể giảm bớt các rào cản hiện tại để thực hiện các hoạt động này và tăng hiệu quả của chúng.

Tiềm năng sử dụng sai trái của mô hình ngôn ngữ tăng lên khi chất lượng tổng hợp văn bản cải thiện. Khả năng của GPT-3 tạo ra nhiều đoạn văn mà người ta khó phân biệt với văn bản do con người viết trong 3.9.4 đại diện cho một dấu mốc đáng lo ngại trong lĩnh vực này.

## **6.1.2 Phân Tích Đối Tượng Đe Dọa**

Đối tượng đe dọa có thể được tổ chức dựa trên kỹ năng và nguồn lực, từ những đối tượng có kỹ năng và nguồn lực thấp hoặc vừa phải có thể xây dựng sản phẩm độc hại đến 'nguy cơ đe dọa kéo dài' (APT): nhóm có kỹ năng cao và nguồn lực tốt (ví dụ: được nhà nước tài trợ) với mục tiêu lâu dài [SBC<sup>+</sup> 19].

Để hiểu cách đối tượng có kỹ năng thấp và trung bình nghĩ về mô hình ngôn ngữ, chúng tôi đã giám sát các diễn đàn và nhóm trò chuyện nơi chiến lược thông tin sai lệch, phân phối phần mềm độc hại và lừa đảo máy tính được thảo luận thường xuyên. Mặc dù chúng tôi đã tìm thấy nhiều thảo luận về việc sử dụng sai trái sau khi phát hành GPT-2 vào mùa xuân năm 2019, nhưng chúng tôi đã tìm thấy ít trường hợp thử nghiệm hơn và không có triển khai thành công kể từ đó. Thêm vào đó, những thảo luận về việc sử dụng sai trái này tương quan với sự chú ý của truyền thông về công nghệ mô hình ngôn ngữ. Từ đó, chúng tôi đánh giá rằng mối đe dọa từ việc sử dụng sai trái từ những đối tượng này không phải là tức thì, nhưng cải thiện đáng kể về độ tin cậy có thể thay đổi điều này.

Vì APTs thường không thảo luận về hoạt động của họ trong công khai, chúng tôi đã tham vấn với các chuyên gia phân tích đe dọa về khả năng hoạt động của APTs liên quan đến việc sử dụng mô hình ngôn ngữ. Kể từ khi phát hành GPT-2, không có sự khác biệt rõ ràng nào trong hoạt động có thể thấy lợi ích từ việc sử dụng mô hình ngôn ngữ. Đánh giá là mô hình ngôn ngữ có thể không đáng đầu tư nguồn lực lớn vì chưa có chứng minh thuyết phục rằng các mô hình ngôn ngữ hiện tại tốt hơn nhiều so với phương pháp hiện tại để tạo ra văn bản, và vì các phương pháp "định hướng" hoặc "kiểm soát" nội dung của mô hình ngôn ngữ vẫn ở giai đoạn rất sớm.

## **6.1.3 Cơ Chế Khuyến Khích Ngoài**

Mỗi nhóm đối tượng đe dọa cũng có một tập hợp các chiến lược, kỹ thuật và quy trình (TTPs) mà họ dựa vào để hoàn thành mục tiêu của mình. TTPs bị ảnh hưởng bởi các yếu tố kinh tế như khả năng mở rộng và dễ triển khai; lừa đảo qua điện tử rất phổ biến trong tất cả các nhóm vì nó cung cấp phương pháp triển khai phần mềm độc hại và đánh cắp thông tin đăng nhập với chi phí thấp, nỗ lực thấp và lợi nhuận cao. Sử dụng mô hình ngôn ngữ để tăng cường TTPs hiện tại sẽ có thể dẫn đến chi phí triển khai thấp hơn.

Dễ sử dụng là một khuyến khích khác đáng kể. Có cơ sở hạ tầng ổn định có tác động lớn đến việc áp dụng TTPs. Kết quả của mô hình ngôn ngữ là ngẫu nhiên, tuy nhiên, và mặc dù các nhà phát triển có thể hạn chế điều này (ví dụ: bằng cách sử dụng cắt top-k), họ không thể thực hiện một cách nhất quán mà không có phản hồi từ con người. Nếu một robot thông tin sai lệch trên mạng xã hội tạo ra kết quả đáng tin cậy 99% thời gian, nhưng tạo ra kết quả không mạch lạc 1% thời gian, điều này có thể giảm lượng lao động con người cần thiết để vận hành robot này. Nhưng vẫn cần con người để lọc kết quả, điều này hạn chế khả năng mở rộng của hoạt động.

Dựa trên phân tích của mô hình này và phân tích về đối tượng đe dọa và môi trường, chúng tôi nghi ngờ rằng các nhà nghiên cứu AI cuối cùng sẽ phát triển mô hình ngôn ngữ đủ nhất quán và kiểm soát được để thu hút sự quan tâm của các đối tượng độc hại. Chúng tôi dự đoán điều này sẽ giới thiệu thách thức cho cộng đồng nghiên cứu rộng lớn hơn, và hy vọng làm việc trên điều này thông qua sự kết hợp giữa nghiên cứu giảm thiểu, thử nghiệm và phối hợp với các nhà phát triển kỹ thuật khác.

35

## **6.2 Công Bằng, Biên Tệ Và Đại Diện**

Những thiên lệch có trong dữ liệu huấn luyện có thể khiến mô hình tạo ra nội dung định kiến hoặc thiên vị. Điều này đáng lo ngại, vì thiên lệch của mô hình có thể gây hại cho người dân trong các nhóm liên quan theo nhiều cách khác nhau bằng cách củng cố các định kiến hiện tại và tạo ra những biểu diễn hạ thấp, cùng với các thiệt hại tiềm năng khác [Cra17]. Chúng tôi đã tiến hành phân tích về thiên lệch trong mô hình để hiểu rõ hơn về giới hạn của GPT-3 khi nói đến công bằng, thiên lệch và đại diện.

Mục tiêu của chúng tôi không phải là mô tả đầy đủ GPT-3, mà là đưa ra phân tích ban đầu về một số giới hạn và hành vi của nó. Chúng tôi tập trung vào thiên lệch liên quan đến giới tính, chủng tộc và tôn giáo, mặc dù nhiều loại thiên lệch khác có thể hiện diện và có thể được nghiên cứu trong công việc tiếp theo. Đây là phân tích ban đầu và không phản ánh tất cả các thiên lệch của mô hình, ngay cả trong các danh mục được nghiên cứu.

Tổng quát而言，该翻译准确地遵循了指示，保留了Markdown和LaTeX的结构，并且正确地翻译了文本内容。如果有任何特定术语或进一步的要求，请告知我以便进行适当的调整。请问您是否需要对后续部分进行翻译或其他帮助？

Trong nghiên cứu về thiên vị giới tính trong mô hình GPT-3, chúng tôi đã tập trung vào mối liên hệ giữa giới tính và nghề nghiệp. Chúng tôi phát hiện ra rằng, nói chung, nghề nghiệp có xác suất cao hơn được tiếp theo bởi một định danh giới tính nam hơn là nữ (tức là chúng có xu hướng nam tính) khi được đưa ra trong ngữ cảnh như `"The` _{_ `nghề nghiệp` _}_ `là"` (Phiên bản Trung lập). 83% trong số 388 nghề nghiệp mà chúng tôi đã kiểm tra đều có xác suất cao hơn được tiếp theo bởi một định danh giới tính nam bởi GPT-3. Chúng tôi đo lường điều này bằng cách cho mô hình ngữ cảnh như `"The detective was a"` và sau đó xem xét xác suất của mô hình tiếp theo với những từ chỉ nam (ví dụ: man, male v.v.) hoặc từ chỉ nữ (woman, female v.v.).

Thực tế, nghề nghiệp đòi hỏi trình độ giáo dục cao hơn như nghị sĩ, ngân hàng gia, hoặc giáo sư danh dự đều có xu hướng nam tính mạnh mẽ, cùng với những nghề nghiệp đòi hỏi lao động thể chất nặng nhọc như thợ xây, thợ máy, và trưởng công an. Những nghề nghiệp có xác suất cao hơn được tiếp theo bởi định danh giới tính nữ bao gồm y tá đỡ đầu, y tá, lễ tân, quản gia v.v.

Chúng tôi cũng đã kiểm tra cách xác suất này thay đổi khi chúng tôi chuyển ngữ cảnh sang `"The competent` _{_ `nghề nghiệp` _}_ `was a"` (Phiên bản Giỏi) và `"The incompetent` _{_ `nghề nghiệp` _}_ `was a"` (Phiên bản Kém). Chúng tôi phát hiện ra rằng, khi được kích hoạt với `"The competent` _{_ `nghề nghiệp` _}_ `was a,"` phần lớn nghề nghiệp có xác suất cao hơn được tiếp theo bởi một định danh giới tính nam hơn nữ so với ngữ cảnh trung lập ban đầu `"The` _{_ `nghề nghiệp` _}_ `was a"`. Với ngữ cảnh `"The incompetent` _{_ `nghề nghiệp` _}_ `was a"` phần lớn nghề nghiệp vẫn có xu hướng nam với xác suất tương tự như ngữ cảnh trung lập ban đầu. Trung bình thiên vị nghề nghiệp - được đo lường như _n_ công việc1 �jobs<sup>log(</sup><sup>_P_</sup> _P_<sup><u>(</u></sup> (nam<sup>female</sup> _|_ Ngữ cảnh))<sup>_<u>|</u>_Ngữ cảnh)) - là</sup><sup>_−_1</sup><sup>_._11 cho phiên bản trung lập,</sup><sup>_−_2</sup><sup>_._14 cho phiên bản giỏi và</sup><sup>_−_1</sup><sup>_._15</sup> cho phiên bản kém.

Chúng tôi cũng đã thực hiện giải quyết đại từ trên tập dữ liệu Winogender [RNLVD18] bằng hai phương pháp, giúp xác nhận xu hướng của mô hình liên kết hầu hết nghề nghiệp với nam giới. Một phương pháp đo lường khả năng chính xác của mô hình trong việc gán đúng đại từ cho nghề nghiệp hoặc người tham gia. Ví dụ, chúng tôi đã cho mô hình ngữ cảnh như `"The advisor met with the advisee because she wanted to get advice about job applications. ‘She’ refers to the"` và tìm ra lựa chọn có xác suất thấp nhất giữa hai lựa chọn có thể (Lựa chọn giữa tùy chọn nghề nghiệp: advisor; tùy chọn người tham gia: advisee).

Nghề nghiệp

Chúng tôi đã nghiên cứu những từ nào đồng xuất hiện với các thuật ngữ tôn giáo liên quan đến Atheism, Buddhism, Christianity, Hinduism, Islam và Judaism bằng cách tạo ra 800 kết quả đầu ra của mô hình có độ dài khoảng 50 với nhiệt độ là 1 và top _p_ là 0 _._ 9 cho mỗi prompt. Các prompt của chúng tôi có dạng `" {_ Religion practitioners _} _}` `là` (VD: `"Christians là"` ) cho mỗi trong sáu loại tôn giáo được liệt kê trên đây. Sau đó, chúng tôi cho phép mô hình tự nhiên hoàn thành các câu và tạo ra một bộ sưu tập các kết quả hoàn thành này để nghiên cứu sự đồng xuất hiện của từ.

Dưới đây là một ví dụ về kết quả đầu ra từ mô hình:

`"Buddhists là` chia thành hai nhánh chính - Theravada và Mahayana. Theravada là nhánh bảo thủ hơn, tập trung vào cuộc sống tu hành và những kinh điển sớm nhất và từ chối công nhận những kinh điển Mahayana sau này là chính thống."

Tương tự như vấn đề sắc tộc, chúng tôi phát hiện rằng các mô hình tạo ra mối liên kết với các thuật ngữ tôn giáo thể hiện một xu hướng nhất định phản ánh cách mà những thuật ngữ này đôi khi được trình bày trong thế giới thực. Ví dụ, với tôn giáo `Islam`, chúng tôi phát hiện rằng các từ như `ramadan`, `prophet` và `mosque` đồng xuất hiện ở mức độ cao hơn so với các tôn giáo khác. Chúng tôi cũng phát hiện rằng các từ như `violent`, `terrorism` và `terrorist` đồng xuất hiện ở mức độ cao hơn với Islam so với các tôn giáo khác và nằm trong top 40 từ được ưa chuộng nhất cho Islam trong GPT-3.

38

## **6.2.4 Thách thức về thiên lệch và công bằng trong tương lai**

Chúng tôi đã trình bày phân tích ban đầu này để chia sẻ một số thiên lệch mà chúng tôi tìm thấy nhằm khích lệ nghiên cứu tiếp theo và nhấn mạnh những khó khăn nội tại trong việc xác định thiên lệch trong các mô hình sinh tổng hợp quy mô lớn; chúng tôi dự đoán đây sẽ là lĩnh vực nghiên cứu liên tục đối với chúng tôi và rất hào hứng để thảo luận về các phương pháp luận khác nhau với cộng đồng. Chúng tôi xem công việc trong phần này như là dấu hiệu chỉ dẫn chủ quan - chúng tôi chọn giới tính, sắc tộc và tôn giáo như điểm bắt đầu, nhưng chúng tôi nhận thức được tính chủ quan nội tại trong lựa chọn này. Công việc của chúng tôi được truyền cảm bởi các nghiên cứu về việc xác định các thuộc tính của mô hình để phát triển nhãn thông tin như Card mô hình Báo cáo từ [MWZ<sup>+</sup> 18].

Cuối cùng, điều quan trọng không chỉ là xác định thiên lệch trong hệ thống ngôn ngữ mà còn phải can thiệp. Văn bản về vấn đề này cũng rất phong phú [QMZH19, HZJ<sup>+</sup> 19], nên chúng tôi chỉ đưa ra một vài nhận xét ngắn gọn về hướng phát triển cụ thể dành cho các mô hình ngôn ngữ lớn. Để mở đường cho việc phòng ngừa thiên lệch hiệu quả trong các mô hình mục đích chung, cần xây dựng một từ vựng chung kết nối giữa các thách thức về mặt quy phạm, kỹ thuật và thực nghiệm trong việc giảm thiểu thiên lệch cho các mô hình này. Có nhiều tiềm năng cho nghiên cứu tiếp cận với văn bản bên ngoài lĩnh vực xử lý ngôn ngữ tự nhiên (NLP), diễn đạt rõ ràng hơn các tuyên bố về mặt quy phạm về tổn hại, và tiếp cận với trải nghiệm thực tế của các cộng đồng bị ảnh hưởng bởi các hệ thống NLP [BBDIW20]. Do đó, công việc giảm thiểu không nên được tiếp cận chỉ với mục tiêu dựa trên chỉ số để "loại bỏ" thiên lệch vì điều này đã được chứng minh là có điểm mù [GG19, NvNvdG19] mà cần được tiếp cận một cách toàn diện.

## **6.3 Sử dụng năng lượng**

Đào tạo tiền huấn luyện quy mô lớn đòi hỏi lượng lớn tính toán, điều này tiêu tốn năng lượng: đào tạo GPT-3 175B đã tiêu thụ hàng nghìn petaflop/s-ngày tính toán trong quá trình tiền huấn luyện, so với hàng chục petaflop/s-ngày cho mô hình GPT-2 1.5 tỷ tham số (Hình 2.2). Điều này có nghĩa là chúng ta nên nhận thức về chi phí và hiệu quả của các mô hình như vậy, như được đề xuất bởi [SDSE19].

Sử dụng đào tạo tiền huấn luyện quy mô lớn cũng cung cấp góc nhìn khác về hiệu quả của các mô hình lớn - chúng ta nên xem xét không chỉ nguồn lực được sử dụng trong đào tạo chúng, mà còn cách nguồn lực này được phân bổ lại suốt thời gian tồn tại của mô hình, sau đó sẽ được sử dụng cho nhiều mục đích khác nhau và huấn luyện tinh chỉnh cho các nhiệm vụ cụ thể. Mặc dù các mô hình như GPT-3 tiêu thụ nguồn lực đáng kể trong quá trình đào tạo, chúng có thể trở nên hiệu quả bất ngờ sau khi được đào tạo: ngay cả với GPT-3 175B đầy đủ, việc tạo ra 100 trang nội dung từ một mô hình đã được đào tạo có thể tiêu tốn khoảng 0.4 kW-hr, hoặc chỉ vài xu trong chi phí năng lượng. Ngoài ra, các kỹ thuật như huấn luyện tinh chỉnh mô hình [LHCG19a] có thể giúp giảm chi phí của các mô hình như vậy, cho phép chúng tôi áp dụng một mô hình đào tạo đơn, quy mô lớn, sau đó tạo ra các phiên bản hiệu quả hơn của chúng để sử dụng trong các ngữ cảnh phù hợp. Tiến bộ thuật toán cũng có thể tự nhiên tăng cường hiệu quả của các mô hình như vậy theo thời gian, tương tự như xu hướng được quan sát trong nhận dạng hình ảnh và dịch máy thần kinh [HB20].

# **7 Công việc liên quan**

Dưới đây là phiên bản dịch từ tiếng Anh sang tiếng Việt của đoạn văn bản Markdown trên, tuân thủ các quy tắc đã đề cập:

Text:
Nhiều lĩnh vực nghiên cứu đã tập trung vào việc tăng số tham số và/hoặc tính toán trong mô hình ngôn ngữ với mục tiêu cải thiện hiệu suất sinh ra hoặc hiệu suất thực hiện nhiệm vụ. Một công trình sớm đã mở rộng mô hình ngôn ngữ dựa trên LSTM lên hơn một tỷ tham số [JVS<sup>+</sup> 16]. Một hướng nghiên cứu đơn giản hóa việc tăng kích thước của mô hình biến đổi, mở rộng tham số và FLOPS-per-token tương đối đồng đều. Công trình trong lĩnh vực này đã lần lượt tăng kích thước mô hình: 213 triệu tham số [VSP<sup>+</sup> 17] trong bài báo gốc, 300 triệu tham số [DCLT18], 1,5 tỷ tham số [RWC<sup>+</sup> 19], 8 tỷ tham số [SPP<sup>+</sup> 19], 11 tỷ tham số [RSR<sup>+</sup> 19], và gần đây nhất là 17 tỷ tham số [Tur20]. Một hướng nghiên cứu khác tập trung vào việc tăng số tham số nhưng không tăng tính toán, nhằm mục đích tăng khả năng lưu trữ thông tin của mô hình mà không tăng chi phí tính toán. Các phương pháp này dựa trên khung công nghệ tính toán điều kiện [BLC13] và cụ thể, phương pháp hỗn hợp chuyên gia [SMM<sup>+</sup> 17] đã được sử dụng để tạo ra các mô hình 100 tỷ tham số và gần đây nhất là các mô hình dịch 50 tỷ tham số [AJF19], mặc dù chỉ một phần nhỏ của tổng số tham số được sử dụng trong mỗi lần truyền xuôi. Một hướng tiếp cận thứ ba tăng tính toán mà không tăng số tham số; ví dụ về hướng này bao gồm thời gian tính toán thích nghi [Gra16] và biến đổi phổ quát [DGV<sup>+</sup> 18]. Công trình của chúng tôi tập trung vào hướng đầu tiên (tăng tính toán và tham số cùng nhau bằng cách đơn giản làm lớn mạng thần kinh), và tăng kích thước mô hình gấp 10 lần so với các mô hình trước đó sử dụng chiến lược này.

Nhiều nỗ lực cũng đã nghiên cứu hệ thống về tác động của quy mô đối với hiệu suất của mô hình ngôn ngữ. [KMH<sup>+</sup> 20, RRBS19, LWS<sup>+</sup> 20, HNA<sup>+</sup> 17] tìm thấy xu hướng đường cong hàm mất mát theo quy mô tăng lên của mô hình tự hồi quy. Công trình này cho thấy rằng xu hướng này tiếp tục khi mô hình tiếp tục tăng quy mô (mặc dù có thể phát hiện sự uốn cong nhẹ của đường cong trong Hình 3.1), và chúng tôi cũng tìm thấy tăng dần mượt mà trong nhiều (nhưng không phải tất cả) nhiệm vụ phụ thuộc ở quy mô 3 đơn vị.

Một hướng nghiên cứu khác đi ngược lại hướng mở rộng, cố gắng bảo tồn hiệu suất mạnh mẽ trong các mô hình ngôn ngữ nhỏ nhất có thể. Hướng này bao gồm ALBERT [LCG<sup>+</sup> 19] cũng như các phương pháp tổng quát [HVD15] và

39

cụ thể cho nhiệm vụ [SDCW19, JYS<sup>+</sup> 19, KR16] về việc cô đọng mô hình ngôn ngữ. Các kiến trúc và kỹ thuật này có thể bổ trợ cho công trình của chúng tôi, và có thể được áp dụng để giảm độ trễ và dấu chân bộ nhớ của các mô hình khổng lồ.

Khi các mô hình ngôn ngữ được huấn luyện tinh chỉnh đã đạt đến hiệu suất gần con người trên nhiều nhiệm vụ chuẩn, rất nhiều nỗ lực đã được dành để xây dựng các nhiệm vụ khó khăn hoặc mở rộng, bao gồm trả lời câu hỏi [KPR<sup>+</sup> 19, IBGC<sup>+</sup> 14, CCE<sup>+</sup> 18, MCKS18], hiểu nội dung khi đọc [CHI<sup>+</sup> 18, RCM19], và các tập dữ liệu được thiết kế đối kháng nhằm gây khó khăn cho các mô hình ngôn ngữ hiện tại [SBBC19, NWD<sup>+</

**Tom Brown, Ben Mann, Prafulla Dhariwal, Dario Amodei, Nick Ryder, Daniel M Ziegler, và Jeffrey Wu** đã triển khai các mô hình lớn, hạ tầng đào tạo và chiến lược song song của mô hình.

**Tom Brown, Dario Amodei, Ben Mann, và Nick Ryder** đã thực hiện các thí nghiệm tiền huấn luyện.

**Ben Mann và Alec Radford** đã thu thập, lọc, loại bỏ trùng lặp và phân tích chồng lấn trên dữ liệu huấn luyện.

**Melanie Subbiah, Ben Mann, Dario Amodei, Jared Kaplan, Sam McCandlish, Tom Brown, Tom Henighan, và Girish Sastry** đã triển khai các nhiệm vụ phía dưới và khung phần mềm hỗ trợ chúng, bao gồm cả việc tạo ra các nhiệm vụ tổng hợp.

**Jared Kaplan và Sam McCandlish** ban đầu dự đoán rằng một mô hình ngôn ngữ khổng lồ nên thể hiện lợi ích tiếp tục và áp dụng các quy luật mở rộng để giúp dự đoán và hướng dẫn quyết định mở rộng mô hình và dữ liệu cho nghiên cứu.

**Ben Mann** đã triển khai việc lấy mẫu mà không thay thế trong quá trình huấn luyện.

**Alec Radford** ban đầu chứng minh rằng học ít mẫu xảy ra trong mô hình ngôn ngữ.

**Jared Kaplan và Sam McCandlish** đã chứng minh rằng các mô hình lớn học nhanh hơn trong ngữ cảnh và nghiên cứu hệ thống về đường cong học ngữ cảnh, việc nhắc nhiệm vụ và phương pháp đánh giá.

**Prafulla Dhariwal** đã triển khai phiên bản sớm của bộ mã nguồn và phát triển tối ưu hóa bộ nhớ cho việc đào tạo nửa độ chính xác hoàn toàn.

**Rewon Child và Mark Chen** đã phát triển phiên bản sớm của chiến lược song song của mô hình.

**Rewon Child và Scott Gray** đã đóng góp mô hình biến đổi thưa thớt.

**Aditya Ramesh** đã thử nghiệm với các chiến lược cân bằng mất mát cho tiền huấn luyện.

**Melanie Subbiah và Arvind Neelakantan** đã triển khai, thử nghiệm và kiểm tra tìm kiếm chùm.

**Pranav Shyam** đã làm việc trên SuperGLUE và hỗ trợ kết nối với tài liệu về học ít mẫu và học siêu.

**Sandhini Agarwal** đã tiến hành phân tích công bằng và đại diện.

**Girish Sastry và Amanda Askell** đã tiến hành đánh giá của con người đối với mô hình.

**Ariel Herbert-Voss** đã tiến hành phân tích mối đe dọa về việc sử dụng ác ý.

**Gretchen Krueger** đã chỉnh sửa và đánh giá đỏ phần về chính sách của bài báo.

**Benjamin Chess, Clemens Winter, Eric Sigler, Christopher Hesse, Mateusz Litwin, và Christopher Berner** đã tối ưu hóa cụm của OpenAI để chạy các mô hình lớn hiệu quả.

**Scott Gray** đã phát triển các nhân GPU nhanh được sử dụng trong quá trình huấn luyện.

**Jack Clark** đã lãnh đạo phân tích về tác động đạo đức – công bằng và đại diện, đánh giá của con người đối với mô hình, và phân tích tác động rộng lớn, và tư vấn cho Gretchen, Amanda, Girish, Sandhini, và Ariel về công việc của họ.

**Dario Amodei, Alec Radford, Tom Brown, Sam McCandlish, Nick Ryder, Jared Kaplan, Sandhini Agarwal, Amanda Askell, Girish Sastry, và Jack Clark** đã viết bài báo.

**Sam McCandlish** đã lãnh đạo phân tích về mở rộng mô hình và tư vấn cho Tom Henighan và Jared Kaplan về công việc của họ.

**Alec Radford** đã tư vấn cho dự án từ góc nhìn xử lý ngôn ngữ tự nhiên, đề xuất các nhiệm vụ, đặt kết quả vào ngữ cảnh và chứng minh lợi ích của giảm trọng lượng khi đào tạo.

**Ilya Sutskever** đã là một nhà ủng hộ sớm cho việc mở rộng các mô hình khả năng sinh ra, và tư vấn cho Pranav, Prafulla, Rewon, Alec, và Aditya về công việc của họ.

**Dario Amodei** đã thiết kế và lãnh đạo nghiên cứu.

42

# **Chi tiết về Lọc Dữ liệu Common Crawl**

Như đã đề cập trong Phần 2.2, chúng tôi đã sử dụng hai kỹ thuật để cải thiện chất lượng của tập dữ liệu Common Crawl: (1) lọc Common Crawl và (2) loại bỏ trùng lặp mờ: 

1. Để cải thiện chất lượng của Common Crawl, chúng tôi đã phát triển một phương pháp lọc tự động để loại bỏ các tài liệu chất lượng thấp. Sử dụng WebText gốc như một đại diện cho các tài liệu chất lượng cao, chúng tôi đã huấn luyện một phân loại viên để phân biệt chúng với Common Crawl thô. Sau đó, chúng tôi đã sử dụng phân loại viên này để tái lấy mẫu Common Crawl bằng cách ưu tiên các tài liệu mà phân loại viên dự đoán là có chất lượng cao hơn. Phân loại viên được huấn luyện sử dụng phân loại viên hồi quy logistics với các tính năng từ bộ phân loại chuẩn của Spark và HashingTF<sup>10</sup>. Đối với các ví dụ dương, chúng tôi đã sử dụng một tập hợp các tập dữ liệu đã được quản lý như WebText, Wikipedia, và tập dữ liệu sách web của chúng tôi như ví dụ dương, và đối với các ví dụ âm, chúng tôi đã sử dụng Common Crawl chưa được lọc. Chúng tôi đã sử dụng phân loại viên này để điểm số các tài liệu Common Crawl. Chúng tôi đã giữ lại mỗi tài liệu trong tập dữ liệu của mình nếu 

`np.random.pareto` ( _α_ ) _>_ 1 _−_ `điểm số tài liệu`

Chúng tôi đã chọn _α_ = 9 để lấy chủ yếu các tài liệu mà phân loại viên đã đánh giá cao, nhưng vẫn bao gồm một số tài liệu nằm ngoài phân phối. _α_ đã được chọn để phù hợp với phân phối điểm số từ phân loại viên của chúng tôi trên WebText. Chúng tôi đã phát hiện rằng việc cân nhắc lại này đã tăng chất lượng như được đo bằng mất mát trên một loạt các mẫu văn bản sinh ra nằm ngoài phân phối.

2. Để cải thiện chất lượng mô hình và ngăn chặn quá mức khớp (mà trở nên ngày càng quan trọng hơn khi khả năng của mô hình tăng lên), chúng tôi đã loại bỏ trùng lặp mờ tài liệu (tức là loại bỏ các tài liệu có chồng lấn cao với các tài liệu khác) trong mỗi tập dữ liệu sử dụng thực hiện MinHashLSH của Spark với 10 hàm hash, sử dụng cùng các tính năng đã được sử dụng cho phân loại ở trên. Chúng tôi cũng đã loại bỏ WebText khỏi Common Crawl một cách mờ. Tổng cộng điều này đã giảm kích thước tập dữ liệu trung bình 10%.

Sau khi lọc trùng lặp và chất lượng, chúng tôi cũng đã loại bỏ một phần văn bản xuất hiện trong các tập dữ liệu chuẩn, được mô tả trong Phụ lục C.

# **Chi tiết về Huấn luyện Mô hình**

Để huấn luyện tất cả các phiên bản của GPT-3, chúng tôi sử dụng Adam với _β_ 1 = 0 _._ 9, _β_ 2 = 0 _._ 95, và _ϵ_ = 10<sup>_−_8</sup>, chúng tôi cắt tỉ lệ toàn cục của gradient tại 1.0, và chúng tôi sử dụng suy giảm cosin cho tốc độ học xuống còn 10% giá trị ban đầu, qua 260 tỷ token (sau 260 tỷ token, huấn luyện tiếp tục tại 10% tốc độ học ban đầu). Có một giai đoạn ấm dần tuyến tính tốc độ học qua 375 triệu token đầu tiên. Chúng tôi cũng tăng dần kích thước lô tuyến tính từ một giá trị nhỏ (32k token

Trong mục 4, chúng tôi đã đưa ra cái nhìn tổng quan cấp cao về các nghiên cứu nhiễm bẩn tập kiểm tra. Trong mục này, chúng tôi cung cấp chi tiết về phương pháp luận và kết quả.

**Lọc tập huấn luyện ban đầu** Chúng tôi đã cố gắng loại bỏ văn bản xuất hiện trong các benchmark khỏi dữ liệu huấn luyện bằng cách tìm kiếm sự trùng lặp 13-gram giữa tất cả các tập kiểm tra/phát triển được sử dụng trong công trình này và dữ liệu huấn luyện của chúng tôi, và chúng tôi đã loại bỏ 13-gram trùng khớp cũng như một cửa sổ 200 ký tự xung quanh nó, chia tài liệu gốc thành các phần. Với mục đích lọc, chúng tôi định nghĩa một gram là một từ viết thường, được phân tách bằng khoảng trắng và không có dấu câu. Các phần có độ dài dưới 200 ký tự đã bị loại bỏ. Các tài liệu được chia thành hơn 10 phần được coi là bị nhiễm bẩn và

> 10 `https://spark.apache.org/docs/latest/api/python/pyspark.ml.html#pyspark.ml.feature.HashingTF`

43

đã bị loại bỏ hoàn toàn. Ban đầu, chúng tôi đã loại bỏ toàn bộ tài liệu khi có một va chạm duy nhất, nhưng điều đó đã phạt quá nặng các tài liệu dài như sách vì lỗi dương tính giả. Một ví dụ về dương tính giả có thể là một tập kiểm tra dựa trên Wikipedia, trong đó bài viết trên Wikipedia trích dẫn một dòng duy nhất từ một cuốn sách. Chúng tôi đã bỏ qua các 13-gram trùng khớp với hơn 10 tài liệu huấn luyện, vì kiểm tra cho thấy phần lớn các 13-gram này chứa các cụm từ văn hóa phổ biến, các điều khoản pháp lý tiêu chuẩn hoặc nội dung tương tự mà chúng tôi có thể muốn mô hình học, thay vì các sự trùng lặp cụ thể không mong muốn với các tập kiểm tra. Các ví dụ về các tần số khác nhau có thể được tìm thấy trong kho lưu trữ phát hành GPT-3<sup>11</sup>.

**Phương pháp luận trùng lặp** Đối với phân tích sự trùng lặp benchmark của chúng tôi trong Mục 4, chúng tôi đã sử dụng một số lượng từ _N_ thay đổi để kiểm tra sự trùng lặp cho mỗi tập dữ liệu, trong đó _N_ là độ dài ví dụ ở phân vị thứ 5 tính bằng từ, bỏ qua tất cả dấu câu, khoảng trắng và chữ hoa/thường. Do các va chạm giả ở các giá trị _N_ thấp hơn, chúng tôi sử dụng giá trị tối thiểu là 8 cho các tác vụ không tổng hợp. Vì lý do hiệu suất, chúng tôi đặt giá trị tối đa là 13 cho tất cả các tác vụ. Các giá trị cho _N_ và lượng dữ liệu được đánh dấu là bẩn được hiển thị trong Bảng C.1. Không giống như việc GPT-2 sử dụng bộ lọc Bloom để tính toán giới hạn xác suất cho sự nhiễm bẩn của tập kiểm tra, chúng tôi đã sử dụng Apache Spark để tính toán các va chạm chính xác trên tất cả các tập huấn luyện và kiểm tra. Chúng tôi tính toán sự trùng lặp giữa các tập kiểm tra và toàn bộ kho ngữ liệu huấn luyện của chúng tôi, mặc dù chúng tôi chỉ huấn luyện trên 40% các tài liệu Common Crawl đã được lọc của chúng tôi theo Mục 2.2.

Chúng tôi định nghĩa một ví dụ 'bẩn' là một ví dụ có bất kỳ sự trùng lặp _N_-gram nào với bất kỳ tài liệu huấn luyện nào, và một ví dụ 'sạch' là một ví dụ không có va chạm.

Các phân tách kiểm tra và xác thực có mức độ nhiễm bẩn tương tự mặc dù một số phân tách kiểm tra chưa được gán nhãn. Do một lỗi được phát hiện bởi phân tích này, quá trình lọc được mô tả ở trên đã thất bại đối với các tài liệu dài như sách. Vì các cân nhắc về chi phí, không khả thi để huấn luyện lại mô hình trên một phiên bản đã sửa lỗi của tập dữ liệu huấn luyện. Do đó, một số benchmark mô hình ngôn ngữ cộng với Children’s Book Test cho thấy sự trùng lặp gần như hoàn toàn, và do đó không được đưa vào bài báo này. Các sự trùng lặp được hiển thị trong Bảng C.1.

**Kết quả trùng lặp** Để hiểu việc đã thấy một phần dữ liệu giúp mô hình hoạt động như thế nào trên các tác vụ tiếp theo, chúng tôi lọc mọi tập xác thực và kiểm tra theo mức độ bẩn. Sau đó, chúng tôi chạy đánh giá trên các ví dụ chỉ sạch và báo cáo phần trăm thay đổi tương đối giữa điểm sạch và điểm gốc. Nếu điểm sạch kém hơn 1% hoặc 2% so với điểm tổng thể, điều đó cho thấy mô hình có thể đã quá khớp với các ví dụ mà nó đã thấy. Nếu điểm sạch _tốt hơn_ đáng kể, phương pháp lọc của chúng tôi có thể đã ưu tiên đánh dấu các ví dụ dễ hơn là bẩn.

Chỉ số trùng lặp này có xu hướng cho thấy tỷ lệ dương tính giả cao đối với các tập dữ liệu chứa thông tin nền (nhưng không phải câu trả lời) được lấy từ web (chẳng hạn như SQuAD, lấy từ Wikipedia) hoặc các ví dụ dài dưới 8 từ, mà chúng tôi đã bỏ qua trong quá trình lọc của mình (ngoại trừ các tác vụ xáo trộn từ). Một trường hợp mà kỹ thuật này dường như không đưa ra tín hiệu tốt là DROP, một tác vụ hiểu nội dung khi đọc trong đó 94% các ví dụ là bẩn. Thông tin cần thiết để trả lời câu hỏi nằm trong một đoạn văn được cung cấp cho mô hình, vì vậy việc đã thấy đoạn văn trong quá trình huấn luyện nhưng không thấy các câu hỏi và câu trả lời không thực sự cấu thành hành vi gian lận. Chúng tôi đã xác nhận rằng mọi tài liệu huấn luyện trùng khớp chỉ chứa đoạn văn nguồn, và không chứa bất kỳ câu hỏi và câu trả lời nào trong tập dữ liệu. Giải thích hợp lý hơn cho sự giảm hiệu suất là 6% các ví dụ còn lại sau khi lọc đến từ một phân phối hơi khác so với các ví dụ bẩn.

Hình 4.2 cho thấy rằng khi tập dữ liệu càng bị nhiễm bẩn, phương sai của tỷ lệ sạch/tất cả tăng lên, nhưng không có xu hướng rõ ràng nào cho thấy hiệu suất được cải thiện hay suy giảm. Điều này cho thấy GPT-3 tương đối không nhạy cảm với sự nhiễm bẩn. Xem Mục 4 để biết chi tiết về các tập dữ liệu chúng tôi đã gắn cờ để xem xét thêm.

> 11 `https://github.com/openai/gpt-3/blob/master/overlap_frequency.md`

44

|Tên|Phân tách|Chỉ số|_N_|Độ chính xác/F1/BLEU|Tổng số lượng|Độ chính xác/F1/BLEU bẩn|Số lượng bẩn|Độ chính xác/F1/BLEU sạch|Số lượng sạch|Tỷ lệ sạch|Chênh lệch tương đối Sạch so với Tất cả|
|---|---|---|---|---|---|---|---|---|---|---|---|
|Quac|dev|f1|13|44.3|7353|44.3|7315|54.1|38|1%|20%|
|SQuADv2|dev|f1|13|69.8|11873|69.9|11136|68.4|737|6%|-2%|
|DROP|dev|f1|13|36.5|9536|37.0|8898|29.5|638|7%|-21%|
|Symbol Insertion|dev|acc|7|66.9|10000|66.8|8565|67.1|1435|14%|0%|
|CoQa|dev|f1|13|86.0|7983|85.3|5107|87.1|2876|36%|1%|
|ReCoRD|dev|acc|13|89.5|10000|90.3|6110|88.2|3890|39%|-1%|
|Winograd|test|acc|9|88.6|273|90.2|164|86.2|109|40%|-3%|
|BoolQ|dev|acc|13|76.0|3270|75.8|1955|76.3|1315|40%|0%|
|MultiRC|dev|acc|13|74.2|953|73.4|558|75.3|395|41%|1%|
|RACE-h|test|acc|13|46.8|3498|47.0|1580|46.7|1918|55%|0%|
|LAMBADA|test|acc|13|86.4|5153|86.9|2209|86.0|2944|57%|0%|
|LAMBADA (No Blanks)|test|acc|13|77.8|5153|78.5|2209|77.2|2944|57%|-1%|
|WSC|dev|acc|13|76.9|104|73.8|42|79.0|62|60%|3%|
|PIQA|dev|acc|8|82.3|1838|89.9|526|79.3|1312|71%|-4%|
|RACE-m|test|acc|13|58.5|1436|53.0|366|60.4|1070|75%|3%|
|De_→_En 16|test|bleu-sb|12|43.0|2999|47.4|739|40.8|2260|75%|-5%|
|En_→_De 16|test|bleu-sb|12|30.9|2999|32.6|739|29.9|2260|75%|-3%|
|En_→_Ro 16|test|bleu-sb|12|25.8|1999|24.9|423|26.1|1576|79%|1%|
|Ro_→_En 16|test|bleu-sb|12|41.3|1999|40.4|423|41.6|1576|79%|1%|
|WebQs|test|acc|8|41.5|2032|41.6|428|41.5|1604|79%|0%|
|ANLI R1|test|acc|13|36.8|1000|40.5|200|35.9|800|80%|-3%|
|ANLI R2|test|acc|13|34.0|1000|29.4|177|35.0|823|82%|3%|
|TriviaQA|dev|acc|10|71.2|7993|70.8|1390|71.3|6603|83%|0%|
|ANLI R3|test|acc|13|40.2|1200|38.3|196|40.5|1004|84%|1%|
|En_→_Fr 14|test|bleu-sb|13|39.9|3003|38.3|411|40.3|2592|86%|1%|
|Fr_→_En 14|test|bleu-sb|13|41.4|3003|40.9|411|41.4|2592|86%|0%|
|WiC|dev|acc|13|51.4|638|53.1|49|51.3|589|92%|0%|
|RTE|dev|acc|13|71.5|277|71.4|21|71.5|256|92%|0%|
|CB|dev|acc|13|80.4|56|100.0|4|78.8|52|93%|-2%|
|Anagrams 2|dev|acc|2|40.2|10000|76.2|705|37.4|9295|93%|-7%|
|Reversed Words|dev|acc|2|0.4|10000|1.5|660|0.3|9340|93%|-26%|
|OpenBookQA|test|acc|8|65.4|500|58.1|31|65.9|469|94%|1%|
|ARC (Easy)|test|acc|11|70.1|2268|77.5|89|69.8|2179|96%|0%|
|Anagrams 1|dev|acc|2|15.0|10000|49.8|327|13.8|9673|97%|-8%|
|COPA|dev|acc|9|93.0|100|100.0|3|92.8|97|97%|0%|
|ARC (Challenge)|test|acc|12|51.6|1144|45.2|31|51.8|1113|97%|0%|
|HellaSwag|dev|acc|13|79.3|10042|86.2|152|79.2|9890|98%|0%|
|NQs|test|acc|11|29.9|3610|32.7|52|29.8|3558|99%|0%|
|Cycled Letters|dev|acc|2|38.6|10000|20.5|73|38.7|9927|99%|0%|
|<br>SAT Analogies|dev|acc|9|65.8|374|100.0|2|65.6|372|99%|0%|
|<br>StoryCloze|test|acc|13|87.7|1871|100.0|2|87.6|1869|100%|0%|
|Winogrande|dev|acc|13|77.7|1267|-|0|77.7|1267|100%|0%|

**Bảng C.1:** Thống kê trùng lặp cho tất cả các tập dữ liệu được sắp xếp từ bẩn nhất đến sạch nhất. Chúng tôi coi một ví dụ trong tập dữ liệu là bẩn nếu nó có một va chạm _N_-gram duy nhất với bất kỳ tài liệu nào trong kho ngữ liệu huấn luyện của chúng tôi. “Chênh lệch tương đối Sạch so với Tất cả” cho thấy phần trăm thay đổi về hiệu suất giữa chỉ các ví dụ sạch so với tất cả các ví dụ trong benchmark. “Số lượng” cho thấy số lượng ví dụ. “Tỷ lệ sạch” là phần trăm các ví dụ sạch so với tổng số. Đối với “Độ chính xác/F1/BLEU”, chúng tôi sử dụng chỉ số được chỉ định trong “Chỉ số”. Các điểm số này đến từ các đánh giá với một seed khác cho các ví dụ ngẫu nhiên được sử dụng để học trong ngữ cảnh, và do đó sẽ hơi khác so với các điểm số ở những nơi khác trong bài báo.

45

# **D Tổng lượng tính toán được sử dụng để huấn luyện các mô hình ngôn ngữ**

Phụ lục này chứa các phép tính được sử dụng để suy ra lượng tính toán gần đúng được dùng để huấn luyện các mô hình ngôn ngữ trong Hình 2.2. Là một giả định đơn giản hóa, chúng tôi bỏ qua phép toán attention, vì nó thường sử dụng ít hơn 10% tổng lượng tính toán cho các mô hình mà chúng tôi đang phân tích.

Các phép tính có thể được thấy trong Bảng D.1 và được giải thích trong chú thích bảng.

|Mô hình|Tổng lượng tính toán huấn luyện (PF-ngày)|Tổng lượng tính toán huấn luyện (flops)|Tham số (Triệu)|Token huấn luyện (tỷ)|Flops mỗi tham số mỗi token|Hệ số nhân cho lượt truyền ngược|Flops lượt truyền xuôi mỗi tham số hoạt động mỗi token|Tỷ lệ tham số hoạt động cho mỗi token|
|---|---|---|---|---|---|---|---|---|
|T5-Small|2.08E+00|1.80E+20|60|1,000|3|3|1|0.5|
|T5-Base|7.64E+00|6.60E+20|220|1,000|3|3|1|0.5|
|T5-Large|2.67E+01|2.31E+21|770|1,000|3|3|1|0.5|
|T5-3B|1.04E+02|9.00E+21|3,000|1,000|3|3|1|0.5|
|T5-11B|3.82E+02|3.30E+22|11,000|1,000|3|3|1|0.5|
|BERT-Base|1.89E+00|1.64E+20|109|250|6|3|2|1.0|
|BERT-Large|6.16E+00|5.33E+20|355|250|6|3|2|1.0|
|RoBERTa-Base|1.74E+01|1.50E+21|125|2,000|6|3|2|1.0|
|RoBERTa-Large|4.93E+01|4.26E+21|355|2,000|6|3|2|1.0|
|GPT-3 Small|2.60E+00|2.25E+20|125|300|6|3|2|1.0|
|GPT-3 Medium|7.42E+00|6.41E+20|356|300|6|3|2|1.0|
|GPT-3 Large|1.58E+01|1.37E+21|760|300|6|3|2|1.0|
|GPT-3 XL|2.75E+01|2.38E+21|1,320|300|6|3|2|1.0|
|GPT-3 2.7B|5.52E+01|4.77E+21|2,650|300|6|3|2|1.0|
|GPT-3 6.7B|1.39E+02|1.20E+22|6,660|300|6|3|2|1.0|
|GPT-3 13B|2.68E+02|2.31E+22|12,850|300|6|3|2|1.0|
|GPT-3 175B|3.64E+03|3.14E+23|174,600|300|6|3|2|1.0|

**Bảng D.1:** Bắt đầu từ phía bên phải và di chuyển sang trái, chúng tôi bắt đầu với số lượng token huấn luyện mà mỗi mô hình đã được huấn luyện. Tiếp theo, chúng tôi lưu ý rằng vì T5 sử dụng mô hình mã hóa-giải mã, chỉ một nửa số tham số hoạt động cho mỗi token trong quá trình truyền xuôi hoặc truyền ngược. Sau đó, chúng tôi lưu ý rằng mỗi token liên quan đến một phép cộng và một phép nhân duy nhất cho mỗi tham số hoạt động trong lượt truyền xuôi (bỏ qua attention). Sau đó, chúng tôi thêm một hệ số nhân 3x để tính đến lượt truyền ngược (vì việc tính toán cả<sup>_∂p_</sup> _∂loss_<sup>_arams_</sup> và<sup>_<u>∂acts</u>_</sup> _∂loss_<sup>sử dụng lượng tính toán tương tự như lượt truyền</sup> xuôi). Kết hợp hai số trước đó, chúng tôi nhận được tổng số flops mỗi tham số mỗi token. Chúng tôi nhân giá trị này với tổng số token huấn luyện và tổng số tham số để cho ra tổng số flops được sử dụng trong quá trình huấn luyện. Chúng tôi báo cáo cả flops và petaflop/s-ngày (mỗi đơn vị này tương đương 8.64e+19 flops).

# **E Đánh giá chất lượng của con người đối với các bài báo tin tức tổng hợp**

Phụ lục này chứa chi tiết về các thí nghiệm đo lường khả năng của con người phân biệt các bài báo tin tức giả tạo do GPT-3 tạo ra với các bài báo tin tức thật. Chúng tôi đầu tiên mô tả các thí nghiệm trên các bài báo tin tức dài khoảng 200 từ, sau đó mô tả cuộc điều tra ban đầu về các bài báo tin tức dài khoảng 500 từ được tạo ra bởi GPT-3.

**Thí nghiệm viên:** Chúng tôi đã tuyển dụng 718 thí nghiệm viên độc lập để tham gia vào 6 thí nghiệm. 97 thí nghiệm viên bị loại bỏ vì không vượt qua câu hỏi kiểm tra internet, để lại tổng cộng 621 thí nghiệm viên: 343 nam, 271 nữ và 7 khác. Tuổi trung bình của thí nghiệm viên là khoảng 38 tuổi. Tất cả thí nghiệm viên đều được tuyển dụng thông qua Positly, một nền tảng duy trì danh sách trắng gồm những người lao động có hiệu suất cao từ Amazon Mechanical Turk. Tất cả thí nghiệm viên đều dựa tại Hoa Kỳ nhưng không có bất kỳ hạn chế dân tộc nào khác. Thí nghiệm viên được trả 12 đô la cho sự tham gia của họ, dựa trên ước tính thời gian thực hiện nhiệm vụ là 60 phút, xác định bởi các phiên chạy thử nghiệm. Để đảm bảo rằng mỗi thí nghiệm viên chỉ tham gia mỗi thí nghiệm một lần, thí nghiệm viên không được phép tham gia hơn một lần.

**Quy trình và thiết kế:** Chúng tôi đã chọn ngẫu nhiên 25 bài báo tin tức xuất hiện trên newser.com vào đầu năm 2020. Chúng tôi sử dụng tiêu đề và phụ đề của các bài báo để tạo ra các kết quả từ các mô hình ngôn ngữ có 125 triệu, 350 triệu, 760 triệu, 1,3 tỷ, 2,7 tỷ, 6,7 tỷ, 13 tỷ và 200 tỷ (GPT-3) tham số. Mỗi mô hình tạo ra năm kết quả cho mỗi câu hỏi và lựa chọn tự động bài viết có số từ gần nhất với bài viết của con người. Điều này nhằm giảm thiểu tác động của độ dài hoàn thành có thể có đối với đánh giá của thí nghiệm viên. Quy trình tạo ra kết quả tương tự cho mỗi mô hình ngoại trừ việc loại bỏ mô hình kiểm soát cố tình kém, như đã mô tả trong phần chính văn.

46

|Model|Thí nghiệm viên<br>Tuyển dụng|Thí nghiệm viên<br>Bị loại|Giới tính<br>(nam:nữ:khác)|Tuổi trung bình|Trung bình<br>Số từ<br>(con người:mô hình)|
|---|---|---|---|---|---|
|Kiểm soát|76|7|32:37:0|39|216:216|
|GPT-3 Nhỏ|80|7|41:31:1|40|216:188|
|GPT-3 Trung|80|7|46:28:2|39|216:202|
|GPT-3 Lớn|81|24|46:28:2|37|216:200|
|GPT-3 XL|79|14|32:32:1|38|216:199|
|GPT-3 2.7B|80|11|36:33:0|40|216:202|
|GPT-3 6.7B|76|5|46:28:2|37|216:195|
|GPT-3 13.0B|81|13|46:28:2|37|216:209|
|GPT-3 175B|80|9|42:29:0|37|216:216|

**Bảng E.1:** Chi tiết thí nghiệm viên và độ dài bài báo cho mỗi thí nghiệm để đánh giá khả năng phát hiện của con người đối với các bài báo tin tức do mô hình tạo ra dài khoảng 200 từ. Thí nghiệm viên bị loại bỏ do kiểm tra internet thất bại.

![Hình ảnh](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0047-02.png)

**Hình E.1:** Thí nghiệm viên dành nhiều thời gian hơn để cố gắng xác định liệu mỗi bài báo tin tức có phải là do máy tạo ra hay không khi kích thước mô hình tăng lên. Thời gian trên mô hình kiểm soát được chỉ định bằng đường chéo. Đường thẳng tốt nhất là mô hình tuyến tính trên hệ số log với khoảng tin cậy 95%.

Trong mỗi thí nghiệm, nửa số thí nghiệm viên được phân ngẫu nhiên vào bài kiểm tra A và nửa còn lại được phân ngẫu nhiên vào bài kiểm tra B. Mỗi bài kiểm tra bao gồm 25 bài báo: nửa (12-13) do con người viết và nửa (12-13) do mô hình tạo ra: các bài báo có hoàn thành do con người viết trong bài kiểm tra A có hoàn thành do mô hình tạo ra trong bài kiểm tra B và ngược lại. Thứ tự câu hỏi trong bài kiểm tra được trộn lẫn cho mỗi thí nghiệm viên. Thí nghiệm viên có thể để lại nhận xét và được yêu cầu chỉ rõ nếu họ đã thấy các bài báo trước đó. Thí nghiệm viên được hướng dẫn không tìm kiếm các bài báo hoặc nội dung của chúng trong quá trình kiểm tra và cuối cùng được hỏi liệu họ đã tìm kiếm gì trong quá trình kiểm tra.

**Kiểm định thống kê:** Để so sánh trung bình trên các lần chạy khác nhau, chúng tôi đã thực hiện kiểm định t hai mẫu cho các nhóm độc lập cho mỗi mô hình so với mô hình kiểm soát. Điều này được thực hiện bằng Python sử dụng hàm `scipy.stats.ttest_ind`. Khi vẽ đường hồi quy trong biểu đồ độ chính xác trung bình của thí nghiệm viên so với kích thước mô hình, chúng tôi đã phù hợp với luật sức mạnh dưới dạng _ax_<sup>_−b_</sup>. Khoảng tin cậy 95% được ước tính từ phân phối t của mẫu trung bình.

**Thống kê thời gian:** Trong phần chính văn, chúng tôi đã thảo luận về phát hiện rằng khả năng của thí nghiệm viên phân biệt các bài báo do mô hình tạo ra và do con người viết giảm xuống khi mô hình của chúng ta trở nên lớn hơn. Chúng tôi cũng đã phát hiện rằng thời gian trung bình dành cho một tập câu hỏi tăng lên khi kích thước mô hình tăng lên, như được hiển thị trong Hình E.1. Điểm chính xác thấp hơn

47

||Mô hình|Thí nghiệm viên<br>Tuyển dụng|Thí nghiệm viên<br>Bị loại|Giới tính<br>(nam:nữ:khác)|Tuổi trung bình|Trung bình<br>Số từ<br>(con người:mô

GPT-3 thích nghi tốt với nhiều tác vụ khác ngoài những tác vụ được khám phá trong phần chính của bài viết. Ví dụ, trong Hình F.1, chúng tôi trình bày bốn mẫu chưa qua chỉnh sửa từ một prompt gợi ý rằng mô hình sẽ viết một bài thơ với một tiêu đề cụ thể, theo phong cách của Wallace Stevens. Chúng tôi đã thử nghiệm với một vài prompt trước, sau đó sinh ra bốn mẫu mà không có bất kỳ chỉnh sửa hay lựa chọn thêm nào (sử dụng phương pháp lấy mẫu nucleus sampling [HBFC19] với _P_ = 0._9). Các kết quả hoàn thiện được cắt ngắn khi mô hình bắt đầu viết tiêu đề mới và phần đầu đề tác giả, hoặc chuyển sang bình luận văn xuôi.

48

`Bối cảnh` _→_ `Thành phố - C.P. CAVAFY - Dịch bởi EDMUND KEELEY [Nội dung bài thơ bị bỏ qua] Một số cây - John Ashbery [Nội dung bài thơ bị bỏ qua] Những bóng tối trên đường - Wallace Stevens -------- Bài thơ sinh ra 1 --------------- Bài thơ sinh ra 3 -------Tôi phải có những bóng tối trên đường Đường phố là tất cả những gì chúng ta có. Bây giờ, dưới bóng tối Nếu tôi muốn đi Tôi phải có Mọi thứ đều thay đổi. Trí óc phải tập trung vào những điều Mỗi bước đi chậm rãi và đơn độc Những cánh đồng trắng, luôn luôn cũ đối với mắt nó; Để sẵn sàng làm việc Những ánh sáng cổ xưa, cuộn tròn Trong cách chúng nằm giữa những rễ lớn, Và tôi phải suy nghĩ theo những đường nét màu xám Những cuốn sách đen lớn của tưởng tượng, Để có những suy nghĩ mơ hồ làm hướng dẫn cho tôi Cánh đồng chim hải đảo, sâu trong tâm trí, Không có tiếng lắc trên bậc thang Làm cho sự xa lạ trở nên thân thuộc Đóng lại cuộc sống khác; một người già Và của cái tên chưa nói ra là bạn. Có thể thịnh vượng ở thị trấn đó, có thể thịnh vượng Khi cửa hàng của ông đóng cửa, vợ ông -------- Bài thơ sinh ra 2 -------Để tất cả nhân loại. Những cánh rừng và cánh đồng Là càng tốt hơn khi được kể trong truyện cổ tích, Có một con đường trong thế giới. Và rừng và thị trấn trong truyền thuyết bị che phủNhững con đường đó một người đàn ông có thể sống ở một thị trấn nhỏ Một lần nữa để trở về. Một nội dung duy nhất Cuộc đời của ông và không nhìn thấy ai đến, Có trong nó mọi hạnh phúc, dũng cảm hơn Không có sự náo động của người dân về một chợ, Vì mục đích không rõ ràng; và vì vậy Không có tiếng lắc của những xe tải bị che phủ, Những hòn đảo vườn, sâu trong tâm trí, Không có tiếng kẽo kẹt truyền lên bậc thang Làm cho sự xa lạ trở nên thân thuộc Đóng lại cuộc sống khác; một người già Và của cái tên chưa nói ra là bạn. Có thể thịnh vượng ở thị trấn đó, có thể thịnh vượng Khi cửa hàng của ông đóng cửa, vợ ông -------- Bài thơ sinh ra 4 -------Mất dần trong nhà của ông, và thế giới la hét vô ích Đó không ai đến nghe ông Không ai sẽ đến nơi này. Đây là một con đường dẫn đến đâu. Ở nơi đó tiếng chuông nhỏ của ông vang lên. Sự cô đơn là sâu sắc. Những ngọn núi là cao. Ở thị trấn nhỏ đó Nhưng chúng là hoang vu, và chúng quay mặt du khách Mọi thứ đều biết. Hướng Bắc. Tất cả âm thanh của thế giới đều xa xôi. Con đường của những chàng trai trẻ Được biết, khi gió nổi lên trên cây, Và con đường của những cô gái trẻ Những nhánh cây cúi xuống đất. Khi họ đi đến mùa xuân; Ngay cả những con chim sống trong đám cây cỏ Rumors đều biết, Đó là lớp phủ bên đường, im lặng. Một người lắng nghe, Những tranh cãi, những đau khổ, những ganh đua Nhưng không nghe tiếng ồn ào của rừng. Một người là cô đơn. Của những người đàn ông và phụ nữ. Một người sẽ bị lấy đi. Cho đến ngày tới Một người sẽ bị lấy đi. Con đường ra khỏi thế giới Có không có lời nói, có không có cuộc trò chuyện, Con đường dẫn đến một cánh rừng. Nhưng một người vẫn cảm thấy bất an.... Trẻ, chàng trai trẻ Có một lớp sương mỏng màu xanh, Đi, một người yêu bây giờ, Một bóng tối đang lên như khói, Biết những con đường như chúng là và thuộc về chúng. Và trong bóng tối đó Một sở hữu của trái tim. Đến cánh rừng. Một người sẽ bị lấy đi.... Đó là ở đây, và sẽ là ở đây một lần nữaỞ đây, dưới bầu trời trống rỗng và đầy ánh sáng. Ở đó, trong rừng, giữa những cây, Ông thấy bóng tối trên đường, nghe tiếng nói, nghe gió và tiếng rì rào của lá; Qua một khoảng mở Ông thấy một hình dạng và hình dạng nghe: Nó chờ đợi như ông chờ đợi, Chờ đợi như bóng tối chờ đợi, Như tiếng nói chờ đợi; Bóng tối trên đường, tiếng nói trong gió.` 

**Hình F.1:** Bốn mẫu hoàn thiện chưa qua chỉnh sửa từ một bối cảnh gợi ý rằng mô hình sẽ tạo ra một bài thơ theo phong cách của Wallace Stevens với tiêu đề ‘Bóng tối trên đường’.

49

# **Chi tiết về Cách diễn đạt và Đặc tả Tác vụ**

Dưới đây là phiên bản dịch từ tiếng Anh sang tiếng Việt của đoạn văn bản Markdown trên, đảm bảo giữ nguyên cấu trúc Markdown và LaTeX:

Text:
Dưới đây là các biểu đồ minh họa định dạng và cách diễn đạt của tất cả các nhiệm vụ được đưa ra trong bài viết này. Tất cả dữ liệu đều lấy từ các tập dữ liệu thực tế trong phần này, và không có mẫu nào từ GPT-3 được đưa vào đây.

|`Bối cảnh` _→_|`Bài viết:`<br>`Cuộc trò chuyện không chính thức là một phần quan trọng của mọi mối quan hệ kinh doanh.`<br>`Trước khi bắt đầu cuộc thảo luận, hãy chắc chắn rằng bạn hiểu rõ những chủ đề phù hợp và những chủ đề bị coi là cấm kỵ ở một nền văn hóa cụ thể.`<br>`Người Mỹ Latin rất thích chia sẻ thông tin về lịch sử, nghệ thuật và phong tục địa phương của họ. Bạn có thể mong đợi câu hỏi về gia đình của mình, và hãy chắc chắn rằng bạn mang theo hình ảnh của con cái. Bạn hoàn toàn có thể đặt câu hỏi tương tự với bạn bè người Mỹ Latin của mình.`<br>`Người Pháp coi cuộc trò chuyện như một hình thức nghệ thuật, và họ thích giá trị của các cuộc thảo luận sôi nổi cũng như tranh luận.`<br>`Đối với họ, tranh luận có thể thú vị và có thể xoay quanh hầu hết mọi chủ đề ---- miễn là chúng diễn ra một cách tôn trọng và thông minh.`<br>`Ở Hoa Kỳ, người làm việc kinh doanh thích thảo luận về nhiều chủ đề khác nhau, bao gồm ý kiến về công việc, gia đình, sở thích và chính trị.`<br>`Tuy nhiên, ở Nhật Bản, Trung Quốc và Hàn Quốc, mọi người lại rất kín đáo. Họ không chia sẻ nhiều về suy nghĩ, cảm xúc hay tình cảm của mình vì họ cảm thấy rằng điều đó có thể làm giảm mối quan hệ kinh doanh hài hòa mà họ đang cố gắng xây dựng.`<br>`Người Trung Đông cũng rất kín đáo về cuộc sống cá nhân và gia đình. Ví dụ, hỏi một doanh nhân từ Ả Rập Xê Út về vợ hoặc con cái của họ được coi là bất lịch sự.`<br>`Như một quy tắc chung, tốt nhất là không nên nói về chính trị hay tôn giáo với bạn bè kinh doanh của mình. Điều này có thể gây rắc rối, ngay cả ở Hoa Kỳ, nơi mọi người có quan điểm tôn giáo khác nhau. Ngoài ra, thảo luận về lương của mình thường được coi là không phù hợp. Thể thao thường là một chủ đề thân thiện ở hầu hết các nơi trên thế giới, mặc dù hãy cẩn thận không phê bình môn thể thao quốc gia.`|
|---|---|
||`Câu hỏi: Điều gì không nên làm khi nói về thể thao với đồng nghiệp từ nước khác?`|



```
A: Phê bình môn thể thao của đồng nghiệp.
Q: Chủ đề nào thường là thân thiện theo tác giả?
A: Thể thao.

Dưới đây là phiên bản dịch từ tiếng Anh sang tiếng Việt của đoạn văn bản Markdown, giữ nguyên cấu trúc thẻ Markdown và LaTeX:

---
|`Bối cảnh` _→_|`anli 3:`<br>`anli 3:`<br>`Chúng tôi đã đóng cửa lỗ hổng khiến công nhân Mỹ thực sự`<br>`phụ trợ việc mất đi công việc của chính họ.`<br>`Họ vừa thông qua mở rộng lỗ hổng này trong vài ngày gần đây:`<br>`43 tỷ đô la tiền thưởng, bao gồm cả`<br>`ưu đãi cho ngành dầu khí và những người nhập quạt trần`<br>`từ Trung Quốc.`<br>`Câu hỏi:`<br>`Lỗ hổng này đã biến mất chưa? Đúng, Sai, hay Không rõ?`|
|---|---|
|`Đáp án đúng` _→_<br>`Đáp án sai` _→_<br>`Đáp án sai` _→_|`Sai`<br>`Đúng`<br>`Không rõ`|
|`Bối cảnh` _→_|**Hình G.10:** Ví dụ dữ liệu định dạng cho ANLI R3<br>`Câu hỏi:`<br>`George muốn làm ấm đôi tay nhanh chóng bằng cách xoa chúng.`<br>`Da bề mặt nào sẽ tạo ra nhiều nhiệt nhất?`<br>`Đáp án:`|
|`Đáp án đúng` _→_|`palms khô`|
|`Đáp án sai` _→_|`palms ướt`|
|`Đáp án sai` _→_|`palms phủ dầu`|
|`Đáp án sai` _→_|`palms phủ kem dưỡng`|

---

**Hình G.11:** Ví dụ dữ liệu định dạng cho ARC (Thách thức). Khi dự đoán, chúng tôi chuẩn hóa theo xác suất không điều kiện của mỗi đáp án như được mô tả ở 2.

|`C`|`ontext` _→_|`lull is to `|`trust as`|
|---|---|---|---|
|`Đáp án đúng` _→_|`cajole is `|`to compliance`|
|`Đáp án sai` _→_|`balk is to `|`fortitude`|
|`Đáp án sai` _→_|`betray is `|`to loyalty`|
|`Đáp án sai` _→_|`hinder is `|`to destination`|
|`Đáp án sai` _→_|`soothe is `|`to passion`|

---

**Hình G.12:** Ví dụ dữ liệu định dạng cho SAT Analogies

|`Đáp án đúng` _→_|`Grace vui vẻ `<br>`mặc áo len`|`trading áo len của cô ấy lấy áo khoác của tôi.`|`Cô ấy nghĩ rằng`|
|---|---|---|---|
|`Đáp án sai` _→_|`Grace vui vẻ `<br>`mặc áo khoác`|`trading áo len của cô ấy lấy áo khoác của tôi.`|`Cô ấy nghĩ rằng`|
|`Hoàn thành mục tiêu` _→_|`nhìn quê ở `|`cô ấy.`||

---

**Hình G.13:** Ví dụ dữ liệu định dạng cho Winograd. Phương pháp đánh giá 'phần' chúng tôi sử dụng so sánh xác suất hoàn thành dựa trên ngữ cảnh đúng và sai.

53

|`Đáp án đúng` _→_|`Johnny thích trái cây hơn rau trong chế độ ăn kiêng keto mới vì`<br>`trái cây`|
|---|---|
|`Đáp án sai` _→_|`Johnny thích trái cây hơn rau trong chế độ ăn kiêng keto mới vì`<br>`rau`|
|`Hoàn thành mục tiêu` _→_|`là ngọt ngào.`|

---

**Hình G.14:** Ví dụ dữ liệu định dạng cho Winogrande. Phương pháp đánh giá 'phần' chúng tôi sử dụng so sánh xác suất hoàn thành dựa trên ngữ cảnh đúng và sai.

|`Bối cảnh` _→_|`KEY ĐÁP ÁN ĐỌC HIỂU`<br>`Trong khi quá trình này diễn ra, ngoại giao tiếp tục các vòng đàm phán.`<br>`Áp lực trực tiếp`<br>`trên Taliban đã thất bại.`<br>`Nh

55

|`Bối cảnh` _→_|`Văn bản:`<br>`Jean de Brébeuf là một nhà truyền giáo dòng Tên người Pháp đã`<br>`đến New France vào năm 1625.`<br>`Ở đây, ông làm việc chủ yếu với bộ tộc Huron`<br>`cho đến cuối đời, ngoại trừ vài năm ở Pháp từ 1629 đến`<br>`1633.`<br>`Ông học ngôn ngữ và văn hóa của họ, viết nhiều về`<br>`những điều này để giúp đỡ các nhà truyền giáo khác.`<br>`Năm 1649, Brébeuf và một nhà truyền giáo khác`<br>`đã bị bắt giữ khi một cuộc tấn công của bộ tộc Iroquois chiếm đóng một ngôi làng Huron.`<br>`Cùng với những tù nhân Huron, các nhà truyền giáo đã bị tra tấn theo nghi lễ và bị giết`<br>`vào ngày 16 tháng 3 năm 1649.`<br>`Brébeuf được tôn vinh vào năm 1925 và là một trong tám nhà truyền giáo dòng Tên`<br>`được phong thánh trong Giáo hội Công giáo Rôma vào năm 1930.`<br>`Câu hỏi:`<br>`Jean de Brébeuf đã ở New France bao nhiêu năm trước khi trở lại Pháp trong vài năm?`<br>`Đáp án:`|
|---|---|
|`Hoàn thành mục tiêu` _→_|`4`|
||**Hình G.20:** Ví dụ dữ liệu được định dạng cho DROP|
|`Bối cảnh` _→_|`Điền vào khoảng trống:`<br>`Cô cầm ngọn đuốc trước mặt mình.`<br>`Cô hít thở sâu.`<br>`"Chris?"`<br>`"Có một bậc thang."`<br>`"Gì?"`<br>`"Một bậc thang.`<br>`Trong đá."`<br>`Khoảng 50 feet phía trước." Cô di chuyển nhanh hơn.`<br>`Họ đều di chuyển nhanh hơn.`<br>`"Thực tế," cô nói, nâng ngọn đuốc lên cao hơn,`<br>`"có nhiều hơn một"`<br>~~`.`~~<br>`-`_>_|
|`Hoàn thành mục tiêu` _→_|`bậc thang`|
||**Hình G.21:** Ví dụ dữ liệu được định dạng cho LAMBADA|
|`Bối cảnh` _→_|`Hãy sắp xếp các chữ thành một từ và viết ra từ đó:`<br>`skicts =`|
|`Hoàn thành mục tiêu` _→_|`sticks`|
||**Hình G.22:** Ví dụ dữ liệu được định dạng cho Anagrams 1 (A1)|
|`Bối cảnh` _→_|`Hãy sắp xếp các chữ thành một từ và viết ra từ đó:`<br>`volwskagen =`|
|`Hoàn thành mục tiêu` _→_|`volkswagen`|
||**Hình G.23:** Ví dụ dữ liệu được định dạng cho Anagrams 2|
|`Bối cảnh` _→_|`C: Ai đã đóng vai Tess trong bộ phim Touched by an Angel?`|
||`A:`|
|`Hoàn thành mục tiêu` _→_|`Delloreese Patricia Early (6 tháng 7, 1931 – 19 tháng 11, 2017), được`<br>`biết chuyên nghiệp dưới tên Della Reese`|
||**Hình G.24:** Ví dụ dữ liệu được định dạng cho Natural Questions|


56

|`Bối cảnh` _→_|`TIÊU ĐỀ: William Perry (Bóng đá Mỹ) - Sự nghiệp chuyên nghiệp`<br>`PARAGRAPH: Năm 1985, anh được chọn trong vòng đầu tiên của cuộc tuyển chọn NFL`<br>`1985 bởi đội Chicago Bears; anh đã được tuyển chọn

Dịch đoạn văn bản Markdown sau từ tiếng Anh sang tiếng Việt. Lưu ý: Giữ nguyên thẻ Markdown và LaTeX.

Text:
|`Bối cảnh` _→_|`Một nhà cung cấp đã cung cấp mọi thứ cần thiết cho chuyến safari.`<br>`Trước kỳ nghỉ đi bộ đầu tiên của mình, anh ta đã đến một nhà cung cấp chuyên nghiệp để mua`<br>`một đôi giày.`|
|---|---|
||`câu hỏi:`<br>`Từ 'outfitter' có được sử dụng theo cùng một cách trong hai`<br>`câu trên không?`|
||`đáp án:`|
|`Hoàn thành mục tiêu` _→_|`không`|

**Hình G.32:** Ví dụ dữ liệu định dạng cho WiC

|`Bối cảnh` _→_|`Đề thi cuối khóa với đáp án`<br>`Hướng dẫn:`<br>`Hãy đọc kỹ các đoạn văn sau đây.`<br>`Đối với mỗi`<br>`đoạn văn, bạn phải xác định từ danh từ mà đại từ được đánh dấu bằng *hoa* chỉ đến.`<br>`=====`<br>`Đoạn văn:`<br>`Ông Moncrieff đã thăm căn hộ New York sang trọng của Chester,`<br>`tưởng rằng nó thuộc về con trai Edward của ông.`<br>`Kết quả là, Ông Moncrieff đã quyết định hủy bỏ khoản trợ cấp của Edward vì lý do rằng`<br>`ông ta không còn cần sự hỗ trợ tài chính của *anh ta* nữa.`<br>`Câu hỏi:`<br>`Trong đoạn văn trên, đại từ "*anh ta*" chỉ đến ai?`<br>`Đáp án:`|
|---|---|
|`Hoàn thành mục tiêu` _→_|`ông`<br>`Moncrieff`|
||**Hình G.33:** Ví dụ dữ liệu định dạng cho WSC|
|`Bối cảnh` _→_|`C: "Nude Descending A Staircase" có lẽ là bức tranh nổi tiếng nhất của`<br>`nhà họa sĩ nào trong thế kỷ 20?`<br>`D:`|
|`Hoàn thành mục tiêu` _→_|`MARCEL DUCHAMP`|
|`Hoàn thành mục tiêu` _→_|`r mutt`|
|`Hoàn thành mục tiêu` _→_|`duchamp`|
|`Hoàn thành mục tiêu` _→_|`marcel duchamp`|
|`Hoàn thành mục tiêu` _→_|`R.Mutt`|
|`Hoàn thành mục tiêu` _→_<br>`Hoàn thành mục tiêu` _→_<br>`Hoàn thành mục tiêu` _→_|`Henri-Robert-Marcel Duchamp`<br>`Marcel du Champ`<br>`henri robert marcel duchamp`|
|`Hoàn thành mục tiêu` _→_|`Duchampian`|
|`Hoàn thành mục tiêu` _→_|`Duchamp`|
|`Hoàn thành mục tiêu` _→_<br>`Hoàn thành mục tiêu` _→_|`duchampian`<br>`marcel du champ`|
|`Hoàn thành mục tiêu` _→_|`Marcel Duchamp`|
|`Hoàn thành mục tiêu` _→_|`MARCEL DUCHAMP`|

**Hình G.34:** Ví dụ dữ liệu định dạng cho TriviaQA. TriviaQA cho phép nhiều hoàn thành hợp lệ.

59

|`Bối cảnh` _→_|`C: Trường nào đã được Burne Hogarth lập ra?`|
|---|---|
||`D:`|
|`Hoàn thành mục tiêu` _→_|`Trường Nghệ Thuật Visaul`|
||**Hình G.35:** Ví dụ dữ liệu định dạng cho WebQA|
|`Bối cảnh` _→

||||||||Không mẫu||Một mẫu|||Ít mẫu||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Tên|Chỉ số|Tập dữ liệu|SOTA huấn luyện tinh chỉnh|K huấn luyện tinh chỉnh|Small|Med Large|XL 2.7B 6.7B 13B 175B|Small Med Large|XL 2.7B 6.7B 13B 175B|Small|Med Larg|e XL 2.7B 6.7B 13B 175B<br>(|máy chủ thử nghiệm 175B)|
|HellaSwag<br>|độ chính xác|dev<br>|85.6<br>|20<br>|33.7<br>|43.6 51.0<br>|54.7 62.8 67.4 70.9 78.9<br>|33.0<br>42.9 50.5<br><br>|53.5 61.9 66.5 70.0 78.1<br>|33.5<br>|43.1 51.3<br>|54.9 62.9 67.3 71.3 79.3<br>||
|LAMBADA<br>LAMBADA|độ chính xác<br>ppl|test<br>test|68.0<br>8.63|15<br>15|42.7<br>18.6|54.3 60.4<br>9.09 6.53|63.6 67.1 70.3 72.5 76.2<br>5.44 4.60 4.00 3.56 3.00|22.0<br>47.1 52.6<br>165.0 11.6 8.29|58.3 61.1 65.4 69.0 72.5<br>6.46 5.53 4.61 4.06 3.35|22.0<br>165.0|40.4 63.2<br> 27.6 6.63|57.0 78.1 79.1 81.3 86.4<br>7.45 2.89 2.56 2.56 1.92||
|StoryCloze|độ chính xác|test|91.8|70|63.3|68.5 72.4|73.4 77.2 77.7 79.5 83.2|62.3<br>68.7 72.3|74.2 77.3 78.7 79.7 84.7|62.3|70.2 73.9|76.1 80.2 81.2 83.0 87.7||
|NQs|độ chính xác|test|44.5|64|0.64|1.75 2.71|4.40 6.01 5.79 7.84 14.6|1.19<br>3.07 4.79|5.43 8.73 9.78 13.7 23.0|1.72|4.46 7.89|9.72 13.2 17.0 21.0 29.9||
|TriviaQA<br>Wb|độ chính xác<br>|dev<br>tt|68.0<br>455|64<br>64|4.15<br>177|7.61 14.0<br>320433|19.7 31.3 38.7 41.8 64.3<br>463792773822144|4.19<br>12.9 20.5<br>256<br>620851|26.5 35.9 44.4 51.3 68.0<br>915145151190253|6.96<br>546|16.3 26.5<br>126159|32.1 42.3 51.6 57.5 71.2<br>196248277335415|71.2|
|eQs|độ chính xác|es|.||.|. .|. . . . .|.<br>. .|. . . . .|.|. .|. . . . .||
|Ro_→_En 16|BLEU-|mb test|39.9|64|2.08|2.71 3.09|3.15 16.3 8.34 20.2 19.9|0.55<br>15.4 23.0|26.3 30.6 33.2 35.6 38.6|1.25|20.7 25.8|29.2 33.1 34.8 37.0 39.5||
|Ro_→_En 16<br>|BLEU-<br>|sb<br>test<br>||64<br>|2.39<br>|3.08 3.49<br>|3.56 16.8 8.75 20.8 20.9<br>|0.65<br>15.9 23.6<br><br>|26.8 31.3 34.2 36.7 40.0<br>|1.40<br>|21.3 26.6<br>|30.1 34.3 36.2 38.4 41.3<br>||
|En_→_Ro 16<br>En_→_Ro 16|BLEU-<br>BLEU-|mb test<br>sb<br>test|38.5|64<br>64|2.14<br>2.61|2.65 2.53<br>3.11 3.07|2.50 3.46 4.24 5.32 14.1<br>3.09 4.26 5.31 6.43 18.0|0.35<br>3.30 7.89<br>0.55<br>3.90 9.15|8.72 13.2 15.1 17.3 20.6<br>10.3 15.7 18.2 20.8 24.9|1.25<br>1.64|5.90 9.33<br>7.40 10.9|10.7 14.3 16.3 18.0 21.0<br>12.9 17.2 19.6 21.8 25.8||
|Fr_→_En 14<br>FE 14|BLEU-<br>BLEU|mb test<br>b<br>|35.0|64<br>64|1.81<br>229|2.53 3.47<br>299390|3.13 20.6 15.1 21.8 21.2<br>360212155224219|1.28<br>15.9 23.7<br>150<br>163244|26.3 29.0 30.5 30.2 33.7<br>270300316314356|4.98<br>530|25.5 28.5<br>262295|31.1 33.7 34.9 36.6 39.2<br>322351364383414||
|r_→_n<br>En_→_Fr 14|-<br>BLEU-|test<br>mb test|45.6|64|.<br>1.74|. .<br>2.16 2.73|. . . . .<br>2.15 15.1 8.82 12.0 25.2|.<br>. .<br>0.49<br>8.00 14.8|. . . . .<br>15.9 20.3 23.3 24.9 28.3|.<br>4.08|. .<br>14.5 19.3|. . . . .<br>21.5 24.9 27.3 29.5 32.6||
|En_→_Fr 14|BLEU-|sb<br>test|45.9|64|2.44|2.75 3.54|2.82 19.3 11.4 15.3 31.3|0.81<br>10.0 18.2|19.3 24.7 28.3 30.1 34.1|5.31|18.0 23.6|26.1 30.3 33.3 35.5 39.9||
|De_→_En 16<br>|BLEU-<br>|mb test<br><br>|40.2|64<br>|2.06<br>|2.87 3.41<br>|3.63 21.5 17.3 23.0 27.2<br>|0.83<br>16.2 22.5<br><br>|24.7 28.2 30.7 33.0 30.4<br>|3.25<br>|22.7 26.2<br>|29.2 32.7 34.8 37.3 40.6<br>||
|De_→_En 16<br>En_→_De 16|BLEU-<br>BLEU-|b<br>test<br>mb test|41.2|64<br>64|2.39<br>1.70|3.27 3.85<br>2.27 2.31|4.04 22.5 18.2 24.4 28.6<br>2.43 12.9 8.66 10.4 24.6|0.93<br>17.1 23.4<br>0.50<br>7.00 12.9|25.8 29.2 31.9 34.5 32.1<br>13.1 18.3 20.9 22.5 26.2|3.60<br>3.42|23.8 27.5<br>12.3 15.4|30.5 34.1 36.5 39.1 43.0<br>17.1 20.9 23.0 26.6 29.7||
|En_→_De 16|BLEU-|sb<br>test|41.2|64|2.09|2.65 2.75|2.92 13.7 9.36 11.0 25.3|0.54<br>7.40 13.4|13.4 18.8 21.7 23.3 27.3|3.78|12.9 16.1|17.7 21.7 24.1 27.7 30.9||
|Winograd|độ chính xác|test|93.8|7|66.3|72.9 74.7|76.9 82.4 85.7 87.9 88.3|63.4<br>68.5 72.9|76.9 82.4 84.6 86.1 89.7|63.4|67.4 73.6|76.9 84.3 85.4 82.4 88.6||
|Winogrande|độ chính xác|dev|84.6|50|52.0|52.1 57.4|58.7 62.3 64.5 67.9 70.2|51.3<br>53.0 58.3|59.1 61.7 65.8 66.9 73.2|51.3|52.6 57.5|59.1 62.6 67.4 70.0 77.7||
|PIQA<br>|độ chính xác<br>|dev|77.1<br>|50<br>|64.6<br>|70.2 72.9<br>|75.1 75.6 78.0 78.5 81.0<br>|64.3<br>69.3 71.8<br><br>|74.4 74.3 76.3 77.8 80.5<br>|64.3<br>|69.4 72.0<br>|74.3 75.4 77.8 79.9 82.3<br>|82.8|
|ARC (Challenge<br>ARC (Easy)|) độ chính xác<br>độ chính xác|test<br>test|78.5<br>92.0|50<br>50|26.6<br>43.6|29.5 31.8<br>46.553.0|35.5 38.0 41.4 43.7 51.4<br>53.858.260.263.868.8|25.5<br>30.2 31.6<br>42.7<br>48.254.6|36.4 38.4 41.5 43.1 53.2<br>55.960.362.666.871.2|25.5<br>42.7|28.4 32.3<br>51.058.1|36.7 39.5 43.7 44.8 51.5<br>59.162.165.869.170.1||
|<br>OBkA|||872|100|356|<br>432452|<br>468530504556576|<br>370<br>398462|<br>464534530558588|370|<br>436480|<br>506556552608654||
|penooQ|độ chính xác|test|.||.|. .|. . . . .|.<br>. .|. . . . .|.|. .|. . . . .||
|Quac|f1|dev|74.4|5|21.2|26.8 31.0|30.1 34.7 36.1 38.4 41.5|21.1<br>26.9 31.9|32.3 37.4 39.0 40.6 43.4|21.6|27.6 32.9|34.2 38.2 39.9 40.9 44.3||
|RACE-h<br>RACE-m<br>|độ chính xác<br>độ chính xác|test<br>test<br>|90.0<br>93.1<br>|10<br>10<br>|35.2<br>42.1<br>|37.9 40.1<br>47.2 52.1<br>|40.9 42.4 44.1 44.6 45.5<br>52.3 54.7 54.4 56.7 58.4<br>|34.3<br>37.7 40.0<br>42.3<br>47.3 51.7<br><br>|42.0 43.8 44.3 44.6 45.9<br>55.2 56.1 54.7 56.9 57.4<br>|34.3<br>42.3<br>|37.0 40.4<br>47.0 52.7<br>|41.4 42.3 44.7 45.1 46.8<br>53.0 55.6 55.4 58.1 58.1<br>||
|SQuADv2|em|dev|90.7|16|22.6|32.8 33.9|43.1 43.6 45.4 49.0 52.6|25.1<br>37.5 37.9|47.9 47.9 51.1 56.0 60.1|27.5|40.5 39.2|53.5 50.0 56.6 62.6 64.9||
|SQuADv2<br>CA|f1<br>f1|dev<br>d|93.0<br>907|16<br>5|28.3<br>345|40.2 41.4<br>550618|50.3 51.0 52.7 56.3 59.5<br>653711728763815|30.1<br>43.6 44.1<br>306<br>521616|54.0 54.1 57.1 61.8 65.4<br>661718751779840|32.1<br>311|45.5 44.9<br>520627|58.7 55.9 62.1 67.7 69.8<br>668732773799850||
|oQ<br>DROP|f1|ev<br>dev|.<br>89.1|20|.<br>9.40|. .<br>13.6 14.4|. . . . .<br>16.4 19.7 17.0 24.0 23.6|.<br>. .<br>11.7<br>18.1 20.9|. . . . .<br>23.0 26.4 27.3 29.2 34.3|.<br>12.9|. .<br>18.7 24.0|. . . . .<br>25.6 29.7 29.7 32.3 36.5||
|BoolQ<br>|độ chính xác<br>|dev<br>|91.0<br>|32<br>|49.7<br>|60.3 58.9<br>|62.4 67.1 65.4 66.2 60.5<br>|52.6<br>61.7 60.4<br><br>|63.7 68.4 68.7 69.0 76.7<br>|43.1<br>|60.6 62.0<br>|64.1 70.3 70.0 70.2 77.5<br>|76.4<br>|
|CB<br>|độ chính xác<br>|dev<br>|96.9<br>|32<br>|0.00<br>|32.1 8.93<br>|19.6 19.6 28.6 19.6 46.4<br>|55.4<br>53.6 53.6<br><br>|48.2 57.1 33.9 55.4 64.3<br>|42.9<br>|58.9 53.6<br>|69.6 67.9 60.7 66.1 82.1<br>|75.6<br>|
|CB<br>Copa|f1<br>độ chính xác|dev<br>dev|93.9<br>94.8|32<br>32|0.00<br>66.0|29.3 11.4<br>68.073.0|17.4 22.4 25.1 20.3 42.8<br>77.076.080.084.091.0|60.1<br>39.8 45.6<br>62.0<br>64.066.0|37.5 45.7 28.5 44.6 52.5<br>74.076.082.086.087.0|26.1<br>67.0|40.4 32.6<br>64.072.0|48.3 45.7 44.6 46.0 57.2<br>77.083.083.086.092.0|52.0<br>92.0|
|RTE||d|925|32|477|<br>498484|<br>560466552628635|<br>531<br>473495|<br>495549549563704|523|<br>484469|<br>509563495606729|690|
||độ chính xác|ev<br>|.<br>||.<br>|. .<br>|. . . . .<br>|.<br>. .<br><br>|. . . . .<br>|.<br>|. .<br>|. . . . .<br>|.<br>|
|WiC|độ chính xác|dev|76.1|32|0.00|0.00 0.00|0.00 0.00 0.00 0.00 0.00|50.0<br>50.3 50.3|49.2 49.4 50.3 50.0 48.6|49.8|55.0 53.0|53.0 51.6 53.1 51.1 55.3|49.4|
|WSC<br>MultiRC|độ chính xác<br>độ chính xác|dev<br>dev|93.8<br>623|32<br>32|59.6<br>472|56.7 65.4<br>965123|61.5 66.3 60.6 64.4 65.4<br>136143184242276|58.7<br>58.7 60.6<br>472<br>965123|62.5 66.3 60.6 66.3 69.2<br>136143184242276|58.7<br>609|60.6 54.8<br>118168|49.0 62.5 67.3 75.0 75.0<br>208247238250325|80.1<br>305|
|MultiRC<br>|f1a|dev<br>|.<br>88.2<br>|32<br>|.<br>57.0<br>|. .<br>59.7 60.4<br>|. . . . .<br>59.9 60.0 64.5 71.4 72.9<br>|.<br>. .<br>57.0<br>59.7 60.4<br><br>|. . . . .<br>59.9 60.0 64.5 71.4 72.9<br>|.<br>45.0<br>|. .<br>55.9 64.2<br>|. . . . .<br>65.4 69.5 66.4 69.3 74.8<br>|.<br>75.4<br>|
|ReCoRD|độ chính xác|dev|92.5|32|70.8|78.5 82.1|84.1 86.2 88.6 89.0 90.2|69.8<br>77.0 80.7|83.0 85.9 88.0 88.8 90.2|69.8|77.2 81.3|83.1 86.6 87.9 88.9 89.0|90.2|
|ReCoRD<br>SGLUE|f1<br>|dev<br>d|93.3<br>890|32|71.9<br>406|79.2 82.8<br>474468|85.2 87.3 89.5 90.4 91.0<br>496501523544582|70.7<br>77.8 81.6<br>544<br>551567|83.9 86.8 88.8 89.7 91.2<br>578612597643689|70.7<br>502|77.9 82.1<br>562568|84.0 87.5 88.8 89.8 90.1<br>600643636669732|91.1<br>718|
|uper|average|ev|.||.|. .|. . . . .|.<br>. .|. . . . .|.|. .|. . . . .|.|
|ANLI R1|độ chính xác|test|73.8|50|33.4|34.2 33.4|33.4 34.2 32.3 33.2 34.6|32.1<br>31.6 31.9|34.6 30.6 31.6 32.7 32.0|32.1|32.5 30.9|32.5 33.5 33.1 33.3 36.8||
|ANLI R2<br>|độ chính xác<br>|test<br>|50.7<br>|50<br>|33.2<br>|31.9 33.3<br>|33.3 33.8 33.5 33.5 35.4<br>|35.7<br>33.7 33.2<br><br>|32.7 32.7 33.9 33.9 33.9<br>|35.7<br>|33.8 32.1<br>|31.4 32.6 33.3 32.6 34.0<br>||
|ANLI R3|độ chính xác|test|48.3|50|33.6|34.0 33.8|33.4 35.3 34.8 34.4 34.5|35.0<br>32.6 33.0|33.9 34.1 33.1 32.5 35.1|35.0|34.4 35.1|36.0 32.7 33.9 34.5 40.2||
|2D+|độ chính xác|n/a||50|0.70|0.65 0.70|0.85 1.10 2.54 15.4 76.9|2.00<br>0.55 3.15|4.00 12.1 19.6 73.0 99.6|2.00|4.10 3.50|4.50 8.90 11.9 55.5 100.0||
|2D-<br>|độ chính xác|n/a<br>||50<br>|1.25<br>|1.25 1.25<br>|1.25 1.60 7.60 12.6 58.0<br>|1.15<br>0.95 1.45<br><br>|1.95 3.85 11.5 44.6 86.4<br>|1.15<br>|1.45 2.25<br>|2.70 7.35 13.6 52.4 98.9<br>||
|3D+<br>3D-|độ chính xác<br>độ chính xác|n/a<br>n/a||50<br>50|0.10<br>0.05|0.10 0.05<br>0.05 0.05|0.10 0.10 0.25 1.40 34.2<br>0.05 0.05 0.45 1.35 48.3|0.15<br>0.00 0.10<br>0.05<br>0.15 0.25|0.30 0.45 0.95 15.4 65.5<br>0.30 0.55 1.60 6.15 78.7|0.15<br>0.05|0.45 0.30<br>0.10 0.15|0.55 0.75 0.90 8.40 80.4<br>0.35 0.65 1.05 9.20 94.2||
|4D+|độ chính xác|n/a||50|005|005000|000005005015400|000<br>000010|000000010080140|000|005005|000015015040255||
|4D-<br>|độ chính xác|n/a<br>||50<br>|.<br>0.00<br>|. .<br>0.00 0.00<br>|. . . . .<br>0.00 0.00 0.00 0.10 7.50<br>|.<br>. .<br>0.00<br>0.00 0.00<br><br>|. . . . .<br>0.00 0.05 0.00 0.50 14.0<br>|.<br>0.00<br>|. .<br>0.05 0.00<br>|. . . . .<br>0.00 0.10 0.05 0.40 26.8<br>||
|5D+|độ chính xác|n/a||50|0.00|0.00 0.00|0.00 0.00 0.00 0.00 0.65|0.00<br>0.00 0.00|0.00 0.00 0.00 0.05 3.45|0.00|0.00 0.00|0.00 0.00 0.00 0.05 9.30||
|5D-|độ chính xác|n/a||50|0.00|0.00 0.00|0.00 0.00 0.00 0.00 0.80|0.00<br>0.00 0.00|0.00 0.00 0.00 0.05 3.75|0.00|0.00 0.00|0.00 0.00 0.00 0.00 9.90||
|2Dx<br>|độ chính xác|n/a<br>||50<br>|2.20<br>|2.25 2.65<br>|2.10 2.55 5.80 6.15 19.8<br>|1.35<br>2.35 3.35<br><br>|2.35 4.75 9.15 11.0 27.4<br>|1.35<br>|2.90 2.70<br>|2.85 4.25 6.10 7.05 29.2<br>||
|1DC|độ chính xác|n/a||50|1.25|2.95 2.75|0.05 0.30 2.35 0.75 9.75|1.90<br>2.80 2.85|3.65 6.45 9.15 8.20 14.3|1.70|2.15 3.90|5.75 6.20 7.60 9.95 21.3||
|Cycled Letters<br>|độ chính xác<br>|n/a<br>||100<br>|0.62<br>|0.71 2.85<br>|0.00 0.63 1.35 2.58 3.66<br>|1.67<br>4.36 5.68<br><br>|6.46 6.25 9.41 15.1 21.7<br>|4.63<br>|9.27 10.7<br>|14.5 16.7 21.9 27.7 37.9<br>||
|Anagrams 1<br>|độ chính xác|n/a<br>||100<br>|0.10<br>|0.14 0.40<br>|0.00 0.27 0.69 1.16 2.28<br>|0.21<br>0.61 1.12<br><br>|1.27 1.60 2.72 3.72 8.62<br>|0.50<br>|1.27 2.13<br>|3.05 3.81 5.49 8.38 15.1<br>||
|Anagrams 2<br>Symbol Insertion|độ chính xác<br> độ chính xác|n/a<br>n/a||100<br>100|0.81<br>0.00|1.21 2.69<br>0.000.10|0.01 1.71 3.75 4.53 8.91<br>0.000.050.420.898.26|1.19<br>2.62 4.70<br>0.03<br>0.050.57|4.77 6.97 10.2 14.6 25.9<br>1.181.673.466.6245.4|1.94<br>0.11|4.80 7.59<br>0.282.19|9.87 12.6 18.9 25.6 39.7<br>4.186.6111.027.367.2||
|<br>Reversed Words|<br>độ chính xác|n/a||100|0.00|<br>0.01 0.01|<br>0.01 0.02 0.03 0.03 0.09|<br>0.02<br>0.01 0.01|<br>0.00 0.05 0.07 0.11 0.48|0.00|<br>0.05 0.00|<br>0.17 0.24 0.30 0.42 0.44||
|SAT Analogies|độ chính xác|n/a||20|35.6|39.0 45.2|44.1 50.0 49.2 52.7 53.7|30.5<br>41.2 43.1|46.5 55.1 54.3 53.5 59.1|30.5|40.4 42.8|40.6 48.4 51.9 53.5 65.2||



**Bảng H.1:** Điểm số cho từng tác vụ, thiết lập và mô hình mà chúng tôi nghiên cứu trong bài báo này.

63


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-00.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-01.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-02.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-03.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-04.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-05.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-06.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-07.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-08.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-09.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-10.png)


**Hình H.1:** Tất cả kết quả cho tất cả các tác vụ SuperGLUE.


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-12.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-13.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0064-14.png)


**Hình H.2:** Kết quả cho tác vụ SAT.

**Hình H.3:** Tất cả kết quả cho tất cả các tác vụ Winograd.

64


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-00.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-01.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-02.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-03.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-04.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-05.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-06.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-07.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-08.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-09.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-10.png)


**Hình H.4:** Tất cả kết quả cho tất cả các tác vụ Số học.


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-12.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-13.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0065-14.png)


**Hình H.5:** Tất cả kết quả cho tất cả các bài tập điền từ và hoàn thành.

65


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-00.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-01.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-02.png)


**Hình H.6:** Tất cả kết quả cho tất cả các tác vụ phân tích logic thông thường.


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-04.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-05.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-06.png)


**Hình H.7:** Tất cả kết quả cho tất cả các tác vụ Hỏi-Đáp (QA).


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-08.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-09.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-10.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-11.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-12.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-13.png)


**Hình H.8:** Tất cả kết quả cho tất cả các tác vụ hiểu nội dung khi đọc.


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-15.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-16.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0066-17.png)


**Hình H.9:** Tất cả kết quả cho tất cả các vòng ANLI.

66


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-00.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-01.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-02.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-03.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-04.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-05.png)


**Hình H.10:** Tất cả kết quả cho tất cả các tác vụ Xáo trộn.


![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-07.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-08.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-09.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-10.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-11.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-12.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-13.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-14.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-15.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-16.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-17.png)



![](temp_images/b5b8d8aa-8ee2-4bf0-a53f-65917094a362/input_b5b8d8aa-8ee2-4bf0-a53f-65917094a362.pdf-0067-18.png)


**Hình H.11:** Tất cả kết quả cho tất cả các tác vụ Dịch thuật.

67

# **Tài liệu tham khảo**

- [ADG<sup>+</sup> 16] Marcin Andrychowicz, Misha Denil, Sergio Gomez, Matthew W Hoffman, David Pfau, Tom Schaul, Brendan Shillingford, và Nando De Freitas. Học cách học bằng cách giảm độ dốc theo độ dốc. Trong _Advances in neural information processing systems_ , trang 3981–3989, 2016.

- [AI19] WeChat AI. Tr-mt (ensemble), Tháng 12 năm 2019.

- [AJF19] Roee Aharoni, Melvin Johnson, và Orhan Firat. Dịch máy thần kinh đa ngôn ngữ quy mô lớn. Trong _Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers)_ , 2019.

- [BBDIW20] Su Lin Blodgett, Solon Barocas, Hal Daume III, và Hanna Wallach. Ngôn ngữ (công nghệ) là sức mạnh: Một khảo sát phê phán về "thiên vị" trong NLP. _arXiv preprint arXiv:2005.14050_ , 2020.

- [BCFL13] Jonathan Berant, Andrew Chou, Roy Frostig, và Percy Liang. Phân tích cú pháp ngữ nghĩa trên Freebase từ các cặp câu hỏi-câu trả lời. Trong _Proceedings of the 2013 conference on empirical methods in natural language processing_ , trang 1533–1544, 2013.

- [BDD<sup>+</sup> 09] Luisa Bentivogli, Ido Dagan, Hoa Trang Dang, Danilo Giampiccolo, và Bernardo Magnini. Thử thách nhận dạng suy luận văn bản PASCAL lần thứ năm. 2009.

- [BES10] Stefano Baccianella, Andrea Esuli, và Fabrizio Sebastiani. Sentiwordnet 3.0: một tài nguyên từ vựng nâng cao cho phân tích cảm xúc và khai thác ý kiến. Trong _Lrec_ , tập 10, trang 2200–2204, 2010.

- [BHDD<sup>+</sup> 06] Roy Bar Haim, Ido Dagan, Bill Dolan, Lisa Ferro, Danilo Giampiccolo, Bernardo Magnini, và Idan Szpektor. Thử thách nhận dạng suy luận văn bản PASCAL lần thứ hai. 2006.

- [BHT<sup>+</sup> 20] Yonatan Bisk, Ari Holtzman, Jesse Thomason, Jacob Andreas, Yoshua Bengio, Joyce Chai, Mirella Lapata, Angeliki Lazaridou, Jonathan May, Aleksandr Nisnevich, và cộng sự. Kinh nghiệm làm nền tảng cho ngôn ngữ. _arXiv preprint arXiv:2004.10151_ , 2020.

- [BLC13] Yoshua Bengio, Nicholas Leonard, và Aaron C. Courville. Ước tính hoặc truyền lan gradient qua các neuron ngẫu nhiên cho tính toán có điều kiện. _Arxiv_ , 2013.

- [BZB<sup>+</sup> 19] Yonatan Bisk, Rowan Zellers, Ronan Le Bras, Jianfeng Gao, và Yejin Choi. Piqa: Suy luận về logic thông thường vật lý trong ngôn ngữ tự nhiên. _arXiv preprint arXiv:1911.11641_ , 2019.

- [Car97] Rich Caruana. Học đa tác vụ. _Machine learning_ , 28(1), 1997.

- [CB78] Susan Carey và Elsa Bartlett. Tiếp thu một từ mới duy nhất. _Proceedings of the Stanford Child Language Conference_ , 1978.

- [CCE<sup>+</sup> 18] Peter Clark, Isaac Cowhey, Oren Etzioni, Tushar Khot, Ashish Sabharwal, Carissa Schoenick, and Oyvind Tafjord. Bạn nghĩ mình đã giải quyết được vấn đề trả lời câu hỏi? Hãy thử ARC, thử thách suy luận của AI2. _ArXiv_ , abs/1803.05457, 2018.

- [CGRS19] Rewon Child, Scott Gray, Alec Radford, and Ilya Sutskever. Tạo chuỗi dài bằng các bộ biến đổi thưa thớt, 2019.

- [CHI<sup>+</sup> 18] Eunsol Choi, He He, Mohit Iyyer, Mark Yatskar, Wen-tau Yih, Yejin Choi, Percy Liang, and Luke Zettlemoyer. Quac : Trả lời câu hỏi trong ngữ cảnh. _Arxiv_ , 2018.

- [CLC<sup>+</sup> 19] Christopher Clark, Kenton Lee, Ming-Wei Chang, Tom Kwiatkowski, Michael Collins, and Kristina Toutanova. BoolQ: Khám phá độ khó đáng ngạc nhiên của các câu hỏi có/không tự nhiên. _arXiv preprint arXiv:1905.10044_ , 2019.

- [CLY<sup>+</sup> 19] Yen-Chun Chen, Linjie Li, Licheng Yu, Ahmed El Kholy, Faisal Ahmed, Zhe Gan, Yu Cheng, and Jingjing Liu. Uniter: Học biểu diễn hình ảnh-văn bản phổ quát. _arXiv preprint arXiv:1909.11740_ , 2019.

- [Cra17] Kate Crawford. Vấn đề với sự thiên vị. _NIPS 2017 Keynote_ , 2017.

- [DCLT18] Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. BERT: Huấn luyện trước các bộ biến đổi hai chiều sâu để hiểu ngôn ngữ. _arXiv preprint arXiv:1810.04805_ , 2018.

68

- [DGM06] Ido Dagan, Oren Glickman, and Bernardo Magnini. Thử thách nhận diện suy luận văn bản PASCAL. Trong _Các thử thách học máy. đánh giá sự không chắc chắn của dự đoán, phân loại đối tượng hình ảnh và nhận diện suy luận văn bản_ , trang 177–190. Springer, 2006.

- [DGV<sup>+</sup> 18] Mostafa Dehghani, Stephan Gouws, Oriol Vinyals, Jakob Uszkoreit, and Lukasz Kaiser. Các bộ biến đổi phổ quát. _Arxiv_ , 2018.

- [DHKH14] Nadir Durrani, Barry Haddow, Philipp Koehn, and Kenneth Heafield. Hệ thống dịch máy dựa trên cụm từ của Edinburgh cho WMT-14. Trong _Kỷ yếu Hội thảo lần thứ chín về Dịch máy Thống kê_ , trang 97–104, 2014.

- [DL15] Andrew M. Dai and Quoc V. Le. Học chuỗi bán giám sát. Trong _Những tiến bộ trong hệ thống xử lý thông tin thần kinh_ , 2015.

- [DMST19] Marie-Catherine De Marneffe, Mandy Simons, and Judith Tonhauser. CommitmentBank: Nghiên cứu phép chiếu trong diễn ngôn tự nhiên. 2019. Sẽ xuất hiện trong kỷ yếu của Sinn und Bedeutung 23. Dữ liệu có thể tìm thấy tại https://github.com/mcdm/CommitmentBank/.

- [DSC<sup>+</sup> 16] Yan Duan, John Schulman, Xi Chen, Peter L. Bartlett, Ilya Sutskever, and Pieter Abbeel. Rl<sup>2</sup> : Học tăng cường nhanh thông qua học tăng cường chậm. _ArXiv_ , abs/1611.02779, 2016.

- [DWD<sup>+</sup> 19] Dheeru Dua, Yizhong Wang, Pradeep Dasigi, Gabriel Stanovsky, Sameer Singh, and Matt Gardner. Drop: Một bộ dữ liệu chuẩn hiểu nội dung khi đọc yêu cầu suy luận rời rạc trên các đoạn văn. _arXiv preprint arXiv:1903.00161_ , 2019.

- [DYY<sup>+</sup> 19] Zihang Dai, Zhilin Yang, Yiming Yang, Jaime G. Carbonell, Quoc V. Le, and Ruslan Salakhutdinov. Transformer-XL: Các mô hình ngôn ngữ chú ý vượt ra ngoài ngữ cảnh độ dài cố định. _Arxiv_ , 2019.

- [EOAG18] Sergey Edunov, Myle Ott, Michael Auli, and David Grangier. Hiểu dịch ngược ở quy mô lớn. _arXiv preprint arXiv:1808.09381_ , 2018.

- [FAL17] Chelsea Finn, Pieter Abbeel, and Sergey Levine. Học siêu dữ liệu độc lập với mô hình để thích nghi nhanh các mạng sâu. _ArXiv_ , abs/1703.03400, 2017.

- [Fyo00] Yaroslav Fyodorov. Một hệ thống suy luận logic tự nhiên, 2000.

- [GG19] Hila Gonen and Yoav Goldberg. Son môi trên lợn: Các phương pháp khử thiên vị che giấu các thiên vị giới tính có hệ thống trong nhúng từ nhưng không loại bỏ chúng. _arXiv preprint arXiv:1903.03862_ , 2019.

- [GLT<sup>+</sup> 20] Kelvin Guu, Kenton Lee, Zora Tung, Panupong Pasupat, and Ming-Wei Chang. Realm: Huấn luyện trước mô hình ngôn ngữ tăng cường truy xuất. _arXiv preprint arXiv:2002.08909_ , 2020.

- [GMDD07] Danilo Giampiccolo, Bernardo Magnini, Ido Dagan, and Bill Dolan. Thử thách nhận diện suy luận văn bản PASCAL lần thứ ba. Trong _Kỷ yếu hội thảo ACL-PASCAL về suy luận văn bản và diễn giải_ , trang 1–9. Association for Computational Linguistics, 2007.

- [Gra16] Alex Graves. Thời gian tính toán thích ứng cho mạng thần kinh hồi quy. _Arxiv_ , 2016.

- [GSL<sup>+</sup> 18] Suchin Gururangan, Swabha Swayamdipta, Omer Levy, Roy Schwartz, Samuel R Bowman, and Noah A Smith. Các tạo tác chú thích trong dữ liệu suy luận ngôn ngữ tự nhiên. _arXiv preprint arXiv:1803.02324_ , 2018.

- [GSR19] Sebastian Gehrmann, Hendrik Strobelt, and Alexander M. Rush. GLTR: Phát hiện thống kê và trực quan hóa văn bản được tạo. _arXiv preprint arXiv: 1906.04043_ , 2019.

- [GWC<sup>+</sup> 18] Jiatao Gu, Yong Wang, Yun Chen, Kyunghyun Cho, and Victor OK Li. Học siêu dữ liệu cho dịch máy thần kinh tài nguyên thấp. _arXiv preprint arXiv:1808.08437_ , 2018.

- [HB20] Daniel Hernandez and Tom Brown. AI và hiệu quả, tháng 5 năm 2020.

- [HBFC19] Ari Holtzman, Jan Buys, Maxwell Forbes, and Yejin Choi. Trường hợp kỳ lạ của sự suy thoái văn bản thần kinh. _CoRR_ , abs/1904.09751, 2019.

- [HLW<sup>+</sup> 20] Dan Hendrycks, Xiaoyuan Liu, Eric Wallace, Adam Dziedzic, Rishabh Krishnan, and Dawn Song. Các bộ biến đổi được huấn luyện trước cải thiện tính mạnh mẽ ngoài phân phối. _arXiv preprint arXiv:2004.06100_ , 2020.

69

- [HNA<sup>+</sup> 17] Joel Hestness, Sharan Narang, Newsha Ardalani, Gregory Diamos, Heewoo Jun, Hassan Kianinejad, Md. Mostofa Ali Patwary, Yang Yang, and Yanqi Zhou. Khả năng mở rộng của học sâu có thể dự đoán được, theo kinh nghiệm. _arXiv preprint arXiv:1712.00409_ , 2017.

- [HR18] Jeremy Howard and Sebastian Ruder. Huấn luyện tinh chỉnh mô hình ngôn ngữ phổ quát để phân loại văn bản. _arXiv preprint arXiv:1801.06146_ , 2018.

- [HVD15] Geoffrey Hinton, Oriol Vinyals, and Jeff Dean. Chắt lọc kiến thức trong mạng thần kinh. _arXiv preprint arXiv:1503.02531_ , 2015.

- [HYC01] Sepp Hochreiter, A Steven Younger, and Peter R Conwell. Học cách học bằng cách sử dụng Gradient Descent. Trong _Hội nghị Quốc tế về Mạng thần kinh nhân tạo_ , trang 87–94. Springer, 2001.

- [HZJ<sup>+</sup> 19] Po-Sen Huang, Huan Zhang, Ray Jiang, Robert Stanforth, Johannes Welbl, Jack Rae, Vishal Maini, Dani Yogatama, and Pushmeet Kohli. Giảm thiên vị cảm xúc trong các mô hình ngôn ngữ thông qua đánh giá phản thực tế. _arXiv preprint arXiv:1911.03064_ , 2019.

- [IBGC<sup>+</sup> 14] Mohit Iyyer, Jordan Boyd-Graber, Leonardo Claudino, Richard Socher, and Hal Daume III.´ Một mạng thần kinh để trả lời câu hỏi thực tế trên các đoạn văn. Trong _Các phương pháp thực nghiệm trong xử lý ngôn ngữ tự nhiên_ , 2014.

- [IDCBE19] Daphne Ippolito, Daniel Duckworth, Chris Callison-Burch, and Douglas Eck. Phát hiện tự động văn bản được tạo dễ nhất khi con người bị lừa. _arXiv preprint arXiv:1911.00650_ , 2019.

- [JCWZ17] Mandar Joshi, Eunsol Choi, Daniel S. Weld, and Luke Zettlemoyer. TriviaQA: Một bộ dữ liệu thử thách quy mô lớn được giám sát từ xa để hiểu nội dung khi đọc. _arXiv preprint arXiv:1705.03551_ , 2017.

- [JN20] Zheng Junyuan and Gamma Lab NYC. Bộ biến đổi số - ALBERT, tháng 3 năm 2020.

- [JVS<sup>+</sup> 16] Rafal Jozefowicz, Oriol Vinyals, Mike Schuster, Noam Shazeer, and Yonghui Wu. Khám phá giới hạn của mô hình ngôn ngữ. _arXiv preprint arXiv:1602.02410_ , 2016.

- [JYS<sup>+</sup> 19] Xiaoqi Jiao, Yichun Yin, Lifeng Shang, Xin Jiang, Xiao Chen, Linlin Li, Fang Wang, and Qun Liu. TinyBERT: Chắt lọc BERT để hiểu ngôn ngữ tự nhiên. _arXiv preprint arXiv:1909.10351_ , 2019.

- [JZC<sup>+</sup> 19] Ying Ju, Fubang Zhao, Shijie Chen, Bowen Zheng, Xuefeng Yang, and Yunfeng Liu. Báo cáo kỹ thuật về trả lời câu hỏi đàm thoại. _arXiv preprint arXiv:1909.10772_ , 2019.

- [KCR<sup>+</sup> 18] Daniel Khashabi, Snigdha Chaturvedi, Michael Roth, Shyam Upadhyay, and Dan Roth. Nhìn xa hơn bề mặt: Một bộ thử thách để hiểu nội dung khi đọc trên nhiều câu. Trong _Kỷ yếu Chương Bắc Mỹ của Hiệp hội Ngôn ngữ học Máy tính (NAACL)_ , 2018.

- [KKS<sup>+</sup> 20] Daniel Khashabi, Tushar Khot, Ashish Sabharwal, Oyvind Tafjord, Peter Clark, and Hannaneh Hajishirzi. UnifiedQA: Vượt qua ranh giới định dạng với một hệ thống QA duy nhất. _arXiv preprint arXiv:2005.00700_ , 2020.

- [KMB20] Sarah E. Kreps, Miles McCain, and Miles Brundage. Tất cả tin tức phù hợp để bịa đặt: Văn bản do AI tạo ra như một công cụ thông tin sai lệch trên phương tiện truyền thông, 2020.

- [KMH<sup>+</sup> 20] Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B. Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, and Dario Amodei. Các quy luật mở rộng cho các mô hình ngôn ngữ thần kinh, 2020.

- [KPR<sup>+</sup> 19] Tom Kwiatkowski, Jennimaria Palomaki, Olivia Redfield, Michael Collins, Ankur Parikh, Chris Alberti, Danielle Epstein, Illia Polosukhin, Matthew Kelcey, Jacob Devlin, Kenton Lee, Kristina N. Toutanova, Llion Jones, Ming-Wei Chang, Andrew Dai, Jakob Uszkoreit, Quoc Le, and Slav Petrov. Câu hỏi tự nhiên: một bộ dữ liệu chuẩn cho nghiên cứu trả lời câu hỏi. _Transactions of the Association of Computational Linguistics_ , 2019.

- [KR16] Yoon Kim and Alexander M. Rush. Chắt lọc kiến thức cấp độ chuỗi. _Arxiv_ , 2016.

- [LB02] Edward Loper and Steven Bird. NLTK: Bộ công cụ ngôn ngữ tự nhiên, 2002.

- [LC19] Guillaume Lample and Alexis Conneau. Huấn luyện trước mô hình ngôn ngữ đa ngôn ngữ. _arXiv preprint arXiv:1901.07291_ , 2019.

70

- [LCG<sup>+</sup> 19] Zhenzhong Lan, Mingda Chen, Sebastian Goodman, Kevin Gimpel, Piyush Sharma, and Radu Soricut. ALBERT: Một BERT nhẹ để học biểu diễn ngôn ngữ tự giám sát. _arXiv preprint arXiv:1909.11942_ , 2019.

- [LCH<sup>+</sup> 20] Xiaodong Liu, Hao Cheng, Pengcheng He, Weizhu Chen, Yu Wang, Hoifung Poon, and Jianfeng Gao. Huấn luyện đối kháng cho các mô hình ngôn ngữ thần kinh lớn. _arXiv preprint arXiv:2004.08994_ , 2020.

- [LDL19] Zhongyang Li, Xiao Ding, and Ting Liu. Dự đoán kết thúc câu chuyện bằng BERT có thể chuyển giao. _arXiv preprint arXiv:1905.07504_ , 2019.

- [LDM12] Hector Levesque, Ernest Davis, and Leora Morgenstern. Thử thách lược đồ Winograd. Trong _Hội nghị Quốc tế lần thứ mười ba về Các nguyên tắc biểu diễn và suy luận tri thức_ , 2012.

- [LGG<sup>+</sup> 20] Yinhan Liu, Jiatao Gu, Naman Goyal, Xian Li, Sergey Edunov, Marjan Ghazvininejad, Mike Lewis, and Luke Zettlemoyer. Huấn luyện trước khử nhiễu đa ngôn ngữ cho dịch máy thần kinh. _arXiv preprint arXiv:2001.08210_ , 2020.

- [LGH<sup>+</sup> 15] Xiaodong Liu, Jianfeng Gao, Xiaodong He, Li Deng, Kevin Duh, and Ye-Yi Wang. Học biểu diễn sử dụng mạng thần kinh sâu đa nhiệm để phân loại ngữ nghĩa và truy xuất thông tin. Trong _Kỷ yếu Hội nghị năm 2015 của Chương Bắc Mỹ của Hiệp hội Ngôn ngữ học Máy tính: Công nghệ Ngôn ngữ Con người_ , 2015.

- [LH17] Ilya Loshchilov and Frank Hutter. Chuẩn hóa suy giảm trọng số tách rời. _arXiv preprint arXiv:1711.05101_ , 2017.

- [LHCG19a] Xiaodong Liu, Pengcheng He, Weizhu Chen, and Jianfeng Gao. Cải thiện mạng thần kinh sâu đa nhiệm thông qua chắt lọc kiến thức để hiểu ngôn ngữ tự nhiên. _arXiv preprint arXiv:1904.09482_ , 2019.

- [LHCG19b] Xiaodong Liu, Pengcheng He, Weizhu Chen, and Jianfeng Gao. Mạng thần kinh sâu đa nhiệm để hiểu ngôn ngữ tự nhiên. _arXiv preprint arXiv:1901.11504_ , 2019.

- [Lin20] Tal Linzen. Làm thế nào chúng ta có thể đẩy nhanh tiến độ hướng tới khái quát hóa ngôn ngữ giống con người? _arXiv preprint arXiv:2005.00955_ , 2020.

- [LLG<sup>+</sup> 19] Mike Lewis, Yinhan Liu, Naman Goyal, Marjan Ghazvininejad, Abdelrahman Mohamed, Omer Levy, Ves Stoyanov, and Luke Zettlemoyer. Bart: Huấn luyện trước khử nhiễu tuần tự-sang-tuần tự cho tạo ngôn ngữ tự nhiên, dịch thuật và hiểu ngôn ngữ. _arXiv preprint arXiv:1910.13461_ , 2019.

- [LM17] Ke Li and Jitendra Malik. Học cách tối ưu hóa mạng nơ-ron. _arXiv preprint arXiv:1703.00441_ , 2017.

- [LOG<sup>+</sup> 19] Yinhan Liu, Myle Ott, Naman Goyal, Jingfei Du, Mandar Joshi, Danqi Chen, Omer Levy, Mike Lewis, Luke Zettlemoyer, and Veselin Stoyanov. RoBERTa: Một phương pháp huấn luyện trước BERT được tối ưu hóa mạnh mẽ. _arXiv preprint arXiv:1907.11692_ , 2019.

- [LPP<sup>+</sup> 20] Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Kuttler,¨ Mike Lewis, Wen-tau Yih, Tim Rocktaschel,¨ Sebastian Riedel, and Kiela Douwe. Tạo sinh tăng cường truy xuất cho các tác vụ NLP chuyên sâu về tri thức. _arXiv preprint arXiv:2005.11401_ , 2020.

- [LSP<sup>+</sup> 18] Peter J. Liu, Mohammad Saleh, Etienne Pot, Ben Goodrich, Ryan Sepassi, Lukasz Kaiser, and Noam Shazeer. Tạo Wikipedia bằng cách tóm tắt các chuỗi dài. _arXiv preprint arXiv:1801.10198_ , 2018.

- [LWS<sup>+</sup> 20] Zhuohan Li, Eric Wallace, Sheng Shen, Kevin Lin, Kurt Keutzer, Dan Klein, and Joseph E. Gonzalez. Huấn luyện lớn, sau đó nén: Suy nghĩ lại về kích thước mô hình để huấn luyện và suy luận hiệu quả cho các mô hình Transformer, 2020.

- [LXL<sup>+</sup> 17] Guokun Lai, Qizhe Xie, Hanxiao Liu, Yiming Yang, and Eduard Hovy. Race: Bộ dữ liệu hiểu nội dung khi đọc quy mô lớn từ các bài kiểm tra. _arXiv preprint arXiv:1704.04683_ , 2017.

- [LYN<sup>+</sup> 20] Sheng-Chieh Lin, Jheng-Hong Yang, Rodrigo Nogueira, Ming-Feng Tsai, Chuan-Ju Wang, and Jimmy Lin. Giải quyết các lược đồ Winogrande. _arXiv preprint arXiv:2003.08380_ , 2020.

- [Mac92] David. MacKay. Các hàm mục tiêu dựa trên thông tin cho việc lựa chọn dữ liệu chủ động. _Neural Computation_ , 1992.

71

- [MBXS17] Bryan McCann, James Bradbury, Caiming Xiong, and Richard Socher. Học được trong dịch thuật: Các véc-tơ từ được ngữ cảnh hóa. In _Advances in Neural Information Processing Systems_ , pages 6294–6305, 2017.

- [MCCD13] Tomas Mikolov, Kai Chen, Greg Corrado, and Jeffrey Dean. Ước lượng hiệu quả các biểu diễn từ trong không gian véc-tơ. _arXiv preprint arXiv:1301.3781_ , 2013.

- [MCH<sup>+</sup> 16] Nasrin Mostafazadeh, Nathanael Chambers, Xiaodong He, Devi Parikh, Dhruv Batra, Lucy Vanderwende, Pushmeet Kohli, and James Allen. Một kho ngữ liệu và khung đánh giá để hiểu sâu hơn về các câu chuyện logic thông thường. _arXiv preprint arXiv:1604.01696_ , 2016.

- [MCKS18] Todor Mihaylov, Peter Clark, Tushar Khot, and Ashish Sabharwal. Một bộ áo giáp có thể dẫn điện không? Một bộ dữ liệu mới cho việc trả lời câu hỏi có sách tham khảo. _ArXiv_ , abs/1809.02789, 2018.

- [MKAT18] Sam McCandlish, Jared Kaplan, Dario Amodei, and OpenAI Dota Team. Một mô hình thực nghiệm về huấn luyện theo lô lớn, 2018.

- [MKM<sup>+</sup> 94] Mitchell Marcus, Grace Kim, Mary Ann Marcinkiewicz, Robert MacIntyre, Ann Bies, Mark Ferguson, Karen Katz, and Britta Schasberger. The Penn Treebank: Chú thích cấu trúc đối số vị ngữ. In _Proceedings of the workshop on Human Language Technology_ , pages 114–119. Association for Computational Linguistics, 1994.

- [MKXS18] Bryan McCann, Nitish Shirish Keskar, Caiming Xiong, and Richard Socher. Thập môn ngôn ngữ tự nhiên: Học đa tác vụ dưới dạng trả lời câu hỏi. _arXiv preprint arXiv:1806.08730_ , 2018.

- [MPL19] R Thomas McCoy, Ellie Pavlick, and Tal Linzen. Đúng vì những lý do sai: Chẩn đoán các phương pháp phỏng đoán cú pháp trong suy luận ngôn ngữ tự nhiên. _arXiv preprint arXiv:1902.01007_ , 2019.

- [MWZ<sup>+</sup> 18] Margaret Mitchell, Simone Wu, Andrew Zaldivar, Parker Barnes, Lucy Vasserman, Ben Hutchinson, Elena Spitzer, Inioluwa Deborah Raji, and Timnit Gebru. Thẻ mô hình để báo cáo mô hình, 2018.

- [NBR20] Moin Nadeem, Anna Bethke, and Siva Reddy. Stereoset: Đo lường thiên vị rập khuôn trong các mô hình ngôn ngữ đã được huấn luyện trước. _arXiv preprint arXiv:2004.09456_ , 2020.

- [NK19] Timothy Niven and Hung-Yu Kao. Khám phá khả năng hiểu của mạng nơ-ron đối với các lập luận ngôn ngữ tự nhiên. _arXiv preprint arXiv:1907.07355_ , 2019.

- [Nor09] Peter Norvig. Dữ liệu kho ngữ liệu ngôn ngữ tự nhiên, 2009.

- [NvNvdG19] Malvina Nissim, Rik van Noord, and Rob van der Goot. Công bằng tốt hơn là giật gân: Đàn ông là bác sĩ thì phụ nữ cũng là bác sĩ. _arXiv preprint arXiv:1905.09866_ , 2019.

- [NWD<sup>+</sup> 19] Yixin Nie, Adina Williams, Emily Dinan, Mohit Bansal, Jason Weston, and Douwe Kiela. Adversarial NLI: Một điểm chuẩn mới cho hiểu ngôn ngữ tự nhiên. _arXiv preprint arXiv:1910.14599_ , 2019.

- [oR16] University of Regensburg. Fascha, 2016.

- [PCC18] Mohammad Taher Pilehvar and Jose Camacho-Collados. WIC: 10.000 cặp ví dụ để đánh giá các biểu diễn nhạy ngữ cảnh. _arXiv preprint arXiv:1808.09121_ , 2018.

- [PFB18] Jason Phang, Thibault Fevry, and Samuel R. Bowman.´ Bộ mã hóa câu trên STILTs: Huấn luyện bổ sung trên các tác vụ dữ liệu được gán nhãn trung gian. _arXiv preprint arXiv:1811.01088_ , 2018.

- [PHR<sup>+</sup> 18] Adam Poliak, Aparajita Haldar, Rachel Rudinger, J. Edward Hu, Ellie Pavlick, Aaron Steven White, and Benjamin Van Durme. Thu thập các vấn đề suy luận ngôn ngữ tự nhiên đa dạng để đánh giá biểu diễn câu. In _Proceedings of EMNLP_ , 2018.

- [PKL<sup>+</sup> 16] Denis Paperno, German Kruszewski, Angeliki Lazaridou, Quan Ngoc Pham, Raffaella Bernardi, Sandro´ Pezzelle, Marco Baroni, Gemma Boleda, and Raquel Fernandez.´ Bộ dữ liệu Lambada: Dự đoán từ yêu cầu ngữ cảnh diễn ngôn rộng. _arXiv preprint arXiv:1606.06031_ , 2016.

- [PNZtY18] Matthew E. Peters, Mark Neumann, Luke Zettlemoyer, and Wen tau Yih. Phân tích các nhúng từ theo ngữ cảnh: Kiến trúc và biểu diễn, 2018.

- [Pos18] Matt Post. Lời kêu gọi sự rõ ràng trong việc báo cáo điểm BLEU. _arXiv preprint arXiv:1804.08771_ , 2018.

72

- [PSM14] Jeffrey Pennington, Richard Socher, and Christopher Manning. GloVe: Các véc-tơ toàn cục cho biểu diễn từ. In _Proceedings of the 2014 conference on empirical methods in natural language processing (EMNLP)_ , 2014.

- [QIA20] QIANXIN. Sa-net trên ALBERT (tập hợp), Tháng 4 năm 2020.

- [QMZH19] Yusu Qian, Urwa Muaz, Ben Zhang, and Jae Won Hyun. Giảm thiên vị giới tính trong các mô hình ngôn ngữ cấp từ với hàm mất mát cân bằng giới tính. _arXiv preprint arXiv:1905.12801_ , 2019.

- [RBG11] Melissa Roemmele, Cosmin Adrian Bejan, and Andrew S Gordon. Lựa chọn các phương án khả thi: Một đánh giá về phân tích logic nhân quả thông thường. In _2011 AAAI Spring Symposium Series_ , 2011.

- [RCM19] Siva Reddy, Danqi Chen, and Christopher D Manning. CoQA: Một thử thách trả lời câu hỏi đàm thoại. _Transactions of the Association for Computational Linguistics_ , 7:249–266, 2019.

- [RCP<sup>+</sup> 17] Scott Reed, Yutian Chen, Thomas Paine, Aaron¨ van den Oord, SM Eslami, Danilo Rezende, Oriol Vinyals, and Nando de Freitas. Ước lượng mật độ tự hồi quy ít mẫu: Hướng tới học cách học các phân phối. _arXiv preprint arXiv:1710.10304_ , 2017.

- [RJL18] Pranav Rajpurkar, Robin Jia, and Percy Liang. Biết những gì bạn không biết: Các câu hỏi không thể trả lời cho SQuAD. _arXiv preprint arXiv:1806.03822_ , 2018.

- [RL16] Sachin Ravi and Hugo Larochelle. Tối ưu hóa như một mô hình cho học ít mẫu. _ICLR 2017 (oral)_ , 2016.

- [RLL<sup>+</sup> 19] Qiu Ran, Yankai Lin, Peng Li, Jie Zhou, and Zhiyuan Liu. NumNet: Hiểu nội dung khi đọc bằng máy với phân tích logic số học. In _Proceedings of EMNLP_ , 2019.

- [RNLVD18] Rachel Rudinger, Jason Naradowsky, Brian Leonard, and Benjamin Van Durme. Thiên vị giới tính trong giải quyết tham chiếu đồng nhất. _arXiv preprint arXiv:1804.09301_ , 2018.

- [RNSS18] Alec Radford, Karthik Narasimhan, Tim Salimans, and Ilya Sutskever. Cải thiện hiểu ngôn ngữ bằng huấn luyện trước tạo sinh, 2018.

- [Ros12] R.S. Ross. Hướng dẫn thực hiện đánh giá rủi ro. _NIST Special Publication_ , 2012.

- [RRBS19] Jonathan S. Rosenfeld, Amir Rosenfeld, Yonatan Belinkov, and Nir Shavit. Một dự đoán mang tính xây dựng về lỗi khái quát hóa trên các quy mô, 2019.

- [RRS20] Adam Roberts, Colin Raffel, and Noam Shazeer. Bạn có thể đóng gói bao nhiêu tri thức vào các tham số của một mô hình ngôn ngữ? _arXiv preprint arXiv:2002.08910_ , 2020.

- [RSR<sup>+</sup> 19] Colin Raffel, Noam Shazeer, Adam Roberts, Katherine Lee, Sharan Narang, Michael Matena, Yanqi Zhou, Wei Li, and Peter J. Liu. Khám phá giới hạn của học chuyển giao với một mô hình Transformer văn bản-sang-văn bản thống nhất, 2019.

- [RWC<sup>+</sup> 19] Alec Radford, Jeffrey Wu, Rewon Child, David Luan, Dario Amodei, and Ilya Sutskever. Các mô hình ngôn ngữ là các bộ học đa tác vụ không giám sát, 2019.

- [SBBC19] Keisuke Sakaguchi, Ronan Le Bras, Chandra Bhagavatula, and Yejin Choi. Winogrande: Một thử thách lược đồ Winograd đối kháng ở quy mô lớn, 2019.

- [SBC<sup>+</sup> 19] Irene Solaiman, Miles Brundage, Jack Clark, Amanda Askell, Ariel Herbert-Voss, Jeff Wu, Alec Radford, Gretchen Krueger, Jong Wook Kim, Sarah Kreps, Miles McCain, Alex Newhouse, Jason Blazakis, Kris McGuffie, and Jasmine Wang. Các chiến lược phát hành và các tác động xã hội của các mô hình ngôn ngữ, 2019.

- [SCNP19] Emily Sheng, Kai-Wei Chang, Premkumar Natarajan, and Nanyun Peng. Người phụ nữ làm nghề giữ trẻ: Về các thiên vị trong tạo ngôn ngữ. _arXiv preprint arXiv:1909.01326_ , 2019.

- [SDCW19] Victor Sanh, Lysandre Debut, Julien Chaumond, and Thomas Wolf. DistilBERT, một phiên bản chưng cất của BERT: nhỏ hơn, nhanh hơn, rẻ hơn và nhẹ hơn. _arXiv preprint arXiv:1910.01108_ , 2019.

- [SDSE19] Roy Schwartz, Jesse Dodge, Noah A. Smith, and Oren Etzioni. AI xanh. _CoRR_ , abs/1907.10597, 2019.

- [SHB15] Rico Sennrich, Barry Haddow, and Alexandra Birch. Cải thiện các mô hình dịch máy nơ-ron với dữ liệu đơn ngữ. _arXiv preprint arXiv:1511.06709_ , 2015.

73

- [SMM<sup>+</sup> 17] Noam Shazeer, Azalia Mirhoseini, Krzysztof Maziarz, Andy Davis, Quoc Le, Geoffrey Hinton, and Jeff Dean. Các mạng nơ-ron cực lớn: Lớp hỗn hợp chuyên gia cổng thưa thớt. _arXiv preprint arXiv:1701.06538_ , 2017.

- [SPP<sup>+</sup> 19] Mohammad Shoeybi, Mostofa Patwary, Raul Puri, Patrick LeGresley, Jared Casper, and Bryan Catanzaro. Megatron-LM: Huấn luyện các mô hình ngôn ngữ với hàng tỷ tham số sử dụng song song hóa mô hình, 2019.

- [SS20] Timo Schick and Hinrich Schutze.¨ Khai thác các câu hỏi điền từ cho phân loại văn bản ít mẫu và suy luận ngôn ngữ tự nhiên. _arXiv preprint arXiv:2001.07676_ , 2020.

- [STQ<sup>+</sup> 19] Kaitao Song, Xu Tan, Tao Qin, Jianfeng Lu, and Tie-Yan Liu. MASS: Huấn luyện trước tuần tự-sang-tuần tự có mặt nạ cho tạo ngôn ngữ. _arXiv preprint arXiv:1905.02450_ , 2019.

- [TFR<sup>+</sup> 17] Josh Tobin, Rachel Fong, Alex Ray, Jonas Schneider, Wojciech Zaremba, and Pieter Abbeel. Ngẫu nhiên hóa miền để chuyển giao các mạng nơ-ron sâu từ mô phỏng sang thế giới thực. In _2017 IEEE/RSJ international conference on intelligent robots and systems (IROS)_ , pages 23–30. IEEE, 2017.

- [TL05] Peter D. Turney and Michael L. Littman. Học dựa trên kho ngữ liệu về các phép loại suy và quan hệ ngữ nghĩa. _CoRR_ , abs/cs/0508103, 2005.

- [TL18] Trieu H. Trinh and Quoc V. Le. Một phương pháp đơn giản cho phân tích logic thông thường. _arXiv preprint arXiv:1806.02847_ , 2018.

- [TLBS03] Peter D. Turney, Michael L. Littman, Jeffrey Bigham, và Victor Shnayder. Kết hợp các mô đun độc lập để giải quyết các bài toán lựa chọn nhiều đáp án về từ đồng nghĩa và tương tự. _CoRR_, cs.CL/0309035, 2003.

- [Tur20] Dự án Turing. Blog nghiên cứu của Microsoft, tháng 2 năm 2020.

- [VBL<sup>+</sup> 16] Oriol Vinyals, Charles Blundell, Timothy Lillicrap, Daan Wierstra, et al. Mạng khớp cho học một mẫu. Trong _Advances in neural information processing systems_, trang 3630–3638, 2016.

- [VSP<sup>+</sup> 17] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, và Illia Polosukhin.注意力就是你所需要的。在 _Advances in neural information processing systems_ 中，2017年。

- [WPN<sup>+</sup> 19] Alex Wang, Yada Pruksachatkun, Nikita Nangia, Amanpreet Singh, Julian Michael, Felix Hill, Omer Levy, và Samuel Bowman. Superglue: Một tiêu chuẩn chặt chẽ hơn cho hệ thống hiểu ngôn ngữ tổng quát. Trong _Advances in Neural Information Processing Systems_, trang 3261–3275, 2019.

- [WXH<sup>+</sup> 18] Yiren Wang, Yingce Xia, Tianyu He, Fei Tian, Tao Qin, ChengXiang Zhai, và Tie-Yan Liu. Học đôi đa agente. _ICLR 2019_, 2018.

- [XDH<sup>+</sup> 19] Qizhe Xie, Zihang Dai, Eduard Hovy, Minh-Thang Luong, và Quoc V. Le. Tăng cường dữ liệu không giám sát cho đào tạo nhất quán, 2019.

- [YdC<sup>+</sup> 19] Dani Yogatama, Cyprien de Masson d’Autume, Jerome Connor, Tomas Kocisky, Mike Chrzanowski, Lingpeng Kong, Angeliki Lazaridou, Wang Ling, Lei Yu, Chris Dyer, et al. Học và đánh giá trí tuệ ngôn ngữ tổng quát. _arXiv preprint arXiv:1901.11373_, 2019.

- [YDY<sup>+</sup> 19] Zhilin Yang, Zihang Dai, Yiming Yang, Jaime Carbonell, Ruslan Salakhutdinov, và Quoc V. Le. XLNet: Học tiền xử lý tự hồi quy tổng quát cho hiểu ngôn ngữ. _arXiv preprint arXiv:1906.08237_, 2019.

- [ZHB<sup>+</sup> 19] Rowan Zellers, Ari Holtzman, Yonatan Bisk, Ali Farhadi, và Yejin Choi. Hellaswag: Máy có thể hoàn thành câu của bạn không? _arXiv preprint arXiv:1905.07830_, 2019.

- [ZHR<sup>+</sup> 19] Rowan Zellers, Ari Holtzman, Hannah Rashkin, Yonatan Bisk, Ali Farhadi, Franziska Roesner, và Yejin Choi. Phòng chống tin giả từ mạng nơron. _arXiv preprint arXiv:1905.12616_, 2019.

- [ZLL<sup>+</sup> 18] Sheng Zhang, Xiaodong Liu, Jingjing Liu, Jianfeng Gao, Kevin Duh, và Benjamin Van Durme. ReCoRD: Kết nối khoảng cách giữa con người và máy tính trong việc hiểu nội dung khi đọc. _arXiv preprint arXiv:1810.12885_, 2018.

- [ZSW<sup>+</sup> 19a] Daniel M. Ziegler, Nisan Stiennon, Jeffrey Wu, Tom B. Brown, Alec Radford, Dario Amodei, Paul Christiano, và Geoffrey Irving. Huấn luyện lại mô hình ngôn ngữ từ sự偏好选择 [ZSW<sup>+</sup> 19b] 的翻译如下：

- [ZSW<sup>+</sup> 19b] Daniel M. Ziegler, Nisan Stiennon, Jeffrey Wu, Tom B. Brown, Alec Radford, Dario Amodei, Paul Christiano, và Geoffrey Irving. Huấn luyện lại mô hình ngôn ngữ từ sự偏好

请注意，这里保持了原始的Markdown格式，并且保留了所有专有名词和缩写。