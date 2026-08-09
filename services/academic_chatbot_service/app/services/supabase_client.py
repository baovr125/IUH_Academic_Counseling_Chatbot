import os
from typing import Optional
from supabase import create_client, Client
from app.utils.logger import logger

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if url and key:
        try:
            _supabase_client = create_client(url, key)
            return _supabase_client
        except Exception as e:
            logger.exception(f"Failed to create Supabase client: {e}")
    return None
