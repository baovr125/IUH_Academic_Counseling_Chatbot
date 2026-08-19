import os
import json
import pika
from app.utils.logger import logger

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
RABBITMQ_PASS = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")

def publish_doc_translated_event(doc_id: str, user_id: str, file_name: str, glossary: list, source_lang: str = "en"):
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        ))
        channel = connection.channel()
        channel.exchange_declare(exchange='chatbot_events', exchange_type='topic', durable=True)
        
        message = {
            "doc_id": doc_id,
            "user_id": user_id,
            "file_name": file_name,
            "glossary_json": glossary,
            "source_lang": source_lang
        }
        
        channel.basic_publish(
            exchange='chatbot_events',
            routing_key='doc.translated',
            body=json.dumps(message)
        )
        logger.info(f"Published DocTranslated event for doc_id={doc_id} to RabbitMQ.")
        connection.close()
    except Exception as e:
        logger.error(f"Failed to publish DocTranslated event: {e}")
