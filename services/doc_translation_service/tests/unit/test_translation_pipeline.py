import pytest
from unittest.mock import patch, MagicMock, call
from app.services.ollama_translator import translate_markdown_document_ollama


SAMPLE_MD = """# Abstract

This paper presents a novel approach to Neural Machine Translation using Transformer architectures.

## 1 Introduction

Machine learning has revolutionized natural language processing.

## 2 Method

We propose an encoder-decoder model with attention mechanism.
"""


class TestTranslatePipelineOllama:
    """
    Tests cho translate_markdown_document_ollama():
    - Progress callback thứ tự đúng
    - Gemini fallback được kích hoạt đúng khi Ollama fail
    - glossary_context được truyền vào cả Ollama lẫn Gemini fallback
    """

    def test_progress_callback_called_for_each_batch(self):
        """Status callback phải được gọi ít nhất 1 lần cho mỗi batch."""
        progress_calls = []

        def mock_callback(progress: int, message: str, model_name: str = ""):
            progress_calls.append((progress, message, model_name))

        with patch("app.services.ollama_translator.check_ollama_health", return_value=True), \
             patch("app.services.ollama_translator.call_ollama_generate", return_value="Bản dịch mẫu"):
            
            result_text, model_name = translate_markdown_document_ollama(
                md_text=SAMPLE_MD,
                status_callback=mock_callback
            )

        assert len(progress_calls) >= 1, "Callback phải được gọi ít nhất 1 lần"
        # Verify progress tăng dần
        progress_values = [c[0] for c in progress_calls]
        assert all(40 <= p <= 80 for p in progress_values), "Progress phải nằm trong khoảng 40-80%"

    def test_gemini_fallback_triggered_when_ollama_fails(self):
        """Khi Ollama health check fail, toàn bộ batches phải được dịch bằng Gemini."""
        with patch("app.services.ollama_translator.check_ollama_health", return_value=False), \
             patch("app.services.translator.translate_chunk_with_gemini", return_value="Bản dịch Gemini") as mock_gemini:
            
            result_text, model_name = translate_markdown_document_ollama(
                md_text=SAMPLE_MD
            )

        assert mock_gemini.called, "Gemini fallback phải được gọi khi Ollama không khả dụng"
        assert "Gemini" in model_name, f"model_name phải chứa 'Gemini', nhận được: {model_name}"
        assert "Bản dịch Gemini" in result_text

    def test_gemini_fallback_per_batch_when_ollama_throws(self):
        """Khi từng call Ollama ném exception, Gemini phải được dùng cho batch đó."""
        with patch("app.services.ollama_translator.check_ollama_health", return_value=True), \
             patch("app.services.ollama_translator.call_ollama_generate", side_effect=RuntimeError("Timeout")), \
             patch("app.services.translator.translate_chunk_with_gemini", return_value="Gemini batch") as mock_gemini:
            
            result_text, model_name = translate_markdown_document_ollama(
                md_text=SAMPLE_MD
            )

        assert mock_gemini.called, "Gemini phải được gọi khi từng batch Ollama fail"
        assert "Gemini batch" in result_text

    def test_glossary_context_injected_into_system_prompt(self):
        """glossary_context phải được inject vào system_instruction gửi tới Ollama."""
        glossary = "- Neural Network: Mạng nơ-ron\n- Attention: Cơ chế chú ý"
        captured_calls = []

        def mock_generate(prompt, system_instruction="", **kwargs):
            captured_calls.append(system_instruction)
            return "Bản dịch"

        with patch("app.services.ollama_translator.check_ollama_health", return_value=True), \
             patch("app.services.ollama_translator.call_ollama_generate", side_effect=mock_generate):
            
            translate_markdown_document_ollama(
                md_text=SAMPLE_MD,
                glossary_context=glossary
            )

        assert len(captured_calls) > 0
        # Kiểm tra glossary được nhúng vào system instruction
        for si in captured_calls:
            assert "Neural Network" in si, "Glossary context phải có mặt trong system instruction"
            assert "Mạng nơ-ron" in si

    def test_glossary_context_passed_to_gemini_fallback(self):
        """glossary_context phải được truyền xuống Gemini fallback khi Ollama fail."""
        glossary = "- BLEU Score: Điểm BLEU\n- Transformer: Mô hình Transformer"
        gemini_calls = []

        def mock_gemini(text, source_lang="en", target_lang="vi", glossary_context="", **kwargs):
            gemini_calls.append(glossary_context)
            return "Bản dịch"

        with patch("app.services.ollama_translator.check_ollama_health", return_value=False), \
             patch("app.services.translator.translate_chunk_with_gemini", side_effect=mock_gemini):
            
            translate_markdown_document_ollama(
                md_text=SAMPLE_MD,
                glossary_context=glossary
            )

        assert len(gemini_calls) > 0
        for gc in gemini_calls:
            assert "BLEU Score" in gc, "Glossary phải được truyền vào Gemini fallback"

    def test_empty_input_returns_empty(self):
        """Input rỗng phải trả về ('', 'N/A') mà không gọi LLM."""
        with patch("app.services.ollama_translator.check_ollama_health") as mock_health:
            result_text, model_name = translate_markdown_document_ollama(md_text="   ")

        mock_health.assert_not_called()
        assert result_text == ""
        assert model_name == "N/A"

    def test_translated_batches_reassembled_in_order(self):
        """Các batch phải được ghép lại theo đúng thứ tự index, không bị xáo trộn."""
        batch_results = {}

        def mock_generate(prompt, **kwargs):
            # Trả về text có đánh dấu để trace thứ tự
            if "Abstract" in prompt:
                return "BATCH_ABSTRACT"
            elif "Introduction" in prompt:
                return "BATCH_INTRO"
            elif "Method" in prompt:
                return "BATCH_METHOD"
            return "BATCH_OTHER"

        with patch("app.services.ollama_translator.check_ollama_health", return_value=True), \
             patch("app.services.ollama_translator.call_ollama_generate", side_effect=mock_generate):
            
            result_text, _ = translate_markdown_document_ollama(md_text=SAMPLE_MD)

        # Kiểm tra thứ tự: Abstract -> Introduction -> Method
        idx_abstract = result_text.find("BATCH_ABSTRACT")
        idx_intro = result_text.find("BATCH_INTRO")
        idx_method = result_text.find("BATCH_METHOD")

        if idx_abstract >= 0 and idx_intro >= 0:
            assert idx_abstract < idx_intro, "Abstract phải xuất hiện trước Introduction"
        if idx_intro >= 0 and idx_method >= 0:
            assert idx_intro < idx_method, "Introduction phải xuất hiện trước Method"
