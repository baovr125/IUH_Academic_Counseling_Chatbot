import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

service_root = Path(__file__).resolve().parent.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

os.environ["SUPABASE_URL"] = "https://mock-supabase.test"
os.environ["SUPABASE_KEY"] = "mock-key-test"
os.environ["JWT_SECRET_KEY"] = "super-secret-key-iuh-chatbot-2026"

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
