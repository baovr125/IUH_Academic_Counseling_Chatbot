import os
import time
import asyncio
import re
from typing import Tuple, Optional
from fastapi import HTTPException
from app.services.cache_service import get_cached_translation, set_cached_translation
from app.services.llm_service import get_nllb_translator, LANG_MAP, get_gemini_client
from app.services.supabase_client import get_supabase
from app.utils.logger import logger

async def run_nllb_only(text: str, source_lang: str, target_lang: str) -> str:
    translator, tokenizer = get_nllb_translator()
    if not translator or not tokenizer:
        raise RuntimeError("NLLB model is not available.")
        
    nllb_src = LANG_MAP.get(source_lang, "eng_Latn")
    nllb_tgt = LANG_MAP.get(target_lang, "vie_Latn")
    
    from app.utils.html_parser import HTMLTranslator
    html_translator = HTMLTranslator()
    html_with_placeholders, texts_to_translate = html_translator.extract_text(text)
    
    if not texts_to_translate:
        return html_with_placeholders
    
    tokenizer.src_lang = nllb_src
    source_tokens_list = [tokenizer.convert_ids_to_tokens(tokenizer.encode(t)) for t in texts_to_translate]
    target_prefix = [nllb_tgt]

    results = await asyncio.to_thread(
        translator.translate_batch,
        source_tokens_list,
        target_prefix=[target_prefix] * len(texts_to_translate)
    )
    
    translated_texts = []
    for res in results:
        target_tokens = res.hypotheses[0][1:] 
        translated = tokenizer.decode(tokenizer.convert_tokens_to_ids(target_tokens))
        translated_texts.append(translated)
        
    return html_translator.reconstruct_html(html_with_placeholders, translated_texts)

async def handle_flow_2_domain_translation(text: str, source_lang: str, target_lang: str, domain: str, cache_key: str) -> Tuple[str, bool, float, Optional[str]]:
    start_time = time.perf_counter()
    clean_lower = text.strip().lower()
    words = clean_lower.split()
    keyword_count = len(words)
    warning = None

    # Fetch dictionary directly from Supabase
    supabase = get_supabase()
    domain_dict = {}
    if supabase:
        try:
            # Query exact domain
            res = supabase.table("domain_dictionaries").select("word, translation").eq("domain", domain).execute()
            if res.data:
                for entry in res.data:
                    domain_dict[entry["word"].lower()] = entry["translation"]
        except Exception as e:
            logger.error(f"Supabase query error: {e}")

    # Case 1: <= 3 keywords
    if keyword_count <= 3:
        if clean_lower in domain_dict:
            translated = domain_dict[clean_lower]
            set_cached_translation(cache_key, translated)
            return translated, False, round((time.perf_counter() - start_time) * 1000, 2), None
        else:
            # Dictionary Miss -> NLLB + WARNING
            try:
                translated = await run_nllb_only(text, source_lang, target_lang)
                warning = f"Từ/cụm từ này không được tìm thấy trong từ điển chuyên ngành '{domain}'. Hệ thống sử dụng NLLB để dịch thông thường, kết quả có thể không phản ánh đầy đủ nghĩa chuyên ngành."
                set_cached_translation(cache_key, translated)
                return translated, False, round((time.perf_counter() - start_time) * 1000, 2), warning
            except Exception as e:
                logger.error(f"NLLB failed for short missing term: {e}")
                raise HTTPException(status_code=500, detail="Dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.")

    # Case 2: > 3 keywords
    # Terminology scanning with regex \b for whole-word boundary matching
    found_terms = {}
    # Sort keys by length descending to match longest terms first (multi-word)
    sorted_keys = sorted(domain_dict.keys(), key=len, reverse=True)
    for k in sorted_keys:
        pattern = r'\b' + re.escape(k) + r'\b'
        if re.search(pattern, clean_lower):
            found_terms[k] = domain_dict[k]

    if found_terms:
        # Terminology Found -> Groq/Gemini bypass
        client = get_gemini_client()
        if client:
            glossary_str = "\n".join([f"- {k} -> {v}" for k, v in found_terms.items()])
            prompt = f"Translate the following text accurately from {source_lang} to {target_lang}. You MUST use the following glossary for terminology:\n{glossary_str}\n\nOnly output the direct translation without quotes or extra text. Preserve all HTML tags perfectly if present.\n\nText:\n{text}"
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if res and res.text:
                    translated = res.text.strip()
                    set_cached_translation(cache_key, translated)
                    return translated, False, round((time.perf_counter() - start_time) * 1000, 2), None
            except Exception as e:
                logger.exception(f"Groq/Gemini fallback failed in domain translation: {e}")
                
        # If Groq/Gemini failed or client not available -> Fallback NLLB + WARNING
        try:
            translated = await run_nllb_only(text, source_lang, target_lang)
            warning = f"Hệ thống không thể dịch bằng AI model chuyên ngành. Đã sử dụng NLLB, kết quả có thể không phản ánh đầy đủ nghĩa chuyên ngành."
            set_cached_translation(cache_key, translated)
            return translated, False, round((time.perf_counter() - start_time) * 1000, 2), warning
        except Exception as e:
            logger.error(f"NLLB fallback failed: {e}")
            raise HTTPException(status_code=500, detail="Dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.")
    else:
        # Terminology NOT Found -> NLLB (No warning, no Groq fallback)
        try:
            translated = await run_nllb_only(text, source_lang, target_lang)
            set_cached_translation(cache_key, translated)
            return translated, False, round((time.perf_counter() - start_time) * 1000, 2), None
        except Exception as e:
            logger.error(f"NLLB failed for sentence with no terminology: {e}")
            raise HTTPException(status_code=500, detail="Dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.")


