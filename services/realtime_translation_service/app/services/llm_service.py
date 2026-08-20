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

    model_dir = "/app/models/nllb-200-distilled-600M-ct2-int8"
    if not os.path.exists(model_dir):
        logger.warning(f"NLLB model directory {model_dir} not found. Cannot initialize CTranslate2.")
        return None, None

    try:
        logger.info("Loading NLLB CTranslate2 model on CPU (INT8)...")
        _translator = ctranslate2.Translator(
            model_dir,
            device="cpu",
            compute_type="int8",
            inter_threads=2,
            intra_threads=2
        )
        logger.info("Loading NLLB Tokenizer...")
        _tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir)
        return _translator, _tokenizer
    except Exception as e:
        logger.error(f"Failed to load NLLB model: {e}")
        return None, None
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

async def stream_translation(text: str, source_lang: str, target_lang: str, domain: str = "") -> AsyncGenerator[str, None]:
    """Translates text using local NLLB model via CTranslate2. Falls back to Groq/Gemini."""
    translator, tokenizer = get_nllb_translator()
    
    if translator and tokenizer:
        nllb_src = LANG_MAP.get(source_lang, "eng_Latn")
        nllb_tgt = LANG_MAP.get(target_lang, "vie_Latn")

        try:
            tokenizer.src_lang = nllb_src
            source_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
            target_prefix = [nllb_tgt]

            results = await asyncio.to_thread(
                translator.translate_batch,
                [source_tokens],
                target_prefix=[target_prefix]
            )
            
            target_tokens = results[0].hypotheses[0][1:] 
            translated_text = tokenizer.decode(tokenizer.convert_tokens_to_ids(target_tokens))
            
            yield json.dumps({'text': translated_text})
            return
        except Exception as e:
            logger.error(f"NLLB translation failed: {e}. Falling back to LLM.")

    # Fallback to LLMs if NLLB fails or is not available
    groq_client = get_groq_client()
    
    system_prompt = f"You are a professional translator."
    if domain:
        system_prompt += f" You specialize in the '{domain}' domain. Ensure accurate terminology for this field."
    system_prompt += f" Translate the following text from {source_lang} to {target_lang}. Only output the direct translation, do not explain or converse."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]

    use_fallback = False

    if groq_client:
        try:
            stream = await groq_client.chat.completions.create(
                model="llama-3.1-8b-instant", # or llama3-70b-8192
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
            # Gemini streaming using new SDK
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
