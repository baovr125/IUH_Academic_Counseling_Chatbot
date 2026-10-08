import time
import pytest
from unittest.mock import patch, MagicMock
from nltk.corpus import wordnet as wn
from app.services.word_analysis_service import spacy_to_wordnet_pos

# Giả lập Redis bằng dictionary trên memory
_mock_redis_store = {}

class MockRedis:
    def get(self, key):
        return _mock_redis_store.get(key)
    def setex(self, key, time, value):
        _mock_redis_store[key] = value

@pytest.fixture(autouse=True)
def mock_redis():
    _mock_redis_store.clear()
    with patch("app.services.cache_service.get_redis") as mock_get_redis:
        mock_get_redis.return_value = MockRedis()
        yield

@pytest.fixture(autouse=True)
def mock_heavy_nlp():
    """Mock các model nặng (spaCy, NLLB) để test chạy tức thì."""
    with patch("spacy.load") as mock_spacy, \
         patch("app.services.word_analysis_service.get_nllb_translator") as mock_nllb, \
         patch("app.services.translation_service.run_nllb_only") as mock_run_nllb:
        
        # Mock SpaCy Token
        mock_token = MagicMock()
        mock_token.text = "book"
        mock_token.lemma_ = "book"
        mock_token.pos_ = "VERB"
        
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_token]
        mock_doc.__getitem__.return_value = mock_token
        
        mock_nlp_instance = MagicMock()
        mock_nlp_instance.return_value = mock_doc
        mock_spacy.return_value = mock_nlp_instance
        
        # Mock NLLB
        mock_translator = MagicMock()
        mock_result = MagicMock()
        mock_result.hypotheses = [["<tgt>", "Mock", "dịch"]]
        mock_translator.translate_batch.return_value = [mock_result]
        
        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.return_value = [1]
        mock_tokenizer.convert_ids_to_tokens.return_value = ["mock"]
        mock_tokenizer.convert_tokens_to_ids.return_value = [1]
        mock_tokenizer.decode.return_value = "Mock bản dịch"
        
        mock_nllb.return_value = (mock_translator, mock_tokenizer)
        mock_run_nllb.return_value = "Mock dịch trực tiếp"
        
        yield mock_spacy, mock_nllb, mock_token

def test_spacy_to_wordnet_pos():
    assert spacy_to_wordnet_pos("NOUN") == wn.NOUN
    assert spacy_to_wordnet_pos("VERB") == wn.VERB
    assert spacy_to_wordnet_pos("ADJ") == wn.ADJ
    assert spacy_to_wordnet_pos("ADV") == wn.ADV
    assert spacy_to_wordnet_pos("PRON") is None
    assert spacy_to_wordnet_pos("UNKNOWN") is None

def test_analyze_word_endpoint_success(client):
    """Test standard English word analysis (Cache Miss first, then Hit)"""
    payload = {
        "text": "I want to book a flight to Paris.",
        "selected_text": "book",
        "source_lang": "en",
        "target_lang": "vi"
    }
    
    # Measure time for cache miss
    start_time = time.time()
    response = client.post("/api/v1/translate/analyze_word", json=payload)
    miss_time = time.time() - start_time
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["lemma"] == "book"
    assert data["data"]["part_of_speech"] == "VERB" # Because it's "to book a flight"
    assert data["data"]["contextual_meaning"] is not None
    
    # Measure time for cache hit
    start_time = time.time()
    response_cached = client.post("/api/v1/translate/analyze_word", json=payload)
    hit_time = time.time() - start_time
    
    assert response_cached.status_code == 200
    assert response_cached.json()["data"]["cached"] == True

def test_analyze_word_endpoint_noun(client, mock_heavy_nlp):
    """Test the same word 'book' but as a Noun in different context"""
    mock_spacy, mock_nllb, mock_token = mock_heavy_nlp
    mock_token.pos_ = "NOUN"
    
    payload = {
        "text": "I am reading a very good book right now.",
        "selected_text": "book",
        "source_lang": "en",
        "target_lang": "vi"
    }
    
    response = client.post("/api/v1/translate/analyze_word", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["data"]["lemma"] == "book"
    assert data["data"]["part_of_speech"] == "NOUN"
    assert data["data"]["contextual_meaning"] is not None

def test_analyze_word_non_english(client):
    """Test non-English word analysis which skips NLTK and uses basic translation"""
    payload = {
        "text": "Tôi muốn đặt phòng khách sạn.",
        "selected_text": "phòng",
        "source_lang": "vi",
        "target_lang": "en"
    }
    
    response = client.post("/api/v1/translate/analyze_word", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["data"]["word"] == "phòng"
