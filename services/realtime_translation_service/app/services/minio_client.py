import os
from minio import Minio
from minio.error import S3Error
from app.utils.logger import logger
from io import BytesIO

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
BUCKET_NAME = "dictionary-audio"

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

def init_minio():
    """Tạo bucket nếu chưa có và set policy public read"""
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
            # Set public read policy
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"]
                    }
                ]
            }
            import json
            minio_client.set_bucket_policy(BUCKET_NAME, json.dumps(policy))
            logger.info(f"Đã khởi tạo MinIO bucket '{BUCKET_NAME}' với quyền Public Read.")
        else:
            logger.info(f"MinIO bucket '{BUCKET_NAME}' đã tồn tại.")
    except Exception as e:
        logger.error(f"Lỗi khởi tạo MinIO: {e}")

def upload_audio(file_name: str, audio_bytes: bytes) -> str:
    """Tải file mp3 lên MinIO và trả về URL tĩnh (sử dụng localhost port 9000 cho frontend truy cập)"""
    try:
        minio_client.put_object(
            BUCKET_NAME,
            file_name,
            data=BytesIO(audio_bytes),
            length=len(audio_bytes),
            content_type="audio/mpeg"
        )
        # URL trả về cho client truy cập (client thường ở localhost:9000 hoặc ip của server)
        return f"http://localhost:9000/{BUCKET_NAME}/{file_name}"
    except Exception as e:
        logger.error(f"Lỗi tải file {file_name} lên MinIO: {e}")
        return ""
