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

# --- Luồng chuyên ngành (Flow 2) ------------------------------------------------------------------
# Từ giai đoạn 9, domain thủ công/auto dịch hoàn toàn bằng LLM (NLLB chỉ còn là phao cứu sinh cuối),
# nên các test cũ mô tả hành vi "tra từ điển miss -> NLLB" được thay bằng test của hợp đồng SSE mới.
# Logic chi tiết được test ở tests/unit/test_domain_translation.py.

IT_DOMAIN = "Công nghệ Thông tin (IT)"


@pytest.fixture
def domain_env():
    from app.services.domain_index import DomainIndex

    index = DomainIndex.build([
        {"domain": IT_DOMAIN, "word": "memory leak", "translation": "rò rỉ bộ nhớ"},
        {"domain": "Y khoa / Sức khỏe", "word": "drug interaction", "translation": "tương tác thuốc"},
    ])
    with patch("app.services.domain_translation.get_index", AsyncMock(return_value=index)),          patch("app.services.domain_translation.get_cached_domain_result", return_value=None),          patch("app.services.domain_translation.set_cached_domain_result"),          patch("app.services.domain_translation.get_domain_version", return_value=1):
        from app.services import domain_llm
        domain_llm.reset_cooldowns()
        yield
        domain_llm.reset_cooldowns()


def _groq_stream_client(*contents):
    client = MagicMock()

    class MockChunk:
        def __init__(self, content):
            self.choices = [MagicMock(delta=MagicMock(content=content))]

    async def create(*args, **kwargs):
        async def gen():
            for c in contents:
                yield MockChunk(c)
        return gen()

    client.chat.completions.create = MagicMock(side_effect=create)
    return client


@pytest.mark.asyncio
async def test_exact_match_returns_dictionary_without_llm_or_nllb(mock_dependencies, domain_env):
    """TD_01: cụm ngắn khớp từ điển -> trả bản dịch từ điển, không gọi LLM, không gọi NLLB."""
    chunks = [json.loads(c) async for c in handle_flow_2_stream_translation("memory leak", "en", "vi", IT_DOMAIN)]
    assert [c["text"] for c in chunks if "text" in c] == ["rò rỉ bộ nhớ"]
    assert not any("warnings" in c for c in chunks)
    mock_dependencies["nllb"].assert_not_called()
    mock_dependencies["groq"].assert_not_called()


@pytest.mark.asyncio
async def test_exact_match_is_case_insensitive(mock_dependencies, domain_env):
    chunks = [json.loads(c) async for c in handle_flow_2_stream_translation("MEMORY LEAK", "en", "vi", IT_DOMAIN)]
    assert [c["text"] for c in chunks if "text" in c] == ["rò rỉ bộ nhớ"]


@pytest.mark.asyncio
async def test_short_miss_is_translated_by_llm_not_nllb(mock_dependencies, domain_env):
    """TD_02 (đã đổi): từ ngắn không có trong từ điển vẫn dịch bằng LLM theo ngữ cảnh chuyên ngành."""
    mock_dependencies["groq"].return_value = _groq_stream_client("từ ", "ngẫu nhiên")
    mock_dependencies["gemini"].return_value = None
    chunks = [json.loads(c) async for c in handle_flow_2_stream_translation("random word", "en", "vi", IT_DOMAIN)]
    assert "".join(c["text"] for c in chunks if "text" in c) == "từ ngẫu nhiên"
    warnings = [w for c in chunks for w in c.get("warnings", [])]
    assert warnings == []  # thiếu trong từ điển không còn là cảnh báo
    mock_dependencies["nllb"].assert_not_called()


