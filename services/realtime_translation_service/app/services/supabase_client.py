import os
from typing import Optional
from supabase import create_client, Client
from app.utils.logger import logger

_supabase_client = None

def get_supabase() -> Optional[Client]:
    global _supabase_client
    if _supabase_client:
        return _supabase_client
        
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        logger.warning("Supabase URL or Key not found in environment variables. DB integration disabled.")
        return None
        
    try:
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None
