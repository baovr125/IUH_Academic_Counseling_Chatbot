import pytest
from app.services.pdf_parser import (
    clean_text,
    split_into_sentences_safe,
    is_header_line,
    get_header_level,
    hierarchical_chunk_pages,
)


class TestTextCleaningAndSentenceSplitting:
    def test_clean_text_normalizes_spaces_and_newlines(self):
        dirty = "  Đây là    một   văn bản\r\ncó nhiều khoảng trắng.  \t "
        cleaned = clean_text(dirty)
        assert cleaned == "Đây là một văn bản\ncó nhiều khoảng trắng."

    def test_clean_text_empty_input(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""

    def test_split_into_sentences_safe_multiple_sentences(self):
        text = "Trường Đại học Công nghiệp TP.HCM (IUH). Đây là câu thứ hai! Còn đây là câu thứ ba?"
        sents = split_into_sentences_safe(text)
        assert len(sents) == 3
        assert sents[0] == "Trường Đại học Công nghiệp TP.HCM (IUH)."
        assert sents[1] == "Đây là câu thứ hai!"
        assert sents[2] == "Còn đây là câu thứ ba?"


class TestHeaderDetectionAndHierarchy:
    @pytest.mark.parametrize("line, expected_is_header, expected_level", [
        ("# Chương 1: Giới thiệu hệ thống", True, 1),
        ("## 1.1 Khái niệm cơ bản", True, 2),
        ("### 1.1.1 Kiến trúc Microservices", True, 3),
        ("Chương 2: Cơ sở lý thuyết", True, 1),
        ("Chapter 3: Methodology", True, 1),
        ("1. Đăng ký học phần", True, 2),
        ("2.1 Quy chế học vụ", True, 3),
        ("ĐIỀU KIỆN TỐT NGHIỆP CỦA SINH VIÊN", True, 2),
    ])
    def test_is_header_line_and_get_level(self, line, expected_is_header, expected_level):
        assert is_header_line(line) is expected_is_header
        assert get_header_level(line) == expected_level

    def test_regular_paragraph_not_a_header(self):
        regular_line = "Sinh viên phải hoàn thành tất cả các môn học trong chương trình đào tạo để đủ điều kiện xét tốt nghiệp."
        assert is_header_line(regular_line) is False


class TestHierarchicalChunkingAlgorithm:
    def test_hierarchical_chunking_creates_parents_and_children(self):
        pages_data = [
            {
                "page": 1,
                "text": "Chương 1: Tổng quan\nĐoạn văn giới thiệu về trường Đại học Công nghiệp TP.HCM.",
                "lines": [
                    "Chương 1: Tổng quan",
                    "Đoạn văn giới thiệu về trường Đại học Công nghiệp TP.HCM với bề dày lịch sử phát triển hơn 65 năm qua."
                ]
            },
            {
                "page": 2,
                "text": "1.1 Quy chế tín chỉ\nMỗi học kỳ sinh viên đăng ký từ 14 đến 20 tín chỉ.",
                "lines": [
                    "1.1 Quy chế tín chỉ",
                    "Mỗi học kỳ sinh viên đăng ký từ 14 đến 20 tín chỉ tùy theo năng lực học tập và kế hoạch đào tạo cá nhân."
                ]
            }
        ]

        parents, children = hierarchical_chunk_pages(pages_data)
        assert len(parents) >= 2
        assert len(children) >= 2

        # Verify parent structure
        root_parent = parents[0]
        assert root_parent["id"] == "parent_root"
        assert root_parent["title"] == "Tổng quan tài liệu"

        p1 = parents[1]
        assert p1["title"] == "Chương 1: Tổng quan"
        assert p1["page_number"] == 1

        # Verify child structure & metadata propagation
        child_1 = children[0]
        assert child_1["chunk_index"] == 1
        assert child_1["parent_title"] == "Chương 1: Tổng quan"
        assert "bề dày lịch sử phát triển" in child_1["content"]
        assert child_1["page_number"] == 1

    def test_hierarchical_chunking_empty_pages(self):
        parents, children = hierarchical_chunk_pages([])
        assert len(parents) == 1
        assert len(children) == 0
