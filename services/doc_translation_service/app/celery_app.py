import os
from celery import Celery

# Load URLs from environment or use defaults
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = os.environ.get("RABBITMQ_PORT", "5672")

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", f"amqp://guest:guest@{RABBITMQ_HOST}:{RABBITMQ_PORT}//")
REDIS_URL = os.environ.get("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

celery_app = Celery(
    "doc_translation_worker",
    broker=RABBITMQ_URL,
    backend=REDIS_URL,
    include=["app.tasks.pdf_worker", "app.tasks.cleanup_worker"]
)

# Setup Celery Beat schedule for the cleanup task
from celery.schedules import crontab
celery_app.conf.beat_schedule = {
    "cleanup-old-files-every-day": {
        "task": "app.tasks.cleanup_worker.cleanup_old_files",
        "schedule": crontab(hour=0, minute=0), # Run every day at midnight UTC
    },
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True
)
