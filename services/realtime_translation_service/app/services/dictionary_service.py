import httpx
from typing import Optional, Dict

async def get_word_audio(word: str) -> Optional[Dict[str, str]]:
    """
    Fetches pronunciation audio URL and phonetic from Free Dictionary API.
    Returns {"audio_url": "...", "phonetic": "..."} or None if not found.
    """
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    entry = data[0]
                    
                    # Extract phonetic
                    phonetic = entry.get("phonetic", "")
                    
                    # Extract audio url (some phonetics might not have audio, we need to iterate)
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
            print(f"Error fetching dictionary API for {word}: {e}")
            
    return None