@pytest.mark.asyncio
async def test_llm_stream_contract_domain_event_then_text(mock_dependencies, domain_env):
    """TD_03 (đã đổi): LLM stream; event `domain` phát trước text; glossary nằm trong system prompt."""
    client = _groq_stream_client("Một ", "rò rỉ bộ nhớ ", "gây sập")
    mock_dependencies["groq"].return_value = client
    mock_dependencies["gemini"].return_value = None
    chunks = [json.loads(c) async for c in handle_flow_2_stream_translation(
        "Drug interactions happen during memory leaks", "en", "vi", IT_DOMAIN)]

    assert chunks[0]["event"] == "domain" and chunks[0]["domain"]["status"] == "selected"
    assert [c["text"] for c in chunks if "text" in c] == ["Một ", "rò rỉ bộ nhớ ", "gây sập"]
    system_prompt = client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "- memory leak -> rò rỉ bộ nhớ" in system_prompt  # có xử lý số nhiều
    assert "drug interaction" not in system_prompt  # thuật ngữ thuộc domain khác không bị tiêm
    mock_dependencies["nllb"].assert_not_called()


@pytest.mark.asyncio
async def test_groq_fail_gemini_success(mock_dependencies, domain_env):
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create.side_effect = Exception("Groq sập")
    mock_dependencies["groq"].return_value = mock_groq_client

    async def gemini_stream(**kwargs):
        async def gen():
            yield MagicMock(text="Gemini dịch: Rò rỉ bộ nhớ")
        return gen()

    mock_gemini_client = MagicMock()
    mock_gemini_client.aio.models.generate_content_stream = gemini_stream
    mock_dependencies["gemini"].return_value = mock_gemini_client

    chunks = [json.loads(c) async for c in handle_flow_2_stream_translation("A memory leak causes crashes", "en", "vi", IT_DOMAIN)]
    assert [c["text"] for c in chunks if "text" in c] == ["Gemini dịch: Rò rỉ bộ nhớ"]
    assert not any(w["code"] == "FALLBACK_NLLB" for c in chunks for w in c.get("warnings", []))
    mock_dependencies["nllb"].assert_not_called()


@pytest.mark.asyncio
async def test_all_llm_down_falls_back_to_nllb_with_structured_warning(mock_dependencies, domain_env):
    """TD_04/TD_08 (đã đổi): LLM sập hoặc chưa cấu hình -> NLLB phao cứu sinh + cảnh báo FALLBACK_NLLB."""
    mock_dependencies["groq"].return_value = None
    mock_dependencies["gemini"].return_value = None
    with patch("app.services.domain_translation._nllb", AsyncMock(return_value="Bản dịch NLLB")) as nllb:
        chunks = [json.loads(c) async for c in handle_flow_2_stream_translation("A memory leak causes crashes", "en", "vi", IT_DOMAIN)]
    assert "Bản dịch NLLB" in "".join(c["text"] for c in chunks if "text" in c)
    codes = [w["code"] for c in chunks for w in c.get("warnings", [])]
    assert codes == ["FALLBACK_NLLB"]  # DOMAIN_SERVICE_ERROR đã hợp nhất vào FALLBACK_NLLB
    nllb.assert_awaited_once()


@pytest.mark.asyncio
async def test_flow_1_nllb_success(mock_dependencies):
    from app.services.llm_service import stream_translation
    
    text = "Just a regular sentence"
    stream = stream_translation(text, "en", "vi", "Dịch thông thường (Mặc định)")
    all_chunks = [json.loads(c) async for c in stream]
    # Phase 3 contract: stream luôn mở đầu bằng event detection và resolved_source_lang.
    assert all_chunks[0]["event"] == "detection"
    assert all_chunks[1] == {"resolved_source_lang": "en"}
    chunks = [c for c in all_chunks if "text" in c]

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
    chunks = [c for c in [json.loads(c) async for c in stream] if "text" in c]

    assert len(chunks) == 2
    assert chunks[0]["text"] == "Groq "
    assert chunks[1]["text"] == "dịch"
    assert "warning" not in chunks[0]
    
    mock_dependencies["groq"].assert_called()
