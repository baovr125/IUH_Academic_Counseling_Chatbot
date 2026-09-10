<mark>www.nature.com/scientificdata</mark>

![](temp_images/d970e879-521f-416e-9acc-1cd742546f79/input_d970e879-521f-416e-9acc-1cd742546f79.pdf-0001-01.png)

![](temp_images/d970e879-521f-416e-9acc-1cd742546f79/input_d970e879-521f-416e-9acc-1cd742546f79.pdf-0001-02.png)

![](temp_images/d970e879-521f-416e-9acc-1cd742546f79/input_d970e879-521f-416e-9acc-1cd742546f79.pdf-0001-03.png)

![](temp_images/d970e879-521f-416e-9acc-1cd742546f79/input_d970e879-521f-416e-9acc-1cd742546f79.pdf-0001-04.png)

Đã chỉnh sửa: Phụ lục

MỞ

THỂ LOẠI CHỦ ĐỀ

» Dữ liệu nghiên cứu » Đặc điểm xuất bản

Ghi chú: Nguyên tắc hướng dẫn FAIR về quản lý dữ liệu khoa học và bảo quản dữ liệu

Mark D. Wilkinson et al.<sup>#</sup>

Nhận: 10 tháng 12 năm 2015  
Chấp nhận: 12 tháng 2 năm 2016  
Phát hành: 15 tháng 3 năm 2016

Có một nhu cầu cấp bách để cải thiện hạ tầng hỗ trợ việc tái sử dụng dữ liệu học thuật. Một tập hợp đa dạng các bên liên quan - đại diện cho học thuật, doanh nghiệp, cơ quan tài trợ và nhà xuất bản học thuật - đã cùng nhau thiết kế và đồng ý ủng hộ một tập hợp ngắn gọn và đo lường được các nguyên tắc mà chúng tôi gọi là Nguyên tắc Dữ liệu FAIR. Ý định là những nguyên tắc này có thể đóng vai trò như một hướng dẫn cho những ai muốn tăng cường khả năng tái sử dụng của bộ dữ liệu của họ. Khác biệt với các sáng kiến đối tác tập trung vào học giả, Nguyên tắc FAIR đặt trọng tâm cụ thể vào việc tăng cường khả năng của máy tính để tìm kiếm và sử dụng dữ liệu một cách tự động, ngoài ra còn hỗ trợ việc tái sử dụng dữ liệu bởi cá nhân. Bài viết này là lần xuất bản chính thức đầu tiên của Nguyên tắc FAIR, và bao gồm lý do đằng sau chúng, cũng như một số ví dụ thực hiện trong cộng đồng.

Hỗ trợ khám phá thông qua quản lý dữ liệu tốt

Quản lý dữ liệu tốt không phải là mục tiêu cuối cùng, mà là kênh chính dẫn đến khám phá kiến thức và đổi mới, và sau đó tích hợp và tái sử dụng dữ liệu và kiến thức bởi cộng đồng sau quá trình xuất bản dữ liệu. Tiếc thay, hệ sinh thái kỹ thuật số hiện tại xung quanh xuất bản dữ liệu học thuật ngăn cản chúng ta tận dụng tối đa lợi ích từ đầu tư nghiên cứu của mình (ví dụ, xem [1]). Một phần trong phản ứng đối với điều này, các cơ quan tài trợ khoa học, nhà xuất bản và cơ quan chính phủ bắt đầu yêu cầu kế hoạch quản lý dữ liệu và bảo quản dữ liệu cho dữ liệu được tạo ra trong các thí nghiệm được tài trợ công. Ngoài việc thu thập, chú thích và lưu trữ đúng, bảo quản dữ liệu bao gồm khái niệm về 'sự chăm sóc dài hạn' đối với tài sản kỹ thuật số quý giá, với mục tiêu rằng chúng sẽ được phát hiện và tái sử dụng cho các cuộc điều tra tiếp theo, hoặc đơn độc, hoặc kết hợp với dữ liệu mới được tạo ra. Kết quả từ quản lý dữ liệu và bảo quản dữ liệu tốt, do đó, là các tạp chí điện tử chất lượng cao giúp đỡ và đơn giản hóa quy trình khám phá, đánh giá và tái sử dụng liên tục trong các nghiên cứu tiếp theo. Điều gì cấu thành 'quản lý dữ liệu tốt' là, tuy nhiên, chủ yếu chưa được xác định, và thường được để lại như quyết định của chủ sở hữu dữ liệu hoặc kho lưu trữ.

Bài viết này mô tả bốn nguyên tắc cơ bản - Tìm kiếm, Truy cập, Tương tác và Tái sử dụng - phục vụ như hướng dẫn cho các nhà sản xuất và nhà xuất bản dữ liệu khi họ vượt qua những trở ngại này, nhờ đó giúp tối đa hóa giá trị bổ sung thu được từ xuất bản kỹ thuật số học thuật hiện đại. Quan trọng hơn, ý định của chúng tôi là các nguyên tắc áp dụng không chỉ đối với 'dữ liệu' theo nghĩa truyền thống, mà còn đối với các thuật toán, công cụ và quy trình làm việc đã dẫn đến dữ liệu đó. Tất cả các đối tượng nghiên cứu kỹ thuật số học thuật<sup>2</sup> - từ dữ liệu đến các đường dẫn phân tích - đều được hưởng lợi từ việc áp dụng các nguyên tắc này, vì tất cả các thành phần của quy trình nghiên cứu phải có sẵn để đảm bảo minh bạch, tái tạo được và tái sử dụng.

