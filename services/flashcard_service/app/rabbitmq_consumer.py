import os
import json
import asyncio
import aio_pika
from app.utils.logger import logger
from app.services.flashcard_service import create_deck, create_card, update_card_audio_url
from starlette.concurrency import run_in_threadpool

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
RABBITMQ_PASS = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")

RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

_channel: aio_pika.Channel = None
from typing import Optional

async def publish_flashcard_created_event(card_id: str, term: str, lang_code: str = "en", user_id: str = "anonymous", phonetic: Optional[str] = None):
    global _exchange
    if not _exchange:
        return
    try:
        payload = {
            "card_id": card_id,
            "term": term,
            "lang_code": lang_code,
            "user_id": user_id,
            "phonetic": phonetic
        }
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await _exchange.publish(message, routing_key="flashcard.created")
        logger.info(f"Published flashcard.created event for card_id={card_id}, term='{term}', phonetic='{phonetic}'")
    except Exception as e:
        logger.error(f"Failed to publish flashcard.created event: {e}")

async def process_doc_translated_event(message: aio_pika.IncomingMessage):
    async with message.process():
        body = message.body.decode()
        logger.info(f"Received event DocTranslated: {body[:200]}...")
        try:
            data = json.loads(body)
            glossary = data.get("glossary_json", [])
            user_id = data.get("user_id", "anonymous")
            file_name = data.get("file_name", "Tài liệu")
            source_lang = (data.get("source_lang") or "en").strip().lower()
            doc_id = data.get("doc_id", "")
            
            if not glossary:
                logger.info("No glossary found in DocTranslated event. Skipping flashcard creation.")
                return

            deck_title = f"Thuật ngữ: {file_name}"
            deck_description = f"Được tự động trích xuất từ tài liệu đã dịch (ID: {doc_id})."
            
            # Idempotency Check: Kiểm tra xem Deck đã được tạo cho tài liệu này trước đó chưa
            existing_decks = await get_decks(user_id)
            existing_deck = next((d for d in existing_decks if d.get("title") == deck_title), None)
            
            if existing_deck:
                logger.info(f"Deck '{deck_title}' already exists (ID: {existing_deck.get('id')}). Reusing existing deck.")
                deck_id = existing_deck.get("id")
            else:
                logger.info(f"Creating Flashcard Deck: {deck_title} for user {user_id}")
                deck = await create_deck(deck_title, deck_description, user_id, lang_code=source_lang)
                deck_id = deck.get("id")
                
            if not deck_id:
                logger.error("Failed to acquire Deck ID.")
                return
            
            # Lấy các thẻ hiện có trong deck để tránh trùng lặp từ
            existing_cards = await get_deck_cards(deck_id, user_id)
            existing_terms = {c.get("term", "").strip().lower() for c in existing_cards}
            
            created_count = 0
            for item in glossary:
                term = (item.get("term") or "").strip()
                definition = (item.get("definition") or item.get("translation") or item.get("vi") or "").strip()
                phonetic = item.get("phonetic")
                example = item.get("example") or item.get("context")
                part_of_speech = item.get("part_of_speech") or "phrase"
                
                if term and definition and term.lower() not in existing_terms:
                    card = await create_card(
                        deck_id=deck_id,
                        front_text=term,
                        back_text=definition,
                        user_id=user_id,
                        phonetic=phonetic,
                        example_sentence=example,
                        part_of_speech=part_of_speech,
                        lang_code=source_lang
                    )
                    existing_terms.add(term.lower())
                    created_count += 1
                    
                    # Trigger async event to request TTS audio synthesis
                    card_id = card.get("id")
                    if card_id:
                        await publish_flashcard_created_event(
                            card_id=card_id,
                            term=term,
                            lang_code=source_lang,
                            user_id=user_id,
                            phonetic=phonetic
                        )
            
            logger.info(f"Successfully processed {created_count} new flashcards for deck '{deck_title}' and requested TTS audio.")
            
        except Exception as e:
            logger.exception(f"Error processing DocTranslated event: {e}")

async def process_audio_ready_event(message: aio_pika.IncomingMessage):
    """Lắng nghe phản hồi từ realtime_translation_service khi file âm thanh TTS đã được tạo xong."""
    async with message.process():
        body = message.body.decode()
        logger.info(f"Received event flashcard.audio_ready: {body}")
        try:
            data = json.loads(body)
            card_id = data.get("card_id")
            audio_url = data.get("audio_url")
            if card_id and audio_url:
                await update_card_audio_url(card_id, audio_url)
                logger.info(f"Attached audio_url to card {card_id}")
        except Exception as e:
            logger.error(f"Error processing flashcard.audio_ready event: {e}")

async def start_rabbitmq_consumer():
    global _channel, _exchange
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        _channel = await connection.channel()
        
        _exchange = await _channel.declare_exchange(
            "chatbot_events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        
        # 1. Queue for DocTranslated events
        queue_doc = await _channel.declare_queue("flashcard_service_doc_translated", durable=True)
        await queue_doc.bind(_exchange, routing_key="doc.translated")
        await queue_doc.consume(process_doc_translated_event)
        
        # 2. Queue for AudioReady events
        queue_audio = await _channel.declare_queue("flashcard_service_audio_ready", durable=True)
        await queue_audio.bind(_exchange, routing_key="flashcard.audio_ready")
        await queue_audio.consume(process_audio_ready_event)
        
        logger.info("Flashcard Service RabbitMQ Consumers started successfully (doc.translated & flashcard.audio_ready).")
        return connection
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumer: {e}")
        return None
