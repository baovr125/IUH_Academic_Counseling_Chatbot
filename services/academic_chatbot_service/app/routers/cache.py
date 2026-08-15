from fastapi import APIRouter, Depends
from app.utils.security import get_current_user_id
from app.services.supabase_client import get_supabase_client
from app.schemas.chat import ApiResult
from app.utils.logger import logger

router = APIRouter(prefix="/api/cache", tags=["cache"])

@router.delete("/clear")
async def clear_semantic_cache(current_user_id: str = Depends(get_current_user_id)):
    """Admin endpoint to manually purge the semantic cache."""
    # Note: In a real production scenario, you might want to verify if current_user_id has an 'admin' role.
    supabase = get_supabase_client()
    if not supabase:
        return ApiResult(ok=False, error={"message": "Lỗi kết nối CSDL."})
        
    try:
        # Delete all entries from semantic_cache (Supabase requires a filter for deletes)
        # We use a trick: match everything where id is not a dummy UUID
        supabase.table("semantic_cache").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        logger.info(f"User {current_user_id} cleared the semantic cache.")
        return ApiResult(ok=True, data={"message": "Đã xóa toàn bộ semantic cache thành công."})
    except Exception as e:
        logger.exception(f"Error clearing cache: {e}")
        return ApiResult(ok=False, error={"message": "Không thể xóa semantic cache."})
