import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

service_root = Path(__file__).resolve().parent.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["MINIO_ENDPOINT"] = "localhost:9000"
os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
os.environ["MINIO_SECRET_KEY"] = "minioadmin"
os.environ["MINIO_SECURE"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-key-do-not-use-in-production-0123456789"
os.environ["RABBITMQ_HOST"] = "localhost"
os.environ["TESTING"] = "1"

from app.main import app

from unittest.mock import patch, AsyncMock
import jwt
from datetime import datetime, timedelta

@pytest.fixture(scope="session", autouse=True)
def mock_external_services():
    with patch("app.main.start_rabbitmq_tts_consumer", new_callable=AsyncMock, return_value=None), \
         patch("app.main.init_minio", return_value=None), \
         patch("app.main.sync_dictionary_to_redis", return_value=None), \
         patch("app.main.preload_models", return_value=True), \
         patch("app.services.word_analysis_service.preload_nlp_models", return_value=None):
        yield

@pytest.fixture(scope="session")
def client(mock_external_services):
    # Generate a valid mock JWT token
    secret = os.environ["JWT_SECRET_KEY"]
    token = jwt.encode(
        {"sub": "test_user_id", "role": "student", "iss": "iuh-auth-service", "exp": datetime.utcnow() + timedelta(hours=1)},
        secret,
        algorithm="HS256"
    )
    
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
