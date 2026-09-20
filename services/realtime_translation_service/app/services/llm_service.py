import os
import json
import asyncio
import ctranslate2
import transformers
from typing import AsyncGenerator, Optional
import httpx
from google import genai
from groq import Groq, AsyncGroq
from app.utils.logger import logger

# Initialize Clients
_translator = None
_tokenizer = None

def get_nllb_translator():
    global _translator, _tokenizer
    if _translator is not None and _tokenizer is not None:
        return _translator, _tokenizer

    candidate_paths = [
        "/app/models/nllb-200-distilled-600M-ct2-int8",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../models/nllb-200-distilled-600M-ct2-int8")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models/nllb-200-distilled-600M-ct2-int8")),
        "./models/nllb-200-distilled-600M-ct2-int8"
    ]
    model_dir = None
    for p in candidate_paths:
        if os.path.exists(p):
            model_dir = p
            break

    if not model_dir:
        logger.warning(f"NLLB model directory not found in candidate paths: {candidate_paths}. Cannot initialize CTranslate2.")
        return None, None

    try:
        cuda_available = False
        try:
            if ctranslate2.get_cuda_device_count() > 0:
                cuda_available = True
        except Exception:
            pass

        device = "cuda" if cuda_available else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        logger.info(f"Loading NLLB CTranslate2 model on {device.upper()} ({compute_type})...")
        _translator = ctranslate2.Translator(
            model_dir,
            device=device,
            compute_type=compute_type,
            inter_threads=2,
            intra_threads=2
        )
        logger.info("Loading NLLB Tokenizer...")
        _tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir)
        return _translator, _tokenizer
    except Exception as e:
        logger.error(f"Failed to load NLLB model on {device}: {e}. Retrying on CPU INT8 fallback...")
        try:
            _translator = ctranslate2.Translator(
                model_dir,
                device="cpu",
                compute_type="int8",
                inter_threads=2,
                intra_threads=2
            )
            _tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir)
            return _translator, _tokenizer
        except Exception as cpu_err:
            logger.error(f"Failed to load NLLB model on CPU fallback: {cpu_err}")
            return None, None

def preload_models():
    """Preloads the local translation models into memory (VRAM if available) at startup."""
    logger.info("Preloading local NLLB models...")
    translator, tokenizer = get_nllb_translator()
    
    if translator and tokenizer:
        logger.info("Running dummy inference to warm up CUDA memory allocation...")
        try:
            # Dummy inference to trigger memory allocation and kernel compilation
            nllb_src = LANG_MAP.get("en", "eng_Latn")
            nllb_tgt = LANG_MAP.get("vi", "vie_Latn")
            tokenizer.src_lang = nllb_src
            source_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode("Hello"))
            target_prefix = [nllb_tgt]
            
            # Use synchronous translate_batch for warm-up
            translator.translate_batch(
                [source_tokens],
                target_prefix=[target_prefix]
            )
            logger.info("Dummy inference completed. Model is fully warmed up.")
        except Exception as e:
            logger.warning(f"Failed to run dummy inference: {e}")
            
    logger.info("Local models preloaded successfully.")

