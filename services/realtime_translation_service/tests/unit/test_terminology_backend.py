import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Bỏ qua khởi tạo model thật bằng cách mock ngay khi import
with patch("app.services.llm_service.get_nllb_translator"), \
     patch("app.services.llm_service.get_groq_client"), \
     patch("app.services.llm_service.get_gemini_client"), \
     patch("app.services.supabase_client.get_supabase"):
    from app.services.llm_service import handle_flow_2_stream_translation

@pytest.fixture
def mock_dependencies():
    with patch("app.services.supabase_client.get_supabase") as mock_supa, \
         patch("app.services.llm_service.get_nllb_translator") as mock_nllb, \
         patch("app.services.llm_service.get_groq_client") as mock_groq, \
         patch("app.services.llm_service.get_gemini_client") as mock_gemini:
        
        # Mock Supabase
        mock_db = MagicMock()
        mock_res = MagicMock()
        # Giả lập từ điển có: "memory leak" -> "rò rỉ bộ nhớ", "garbage collection process" -> "thu gom rác"
        mock_res.data = [
            {"word": "memory leak", "translation": "rò rỉ bộ nhớ"},
            {"word": "drug interaction", "translation": "tương tác thuốc"}
        ]
        mock_db.table().select().eq().execute.return_value = mock_res
        mock_supa.return_value = mock_db
        
        # Mock NLLB
        mock_translator = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.return_value = [1, 2, 3]
        mock_tokenizer.convert_ids_to_tokens.return_value = ["mock", "token"]
        
        # Mock translate_batch kết quả
        mock_result = MagicMock()
        mock_result.hypotheses = [["<tgt>", "Bản", "dịch", "NLLB"]]
        mock_translator.translate_batch.return_value = [mock_result]
        mock_tokenizer.convert_tokens_to_ids.return_value = [4, 5, 6]
        mock_tokenizer.decode.return_value = "Bản dịch NLLB"
        
        mock_nllb.return_value = (mock_translator, mock_tokenizer)
        
        yield {
            "supa": mock_supa,
            "nllb": mock_nllb,
            "groq": mock_groq,
            "gemini": mock_gemini
        }

@pytest.mark.asyncio
async def test_exact_match_under_3_words(mock_dependencies):
    """
    Test Case TD_01: <= 3 words, Exact match trong dictionary.
    Kỳ vọng: Không gọi NLLB, Không gọi LLM, trả về trực tiếp dict value.
    """
    text = "memory leak"
    stream = handle_flow_2_stream_translation(text, "en", "vi", "Công nghệ Thông tin (IT)")
    
    chunks = [json.loads(c) async for c in stream]
    
    assert len(chunks) == 1
    assert chunks[0].get("text") == "rò rỉ bộ nhớ"
    assert "warning" not in chunks[0]
    
    mock_dependencies["nllb"].assert_not_called()
    mock_dependencies["groq"].assert_not_called()

@pytest.mark.asyncio
async def test_no_match_under_3_words(mock_dependencies):
    """
    Test Case TD_02: <= 3 words, KHÔNG có exact match trong dictionary.
    Kỳ vọng: Gọi NLLB, trả về text và warning.
    """
    text = "random word" # 2 từ, không nằm trong dict
    stream = handle_flow_2_stream_translation(text, "en", "vi", "Công nghệ Thông tin (IT)")
    
    chunks = [json.loads(c) async for c in stream]
    
    assert len(chunks) == 1
    assert "Bản dịch NLLB" in chunks[0].get("text")
    assert "warning" in chunks[0]
    assert "không được tìm thấy trong từ điển chuyên ngành" in chunks[0]["warning"]
    
    mock_dependencies["nllb"].assert_called()
    mock_dependencies["groq"].assert_not_called()

