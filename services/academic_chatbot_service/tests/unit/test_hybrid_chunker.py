import pytest
from app.data_ingestion.chunkers.hybrid_chunker import HybridChunker

class TestHybridChunkerParentSizingAndHeadings:
    """Kiểm tra logic phân tách Parent Chunks với 1 tham số duy nhất max_parent_tokens (mặc định 1200)."""

    def test_default_parameter_is_1200_tokens(self):
        """Xác nhận giá trị mặc định của HybridChunker là max_parent_tokens = 1200."""
        chunker = HybridChunker()
        assert chunker.max_parent_tokens == 1200

    def test_normal_document_under_limit_keeps_primary_sections(self):
        """
        Tài liệu dưới 1200 tokens KHÔNG bị tách bởi secondary regex,
        ngay cả khi nội dung có chứa số La Mã hoặc in đậm (**I. ...**, **1. ...**).
        """
        chunker = HybridChunker(max_parent_tokens=1200)
        
        doc = (
            "# QUY CHẾ ĐÀO TẠO\n\n"
            "**I. Nguyên tắc chung**\n"
            "Nội dung nguyên tắc chung ngắn gọn.\n\n"
            "**II. Đối tượng tuyển sinh**\n"
            "Nội dung đối tượng tuyển sinh ngắn gọn.\n"
        )
        metadata = {"source_url": "https://camnang.iuh.edu.vn/quy-che"}

        parents = chunker.extract_parent_chunks(doc, metadata)

        # Do tổng độ dài << 1200 tokens, toàn bộ phần sau '# QUY CHẾ ĐÀO TẠO'
        # được giữ nguyên làm 1 parent chunk duy nhất, không kích hoạt secondary regex!
        assert len(parents) == 1
        assert parents[0]["metadata"]["headers"] == ["# QUY CHẾ ĐÀO TẠO"]
        assert "**I. Nguyên tắc chung**" in parents[0]["text"]
        assert "**II. Đối tượng tuyển sinh**" in parents[0]["text"]

    def test_oversized_section_exceeding_token_limit_triggers_secondary_regex(self):
        """
        Section vượt quá max_parent_tokens sẽ kích hoạt secondary regex để tách theo
        các tiêu đề in đậm số La Mã / số thứ tự (**I. ...**, **II. ...**).
        """
        chunker = HybridChunker(max_parent_tokens=100)  # Hạ ngưỡng để test
        
        # Mỗi body khoảng 48 từ, cộng tiêu đề ~55 từ (< 100). Nhưng tổng doc ~120 từ > 100 tokens.
        body_1 = "Quy định chi tiết mục 1. " * 8
        body_2 = "Quy định chi tiết mục 2. " * 8
        
        doc = (
            "Thông tin mở đầu tuyển sinh.\n\n"
            "**I. Nguyên tắc chung**\n"
            f"{body_1}\n\n"
            "**II. Đối tượng tuyển sinh**\n"
            f"{body_2}\n"
        )
        metadata = {"source_url": "https://tuyensinh.iuh.edu.vn/nganhDaoTao"}

        parents = chunker.extract_parent_chunks(doc, metadata)

        # Do tổng doc vượt ngưỡng 100 tokens, secondary regex được kích hoạt và tách thành 3 phần:
        # Preamble, Section I, Section II
        assert len(parents) == 3
        headers_found = [p["metadata"]["headers"] for p in parents]
        assert ["**I. Nguyên tắc chung**"] in headers_found
        assert ["**II. Đối tượng tuyển sinh**"] in headers_found

    def test_oversized_section_without_secondary_headings_triggers_paragraph_fallback(self):
        """
        Section vượt quá ngưỡng token nhưng KHÔNG có secondary headings nào
        sẽ tự động kích hoạt Fallback Chunking theo đoạn văn (\\n\\n),
        đảm bảo mỗi sub-parent chunk <= max_parent_tokens.
        """
        chunker = HybridChunker(max_parent_tokens=60)
        
        # 4 đoạn văn, mỗi đoạn dài 30 từ (tổng ~120 từ > 60 tokens)
        para1 = "Đoạn văn thứ nhất nói về quy chế thi cử và điểm chuẩn. " * 3
        para2 = "Đoạn văn thứ hai nói về điều kiện tốt nghiệp và ngoại ngữ. " * 3
        para3 = "Đoạn văn thứ ba nói về học phí và chính sách miễn giảm. " * 3
        
        doc = f"{para1}\n\n{para2}\n\n{para3}"
        metadata = {"source_url": "https://tuyensinh.iuh.edu.vn/diemChuan"}

        parents = chunker.extract_parent_chunks(doc, metadata)

        # Vì không có heading in đậm nào, fallback bẻ theo \n\n
        assert len(parents) >= 2
        for p in parents:
            assert chunker.estimate_tokens(p["text"]) <= 60

    def test_sub_section_still_oversized_after_secondary_regex_is_paragraph_chunked(self):
        """
        Nếu một mục con sau khi tách bằng secondary regex vẫn vượt quá max_parent_tokens,
        nó sẽ tiếp tục được bẻ nhỏ theo đoạn văn để đảm bảo trần max_parent_tokens.
        """
        chunker = HybridChunker(max_parent_tokens=50)
        
        # Mỗi đoạn ~24 từ + header 5 từ = ~29 từ <= 50 tokens.
        # Nhưng cả mục I = ~53 từ > 50 tokens nên sẽ được tách thành 2 sub-parents.
        sub_para1 = "Nội dung phần 1 của mục I rất dài và chi tiết. " * 2
        sub_para2 = "Nội dung phần 2 của mục I cũng rất dài và chi tiết. " * 2
        
        doc = (
            "**I. Nguyên tắc chung**\n"
            f"{sub_para1}\n\n"
            f"{sub_para2}\n"
        )
        metadata = {"source_url": "https://tuyensinh.iuh.edu.vn/nganhDaoTao"}

        parents = chunker.extract_parent_chunks(doc, metadata)

        # Mục I bị dài hơn 50 tokens nên được chia nhỏ tiếp theo đoạn văn
        assert len(parents) == 2
        for p in parents:
            assert "**I. Nguyên tắc chung**" in p["metadata"]["headers"]
            assert chunker.estimate_tokens(p["text"]) <= 50
