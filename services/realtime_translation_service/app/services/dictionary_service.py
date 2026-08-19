import httpx
import re
import urllib.parse
from typing import Optional, Dict, Any
from app.utils.logger import logger

USER_AGENT = "IUHAcademicCounselingBot/1.0 (https://iuh.edu.vn; contact@iuh.edu.vn) Python-httpx/0.24"

async def fetch_remote_audio_bytes(audio_url: str) -> Optional[bytes]:
    """Tải binary audio từ URL từ điển bên ngoài với header hợp lệ."""
    if not audio_url:
        return None
    
    # Fix protocol-relative URLs (e.g., //ssl.gstatic.com/...)
    if audio_url.startswith("//"):
        audio_url = f"https:{audio_url}"
        
    async with httpx.AsyncClient(follow_redirects=True, timeout=8.0) as client:
        try:
            headers = {"User-Agent": USER_AGENT}
            response = await client.get(audio_url, headers=headers)
            if response.status_code == 200 and len(response.content) > 500:
                return response.content
        except Exception as e:
            logger.debug(f"Failed to fetch audio bytes from {audio_url}: {e}")
    return None


async def get_english_lexicon(word: str) -> Optional[Dict[str, Any]]:
    """Tra cứu phát âm Tiếng Anh chuẩn từ Free Dictionary API."""
    clean_word = word.strip().lower()
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(clean_word)}"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url, headers={"User-Agent": USER_AGENT})
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    entry = data[0]
                    phonetic = entry.get("phonetic", "")
                    audio_url = ""
                    
                    # Ưu tiên audio US -> UK -> audio đầu tiên có sẵn
                    phonetics = entry.get("phonetics", [])
                    for p in phonetics:
                        a_url = p.get("audio", "")
                        if not phonetic and p.get("text"):
                            phonetic = p.get("text")
                        if "-us.mp3" in a_url:
                            audio_url = a_url
                            break
                        elif not audio_url and a_url:
                            audio_url = a_url
                            
                    # Clean IPA
                    if phonetic:
                        phonetic = phonetic.strip().strip("/").strip("[]")
                        phonetic = f"/{phonetic}/"
                        
                    return {
                        "phonetic": phonetic,
                        "audio_url": audio_url,
                        "lang": "en"
                    }
        except Exception as e:
            logger.debug(f"Free Dictionary API error for '{word}': {e}")
            
    return None


async def get_german_lexicon(word: str) -> Optional[Dict[str, Any]]:
    """
    Tra cứu phát âm Tiếng Đức chuẩn từ Wiktionary Đức (de.wiktionary.org).
    Lấy ký hiệu IPA chuẩn {{Lautschrift|...}} và file âm thanh bản xứ {{Audio|De-...ogg}}.
    """
    clean_word = word.strip()
    # German nouns often start with uppercase
    variations = [clean_word, clean_word.capitalize(), clean_word.lower()]
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for query_term in dict.fromkeys(variations):
            url = f"https://de.wiktionary.org/w/api.php?action=parse&page={urllib.parse.quote(query_term)}&prop=wikitext&format=json"
            try:
                response = await client.get(url, headers={"User-Agent": USER_AGENT})
                if response.status_code == 200:
                    data = response.json()
                    wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                    if not wikitext:
                        continue
                        
                    # 1. Trích xuất IPA từ template Lautschrift
                    # Ví dụ: {{Lautschrift|ˈkʁaŋkn̩ˌhaʊ̯s}} hoặc {{IPA}} {{Lautschrift|...}}
                    phonetic = ""
                    ipa_match = re.search(r"\{\{Lautschrift\|([^}|]+)\}\}", wikitext)
                    if ipa_match:
                        raw_ipa = ipa_match.group(1).strip()
                        phonetic = f"/{raw_ipa}/"
                        
                    # 2. Trích xuất file Audio từ template Audio
                    # Ví dụ: {{Audio|De-Krankenhaus.ogg|Audio}} hoặc {{Audio|De-Arbeit.ogg}}
                    audio_url = ""
                    audio_match = re.search(r"\{\{Audio\|([^}|]+\.(?:ogg|mp3))", wikitext, re.IGNORECASE)
                    if audio_match:
                        file_name = audio_match.group(1).strip()
                        audio_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(file_name)}"
                        
                    if phonetic or audio_url:
                        return {
                            "phonetic": phonetic,
                            "audio_url": audio_url,
                            "lang": "de"
                        }
            except Exception as e:
                logger.debug(f"German Wiktionary API error for '{query_term}': {e}")
                
    return None


async def get_word_audio(word: str, lang: str = "en") -> Optional[Dict[str, Any]]:
    """
    Hàm tra cứu phát âm từ điển chuẩn cho cả Tiếng Anh và Tiếng Đức.
    Trả về dict {'phonetic': '...', 'audio_url': '...', 'audio_bytes': Optional[bytes]}
    """
    lang_clean = (lang or "en").strip().lower()
    prefix = lang_clean[:2]
    
    result = None
    if prefix == "de":
        result = await get_german_lexicon(word)
    elif prefix == "en":
        result = await get_english_lexicon(word)
        
    if result and result.get("audio_url"):
        # Thử tải trước audio bytes nếu có URL hợp lệ
        bytes_data = await fetch_remote_audio_bytes(result["audio_url"])
        result["audio_bytes"] = bytes_data
    elif result:
        result["audio_bytes"] = None
        
    return result
