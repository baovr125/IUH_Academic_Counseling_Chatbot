import os
import json
import asyncio
import aio_pika
from app.utils.logger import logger
from app.services.flashcard_service import create_deck, create_card
from starlette.concurrency import run_in_threadpool

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
RABBITMQ_PASS = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")

RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

async def process_doc_translated_event(message: aio_pika.IncomingMessage):
    async with message.process():
        body = message.body.decode()
        logger.info(f"Received event DocTranslated: {body[:200]}...")
        try:
            data = json.loads(body)
            glossary = data.get("glossary_json", [])
            user_id = data.get("user_id", "anonymous")
            file_name = data.get("file_name", "Tài liệu")
            
            if not glossary:
                logger.info("No glossary found in DocTranslated event. Skipping flashcard creation.")
                return

            deck_title = f"Thuật ngữ: {file_name}"
            deck_description = "Được tự động trích xuất từ tài liệu."
            
            logger.info(f"Creating Flashcard Deck: {deck_title} for user {user_id}")
            deck = await create_deck(deck_title, deck_description, user_id)
            deck_id = deck.get("id")
            if not deck_id:
                logger.error("Failed to create Deck.")
                return
            
            for item in glossary:
                term = item.get("term", "")
                definition = item.get("definition", "")
                if term and definition:
                    await create_card(
                        deck_id=deck_id,
                        front_text=term,
                        back_text=definition
                    )
            
            logger.info(f"Successfully processed {len(glossary)} flashcards for deck {deck_title}")
            
        except Exception as e:
            logger.exception(f"Error processing DocTranslated event: {e}")

async def start_rabbitmq_consumer():
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        
        exchange = await channel.declare_exchange(
            "chatbot_events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        
        queue = await channel.declare_queue("flashcard_service_doc_translated", durable=True)
        await queue.bind(exchange, routing_key="doc.translated")
        
        logger.info("Starting RabbitMQ Consumer for DocTranslated events...")
        await queue.consume(process_doc_translated_event)
        
        # Keep connection open
        return connection
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumer: {e}")
        return None
