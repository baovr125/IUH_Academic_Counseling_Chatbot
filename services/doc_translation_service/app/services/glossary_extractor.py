import json
import httpx
from typing import List, Dict, Any
from app.utils.logger import logger
from app.services.ollama_translator import call_ollama_generate
import google.generativeai as genai
import os

async def get_word_audio(word: str) -> Dict[str, str]:
    """
    Fetches pronunciation audio URL and phonetic from Free Dictionary API.
    Returns {"audio_url": "...", "phonetic": "..."}
    """
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)
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
        except httpx.RequestError as e:
            logger.warning(f"Error fetching dictionary API for {word}: {e}")
            
    return {"phonetic": "", "audio_url": ""}

async def extract_glossary(text: str, target_lang: str = "vi") -> List[Dict[str, Any]]:
    """
    Trích xuất từ khóa và thuật ngữ chuyên ngành từ văn bản bằng LLM.
    Trả về mảng: [{"term": "...", "translation": "..."}, ...]
    """
    if not text or len(text.strip()) == 0:
        return []
        
    # Limit text length to avoid token limits for extraction (use first 5000 chars as sample)
    sample_text = text[:5000]
    
    prompt = f"""
    You are an expert linguist. Extract a glossary of 5 to 10 important domain-specific terms or keywords from the following text.
    Translate each term into {target_lang}.
    Return ONLY a valid JSON array of objects with the following format:
    [
      {{"term": "Original Term", "translation": "Translated term"}}
    ]
    
    Text:
    {sample_text}
    """
    
    content = ""
    try:
        content = call_ollama_generate(prompt=prompt, system_instruction="Return only JSON.")
    except Exception as e:
        logger.warning(f"Ollama failed to extract glossary: {e}. Falling back to Gemini.")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("No GEMINI_API_KEY found, skipping glossary extraction fallback.")
            return []
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        try:
            response = model.generate_content(prompt)
            content = response.text.strip()
        except Exception as gemini_err:
            logger.error(f"Gemini fallback failed: {gemini_err}")
            return []
            
    try:
        # Clean up markdown JSON formatting if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        glossary_items = json.loads(content.strip())
        
        # Now fetch phonetics and audio for each term
        for item in glossary_items:
            term = item.get("term", "").split()[0] # Take first word for dictionary lookup if it's a phrase
            if term:
                dict_info = await get_word_audio(term)
                item["phonetic"] = dict_info["phonetic"]
                item["audio_url"] = dict_info["audio_url"]
                
        return glossary_items
    except Exception as e:
        logger.error(f"Failed to extract glossary: {e}")
        return []