@pytest.mark.asyncio
async def test_over_3_words_llm_success(mock_dependencies):
    """
    Test Case TD_03: > 3 words, Có chứa thuật ngữ trong câu, LLM (Groq) hoạt động bình thường.
    Kỳ vọng: Gọi LLM streaming, không có warning.
    """
    text = "A memory leak causes crashes" # 5 từ
    
    # Mock Groq stream
    mock_groq_client = MagicMock()
    mock_stream = AsyncMock()
    
    class MockChunk:
        def __init__(self, content):
            self.choices = [MagicMock(delta=MagicMock(content=content))]
            
    async def mock_async_generator():
        yield MockChunk("Một ")
        yield MockChunk("rò rỉ bộ nhớ ")
        yield MockChunk("gây ra ")

    async def get_stream(*args, **kwargs):
        return mock_async_generator()

    mock_groq_client.chat.completions.create.side_effect = get_stream
    mock_dependencies["groq"].return_value = mock_groq_client
    
    stream = handle_flow_2_stream_translation(text, "en", "vi", "Công nghệ Thông tin (IT)")
    chunks = [json.loads(c) async for c in stream]
    
    assert len(chunks) == 3
    assert chunks[0]["text"] == "Một "
    assert chunks[1]["text"] == "rò rỉ bộ nhớ "
    assert "warning" not in chunks[0]
    
    mock_dependencies["groq"].assert_called()
    mock_dependencies["nllb"].assert_not_called()

@pytest.mark.asyncio
async def test_over_3_words_llm_failure_fallback_nllb(mock_dependencies):
    """
    Test Case TD_04: > 3 words, Có chứa thuật ngữ, NHƯNG LLM (Groq) và Gemini đều chết (Raise Exception).
    Kỳ vọng: Fallback về NLLB, kèm Warning.
    """
    text = "A memory leak causes crashes" # 5 từ
    
    # Groq raise Exception
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create.side_effect = Exception("Groq API Timeout")
    mock_dependencies["groq"].return_value = mock_groq_client
    
    # Gemini raise Exception
    mock_gemini_client = MagicMock()
    mock_gemini_client.models.generate_content_stream.side_effect = Exception("Gemini API Timeout")
    mock_dependencies["gemini"].return_value = mock_gemini_client
    
    stream = handle_flow_2_stream_translation(text, "en", "vi", "Công nghệ Thông tin (IT)")
    chunks = [json.loads(c) async for c in stream]
    
    # Sẽ gọi NLLB sau khi 2 LLM fail
    assert len(chunks) == 1
    assert "Bản dịch NLLB" in chunks[0].get("text")
    assert "warning" in chunks[0]
    assert "không thể dịch bằng AI model chuyên ngành" in chunks[0]["warning"]
    
    mock_dependencies["groq"].assert_called()
    mock_dependencies["gemini"].assert_called()
    mock_dependencies["nllb"].assert_called()


@pytest.mark.asyncio
async def test_over_3_words_no_terminology_found(mock_dependencies):
    text = "this is just a normal sentence without terms"
    stream = handle_flow_2_stream_translation(text, "en", "vi", "Công nghệ Thông tin (IT)")
    chunks = [json.loads(c) async for c in stream]
    
    assert len(chunks) == 1
    assert "Bản dịch NLLB" in chunks[0].get("text")
    assert "warning" not in chunks[0]
    mock_dependencies["nllb"].assert_called()
    mock_dependencies["groq"].assert_not_called()

@pytest.mark.asyncio
async def test_over_3_words_groq_fail_gemini_success(mock_dependencies):
    text = "A memory leak causes crashes"
    
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create.side_effect = Exception("Groq sập")
    mock_dependencies["groq"].return_value = mock_groq_client
    
    mock_gemini_client = MagicMock()
    mock_chunk = MagicMock(text="Gemini dịch: Rò rỉ bộ nhớ")
    mock_gemini_client.models.generate_content_stream.return_value = [mock_chunk]
    mock_dependencies["gemini"].return_value = mock_gemini_client

    stream = handle_flow_2_stream_translation(text, "en", "vi", "Công nghệ Thông tin (IT)")
    chunks = [json.loads(c) async for c in stream]
    
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Gemini dịch: Rò rỉ bộ nhớ"
    assert "warning" not in chunks[0]
    
    mock_dependencies["groq"].assert_called()
    mock_dependencies["gemini"].assert_called()
    mock_dependencies["nllb"].assert_not_called()

@pytest.mark.asyncio
async def test_clients_not_configured(mock_dependencies):
    text = "A memory leak causes crashes"
    mock_dependencies["groq"].return_value = None
    mock_dependencies["gemini"].return_value = None
    
    stream = handle_flow_2_stream_translation(text, "en", "vi", "Công nghệ Thông tin (IT)")
    chunks = [json.loads(c) async for c in stream]
    
    assert len(chunks) == 1
    assert "Bản dịch NLLB" in chunks[0]["text"]
    assert "warning" in chunks[0]
    assert "Hệ thống không thể dịch bằng AI model chuyên ngành" in chunks[0]["warning"]
    mock_dependencies["nllb"].assert_called()

