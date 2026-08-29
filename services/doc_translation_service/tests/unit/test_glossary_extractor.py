import pytest
from unittest.mock import patch, MagicMock
from app.services.glossary_extractor import (
    heuristic_extract_terms,
    extract_glossary,
    parse_glossary_json,
    filter_invalid_terms,
    translate_term_candidates
)
from app.schemas.documents import GlossaryTerm, DocumentStatusResponse


def test_parse_glossary_json_formats():
    # Format 1: Direct JSON array
    raw1 = '[{"term": "Neural Network", "translation": "Mạng nơ-ron", "phonetic": "/.../"}]'
    res1 = parse_glossary_json(raw1)
    assert len(res1) == 1
    assert res1[0]["term"] == "Neural Network"
    assert res1[0]["translation"] == "Mạng nơ-ron"

    # Format 2: Object with "glossary" key
    raw2 = '{"glossary": [{"term": "Deep Learning", "translation": "Học sâu"}]}'
    res2 = parse_glossary_json(raw2)
    assert len(res2) == 1
    assert res2[0]["term"] == "Deep Learning"
    assert res2[0]["translation"] == "Học sâu"

    # Format 3: Markdown codeblock
    raw3 = '```json\n{"terms": [{"term": "BLEU Score", "translation": "Điểm BLEU"}]}\n```'
    res3 = parse_glossary_json(raw3)
    assert len(res3) == 1
    assert res3[0]["term"] == "BLEU Score"
    assert res3[0]["translation"] == "Điểm BLEU"

    # Format 4: Untranslated terms (term == translation) should be filtered out
    raw4 = '[{"term": "Abstract", "translation": "Abstract"}]'
    res4 = parse_glossary_json(raw4)
    assert len(res4) == 0


def test_filter_invalid_terms():
    candidates = [
        {"term": "1 Introduction"},
        {"term": "Abstract"},
        {"term": "2 Method"},
        {"term": "Neural Machine Translation"},
        {"term": "BLEU score"},
        {"term": "References"}
    ]
    filtered = filter_invalid_terms(candidates)
    terms = [item["term"] for item in filtered]
    assert "1 Introduction" not in terms
    assert "Abstract" not in terms
    assert "2 Method" not in terms
    assert "References" not in terms
    assert "Neural Machine Translation" in terms
    assert "BLEU score" in terms


def test_heuristic_extract_terms():
    sample_text = """
    # 1 Introduction
    # 2 Method
    This paper investigates **Neural Machine Translation** and **Transformer Architectures**.
    """
    results = heuristic_extract_terms(sample_text, source_lang="en")
    assert isinstance(results, list)
    terms = [item["term"] for item in results]
    assert "1 Introduction" not in terms
    assert "2 Method" not in terms
    assert any("Neural Machine Translation" in t or "Transformer" in t for t in terms)


@pytest.mark.asyncio
async def test_extract_glossary_fallback_to_gemini():
    sample_text = "Natural language processing is an AI subfield."
    
    mock_gemini_resp = MagicMock()
    mock_gemini_resp.text = '{"glossary": [{"term": "Natural Language Processing", "translation": "Xử lý ngôn ngữ tự nhiên"}]}'
    
    mock_gemini_client = MagicMock()
    mock_gemini_client.models.generate_content.return_value = mock_gemini_resp

    with patch("app.services.glossary_extractor.check_ollama_health", return_value=False), \
         patch("app.services.translator.get_gemini_client", return_value=mock_gemini_client):
        
        glossary = await extract_glossary(sample_text, target_lang="vi", source_lang="en")
        assert len(glossary) == 1
        assert glossary[0]["term"] == "Natural Language Processing"
        assert glossary[0]["translation"] == "Xử lý ngôn ngữ tự nhiên"
        assert glossary[0]["vi"] == "Xử lý ngôn ngữ tự nhiên"


def test_glossary_schema_flexibility():
    term_dict = {
        "term": "Artificial Intelligence",
        "translation": "Trí tuệ nhân tạo",
        "vi": "Trí tuệ nhân tạo",
        "context": "CS Domain",
        "phonetic": "/eɪ aɪ/",
        "audio_url": "/api/v1/translate/audio/terms/en_123.mp3"
    }
    term = GlossaryTerm(**term_dict)
    assert term.term == "Artificial Intelligence"
    assert term.vi == "Trí tuệ nhân tạo"
    assert term.translation == "Trí tuệ nhân tạo"

    status_resp = DocumentStatusResponse(
        doc_id="test-doc-123",
        status="completed",
        progress=100,
        message="Done",
        glossary=[term]
    )
    assert len(status_resp.glossary) == 1
    assert status_resp.glossary[0].term == "Artificial Intelligence"
