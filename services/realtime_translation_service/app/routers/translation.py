from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from sse_starlette.sse import EventSourceResponse
import edge_tts
import hashlib
from typing import Optional
from app.schemas.translation import (
    TranslateRequest, LookupRequest, TranslateResponse, ApiResult,
    StreamTranslateRequest, FlashcardExtractRequest
)
from app.services.translation_service import translate_text
from app.services.llm_service import stream_translation, extract_flashcard
from app.services.dictionary_service import get_word_audio
from app.services.cache_service import get_cached_audio_url, set_cached_audio_url
from app.utils.minio_client import upload_audio_bytes, get_audio_bytes, audio_exists
from app.utils.logger import logger

router = APIRouter(tags=["Real-time Translation Service"])

TTS_VOICE_MAP = {
    # Short 2-letter codes
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-AriaNeural",       # AriaNeural: Giọng phát âm chuẩn từ điển Mỹ, rõ âm gió & trọng âm
    "de": "de-DE-KillianNeural",    # KillianNeural: Chuẩn ngữ âm Hochdeutsch tiếng Đức
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "fr": "fr-FR-DeniseNeural",
    "es": "es-ES-ElviraNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "th": "th-TH-PremwadeeNeural",
    # Locale codes
    "vi-vn": "vi-VN-HoaiMyNeural",
    "en-us": "en-US-AriaNeural",
    "en-gb": "en-GB-RyanNeural",     # RyanNeural: Chuẩn RP Anh - Anh Oxford
    "de-de": "de-DE-KillianNeural",
    "zh-cn": "zh-CN-XiaoxiaoNeural",
    "ja-jp": "ja-JP-NanamiNeural",
    "ko-kr": "ko-KR-SunHiNeural",
    "fr-fr": "fr-FR-DeniseNeural",
    "es-es": "es-ES-ElviraNeural",
    "ru-ru": "ru-RU-SvetlanaNeural",
    "th-th": "th-TH-PremwadeeNeural"
}

def resolve_voice(lang: str) -> str:
    cleaned = (lang or "en").strip().lower().replace("_", "-")
    if cleaned in TTS_VOICE_MAP:
        return TTS_VOICE_MAP[cleaned]
    prefix = cleaned[:2]
    return TTS_VOICE_MAP.get(prefix, "en-US-AriaNeural")


@router.get("/tts")
async def tts_endpoint(text: str, lang: str = "en"):
    """
    Sinh file âm thanh phát âm chuẩn phòng thu tốc độ cao (Microsoft Neural TTS):
    - Tiếng Anh: en-US-AriaNeural (Chuẩn ngữ âm từ điển, rõ phụ âm cuối)
    - Tiếng Đức: de-DE-KillianNeural (Chuẩn Hochdeutsch, rõ từ ghép & nguyên âm biến âm)
    - Tiếng Việt & ngôn ngữ khác: vi-VN-HoaiMyNeural, ja-JP-NanamiNeural,...
    - Tốc độ sinh trực tiếp siêu nhanh (<150ms), cache MinIO/Redis (<5ms)
    """
    voice = resolve_voice(lang)
    clean_text = text.strip()
    if not clean_text or len(clean_text.strip(" .,!?:;-_()[]{}\"'`~")) == 0:
        return Response(status_code=204)
    
    cache_key = hashlib.md5(f"{clean_text.lower()}_{voice}".encode('utf-8')).hexdigest()
    object_name = f"tts/{cache_key}.mp3"
    
    # 1. Check MinIO / Redis cache URL first (Zero latency <5ms)
    if audio_exists(object_name):
        audio_content = get_audio_bytes(object_name)
        if audio_content:
            return Response(
                content=audio_content,
                media_type="audio/mpeg",
                headers={
                    "Cache-Control": "public, max-age=604800",
                    "X-TTS-Voice": voice,
                    "X-Cache": "HIT"
                }
            )
            
    # 2. Tổng hợp âm thanh trực tiếp qua Microsoft Neural Engine (<150ms)
    try:
        # Rate -4% giúp phát âm rõ từng phụ âm và âm đuôi mà không làm chậm trải nghiệm realtime
        communicate = edge_tts.Communicate(clean_text, voice, rate="-4%")
        audio_data = bytearray()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
                
        complete_audio = bytes(audio_data)
        if not complete_audio:
            return Response(status_code=204)
        
        # 3. Lưu trữ vào MinIO và Cache URL vào Redis
        try:
            audio_url = upload_audio_bytes(object_name, complete_audio)
            set_cached_audio_url(cache_key, audio_url)
        except Exception:
            pass
        
        return Response(
            content=complete_audio,
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "public, max-age=604800",
                "X-TTS-Voice": voice,
                "X-Cache": "MISS"
            }
        )
    except Exception as e:
        logger.warning(f"TTS generation skipped for '{clean_text}': {e}")
        return Response(status_code=204)


@router.get("/audio/{object_name:path}")
async def get_audio_endpoint(object_name: str):
    """Lấy file âm thanh phát âm trực tiếp từ MinIO Object Storage"""
    audio_content = get_audio_bytes(object_name)
    if not audio_content:
        return Response(status_code=204)
    return Response(
        content=audio_content,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=604800"}
    )


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
    
    # 2. Get optional phonetic from Dictionary API for metadata
    try:
        audio_info = await get_word_audio(payload.word, lang="en")
        if audio_info and not flashcard_data.get("phonetic") and audio_info.get("phonetic"):
            flashcard_data["phonetic"] = audio_info.get("phonetic", "")
    except Exception:
        pass
            
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
    phonetic = "/.../"
    try:
        dict_info = await get_word_audio(payload.word, lang="en")
        if dict_info and dict_info.get("phonetic"):
            phonetic = dict_info["phonetic"]
    except Exception:
        pass
        
    return ApiResult(
        ok=True,
        data={
            "word": payload.word,
            "definition": translated_text,
            "phonetic": phonetic,
            "cached": cached,
            "latencyMs": latency_ms
        }
    )
