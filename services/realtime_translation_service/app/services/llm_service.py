import os
import json
from typing import AsyncGenerator, Optional
import httpx
from google import genai
from groq import Groq, AsyncGroq
from app.utils.logger import logger

# Initialize Clients
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

async def stream_translation(text: str, source_lang: str, target_lang: str, domain: str = "") -> AsyncGenerator[str, None]:
    """Streams translation from Groq, falls back to Gemini if failed or rate limited."""
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
                model="llama3-8b-8192", # or llama3-70b-8192
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
    system_prompt = "You are a linguist. Extract vocabulary info. Return EXACT JSON with keys: word, phonetic, part_of_speech, meaning. No extra text."
    user_prompt = f"Word: '{word}'. Context: '{context}'. Domain: '{domain}'."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    if groq_client:
        try:
            response = await groq_client.chat.completions.create(
                model="llama3-8b-8192",
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
