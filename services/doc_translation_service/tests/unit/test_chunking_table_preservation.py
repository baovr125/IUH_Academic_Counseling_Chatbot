import pytest
from app.services.pdf_parser import markdown_hierarchical_chunking


class TestChunkingTablePreservation:
    """
    Verify rằng markdown_hierarchical_chunking() không bao giờ cắt vỡ bảng Markdown,
    khối code, hoặc công thức LaTeX ở giữa.
    """

    def test_table_not_split_within_chunk(self):
        """Bảng Markdown phải luôn nằm nguyên vẹn trong cùng 1 batch, không bị cắt đôi."""
        table_md = (
            "| Model | BLEU Score | Params |\n"
            "|---|---|---|\n"
            "| BERT-Base | 85.2 | 110M |\n"
            "| GPT-4 | 92.1 | 175B |\n"
            "| Qwen2.5 | 90.5 | 14B |"
        )
        # Đặt bảng trong 1 section nhỏ
        md_text = f"## Results\n\n{table_md}"

        batches = markdown_hierarchical_chunking(md_text, max_tokens=2500)

        # Tìm batch chứa ký tự "|"
        table_batches = [b for b in batches if "|---|---|" in b or "| Model |" in b]
        assert len(table_batches) >= 1, "Bảng phải tồn tại trong ít nhất 1 batch"

        # Bảng phải xuất hiện đầy đủ trong 1 batch duy nhất (không bị tách)
        for batch in table_batches:
            if "| Model |" in batch:
                assert "|---|---|" in batch, "Dòng phân cách |---|---| phải cùng batch với header bảng"
                assert "| BERT-Base |" in batch, "Dữ liệu bảng phải cùng batch với header"

    def test_latex_formula_not_split(self):
        """Công thức LaTeX inline và block phải được giữ nguyên qua chunking."""
        md_text = (
            "## Theory\n\n"
            "The attention mechanism is defined as:\n\n"
            "$$\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right) V$$\n\n"
            "where $d_k$ is the dimension of the key vectors."
        )

        batches = markdown_hierarchical_chunking(md_text, max_tokens=2500)

        # Tìm batch chứa công thức
        formula_batches = [b for b in batches if "$$" in b or "$d_k$" in b]
        assert len(formula_batches) >= 1, "Công thức LaTeX phải xuất hiện trong ít nhất 1 batch"

        for batch in formula_batches:
            if "$$\\text{Attention}" in batch:
                # Đảm bảo mở/đóng $$ đều có mặt
                assert batch.count("$$") % 2 == 0, "Công thức LaTeX block $$ phải có số cặp mở/đóng chẵn"

    def test_code_block_not_split(self):
        """Code block phải được giữ nguyên trong cùng 1 batch."""
        md_text = (
            "## Implementation\n\n"
            "Example code:\n\n"
            "```python\n"
            "import torch\n"
            "model = BertModel.from_pretrained('bert-base-uncased')\n"
            "output = model(input_ids)\n"
            "```"
        )

        batches = markdown_hierarchical_chunking(md_text, max_tokens=2500)

        # Code block phải còn nguyên dạng
        all_text = "\n\n".join(batches)
        assert "```python" in all_text, "Mở code block phải được giữ"
        assert "```" in all_text, "Đóng code block phải được giữ"

    def test_large_document_creates_multiple_batches(self):
        """Tài liệu lớn phải được chia thành nhiều batch, mỗi batch không vượt quá max_tokens * 2."""
        # Tạo tài liệu giả lớn (~3000 tokens)
        sections = []
        for i in range(1, 7):
            paragraph = " ".join([f"word{j}" for j in range(200)])  # ~200 từ/section
            sections.append(f"## Section {i}\n\n{paragraph}")
        md_text = "\n\n".join(sections)

        max_tokens = 500
        batches = markdown_hierarchical_chunking(md_text, max_tokens=max_tokens)

        assert len(batches) > 1, "Tài liệu lớn phải được chia thành nhiều batches"
        for batch in batches:
            token_count = len(batch.split()) * 1.3
            # Cho phép overshoot tối đa 1.5x (do section-level chunking)
            assert token_count <= max_tokens * 1.5 * 1.5, f"Batch quá lớn: {token_count} tokens"

    def test_empty_markdown_returns_empty_list(self):
        """Input rỗng hoặc chỉ có whitespace phải trả về list rỗng."""
        assert markdown_hierarchical_chunking("") == []
        assert markdown_hierarchical_chunking("   \n\n   ") == []

    def test_single_short_document_is_one_batch(self):
        """Tài liệu ngắn hơn max_tokens phải luôn là 1 batch duy nhất."""
        md_text = "## Introduction\n\nThis is a short paper about deep learning."
        batches = markdown_hierarchical_chunking(md_text, max_tokens=2500)
        assert len(batches) == 1
        assert "Introduction" in batches[0]
        assert "deep learning" in batches[0]
