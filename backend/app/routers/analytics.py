from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from collections import Counter
from app.services.chat_service import get_supabase_client
from app.utils.logger import logger

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview")
async def get_analytics_overview() -> Dict[str, Any]:
    """
    Returns aggregated metrics for RAG Analytics Dashboard:
    - AVG(latency_ms)
    - SUM(prompt_tokens)
    - COUNT(feedback='like') / (COUNT feedback) as satisfaction_rate
    - Top 10 most common user queries
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"ok": False, "error": {"message": "Không thể kết nối đến cơ sở dữ liệu (Supabase)", "code": "500"}}

    try:
        # Fetch all messages (For production, this should use a DB View or RPC function for scalability)
        res = supabase.table("messages").select("role, content, latency_ms, prompt_tokens, feedback").execute()
        messages = res.data or []

        total_latency = 0
        latency_count = 0
        total_prompt_tokens = 0
        
        like_count = 0
        total_feedback = 0

        user_queries = []

        for msg in messages:
            if msg.get("role") == "assistant":
                # Latency
                lat = msg.get("latency_ms")
                if lat is not None:
                    total_latency += lat
                    latency_count += 1
                
                # Prompt tokens
                pt = msg.get("prompt_tokens")
                if pt is not None:
                    total_prompt_tokens += pt

                # Feedback
                fb = msg.get("feedback")
                if fb in ["like", "dislike"]:
                    total_feedback += 1
                    if fb == "like":
                        like_count += 1
                        
            elif msg.get("role") == "user":
                content = msg.get("content")
                if content and isinstance(content, str):
                    user_queries.append(content.strip())

        # Calculations
        avg_latency = (total_latency / latency_count) if latency_count > 0 else 0
        satisfaction_rate = (like_count / total_feedback) if total_feedback > 0 else 0

        # Top 10 queries
        query_counts = Counter(user_queries)
        top_10_queries = [{"query": k, "count": v} for k, v in query_counts.most_common(10)]

        return {
            "ok": True,
            "data": {
                "metrics": {
                    "avg_latency_ms": round(avg_latency, 2),
                    "total_prompt_tokens": total_prompt_tokens,
                    "satisfaction_rate": round(satisfaction_rate, 2),
                    "total_feedback": total_feedback,
                    "like_count": like_count,
                    "dislike_count": total_feedback - like_count
                },
                "top_queries": top_10_queries
            }
        }
    except Exception as e:
        logger.exception(f"Error fetching analytics overview: {e}")
        return {"ok": False, "error": {"message": "Đã xảy ra lỗi nội bộ máy chủ", "code": "500"}}
