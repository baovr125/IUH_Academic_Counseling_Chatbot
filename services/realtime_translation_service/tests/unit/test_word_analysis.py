import time
import pytest
from nltk.corpus import wordnet as wn
from app.services.word_analysis_service import spacy_to_wordnet_pos

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

def test_analyze_word_endpoint_noun(client):
    """Test the same word 'book' but as a Noun in different context"""
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
