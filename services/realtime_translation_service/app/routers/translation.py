from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from sse_starlette.sse import EventSourceResponse
import edge_tts
import hashlib
from app.schemas.translation import (
    TranslateRequest, LookupRequest, TranslateResponse, ApiResult,
    StreamTranslateRequest, FlashcardExtractRequest
)
from app.services.translation_service import translate_text
from app.services.llm_service import stream_translation, extract_flashcard
from app.services.dictionary_service import get_word_audio
from app.services.cache_service import get_cached_audio_url, set_cached_audio_url
from app.utils.minio_client import upload_audio_bytes, get_audio_bytes, audio_exists

router = APIRouter(tags=["Real-time Translation Service"])

TTS_VOICE_MAP = {
    # Short 2-letter codes
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-JennyNeural",
    "de": "de-DE-KatjaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "fr": "fr-FR-DeniseNeural",
    "es": "es-ES-ElviraNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "th": "th-TH-PremwadeeNeural",
    # Locale codes
    "vi-vn": "vi-VN-HoaiMyNeural",
    "en-us": "en-US-JennyNeural",
    "en-gb": "en-GB-SoniaNeural",
    "de-de": "de-DE-KatjaNeural",
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
    return TTS_VOICE_MAP.get(prefix, "en-US-JennyNeural")

@router.get("/tts")
async def tts_endpoint(text: str, lang: str = "en"):
    """
    Sinh file âm thanh phát âm chuẩn phòng thu (Microsoft Neural TTS):
    - Tự động chuẩn hóa ngôn ngữ (vi, en, de, ja, ko, zh...)
    - Tốc độ phát âm chuẩn ngữ điệu tự nhiên
    - Lưu cache tự động trên MinIO S3 & Redis
    """
    voice = resolve_voice(lang)
    cache_key = hashlib.md5(f"{text.strip().lower()}_{voice}".encode('utf-8')).hexdigest()
    object_name = f"tts/{cache_key}.mp3"
    
    # 1. Check MinIO / Redis cache URL first
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
        
    # 2. Generate audio via Edge-TTS (Rate -4% for crystal clear learning pronunciation)
    try:
        communicate = edge_tts.Communicate(text.strip(), voice, rate="-4%")
        audio_data = bytearray()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
                
        complete_audio = bytes(audio_data)
        
        # 3. Store in MinIO (Persistent Object Storage) and Cache URL in Redis
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
        return Response(status_code=500, content=f"TTS generation failed: {e}")

@router.get("/audio/{object_name:path}")
async def get_audio_endpoint(object_name: str):
    """Lấy file âm thanh phát âm trực tiếp từ MinIO Object Storage"""
    audio_content = get_audio_bytes(object_name)
    if not audio_content:
        return Response(status_code=404, content="Audio file not found")
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
