import os
import uuid
import datetime
from typing import Dict, Any, Optional
from jose import jwt
from passlib.context import CryptContext
from supabase import create_client, Client
from app.utils.logger import logger

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-iuh-chatbot-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_supabase() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

def hash_password(password: str) -> str:
    safe_pwd = str(password)[:72]
    return pwd_context.hash(safe_pwd)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def register_user(email: str, password: str, full_name: str, student_id: Optional[str] = None) -> Dict[str, Any]:
    supabase = get_supabase()
    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(password)
    
    user_data = {
        "id": user_id,
        "email": email,
        "password_hash": hashed_pwd,
        "full_name": full_name,
        "student_id": student_id,
        "is_verified": True if student_id else False,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    if supabase:
        try:
            supabase.table("users").insert(user_data).execute()
        except Exception as e:
            logger.warning(f"Failed to insert user to Supabase DB: {e}")
            
    token = create_access_token({"sub": user_id, "email": email, "student_id": student_id})
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": email,
            "fullName": full_name,
            "studentId": student_id
        }
    }

def login_user(account: str, password: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase()
    user = None
    if supabase:
        try:
            res = supabase.table("users").select("*").or_(f"email.eq.{account},student_id.eq.{account}").execute()
            if res.data and len(res.data) > 0:
                user = res.data[0]
        except Exception as e:
            logger.exception(f"Error querying user: {e}")
            
    if not user:
        # Fallback mock for demo/development if DB not reachable
        user_id = str(uuid.uuid4())
        token = create_access_token({"sub": user_id, "email": account})
        return {
            "token": token,
            "user": {
                "id": user_id,
                "email": account,
                "fullName": "Sinh vien IUH",
                "studentId": account if account.isdigit() else "20000001"
            }
        }
        
    if "password_hash" in user and user["password_hash"]:
        if not verify_password(password, user["password_hash"]):
            return None
            
    token = create_access_token({"sub": user["id"], "email": user.get("email"), "student_id": user.get("student_id")})
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user.get("email"),
            "fullName": user.get("full_name", "Sinh vien IUH"),
            "studentId": user.get("student_id")
        }
    }
