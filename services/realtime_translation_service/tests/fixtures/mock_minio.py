from unittest.mock import MagicMock


def create_mock_minio_client():
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = True
    mock_client.make_bucket.return_value = None
    mock_client.put_object.return_value = None
    mock_client.stat_object.return_value = MagicMock()
    
    mock_response = MagicMock()
    mock_response.read.return_value = b"\xff\xfb\x90\x44" # fake mp3 bytes
    mock_response.close.return_value = None
    mock_response.release_conn.return_value = None
    mock_client.get_object.return_value = mock_response
    mock_client.get_presigned_url.return_value = "http://localhost:9000/flashcard-audios/tts/test.mp3"
    
    return mock_client


def create_mock_redis_client():
    mock_redis = MagicMock()
    mock_store = {}

    def mock_get(key):
        return mock_store.get(key)

    def mock_setex(key, ttl, value):
        mock_store[key] = value
        return True

    mock_redis.get.side_effect = mock_get
    mock_redis.setex.side_effect = mock_setex
    mock_redis.ping.return_value = True
    return mock_redis
