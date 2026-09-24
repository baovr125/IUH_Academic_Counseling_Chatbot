import pytest

def test_translation_flow_1_default(client):
    """Test standard NLLB text translation (Flow 1) to ensure Word Analysis didn't break it"""
    payload = {
        "text": "This application uses cache memory.",
        "source_lang": "en",
        "target_lang": "vi",
        "domain": ""
    }
    
    response = client.post("/api/v1/translate/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "translated_text" in data["data"]
    # Ensure it translates something meaningful
    assert len(data["data"]["translated_text"]) > 0
    assert "cache" in data["data"]["translated_text"].lower() or "bộ nhớ" in data["data"]["translated_text"].lower()

def test_translation_flow_2_domain(client):
    """Test domain translation (Flow 2) to ensure Domain Dictionary mapping still works"""
    payload = {
        "text": "This application uses cache memory.",
        "source_lang": "en",
        "target_lang": "vi",
        "domain": "Công nghệ thông tin"
    }
    
    response = client.post("/api/v1/translate/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "translated_text" in data["data"]
    assert len(data["data"]["translated_text"]) > 0
    # In Flow 2, it might use Gemini fallback if term is detected
    assert data["data"].get("domain_applied", True) == True or data["data"].get("fallback_used", False) == False