Có nhiều bên liên quan đa dạng sẽ được hưởng lợi từ việc vượt qua những trở ngại này: các nhà nghiên cứu muốn chia sẻ, nhận tín dụng và tái sử dụng dữ liệu và giải thích của nhau; các nhà xuất bản dữ liệu chuyên nghiệp cung cấp dịch vụ của họ; các nhà phát triển phần mềm và công cụ cung cấp các dịch vụ phân tích và xử lý dữ liệu như các quy trình làm việc tái sử dụng; các cơ quan tài trợ (tư nhân và công) ngày càng quan tâm đến việc bảo quản dữ liệu lâu dài; và một cộng đồng khoa học dữ liệu đang khai thác, tích hợp và phân tích dữ liệu mới và hiện tại để thúc đẩy khám phá. Để hỗ trợ việc đọc bài viết này bởi các bên liên quan đa dạng, chúng tôi cung cấp định nghĩa cho các từ viết tắt phổ biến trong hộp 1. Con người, tuy nhiên, không phải là các bên liên quan duy nhất quan trọng trong môi trường dữ liệu khoa học. Các vấn đề tương tự cũng gặp phải bởi các ứng dụng và các đại diện tính toán mà chúng tôi giao nhiệm vụ để thực hiện việc thu thập và phân tích dữ liệu thay mặt chúng tôi. Những 'bên liên quan tính toán' này ngày càng trở nên quan trọng, và đòi hỏi sự chú ý như vậy, hoặc thậm chí nhiều hơn, khi tầm quan trọng của họ tăng lên. Một trong những thách thức lớn của khoa học dựa trên dữ liệu, do đó, là cải thiện khám phá kiến thức thông qua việc hỗ trợ cả con người và các đại diện tính toán của họ trong việc khám phá, truy cập, tích hợp và phân tích dữ liệu khoa học và các đối tượng kỹ thuật số học thuật khác phù hợp với nhiệm vụ.

Dưới đây là phiên bản dịch tiếng Việt của đoạn văn bản Markdown, giữ nguyên cấu trúc Markdown và LaTeX:

