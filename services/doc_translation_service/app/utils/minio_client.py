import os
from minio import Minio
from minio.error import S3Error
from app.utils.logger import logger

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"

DOCUMENTS_BUCKET = "documents-bucket"

# Initialize minio client
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

def init_buckets():
    try:
        if not client.bucket_exists(DOCUMENTS_BUCKET):
            client.make_bucket(DOCUMENTS_BUCKET)
            logger.info(f"Created MinIO bucket: {DOCUMENTS_BUCKET}")
    except S3Error as e:
        logger.error(f"MinIO initialization error: {e}")

# Initialize bucket on module load
init_buckets()

def upload_file(object_name: str, file_path: str):
    try:
        client.fput_object(DOCUMENTS_BUCKET, object_name, file_path)
        logger.info(f"Successfully uploaded {file_path} to {object_name}")
    except S3Error as e:
        logger.error(f"Error uploading {file_path}: {e}")
        raise

def download_file(object_name: str, file_path: str):
    try:
        client.fget_object(DOCUMENTS_BUCKET, object_name, file_path)
        logger.info(f"Successfully downloaded {object_name} to {file_path}")
    except S3Error as e:
        logger.error(f"Error downloading {object_name}: {e}")
        raise

def get_presigned_url(object_name: str) -> str:
    try:
        url = client.get_presigned_url(
            "GET",
            DOCUMENTS_BUCKET,
            object_name,
        )
        return url
    except S3Error as e:
        logger.error(f"Error generating presigned url: {e}")
        return ""
