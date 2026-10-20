"""Flashcard theo ngôn ngữ: tổng hợp 10 bộ sưu tập, danh sách từ theo ngôn ngữ, lưu từ Realtime Translation.

Quy ước (xem db/migrations/005_flashcard_languages.sql):
- DECK là đơn vị ngôn ngữ; thẻ luôn cùng ngôn ngữ với deck. Deck có `lang_confirmed = FALSE` (hoặc mã ngôn ngữ không hợp lệ)
  KHÔNG nằm trong bộ sưu tập của ngôn ngữ nào mà hiện ở mục "Cần xác nhận ngôn ngữ" cho tới khi người dùng chọn lại.
- Mỗi người có tối đa một "Sổ mặc định" cho mỗi ngôn ngữ (nơi lưu từ khi dịch mà chưa chọn sổ).
- Không bao giờ đoán ngôn ngữ: thiếu hoặc không rõ -> ApiError 422.
"""
from __future__ import annotations

import asyncio
import datetime
import math
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from app.schemas.languages import SaveFromTranslationRequest
from app.services.flashcard_service import (
    MASTERED_STABILITY_DAYS,
    _is_owner,
    _normalize_card_row,
    _parse_due,
    create_card,
    create_deck,
    ensure_deck_for_write,
    get_supabase,
    is_missing_column_error,
    require_lang,
    to_valid_uuid,
    in_memory_cards,
    in_memory_decks,
)
from app.services.normalization import clean_text, dedupe_key
from app.utils.errors import ApiError
from app.utils.languages import (
    EXPLANATION_LANG,
    LEARNABLE_LANGS,
    SUPPORTED_LANGS,
    default_deck_title,
    normalize_lang,
)
from app.utils.logger import logger

PAGE = 1000
IDEMPOTENCY_TTL_SECONDS = 600
SORTS = ("recent", "alpha", "due")
STATUSES = ("all", "due", "new", "weak")

_save_cache: Dict[Tuple[str, str], Tuple[float, Dict[str, Any]]] = {}


def _migration_error(exc: Exception) -> ApiError:
    if is_missing_column_error(exc):
        return ApiError(
            503, "MIGRATION_REQUIRED",
            "Cơ sở dữ liệu chưa chạy migration 005 (db/migrations/005_flashcard_languages.sql). Hãy chạy migration rồi thử lại.",
        )
    logger.error(f"Language service database error: {exc}")
    return ApiError(503, "DB_ERROR", "Không thể truy cập cơ sở dữ liệu. Vui lòng thử lại sau.")


def _require_supabase_and_uid(user_id: str):
    supabase = get_supabase()
    uid = to_valid_uuid(user_id)
    if not supabase or not uid:
        raise ApiError(503, "DB_REQUIRED", "Tính năng này cần kết nối cơ sở dữ liệu và tài khoản hợp lệ.")
    return supabase, uid


