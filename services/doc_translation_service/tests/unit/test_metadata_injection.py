import pytest
from app.services.vector_store import inject_metadata_prefix


class TestMetadataInjection:
    def test_inject_metadata_with_ancestors_and_parent(self):
        text = "Mỗi học kỳ bao gồm 15 tuần học chính thức và 3 tuần thi."
        parent_title = "1.1 Cấu trúc năm học"
        ancestors = ["Chương 1: Quy định chung"]

        result = inject_metadata_prefix(
            child_text=text,
            parent_title=parent_title,
            ancestors=ancestors
        )
        expected_prefix = "[Mục: Chương 1: Quy định chung > 1.1 Cấu trúc năm học] "
        assert result.startswith(expected_prefix)
        assert text in result

    def test_inject_metadata_without_ancestors(self):
        text = "Nội dung phần mở đầu."
        parent_title = "Giới thiệu"
        ancestors = []

        result = inject_metadata_prefix(
            child_text=text,
            parent_title=parent_title,
            ancestors=ancestors
        )
        assert result.startswith("[Mục: Giới thiệu] ")
        assert "Nội dung phần mở đầu." in result

    def test_inject_metadata_fallback_when_titles_empty(self):
        text = "Đoạn văn không có tiêu đề."
        result = inject_metadata_prefix(
            child_text=text,
            parent_title="",
            ancestors=[]
        )
        assert result.startswith("[Mục: Tổng quan] ")
        assert "Đoạn văn không có tiêu đề." in result
