import os
import time
import asyncio
import re
from typing import Tuple, Optional
from fastapi import HTTPException
from app.services.cache_service import (
    get_cached_translation,
    get_translation_text_hash,
    set_cached_translation,
    get_domain_version,
)
from app.services.llm_service import get_nllb_translator, LANG_MAP, get_gemini_client
from app.services.supabase_client import get_supabase
from app.utils.logger import logger
from app.utils.text_normalizer import find_domain_terms, build_context_aware_prompt
from functools import lru_cache
from lingua import Language, LanguageDetectorBuilder

DETECT_MIN_CONFIDENCE = float(os.getenv("DETECT_MIN_CONFIDENCE", "0.45"))
DETECT_MIN_MARGIN = float(os.getenv("DETECT_MIN_MARGIN", "0.12"))
FAST_THRESHOLD = float(os.getenv("DETECT_FAST_THRESHOLD", "0.85"))

SUPPORTED_LANGUAGES = {
    Language.ENGLISH: "en",
    Language.GERMAN: "de",
    Language.CHINESE: "zh",
    Language.JAPANESE: "ja",
    Language.KOREAN: "ko",
    Language.FRENCH: "fr",
    Language.SPANISH: "es",
    Language.RUSSIAN: "ru",
    Language.THAI: "th",
    Language.VIETNAMESE: "vi",
}
GERMAN_MARKERS = {
    "aber", "das", "der", "die", "du", "eine", "einen", "für", "habe",
    "ich", "ihr", "ist", "mit", "nicht", "sein", "sind", "und", "wir",
}
FRENCH_MARKERS = {
    "je", "tu", "il", "elle", "nous", "vous", "les", "des",
    "est", "sont", "dans", "avec", "pour", "sur", "qui", "que",
    "une", "cette", "aussi", "mais", "très", "comme", "être",
}
SPANISH_MARKERS = {
    "yo", "tú", "él", "ella", "nosotros", "los", "las", "está",
    "son", "pero", "como", "para", "por", "también", "más",
    "una", "este", "esta", "ese", "puede", "tiene", "hacer",
}


def _translation_cache_key(
    source_lang: str,
    target_lang: str,
    domain: str,
    domain_version: int,
    text_hash: str,
    *,
    auto_selected: bool = False,
) -> str:
    """Version translation entries and keep auto/manual metadata isolated."""
    origin = "auto" if auto_selected else "direct"
    return f"translation_v2_{source_lang}_{target_lang}_{domain}_{origin}_v{domain_version}_{text_hash}"


def _gemini_timeout_seconds() -> float:
    try:
        return max(0.1, float(os.getenv("GEMINI_REQUEST_TIMEOUT_SECONDS", "20")))
    except (TypeError, ValueError):
        return 20.0


@lru_cache(maxsize=1)
def _get_language_detector():
    return LanguageDetectorBuilder.from_languages(*SUPPORTED_LANGUAGES.keys()).build()

