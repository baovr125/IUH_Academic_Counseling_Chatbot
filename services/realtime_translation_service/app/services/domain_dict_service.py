from app.services.supabase_client import get_supabase
from app.services.cache_service import get_redis
from app.utils.logger import logger

def sync_dictionary_to_redis():
    """Fetches all dictionary entries from Supabase and stores them in Redis for 0ms latency lookups."""
    supabase = get_supabase()
    if not supabase:
        logger.warning("Cannot sync dictionary to Redis: Supabase client is not available.")
        return

    try:
        # Fetch all entries from domain_dictionaries
        response = supabase.table("domain_dictionaries").select("*").execute()
        entries = response.data
        
        if not entries:
            logger.info("No domain dictionary entries found in Supabase.")
            return

        # Group by domain
        domain_dict = {}
        for entry in entries:
            domain = entry.get("domain")
            word = entry.get("word").lower()
            translation = entry.get("translation")
            
            if domain not in domain_dict:
                domain_dict[domain] = {}
            domain_dict[domain][word] = translation

        # Update Redis hashes
        redis_client = get_redis()
        if not redis_client:
            logger.warning("Cannot sync dictionary to Redis: Redis client is not available.")
            return

        pipeline = redis_client.pipeline()
        for domain, word_map in domain_dict.items():
            redis_key = f"domain_dict:{domain}"
            # Clear old dictionary for this domain
            pipeline.delete(redis_key)
            if word_map:
                pipeline.hset(redis_key, mapping=word_map)
        
        # Xóa cache từ điển toàn cục của domain_service. Key có hậu tố version (all_domain_dictionaries_v{n}),
        # nên xóa theo mẫu; key không version cũ không còn được đọc.
        for stale_key in redis_client.scan_iter("all_domain_dictionaries*"):
            pipeline.delete(stale_key)
        
        pipeline.execute()
        logger.info(f"Successfully synced {len(entries)} domain dictionary entries to Redis.")

    except Exception as e:
        logger.error(f"Error syncing domain dictionary to Redis: {e}")
