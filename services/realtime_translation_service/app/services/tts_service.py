"""Tổng hợp giọng đọc (Microsoft Edge Neural TTS): chọn giọng theo ngôn ngữ, thử lại khi lỗi tạm thời, theo dõi sức khỏe.

Một nơi duy nhất cho bảng giọng đọc để endpoint /tts và consumer RabbitMQ (âm thanh thẻ Flashcard) luôn dùng chung.
"""
import asyncio
import os
import time
from typing import Any, Dict, Optional

import edge_tts

from app.utils.logger import logger

# 10 ngôn ngữ của hệ thống. Khóa là mã ISO; kèm mã locale thường gặp.
VOICE_MAP = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-AriaNeural",       # Giọng Mỹ chuẩn từ điển, rõ âm gió và trọng âm
    "de": "de-DE-KillianNeural",    # Hochdeutsch
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "fr": "fr-FR-DeniseNeural",
    "es": "es-ES-ElviraNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "th": "th-TH-PremwadeeNeural",
    "vi-vn": "vi-VN-HoaiMyNeural",
    "en-us": "en-US-AriaNeural",
    "en-gb": "en-GB-RyanNeural",    # Anh - Anh chuẩn RP
    "de-de": "de-DE-KillianNeural",
    "zh-cn": "zh-CN-XiaoxiaoNeural",
    "ja-jp": "ja-JP-NanamiNeural",
    "ko-kr": "ko-KR-SunHiNeural",
    "fr-fr": "fr-FR-DeniseNeural",
    "es-es": "es-ES-ElviraNeural",
    "ru-ru": "ru-RU-SvetlanaNeural",
    "th-th": "th-TH-PremwadeeNeural",
}
DEFAULT_VOICE = "en-US-AriaNeural"


def resolve_voice(lang: Optional[str]) -> str:
    cleaned = (lang or "en").strip().lower().replace("_", "-")
    if cleaned in VOICE_MAP:
        return VOICE_MAP[cleaned]
    return VOICE_MAP.get(cleaned[:2], DEFAULT_VOICE)


class TTSUnavailable(Exception):
    """Dịch vụ tổng hợp giọng đọc không trả được âm thanh (sau khi đã thử lại)."""


RETRIES = int(os.getenv("TTS_RETRIES", "2"))
RETRY_DELAY_S = float(os.getenv("TTS_RETRY_DELAY_S", "0.4"))

_state: Dict[str, Any] = {"last_success_at": None, "last_error": None, "last_error_at": None, "consecutive_failures": 0}


def health() -> Dict[str, Any]:
    """Trạng thái gần nhất của TTS (không gọi mạng): unknown | ok | degraded."""
    if _state["last_success_at"] is None and _state["last_error"] is None:
        status = "unknown"
    elif _state["consecutive_failures"] > 0:
        status = "degraded"
    else:
        status = "ok"
    return {"status": status, **_state}


def reset_state() -> None:
    _state.update(last_success_at=None, last_error=None, last_error_at=None, consecutive_failures=0)


async def synthesize(text: str, voice: str, rate: str = "-4%") -> bytes:
    """
    Trả về MP3. Thử lại vài lần khi Microsoft từ chối tạm thời (403/handshake/mạng). Không bao giờ trả dữ liệu rỗng:
    thất bại thì ném TTSUnavailable để nơi gọi báo lỗi rõ ràng thay vì im lặng.
    """
    last: Optional[BaseException] = None
    for attempt in range(RETRIES + 1):
        try:
            audio = bytearray()
            async for chunk in edge_tts.Communicate(text, voice, rate=rate).stream():
                if chunk["type"] == "audio":
                    audio.extend(chunk["data"])
            if not audio:
                raise TTSUnavailable("Dịch vụ giọng đọc không trả về âm thanh")
            _state.update(last_success_at=time.time(), consecutive_failures=0)
            return bytes(audio)
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < RETRIES:
                await asyncio.sleep(RETRY_DELAY_S * (attempt + 1))

    _state.update(
        last_error=f"{type(last).__name__}: {str(last)[:160]}",
        last_error_at=time.time(),
        consecutive_failures=_state["consecutive_failures"] + 1,
    )
    logger.warning(f"TTS failed for voice={voice} after {RETRIES + 1} attempts: {last}")
    raise TTSUnavailable(str(last)) from last
