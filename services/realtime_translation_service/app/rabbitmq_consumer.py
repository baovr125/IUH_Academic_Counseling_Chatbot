import os
import json
import asyncio
import aio_pika
import edge_tts
import hashlib
from app.utils.logger import logger
from app.utils.minio_client import upload_audio_bytes, audio_exists
from app.services.cache_service import set_cached_audio_url

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
RABBITMQ_PASS = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")

RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

VOICE_MAP = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-JennyNeural",
    "de": "de-DE-KatjaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "fr": "fr-FR-DeniseNeural",
    "es": "es-ES-ElviraNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "th": "th-TH-PremwadeeNeural"
}

_channel: aio_pika.Channel = None
_exchange: aio_pika.Exchange = None

async def generate_and_upload_tts(term: str, lang_code: str, card_id: str) -> str:
    voice = VOICE_MAP.get(lang_code.lower()[:2], "en-US-JennyNeural")
    object_name = f"terms/{card_id}.mp3"
    
    # Check if object already exists
    if audio_exists(object_name):
        return f"/api/v1/translate/audio/{object_name}"
        
    communicate = edge_tts.Communicate(term, voice)
    audio_data = bytearray()
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
            
    complete_audio = bytes(audio_data)
    audio_url = upload_audio_bytes(object_name, complete_audio)
    
    cache_key = hashlib.md5(f"{term.strip()}_{voice}".encode('utf-8')).hexdigest()
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
            
            if not card_id or not term:
                logger.warning("Missing card_id or term in flashcard.created event. Skipping.")
                return

            logger.info(f"Synthesizing TTS audio for flashcard card_id={card_id}, term='{term}'...")
            audio_url = await generate_and_upload_tts(term, lang_code, card_id)
            
            # Rate limit protection: Nghỉ 1.5s giữa các lần gọi Edge-TTS để tránh bị Microsoft block IP
            await asyncio.sleep(1.5)
            
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
        # Giới hạn prefetch_count = 1 để xử lý tuần tự từng thông điệp, không dồn dập
        await _channel.set_qos(prefetch_count=1)
        
        _exchange = await _channel.declare_exchange(
            "chatbot_events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        
        queue = await _channel.declare_queue("realtime_tts_flashcard_generation", durable=True)
        await queue.bind(_exchange, routing_key="flashcard.created")
        
        logger.info("Realtime Translation Service RabbitMQ Consumer started (prefetch=1, safe rate-limited)...")
        await queue.consume(process_flashcard_created_event)
        
        return connection
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ TTS consumer: {e}")
        return None
