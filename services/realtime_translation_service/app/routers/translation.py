from fastapi import APIRouter
from app.schemas.translation import TranslateRequest, LookupRequest, TranslateResponse, ApiResult
from app.services.translation_service import translate_text

router = APIRouter(tags=["Real-time Translation Service"])

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
