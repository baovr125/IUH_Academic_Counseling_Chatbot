import os
import io
from datetime import timedelta
from typing import Optional
from minio import Minio
from minio.error import S3Error
from app.utils.logger import logger

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"

AUDIO_BUCKET = "flashcard-audios"

# Initialize MinIO client
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

def init_audio_bucket():
    try:
        if not client.bucket_exists(AUDIO_BUCKET):
            client.make_bucket(AUDIO_BUCKET)
            logger.info(f"Created MinIO bucket for audio: {AUDIO_BUCKET}")
    except Exception as e:
        logger.warning(f"MinIO audio bucket initialization skipped or offline: {e}")

# Initialize bucket on module load
init_audio_bucket()

def upload_audio_bytes(object_name: str, audio_bytes: bytes, content_type: str = "audio/mpeg") -> str:
    try:
        client.put_object(
            bucket_name=AUDIO_BUCKET,
            object_name=object_name,
            data=io.BytesIO(audio_bytes),
            length=len(audio_bytes),
            content_type=content_type
        )
        logger.info(f"Successfully uploaded audio to MinIO: {AUDIO_BUCKET}/{object_name}")
        return f"/api/v1/translate/audio/{object_name}"
    except S3Error as e:
        logger.error(f"Error uploading audio to MinIO {object_name}: {e}")
        raise

def get_audio_bytes(object_name: str) -> Optional[bytes]:
    try:
        response = client.get_object(AUDIO_BUCKET, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
    except S3Error as e:
        logger.warning(f"Audio object not found in MinIO {object_name}: {e}")
        return None

def audio_exists(object_name: str) -> bool:
    try:
        client.stat_object(AUDIO_BUCKET, object_name)
        return True
    except S3Error:
        return False

def get_presigned_audio_url(object_name: str, expires_seconds: int = 86400) -> str:
    try:
        url = client.get_presigned_url(
            "GET",
            AUDIO_BUCKET,
            object_name,
            expires=timedelta(seconds=expires_seconds)
        )
        return url
    except S3Error as e:
        logger.error(f"Error generating presigned audio url: {e}")
        return ""
