"""Thư viện bộ từ vựng hệ thống ("curated decks") theo mô hình clone-on-start.

- Bộ hệ thống: `flashcard_decks.is_system = TRUE`, `user_id` NULL, các thẻ cũng không có `user_id`.
  Các API cá nhân (/decks, /cards, /review...) từ chối bản ghi không có chủ (xem `_is_owner`), nên người dùng chỉ đọc
  bộ hệ thống qua các hàm ở đây và học bằng cách CLONE sang một deck riêng (trạng thái FSRS mới cho từng người).
- Cần migration 004 (`db/migrations/004_flashcard_catalog.sql`). Chưa chạy thì các hàm trả HTTP 503 kèm hướng dẫn.
- `upsert_system_deck` chỉ dành cho script nạp nội dung (`scripts/seed_catalog.py`), không có API nào gọi tới.
"""
from __future__ import annotations

import asyncio
import datetime
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from app.services.excel_importer import _insert_chunk, bulk_insert_cards
from app.services.flashcard_service import (
    count_deck_cards,
    create_deck,
    db_write_error,
    delete_deck,
    get_supabase,
    new_card_record,
    to_valid_uuid,
)
from app.services.normalization import clean_text
from app.utils.logger import logger

DECK_COLUMNS = "id, title, description, lang_code, icon_flag, category, level, slug, created_at"
CARD_COLUMNS = "term, definition, phonetic, part_of_speech, example, example_translation, audio_url, lang_code"
PAGE = 1000


def _catalog_error(exc: Exception) -> HTTPException:
    text = str(exc).lower()
    if "column" in text and ("does not exist" in text or "schema cache" in text or "could not find" in text):
        return HTTPException(
            status_code=503,
            detail="Thư viện bộ từ chưa sẵn sàng: cơ sở dữ liệu chưa chạy migration 004 (db/migrations/004_flashcard_catalog.sql).",
        )
    logger.error(f"Catalog database error: {exc}")
    return HTTPException(status_code=503, detail="Không thể truy cập thư viện bộ từ. Vui lòng thử lại sau.")


def _require_supabase():
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=503, detail="Thư viện bộ từ cần kết nối cơ sở dữ liệu (Supabase).")
    return supabase