def detect_source_language(text: str) -> str:
    from app.utils.html_parser import HTMLTranslator

    html_translator = HTMLTranslator()
    _, texts = html_translator.extract_text(text)
    clean_text = " ".join(texts).strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Vui lòng nhập văn bản để nhận diện ngôn ngữ.")

    # Minimum length ambiguity rule
    word_count = len(clean_text.split())
    
    # 1. Fast path: fastText (< 1ms)
    try:
        from app.services.fasttext_detector import fasttext_detect
        ft_lang, ft_score, ft_margin = fasttext_detect(clean_text)
        is_ft_uncertain = ft_score < DETECT_MIN_CONFIDENCE or ft_margin < DETECT_MIN_MARGIN
        if word_count < 3 and ft_score < 0.95:
            is_ft_uncertain = True
            
        if ft_lang and ft_score >= FAST_THRESHOLD and not is_ft_uncertain:
            logger.info("LangDetect FAST", extra={"engine": "fasttext", "lang": ft_lang, "score": ft_score, "margin": ft_margin, "input_length": len(clean_text)})
            return ft_lang
    except Exception as e:
        logger.warning(f"fastText fallback error: {e}")

    # 2. Accurate path: Lingua (5-30ms)
    try:
        confidence_values = _get_language_detector().compute_language_confidence_values(clean_text)
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        raise HTTPException(status_code=503, detail="Không thể nhận diện ngôn ngữ lúc này. Vui lòng thử lại hoặc chọn ngôn ngữ nguồn thủ công.") from e

    if not confidence_values:
        raise HTTPException(status_code=400, detail="Chưa đủ thông tin để xác định ngôn ngữ. Hãy nhập thêm văn bản hoặc chọn ngôn ngữ nguồn thủ công.")

    detected = confidence_values[0].language
    top_confidence = confidence_values[0].value
    second_confidence = confidence_values[1].value if len(confidence_values) > 1 else 0.0
    is_uncertain = top_confidence < DETECT_MIN_CONFIDENCE or top_confidence - second_confidence < DETECT_MIN_MARGIN
    if word_count < 3 and top_confidence < 0.95:
        is_uncertain = True

    logger.info(
        "LangDetect LINGUA",
        extra={
            "engine": "lingua",
            "top_lang": str(detected),
            "top_confidence": round(top_confidence, 4),
            "second_lang": str(confidence_values[1].language) if len(confidence_values) > 1 else "N/A",
            "second_confidence": round(second_confidence, 4),
            "margin": round(top_confidence - second_confidence, 4),
            "is_uncertain": is_uncertain,
            "input_length": len(clean_text),
        }
    )

    if is_uncertain:
        words = set(re.findall(r"\b\w+\b", clean_text.casefold()))
        if words & GERMAN_MARKERS:
            detected = Language.GERMAN
            logger.info("LangDetect MARKERS", extra={"engine": "markers", "lang": "de"})
        elif words & FRENCH_MARKERS:
            detected = Language.FRENCH
            logger.info("LangDetect MARKERS", extra={"engine": "markers", "lang": "fr"})
        elif words & SPANISH_MARKERS:
            detected = Language.SPANISH
            logger.info("LangDetect MARKERS", extra={"engine": "markers", "lang": "es"})
        else:
            logger.warning("LangDetect UNCERTAIN - Requesting manual selection")
            raise HTTPException(
                status_code=400,
                detail="Chưa đủ thông tin để xác định ngôn ngữ. Hãy nhập thêm văn bản hoặc chọn ngôn ngữ nguồn thủ công.",
            )

    language_code = SUPPORTED_LANGUAGES.get(detected)
    if language_code not in LANG_MAP:
        raise HTTPException(
            status_code=400,
            detail="Chưa đủ thông tin để xác định ngôn ngữ. Hãy nhập thêm văn bản hoặc chọn ngôn ngữ nguồn thủ công.",
        )
    return language_code

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

    # Auto Domain Logic
    if domain == "auto":
        from app.services.domain_service import auto_detect_domain_long, get_combined_short_translation
        from app.services.cache_service import (
            set_auto_resolved_domain,
            get_domain_version,
            get_classification_hash,
            get_translation_text_hash,
        )
        
        prefix_md5 = get_classification_hash(text)
        
        # We only support dictionary auto-domain for EN -> VI right now
        if source_lang != "en" or target_lang != "vi":
            domain = ""
            warning = "Tính năng tự động nhận diện chuyên ngành hiện chỉ hỗ trợ cặp ngôn ngữ Anh-Việt. Chuyển sang dịch thông thường."
        elif len(text.strip()) < 25 or keyword_count <= 3:
            # Short text scanning
            combined = await get_combined_short_translation(text)
            if combined:
                combined_warning = "Tra cứu đa nghĩa (Multi-domain lookup) do văn bản ngắn:\n\n" + combined
                # We do NOT return the combined string as translation to preserve TTS and Flashcard logic.
                # Instead, fallback to NLLB and attach the combined string as warning metadata.
                try:
                    translated = await run_nllb_only(text, source_lang, target_lang)
                    # Cache key hasn't changed since it's still 'auto', but it's safe for exact word
                    await asyncio.to_thread(set_cached_translation, cache_key, translated, combined_warning)
                    return translated, False, round((time.perf_counter() - start_time) * 1000, 2), combined_warning
                except Exception as e:
                    logger.error(f"NLLB fallback failed for short auto domain: {e}")
                    raise HTTPException(status_code=500, detail="Translation error.")
            domain = "" # No dict entries found across any domain
            warning = "Không tìm thấy từ vựng phù hợp để tra cứu đa miền. Chuyển sang dịch thông thường."
        else:
            # Long text zero-shot classification
            detected_domain = await auto_detect_domain_long(text)
            if detected_domain:
                warning = f"Đã tự động nhận diện chuyên ngành: {detected_domain}"
                domain = detected_domain
                # Remember this resolution for future cache hits
                await asyncio.to_thread(set_auto_resolved_domain, prefix_md5, source_lang, target_lang, detected_domain)
                
                # Fix Cache Bug: Update cache_key for the DETECTED domain
                domain_ver = await asyncio.to_thread(get_domain_version, domain)
                text_hash = get_translation_text_hash(text)
                cache_key = _translation_cache_key(
                    source_lang, target_lang, domain, domain_ver, text_hash, auto_selected=True
                )
            else:
                domain = ""
                warning = "Không thể xác định chuyên ngành, hoặc chuyên ngành không được hỗ trợ. Chuyển sang dịch thông thường."

    if not domain:
        try:
            translated = await run_nllb_only(text, source_lang, target_lang)
            await asyncio.to_thread(set_cached_translation, cache_key, translated, warning)
            return translated, False, round((time.perf_counter() - start_time) * 1000, 2), warning
        except Exception as e:
            logger.error(f"NLLB failed for empty domain fallback: {e}")
            raise HTTPException(status_code=500, detail="Dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.")

    # Fetch dictionary directly from Supabase for the resolved domain
    supabase = get_supabase()
    domain_dict = {}
    if domain and domain != "auto":
        if supabase:
            try:
                def fetch_supabase():
                    return supabase.table("domain_dictionaries").select("word, translation").eq("domain", domain).execute()
                res = await asyncio.to_thread(fetch_supabase)
                if res.data:
                    for entry in res.data:
                        domain_dict[entry["word"].lower()] = entry["translation"]
            except Exception as e:
                logger.error(f"Supabase query error: {e}")

    # Case 1: <= 3 keywords
    if keyword_count <= 3:
        if clean_lower in domain_dict:
            translated = domain_dict[clean_lower]
            await asyncio.to_thread(set_cached_translation, cache_key, translated, warning)
            return translated, False, round((time.perf_counter() - start_time) * 1000, 2), warning
        else:
            # Dictionary Miss -> NLLB + WARNING
            try:
                translated = await run_nllb_only(text, source_lang, target_lang)
                warning = f"Từ/cụm từ này không được tìm thấy trong từ điển chuyên ngành '{domain}'. Hệ thống sử dụng NLLB để dịch thông thường, kết quả có thể không phản ánh đầy đủ nghĩa chuyên ngành."
                await asyncio.to_thread(set_cached_translation, cache_key, translated, warning)
                return translated, False, round((time.perf_counter() - start_time) * 1000, 2), warning
            except Exception as e:
                logger.error(f"NLLB failed for short missing term: {e}")
                raise HTTPException(status_code=500, detail="Dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.")

    # Case 2: > 3 keywords
    # Terminology scanning with morphological suffix matching
    found_terms = find_domain_terms(text, domain_dict)

    if found_terms:
        # Terminology Found -> Groq/Gemini bypass
        client = get_gemini_client()
        if client:
            prompt = build_context_aware_prompt(domain, found_terms, source_lang, target_lang)
            prompt += f"\n\nText:\n{text}"
            try:
                res = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                    ),
                    timeout=_gemini_timeout_seconds(),
                )
                if res and res.text:
                    translated = res.text.strip()
                    await asyncio.to_thread(set_cached_translation, cache_key, translated, warning)
                    return translated, False, round((time.perf_counter() - start_time) * 1000, 2), warning
            except Exception as e:
                logger.exception(f"Groq/Gemini fallback failed in domain translation: {e}")
                
        # If Groq/Gemini failed or client not available -> Fallback NLLB + WARNING
        try:
            translated = await run_nllb_only(text, source_lang, target_lang)
            warning = f"Hệ thống không thể dịch bằng AI model chuyên ngành. Đã sử dụng NLLB, kết quả có thể không phản ánh đầy đủ nghĩa chuyên ngành."
            await asyncio.to_thread(set_cached_translation, cache_key, translated, warning)
            return translated, False, round((time.perf_counter() - start_time) * 1000, 2), warning
        except Exception as e:
            logger.error(f"NLLB fallback failed: {e}")
            raise HTTPException(status_code=500, detail="Dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.")
    else:
        # Terminology NOT Found -> NLLB (No warning, no Groq fallback)
        try:
            translated = await run_nllb_only(text, source_lang, target_lang)
            await asyncio.to_thread(set_cached_translation, cache_key, translated, warning)
            return translated, False, round((time.perf_counter() - start_time) * 1000, 2), warning
        except Exception as e:
            logger.error(f"NLLB failed for sentence with no terminology: {e}")
            raise HTTPException(status_code=500, detail="Dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.")


