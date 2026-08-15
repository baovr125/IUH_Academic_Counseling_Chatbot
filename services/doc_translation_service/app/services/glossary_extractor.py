import os
import re
import json
import httpx
import urllib.parse
from typing import List, Dict, Any
from app.utils.logger import logger
from app.services.ollama_translator import call_ollama_generate
import google.generativeai as genai

async def get_word_audio(word: str) -> Dict[str, str]:
    """
    Fetches pronunciation audio URL and phonetic from Free Dictionary API.
    Returns {"audio_url": "...", "phonetic": "..."}
    """
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    entry = data[0]
                    phonetic = entry.get("phonetic", "")
                    audio_url = ""
                    for p in entry.get("phonetics", []):
                        if p.get("audio"):
                            audio_url = p.get("audio")
                            if not phonetic and p.get("text"):
                                phonetic = p.get("text")
                            break
                            
                    return {
                        "phonetic": phonetic,
                        "audio_url": audio_url
                    }
        except Exception:
            pass
            
    return {"phonetic": "", "audio_url": ""}

def heuristic_extract_terms(text: str) -> List[Dict[str, Any]]:
    """Phương thức dự phòng trích xuất thuật ngữ chuyên ngành dựa trên Markdown syntax."""
    # 1. Tìm các từ in đậm **Từ Khóa**
    bold_matches = re.findall(r'\*\*([A-Za-z0-9\s\-]{3,35})\*\*', text)
    # 2. Tìm các tiêu đề heading ## Tiêu đề
    heading_matches = re.findall(r'#+\s+([A-Za-z0-9\s\-]{3,35})', text)
    
    candidates = bold_matches + heading_matches
    unique_terms = []
    seen = set()
    
    for c in candidates:
        cleaned = c.strip()
        if len(cleaned) > 2 and cleaned.lower() not in seen and not cleaned.isdigit():
            seen.add(cleaned.lower())
            unique_terms.append(cleaned)
            if len(unique_terms) >= 6:
                break
                
    results = []
    for term in unique_terms:
        results.append({
            "term": term,
            "translation": f"Thuật ngữ: {term}",
            "phonetic": "",
            "audio_url": f"/api/v1/translate/tts?text={urllib.parse.quote(term)}&lang=en-US"
        })
    return results

async def extract_glossary(text: str, target_lang: str = "vi") -> List[Dict[str, Any]]:
    """
    Trích xuất từ khóa và thuật ngữ chuyên ngành từ văn bản bằng LLM với cơ chế fallback tự động.
    """
    if not text or len(text.strip()) == 0:
        return []
        
    sample_text = text[:4000]
    
    prompt = f"""
    You are an expert linguist. Extract a glossary of 5 to 8 important domain-specific terms or keywords from the following text.
    Translate each term into {target_lang} and provide an IPA phonetic transcription if known.
    Return ONLY a valid JSON array of objects with the following format:
    [
      {{"term": "Original Term", "translation": "Translated term", "phonetic": "/.../"}}
    ]
    
    Text:
    {sample_text}
    """
    
    content = ""
    # 1. Thử qua Ollama
    try:
        content = call_ollama_generate(prompt=prompt, system_instruction="Return only JSON array.")
    except Exception as e:
        logger.warning(f"Ollama failed to extract glossary: {e}. Trying Gemini fallback...")
        
    # 2. Thử qua Gemini nếu Ollama chưa trả về kết quả
    if not content or len(content.strip()) == 0:
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                content = response.text.strip()
            except Exception as gemini_err:
                logger.error(f"Gemini fallback failed: {gemini_err}")
                
    # 3. Parse JSON kết quả
    if content:
        try:
            clean_json = content.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
                
            glossary_items = json.loads(clean_json.strip())
            
            if isinstance(glossary_items, list) and len(glossary_items) > 0:
                for item in glossary_items:
                    full_term = str(item.get("term", "")).strip()
                    if full_term:
                        item["audio_url"] = f"/api/v1/translate/tts?text={urllib.parse.quote(full_term)}&lang=en-US"
                        if not item.get("phonetic"):
                            first_word = full_term.split()[0]
                            try:
                                dict_info = await get_word_audio(first_word)
                                if dict_info.get("phonetic"):
                                    item["phonetic"] = dict_info["phonetic"]
                            except Exception:
                                pass
                return glossary_items
        except Exception as parse_err:
            logger.warning(f"Failed to parse LLM glossary JSON ({parse_err}). Falling back to heuristic extractor.")
            
    # 4. Fallback trích xuất Heuristic nếu các LLM không phản hồi
    return heuristic_extract_terms(text)