Text:
Đối với một số loại đối tượng kỹ thuật số quan trọng, có những kho lưu trữ được quản lý tốt, tích hợp sâu và có mục đích đặc biệt như Genbank<sup>3</sup>, Worldwide Protein Data Bank (wwPDB<sup>4</sup>), và UniProt<sup>5</sup> trong lĩnh vực sinh học; Space Physics Data Facility (SPDF; http://spdf.gsfc.nasa.gov/) và Set of Identifications, Measurements and Bibliography for Astronomical Data (SIMBAD<sup>6</sup>) trong lĩnh vực vật lý vũ trụ. Những nguồn lực nền tảng và quan trọng này đang tiếp tục quản lý và thu thập các tập dữ liệu tham chiếu chất lượng cao, đồng thời cải tiến chúng để nâng cao hiệu suất nghiên cứu học thuật, hỗ trợ cả người dùng và máy móc, và cung cấp nhiều công cụ để truy cập nội dung của họ theo cách phong phú và động. Tuy nhiên, không phải tất cả các tập dữ liệu hoặc thậm chí cả loại dữ liệu đều có thể được thu thập bởi hoặc gửi đến các kho lưu trữ này. Nhiều tập dữ liệu quan trọng xuất phát từ khoa học phòng thí nghiệm truyền thống, có năng suất thấp, không phù hợp với mô hình dữ liệu của các kho lưu trữ mục đích đặc biệt này, nhưng những tập dữ liệu này không kém phần quan trọng đối với nghiên cứu tích hợp, tái tạo và tái sử dụng nói chung. Có vẻ như để đáp ứng điều này, chúng ta thấy sự xuất hiện của nhiều kho lưu trữ dữ liệu đa mục đích, ở quy mô từ cấp tổ chức (ví dụ, một trường đại học duy nhất) đến kho lưu trữ toàn cầu mở như Dataverse<sup>7</sup>, FigShare (http://figshare.com), Dryad<sup>8</sup>, Mendeley Data (https://data.mendeley.com/), Zenodo (http://zenodo.org/), DataHub (http://datahub.io), DANS (http://www.dans.knaw.nl/), và EUDat<sup>9</sup>. Các kho lưu trữ này chấp nhận một loạt các loại dữ liệu khác nhau dưới nhiều định dạng khác nhau, thường không cố gắng tích hợp hoặc hài hoà dữ liệu đã gửi, và đặt ít hạn chế (hoặc yêu cầu) đối với mô tả của việc gửi dữ liệu. Hệ sinh thái dữ liệu kết quả vì vậy dường như đang chuyển hướng khỏi trung tâm hoá, trở nên đa dạng hơn và ít tích hợp hơn, từ đó làm trầm trọng thêm vấn đề khám phá và tái sử dụng dữ liệu cho cả người dùng và máy tính.

Một ví dụ cụ thể về những rào cản này có thể được tưởng tượng trong lĩnh vực điều chỉnh gen và phân tích biểu hiện. Giả sử một nhà nghiên cứu đã tạo ra một tập dữ liệu về các điểm polyadenylation được chọn khác biệt trong một sinh vật bệnh không phải mô hình, được nuôi dưỡng dưới nhiều điều kiện môi trường kích thích trạng thái bệnh của nó. Nhà nghiên cứu quan tâm đến việc so sánh các gen polyadenylation thay thế trong tập dữ liệu cục bộ này với các ví dụ khác về polyadenylation thay thế, và mức độ biểu hiện của các gen này - cả trong sinh vật này và các sinh vật mô hình liên quan - trong quá trình nhiễm trùng. Do đó, không có kho lưu trữ mục đích đặc biệt nào cho dữ liệu polyadenylation khác biệt, và không có cơ sở dữ liệu sinh vật mô hình nào cho sinh vật này, thì nhà nghiên cứu bắt đầu từ đâu?

Chúng tôi sẽ xem xét cách tiếp cận hiện tại cho vấn đề này từ nhiều góc độ khám phá và tích hợp dữ liệu. Nếu các tập dữ liệu mong muốn tồn tại, chúng có thể đã được xuất bản ở đâu, và làm thế nào để bắt đầu tìm kiếm chúng, sử dụng công cụ tìm kiếm nào? Tìm kiếm mong muốn cần phải lọc dựa trên loài cụ thể, mô cụ thể, loại dữ liệu cụ thể (poly-A, microarray, NGS), điều kiện cụ thể (nhiễm trùng), và gen cụ thể - thông tin ('metadata') này có được lưu trữ bởi các kho lưu trữ không, và nếu có, nó ở định dạng nào, có thể tìm kiếm được không, và như thế nào? Một khi dữ liệu được phát hiện, liệu nó có thể được tải xuống không? Trong định dạng nào? Định dạng đó có thể được tích hợp dễ dàng với dữ liệu nội bộ riêng tư (tập dữ liệu cục bộ về điểm polyadenylation thay thế) cũng như các xuất bản dữ liệu từ bên thứ ba và với các kho lưu trữ gen/protein chính của cộng đồng không? Việc tích hợp này có thể

2

SCIENTIFIC DATA | 3:160018 | DOI: 10.1038/sdata.2016.18

<mark>www.nature.com/sdata/</mark>

được thực hiện tự động để tiết kiệm thời gian và tránh lỗi sao chép/cắt dán không? Nhà nghiên cứu có quyền sử dụng dữ liệu từ các nhà nghiên cứu bên thứ ba này không, dưới điều kiện giấy phép nào, và ai nên được trích dẫn nếu một điểm dữ liệu được tái sử dụng?

Những câu hỏi như vậy nhấn mạnh một số rào cản đối với việc khám phá và tái sử dụng dữ liệu, không chỉ cho con người mà còn thậm chí nhiều hơn nữa cho máy móc; tuy nhiên, chính những loại phân tích tích hợp sâu và rộng rãi này mới là phần lớn của e-Science đương đại. Lý do chúng ta thường cần vài tuần (hoặc tháng) của nỗ lực kỹ thuật chuyên môn để thu thập dữ liệu cần thiết để trả lời các câu hỏi nghiên cứu như vậy không phải là thiếu công nghệ phù hợp; lý do là, chúng ta không dành sự chú ý cẩn thận mà chúng đáng được nhận khi chúng ta tạo ra và bảo tồn chúng. Để vượt qua những rào cản này, tất cả các bên liên quan - bao gồm cả nhà nghiên cứu, kho lưu trữ mục đích đặc biệt và kho lưu trữ đa mục đích - cần phát triển để đáp ứng các thách thức nổi lên như trên. Mục tiêu là cho tất cả các loại đối tượng kỹ thuật số học thuật trở thành "thành viên hạng nhất" trong hệ thống xuất bản khoa học, nơi chất lượng của xuất bản - và quan trọng hơn, tác động của xuất bản - là một hàm của khả năng của nó để được tìm thấy chính xác và thích hợp, tái sử dụng và trích dẫn qua thời gian, bởi tất cả các bên liên quan, cả con người và máy móc.

Với mục tiêu này trong tâm trí, một hội thảo đã được tổ chức tại Leyden, Hà Lan, vào năm 2014, mang tên 'Jointly Designing a Data Fairport'. Hội thảo này đã tập hợp một nhóm rộng lớn các bên liên quan học thuật và tư nhân, tất cả đều có mối quan tâm trong việc vượt qua các rào cản khám phá và tái sử dụng dữ liệu. Từ các thảo luận tại hội thảo, khái niệm đã xuất hiện rằng, thông qua việc xác định và ủng hộ rộng rãi một tập hợp tối thiểu các nguyên tắc và thực hành được cộng đồng đồng ý, tất cả các bên liên quan có thể dễ dàng hơn trong việc khám phá, truy cập, tích hợp và tái sử dụng thích hợp, và trích dẫn đầy đủ, lượng lớn thông tin đang được tạo ra bởi khoa học dữ liệu cường độ cao đương đại. Cuộc họp kết thúc với một bản phác thảo của một tập hợp các nguyên tắc cơ bản, sau đó được mở rộng chi tiết hơn - cụ thể là, tất cả các đối tượng nghiên cứu nên là Findable, Accessible, Interoperable và Reusable (FAIR) cho cả máy móc và con người. Những nguyên tắc này hiện được gọi là Nguyên tắc Hướng dẫn FAIR. Sau đó, một nhóm làm việc FAIR chuyên biệt, được thành lập bởi một số thành viên của cộng đồng FORCE11<sup>10</sup>, đã cải thiện và hoàn thiện các Nguyên tắc. Kết quả của những nỗ lực này được báo cáo ở đây.

## Ý nghĩa của máy tính trong môi trường nghiên cứu giàu dữ liệu

Đoạn văn bản Markdown sau đây đã được dịch từ tiếng Anh sang tiếng Việt. Thẻ Markdown và LaTeX được giữ nguyên:

Text:
Việc nhấn mạnh việc áp dụng tính chất FAIR vào cả hoạt động do con người điều khiển lẫn hoạt động do máy móc thực hiện, là một tập trung cụ thể của Nguyên tắc Hướng dẫn FAIR, điều này giúp chúng khác biệt với nhiều sáng kiến đồng đẳng khác (được thảo luận trong phần tiếp theo). Con người và máy móc thường đối mặt với những rào cản riêng biệt khi cố gắng tìm kiếm và xử lý dữ liệu trên Web. Con người có khả năng hiểu được 'tính ngữ nghĩa' (ý nghĩa hoặc mục đích của một đối tượng kỹ thuật số) vì chúng ta có thể nhận biết và giải thích một loạt các dấu hiệu ngữ cảnh, dù đó là dấu hiệu cấu trúc/visual/iconic trong bố cục của một trang Web hay nội dung của các ghi chú kể chuyện. Do đó, chúng ta ít có khả năng mắc lỗi trong việc lựa chọn dữ liệu phù hợp hoặc các đối tượng kỹ thuật số khác, mặc dù con người sẽ gặp khó khăn tương tự nếu thiếu thông tin ngữ cảnh cần thiết. Tuy nhiên, hạn chế chính của con người là chúng ta không thể hoạt động ở phạm vi, quy mô và tốc độ mà dữ liệu khoa học hiện đại đòi hỏi và sự phức tạp của e-Science. Chính vì lý do này mà con người ngày càng phụ thuộc vào các agen tính toán để thực hiện các nhiệm vụ khám phá và tích hợp thay mặt họ. Điều này đòi hỏi máy móc phải có khả năng hành động độc lập và thích hợp khi đối mặt với một loạt các loại, định dạng và phương thức truy cập/giao thức mà chúng sẽ gặp phải trong quá trình khám phá tự hướng dẫn hệ thống dữ liệu toàn cầu. Nó cũng đòi hỏi rằng máy móc phải ghi chép chi tiết về nguồn gốc để dữ liệu mà chúng thu thập có thể được trích dẫn chính xác và đầy đủ. Do đó, hỗ trợ cho các agen này là một yếu tố quan trọng đối với tất cả các bên tham gia trong quá trình quản lý và bảo quản dữ liệu - từ nhà nghiên cứu và người sản xuất dữ liệu đến người chủ trì kho lưu trữ dữ liệu.

Qua toàn bộ bài viết này, chúng tôi sử dụng cụm từ 'thuật toán máy tính' để chỉ một chuỗi các trạng thái có thể xảy ra, nơi mà một đối tượng kỹ thuật số cung cấp thông tin ngày càng chi tiết hơn cho một agen tính toán độc lập đang khám phá dữ liệu. Thông tin này cho phép agen - theo mức độ phụ thuộc vào lượng thông tin chi tiết được cung cấp - có khả năng, khi đối mặt với một đối tượng kỹ thuật số chưa từng gặp trước đây, để: a) xác định loại đối tượng (với cả cấu trúc và mục đích), b) xác định xem nó có hữu ích trong ngữ cảnh của nhiệm vụ hiện tại của agen bằng cách tra cứu thông tin ngữ cảnh và/hoặc các yếu tố dữ liệu, c) xác định xem nó có thể sử dụng được, dựa trên giấy phép, sự chấp thuận hoặc các ràng buộc sử dụng khác, và d) thực hiện hành động thích hợp, theo cùng cách mà con người sẽ làm.

