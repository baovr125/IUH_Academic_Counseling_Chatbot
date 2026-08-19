import os
import json
import asyncio
import aio_pika
import edge_tts
import hashlib
from typing import Optional
from app.utils.logger import logger
from app.utils.minio_client import upload_audio_bytes, audio_exists
from app.services.cache_service import set_cached_audio_url

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
RABBITMQ_PASS = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")

RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

VOICE_MAP = {
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
    # Full Locale codes
    "vi-vn": "vi-VN-HoaiMyNeural",
    "en-us": "en-US-AriaNeural",
    "en-gb": "en-GB-RyanNeural",
    "de-de": "de-DE-KillianNeural",
    "zh-cn": "zh-CN-XiaoxiaoNeural",
    "ja-jp": "ja-JP-NanamiNeural",
    "ko-kr": "ko-KR-SunHiNeural",
    "fr-fr": "fr-FR-DeniseNeural",
    "es-es": "es-ES-ElviraNeural",
    "ru-ru": "ru-RU-SvetlanaNeural",
    "th-th": "th-TH-PremwadeeNeural"
}

_channel: aio_pika.Channel = None
_exchange: aio_pika.Exchange = None

async def generate_and_upload_tts(term: str, lang_code: str, card_id: str, phonetic: Optional[str] = None) -> str:
    cleaned_lang = (lang_code or "en").strip().lower().replace("_", "-")
    voice = VOICE_MAP.get(cleaned_lang) or VOICE_MAP.get(cleaned_lang[:2], "en-US-AriaNeural")
    lang_prefix = cleaned_lang[:2]
    clean_term = term.strip().lower()
    term_hash = hashlib.md5(f"{lang_prefix}_{clean_term}".encode('utf-8')).hexdigest()
    object_name = f"terms/{lang_prefix}_{term_hash}.mp3"
    
    # 1. Deduplication: Check if audio object already exists in MinIO
    if audio_exists(object_name):
        logger.info(f"Deduplication HIT: Audio already exists in MinIO for '{term}' [{lang_prefix}] -> {object_name}")
        return f"/api/v1/translate/audio/{object_name}"
        
    # 2. Tổng hợp âm thanh chất lượng cao trực tiếp qua Microsoft Edge Neural Engine (Rate -4%)
    communicate = edge_tts.Communicate(clean_term, voice, rate="-4%")
    audio_data = bytearray()
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
            
    complete_audio = bytes(audio_data)
    audio_url = upload_audio_bytes(object_name, complete_audio)
    
    cache_key = hashlib.md5(f"{clean_term}_{voice}".encode('utf-8')).hexdigest()
    set_cached_audio_url(cache_key, audio_url)
    
    return audio_url

async def process_flashcard_created_event(message: aio_pika.IncomingMessage):
    global _exchange
    async with message.process():
        body = message.body.decode()
        logger.info(f"Received flashcard.created event: {body}")
        try:
            data = json.loads(body)
            card_id = data.get("card_id")
            term = data.get("term")
            lang_code = data.get("lang_code", "en")
            phonetic = data.get("phonetic")
            
            if not card_id or not term:
                logger.warning("Missing card_id or term in flashcard.created event. Skipping.")
                return

            logger.info(f"Synthesizing high-precision TTS audio for flashcard card_id={card_id}, term='{term}', lang='{lang_code}'...")
            audio_url = await generate_and_upload_tts(term, lang_code, card_id, phonetic=phonetic)
            
            # Rate limit protection: Nghỉ 1.0s giữa các lần gọi Edge-TTS
            await asyncio.sleep(1.0)
            
            # Publish flashcard.audio_ready event back to RabbitMQ
            if _exchange:
                response_payload = {
                    "card_id": card_id,
                    "audio_url": audio_url,
                    "term": term
                }
                out_msg = aio_pika.Message(
                    body=json.dumps(response_payload).encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                )
                await _exchange.publish(out_msg, routing_key="flashcard.audio_ready")
                logger.info(f"Published flashcard.audio_ready event for card_id={card_id}, audio_url='{audio_url}'")
                
        except Exception as e:
            logger.exception(f"Error processing flashcard.created event: {e}")

async def start_rabbitmq_tts_consumer():
    global _channel, _exchange
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        _channel = await connection.channel()
        await _channel.set_qos(prefetch_count=1)
        
        _exchange = await _channel.declare_exchange(
            "chatbot_events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        
        queue = await _channel.declare_queue("realtime_tts_flashcard_generation", durable=True)
        await queue.bind(_exchange, routing_key="flashcard.created")
        
        logger.info("Realtime Translation Service RabbitMQ Consumer started (prefetch=1, direct neural)...")
        await queue.consume(process_flashcard_created_event)
        
        return connection
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ TTS consumer: {e}")
        return None
