import os
import re
import json
import httpx
import asyncio
import hashlib
import urllib.parse
from typing import List, Dict, Any
from app.utils.logger import logger
from app.services.ollama_translator import call_ollama_generate, check_ollama_health


async def get_word_audio(word: str) -> Dict[str, str]:
    """
    Fetches pronunciation audio URL and phonetic from Free Dictionary API.
    Returns {"audio_url": "...", "phonetic": "..."}
    """
    clean_word = re.sub(r'[^a-zA-Z]', '', word).strip()
    if not clean_word:
        return {"phonetic": "", "audio_url": ""}
        
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{clean_word}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=1.5)
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


def get_tts_lang_code(lang: str) -> str:
    cleaned = (lang or "en").strip().lower()
    mapping = {
        "en": "en-US",
        "vi": "vi-VN",
        "de": "de-DE",
        "zh": "zh-CN",
        "ja": "ja-JP",
        "ko": "ko-KR",
        "fr": "fr-FR",
        "es": "es-ES",
        "ru": "ru-RU",
        "th": "th-TH"
    }
    return mapping.get(cleaned, mapping.get(cleaned[:2], "en-US"))


def parse_glossary_json(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parse robustly bất kỳ định dạng JSON trả về từ LLM (vLLM / Ollama / Gemini).
    Hỗ trợ:
    - Mảng trực tiếp: [ {"term": "...", "translation": "..."}, ... ]
    - Object có key: {"glossary": [...]}, {"terms": [...]}, {"items": [...]}, ...
    - Object dạng key-value: {"1": {...}, "2": {...}}
    """
    if not raw_text or not raw_text.strip():
        return []
    
    clean_text = raw_text.strip()
    
    # Loại bỏ markdown code fence nếu có
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()

    data = None
    try:
        data = json.loads(clean_text)
    except Exception:
        # Regex tìm Object hoặc Array
        obj_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        arr_match = re.search(r'\[.*\]', clean_text, re.DOTALL)
        
        if obj_match:
            try:
                data = json.loads(obj_match.group(0))
            except Exception:
                pass
        if data is None and arr_match:
            try:
                data = json.loads(arr_match.group(0))
            except Exception:
                pass

    if data is None:
        return []

    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ["glossary", "terms", "items", "data", "keywords", "vocabulary", "glossary_items"]:
            if key in data and isinstance(data[key], list):
                items = data[key]
                break
        if not items:
            for v in data.values():
                if isinstance(v, list):
                    items = v
                    break
            if not items and all(isinstance(v, dict) for v in data.values()):
                items = list(data.values())

    cleaned_items = []
    for item in items:
        if isinstance(item, dict) and item.get("term"):
            term_str = str(item.get("term", "")).strip()
            # Lấy nghĩa dịch từ translation, vi hoặc meaning
            meaning_str = str(item.get("translation") or item.get("vi") or item.get("meaning") or "").strip()
            
            # Chỉ giữ lại nếu term và translation khác nhau và không phải chuỗi rỗng
            if term_str and meaning_str and term_str.lower() != meaning_str.lower():
                cleaned_items.append({
                    "term": term_str,
                    "translation": meaning_str,
                    "vi": meaning_str,
                    "phonetic": str(item.get("phonetic", "")).strip(),
                    "context": str(item.get("context", "")).strip()
                })
    return cleaned_items


def filter_invalid_terms(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Loại bỏ các tiêu đề chương mục tài liệu như '1 Introduction', 'Abstract', '2 Method', v.v.
    Áp dụng cả fuzzy match cho multi-word headings (ví dụ: 'Related Work Overview').
    """
    stop_headings = {
        "abstract", "introduction", "method", "methods", "methodology",
        "results", "discussion", "conclusion", "conclusions", "references",
        "acknowledgments", "acknowledgements", "appendix", "background",
        "related work", "experimental setup", "evaluation", "overview",
        "table", "figure", "fig", "tab"
    }
    valid = []
    seen = set()
    for c in candidates:
        raw_term = c.get("term", "").strip()
        # Bỏ các số thứ tự mục (ví dụ '1 Introduction' -> 'Introduction', '2.1 Architecture' -> 'Architecture')
        term = re.sub(r'^\d+(\.\d+)*\s*', '', raw_term).strip()
        term_lower = term.lower()

        if not term or len(term) < 3 or term.isdigit():
            continue

        # Exact match hoặc fuzzy: nếu term_lower chứa một stop_heading đầy đủ
        if term_lower in stop_headings:
            continue
        if any(heading in term_lower for heading in stop_headings):
            continue
        if term_lower in seen:
            continue
            
        seen.add(term_lower)
        c["term"] = term
        valid.append(c)
    return valid


def heuristic_extract_terms(text: str, source_lang: str = "en") -> List[Dict[str, Any]]:
    """Phương thức dự phòng trích xuất thuật ngữ chuyên ngành dựa trên Markdown syntax."""
    bold_matches = re.findall(r'\*\*([A-Za-z0-9\s\-]{3,40})\*\*', text)
    
    candidates = bold_matches  # Chỉ lấy bold text, không lấy headings (dễ lẫn với chapter titles)
    unique_terms = []
    seen = set()
    
    for c in candidates:
        cleaned = c.strip()
        if len(cleaned) > 2 and cleaned.lower() not in seen and not cleaned.isdigit():
            seen.add(cleaned.lower())
            unique_terms.append(cleaned)
            if len(unique_terms) >= 8:
                break
                
    clean_lang = (source_lang or "en").strip().lower()[:2]
    results = []
    for term in unique_terms:
        term_clean = term.strip().lower()
        term_hash = hashlib.md5(f"{clean_lang}_{term_clean}".encode('utf-8')).hexdigest()
        results.append({
            "term": term,
            "translation": "",
            "vi": "",
            "context": f"Thuật ngữ chuyên ngành ({source_lang.upper()})",
            "phonetic": "",
            "audio_url": f"/api/v1/translate/audio/terms/{clean_lang}_{term_hash}.mp3",
            "lang_code": source_lang
        })
    return filter_invalid_terms(results)


def translate_term_candidates(terms: List[str], target_lang: str = "vi", source_lang: str = "en") -> Dict[str, str]:
    """Dịch nhanh danh sách thuật ngữ trích xuất qua LLM / Gemini."""
    if not terms:
        return {}
        
    lang_map = {"vi": "Vietnamese", "en": "English", "fr": "French", "es": "Spanish"}
    target_lang_name = lang_map.get(target_lang, target_lang)
    
    prompt = (
        f"Translate these {len(terms)} technical domain terms from {source_lang.upper()} to {target_lang_name}.\n"
        f"Return ONLY a valid JSON object in format: {{\"term_english\": \"translation_in_{target_lang_name}\"}}\n\n"
        f"Terms:\n" + "\n".join([f"- {t}" for t in terms])
    )
    
    if check_ollama_health():
        try:
            res = call_ollama_generate(prompt=prompt, format="json", system_instruction="Return only JSON key-value pairs.")
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return {k.strip(): str(v).strip() for k, v in parsed.items()}
        except Exception:
            pass
            
    try:
        from app.services.translator import get_gemini_client
        client = get_gemini_client()
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        if res and res.text:
            match = re.search(r'\{.*\}', res.text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return {k.strip(): str(v).strip() for k, v in parsed.items()}
    except Exception:
        pass
        
    return {}


async def extract_glossary(text: str, target_lang: str = "vi", source_lang: str = "en") -> List[Dict[str, Any]]:
    """
    Trích xuất từ khóa và thuật ngữ chuyên ngành từ văn bản bằng LLM với cơ chế fallback 3 tầng tự động.
    """
    if not text or len(text.strip()) == 0:
        return []
        
    sample_text = text[:4000]
    clean_lang = (source_lang or "en").strip().lower()[:2]
    lang_map = {"vi": "Vietnamese", "en": "English", "fr": "French", "es": "Spanish"}
    target_lang_name = lang_map.get(target_lang, target_lang)
    
    prompt = f"""
    You are an expert academic translator and domain terminologist.
    Extract 5 to 8 important technical domain terms and keywords from the academic text below.
    
    IMPORTANT RULES:
    1. Do NOT extract structural document headings or section labels (such as "Abstract", "1 Introduction", "2 Method", "Conclusion", "References").
    2. Extract only actual technical concepts, algorithms, methods, or domain keywords (for example: "Machine Translation", "BLEU score", "Encoder-Decoder", "Back-propagation").
    3. You MUST provide the accurate and natural translation in {target_lang_name} for each term.
    
    Return a valid JSON object with the "glossary" key:
    {{
      "glossary": [
        {{
          "term": "English Technical Term",
          "translation": "Translated Meaning in {target_lang_name}",
          "phonetic": "/.../",
          "context": "Brief usage context"
        }}
      ]
    }}
    
    Text:
    {sample_text}
    """
    
    glossary_items: List[Dict[str, Any]] = []
    
    # ── TẦNG 1: Thử qua vLLM / Ollama ──
    if check_ollama_health():
        try:
            content = call_ollama_generate(
                prompt=prompt, 
                system_instruction="You are a JSON generator. Return only a valid JSON object containing a 'glossary' array.",
                format="json"
            )
            glossary_items = parse_glossary_json(content)
        except Exception as e:
            logger.warning(f"vLLM/Ollama failed to extract glossary ({e}). Trying Gemini fallback...")
    else:
        logger.info("LLM/vLLM server not reachable, switching directly to Gemini fallback for glossary extraction.")
        
    # ── TẦNG 2: Thử qua Gemini Fallback nếu Tầng 1 chưa có kết quả ──
    if not glossary_items:
        try:
            from app.services.translator import get_gemini_client
            client = get_gemini_client()
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            if res and res.text:
                glossary_items = parse_glossary_json(res.text)
        except Exception as gemini_err:
            logger.error(f"Gemini fallback failed for glossary: {gemini_err}")
                
    # ── TẦNG 3: Fallback Heuristic + Dịch thuật danh sách từ ──
    if not glossary_items:
        candidate_objs = heuristic_extract_terms(text, source_lang=source_lang)
        term_names = [c["term"] for c in candidate_objs]
        if term_names:
            translations_map = translate_term_candidates(term_names, target_lang=target_lang, source_lang=source_lang)
            for c in candidate_objs:
                t_name = c["term"]
                meaning = translations_map.get(t_name, "")
                if meaning and meaning.lower() != t_name.lower():
                    c["translation"] = meaning
                    c["vi"] = meaning
                    glossary_items.append(c)
                    
        # Nếu vẫn không dịch được nghĩa, chỉ giữ lại các từ candidate cơ bản
        if not glossary_items and candidate_objs:
            glossary_items = candidate_objs[:6]

    # Làm giàu thêm thông tin phát âm & âm thanh (non-blocking, asyncio đã được import ở top-level)
    if glossary_items:
        async def enrich_item(item):
            full_term = str(item.get("term", "")).strip()
            if full_term:
                term_clean = full_term.lower()
                term_hash = hashlib.md5(f"{clean_lang}_{term_clean}".encode('utf-8')).hexdigest()
                item["audio_url"] = f"/api/v1/translate/audio/terms/{clean_lang}_{term_hash}.mp3"
                item["lang_code"] = source_lang
                meaning = item.get("translation") or item.get("vi", "")
                item["translation"] = meaning
                item["vi"] = meaning
                
                if not item.get("phonetic"):
                    first_word = full_term.split()[0]
                    try:
                        dict_info = await get_word_audio(first_word)
                        if dict_info.get("phonetic"):
                            item["phonetic"] = dict_info["phonetic"]
                    except Exception:
                        pass
        
        await asyncio.gather(*(enrich_item(item) for item in glossary_items))
        
    return glossary_items