def get_groq_client() -> Optional[AsyncGroq]:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        return AsyncGroq(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None

LANG_MAP = {
    "en": "eng_Latn",
    "de": "deu_Latn",
    "zh": "zho_Hans",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "fr": "fra_Latn",
    "es": "spa_Latn",
    "ru": "rus_Cyrl",
    "th": "tha_Thai",
    "vi": "vie_Latn",
}

async def handle_flow_2_stream_translation(text: str, source_lang: str, target_lang: str, domain: str) -> AsyncGenerator[str, None]:
    clean_lower = text.strip().lower()
    words = clean_lower.split()
    keyword_count = len(words)
    
    from app.services.supabase_client import get_supabase
    import re
    
    supabase = get_supabase()
    domain_dict = {}
    if supabase:
        try:
            res = supabase.table("domain_dictionaries").select("word, translation").eq("domain", domain).execute()
            if res.data:
                for entry in res.data:
                    domain_dict[entry["word"].lower()] = entry["translation"]
        except Exception as e:
            logger.error(f"Supabase query error: {e}")

    async def yield_nllb(t, warning_msg=None):
        translator, tokenizer = get_nllb_translator()
        if not translator or not tokenizer:
            yield json.dumps({'error': "NLLB model is not available."})
            return
            
        nllb_src = LANG_MAP.get(source_lang, "eng_Latn")
        nllb_tgt = LANG_MAP.get(target_lang, "vie_Latn")
        
        try:
            from app.utils.html_parser import HTMLTranslator
            html_translator = HTMLTranslator()
            html_with_placeholders, texts_to_translate = html_translator.extract_text(t)
            
            if not texts_to_translate:
                if warning_msg:
                    yield json.dumps({'text': html_with_placeholders, 'warning': warning_msg})
                else:
                    yield json.dumps({'text': html_with_placeholders})
                return
                
            tokenizer.src_lang = nllb_src
            source_tokens_list = [tokenizer.convert_ids_to_tokens(tokenizer.encode(tt)) for tt in texts_to_translate]
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
            
            if warning_msg:
                yield json.dumps({'text': final_translated, 'warning': warning_msg})
            else:
                yield json.dumps({'text': final_translated})
        except Exception as e:
            logger.error(f"NLLB failed: {e}")
            yield json.dumps({'error': "Dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch."})

    # Case 1: < 3 keywords
    if keyword_count < 3:
        if clean_lower in domain_dict:
            yield json.dumps({'text': domain_dict[clean_lower]})
            return
        else:
            warning = f"Từ/cụm từ này không được tìm thấy trong từ điển chuyên ngành '{domain}'. Hệ thống sử dụng NLLB để dịch thông thường, kết quả có thể không phản ánh đầy đủ nghĩa chuyên ngành."
            async for chunk in yield_nllb(text, warning):
                yield chunk
            return

    # Case 2: >= 3 keywords
    found_terms = {}
    sorted_keys = sorted(domain_dict.keys(), key=len, reverse=True)
    for k in sorted_keys:
        pattern = r'\b' + re.escape(k) + r'\b'
        if re.search(pattern, clean_lower):
            found_terms[k] = domain_dict[k]

    if found_terms:
        # LLM streaming (Groq/Gemini bypass)
        groq_client = get_groq_client()
        system_prompt = f"You are a professional translator. You specialize in the '{domain}' domain. Ensure accurate terminology for this field."
        glossary_str = "\n".join([f"- {k} -> {v}" for k, v in found_terms.items()])
        system_prompt += f"\n\nYou MUST use the following glossary for terminology:\n{glossary_str}"
        system_prompt += f"\n\nTranslate the following text from {source_lang} to {target_lang}. Only output the direct translation, do not explain or converse. Preserve all HTML tags perfectly if present."
        
        use_fallback = False
        if groq_client:
            try:
                stream = await groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    stream=True,
                    temperature=0.3
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        yield json.dumps({'text': content})
                return
            except Exception as e:
                logger.warning(f"Groq API streaming failed: {e}. Falling back to Gemini.")
                use_fallback = True
        else:
            use_fallback = True

        if use_fallback:
            gemini_client = get_gemini_client()
            if gemini_client:
                try:
                    full_prompt = f"{system_prompt}\n\nText:\n{text}"
                    response_stream = gemini_client.models.generate_content_stream(
                        model="gemini-2.5-flash",
                        contents=full_prompt
                    )
                    for chunk in response_stream:
                        if chunk.text:
                            yield json.dumps({'text': chunk.text})
                    return
                except Exception as e:
                    logger.error(f"Gemini fallback failed: {e}")
        
        # If both LLMs failed, fallback to NLLB with warning
        warning = f"Hệ thống không thể dịch bằng AI model chuyên ngành. Đã sử dụng NLLB, kết quả có thể không phản ánh đầy đủ nghĩa chuyên ngành."
        async for chunk in yield_nllb(text, warning):
            yield chunk
        return
    else:
        # Terminology not found -> NLLB
        async for chunk in yield_nllb(text, None):
            yield chunk
        return

async def stream_translation(text: str, source_lang: str, target_lang: str, domain: str = "") -> AsyncGenerator[str, None]:
    """Translates text using local NLLB model via CTranslate2. Falls back to Groq/Gemini."""
    
    is_flow_2 = domain and domain != "Dịch thông thường (Mặc định)"
    if is_flow_2:
        async for chunk in handle_flow_2_stream_translation(text, source_lang, target_lang, domain):
            yield chunk
        return
        
    # --- FLOW 1 BEGIN ---
    translator, tokenizer = get_nllb_translator()
    
    if translator and tokenizer:
        nllb_src = LANG_MAP.get(source_lang, "eng_Latn")
        nllb_tgt = LANG_MAP.get(target_lang, "vie_Latn")

        try:
            from app.utils.html_parser import HTMLTranslator
            html_translator = HTMLTranslator()
            html_with_placeholders, texts_to_translate = html_translator.extract_text(text)
            
            if not texts_to_translate:
                yield json.dumps({'text': html_with_placeholders})
                return
                
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
            
            yield json.dumps({'text': final_translated})
            return
        except Exception as e:
            logger.error(f"NLLB translation failed: {e}. Falling back to LLM.")

    # Fallback to LLMs if NLLB fails or is not available
    groq_client = get_groq_client()
    system_prompt = f"You are a professional translator.\n\nTranslate the following text from {source_lang} to {target_lang}. Only output the direct translation, do not explain or converse. Preserve all HTML tags perfectly if present."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]

    use_fallback = False
    if groq_client:
        try:
            stream = await groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                stream=True,
                temperature=0.3
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield json.dumps({'text': content})
            return
        except Exception as e:
            logger.warning(f"Groq API streaming failed: {e}. Falling back to Gemini.")
            use_fallback = True
    else:
        logger.warning("Groq API key not found. Using Gemini fallback.")
        use_fallback = True

    if use_fallback:
        gemini_client = get_gemini_client()
        if not gemini_client:
            yield json.dumps({'error': 'No LLM API keys configured.'})
            return

        try:
            full_prompt = f"{system_prompt}\n\nText:\n{text}"
            response_stream = gemini_client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=full_prompt
            )
            for chunk in response_stream:
                if chunk.text:
                    yield json.dumps({'text': chunk.text})
        except Exception as e:
            logger.error(f"Gemini fallback failed: {e}")
            yield json.dumps({'error': 'Translation service unavailable.'})


async def extract_flashcard(word: str, context: str, domain: str = "") -> dict:
    """Extracts flashcard info returning JSON."""
    groq_client = get_groq_client()
    system_prompt = (
        "You are an expert lexicographer and linguist. Extract vocabulary info. "
        "For English and German words, provide an exact standard IPA phonetic transcription including primary/secondary stress marks (e.g. /əˈsɪŋkrənəs/ or /ˈkʁaŋkn̩ˌhaʊ̯s/). "
        "Return EXACT JSON with keys: word, phonetic, part_of_speech, meaning. No extra text."
    )
    user_prompt = f"Word: '{word}'. Context: '{context}'. Domain: '{domain}'."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    if groq_client:
        try:
            response = await groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.warning(f"Groq JSON extraction failed: {e}")
    
    # Fallback to Gemini for JSON
    gemini_client = get_gemini_client()
    if gemini_client:
        try:
            from google.genai import types
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini Flashcard fallback failed: {e}")
            
    return {}