Ví dụ, một máy có thể xác định được loại dữ liệu của một đối tượng kỹ thuật số được phát hiện, nhưng không thể phân tích nó do nó ở định dạng không biết; hoặc nó có thể xử lý dữ liệu chứa đựng, nhưng không thể xác định yêu cầu giấy phép liên quan đến việc truy cập và/hoặc sử dụng dữ liệu đó. Trạng thái tối ưu - nơi mà máy móc hoàn toàn 'hiểu' và có thể hoạt động độc lập và chính xác trên một đối tượng kỹ thuật số - có thể hiếm khi đạt được. Tuy nhiên, các nguyên tắc FAIR cung cấp 'những bước trên con đường' hướng tới khả năng hoạt động của máy tính; việc áp dụng, toàn bộ hoặc một phần, các nguyên tắc FAIR

3

SCIENTIFIC DATA | 3:160018 | DOI: 10.1038/sdata.2016.18

<mark>www.nature.com/sdata/</mark>

![](temp_images/d970e879-521f-416e-9acc-1cd742556f79/input_d970e879-521f-416e-9acc-1cd742556f79.pdf-0004-01.png)

<!-- Start of picture text -->
Box 2 | Nguyên tắc Hướng dẫn FAIR<br>Để có thể Tìm thấy:<br>F1. (meta)data được gán một định danh toàn cầu duy nhất và bền vững<br>F2. dữ liệu được mô tả với metadata phong phú (được định nghĩa bởi R1 dưới đây)<br>F3. metadata rõ ràng và cụ thể bao gồm định danh của dữ liệu mà nó mô tả<br>F4. (meta)data được đăng ký hoặc lập chỉ mục trong một nguồn lực có thể tìm kiếm<br>Để có thể Truy cập:<br>A1. (meta)data có thể truy hồi bằng định danh của chúng thông qua một giao thức giao tiếp chuẩn<br>A1.1 giao thức này mở, miễn phí và có thể triển khai rộng rãi<br>A1.2 giao thức cho phép quy trình xác thực và ủy quyền, khi cần thiết<br>A2. metadata có thể truy cập, ngay cả khi dữ liệu không còn tồn tại<br>Để có thể Tương tác:<br>I1. (meta)data sử dụng một ngôn ngữ chính thức, có thể truy cập, chia sẻ và áp dụng rộng rãi cho việc biểu diễn kiến thức.<br>I2. (meta)data sử dụng từ vựng tuân thủ nguyên tắc FAIR<br>I3. (meta)data bao gồm tham chiếu được đánh giá đối với (meta)data khác<br>Để có thể Sử dụng lại:<br>R1. meta(data) được mô tả phong phú với nhiều đặc điểm chính xác và liên quan<br>R1.1. (meta)data được phát hành với giấy phép sử dụng dữ liệu rõ ràng và dễ tiếp cận<br>R1.2. (meta)data được liên kết với lịch sử nguồn gốc chi tiết<br>R1.3. (meta)data đáp ứng tiêu chuẩn cộng đồng liên quan

<!-- End of picture text -->

áp dụng nguyên tắc FAIR, dẫn dắt nguồn lực đi theo chuỗi liên tục hướng tới trạng thái tối ưu này. Ngoài ra, khái niệm về khả năng hoạt động của máy tính áp dụng trong hai ngữ cảnh - đầu tiên, khi đề cập đến metadata ngữ cảnh xung quanh một đối tượng kỹ thuật số ('đó là gì?'), và thứ hai, khi đề cập đến nội dung của đối tượng kỹ thuật số đó ('tôi sẽ xử lý nó như thế nào/tích hợp nó như thế nào?'). Có thể cả hai hoặc cả hai đều có thể hoạt động theo cách của máy tính, và mỗi yếu tố tạo thành một liên tục riêng của khả năng hoạt động.

Cuối cùng, chúng tôi muốn phân biệt giữa dữ liệu có thể hoạt động theo cách của máy tính do đầu tư cụ thể vào phần mềm hỗ trợ loại dữ liệu đó, ví dụ như các trình phân tích tùy chỉnh hiểu tệp wwPDB khoa học đời sống hoặc tệp SPASE khoa học vũ trụ, và dữ liệu có thể hoạt động theo cách của máy tính chỉ thông qua việc sử dụng công nghệ tổng quát, mở. Để nhắc lại điểm trước đây - khả năng hoạt động cuối cùng của máy tính xảy ra khi một máy có thể đưa ra quyết định hữu ích về dữ liệu mà nó chưa từng gặp trước đây. Sự phân biệt này quan trọng khi cân nhắc cả (a) môi trường dữ liệu đang phát triển và tiến hóa nhanh chóng, với các công nghệ mới và các loại dữ liệu mới, phức tạp hơn liên tục được phát triển, và (b) sự tăng trưởng của các kho lưu trữ tổng quát, nơi mà các loại dữ liệu có thể được gặp bởi một agen là không thể dự đoán. Tạo ra các trình phân tích tùy chỉnh, trong tất cả các ngôn ngữ máy tính, cho tất cả các loại dữ liệu và tất cả các công cụ phân tích yêu cầu loại dữ liệu đó, không phải là một hoạt động bền vững. Do đó, việc tập trung vào việc hỗ trợ máy tính trong việc khám phá và khám phá dữ liệu thông qua việc áp dụng công nghệ và tiêu chuẩn tương tác tổng quát hơn ở cấp độ dữ liệu/kho lưu trữ trở thành ưu tiên hàng đầu cho việc bảo quản dữ liệu tốt.

