"""Hạn mức số lượt sinh từ vựng bằng AI mỗi ngày (giống huy hiệu "CÒN x/y LƯỢT HÔM NAY" trên giao diện).

- Ngày tính theo giờ Việt Nam (UTC+7, cố định để không cần tzdata trong image slim).
- Lưu ở bảng Supabase `vocab_generation_usage` (migration 003). Chưa có bảng, hoặc user id không phải UUID,
  thì dùng bộ đếm trong bộ nhớ (mất khi restart; có log cảnh báo một lần).
- Cách tính: giữ chỗ 1 lượt TRƯỚC khi gọi AI và hoàn lại nếu lần sinh thất bại, nên lỗi hệ thống không mất lượt.
  Đọc-rồi-ghi không nguyên tử; hai yêu cầu song song cùng lúc có thể vượt hạn mức 1 lượt (chấp nhận được).
- Biến môi trường: VOCAB_DAILY_LIMIT_ADMIN (mặc định 50), VOCAB_DAILY_LIMIT_STUDENT (sinh viên/giảng viên IUH, mặc định 10),
  VOCAB_DAILY_LIMIT_NORMAL (tài khoản thường/công cộng, mặc định 3).
"""
from __future__ import annotations

import datetime
import os
from typing import Any, Dict, Optional, Tuple

from starlette.concurrency import run_in_threadpool

from app.services.flashcard_service import get_supabase, to_valid_uuid
from app.services.vocab_pipeline import VocabError
from app.utils.logger import logger

VN_TZ = datetime.timezone(datetime.timedelta(hours=7))
TABLE = "vocab_generation_usage"

_memory: Dict[Tuple[str, str], int] = {}
_warned_missing_table = False


def _env_int(name: str, default: int) -> int:
    try:
        return max(0, int(os.getenv(name, default)))
    except ValueError:
        return default


def tier_info(role: Optional[str]) -> Tuple[str, str, int]:
    """(mã tier, nhãn hiển thị, hạn mức/ngày)."""
    if role == "admin":
        return "admin", "QUẢN TRỊ", _env_int("VOCAB_DAILY_LIMIT_ADMIN", 50)
    if role == "student":
        return "student", "SINH VIÊN IUH", _env_int("VOCAB_DAILY_LIMIT_STUDENT", 10)
    return "normal", "THƯỜNG", _env_int("VOCAB_DAILY_LIMIT_NORMAL", 3)


def _today() -> datetime.date:
    return datetime.datetime.now(VN_TZ).date()


def _resets_at() -> str:
    tomorrow = datetime.datetime.combine(_today() + datetime.timedelta(days=1), datetime.time.min, tzinfo=VN_TZ)
    return tomorrow.isoformat()


def _warn_missing_table(exc: Exception) -> None:
    global _warned_missing_table
    if not _warned_missing_table:
        _warned_missing_table = True
        logger.warning(
            f"Không dùng được bảng {TABLE} (chạy db/migrations/003_flashcard_ai_generation.sql); "
            f"tạm đếm hạn mức trong bộ nhớ. Chi tiết: {exc}"
        )


async def _read_used(user_id: str) -> int:
    day = _today().isoformat()
    supabase = get_supabase()
    uid = to_valid_uuid(user_id)
    if supabase and uid:
        try:
            res = await run_in_threadpool(
                lambda: supabase.table(TABLE).select("used").eq("user_id", uid).eq("usage_date", day).execute()
            )
            return int(res.data[0]["used"]) if res.data else 0
        except Exception as exc:  # noqa: BLE001
            _warn_missing_table(exc)
    return _memory.get((user_id, day), 0)


async def _write_used(user_id: str, used: int) -> None:
    day = _today().isoformat()
    used = max(0, used)
    supabase = get_supabase()
    uid = to_valid_uuid(user_id)
    if supabase and uid:
        try:
            await run_in_threadpool(
                lambda: supabase.table(TABLE).upsert(
                    {"user_id": uid, "usage_date": day, "used": used}, on_conflict="user_id,usage_date"
                ).execute()
            )
            return
        except Exception as exc:  # noqa: BLE001
            _warn_missing_table(exc)
    _memory[(user_id, day)] = used


async def get_quota(user_id: str, role: Optional[str] = None) -> Dict[str, Any]:
    tier, label, limit = tier_info(role)
    used = await _read_used(user_id)
    return {
        "tier": tier,
        "tier_label": label,
        "limit": limit,
        "used": used,
        "remaining": max(0, limit - used),
        "resets_at": _resets_at(),
    }


async def reserve(user_id: str, role: Optional[str] = None) -> Dict[str, Any]:
    """Giữ chỗ 1 lượt. Raise VocabError 429 nếu đã hết lượt hôm nay."""
    quota = await get_quota(user_id, role)
    if quota["remaining"] <= 0:
        raise VocabError(
            429, "QUOTA_EXCEEDED",
            f"Bạn đã dùng hết {quota['limit']} lượt tạo từ vựng bằng AI hôm nay. Lượt mới sẽ có vào 00:00 ngày mai."
        )
    await _write_used(user_id, quota["used"] + 1)
    return quota


async def refund(user_id: str) -> None:
    """Hoàn lại 1 lượt (khi lần sinh thất bại)."""
    try:
        await _write_used(user_id, (await _read_used(user_id)) - 1)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Không hoàn được lượt sinh từ cho user {user_id}: {exc}")