async def _user_decks(supabase, uid: str) -> List[Dict[str, Any]]:
    try:
        res = await run_in_threadpool(
            lambda: supabase.table("flashcard_decks")
                .select("id, title, lang_code, lang_confirmed, is_default, created_at")
                .eq("user_id", uid).order("created_at").range(0, PAGE - 1).execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise _migration_error(exc) from exc
    return res.data or []


async def _user_card_rows(supabase, uid: str) -> List[Dict[str, Any]]:
    """Các cột tối thiểu của MỌI thẻ của người dùng (để đếm); đọc song song theo trang 1000 dòng."""
    cols = "deck_id, state, due, last_review, lapses, stability"
    try:
        head = await run_in_threadpool(
            lambda: supabase.table("flashcards").select("id", count="exact").eq("user_id", uid).limit(1).execute()
        )
        total = int(head.count or 0)
        pages = max(1, math.ceil(total / PAGE))
        batches: List[List[Dict[str, Any]]] = []
        for start in range(0, pages, 6):  # tối đa 6 trang song song để không dồn kết nối
            results = await asyncio.gather(*[
                run_in_threadpool(
                    lambda o=i * PAGE: supabase.table("flashcards").select(cols).eq("user_id", uid)
                        .order("id").range(o, o + PAGE - 1).execute()
                )
                for i in range(start, min(start + 6, pages))
            ])
            batches.extend(r.data or [] for r in results)
    except Exception as exc:  # noqa: BLE001
        raise _migration_error(exc) from exc
    return [row for batch in batches for row in batch]


def _deck_language(deck: Dict[str, Any]) -> Optional[str]:
    """Ngôn ngữ của deck nếu đã được xác nhận và hợp lệ; ngược lại None (thuộc mục "Cần xác nhận")."""
    return normalize_lang(deck.get("lang_code")) if deck.get("lang_confirmed") else None


async def language_summary(user_id: str) -> Dict[str, Any]:
    """Số sổ/thẻ/đến hạn/mới/đã thuộc/hay quên của từng trong 10 ngôn ngữ + các deck cần xác nhận ngôn ngữ.

    `mastered`: thẻ đã học (không còn mới) có độ bền trí nhớ >= MASTERED_STABILITY_DAYS, cùng quy tắc với `get_study_stats`.
    """
    supabase, uid = _require_supabase_and_uid(user_id)
    decks, cards = await asyncio.gather(_user_decks(supabase, uid), _user_card_rows(supabase, uid))
    now = datetime.datetime.now(datetime.timezone.utc)

    lang_of_deck = {d["id"]: _deck_language(d) for d in decks}
    stats: Dict[str, Dict[str, Any]] = {
        code: {"code": code, "learnable": code in LEARNABLE_LANGS, "decks": 0, "cards": 0, "due": 0, "new": 0, "mastered": 0, "weak": 0,
               "last_activity": None, "default_deck_id": None}
        for code in SUPPORTED_LANGS
    }
    card_counts: Dict[str, int] = {}
    for deck in decks:
        lang = lang_of_deck[deck["id"]]
        if lang:
            stats[lang]["decks"] += 1
            if deck.get("is_default"):
                stats[lang]["default_deck_id"] = deck["id"]

    for card in cards:
        deck_id = card.get("deck_id")
        card_counts[deck_id] = card_counts.get(deck_id, 0) + 1
        lang = lang_of_deck.get(deck_id)
        if not lang:
            continue
        entry = stats[lang]
        entry["cards"] += 1
        is_new = int(card.get("state") or 0) == 0 and not card.get("last_review")
        if is_new:
            entry["new"] += 1
        else:
            if _parse_due(card.get("due")) <= now:
                entry["due"] += 1
            if float(card.get("stability") or 0.0) >= MASTERED_STABILITY_DAYS:
                entry["mastered"] += 1
        if int(card.get("lapses") or 0) > 0:
            entry["weak"] += 1
        last = card.get("last_review")
        if last and (entry["last_activity"] is None or str(last) > str(entry["last_activity"])):
            entry["last_activity"] = last

    unconfirmed = [
        {"id": d["id"], "title": d["title"], "lang_code": d.get("lang_code"), "cards_count": card_counts.get(d["id"], 0)}
        for d in decks if lang_of_deck[d["id"]] is None
    ]
    return {
        "languages": [stats[code] for code in SUPPORTED_LANGS],
        "unconfirmed": {"decks": unconfirmed, "cards": sum(d["cards_count"] for d in unconfirmed)},
    }


def _search_term(q: str) -> str:
    """Bỏ ký tự có nghĩa đặc biệt trong bộ lọc PostgREST (`,` `(` `)` và ký tự đại diện) khỏi chuỗi tìm kiếm."""
    return re.sub(r"[,()%*_\\]", " ", clean_text(q, 60)).strip()


async def list_language_cards(
    user_id: str,
    lang_code: str,
    q: Optional[str] = None,
    sort: str = "recent",
    status: str = "all",
    deck_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Thẻ của một ngôn ngữ (qua các deck ĐÃ xác nhận của ngôn ngữ đó), lọc/sắp xếp/phân trang ngay ở máy chủ."""
    lang = require_lang(lang_code)
    if sort not in SORTS or status not in STATUSES:
        raise ApiError(422, "INVALID_QUERY", f"sort phải thuộc {SORTS}, status phải thuộc {STATUSES}.")
    supabase, uid = _require_supabase_and_uid(user_id)

    decks = [d for d in await _user_decks(supabase, uid) if _deck_language(d) == lang]
    titles = {d["id"]: d["title"] for d in decks}
    if deck_id:
        if deck_id not in titles:
            raise ApiError(404, "DECK_NOT_FOUND", "Không tìm thấy bộ thẻ này trong ngôn ngữ đã chọn.")
        deck_ids = [deck_id]
    else:
        deck_ids = list(titles)
    if not deck_ids:
        return {"lang_code": lang, "items": [], "total": 0, "limit": limit, "offset": offset}

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    term = _search_term(q) if q else ""

    def build():
        query = supabase.table("flashcards").select("*", count="exact").in_("deck_id", deck_ids)
        if status == "new":
            query = query.eq("state", 0)
        elif status == "due":
            query = query.neq("state", 0).lte("due", now_iso)
        elif status == "weak":
            query = query.gt("lapses", 0)
        if term:
            query = query.or_(f"term.ilike.%{term}%,definition.ilike.%{term}%")
        if sort == "alpha":
            query = query.order("term")
        elif sort == "due":
            query = query.order("due")
        else:
            query = query.order("created_at", desc=True)
        return query.order("id").range(offset, offset + limit - 1).execute()

    try:
        res = await run_in_threadpool(build)
    except Exception as exc:  # noqa: BLE001
        raise _migration_error(exc) from exc

    items = []
    for row in res.data or []:
        card = _normalize_card_row(row, row["deck_id"])
        card["deck_title"] = titles.get(row["deck_id"])
        items.append(card)
    return {"lang_code": lang, "items": items, "total": int(res.count or 0), "limit": limit, "offset": offset}


async def get_or_create_default_deck(user_id: str, lang_code: str) -> Dict[str, Any]:
    """'Sổ mặc định' của ngôn ngữ: tìm hoặc tạo (an toàn khi gọi song song nhờ chỉ mục UNIQUE một phần)."""
    lang = require_lang(lang_code)
    supabase, uid = _require_supabase_and_uid(user_id)

    async def find() -> Optional[Dict[str, Any]]:
        try:
            res = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("*")
                    .eq("user_id", uid).eq("lang_code", lang).eq("is_default", True).limit(1).execute()
            )
        except Exception as exc:  # noqa: BLE001
            raise _migration_error(exc) from exc
        return res.data[0] if res.data else None

    existing = await find()
    if existing:
        return existing
    try:
        return await create_deck(
            default_deck_title(lang), f"Từ vựng {lang.upper()} lưu từ Dịch thuật", user_id, lang_code=lang,
            extra={"is_default": True},
        )
    except HTTPException:
        again = await find()  # có thể một yêu cầu song song vừa tạo xong (vi phạm UNIQUE)
        if again:
            return again
        raise


def _escape_like(term: str) -> str:
    return re.sub(r"[%*\\]", "_", term)


async def _find_duplicate(supabase, deck_id: str, term: str) -> Optional[Dict[str, Any]]:
    try:
        res = await run_in_threadpool(
            lambda: supabase.table("flashcards").select("*").eq("deck_id", deck_id).ilike("term", _escape_like(term.strip())).execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise _migration_error(exc) from exc
    key = dedupe_key(term)
    return next((r for r in (res.data or []) if dedupe_key(r.get("term", "")) == key), None)


async def save_from_translation(user_id: str, req: SaveFromTranslationRequest) -> Dict[str, Any]:
    """
    Lưu một từ từ Realtime Translation vào bộ sưu tập ĐÚNG ngôn ngữ nguồn.
    - `source_lang` bắt buộc, thuộc 9 ngôn ngữ học (không 'auto', không 'vi'); không đoán.
    - `deck_id` (nếu có) phải của người dùng và cùng ngôn ngữ (409 LANG_MISMATCH nếu lệch); không có thì dùng Sổ mặc định.
    - Trùng từ trong cùng sổ: 409 DUPLICATE_CARD kèm thẻ đã có, hoặc `on_duplicate="update"` để cập nhật nghĩa.
    - Idempotent theo `client_request_id` (10 phút).
    """
    now = time.time()
    for key in [k for k, (ts, _) in _save_cache.items() if now - ts > IDEMPOTENCY_TTL_SECONDS]:
        _save_cache.pop(key, None)
    cache_key = (user_id, req.client_request_id)
    if cache_key in _save_cache:
        return {**_save_cache[cache_key][1], "idempotent_replay": True}

    lang = require_lang(req.source_lang)
    if lang == EXPLANATION_LANG:
        raise ApiError(
            422, "LANG_UNSUPPORTED",
            "Tiếng Việt là ngôn ngữ giải nghĩa nên không có sổ học riêng. Hãy chọn ngôn ngữ nguồn là một ngoại ngữ.",
        )
    term, meaning = clean_text(req.term, 500), clean_text(req.translation, 1000)
    if not term or not meaning:
        raise ApiError(422, "INVALID_INPUT", "Từ vựng và nghĩa tiếng Việt không được để trống.")

    supabase, uid = _require_supabase_and_uid(user_id)

    if req.deck_id:
        deck_row = await ensure_deck_for_write(req.deck_id, user_id, lang)
        deck_lang = normalize_lang((deck_row or {}).get("lang_code"))
        if deck_lang != lang:
            raise ApiError(409, "LANG_MISMATCH", f"Bộ thẻ này thuộc ngôn ngữ '{deck_lang or '?'}', không phải '{lang}'. Hãy chọn bộ thẻ đúng ngôn ngữ.")
        try:
            flag = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("lang_confirmed").eq("id", req.deck_id).execute()
            )
        except Exception as exc:  # noqa: BLE001
            raise _migration_error(exc) from exc
        if flag.data and not flag.data[0].get("lang_confirmed"):
            raise ApiError(
                409, "DECK_LANG_UNCONFIRMED",
                "Ngôn ngữ của bộ thẻ này chưa được xác nhận. Hãy xác nhận ngôn ngữ cho bộ thẻ trước khi thêm từ.",
            )
        deck = deck_row
    else:
        deck = await get_or_create_default_deck(user_id, lang)

    existing = await _find_duplicate(supabase, deck["id"], term)
    if existing:
        if req.on_duplicate == "reject":
            raise ApiError(
                409, "DUPLICATE_CARD", f"Từ '{term}' đã có trong sổ '{deck.get('title', '')}'.",
                data={"card": {"id": existing["id"], "term": existing.get("term"), "definition": existing.get("definition")},
                      "deck": {"id": deck["id"], "title": deck.get("title")}},
            )
        updates = {"definition": meaning, "target_lang": EXPLANATION_LANG}
        for column, value in (("phonetic", req.phonetic), ("example", req.example), ("example_translation", req.example_translation)):
            if value:
                updates[column] = value
        try:
            await run_in_threadpool(lambda: supabase.table("flashcards").update(updates).eq("id", existing["id"]).execute())
        except Exception as exc:  # noqa: BLE001
            if not is_missing_column_error(exc):
                raise ApiError(503, "DB_ERROR", "Không thể cập nhật thẻ. Vui lòng thử lại sau.") from exc
            updates = {k: v for k, v in updates.items() if k not in ("target_lang", "example_translation")}
            await run_in_threadpool(lambda: supabase.table("flashcards").update(updates).eq("id", existing["id"]).execute())
        result = {"created": False, "updated": True, "card": {**existing, **updates}, "deck": deck}
        _save_cache[cache_key] = (now, result)
        return result

    card = await create_card(
        deck_id=deck["id"], front_text=term, back_text=meaning, user_id=user_id, phonetic=req.phonetic,
        example_sentence=req.example, part_of_speech=req.part_of_speech or "phrase", lang_code=lang,
        extra={"source": "translation", "target_lang": EXPLANATION_LANG, "example_translation": req.example_translation},
    )
    if req.detection:
        logger.info(f"Saved from translation: lang={lang} detection={req.detection.model_dump(exclude_none=True)}")
    result = {"created": True, "updated": False, "card": card, "deck": deck}
    _save_cache[cache_key] = (now, result)
    return result


def reset_caches() -> None:
    """Dùng cho test."""
    _save_cache.clear()