@pytest.mark.asyncio
async def test_exact_match_under_3_words_case_insensitivity(mock_dependencies):
    text = "MEMORY LEAK"
    stream = handle_flow_2_stream_translation(text, "en", "vi", "Công nghệ Thông tin (IT)")
    chunks = [json.loads(c) async for c in stream]
    
    assert len(chunks) == 1
    assert chunks[0].get("text") == "rò rỉ bộ nhớ"
    assert "warning" not in chunks[0]

@pytest.mark.asyncio
async def test_multi_term_match(mock_dependencies):
    text = "Drug interaction happens during memory leak"
    
    mock_groq_client = MagicMock()
    async def get_stream(*args, **kwargs):
        class MockChunk:
            def __init__(self, content):
                self.choices = [MagicMock(delta=MagicMock(content=content))]
        yield MockChunk("Mocked")
    mock_groq_client.chat.completions.create.side_effect = get_stream
    mock_dependencies["groq"].return_value = mock_groq_client
    
    stream = handle_flow_2_stream_translation(text, "en", "vi", "Công nghệ Thông tin (IT)")
    chunks = [json.loads(c) async for c in stream]
    
    call_args = mock_groq_client.chat.completions.create.call_args
    assert call_args is not None
    
    messages = call_args.kwargs.get("messages", [])
    system_prompt = messages[0]["content"] if messages else ""
    
    assert "- memory leak -> rò rỉ bộ nhớ" in system_prompt
    assert "- drug interaction -> tương tác thuốc" in system_prompt
    assert "You are an expert translator" in system_prompt

@pytest.mark.asyncio
async def test_morphological_matching(mock_dependencies):
    text = "Drug interactions happen during memory leaks"
    
    mock_groq_client = MagicMock()
    async def get_stream(*args, **kwargs):
        class MockChunk:
            def __init__(self, content):
                self.choices = [MagicMock(delta=MagicMock(content=content))]
        yield MockChunk("Mocked")
    mock_groq_client.chat.completions.create.side_effect = get_stream
    mock_dependencies["groq"].return_value = mock_groq_client
    
    stream = handle_flow_2_stream_translation(text, "en", "vi", "Công nghệ Thông tin (IT)")
    chunks = [json.loads(c) async for c in stream]
    
    call_args = mock_groq_client.chat.completions.create.call_args
    messages = call_args.kwargs.get("messages", [])
    system_prompt = messages[0]["content"] if messages else ""
    
    # Should find base forms despite plurals in text
    assert "- memory leak -> rò rỉ bộ nhớ" in system_prompt
    assert "- drug interaction -> tương tác thuốc" in system_prompt


@pytest.mark.asyncio
async def test_flow_1_nllb_success(mock_dependencies):
    from app.services.llm_service import stream_translation
    
    text = "Just a regular sentence"
    stream = stream_translation(text, "en", "vi", "Dịch thông thường (Mặc định)")
    chunks = [json.loads(c) async for c in stream]
    
    assert len(chunks) == 1
    assert "Bản dịch NLLB" in chunks[0]["text"]
    assert "warning" not in chunks[0]
    
    mock_dependencies["nllb"].assert_called()
    mock_dependencies["groq"].assert_not_called()

@pytest.mark.asyncio
async def test_flow_1_nllb_fail_groq_success(mock_dependencies):
    from app.services.llm_service import stream_translation
    
    # Mock NLLB fail
    mock_translator, _ = mock_dependencies["nllb"].return_value
    mock_translator.translate_batch.side_effect = Exception("NLLB sập")
    
    # Mock Groq success
    mock_groq_client = MagicMock()
    async def get_stream(*args, **kwargs):
        class MockChunk:
            def __init__(self, content):
                self.choices = [MagicMock(delta=MagicMock(content=content))]
        async def mock_async_generator():
            yield MockChunk("Groq ")
            yield MockChunk("dịch")
        return mock_async_generator()
    mock_groq_client.chat.completions.create.side_effect = get_stream
    mock_dependencies["groq"].return_value = mock_groq_client
    
    text = "Just a regular sentence"
    stream = stream_translation(text, "en", "vi", "Dịch thông thường (Mặc định)")
    chunks = [json.loads(c) async for c in stream]
    
    assert len(chunks) == 2
    assert chunks[0]["text"] == "Groq "
    assert chunks[1]["text"] == "dịch"
    assert "warning" not in chunks[0]
    
    mock_dependencies["groq"].assert_called()