## Chi tiết về Nguyên tắc Hướng dẫn FAIR

Dẫn xuất:
Đại diện của các nhóm bên liên quan quan tâm đã tập trung vào bốn mục tiêu cốt lõi – Nguyên tắc hướng dẫn FAIR – và giới thiệu chi tiết về chúng, đã được tinh chỉnh (Hộp 2) từ bản nháp ban đầu của cuộc họp, có thể truy cập tại (https://www.force11.org/node/6062). Một tài liệu riêng biệt đang được xây dựng một cách động lực để đáp ứng thảo luận cộng đồng liên quan đến việc làm rõ và giải thích các nguyên tắc, cũng như hướng dẫn chi tiết và ví dụ về việc thực hiện FAIR, hiện đang được xây dựng (http://datafairport.org/fair-principles-living-document-menu). Nguyên tắc hướng dẫn FAIR mô tả những cân nhắc riêng biệt cho môi trường xuất bản dữ liệu hiện đại với sự hỗ trợ cho cả việc nộp dữ liệu bằng tay và tự động, khám phá, chia sẻ và tái sử dụng. Trong khi đã có nhiều xuất bản gần đây, thường tập trung vào lĩnh vực cụ thể, ủng hộ cải thiện cụ thể về thực hành quản lý dữ liệu và lưu trữ<sup>1,11,12</sup>, FAIR khác biệt ở chỗ nó mô tả những nguyên tắc ngắn gọn, độc lập với lĩnh vực, cấp cao mà có thể áp dụng cho một loạt rộng rãi các sản phẩm nghiên cứu học thuật. Qua nguyên tắc, chúng tôi sử dụng cụm từ ‘(thông tin) dữ liệu’ trong các trường hợp mà nguyên tắc nên được áp dụng cho cả thông tin dữ liệu và dữ liệu.

Các yếu tố của Nguyên tắc FAIR có liên quan nhưng độc lập và có thể tách rời. Các nguyên tắc định nghĩa các đặc điểm mà các nguồn dữ liệu hiện đại, công cụ, từ vựng và hạ tầng nên thể hiện để hỗ trợ khám phá và tái sử dụng bởi các bên thứ ba. Bằng cách định nghĩa tối thiểu mỗi nguyên tắc hướng dẫn, rào cản để tiếp cận đối với người sản xuất, nhà xuất bản và bảo quản dữ liệu muốn làm cho dữ liệu của họ trở thành FAIR được duy trì cố tình ở mức thấp nhất có thể. Các nguyên tắc có thể tuân thủ theo bất kỳ kết hợp nào và tăng dần, khi môi trường xuất bản của người cung cấp dữ liệu phát triển đến mức độ ngày càng tăng của ‘FAIRness’. Hơn nữa, tính mô-đun của các nguyên tắc, và sự phân biệt giữa dữ liệu và thông tin dữ liệu, rõ ràng hỗ trợ một loạt rộng rãi các trường hợp đặc biệt. Một ví dụ như vậy là dữ liệu nhạy cảm cao hoặc có thể xác định cá nhân, nơi xuất bản thông tin dữ liệu phong phú để hỗ trợ khám phá, bao gồm quy tắc rõ ràng về quá trình truy cập dữ liệu, cung cấp mức độ cao của ‘FAIRness’ ngay cả khi không có xuất bản FAIR của dữ liệu chính nó. Một ví dụ khác liên quan đến việc xuất bản

4

SCIENDATA | 3:160018 | DOI: 10.1038/sdata.2016.18

<mark>www.nature.com/sdata/</mark>

của các đối tượng nghiên cứu không phải dữ liệu. Workflow phân tích, ví dụ, là một thành phần quan trọng của hệ sinh thái học thuật, và việc xuất bản chính thức của chúng là cần thiết để đạt được cả minh bạch và khả năng tái tạo khoa học. Các nguyên tắc FAIR có thể được áp dụng tương tự đối với các tài sản không phải dữ liệu này, cần được xác định, mô tả, khám phá và tái sử dụng theo cùng một cách như dữ liệu.

Các nỗ lực biểu diễn cụ thể cung cấp các mức độ khác nhau của FAIRness được chi tiết sau trong tài liệu này. Tuy nhiên, vẫn còn một số vấn đề cần được giải quyết. Đầu tiên, khi từ vựng được chấp nhận bởi cộng đồng hoặc các chuẩn (meta)data khác không bao gồm các thuộc tính cần thiết để đạt được chú thích phong phú, có hai giải pháp có thể: hoặc xuất bản mở rộng của một từ vựng hiện có, gần gũi liên quan, hoặc - trong trường hợp cực đoan - tạo ra và xuất bản rõ ràng một nguồn từ vựng mới, theo nguyên tắc FAIR ('I2'). Thứ hai, để xác định rõ chuẩn được chọn khi có hơn một từ vựng hoặc chuẩn (meta)data khác có sẵn, và cho rằng ví dụ trong khoa học đời sống có hơn 600 chuẩn nội dung, đăng ký BioSharing (https://biosharing.org/) có thể hữu ích vì nó mô tả các chuẩn chi tiết, bao gồm phiên bản nếu có.

## Nguyên tắc trước khi thực hiện

Những nguyên tắc FAIR cấp cao này trước lựa chọn thực hiện, và không đề xuất bất kỳ công nghệ cụ thể, chuẩn, hoặc giải pháp thực hiện; hơn nữa, nguyên tắc không phải là một chuẩn hoặc một thông số kỹ thuật. Chúng hoạt động như một hướng dẫn cho nhà xuất bản và bảo quản dữ liệu để giúp họ đánh giá liệu lựa chọn thực hiện cụ thể của họ có làm cho các tác phẩm nghiên cứu kỹ thuật số của họ dễ tìm kiếm, truy cập, tương tác và tái sử dụng hay không. Chúng tôi dự đoán rằng những nguyên tắc cấp cao này sẽ cho phép một loạt rộng rãi các hành vi tích hợp và khám phá dựa trên một loạt rộng rãi lựa chọn công nghệ và thực hiện. Thật vậy, nhiều kho lưu trữ đã bắt đầu thực hiện các khía cạnh khác nhau của FAIR sử dụng một loạt các lựa chọn công nghệ và một số ví dụ được chi tiết trong phần tiếp theo; ví dụ bao gồm SCIENDATA chính nó và cách các bài viết dữ liệu câu chuyện được gắn vào một cấu trúc metadata FAIR ngày càng tiến bộ.

## Ví dụ về FAIRness, và giá trị bổ sung kết quả

Dataverse<sup>7</sup>: Dataverse là phần mềm kho dữ liệu nguồn mở được cài đặt tại hàng chục tổ chức trên toàn cầu để hỗ trợ các kho dữ liệu cộng đồng công khai hoặc kho dữ liệu nghiên cứu của tổ chức. Harvard Dataverse với hơn 60.000 bộ dữ liệu là kho dữ liệu lớn nhất hiện nay và mở cửa cho tất cả các nhà nghiên cứu từ mọi lĩnh vực nghiên cứu. Dataverse tạo ra một trích dẫn chính thức cho mỗi khoản đóng góp, tuân theo tiêu chuẩn do Altman và King<sup>13</sup> đề xuất. Dataverse công bố Mã định danh Đối tượng Số hóa (DOI) hoặc các định danh bền vững khác (Handles) khi bộ dữ liệu được xuất bản ('F'). Điều này dẫn đến trang đích, cung cấp quyền truy cập vào thông tin mô tả, tệp dữ liệu, điều khoản bộ dữ liệu, giấy phép hoặc miễn trừ, và thông tin phiên bản, tất cả đều được lập chỉ mục và tìm kiếm ('F', 'A' và 'R'). Các khoản đóng góp bao gồm thông tin mô tả, tệp dữ liệu và bất kỳ tệp bổ sung nào (như tài liệu hoặc mã) cần thiết để hiểu dữ liệu và phân tích ('R'). Thông tin mô tả luôn công khai, ngay cả khi dữ liệu bị hạn chế hoặc loại bỏ vì vấn đề bảo mật ('F', 'A'). Thông tin mô tả này được cung cấp ở ba cấp độ, hỗ trợ rộng rãi các nguyên tắc 'I' và 'R' FAIR: 1) thông tin mô tả trích dẫn dữ liệu, tương ứng với lược đồ DataCite hoặc các thuật ngữ Dublin Core, 2) thông tin mô tả cụ thể lĩnh vực, khi có thể tương ứng với các tiêu chuẩn thông tin mô tả được sử dụng trong một lĩnh vực khoa học, và 3) thông tin mô tả cấp tệp, có thể sâu và rộng rãi đối với các tệp dữ liệu bảng (bao gồm thông tin mô tả cấp cột). Cuối cùng, Dataverse cung cấp các giao diện máy tính công khai để tìm kiếm dữ liệu, truy cập thông tin mô tả và tải xuống tệp dữ liệu, sử dụng một token để cấp quyền truy cập khi tệp dữ liệu bị hạn chế ('A').

