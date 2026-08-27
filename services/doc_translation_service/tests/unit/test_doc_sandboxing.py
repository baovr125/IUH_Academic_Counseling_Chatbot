import pytest
from app.services.vector_store import wrap_document_context_sandbox


class TestDocumentContextSandboxing:
    def test_wrap_document_sandbox_empty_chunks_returns_fallback(self):
        result = wrap_document_context_sandbox([])
        assert "<retrieved_context>" in result
        assert "</retrieved_context>" in result
        assert "Không tìm thấy thông tin" in result

    def test_wrap_document_sandbox_chunks_with_page_and_id(self):
        chunks = [
            {"content": "Tài liệu trang 1", "translated_content": "Document page 1", "page_number": 1},
            {"content": "Tài liệu trang 2", "translated_content": "Document page 2", "page_number": 2}
        ]
        result = wrap_document_context_sandbox(chunks)
        assert '<source id="1" page="1">\nDocument page 1\n</source>' in result
        assert '<source id="2" page="2">\nDocument page 2\n</source>' in result
        assert result.startswith("<retrieved_context>")
        assert result.endswith("</retrieved_context>")

    def test_wrap_document_sandbox_falls_back_to_raw_content(self):
        chunks = [
            {"content": "Nội dung gốc chưa dịch", "translated_content": None, "page_number": 5}
        ]
        result = wrap_document_context_sandbox(chunks)
        assert '<source id="1" page="5">\nNội dung gốc chưa dịch\n</source>' in result