async def translate_text(text: str, source_lang: str = "en", target_lang: str = "vi", domain: str = "") -> Tuple[str, bool, float, Optional[str]]:
    start_time = time.perf_counter()
    cache_key = f"{source_lang}_{target_lang}_{domain}_{text.strip().lower()}"
    
    cached = get_cached_translation(cache_key)
    if cached:
        latency = (time.perf_counter() - start_time) * 1000
        return cached, True, round(latency, 2), None
        
    is_flow_2 = domain and domain != "Dịch thông thường (Mặc định)"
    if is_flow_2:
        return await handle_flow_2_domain_translation(text, source_lang, target_lang, domain, cache_key)
        
    # --- FLOW 1 BẮT ĐẦU TỪ ĐÂY (Giữ nguyên) ---
    clean_lower = text.strip().lower()
        
    # Try NLLB first (cost optimized)
    translator, tokenizer = get_nllb_translator()
    if translator and tokenizer:
        nllb_src = LANG_MAP.get(source_lang, "eng_Latn")
        nllb_tgt = LANG_MAP.get(target_lang, "vie_Latn")
        try:
            from app.utils.html_parser import HTMLTranslator
            html_translator = HTMLTranslator()
            html_with_placeholders, texts_to_translate = html_translator.extract_text(text)
            
            if not texts_to_translate:
                # No text to translate (e.g. only images or empty)
                return html_with_placeholders, False, round((time.perf_counter() - start_time) * 1000, 2), None
            
            tokenizer.src_lang = nllb_src
            source_tokens_list = [tokenizer.convert_ids_to_tokens(tokenizer.encode(t)) for t in texts_to_translate]
            target_prefix = [nllb_tgt]

            results = await asyncio.to_thread(
                translator.translate_batch,
                source_tokens_list,
                target_prefix=[target_prefix] * len(texts_to_translate)
            )
            
            translated_texts = []
            for res in results:
                target_tokens = res.hypotheses[0][1:] 
                translated = tokenizer.decode(tokenizer.convert_tokens_to_ids(target_tokens))
                translated_texts.append(translated)
                
            final_translated = html_translator.reconstruct_html(html_with_placeholders, translated_texts)
            
            set_cached_translation(cache_key, final_translated)
            latency = (time.perf_counter() - start_time) * 1000
            return final_translated, False, round(latency, 2), None
        except Exception as e:
            logger.error(f"NLLB translation failed in translate_text: {e}. Falling back to Gemini.")

    # Fallback to LLMs if NLLB fails (Groq -> Gemini)
    from app.services.llm_service import get_groq_client
    groq_client = get_groq_client()
    
    prompt = f"Translate the following text accurately from {source_lang} to {target_lang}. Only output the direct translation without quotes or extra text. Preserve all HTML tags perfectly if present.\n\n{text}"
    
    use_fallback = False
    if groq_client:
        try:
            res = await groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a professional translator. Preserve HTML perfectly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            if res.choices and res.choices[0].message.content:
                translated = res.choices[0].message.content.strip()
                set_cached_translation(cache_key, translated)
                latency = (time.perf_counter() - start_time) * 1000
                return translated, False, round(latency, 2), None
        except Exception as e:
            logger.warning(f"Groq fallback failed: {e}. Falling back to Gemini.")
            use_fallback = True
    else:
        use_fallback = True

    if use_fallback:
        client = get_gemini_client()
        if client:
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if res and res.text:
                    translated = res.text.strip()
                    set_cached_translation(cache_key, translated)
                    latency = (time.perf_counter() - start_time) * 1000
                    return translated, False, round(latency, 2), None
            except Exception as e:
                logger.exception(f"Gemini fallback error: {e}")
            
    # Mock fallback
    translated = f"[Bản dịch: {text}]"
    latency = (time.perf_counter() - start_time) * 1000
    return translated, False, round(latency, 2), None
