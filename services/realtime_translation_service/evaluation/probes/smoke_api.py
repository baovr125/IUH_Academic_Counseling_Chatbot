import os, sys, json, logging
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
os.environ["FASTTEXT_LID_MODEL"] = str(__import__("pathlib").Path(__file__).resolve().parents[2].parent / "models" / "lid.176.ftz")
os.environ["TESTING"] = "1"
os.environ["JWT_SECRET_KEY"] = __import__("secrets").token_hex(32)  # khóa thử dùng một lần, không phải secret thật
os.environ["REDIS_HOST"] = "localhost"
logging.disable(logging.CRITICAL)
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app

# Service chỉ nhận token do auth-service ký: HS256, issuer "iuh-auth-service", bắt buộc có exp (app/utils/security.py)
token = jwt.encode({"sub": "u", "iss": "iuh-auth-service", "exp": datetime.utcnow() + timedelta(hours=1)}, os.environ["JWT_SECRET_KEY"], algorithm="HS256")
H = {"Authorization": f"Bearer {token}"}
with TestClient(app) as c:
    for text in ["Trí tuệ nhân tạo đang thay đổi giáo dục", "La inteligenza artificiale sta cambiando il mondo", "merci", "12345"]:
        r = c.post("/api/v1/translate/detect", json={"text": text}, headers=H)
        j = r.json()
        d = j.get("data") or {}
        print("DETECT", r.status_code, repr(text[:30]), d.get("status"), d.get("resolved_source_lang"), d.get("detected_language"), j.get("detail"))
    for text in ["La inteligenza artificiale sta cambiando il mondo", "merci", "12345"]:
        r = c.post("/api/v1/translate/text", json={"text": text, "source_lang": "auto", "target_lang": "vi"}, headers=H)
        print("TEXT", r.status_code, repr(text[:30]), json.dumps(r.json(), ensure_ascii=False)[:230])
    for text in ["La inteligenza artificiale sta cambiando il mondo", "merci"]:
        with c.stream("POST", "/api/v1/translate/stream", json={"text": text, "source_lang": "auto", "target_lang": "vi"}, headers=H) as r:
            body = "".join(r.iter_text())
        print("STREAM", r.status_code, repr(text[:30]), body.replace("\r", "").replace("\n", " | ")[:330])
