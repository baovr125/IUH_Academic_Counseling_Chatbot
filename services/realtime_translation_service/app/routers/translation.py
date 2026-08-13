from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import edge_tts
from app.schemas.translation import (
    TranslateRequest, LookupRequest, TranslateResponse, ApiResult,
    StreamTranslateRequest, FlashcardExtractRequest
)
from app.services.translation_service import translate_text
from app.services.llm_service import stream_translation, extract_flashcard
from app.services.dictionary_service import get_word_audio

router = APIRouter(tags=["Real-time Translation Service"])

TTS_VOICE_MAP = {
    "vi-VN": "vi-VN-HoaiMyNeural",
    "en-US": "en-US-JennyNeural",
    "de-DE": "de-DE-KatjaNeural",
    "zh-CN": "zh-CN-XiaoxiaoNeural",
    "ja-JP": "ja-JP-NanamiNeural",
    "ko-KR": "ko-KR-SunHiNeural",
    "fr-FR": "fr-FR-DeniseNeural",
    "es-ES": "es-ES-ElviraNeural",
    "ru-RU": "ru-RU-SvetlanaNeural",
    "th-TH": "th-TH-PremwadeeNeural"
}

@router.get("/tts")
async def tts_endpoint(text: str, lang: str = "vi-VN"):
    voice = TTS_VOICE_MAP.get(lang, "en-US-JennyNeural")
    communicate = edge_tts.Communicate(text, voice)
    
    async def generate():
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
                
    return StreamingResponse(generate(), media_type="audio/mpeg")

@router.post("/text")
async def translate_endpoint(payload: TranslateRequest):
    translated_text, cached, latency_ms = await translate_text(
        text=payload.text,
        source_lang=payload.source_lang,
        target_lang=payload.target_lang
    )
    return ApiResult(
        ok=True,
        data=TranslateResponse(
            translated_text=translated_text,
            source_lang=payload.source_lang,
            target_lang=payload.target_lang,
            cached=cached,
            latency_ms=latency_ms
        )
    )

@router.post("/stream")
async def stream_translate_endpoint(payload: StreamTranslateRequest):
    return EventSourceResponse(
        stream_translation(
            text=payload.text,
            source_lang=payload.source_lang,
            target_lang=payload.target_lang,
            domain=payload.domain
        )
    )

@router.post("/flashcard")
async def flashcard_endpoint(payload: FlashcardExtractRequest):
    # 1. Extract vocabulary info using LLM (JSON Mode)
    flashcard_data = await extract_flashcard(
        word=payload.word,
        context=payload.context,
        domain=payload.domain
    )
    
    # 2. Get audio from Free Dictionary API
    audio_info = await get_word_audio(payload.word)
    if audio_info:
        flashcard_data["audio_url"] = audio_info.get("audio_url", "")
        if not flashcard_data.get("phonetic"):
            flashcard_data["phonetic"] = audio_info.get("phonetic", "")
            
    return ApiResult(
        ok=True,
        data=flashcard_data
    )

@router.post("/lookup")
async def lookup_endpoint(payload: LookupRequest):
    translated_text, cached, latency_ms = await translate_text(
        text=payload.word,
        source_lang="en",
        target_lang="vi"
    )
    return ApiResult(
        ok=True,
        data={
            "word": payload.word,
            "definition": translated_text,
            "phonetic": "/.../",
            "cached": cached,
            "latencyMs": latency_ms
        }
    )
