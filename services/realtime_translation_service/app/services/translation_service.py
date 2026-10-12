import os
import time
import asyncio
import re
from typing import Tuple, Optional, Any
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
from app.services.language_detection import (  # noqa: F401  (re-export cho code/test phụ thuộc)
    LanguageResolutionError,
    SUPPORTED_CODES,
    detect_language_detailed,
    resolve_source_language,
    aresolve_source_language,
)


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


def detect_source_language(text: str) -> str:
    """Tương thích ngược: trả mã ngôn ngữ hoặc ném HTTPException khi chưa xác định được."""
    resolution = resolve_source_language(text, "auto")
    if not resolution.should_translate:
        raise HTTPException(status_code=resolution.http_status, detail=resolution.message)
    return resolution.source_lang


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

async def translate_domain_text(
    text: str, source_lang: str, target_lang: str, domain: str, start_time: float,
    detected_lang: Optional[str], detection_details: Optional[Any],
):
    """Dịch theo chuyên ngành bằng LLM (domain thủ công hoặc auto) cho /text. Trả tuple 8 phần tử."""
    from app.services.domain_translation import collect_domain_translation

    res = await collect_domain_translation(text, source_lang, target_lang, domain)
    if res["error"]:
        raise HTTPException(status_code=503, detail=res["error"]["error"])
    warnings = res["warnings"]
    # Trường `warning` (chuỗi) giữ để tương thích ngược: ưu tiên cảnh báo mức cao nhất.
    legacy = next((w["message"] for w in warnings if w["severity"] != "info"), None)
    if legacy is None and warnings:
        legacy = warnings[0]["message"]
    latency = round((time.perf_counter() - start_time) * 1000, 2)
    return res["text"], res["cached"], latency, legacy, detected_lang, detection_details, res["domain"], warnings


async def translate_text(text: str, source_lang: str = "en", target_lang: str = "vi", domain: str = "", source_lang_hint: Optional[str] = None) -> Tuple[str, bool, float, Optional[str], Optional[str], Optional[Any]]:
    start_time = time.perf_counter()

    detected_lang = None
    uncertain_warning = None

    # Một đường nhận diện duy nhất (dùng chung với /stream và /detect).
    resolution = await aresolve_source_language(text, source_lang, source_lang_hint)
    detection_details = resolution.details
    if not resolution.should_translate:
        raise LanguageResolutionError(resolution)
    if source_lang == "auto":
        source_lang = resolution.source_lang
        detected_lang = source_lang

    if domain and domain != "Dịch thông thường (Mặc định)":
        return await translate_domain_text(
            text, source_lang, target_lang, domain, start_time, detected_lang, detection_details
        )

    text_hash = get_translation_text_hash(text)

    # Generate versioned cache key
    domain_ver = await asyncio.to_thread(get_domain_version, domain)
    cache_key = _translation_cache_key(
        source_lang, target_lang, domain, domain_ver, text_hash,
    )
    
    cached = await asyncio.to_thread(get_cached_translation, cache_key)
    if cached:
        latency = (time.perf_counter() - start_time) * 1000
        from app.services.cache_service import get_cached_warning
        cached_warning = await asyncio.to_thread(get_cached_warning, cache_key)
        final_warning = cached_warning or uncertain_warning
        return cached, True, round(latency, 2), final_warning, detected_lang, detection_details
        
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
                return html_with_placeholders, False, round((time.perf_counter() - start_time) * 1000, 2), uncertain_warning, detected_lang, detection_details
            
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
            return final_translated, False, round(latency, 2), uncertain_warning, detected_lang, detection_details
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
                return translated, False, round(latency, 2), uncertain_warning, detected_lang, detection_details
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
                    return translated, False, round(latency, 2), uncertain_warning, detected_lang, detection_details
            except Exception as e:
                logger.exception(f"Gemini fallback error: {e}")
            
    # No providers succeeded
    raise HTTPException(status_code=503, detail="Tất cả dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.")