async def _published_system_deck(supabase, deck_id: str) -> Dict[str, Any]:
    valid_id = to_valid_uuid(deck_id)
    if not valid_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ từ.")
    try:
        res = await run_in_threadpool(
            lambda: supabase.table("flashcard_decks").select(DECK_COLUMNS)
                .eq("id", valid_id).eq("is_system", True).eq("status", "published").execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise _catalog_error(exc) from exc
    if not res.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ từ.")
    return res.data[0]


async def _fetch_cards(supabase, deck_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    offset = 0
    try:
        while True:
            size = PAGE if limit is None else min(PAGE, limit - len(rows))
            if size <= 0:
                break
            res = await run_in_threadpool(
                lambda o=offset, n=size: supabase.table("flashcards").select(CARD_COLUMNS)
                    .eq("deck_id", deck_id).order("created_at").order("id").range(o, o + n - 1).execute()
            )
            batch = res.data or []
            rows.extend(batch)
            if len(batch) < size:
                break
            offset += size
    except Exception as exc:  # noqa: BLE001
        raise _catalog_error(exc) from exc
    return rows


async def count_cards_by_deck(supabase, deck_ids: List[str]) -> Dict[str, int]:
    """Số thẻ của nhiều bộ bằng một truy vấn phân trang (nhanh hơn N truy vấn COUNT khi mỗi bộ chỉ vài chục thẻ)."""
    counts: Dict[str, int] = {d: 0 for d in deck_ids}
    offset = 0
    try:
        while True:
            res = await run_in_threadpool(
                lambda o=offset: supabase.table("flashcards").select("deck_id")
                    .in_("deck_id", deck_ids).order("id").range(o, o + PAGE - 1).execute()
            )
            rows = res.data or []
            for row in rows:
                counts[str(row["deck_id"])] = counts.get(str(row["deck_id"]), 0) + 1
            if len(rows) < PAGE:
                return counts
            offset += PAGE
    except Exception as exc:  # noqa: BLE001
        raise _catalog_error(exc) from exc


async def list_catalog(
    user_id: str, category: Optional[str] = None, level: Optional[str] = None, query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Các bộ hệ thống đã xuất bản, kèm số thẻ và cờ `added_deck_id` (sổ của chính người dùng nếu đã thêm)."""
    supabase = get_supabase()
    if not supabase:
        return []
    try:
        def build():
            q = supabase.table("flashcard_decks").select(DECK_COLUMNS).eq("is_system", True).eq("status", "published")
            if category:
                q = q.eq("category", category)
            if level:
                q = q.eq("level", level)
            if query:
                cleaned = clean_text(query, 60).replace("%", "").replace("_", "").replace(",", " ")
                if cleaned:
                    q = q.ilike("title", f"%{cleaned}%")
            return q.order("category").order("created_at").execute()

        res = await run_in_threadpool(build)
    except Exception as exc:  # noqa: BLE001
        raise _catalog_error(exc) from exc

    decks = [dict(d) for d in (res.data or [])]
    if not decks:
        return []

    uid = to_valid_uuid(user_id)
    ids = [d["id"] for d in decks]

    async def my_copies() -> Dict[str, str]:
        if not uid:
            return {}
        try:
            mine = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("id, origin_deck_id")
                    .eq("user_id", uid).in_("origin_deck_id", ids).execute()
            )
        except Exception as exc:  # noqa: BLE001
            raise _catalog_error(exc) from exc
        return {str(r["origin_deck_id"]): str(r["id"]) for r in (mine.data or [])}

    # Đếm thẻ của mọi bộ và tra các bản sao của tôi chạy song song (đều độc lập nhau).
    added, counts = await asyncio.gather(my_copies(), count_cards_by_deck(supabase, [str(i) for i in ids]))
    for deck in decks:
        deck["cards_count"] = counts.get(str(deck["id"]), 0)
        deck["added_deck_id"] = added.get(str(deck["id"]))
    return decks


async def get_catalog_preview(deck_id: str, limit: int = 10) -> Dict[str, Any]:
    supabase = _require_supabase()
    deck = await _published_system_deck(supabase, deck_id)
    cards, total = await asyncio.gather(_fetch_cards(supabase, deck["id"], limit=limit), count_deck_cards(supabase, str(deck["id"])))
    deck["cards_count"] = total
    return {"deck": deck, "cards": cards}


def _is_unique_violation(exc: Exception) -> bool:
    text = str(exc).lower()
    return "duplicate key" in text or "23505" in text or "unique" in text


async def _existing_clone(supabase, uid: str, origin_id: str) -> Optional[Dict[str, Any]]:
    try:
        res = await run_in_threadpool(
            lambda: supabase.table("flashcard_decks").select("*")
                .eq("user_id", uid).eq("origin_deck_id", origin_id).limit(1).execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise _catalog_error(exc) from exc
    if not res.data:
        return None
    deck = dict(res.data[0])
    deck["cards_count"] = await count_deck_cards(supabase, str(deck["id"]))
    return deck


async def clone_catalog_deck(deck_id: str, user_id: str) -> Dict[str, Any]:
    """
    Sao chép bộ hệ thống sang deck riêng của người dùng (trạng thái FSRS mới). Idempotent:
    đã có bản sao thì trả lại bản đó (`created=False`). Lỗi giữa chừng thì xóa deck dở dang.
    """
    supabase = _require_supabase()
    uid = to_valid_uuid(user_id)
    if not uid:
        raise HTTPException(status_code=400, detail="Tài khoản không hợp lệ.")
    source = await _published_system_deck(supabase, deck_id)

    existing = await _existing_clone(supabase, uid, source["id"])
    if existing:
        return {"deck": existing, "created": False, "inserted": 0, "skipped_duplicates": 0}

    cards = await _fetch_cards(supabase, source["id"])
    if not cards:
        raise HTTPException(status_code=409, detail="Bộ từ này chưa có thẻ nào.")

    try:
        deck = await create_deck(
            source["title"], source.get("description") or "", user_id, lang_code=source.get("lang_code") or "en",
            extra={"origin_deck_id": source["id"], "category": source.get("category"), "level": source.get("level")},
        )
    except HTTPException as exc:
        if exc.status_code == 503 and (existing := await _existing_clone(supabase, uid, source["id"])):
            return {"deck": existing, "created": False, "inserted": 0, "skipped_duplicates": 0}  # bấm đúp: đã có bản sao
        raise

    cards_data = [
        {
            "term": c["term"],
            "definition": c["definition"],
            "phonetic": c.get("phonetic"),
            "part_of_speech": c.get("part_of_speech"),
            "example": c.get("example"),
            "example_translation": c.get("example_translation"),
            "level": source.get("level"),
            "source": "curated",
            "target_lang": "vi",
        }
        for c in cards
    ]
    try:
        result = await bulk_insert_cards(
            deck_id=deck["id"], user_id=user_id, cards_data=cards_data, lang_code=source.get("lang_code") or "en"
        )
    except Exception:
        try:
            await delete_deck(deck["id"], user_id)
        except Exception as cleanup_exc:  # noqa: BLE001
            logger.warning(f"Không dọn được deck clone dở dang {deck['id']}: {cleanup_exc}")
        raise
    deck["cards_count"] = result["inserted"]
    return {
        "deck": deck,
        "created": True,
        "inserted": result["inserted"],
        "skipped_duplicates": result["skipped_duplicates"],
    }


# --------------------------------------------------------------------------- dành cho script nạp nội dung
async def system_deck_exists(slug: str) -> bool:
    supabase = _require_supabase()
    try:
        res = await run_in_threadpool(
            lambda: supabase.table("flashcard_decks").select("id").eq("slug", slug).eq("is_system", True).execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise _catalog_error(exc) from exc
    return bool(res.data)


async def upsert_system_deck(
    slug: str,
    title: str,
    description: str,
    category: str,
    level: str,
    cards: List[Dict[str, Any]],
    lang_code: str = "en",
    status: str = "published",
    replace: bool = False,
) -> Dict[str, Any]:
    """
    Tạo (hoặc thay thế) một bộ hệ thống theo `slug`. Không có API nào gọi hàm này; chỉ `scripts/seed_catalog.py`.
    Đã có slug và `replace=False` -> bỏ qua (idempotent).
    """
    supabase = _require_supabase()
    try:
        res = await run_in_threadpool(
            lambda: supabase.table("flashcard_decks").select("id").eq("slug", slug).eq("is_system", True).execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise _catalog_error(exc) from exc

    row = {
        "title": title, "description": description, "lang_code": lang_code, "icon_flag": "📚",
        "is_system": True, "status": status, "category": category, "level": level, "slug": slug,
    }
    if res.data:
        deck_id = res.data[0]["id"]
        if not replace:
            return {"deck_id": deck_id, "skipped": True, "inserted": 0}
        try:
            await run_in_threadpool(lambda: supabase.table("flashcards").delete().eq("deck_id", deck_id).execute())
            await run_in_threadpool(lambda: supabase.table("flashcard_decks").update(row).eq("id", deck_id).execute())
        except Exception as exc:  # noqa: BLE001
            raise db_write_error("thay thế bộ từ hệ thống", exc) from exc
    else:
        deck_id = str(uuid.uuid4())
        try:
            await run_in_threadpool(lambda: supabase.table("flashcard_decks").insert({"id": deck_id, **row}).execute())
        except Exception as exc:  # noqa: BLE001
            raise _catalog_error(exc) from exc

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    records = [
        new_card_record(
            deck_id=deck_id, user_id="", term=c["term"], definition=c["definition"], lang_code=lang_code,
            phonetic=c.get("phonetic") or None, example_sentence=c.get("example") or None,
            part_of_speech=c.get("part_of_speech"), now_iso=now_iso,
            extra={k: c.get(k) for k in ("example_translation", "level", "source") if c.get(k)},
        )
        for c in cards
        if c.get("term") and c.get("definition")
    ]
    for i in range(0, len(records), 200):
        await _insert_chunk(supabase, records[i:i + 200])
    return {"deck_id": deck_id, "skipped": False, "inserted": len(records)}
