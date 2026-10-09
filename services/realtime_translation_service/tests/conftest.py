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
os.environ["JWT_SECRET_KEY"] = "super-secret-key-iuh-chatbot-2026"
os.environ["RABBITMQ_HOST"] = "localhost"

from app.main import app

import jwt
from datetime import datetime, timedelta

@pytest.fixture(scope="session")
def client():
    # Generate a valid mock JWT token
    secret = os.environ.get("JWT_SECRET_KEY", "super-secret-key-iuh-chatbot-2026")
    token = jwt.encode(
        {"sub": "test_user_id", "exp": datetime.utcnow() + timedelta(hours=1)},
        secret,
        algorithm="HS256"
    )
    
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