async def translate_text(text: str, source_lang: str = "en", target_lang: str = "vi", domain: str = "") -> Tuple[str, bool, float, Optional[str], Optional[str]]:
    start_time = time.perf_counter()
    
    detected_lang = None
    if source_lang == "auto":
        detected_lang = detect_source_language(text)
        source_lang = detected_lang
        
    requested_auto_domain = domain == "auto"
    text_hash = get_translation_text_hash(text)
    
    if domain == "auto":
        from app.services.cache_service import get_auto_resolved_domain, get_classification_hash
        prefix_md5 = get_classification_hash(text)
        resolved = await asyncio.to_thread(get_auto_resolved_domain, prefix_md5, source_lang, target_lang)
        if resolved:
            domain = resolved
            
    # Generate versioned cache key
    domain_ver = await asyncio.to_thread(get_domain_version, domain)
    cache_key = _translation_cache_key(
        source_lang, target_lang, domain, domain_ver, text_hash,
        auto_selected=requested_auto_domain,
    )
    
    cached = await asyncio.to_thread(get_cached_translation, cache_key)
    if cached:
        latency = (time.perf_counter() - start_time) * 1000
        from app.services.cache_service import get_cached_warning
        cached_warning = await asyncio.to_thread(get_cached_warning, cache_key)
        return cached, True, round(latency, 2), cached_warning, detected_lang
        
    is_flow_2 = domain and domain != "Dịch thông thường (Mặc định)"
    if is_flow_2:
        res = await handle_flow_2_domain_translation(text, source_lang, target_lang, domain, cache_key)
        return res[0], res[1], res[2], res[3], detected_lang
        
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
                return html_with_placeholders, False, round((time.perf_counter() - start_time) * 1000, 2), None, detected_lang
            
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
            
            await asyncio.to_thread(set_cached_translation, cache_key, final_translated)
            latency = (time.perf_counter() - start_time) * 1000
            return final_translated, False, round(latency, 2), None, detected_lang
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
                await asyncio.to_thread(set_cached_translation, cache_key, translated)
                latency = (time.perf_counter() - start_time) * 1000
                return translated, False, round(latency, 2), None, detected_lang
        except Exception as e:
            logger.warning(f"Groq fallback failed: {e}. Falling back to Gemini.")
            use_fallback = True
    else:
        use_fallback = True

    if use_fallback:
        client = get_gemini_client()
        if client:
            try:
                res = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                    ),
                    timeout=_gemini_timeout_seconds(),
                )
                if res and res.text:
                    translated = res.text.strip()
                    await asyncio.to_thread(set_cached_translation, cache_key, translated)
                    latency = (time.perf_counter() - start_time) * 1000
                    return translated, False, round(latency, 2), None, detected_lang
            except Exception as e:
                logger.exception(f"Gemini fallback error: {e}")
            
    # No providers succeeded
    raise HTTPException(status_code=503, detail="Tất cả dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.")