FAIRDOM (http://fair-dom.org/about): tích hợp các nền tảng SEEK<sup>14</sup> và openBIS<sup>15</sup> để tạo ra một cơ sở hạ tầng quản lý dữ liệu và mô hình FAIR cho Sinh học Hệ thống. Các tài sản nghiên cứu riêng lẻ (hoặc tập hợp dữ liệu và mô hình) được xác định bằng các URL HTTP duy nhất và bền vững, có thể đăng ký với DOI để xuất bản ('F'). Các tài sản có thể được truy cập qua Web dưới nhiều định dạng phù hợp với cá nhân và/hoặc máy tính của họ (RDF, XML) ('I'). Các tài sản nghiên cứu được gắn nhãn với thông tin mô tả phong phú, sử dụng các chuẩn, định dạng và ontology cộng đồng ('I'). Thông tin mô tả được lưu trữ dưới dạng RDF để cho phép khả năng tương tác và các tài sản có thể được tải xuống để tái sử dụng ('R').

ISA<sup>16</sup>: là khung theo dõi thông tin mô tả cộng đồng hướng dẫn để thúc đẩy việc thu thập, quản lý, curation và tái sử dụng các bộ dữ liệu khoa học đời sống theo chuẩn. ISA cung cấp thông tin mô tả cấu trúc tiến tới FAIR cho các bài viết Descriptors dữ liệu của Nature Scientific Data và nhiều bài báo dữ liệu của GigaScience, và hỗ trợ cơ sở dữ liệu MetaboLights của EBI và các nguồn dữ liệu khác. Trái tim của nó là một mô hình ISA tổng quát, mở rộng, ban đầu chỉ có sẵn dưới dạng biểu diễn bảng nhưng sau đó được cải thiện dưới dạng biểu diễn RDF<sup>17</sup>, và các serializations JSON để cho phép 'I' và 'R', trở thành 'FAIR' khi được xuất bản dưới dạng dữ liệu liên kết (http://elixir-uk.org/node-events/201cisa-as-afair-research-object201d-hack-the-spec-event-1) và bổ sung các đối tượng nghiên cứu khác<sup>18</sup>.

Open PHACTS<sup>19</sup>: Open PHACTS là một nền tảng tích hợp dữ liệu dành cho thông tin liên quan đến khám phá thuốc. Truy cập vào nền tảng được trung gian thông qua một giao diện máy tính công khai<sup>20</sup> cung cấp nhiều biểu diễn vừa đọc được bởi con người (HTML) và máy tính (RDF, JSON, XML, CSV, v.v.), cung cấp khía cạnh 'A' của FAIR.

wwPDB<sup>4,21</sup>: wwPDB là kho lưu trữ dữ liệu đặc biệt, được chăm sóc kỹ lưỡng, chứa thông tin về cấu trúc 3 chiều của protein và axit nucleic được xác định bởi thí nghiệm.

## FAIRness là điều kiện tiên quyết cho quản lý dữ liệu và bảo quản dữ liệu đúng đắn

Những ý tưởng trong Nguyên tắc hướng dẫn FAIR phản ánh, kết hợp, xây dựng dựa trên và mở rộng công việc trước đó của cả Liên minh Web Khái niệm (https://conceptweblog.wordpress.com/) - những đối tác tập trung vào khả năng thực hiện của máy móc và sự hài hoà của cấu trúc dữ liệu và ngữ nghĩa, cũng như của các tổ chức khoa học và học thuật đã phát triển Tuyên bố chung về Nguyên tắc trích dẫn dữ liệu (JDDCP<sup>29</sup>),

6

SCIENTIFIC DATA | 3:160018 | DOI: 10.1038/sdata.2016.18

<mark>www.nature.com/sdata/</mark>

đối tác tập trung vào việc làm cho dữ liệu học thuật chính yếu trở nên có thể trích dẫn, tìm thấy và tái sử dụng, nhằm mục đích hỗ trợ học thuật nghiêm túc hơn. Một nỗ lực định rõ sự tương đồng và chồng lấn giữa Nguyên tắc FAIR và JDDCP được cung cấp tại (https://www.force11.org/node/ 6062). Nguyên tắc FAIR cũng bổ sung cho 'Biểu trưng chấp thuận dữ liệu' (DSA) (http://datasealofapproval.org/media/filer_public/2013/09/27/guidelines_2014-2015.pdf) ở chỗ chúng chia sẻ mục tiêu tổng quát là làm cho dữ liệu có thể tái sử dụng cho người dùng khác ngoài những người đã tạo ra chúng. Trong khi DSA tập trung chủ yếu vào trách nhiệm và hành vi của nhà sản xuất dữ liệu và kho lưu trữ, FAIR tập trung chủ yếu vào dữ liệu chính nó. Rõ ràng, cộng đồng rộng lớn các bên liên quan đang tụ họp xung quanh một tập hợp các tầm nhìn chung, đồng bộ hoá, trải dài qua tất cả các khía cạnh của hệ thống xuất bản dữ liệu học thuật.

Kết quả cuối cùng, khi được thực hiện, sẽ là quản lý và bảo quản dữ liệu này tốt hơn, mang lại lợi ích cho toàn bộ cộng đồng học thuật. Như đã đề cập ở đầu, quản lý dữ liệu và bảo quản dữ liệu tốt không phải là mục tiêu tự thân, mà là điều kiện tiên quyết hỗ trợ khám phá và đổi mới kiến thức. Khoa học điện tử đương đại đòi hỏi dữ liệu phải là Findable (tìm thấy), Accessible (truy cập được), Interoperable (tương thích), và Reusable (tái sử dụng) trong dài hạn, và những mục tiêu này đang dần trở thành kỳ vọng của các cơ quan và nhà xuất bản. Chúng tôi chứng minh rằng Nguyên tắc dữ liệu FAIR cung cấp một loạt các dấu mốc cho nhà sản xuất dữ liệu và nhà xuất bản. Chúng hướng dẫn việc thực hiện các mức độ cơ bản nhất của quản lý dữ liệu và bảo quản dữ liệu tốt, do đó giúp các nhà nghiên cứu tuân thủ kỳ vọng và yêu cầu của các cơ quan tài trợ. Chúng tôi kêu gọi tất cả nhà sản xuất dữ liệu và nhà xuất bản hãy xem xét và thực hiện các nguyên tắc này, và tích cực tham gia với sáng kiến FAIR bằng cách gia nhập nhóm làm việc của Force11. Bằng cách làm việc cùng nhau hướng tới các mục tiêu chung, dữ liệu quý giá do cộng đồng chúng ta tạo ra sẽ dần đạt được các mục tiêu then chốt của FAIRness.

# Tham khảo

Text:

1. Roche, D. G., Kruuk, L. E. B., Lanfear, R. & Binning, S. A. Lưu trữ dữ liệu công khai trong sinh thái và tiến hóa: Chúng ta đang làm tốt đến đâu? PLOS Biol. 13, e1002295 (2015).

2. Bechhofer, S. et al. Đối tượng nghiên cứu: Hướng tới việc trao đổi và tái sử dụng kiến thức kỹ thuật số. Nat. Preced. doi:10.1038/npre.2010.4626.1 (2010).

3. Benson, D. A. et al. GenBank. Nucleic Acids Res. 41, D36–D42 (2013).

4. Berman, H., Henrick, K. & Nakamura, H. Thông báo về Protein Data Bank toàn cầu. Nat. Struct. Biol. 10, 980–980 (2003).

5. The Uniprot Consortium. UniProt: một trung tâm thông tin cho protein. Nucleic Acids Res. 43, D204–D212 (2015).

6. Wenger, M. et al. Cơ sở dữ liệu thiên văn học SIMBAD - Cơ sở dữ liệu tham chiếu của CDS cho đối tượng thiên văn học. Astron. Astrophys. Suppl. Ser. 143, 9–22 (2000).

7. Crosas, M. "The Dataverse Network<sup>®</sup>: Một ứng dụng nguồn mở để chia sẻ, khám phá và bảo tồn dữ liệu". D-Lib Mag 17 (1), trang 2 (2011).

8. White, H. C., Carrier, S., Thompson, A., Greenberg, J. & Scherle, R. Trung tâm dữ liệu Dryad: Một kiến trúc metadata Singapore trong môi trường DSpace. Univ. Göttingen, trang 157 (2008).

9. Lecarpentier, D. et al. EUDAT: Một cơ sở dữ liệu đa ngành mới cho khoa học. Int. J. Digit. Curation 8, 279–287 (2013).

10. Martone, M. E. FORCE11: Xây dựng tương lai cho giao tiếp nghiên cứu và e-scholarship. Bioscience 65, 635 (2015).

11. White, E. et al. Chín cách đơn giản để làm cho việc sử dụng dữ liệu trở nên dễ dàng hơn. Ideas Ecol. Evol. 6 (2013).

12. Sandve, G. K., Nekrutenko, A., Taylor, J. & Hovig, E. Mười quy tắc đơn giản cho nghiên cứu tính toán có thể tái tạo. PLoS Comput. Biol. 9, e1003285 (2013).

13. Altman, M. & King, G. trong D-Lib Magazine 13, số 3/4 (2007).

14. Wolstencroft, K. et al. SEEK: một nền tảng quản lý dữ liệu và mô hình hệ sinh học. BMC Syst. Biol. 9, 33 (2015).

15. Bauch, A. et al. openBIS: một khung linh hoạt để quản lý và phân tích dữ liệu phức tạp trong nghiên cứu sinh học. BMC Bioinformatics 12, 468 (2011).

16. Sansone, S.-A. et al. Hướng tới sự tương tác giữa dữ liệu sinh học. Nat. Genet. 44, 121–126 (2012).

17. González-Beltrán, A., Maguire, E., Sansone, S.-A. & Rocca-Serra, P. linkedISA: biểu diễn ngữ nghĩa của metadata ISA-Tab. BMC Bioinformatics 15, S4 (2014).

18. González-Beltrán, A. et al. Từ peer-reviewed đến peer-reproduced trong xuất bản học thuật: vai trò bổ sung của các mô hình dữ liệu và quy trình làm việc trong sinh học tính toán. PLoS ONE 10, e0127612 (2015).

19. Harland, L. Open PHACTS: Một kiến trúc tri thức liên kết cho nghiên cứu phát hiện thuốc công cộng và thương mại. Knowl. Eng. Knowl. Manag. Lect. Notes Comput. Sci. 7603/2012, 1–7 (2012).

20. Groth, P. et al. API-centric Linked Data integration: Trường hợp nghiên cứu của Discovery Platform Open PHACTS. Web Semant. Sci. Serv. Agents World Wide Web 29, 12–18 (2014).

21. Berman, H. M. et al. Protein Data Bank. Nucleic Acids Res. 28, 235–242 (2000).

22. Bourne, P. E., Berman, H. M., Watenpaugh, K., Westbrook, J. D. & Fitzgerald, P. M. D. Macromolecular Crystallographic Information File (mmCIF). Meth. Enzym 277, 571–590 (1997).

23. Rose, P. W. et al. RCSB Protein Data Bank: nhìn nhận về sinh học phân tử cho nghiên cứu cơ bản và áp dụng, và giáo dục. Nucleic Acids Res.

**Lợi ích tài chính cạnh tranh:** M.A. là Tổng biên tập của Nature Genetics; S.A.S. là Học giả danh dự và cố vấn học thuật của Scientific Data.

**Cách trích dẫn bài viết này:** Wilkinson, M. D. et al. Nguyên tắc hướng dẫn FAIR cho quản lý dữ liệu khoa học và bảo quản dữ liệu. Sci. Data 3:160018 doi: 10.1038/sdata.2016.18 (2016).

Bài viết này được cấp phép theo Giấy phép Creative Commons Attribution 4.0 Quốc tế. Các hình ảnh hoặc vật liệu khác của bên thứ ba trong bài viết này được bao gồm trong giấy phép Creative Commons của bài viết, trừ khi được chỉ rõ khác trong thông tin tín dụng; nếu vật liệu không được bao gồm trong giấy phép Creative Commons, người dùng sẽ cần phải nhận được sự cho phép từ chủ sở hữu giấy phép để tái sản xuất vật liệu đó. Để xem một bản sao của giấy phép này, hãy truy cập http://creativecommons.org/licenses/by/4.0

Mark D. Wilkinson<sup>1</sup> , Michel Dumontier<sup>2</sup> , IJsbrand Jan Aalbersberg<sup>3</sup> , Gabrielle Appleton<sup>3</sup> , Myles Axton<sup>4</sup> , Arie Baak<sup>5</sup> , Niklas Blomberg<sup>6</sup> , Jan-Willem Boiten<sup>7</sup> , Luiz Bonino da Silva Santos<sup>8</sup> , Philip E. Bourne<sup>9</sup> , Jildau Bouwman<sup>10</sup> , Anthony J. Brookes<sup>11</sup> , Tim Clark<sup>12</sup> , Mercè Crosas<sup>13</sup> , Ingrid Dillo<sup>14</sup> , Olivier Dumon<sup>3</sup> , Scott Edmunds<sup>15</sup> , Chris T. Evelo<sup>16</sup> , Richard Finkers<sup>17</sup> , Alejandra Gonzalez-Beltran<sup>18</sup> , Alasdair J.G. Gray<sup>19</sup> , Paul Groth<sup>3</sup> , Carole Goble<sup>20</sup> , Jeffrey S. Grethe<sup>21</sup> , Jaap Heringa<sup>22</sup> , Peter A.C. ’t Hoen<sup>23</sup> , Rob Hooft<sup>24</sup> , Tobias Kuhn<sup>25</sup> , Ruben Kok<sup>22</sup> , Joost Kok<sup>26</sup> , Scott J. Lusher<sup>27</sup> , Maryann E. Martone<sup>28</sup> , Albert Mons<sup>29</sup> , Abel L. Packer<sup>30</sup> , Bengt Persson<sup>31</sup> , Philippe Rocca-Serra<sup>18</sup> , Marco Roos<sup>32</sup> , Rene van Schaik<sup>33</sup> , Susanna-Assunta Sansone<sup>18</sup> , Erik Schultes<sup>34</sup> , Thierry Sengstag<sup>35</sup> , Ted Slater<sup>36</sup> , George Strawn<sup>37</sup> , Morris A. Swertz<sup>38</sup> , Mark Thompson<sup>32</sup> , Johan van der Lei<sup>39</sup> , Erik van Mulligen<sup>39</sup> , Jan Velterop<sup>40</sup> , Andra Waagmeester<sup>41</sup> , Peter Wittenburg<sup>42</sup> , Katherine Wolstencroft<sup>43</sup> , Jun Zhao<sup>44</sup> & Barend Mons<sup>45,46,47</sup>

> 1Trung tâm Công nghệ Sinh học và Di truyền học, Universidad Politécnica de Madrid, Madrid 28223, Tây Ban Nha.

> 2Đại học Stanford, Stanford 94305-5411, Hoa Kỳ. 3Elsevier, Amsterdam 1043 NX, Hà Lan. 4Nature Genetics, New York 10004-1562, Hoa Kỳ.<sup>5</sup> Euretos và Phortos Consultants, Rotterdam 2741 CA, Hà Lan.